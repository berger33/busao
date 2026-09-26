#!/usr/bin/env python3
"""Herói 10/10 — Fase 2: UV + bake PBR da heroína Júlia.

Plano: docs/PLANO_HEROI_10_10.md (Fase 2 — UV + bake PBR).
Entrada: tools/blender/out/heroi_julia_base.blend (Fase 1).

O que faz:
  1. Smart UV Project com margem de ilha (corpo inteiro num atlas).
  2. Monta um material de pele **procedural** de alta frequência em Cycles:
     variação de tom, oclusão nas dobras, poro/microrelevo e brilho de suor.
  3. Bakeia albedo, normal, roughness e AO nesse atlas.
  4. Empacota AO+Roughness+Metallic num único **ORM** (padrão glTF).
  5. Reaplica um material final enxuto (Principled com as texturas bakeadas)
     e exporta o GLB com as imagens embarcadas.

Uso:
  tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py [--res 2048] [--samples 24]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
TEX_DIR = REPO / "assets" / "textures" / "heroi"
BASE_BLEND = OUT_DIR / "heroi_julia_base.blend"

# Paleta de pele morena brasileira (linear, não sRGB)
PELE_BASE = (0.352, 0.170, 0.108, 1.0)
PELE_CLARA = (0.480, 0.250, 0.163, 1.0)
PELE_ESCURA = (0.205, 0.092, 0.060, 1.0)


def log(msg):
    print(f"[bake] {msg}", flush=True)


def ativar(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


# -----------------------------------------------------------------------------
# 1. UV
# -----------------------------------------------------------------------------
def desdobrar(obj, margem=0.006):
    ativar(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(64.0),
        island_margin=margem,
        area_weight=0.35,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.0035)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = obj.data.uv_layers.active
    log(f"UV: {uv.name}, {len(uv.data)} loops")
    return obj


def cobertura_uv(obj, res=512):
    """Fração do atlas ocupada — mede desperdício do unwrap."""
    me = obj.data
    uv = me.uv_layers.active.data
    grid = np.zeros((res, res), dtype=bool)
    for poly in me.polygons:
        us, vs = [], []
        for li in poly.loop_indices:
            u, v = uv[li].uv
            us.append(u)
            vs.append(v)
        u0, u1 = int(max(0, min(us) * res)), int(min(res - 1, max(us) * res))
        v0, v1 = int(max(0, min(vs) * res)), int(min(res - 1, max(vs) * res))
        grid[v0:v1 + 1, u0:u1 + 1] = True
    return round(float(grid.mean()), 3)


# -----------------------------------------------------------------------------
# 2. Material procedural de pele (fonte do bake)
# -----------------------------------------------------------------------------
def material_pele_procedural():
    mat = bpy.data.materials.new("PeleProcedural")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    coord = nt.nodes.new("ShaderNodeTexCoord")

    # --- variação macro de tom (manchas suaves, quebra o bege chapado) -------
    noise_macro = nt.nodes.new("ShaderNodeTexNoise")
    noise_macro.inputs["Scale"].default_value = 9.0
    noise_macro.inputs["Detail"].default_value = 4.0
    noise_macro.inputs["Roughness"].default_value = 0.55
    nt.links.new(coord.outputs["Object"], noise_macro.inputs["Vector"])

    ramp_macro = nt.nodes.new("ShaderNodeValToRGB")
    ramp_macro.color_ramp.elements[0].position = 0.38
    ramp_macro.color_ramp.elements[0].color = PELE_ESCURA
    ramp_macro.color_ramp.elements[1].position = 0.68
    ramp_macro.color_ramp.elements[1].color = PELE_CLARA
    nt.links.new(noise_macro.outputs["Fac"], ramp_macro.inputs["Fac"])

    mix_base = nt.nodes.new("ShaderNodeMixRGB")
    mix_base.blend_type = "MIX"
    mix_base.inputs["Fac"].default_value = 0.55
    mix_base.inputs["Color1"].default_value = PELE_BASE
    nt.links.new(ramp_macro.outputs["Color"], mix_base.inputs["Color2"])

    # --- rubor: gradiente vertical quente no rosto/joelho/cotovelo ----------
    grad = nt.nodes.new("ShaderNodeTexNoise")
    grad.inputs["Scale"].default_value = 2.2
    grad.inputs["Detail"].default_value = 2.0
    nt.links.new(coord.outputs["Object"], grad.inputs["Vector"])

    rubor = nt.nodes.new("ShaderNodeMixRGB")
    rubor.blend_type = "SOFT_LIGHT"
    rubor.inputs["Fac"].default_value = 0.22
    rubor.inputs["Color2"].default_value = (0.52, 0.16, 0.13, 1.0)
    nt.links.new(mix_base.outputs["Color"], rubor.inputs["Color1"])
    nt.links.new(grad.outputs["Fac"], rubor.inputs["Fac"])

    # --- microtextura de poro (voronoi fina) --------------------------------
    poro = nt.nodes.new("ShaderNodeTexVoronoi")
    poro.feature = "F1"
    poro.inputs["Scale"].default_value = 420.0
    nt.links.new(coord.outputs["Object"], poro.inputs["Vector"])

    poro_ramp = nt.nodes.new("ShaderNodeValToRGB")
    poro_ramp.color_ramp.elements[0].position = 0.10
    poro_ramp.color_ramp.elements[1].position = 0.55
    nt.links.new(poro.outputs["Distance"], poro_ramp.inputs["Fac"])

    # --- ruído fino para dobras/estrias de pele -----------------------------
    micro = nt.nodes.new("ShaderNodeTexNoise")
    micro.inputs["Scale"].default_value = 120.0
    micro.inputs["Detail"].default_value = 6.0
    nt.links.new(coord.outputs["Object"], micro.inputs["Vector"])

    mistura_relevo = nt.nodes.new("ShaderNodeMixRGB")
    mistura_relevo.blend_type = "OVERLAY"
    mistura_relevo.inputs["Fac"].default_value = 0.6
    nt.links.new(poro_ramp.outputs["Color"], mistura_relevo.inputs["Color1"])
    nt.links.new(micro.outputs["Fac"], mistura_relevo.inputs["Color2"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(mistura_relevo.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # --- roughness variável (testa/nariz mais oleosos que o resto) ----------
    rough_noise = nt.nodes.new("ShaderNodeTexNoise")
    rough_noise.inputs["Scale"].default_value = 26.0
    rough_noise.inputs["Detail"].default_value = 3.0
    nt.links.new(coord.outputs["Object"], rough_noise.inputs["Vector"])

    rough_ramp = nt.nodes.new("ShaderNodeValToRGB")
    rough_ramp.color_ramp.elements[0].position = 0.30
    rough_ramp.color_ramp.elements[0].color = (0.38, 0.38, 0.38, 1.0)  # brilho
    rough_ramp.color_ramp.elements[1].position = 0.80
    rough_ramp.color_ramp.elements[1].color = (0.66, 0.66, 0.66, 1.0)  # fosco
    nt.links.new(rough_noise.outputs["Fac"], rough_ramp.inputs["Fac"])
    nt.links.new(rough_ramp.outputs["Color"], bsdf.inputs["Roughness"])

    nt.links.new(rubor.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.0
    # SSS moderado: pele viva sem virar cera
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.18
        bsdf.inputs["Subsurface Radius"].default_value = (0.012, 0.005, 0.003)
        bsdf.inputs["Subsurface Scale"].default_value = 0.012
    return mat


# -----------------------------------------------------------------------------
# 3. Bake
# -----------------------------------------------------------------------------
def nova_imagem(nome, res, cor=(0, 0, 0, 1), float_buffer=False, nao_cor=True):
    img = bpy.data.images.new(nome, res, res, alpha=False, float_buffer=float_buffer)
    img.generated_color = cor
    if nao_cor:
        img.colorspace_settings.name = "Non-Color"
    return img


def preparar_bake(scene, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.margin = 8
    scene.render.bake.use_clear = True


def bake_canal(obj, mat, img, tipo, scene, **kw):
    nt = mat.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    # O bake escreve no nó de imagem ATIVO **e selecionado** do material.
    # Sem o select a operação roda e não grava nada (imagem fica na cor gerada).
    for n in nt.nodes:
        n.select = False
    node.select = True
    nt.nodes.active = node
    ativar(obj)
    if tipo == "DIFFUSE":
        scene.render.bake.use_pass_direct = False
        scene.render.bake.use_pass_indirect = False
        scene.render.bake.use_pass_color = True
    log(f"bake {tipo} -> {img.name} ({img.size[0]}px)")
    r = bpy.ops.object.bake(type=tipo, **kw)
    if "FINISHED" not in r:
        raise SystemExit(f"bake {tipo} falhou: {r}")
    arr = px(img)
    log(f"  {tipo}: min={arr.min():.3f} max={arr.max():.3f} std={arr.std():.4f}")
    if arr.std() < 1e-5:
        log(f"  AVISO: {tipo} saiu chapado")
    nt.nodes.remove(node)
    return img


def px(img):
    a = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def redimensionar(img, res):
    if img.size[0] != res:
        img.scale(res, res)
    return img


def salvar(img, caminho: Path, srgb=False, qualidade=None):
    """Grava o buffer do bake em disco.

    Cuidado: `Image.save()` numa imagem GENERATED (que é o que o bake usa)
    grava o PADRÃO GERADO, não o resultado do bake — o PNG sai chapado. Por
    isso o buffer é copiado para uma imagem nova via foreach_set antes de
    salvar. Testado: salvar direto -> std 0.000; via cópia -> std 0.234.
    """
    arr = px(img)
    res_y, res_x = arr.shape[0], arr.shape[1]
    copia = bpy.data.images.new(img.name + "_out", res_x, res_y, alpha=False)
    copia.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    copia.pixels.foreach_set(arr.reshape(-1))
    copia.filepath_raw = str(caminho)
    if caminho.suffix.lower() in (".jpg", ".jpeg"):
        copia.file_format = "JPEG"
        bpy.context.scene.render.image_settings.quality = qualidade or 90
    else:
        copia.file_format = "PNG"
    copia.save()
    return copia


def empacotar_orm(ao, rough, res, destino: Path):
    """glTF ORM: R=occlusion, G=roughness, B=metallic."""
    a = px(ao)[:, :, 0]
    r = px(rough)[:, :, 0]
    orm = np.zeros((res, res, 4), dtype=np.float32)
    orm[:, :, 0] = a
    orm[:, :, 1] = r
    orm[:, :, 2] = 0.0   # metallic: pele/roupa de pano não são metal
    orm[:, :, 3] = 1.0
    img = bpy.data.images.new("julia_orm", res, res, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(orm.reshape(-1))
    img.filepath_raw = str(destino)
    img.file_format = "PNG"
    img.save()
    return img


# -----------------------------------------------------------------------------
# 4. Material final (texturas bakeadas) + export
# -----------------------------------------------------------------------------
def material_final(albedo, normal, orm):
    mat = bpy.data.materials.new("PeleJulia")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    t_alb = nt.nodes.new("ShaderNodeTexImage")
    t_alb.image = albedo
    t_alb.image.colorspace_settings.name = "sRGB"
    nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Base Color"])

    t_orm = nt.nodes.new("ShaderNodeTexImage")
    t_orm.image = orm
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t_orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])

    t_nrm = nt.nodes.new("ShaderNodeTexImage")
    t_nrm.image = normal
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nrm.inputs["Strength"].default_value = 0.85
    nt.links.new(t_nrm.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])

    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.15
        bsdf.inputs["Subsurface Radius"].default_value = (0.012, 0.005, 0.003)
        bsdf.inputs["Subsurface Scale"].default_value = 0.010
    return mat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=2048)
    ap.add_argument("--samples", type=int, default=24)
    # Normal/ORM em meia resolução e JPEG: PNG 2K nos três mapas dava GLB de
    # 11,5 MB (teto do plano: 2 MB). Albedo fica em 2K porque é o que a câmera
    # de corrida mostra de perto.
    ap.add_argument("--res-normal", type=int, default=1024)
    ap.add_argument("--qualidade", type=int, default=88)
    args = ap.parse_args([a for a in sys.argv[1:] if not a.endswith(".py")])

    res = args.res
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BASE_BLEND))
    scene = bpy.context.scene
    # A Fase 3 (build_heroi_julia.py) adicionou olhos/cabelo/sobrancelha/cílio
    # como objetos separados — cada um já tem seu próprio material (não
    # dependem de bake Cycles). Só o corpo ("JuliaBase") passa por UV+bake
    # aqui; os extras seguem intactos até o export final.
    obj = scene.objects.get("JuliaBase") or next(o for o in scene.objects if o.type == "MESH")
    extras = [o for o in scene.objects if o.type == "MESH" and o is not obj]
    log(f"objeto: {obj.name}, {len(obj.data.polygons)} faces (+{len(extras)} extras da Fase 3)")

    desdobrar(obj)
    cobertura = cobertura_uv(obj)
    log(f"cobertura do atlas: {cobertura * 100:.1f}%")

    mat = material_pele_procedural()
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    preparar_bake(scene, args.samples)
    img_alb = nova_imagem("julia_albedo", res, (0.5, 0.3, 0.2, 1), nao_cor=False)
    img_nrm = nova_imagem("julia_normal", res, (0.5, 0.5, 1.0, 1))
    img_rgh = nova_imagem("julia_rough", res, (0.5, 0.5, 0.5, 1))
    img_ao = nova_imagem("julia_ao", res, (1, 1, 1, 1))

    bake_canal(obj, mat, img_alb, "DIFFUSE", scene)
    bake_canal(obj, mat, img_nrm, "NORMAL", scene)
    bake_canal(obj, mat, img_rgh, "ROUGHNESS", scene)
    scene.cycles.samples = max(8, args.samples // 2)
    bake_canal(obj, mat, img_ao, "AO", scene)

    orm_full = empacotar_orm(img_ao, img_rgh, res, TEX_DIR / "_orm_tmp.png")
    redimensionar(img_nrm, args.res_normal)
    redimensionar(orm_full, args.res_normal)

    p_alb = TEX_DIR / "julia_albedo.jpg"
    p_nrm = TEX_DIR / "julia_normal.jpg"
    p_orm = TEX_DIR / "julia_orm.jpg"
    alb_out = salvar(img_alb, p_alb, srgb=True, qualidade=args.qualidade)
    nrm_out = salvar(img_nrm, p_nrm, qualidade=max(92, args.qualidade))
    orm = salvar(orm_full, p_orm, qualidade=args.qualidade)
    (TEX_DIR / "_orm_tmp.png").unlink(missing_ok=True)

    final = material_final(alb_out, nrm_out, orm)
    obj.data.materials.clear()
    obj.data.materials.append(final)

    # Export final: corpo texturizado + todos os extras da Fase 3 (eles já
    # trazem seus próprios materiais/imagens do build_heroi_julia.py).
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    for extra in extras:
        extra.select_set(True)
    bpy.context.view_layer.objects.active = obj

    glb = OUT_DIR / "heroi_julia_pbr.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_image_format="JPEG",
        export_jpeg_quality=args.qualidade,
        export_draco_mesh_compression_enable=False,
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_DIR / "heroi_julia_pbr.blend"))

    tris_extras = sum(sum(len(p.vertices) - 2 for p in e.data.polygons) for e in extras)
    faces_extras = sum(len(e.data.polygons) for e in extras)
    m = {
        "res": res,
        "samples": args.samples,
        "faces_corpo": len(obj.data.polygons),
        "faces_extras": faces_extras,
        "tris_extras": tris_extras,
        "extras": sorted(e.name for e in extras),
        "cobertura_uv": cobertura,
        "res_normal_orm": args.res_normal,
        "texturas": [p_alb.name, p_nrm.name, p_orm.name],
        "kb_albedo": round(p_alb.stat().st_size / 1024, 1),
        "kb_normal": round(p_nrm.stat().st_size / 1024, 1),
        "kb_orm": round(p_orm.stat().st_size / 1024, 1),
        "glb_kb": round(glb.stat().st_size / 1024, 1),
    }
    m["gate_texturas"] = len(m["texturas"]) >= 3
    m["gate_cobertura"] = cobertura >= 0.45
    m["gate_glb"] = m["glb_kb"] <= 2048
    m["gate"] = all(m[k] for k in ("gate_texturas", "gate_cobertura", "gate_glb"))
    (OUT_DIR / "heroi_julia_pbr_metrics.json").write_text(json.dumps(m, indent=2))
    log(json.dumps(m, indent=2))
    return 0 if m["gate"] else 1


if __name__ == "__main__":
    sys.exit(main())
