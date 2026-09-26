#!/usr/bin/env python3
"""Herói 10/10 — Fase 1: corpo base esculpido da heroína Júlia.

Plano: docs/PLANO_HEROI_10_10.md (Fase 1 — Corpo base esculpido).
Referência visual: docs/arte_alvo_final/6_model_sheet_heroi.png

Por que um script novo em vez de corrigir `build_humanos.py`: aquele pipeline
gera membros por revolução de anéis (tubos lofted), sem edge loops de
deformação e com UV que estica em qualquer bake. Aqui o corpo nasce de um
esqueleto de arestas + modificador Skin (volume orgânico contínuo), passa por
Subdivision e é **retopologizado por QuadriFlow** em quads distribuídos, o que
dá loops utilizáveis em cotovelo, joelho, ombro e quadril.

Saídas (em tools/blender/out/):
  heroi_julia_base.glb    corpo base sem rig (Fase 4 adiciona armature)
  heroi_julia_base.blend  cena para iteração
  heroi_julia_metrics.json métricas do gate da Fase 1

Uso: tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

TAU = math.tau
D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Alvos do gate da Fase 1 -------------------------------------------------
ALTURA_ALVO = 1.72          # m, heroína adulta (model sheet: 168-172 cm)
PISO_OFFSET = 0.012         # m, contato da sola (mesmo contrato do runner atual)
TRIS_ALVO = 32000           # 28k-45k
TRIS_MIN, TRIS_MAX = 24000, 46000
QUADRIFLOW_FACES = 9000    # quads -> ~26k tris antes do detalhe das mãos

# --- Proporções (metros, personagem em pé, Z para cima, frente = -Y) ---------
# 7,5 cabeças: cabeça ~0,229 m. Valores em altura absoluta.
Z_TOPO = 1.720
Z_QUEIXO = 1.495
Z_PESCOCO = 1.425
Z_OMBRO = 1.400
Z_PEITO = 1.290
Z_COSTELA = 1.180
Z_CINTURA = 1.060
Z_QUADRIL = 0.955
Z_VIRILHA = 0.880
Z_COXA_MEIO = 0.690
Z_JOELHO = 0.470
Z_PANTURRILHA = 0.330
Z_TORNOZELO = 0.095
Z_PE = 0.030

X_OMBRO = 0.188
X_COTOVELO = 0.205
X_PUNHO = 0.215
X_QUADRIL = 0.095
X_JOELHO = 0.090
X_TORNOZELO = 0.075

Z_COTOVELO = 1.120
Z_PUNHO = 0.870
Z_MAO = 0.790


def log(msg: str) -> None:
    print(f"[heroi] {msg}", flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def ativar(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def material(nome, cor, rough=0.60, metal=0.0):
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# -----------------------------------------------------------------------------
# 1. Esqueleto de arestas com raios por junta (entrada do modificador Skin)
# -----------------------------------------------------------------------------
# Cada nó: nome -> (posição, raio). As arestas ligam nós em cadeia.
def esqueleto_corpo():
    """Retorna (vertices, arestas, raios) do grafo que vira volume no Skin."""
    nos = {}

    def no(nome, pos, raio):
        nos[nome] = (Vector(pos), raio)
        return nome

    # Tronco (cadeia central, y levemente para trás nas costas)
    no("pelvis", (0.0, 0.010, Z_QUADRIL), 0.108)
    no("cintura", (0.0, 0.000, Z_CINTURA), 0.093)
    no("costela", (0.0, -0.008, Z_COSTELA), 0.107)
    no("peito", (0.0, -0.012, Z_PEITO), 0.115)
    no("ombro_c", (0.0, -0.006, Z_OMBRO), 0.112)
    no("pescoco", (0.0, 0.006, Z_PESCOCO), 0.052)
    # Cabeça = 1/7,5 da altura (~0,229 m): mandíbula, face, crânio e topo.
    no("mandibula", (0.0, -0.014, Z_QUEIXO + 0.004), 0.078)
    no("face", (0.0, -0.008, 1.556), 0.100)
    no("cranio", (0.0, 0.012, 1.614), 0.107)
    no("topo", (0.0, 0.008, 1.664), 0.082)

    arestas = [
        ("pelvis", "cintura"), ("cintura", "costela"), ("costela", "peito"),
        ("peito", "ombro_c"), ("ombro_c", "pescoco"), ("pescoco", "mandibula"),
        ("mandibula", "face"), ("face", "cranio"), ("cranio", "topo"),
    ]

    for lado, s in (("l", 1.0), ("r", -1.0)):
        # Braço: clavícula -> ombro -> cotovelo -> punho -> mão
        no(f"clav_{lado}", (s * 0.062, -0.012, Z_OMBRO + 0.014), 0.072)
        no(f"ombro_{lado}", (s * X_OMBRO, -0.004, Z_OMBRO - 0.014), 0.068)
        no(f"braco_{lado}", (s * (X_OMBRO + 0.014), 0.000, 1.258), 0.054)
        no(f"cotovelo_{lado}", (s * X_COTOVELO, 0.004, Z_COTOVELO), 0.047)
        no(f"antebraco_{lado}", (s * (X_COTOVELO + 0.008), 0.002, 0.995), 0.043)
        no(f"punho_{lado}", (s * X_PUNHO, 0.000, Z_PUNHO), 0.032)
        no(f"palma_{lado}", (s * (X_PUNHO + 0.004), -0.006, Z_MAO), 0.040)
        arestas += [
            ("ombro_c", f"clav_{lado}"), (f"clav_{lado}", f"ombro_{lado}"),
            (f"ombro_{lado}", f"braco_{lado}"), (f"braco_{lado}", f"cotovelo_{lado}"),
            (f"cotovelo_{lado}", f"antebraco_{lado}"), (f"antebraco_{lado}", f"punho_{lado}"),
            (f"punho_{lado}", f"palma_{lado}"),
        ]

        # Perna: quadril -> coxa -> joelho -> panturrilha -> tornozelo -> pé
        no(f"quadril_{lado}", (s * X_QUADRIL, 0.006, Z_VIRILHA + 0.045), 0.104)
        no(f"coxa_{lado}", (s * (X_QUADRIL + 0.004), 0.004, Z_COXA_MEIO), 0.093)
        no(f"joelho_{lado}", (s * X_JOELHO, 0.002, Z_JOELHO), 0.066)
        no(f"pantur_{lado}", (s * (X_JOELHO - 0.002), -0.012, Z_PANTURRILHA), 0.068)
        no(f"tornozelo_{lado}", (s * X_TORNOZELO, 0.006, Z_TORNOZELO), 0.042)
        no(f"calcanhar_{lado}", (s * X_TORNOZELO, 0.052, Z_PE + 0.016), 0.043)
        no(f"pe_{lado}", (s * X_TORNOZELO, -0.090, Z_PE + 0.004), 0.048)
        no(f"dedos_{lado}", (s * X_TORNOZELO, -0.152, Z_PE - 0.004), 0.036)
        arestas += [
            ("pelvis", f"quadril_{lado}"), (f"quadril_{lado}", f"coxa_{lado}"),
            (f"coxa_{lado}", f"joelho_{lado}"), (f"joelho_{lado}", f"pantur_{lado}"),
            (f"pantur_{lado}", f"tornozelo_{lado}"),
            (f"tornozelo_{lado}", f"calcanhar_{lado}"),
            (f"tornozelo_{lado}", f"pe_{lado}"), (f"pe_{lado}", f"dedos_{lado}"),
        ]

    return nos, arestas


def criar_base_skin():
    """Grafo -> malha volumétrica contínua via modificador Skin + Subsurf."""
    nos, arestas = esqueleto_corpo()
    ordem = list(nos.keys())
    idx = {n: i for i, n in enumerate(ordem)}
    verts = [nos[n][0] for n in ordem]
    edges = [(idx[a], idx[b]) for a, b in arestas]

    me = D.meshes.new("JuliaBase")
    me.from_pydata([tuple(v) for v in verts], edges, [])
    me.update()
    obj = D.objects.new("JuliaBase", me)
    bpy.context.scene.collection.objects.link(obj)
    ativar(obj)

    mod = obj.modifiers.new("Skin", "SKIN")
    mod.use_smooth_shade = True
    mod.branch_smoothing = 0.35

    skin_layer = me.skin_vertices[0].data
    for n, i in idx.items():
        r = nos[n][1]
        # Achatamento anteroposterior/lateral por região: o Skin é radial,
        # então o ajuste fino de seção vem do lattice/shape depois.
        skin_layer[i].radius = (r, r)
    # Raiz do skin no pelvis (evita ilhas soltas)
    skin_layer[idx["pelvis"]].use_root = True

    sub = obj.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2

    bpy.ops.object.modifier_apply(modifier="Skin")
    bpy.ops.object.modifier_apply(modifier="Subsurf")
    log(f"base skin+subsurf: {len(obj.data.polygons)} faces")
    return obj


# -----------------------------------------------------------------------------
# 2. Seções anatômicas: o Skin gera seção circular; aqui achatamos peito/costas,
#    cabeça e pés para a silhueta deixar de ser tubo.
# -----------------------------------------------------------------------------
def moldar_secoes(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    for v in bm.verts:
        x, y, z = v.co

        # Tronco: elipse (mais largo que profundo) e caixa torácica marcada
        if Z_VIRILHA < z < Z_OMBRO + 0.02:
            t = (z - Z_VIRILHA) / (Z_OMBRO + 0.02 - Z_VIRILHA)
            largura = 1.06 + 0.16 * math.sin(math.pi * min(1.0, t * 1.15))
            profundidade = 0.93 + 0.07 * t
            v.co.x = x * largura
            v.co.y = y * profundidade
            # Cintura mais estreita (silhueta feminina atlética)
            if Z_CINTURA - 0.10 < z < Z_CINTURA + 0.09:
                k = 1.0 - 0.13 * math.cos((z - Z_CINTURA) / 0.10 * math.pi * 0.5)
                v.co.x *= k
                v.co.y *= k * 0.98

        # Quadril levemente mais largo que a cintura
        if Z_VIRILHA - 0.02 < z < Z_QUADRIL + 0.05:
            v.co.x *= 1.05

        # Crânio: ovoide, não esfera; nuca para trás e testa reta
        if z > Z_QUEIXO - 0.02:
            v.co.x *= 0.88          # crânio mais estreito que profundo
            v.co.y = y * 1.10 - 0.004
            if y > 0:               # nuca projetada para trás
                v.co.y = v.co.y * 1.08

        # Pés: achatar no eixo Z, alargar a planta e endireitar o peito do pé
        if z < Z_TORNOZELO:
            t_pe = 1.0 - max(0.0, (z - Z_PE) / max(1e-4, Z_TORNOZELO - Z_PE))
            v.co.z = Z_PE + (z - Z_PE) * 0.50
            v.co.x *= 1.0 + 0.22 * t_pe
            if y < -0.03:   # antepé/dedos mais largos que o calcanhar
                v.co.x *= 1.12

        # Mãos: achatar a palma (prepara os dedos da Fase 1b)
        if abs(z - Z_MAO) < 0.06 and abs(x) > X_PUNHO - 0.06:
            v.co.y = y * 0.62

    bm.to_mesh(me)
    bm.free()
    me.update()
    return obj


# -----------------------------------------------------------------------------
# 3. Retopologia QuadriFlow -> quads distribuídos com loops de deformação
# -----------------------------------------------------------------------------
def retopo(obj, faces=QUADRIFLOW_FACES):
    ativar(obj)
    try:
        bpy.ops.object.quadriflow_remesh(
            use_mesh_symmetry=True,
            use_preserve_sharp=False,
            use_preserve_boundary=False,
            preserve_attributes=False,
            smooth_normals=True,
            mode="FACES",
            target_faces=faces,
        )
        log(f"quadriflow: {len(obj.data.polygons)} faces")
    except Exception as exc:  # pragma: no cover - depende do build do bpy
        log(f"quadriflow indisponível ({exc}); caindo para decimate")
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = min(1.0, faces * 2.0 / max(1, len(obj.data.polygons)))
        ativar(obj)
        bpy.ops.object.modifier_apply(modifier="Decimate")
    return obj


def suavizar(obj, fator=0.55, repeticoes=8):
    """Corrective Smooth: tira o facetado do QuadriFlow sem encolher o volume
    (o Smooth comum derretia coxa/panturrilha e deixava a perna de palito)."""
    ativar(obj)
    mod = obj.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
    mod.factor = fator
    mod.iterations = repeticoes
    mod.smooth_type = "LENGTH_WEIGHTED"
    mod.use_only_smooth = True
    bpy.ops.object.modifier_apply(modifier="Smooth")
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


# -----------------------------------------------------------------------------
# 4. Loops extras nas juntas (o gate pede 3 loops em cotovelo/joelho)
# -----------------------------------------------------------------------------
def loops_de_deformacao(obj):
    """Subdivide anéis de faces próximos às juntas para densificar a deformação."""
    juntas = [
        (Z_COTOVELO, 0.055), (Z_JOELHO, 0.060), (Z_OMBRO - 0.01, 0.060),
        (Z_VIRILHA + 0.03, 0.055), (Z_PUNHO, 0.040), (Z_TORNOZELO, 0.045),
    ]
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    alvo = set()
    for f in bm.faces:
        z = f.calc_center_median().z
        for zj, raio in juntas:
            if abs(z - zj) <= raio:
                alvo.add(f)
                break
    if alvo:
        bmesh.ops.subdivide_edges(
            bm,
            edges=list({e for f in alvo for e in f.edges}),
            cuts=1,
            use_grid_fill=True,
        )
    bm.to_mesh(me)
    bm.free()
    me.update()
    log(f"loops de deformação: {len(me.polygons)} faces")
    return obj


# -----------------------------------------------------------------------------
# 4b. Mãos: 5 dedos separados (o Skin do corpo só entrega a palma como bloco)
# -----------------------------------------------------------------------------
# Dedo = 3 falanges em cápsulas levemente cônicas, ligadas à palma. Cada dedo
# é uma ilha fechada — o rig da Fase 4 usa thumb/index/middle/ring/pinky_01..03.
DEDOS = [
    # (nome, offset_x_na_palma, offset_y, comprimento, raio_base)
    ("index", 0.019, -0.014, 0.066, 0.0104),
    ("middle", 0.006, -0.016, 0.071, 0.0108),
    ("ring", -0.007, -0.014, 0.065, 0.0100),
    ("pinky", -0.019, -0.009, 0.052, 0.0088),
]
POLEGAR = ("thumb", 0.026, 0.008, 0.052, 0.0116)


def _capsula(nome, p0, p1, r0, r1, seg=8):
    """Tronco de cone fechado entre dois pontos (falange)."""
    p0, p1 = Vector(p0), Vector(p1)
    eixo = (p1 - p0)
    comp = eixo.length
    quat = eixo.to_track_quat("Z", "Y")
    me = D.meshes.new(nome)
    verts, faces = [], []
    for i, (r, z) in enumerate(((r0, 0.0), (r1, comp))):
        for k in range(seg):
            a = k / seg * TAU
            local = Vector((r * math.cos(a), r * math.sin(a), z))
            verts.append(tuple(p0 + quat @ local))
    for k in range(seg):
        kn = (k + 1) % seg
        faces.append((k, kn, seg + kn, seg + k))
    base = len(verts)
    verts.append(tuple(p0))
    verts.append(tuple(p1))
    for k in range(seg):
        kn = (k + 1) % seg
        faces.append((base, kn, k))
        faces.append((base + 1, seg + k, seg + kn))
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def criar_maos():
    """Gera 10 dedos (3 falanges cada) posicionados nas palmas."""
    pecas = []
    for lado, s in (("l", 1.0), ("r", -1.0)):
        palma_x = s * (X_PUNHO + 0.004)
        for nome, dx, dy, comp, raio in DEDOS + [POLEGAR]:
            polegar = nome == "thumb"
            x = palma_x + s * dx
            y = -0.006 + dy
            z_top = Z_MAO + (0.010 if polegar else 0.002)
            # 3 falanges: 45% / 32% / 23% do comprimento
            fracoes = (0.45, 0.32, 0.23)
            z = z_top
            r = raio
            for i, f in enumerate(fracoes):
                comp_f = comp * f
                if polegar:
                    # polegar aponta para frente/baixo, afastado da palma
                    p0 = (x + s * 0.005 * i, y - 0.012 * i, z)
                    p1 = (x + s * 0.005 * (i + 1), y - 0.012 * (i + 1), z - comp_f)
                else:
                    # leve curl: cada falange avança para frente (mão relaxada)
                    p0 = (x, y - 0.007 * i, z)
                    p1 = (x, y - 0.007 * (i + 1), z - comp_f)
                r_next = r * 0.88
                pecas.append(_capsula(f"{nome}_{i+1:02d}_{lado}", p0, p1, r, r_next))
                z -= comp_f
                r = r_next
    return pecas


def juntar(corpo, pecas):
    ativar(corpo)
    for p in pecas:
        p.select_set(True)
    bpy.context.view_layer.objects.active = corpo
    bpy.ops.object.join()
    log(f"mãos unidas: {len(corpo.data.polygons)} faces")
    return corpo


# -----------------------------------------------------------------------------
# 5. Normalização de escala e contato com o solo
# -----------------------------------------------------------------------------
def normalizar(obj, altura=ALTURA_ALVO, piso=PISO_OFFSET):
    ativar(obj)
    bpy.context.view_layer.update()
    zs = [(obj.matrix_world @ v.co).z for v in obj.data.vertices]
    z_min, z_max = min(zs), max(zs)
    escala = altura / (z_max - z_min)
    obj.scale = (escala, escala, escala)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    zs = [(obj.matrix_world @ v.co).z for v in obj.data.vertices]
    obj.location.z += piso - min(zs)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return obj


def metricas(obj):
    me = obj.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
    zs = [v.co.z for v in me.vertices]
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    nao_manifold = 0
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) != 2:
            nao_manifold += 1
    bm.free()
    return {
        "verts": len(me.vertices),
        "faces": len(me.polygons),
        "tris": tris,
        "quads_pct": round(100.0 * quads / max(1, len(me.polygons)), 1),
        "altura_m": round(max(zs) - min(zs), 4),
        "piso_z_m": round(min(zs), 4),
        "largura_m": round(max(xs) - min(xs), 4),
        "profundidade_m": round(max(ys) - min(ys), 4),
        "arestas_nao_manifold": nao_manifold,
    }


def exportar(obj, nome="heroi_julia_base"):
    mat = material("PeleJulia", (0.74, 0.52, 0.40), rough=0.52)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    ativar(obj)
    glb = OUT_DIR / f"{nome}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_draco_mesh_compression_enable=False,  # Godot 4 não decodifica Draco
    )
    blend = OUT_DIR / f"{nome}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    return glb, blend


def main():
    reset()
    log("Fase 1 — corpo base da heroína Júlia")
    corpo = criar_base_skin()
    moldar_secoes(corpo)
    retopo(corpo)
    suavizar(corpo)
    loops_de_deformacao(corpo)
    juntar(corpo, criar_maos())
    normalizar(corpo)

    m = metricas(corpo)
    glb, blend = exportar(corpo)
    m["glb_kb"] = round(glb.stat().st_size / 1024, 1)
    m["gate_tris"] = TRIS_MIN <= m["tris"] <= TRIS_MAX
    m["gate_altura"] = 1.70 <= m["altura_m"] <= 1.75
    m["gate_piso"] = abs(m["piso_z_m"] - PISO_OFFSET) < 0.005
    m["gate_manifold"] = m["arestas_nao_manifold"] == 0
    m["gate"] = all(m[k] for k in ("gate_tris", "gate_altura", "gate_piso", "gate_manifold"))

    (OUT_DIR / "heroi_julia_metrics.json").write_text(json.dumps(m, indent=2))
    log(json.dumps(m, indent=2))
    log(f"GLB: {glb}")
    log(f"BLEND: {blend}")
    return 0 if m["gate"] else 1


if __name__ == "__main__":
    sys.exit(main())
