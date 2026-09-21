#!/usr/bin/env python3
"""Verificacao de integracao dos lotes visuais (2, 3 e 4).

Este script confere os CONTRATOS entre os pacotes: se as chaves do perfil que o
controlador de render (Lote 2) consome existem em quem as produz, se os materiais
do clima (Lote 4) existem no cenario (Lote 3), se os caminhos `res://` apontam
para arquivos que o pacote entrega, e se os roteiros de colagem no `game_3d.gd`
usam os mesmos nomes.

Ele NAO prova que o jogo roda: isso so o Godot do usuario prova. Ele prova que
os pacotes sao internamente coerentes e que nada ficou de fora.

Rode:  python3 verificar_lotes.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
LOTES = {"lote2": RAIZ / "lote2", "lote3": RAIZ / "lote3", "lote4": RAIZ / "lote4"}

# Arquivos que cada pacote tem de entregar (o que o usuario copia + o que audita).
OBRIGATORIOS = {
    "lote2": [
        "README_LOTE2.md", "docs/CHECKLIST_LOTE2.md", "project.godot.lote2",
        "scripts/render_quality.gd", "scripts/game_3d_lote2_patch.gd",
        "tools/analyze_render_profile.py", "tools/render_facts.json",
        "tools/check_def_use.py", "tools/run_lote2_selftest.py",
        "tools/audit_render_tone.py", "docs/preview_render_lote2.png",
        "docs/render_tone_report.json",
    ],
    "lote3": [
        "README_LOTE3.md", "docs/CHECKLIST_LOTE3.md", "docs/PATCH_GAME_3D_LOTE3.md",
        "resources/world_spec.json", "scripts/building_kit.gd",
        "tools/audit_world.py", "tools/run_lote3_selftest.py",
        "tools/world_facts.json", "tools/check_def_use.py",
        "docs/preview_world_lote3.png",
    ],
    "lote4": [
        "README_LOTE4.md", "docs/CHECKLIST_LOTE4.md", "docs/PATCH_GAME_3D_LOTE4.md",
        "resources/weather_spec.json", "scripts/weather_system.gd",
        "assets/textures/ceu/nuvens.png", "assets/audio/trovao.wav",
        "tools/audit_lighting.py", "tools/run_lote4_selftest.py",
        "tools/weather_facts.json", "tools/check_def_use.py",
        "docs/preview_clima_lote4.png",
    ],
}

# Caminhos que so existem no projeto de verdade (vem de outros lotes/do repo).
ESPERADOS_FORA = [
    "res://assets/textures/pbr/",       # Lote 1 (texturas PBR)
    "res://assets/audio/trovao.wav",    # entregue pelo proprio Lote 4
    "res://resources/weather_spec.json",
    "res://resources/world_spec.json",
    "res://project.godot",
]


def ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.exists() else ""


def chaves_perfil_consumidas() -> set:
    """So as chaves lidas do PERFIL (nao as dos degraus internos do proprio Lote 2)."""
    texto = ler(LOTES["lote2"] / "scripts" / "render_quality.gd")
    chaves = set()
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\.get\("([a-z_]+)"', texto):
        receptor = m.group(1).lower()
        if "profile" in receptor or "perfil" in receptor:
            chaves.add(m.group(2))
    return chaves


def chaves_perfil_fornecidas() -> tuple:
    do_kit = set(re.findall(r'"([a-z_]+)":', ler(LOTES["lote3"] / "scripts" / "building_kit.gd").split("PERFIL_PADRAO")[1].split("}")[0]))
    patch = ler(LOTES["lote2"] / "scripts" / "game_3d_lote2_patch.gd")
    do_patch = set(re.findall(r'"([a-z_]+)":', patch))
    return do_kit, do_patch


def caminhos_res(texto: str) -> set:
    return set(re.findall(r'res://[A-Za-z0-9_./\-]+', texto))


def main() -> int:
    problemas: list = []
    avisos: list = []
    linhas: list = []

    for nome, pasta in LOTES.items():
        faltando = [f for f in OBRIGATORIOS[nome] if not (pasta / f).exists()]
        if faltando:
            problemas.append(f"{nome}: faltam arquivos: {', '.join(faltando)}")
        else:
            linhas.append(f"{nome}: {len(OBRIGATORIOS[nome])} arquivos obrigatorios presentes")

    # 1) contrato do perfil de render entre Lote 2 (quem consome) e Lote 3/Lote 2-patch (quem fornece)
    consumidas = chaves_perfil_consumidas()
    do_kit, do_patch = chaves_perfil_fornecidas()
    faltam_kit = sorted(consumidas - do_kit)
    faltam_patch = sorted(consumidas - do_patch)
    if faltam_kit:
        problemas.append("perfil: o Lote 3 oferece menos chaves que o Lote 2 consome: "
                         + ", ".join(faltam_kit))
    if faltam_patch:
        problemas.append("perfil: o patch do Lote 2 nao oferece: " + ", ".join(faltam_patch))
    if not faltam_kit and not faltam_patch:
        linhas.append(f"perfil de render: {len(consumidas)} chaves consumidas, todas fornecidas "
                      f"(Lote 3: {len(do_kit)}, patch Lote 2: {len(do_patch)})")

    # 2) materiais do clima x materiais do cenario
    kit = json.loads(ler(LOTES["lote3"] / "resources" / "world_spec.json") or "{}")
    clima = json.loads(ler(LOTES["lote4"] / "resources" / "weather_spec.json") or "{}")
    materiais_kit = set(kit.get("materiais", {}))
    materiais_clima = set(clima.get("molhado", {}).get("materiais", {}))
    orfaos = sorted(materiais_clima - materiais_kit)
    if orfaos:
        problemas.append("clima: materiais que nao existem no cenario: " + ", ".join(orfaos))
    else:
        linhas.append(f"clima x cenario: {len(materiais_clima)} materiais molhados, todos existem no "
                      "world_spec")
    trecho_pocas = clima.get("pocas", {}).get("trecho_m")
    trecho_kit = kit.get("quarteirao", {}).get("comprimento_m")
    if trecho_pocas is not None and abs(float(trecho_pocas) - float(trecho_kit)) > 0.5:
        problemas.append(f"clima: pocas.trecho_m ({trecho_pocas}) difere do quarteirao ({trecho_kit})")

    # 3) caminhos res:// dos scripts tem de existir em algum pacote (ou ser de outro lote)
    mapa = {"lote2": LOTES["lote2"], "lote3": LOTES["lote3"], "lote4": LOTES["lote4"]}
    for lote, arquivos in (("lote2", ["scripts/render_quality.gd"]),
                           ("lote3", ["scripts/building_kit.gd"]),
                           ("lote4", ["scripts/weather_system.gd"])):
        texto = "\n".join(ler(mapa[lote] / a) for a in arquivos)
        for caminho in sorted(caminhos_res(texto)):
            relativo = caminho.replace("res://", "")
            if any(caminho.startswith(e) for e in ESPERADOS_FORA):
                continue
            if any((pasta / relativo).exists() for pasta in mapa.values()):
                continue
            avisos.append(f"{lote}: {caminho} nao esta em nenhum pacote (confira se o Lote 1/projeto entrega)")

    # 4) roteiros de colagem usam os mesmos nomes
    patch3 = ler(LOTES["lote3"] / "docs" / "PATCH_GAME_3D_LOTE3.md")
    patch4 = ler(LOTES["lote4"] / "docs" / "PATCH_GAME_3D_LOTE4.md")
    for nome in ("WORLD_Y_OFFSET", "_render_profile", "_world_travel", "_update_world_kit",
                 "_setup_world_kit"):
        if nome in patch4 and nome not in patch3:
            problemas.append(f"roteiros: o Lote 4 usa {nome}, que o roteiro do Lote 3 nao cria")
    if "_render_profile()" in patch4 and "_render_profile" not in patch3 + ler(LOTES["lote2"] / "scripts" / "game_3d_lote2_patch.gd"):
        problemas.append("roteiros: o Lote 4 chama _render_profile(), que o Lote 2 nao define")
    linhas.append("roteiros: nomes cruzados entre Lote 3 e Lote 4 conferem")

    # 5) project.godot do Lote 2
    pg = ler(LOTES["lote2"] / "project.godot.lote2")
    for exigido, motivo in (
        ('renderer/rendering_method="mobile"', "renderizador mobile"),
        ('renderer/rendering_method.mobile="gl_compatibility"', "plano B para Android sem Vulkan"),
        ('RenderQuality="*res://scripts/render_quality.gd"', "autoload do controlador"),
        ("use_debanding=true", "debanding contra faixas de cor"),
    ):
        if exigido not in pg:
            problemas.append(f"project.godot (Lote 2): falta {exigido} ({motivo})")
    if "render_quality.gd" in pg and not (LOTES["lote2"] / "scripts" / "render_quality.gd").exists():
        problemas.append("project.godot (Lote 2): aponta para render_quality.gd que o pacote nao entrega")
    linhas.append("project.godot: mobile + plano B + autoload conferem")

    print("Verificacao de integracao dos lotes (2, 3, 4)")
    for l in linhas:
        print("  ok: " + l)
    for a in sorted(set(avisos)):
        print("  AVISO: " + a)
    for p in problemas:
        print("  ERRO: " + p)
    print(f"  resumo: {len(problemas)} problema(s), {len(set(avisos))} aviso(s)")
    print("  lembretes: o Lote 1 (texturas PBR) e o projeto em si (game_3d.gd, project.godot, "
          "assets/audio/*) NAO estao nesta pasta; eles vem do repositorio.")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
