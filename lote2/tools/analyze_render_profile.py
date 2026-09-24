#!/usr/bin/env python3
"""Analisador do Lote 2 (render, ceu, luz e camera).

Confere o codigo do Lote 2 contra os fatos do Godot 4.7.2
(tools/render_facts.json) e contra as regras do plano de qualidade visual.
Sai com codigo 1 se achar erro.

Rode:  python3 tools/analyze_render_profile.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
FACTS = TOOLS / "render_facts.json"
RUNTIME = ROOT / "scripts" / "render_quality.gd"
WORLD_CANDIDATES = [ROOT / "scripts" / "game_3d.gd", ROOT / "scripts" / "game_3d_lote2_patch.gd"]
PROJECT_CANDIDATES = [ROOT / "project.godot", ROOT / "project.godot.lote2"]

# Identificadores usados pelo codigo que ainda nao foram conferidos nos XMLs.
PENDENTES = {
    "Viewport.MSAA_DISABLED", "Viewport.MSAA_2X", "Viewport.MSAA_4X", "Viewport.MSAA_8X",
    "Environment.FOG_MODE_EXPONENTIAL",
    "Engine.get_frames_per_second",
}

# Metodos de qualquer Object usados no codigo.
METODOS_DE_OBJECT = {"new", "size", "is_empty", "get", "has", "duplicate", "has_method",
                     "connect", "call", "call_deferred", "set", "emit_signal", "free"}

# atributo -> (guarda exigida, explicacao). Guardas:
#   "fp"      -> so dentro de "if _method == \"forward_plus\""
#   "not_gl"  -> so dentro de "if _method != \"gl_compatibility\""
#   "not_fp"  -> nunca dentro do ramo forward_plus
GUARD_RULES = [
    ("light_angular_distance", "fp", "PCSS e exclusivo do Forward+ (Light3D.light_angular_distance)"),
    ("auto_exposure_enabled", "fp", "auto-exposicao e exclusiva do Forward+ (CameraAttributesPractical)"),
    ("auto_exposure_min_sensitivity", "fp", "auto-exposicao e exclusiva do Forward+ (CameraAttributesPractical)"),
    ("auto_exposure_max_sensitivity", "fp", "auto-exposicao e exclusiva do Forward+ (CameraAttributesPractical)"),
    ("auto_exposure_speed", "fp", "auto-exposicao e exclusiva do Forward+ (CameraAttributesPractical)"),
    ("ssil_enabled", "fp", "SSIL e exclusivo do Forward+ (Environment)"),
    ("ssr_enabled", "fp", "SSR e exclusivo do Forward+ (Environment)"),
    ("sdfgi_enabled", "fp", "SDFGI e exclusivo do Forward+ (Environment)"),
    ("volumetric_fog_enabled", "fp", "nevoa volumetrica e exclusiva do Forward+ (Environment)"),
    ("fog_aerial_perspective", "fp", "perspectiva aerea e exclusiva do Forward+ (Environment)"),
    ("glow_strength", "not_gl", "glow_strength nao existe no caminho de Compatibilidade"),
    ("glow_blend_mode", "not_gl", "glow_blend_mode nao existe no caminho de Compatibilidade"),
    ("glow_map", "not_gl", "glow_map nao existe no caminho de Compatibilidade"),
    ("msaa_3d", "not_gl", "MSAA 3D nao existe no Compatibility"),
    ("scaling_3d_scale", "not_gl", "escala 3D nao existe no Compatibility"),
    ("scaling_3d_mode", "not_gl", "escala 3D/FSR nao existe no Compatibility"),
    ("dof_blur_amount", "not_gl", "DOF so existe em Forward+ e Mobile (CameraAttributesPractical)"),
    ("dof_blur_far_enabled", "not_gl", "DOF so existe em Forward+ e Mobile (CameraAttributesPractical)"),
    ("dof_blur_far_distance", "not_gl", "DOF so existe em Forward+ e Mobile (CameraAttributesPractical)"),
    ("dof_blur_far_transition", "not_gl", "DOF so existe em Forward+ e Mobile (CameraAttributesPractical)"),
    ("sky_cover", "not_gl", "nuvens do ceu procedural ficam fora do caminho de Compatibilidade"),
    ("AMBIENT_SOURCE_SKY", "fp", "ambiente vindo do ceu exige Forward+ neste projeto"),
    ("AMBIENT_SOURCE_COLOR", "not_fp", None),
]

# Paleta de referencia da imagem (normalizada).
PALETA = {
    "sol_creme": (1.00, 0.93, 0.80, 0.08),
    "sombra_azulada": (0.33, 0.39, 0.48, 0.09),
    "nevoa_creme": (0.84, 0.79, 0.70, 0.10),
}

EXIGIDOS = {
    "scaling_3d_scale": "escala 3D (desempenho no celular)",
    "scaling_3d_mode": "modo de escala 3D/FSR",
    "use_debanding": "debanding (obrigatorio com ceu de degrade)",
    "shadow_blur": "suavidade da sombra (substitui PCSS no Mobile)",
    "fog_density": "nevoa de profundidade",
    "adjustment_saturation": "ajuste de saturacao da paleta",
    "TONE_MAPPER_ACES": "tone mapping filmico/ACES",
    "_configure_viewport": "fase 1 do controlador (pipeline)",
    "_configure_world": "fase 2 do controlador (mundo)",
    "apply(": "ponto de entrada do controlador",
    "node_added": "reconexao depois de refazer o mundo (Lote 3)",
}


def strip_comment(line: str) -> str:
    return line.split("#", 1)[0] if "#" in line else line


def annotate(lines: list) -> list:
    """(num, texto_sem_comentario, guardas_ativas) por linha."""
    out = []
    stack = []  # (indentacao, tipo)
    for num, raw in enumerate(lines, start=1):
        line = strip_comment(raw)
        stripped = line.strip()
        if not stripped:
            out.append((num, "", [kind for _, kind in stack]))
            continue
        indent = len(line) - len(line.lstrip())
        while stack and indent <= stack[-1][0]:
            stack.pop()
        guards = [kind for _, kind in stack]
        out.append((num, stripped, guards))
        kind = None
        if stripped.startswith('if _method == "forward_plus"'):
            kind = "fp"
        elif stripped.startswith('if _method != "gl_compatibility"'):
            kind = "not_gl"
        elif stripped.startswith('if _method == "gl_compatibility"'):
            kind = "gl"
        if kind is not None and stripped.endswith(":"):
            stack.append((indent, kind))
    return out


def guard_ok(guards: list, need: str) -> bool:
    if need == "fp":
        return "fp" in guards
    if need == "not_gl":
        return "gl" not in guards and "not_gl" in guards
    if need == "not_fp":
        return "fp" not in guards
    return False


def main() -> int:
    if not FACTS.exists():
        print(f"ERRO: {FACTS.name} nao encontrado")
        return 1
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    if not RUNTIME.exists():
        print(f"ERRO: {RUNTIME} nao encontrado")
        return 1

    text = RUNTIME.read_text(encoding="utf-8")
    lines = text.splitlines()
    problems: list = []
    warnings: list = []

    members = set()
    for cls, names in facts["membros"].items():
        members.update(names)
    constants = set()
    for cls, names in facts["constantes"].items():
        constants.update(names)

    annotated = annotate(lines)

    # 1) regras de renderizador, respeitando os blocos if/else
    for num, line, guards in annotated:
        if line.startswith("#"):
            continue
        for pattern, need, why in GUARD_RULES:
            if pattern not in line:
                continue
            if why is None:
                if not guard_ok(guards, need):
                    problems.append(f"ERRO (linha {num}): {pattern} no lugar errado do if/else")
                continue
            if not guard_ok(guards, need):
                problems.append(f"ERRO (linha {num}): {pattern} sem a guarda devida - {why}")

    # 2) identificadores nao conferidos
    for num, line, _guards in annotated:
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", line):
            dotted, attr = f"{m.group(1)}.{m.group(2)}", m.group(2)
            if attr in METODOS_DE_OBJECT or attr in members or attr in constants:
                continue
            if dotted in PENDENTES:
                warnings.append(f"AVISO (linha {num}): {dotted} ainda nao foi conferido nos XMLs do 4.7.2")
                continue
            cls = dotted.split(".")[0]
            if cls in facts["membros"]:
                warnings.append(f"AVISO (linha {num}): {dotted} fora da lista de membros conferidos de {cls}")
            elif cls[0].isupper():
                warnings.append(f"AVISO (linha {num}): {dotted} nao verificado")
    warnings = sorted(set(warnings))

    # 3) recursos exigidos pelo plano
    for key, why in EXIGIDOS.items():
        if key not in text:
            problems.append(f"ERRO: falta {why} ({key})")

    # 4) paleta da referencia
    def luma(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    for name, (r, g, b, tol) in PALETA.items():
        found = False
        for m in re.finditer(r"Color\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)", text):
            cr, cg, cb = (float(m.group(1)), float(m.group(2)), float(m.group(3)))
            if abs(cr - r) <= tol and abs(cg - g) <= tol and abs(cb - b) <= tol:
                found = True
                break
        if not found:
            problems.append(f"ERRO: paleta - cor {name} ausente do controlador")
    if luma(PALETA["sol_creme"][:3]) <= luma(PALETA["sombra_azulada"][:3]) + 0.4:
        problems.append("ERRO: paleta - sol e sombra com luminancia parecida demais")

    # 5) projeto (renderizador + autoload) e chamada do jogo
    project = next((p for p in PROJECT_CANDIDATES if p.exists()), None)
    if project is None:
        warnings.append("AVISO: sem project.godot nesta copia; confira renderizador e autoload manualmente")
    else:
        ptext = project.read_text(encoding="utf-8")
        if 'rendering_method="mobile"' not in ptext:
            warnings.append('AVISO: project.godot sem rendering_method="mobile"')
        if "render_quality.gd" not in ptext:
            warnings.append("AVISO: autoload RenderQuality nao registrado no project.godot")
        if 'rendering_method.mobile="gl_compatibility"' not in ptext:
            warnings.append("AVISO: sem plano B gl_compatibility para Android sem Vulkan")

    world = next((p for p in WORLD_CANDIDATES if p.exists()), None)
    if world is None:
        warnings.append("AVISO: game_3d.gd nao encontrado nesta copia; confirme a chamada RenderQuality.apply()")
    elif "RenderQuality" not in world.read_text(encoding="utf-8"):
        warnings.append("AVISO: game_3d.gd ainda nao chama RenderQuality.apply()")

    # 6) o controlador precisa de degrau leve para o Adreno 610
    if "0.68" not in text:
        warnings.append("AVISO: o degrau mais leve do Mobile nao chega a 0.68 de escala")

    print("Analise do Lote 2 - renderizador, ceu, luz e camera")
    print(f"  fatos: {FACTS.name} (Godot {facts['tag']})")
    print(f"  codigo: {RUNTIME.name} ({len(lines)} linhas)")
    for w in warnings:
        print("  " + w)
    for p in problems:
        print("  " + p)
    print(f"  resumo: {len(problems)} problema(s), {len(warnings)} aviso(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
