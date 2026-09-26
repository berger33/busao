#!/usr/bin/env python3
"""Herói 10/10 — Fase 1-3: corpo, rosto, olhos e cabelo da heroína Júlia.

Plano: docs/PLANO_HEROI_10_10.md (Fase 1 — Corpo base esculpido; Fase 3 —
cabelo e olhos). Referência visual: docs/arte_alvo_final/6_model_sheet_heroi.png

Por que um script novo em vez de corrigir `build_humanos.py`: aquele pipeline
gera membros por revolução de anéis (tubos lofted), sem edge loops de
deformação e com UV que estica em qualquer bake. Aqui o corpo nasce de um
esqueleto de arestas + modificador Skin (volume orgânico contínuo), passa por
Subdivision e é **retopologizado por QuadriFlow** em quads distribuídos, o que
dá loops utilizáveis em cotovelo, joelho, ombro e quadril.

A Fase 3 (seção "6" abaixo) adiciona objetos separados do corpo — olhos
(esclera+córnea), sobrancelhas, cílios e cabelo — cada um com seu próprio
material. Eles nascem no MESMO espaço de coordenadas pré-normalização do
corpo (ver `ROSTO` em "4c") e recebem a mesma escala/deslocamento em
`normalizar()`, então ficam alinhados ao rosto esculpido sem precisar de
parenting nem de re-hierarquia.

Saídas (em tools/blender/out/):
  heroi_julia_base.glb    corpo+rosto+olhos+cabelo sem rig (Fase 4 adiciona armature)
  heroi_julia_base.blend  cena para iteração
  heroi_julia_metrics.json métricas do gate da Fase 1/3

Texturas novas da Fase 3 (não dependem de bake Cycles — são geradas por numpy
e gravadas direto, o bake da Fase 2 continua bakeando só a pele):
  assets/textures/heroi/julia_cabelo_alpha.png  atlas de cartões com alpha (cabelo/sobrancelha/cílio)
  assets/textures/heroi/julia_olho_albedo.jpg   esclera + íris
  assets/textures/heroi/julia_olho_normal.jpg   normal radial da íris

Uso: tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

TAU = math.tau
D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TEX_DIR = REPO / "assets" / "textures" / "heroi"
TEX_DIR.mkdir(parents=True, exist_ok=True)

# --- Alvos do gate da Fase 1 -------------------------------------------------
ALTURA_ALVO = 1.72          # m, heroína adulta (model sheet: 168-172 cm)
PISO_OFFSET = 0.012         # m, contato da sola (mesmo contrato do runner atual)
TRIS_ALVO = 32000           # 28k-45k
TRIS_MIN, TRIS_MAX = 24000, 46000
QUADRIFLOW_FACES = 7600    # quads -> ~32k tris depois dos loops de junta e das mãos

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
X_COTOVELO = 0.212   # derivado: mantido só para referência de documentação
X_PUNHO = 0.243
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
        # Braço: clavícula -> ombro -> cotovelo -> punho -> mão.
        # Todos os nós do braço ficam sobre a MESMA reta ombro→punho (A-pose
        # com ~6° de abertura). Antes cada nó tinha um X escolhido à mão e a
        # cadeia serpenteava: o cotovelo saía para fora e o antebraço voltava,
        # o que lia como braço torto/quebrado no turnaround.
        def _braco(t):
            """Ponto na reta ombro→punho (t=0 ombro, t=1 punho)."""
            x = X_OMBRO + (X_PUNHO - X_OMBRO) * t
            z = (Z_OMBRO - 0.014) + (Z_PUNHO - (Z_OMBRO - 0.014)) * t
            # leve arco para trás no cotovelo (y positivo = costas)
            y = -0.004 + 0.012 * math.sin(math.pi * t)
            return (s * x, y, z)

        no(f"clav_{lado}", (s * 0.062, -0.012, Z_OMBRO + 0.014), 0.072)
        no(f"ombro_{lado}", _braco(0.00), 0.068)
        no(f"braco_{lado}", _braco(0.27), 0.054)
        no(f"cotovelo_{lado}", _braco(0.52), 0.047)
        no(f"antebraco_{lado}", _braco(0.76), 0.042)
        no(f"punho_{lado}", _braco(1.00), 0.031)
        # A palma NÃO é mais um nó do Skin (virava bola solta): agora é uma
        # laje modelada em criar_maos(), encaixada no punho.
        arestas += [
            ("ombro_c", f"clav_{lado}"), (f"clav_{lado}", f"ombro_{lado}"),
            (f"ombro_{lado}", f"braco_{lado}"), (f"braco_{lado}", f"cotovelo_{lado}"),
            (f"cotovelo_{lado}", f"antebraco_{lado}"), (f"antebraco_{lado}", f"punho_{lado}"),
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

        # Máscara lateral do tronco: sem ela a elipse do tórax também puxava os
        # vértices do BRAÇO (mesma faixa de altura), empurrando cotovelo e
        # antebraço para fora — era a origem dos "braços tortos".
        # 1.0 no eixo do corpo, 0.0 a partir de onde o braço começa.
        largura_tronco = 0.135
        feather = 0.055
        m_tronco = 1.0 - min(1.0, max(0.0, (abs(x) - largura_tronco) / feather))

        # Tronco: elipse (mais largo que profundo) e caixa torácica marcada
        if Z_VIRILHA < z < Z_OMBRO + 0.02 and m_tronco > 0.0:
            t = (z - Z_VIRILHA) / (Z_OMBRO + 0.02 - Z_VIRILHA)
            largura = 1.0 + (0.06 + 0.16 * math.sin(math.pi * min(1.0, t * 1.15))) * m_tronco
            profundidade = 1.0 - (0.07 - 0.07 * t) * m_tronco
            v.co.x = x * largura
            v.co.y = y * profundidade
            # Cintura mais estreita (silhueta feminina atlética)
            if Z_CINTURA - 0.10 < z < Z_CINTURA + 0.09:
                k = 1.0 - 0.13 * m_tronco * math.cos((z - Z_CINTURA) / 0.10 * math.pi * 0.5)
                v.co.x *= k
                v.co.y *= k * (1.0 - 0.02 * m_tronco)

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

        # (a palma agora é malha própria em criar_maos(); nada a achatar aqui)

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
    ("index", 0.027, -0.004, 0.070, 0.0095),
    ("middle", 0.009, -0.006, 0.076, 0.0100),
    ("ring", -0.009, -0.005, 0.069, 0.0093),
    ("pinky", -0.026, -0.002, 0.055, 0.0081),
]
POLEGAR = ("thumb", 0.036, -0.002, 0.056, 0.0112)


def _capsula(nome, p0, p1, r0, r1, seg=10):
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


def _laje_palma(nome, centro, largura, espessura, comprimento, seg=14):
    """Palma: tubo elíptico achatado e afunilado (punho -> nós dos dedos)."""
    cx, cy, cz = centro
    perfis = [
        (0.00, largura * 0.40, espessura * 0.46),   # encaixe no punho
        (0.30, largura * 0.50, espessura * 0.50),
        (0.72, largura * 0.50, espessura * 0.45),
        (1.00, largura * 0.46, espessura * 0.38),   # linha dos nós
    ]
    me = D.meshes.new(nome)
    verts, faces = [], []
    for t, rx, ry in perfis:
        z = cz - comprimento * t
        for k in range(seg):
            a = k / seg * TAU
            verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    for i in range(len(perfis) - 1):
        v0, v1 = i * seg, (i + 1) * seg
        for k in range(seg):
            kn = (k + 1) % seg
            faces.append((v0 + k, v0 + kn, v1 + kn, v1 + k))
    topo = len(verts)
    verts.append((cx, cy, cz))
    base = len(verts)
    verts.append((cx, cy, cz - comprimento))
    ult = (len(perfis) - 1) * seg
    for k in range(seg):
        kn = (k + 1) % seg
        faces.append((topo, kn, k))
        faces.append((base, ult + k, ult + kn))
    me.from_pydata(verts, [], faces)
    me.update()
    for f in me.polygons:
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def criar_maos():
    """Palma + 5 dedos por mão, todos partindo da linha dos nós da palma."""
    pecas = []
    largura = 0.082      # mão de mulher adulta: ~8,2 cm de largura
    espessura = 0.030
    comprimento = 0.060  # do punho até os nós
    for lado, s in (("l", 1.0), ("r", -1.0)):
        px_ = s * (X_PUNHO + 0.004)
        py_ = -0.012
        # começa ACIMA do nó do punho para a laje penetrar o antebraço
        # (sem isso aparecia a tampa chata da palma flutuando abaixo do braço)
        z_punho = Z_PUNHO - 0.004
        pecas.append(_laje_palma(f"palma_{lado}", (px_, py_, z_punho),
                                 largura, espessura, comprimento))
        z_nos = z_punho - comprimento

        for nome, dx, dy, comp, raio in DEDOS:
            x = px_ + s * dx
            y = py_ + dy
            # começa 8 mm acima da linha dos nós: o dedo nasce dentro da palma
            z = z_nos + 0.008
            r = raio
            for i, f in enumerate((0.45, 0.32, 0.23)):
                comp_f = comp * f
                p0 = (x, y - 0.006 * i, z)
                p1 = (x, y - 0.006 * (i + 1), z - comp_f)
                r_next = r * 0.87
                pecas.append(_capsula(f"{nome}_{i+1:02d}_{lado}", p0, p1, r, r_next))
                z -= comp_f
                r = r_next

        # Polegar: sai da LATERAL da palma, apontando para frente e para baixo
        nome, dx, dy, comp, raio = POLEGAR
        x = px_ + s * dx
        y = py_ + dy
        z = z_punho - 0.014
        r = raio
        for i, f in enumerate((0.42, 0.33, 0.25)):
            comp_f = comp * f
            p0 = (x + s * 0.008 * i, y - 0.013 * i, z)
            p1 = (x + s * 0.008 * (i + 1), y - 0.013 * (i + 1), z - comp_f * 0.82)
            r_next = r * 0.86
            pecas.append(_capsula(f"{nome}_{i+1:02d}_{lado}", p0, p1, r, r_next))
            z -= comp_f * 0.82
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
# 4c. Rosto (Fase 3): densificar o crânio e esculpir órbita, nariz, boca e queixo
# -----------------------------------------------------------------------------
# Marcos anatômicos no espaço do build (frente = -Y), antes da normalização.
ROSTO = {
    "olho_z": 1.588, "olho_x": 0.034, "olho_y": -0.080,
    "sobrancelha_z": 1.610,
    "nariz_z": 1.560, "nariz_y": -0.104,
    "boca_z": 1.526, "boca_y": -0.092,
    "queixo_z": 1.497,
    "maca_z": 1.566, "maca_x": 0.058,
}


def densificar_cabeca(obj, z_min=1.470, cortes=1):
    """Subdivide só as faces do crânio: o QuadriFlow distribui triângulos por
    área e a cabeça fica grossa demais para receber órbita/nariz/boca."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    faces = [f for f in bm.faces if f.calc_center_median().z > z_min]
    if faces:
        bmesh.ops.subdivide_edges(
            bm,
            edges=list({e for f in faces for e in f.edges}),
            cuts=cortes,
            use_grid_fill=True,
        )
    bm.to_mesh(me)
    bm.free()
    me.update()
    log(f"crânio densificado: {len(me.polygons)} faces")
    return obj


def _gauss(v, centro, raios):
    """Peso 0..1 com queda gaussiana elíptica em torno de um marco do rosto."""
    dx = (v.x - centro[0]) / raios[0]
    dy = (v.y - centro[1]) / raios[1]
    dz = (v.z - centro[2]) / raios[2]
    d2 = dx * dx + dy * dy + dz * dz
    return math.exp(-d2 * 2.2)


def esculpir_rosto(obj):
    """Órbita ocular escavada, arco superciliar, nariz, lábios e queixo.

    Tudo por deslocamento gaussiano: cada marco empurra os vértices próximos
    numa direção, com queda suave — o equivalente procedural do pincel de
    escultura com falloff.
    """
    R = ROSTO
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    # (centro, raios, direção, amplitude)
    brushes = []
    for s in (1.0, -1.0):
        # órbita: empurra para DENTRO (y positivo = costas)
        brushes.append(((s * R["olho_x"], R["olho_y"], R["olho_z"]),
                        (0.030, 0.030, 0.019), (0.0, 1.0, 0.0), 0.0135))
        # arco superciliar: volume para fora, acima da órbita
        brushes.append(((s * R["olho_x"], R["olho_y"] - 0.004, R["sobrancelha_z"]),
                        (0.036, 0.030, 0.011), (0.0, -1.0, 0.0), 0.0070))
        # maçã do rosto
        brushes.append(((s * R["maca_x"], -0.062, R["maca_z"]),
                        (0.028, 0.034, 0.024), (0.0, -1.0, 0.0), 0.0055))
    # dorso do nariz
    brushes.append(((0.0, R["nariz_y"], R["nariz_z"] + 0.022),
                    (0.013, 0.030, 0.026), (0.0, -1.0, 0.0), 0.0130))
    # ponta do nariz
    brushes.append(((0.0, R["nariz_y"], R["nariz_z"]),
                    (0.014, 0.026, 0.011), (0.0, -1.0, 0.0), 0.0185))
    # asas do nariz
    for s in (1.0, -1.0):
        brushes.append(((s * 0.016, R["nariz_y"] + 0.006, R["nariz_z"] - 0.006),
                        (0.010, 0.020, 0.008), (s * 1.0, -0.4, 0.0), 0.0075))
    # lábio superior e inferior
    brushes.append(((0.0, R["boca_y"], R["boca_z"] + 0.007),
                    (0.024, 0.024, 0.007), (0.0, -1.0, 0.0), 0.0075))
    brushes.append(((0.0, R["boca_y"], R["boca_z"] - 0.008),
                    (0.022, 0.024, 0.008), (0.0, -1.0, 0.0), 0.0070))
    # fenda da boca (entra)
    brushes.append(((0.0, R["boca_y"] - 0.004, R["boca_z"]),
                    (0.026, 0.020, 0.0030), (0.0, 1.0, 0.0), 0.0055))
    # queixo e sulco mentolabial
    brushes.append(((0.0, -0.086, R["queixo_z"]),
                    (0.024, 0.030, 0.018), (0.0, -1.0, 0.0), 0.0090))
    brushes.append(((0.0, -0.086, R["queixo_z"] + 0.016),
                    (0.020, 0.024, 0.007), (0.0, 1.0, 0.0), 0.0040))
    # orelhas
    for s in (1.0, -1.0):
        brushes.append(((s * 0.092, 0.006, 1.572),
                        (0.014, 0.020, 0.026), (s * 1.0, 0.0, 0.0), 0.0110))

    for v in bm.verts:
        if v.co.z < 1.455:
            continue
        desloc = Vector((0.0, 0.0, 0.0))
        for centro, raios, direcao, amp in brushes:
            w = _gauss(v.co, centro, raios)
            if w > 0.002:
                d = Vector(direcao)
                d.normalize()
                desloc += d * (amp * w)
        v.co += desloc

    # mandíbula afunilada: rosto de heroína, não de boneco esférico
    for v in bm.verts:
        if 1.470 < v.co.z < 1.540:
            t = (1.540 - v.co.z) / 0.070
            v.co.x *= 1.0 - 0.13 * t
            v.co.y *= 1.0 - 0.05 * t

    bm.to_mesh(me)
    bm.free()
    me.update()
    log("rosto esculpido (órbita, nariz, boca, queixo, orelhas)")
    return obj


# -----------------------------------------------------------------------------
# 5. Utilitários de malha/textura reaproveitados por olhos, cabelo, sobrancelha
#    e cílios (Fase 3): cartões (ribbons) planos e calotas esféricas (olho).
# -----------------------------------------------------------------------------
def _fita(nome, pontos, larguras, eixos, uv_rect):
    """Cartão plano (ribbon): N pontos centrais, largura e eixo de largura por
    ponto. UV mapeia t=0 (base) -> topo do retângulo do atlas, t=1 (ponta) ->
    base — usado por cabelo, franja, sobrancelha e cílio (mesma função, o que
    muda é a trajetória e o retângulo do atlas).
    """
    u0, v0, u1, v1 = uv_rect
    n = len(pontos)
    verts, uvs = [], []
    for i in range(n):
        t = i / (n - 1)
        p, w, eixo = pontos[i], larguras[i] * 0.5, eixos[i]
        verts.append(tuple(p - eixo * w))
        verts.append(tuple(p + eixo * w))
        v = v0 + (v1 - v0) * t
        uvs.append((u0, v))
        uvs.append((u1, v))
    faces = [(i * 2, i * 2 + 1, (i + 1) * 2 + 1, (i + 1) * 2) for i in range(n - 1)]
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    uvlayer = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvlayer.data[li].uv = uvs[me.loops[li].vertex_index]
    for p in me.polygons:
        p.use_smooth = False
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _hemisferio(nome, centro, raio, frente, ang_max_graus, seg_u=16, seg_v=8):
    """Calota esférica aberta (dome) apontando para `frente`. UV polar: o
    ápice (ang=0) cai no centro do quadrado de textura, a borda (ang_max) cai
    no círculo unitário — usado pelo globo ocular (esclera+íris no mesmo
    mapa) e pela córnea.
    """
    centro = Vector(centro)
    frente = Vector(frente).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(frente.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    lado = frente.cross(ref).normalized()
    cima = lado.cross(frente).normalized()
    ang_max = math.radians(ang_max_graus)

    verts = [tuple(centro + frente * raio)]
    uvs = [(0.5, 0.5)]
    aneis = []
    for j in range(1, seg_v + 1):
        polar = ang_max * (j / seg_v)
        anel = []
        for i in range(seg_u):
            az = i / seg_u * TAU
            dirv = frente * math.cos(polar) + (lado * math.cos(az) + cima * math.sin(az)) * math.sin(polar)
            verts.append(tuple(centro + dirv * raio))
            r = polar / ang_max
            uvs.append((0.5 + 0.5 * r * math.cos(az), 0.5 + 0.5 * r * math.sin(az)))
            anel.append(len(verts) - 1)
        aneis.append(anel)

    faces = []
    for i in range(seg_u):
        i2 = (i + 1) % seg_u
        faces.append((0, aneis[0][i], aneis[0][i2]))
    for j in range(len(aneis) - 1):
        a0, a1 = aneis[j], aneis[j + 1]
        for i in range(seg_u):
            i2 = (i + 1) % seg_u
            faces.append((a0[i], a0[i2], a1[i2], a1[i]))

    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    uvlayer = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvlayer.data[li].uv = uvs[me.loops[li].vertex_index]
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _salvar_imagem_numpy(nome, rgba, caminho, srgb=True):
    """Grava um array numpy (H, W, 3|4) float 0..1 como PNG/JPEG e recarrega
    do disco — o GLB embute o arquivo salvo, não o buffer em memória (mesma
    armadilha documentada em bake_heroi_julia.py::salvar()).
    """
    h, w = rgba.shape[0], rgba.shape[1]
    if rgba.shape[2] == 3:
        rgba = np.concatenate([rgba, np.ones((h, w, 1), dtype=np.float32)], axis=2)
    img = D.images.new(nome, w, h, alpha=True)
    img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    buf = np.flipud(np.clip(rgba, 0.0, 1.0)).astype(np.float32)
    img.pixels.foreach_set(buf.reshape(-1))
    img.filepath_raw = str(caminho)
    if caminho.suffix.lower() in (".jpg", ".jpeg"):
        img.file_format = "JPEG"
        bpy.context.scene.render.image_settings.quality = 90
    else:
        img.file_format = "PNG"
    img.save()
    D.images.remove(img)
    return D.images.load(str(caminho))


# -----------------------------------------------------------------------------
# 6. Cabelo, olhos, sobrancelhas e cílios (Fase 3)
# -----------------------------------------------------------------------------
# Marcos derivados de ROSTO (seção "4c"); tudo em espaço pré-normalização.
CABELO = {
    "rabo_x": 0.0, "rabo_y": 0.096, "rabo_z": 1.598,   # elástico do rabo de cavalo
    "comprimento": 0.400,
    "largura_base": 0.050,
    "largura_ponta": 0.009,
}
OLHO = {
    "raio_esclera": 0.0118,
    "raio_cornea": 0.0092,
    "ang_esclera": 62.0,   # graus visíveis pela órbita esculpida
    "ang_cornea": 30.0,
    "recuo": 0.006,        # m que o centro do globo fica ATRÁS de ROSTO["olho_y"]
    "toe_out_graus": 4.0,  # leve divergência natural do olhar
}


def _forma_mecha(uu, vv, variante=0):
    """Cartão de mecha: silhueta afunilada da raiz (vv=0) à ponta (vv=1) com
    fios internos (listras) e gradiente raiz-escura -> ponta-clara."""
    largura_local = 1.0 - 0.55 * vv
    dist_centro = np.abs(uu - 0.5) * 2.0
    alpha = np.clip((largura_local - dist_centro) / 0.06, 0.0, 1.0)

    freq = 9.0 + variante * 2.0
    fase = variante * 1.7
    linhas = 0.5 + 0.5 * np.sin((uu * freq + fase) * TAU)
    tom = 0.30 + 0.65 * vv
    escuro = np.array([0.045, 0.028, 0.024])
    claro = np.array([0.24, 0.15, 0.10])
    brilho = np.array([0.36, 0.24, 0.16])
    base = escuro[None, None, :] * (1 - tom)[..., None] + claro[None, None, :] * tom[..., None]
    cor = base * (0.78 + 0.22 * linhas)[..., None]
    cor = cor + brilho[None, None, :] * (0.10 * np.clip(linhas - 0.7, 0.0, 1.0))[..., None]
    return alpha, np.clip(cor, 0.0, 1.0)


def _forma_sobrancelha(uu, vv):
    """Feixe de fios finos (não um bloco sólido): linhas paralelas em arco
    com folgas entre elas — mesma lógica do cílio, só mais larga/densa. Sem
    ondulação de alta frequência por fio (isso lia como rabisco no render)."""
    centro = 0.5 + 0.10 * np.sin(uu * math.pi)
    n = 5
    alpha = np.zeros_like(uu)
    for k in range(n):
        offset = (k / (n - 1) - 0.5) * 0.095
        largura = 0.0085 * (1.0 - 0.30 * np.abs(uu - 0.5) * 2.0)
        d = np.abs(vv - (centro + offset))
        alpha = np.maximum(alpha, np.clip((largura - d) / 0.006, 0.0, 1.0))
    fade_ponta = np.clip(np.minimum(uu, 1.0 - uu) / 0.05, 0.0, 1.0)
    alpha = alpha * fade_ponta
    cor = np.tile(np.array([0.090, 0.055, 0.040]), uu.shape + (1,))
    return alpha, cor


def _forma_cilio(uu, vv):
    alpha = np.zeros_like(uu)
    n = 7
    for k in range(n):
        cx = (k + 0.5) / n
        curva = 0.10 * math.sin(cx * math.pi)
        cx_v = cx + curva * vv
        largura = 0.011 * (1.0 - 0.6 * vv)
        d = np.abs(uu - cx_v)
        fio = np.clip((largura - d) / 0.006, 0.0, 1.0) * np.clip((0.85 - vv) / 0.15, 0.0, 1.0)
        alpha = np.maximum(alpha, fio)
    cor = np.tile(np.array([0.03, 0.02, 0.02]), uu.shape + (1,))
    return alpha, cor


def gerar_atlas_cabelo(cel=128):
    """Atlas 2x2 (cel px cada): mecha_a, mecha_b, sobrancelha, cílio.

    As 5 mechas do rabo reaproveitam mecha_a/mecha_b em rodízio (igual à
    técnica padrão de hair-cards em jogos, onde poucos cartões de textura
    cobrem várias tiras de geometria) — mantém o atlas minúsculo.
    """
    W, H = cel * 2, cel * 2
    rgba = np.zeros((H, W, 4), dtype=np.float32)
    u = (np.arange(cel) + 0.5) / cel
    v = (np.arange(cel) + 0.5) / cel
    uu, vv = np.meshgrid(u, v)

    celulas = {}
    layout = [("mecha_a", 0, 0, 0), ("mecha_b", 1, 0, 1), ("sobrancelha", 0, 1, None), ("cilio", 1, 1, None)]
    for nome, col, row, var in layout:
        if nome.startswith("mecha"):
            alpha, cor = _forma_mecha(uu, vv, variante=var)
        elif nome == "sobrancelha":
            alpha, cor = _forma_sobrancelha(uu, vv)
        else:
            alpha, cor = _forma_cilio(uu, vv)
        x0, y0 = col * cel, row * cel
        rgba[y0:y0 + cel, x0:x0 + cel, :3] = cor
        rgba[y0:y0 + cel, x0:x0 + cel, 3] = alpha
        # Retângulo em coordenadas UV (v=0 embaixo, padrão OpenGL/Blender).
        # t=0 (base/raiz) mapeia para o topo da célula, t=1 (ponta) para a base.
        v_topo = 1.0 - row / 2.0
        v_base = 1.0 - (row + 1) / 2.0
        celulas[nome] = (col / 2.0 + 0.02, v_topo - 0.02, (col + 1) / 2.0 - 0.02, v_base + 0.02)
    return rgba, celulas


def gerar_texturas_olho(res=160):
    """Albedo (esclera+íris+pupila) e normal radial da íris, num só disco."""
    xs = (np.arange(res) + 0.5) / res * 2.0 - 1.0
    ys = (np.arange(res) + 0.5) / res * 2.0 - 1.0
    uu, vv = np.meshgrid(xs, ys)
    r = np.sqrt(uu * uu + vv * vv)
    ang = np.arctan2(vv, uu)

    raio_pupila, raio_iris = 0.20, 0.52
    cor_pupila = np.array([0.015, 0.015, 0.015])
    cor_iris_a = np.array([0.26, 0.16, 0.06])
    cor_iris_b = np.array([0.11, 0.065, 0.03])
    cor_esclera = np.array([0.93, 0.91, 0.89])

    veia = 0.05 * np.clip(np.sin(ang * 9.0 + r * 22.0) - 0.75, 0.0, 1.0)
    esclera = cor_esclera[None, None, :] * (1 - veia)[..., None] + np.array([0.85, 0.55, 0.5])[None, None, :] * veia[..., None]

    raios_iris = 0.5 + 0.5 * np.sin(ang * 24.0)
    iris = cor_iris_a[None, None, :] * raios_iris[..., None] + cor_iris_b[None, None, :] * (1 - raios_iris)[..., None]
    limbo = np.clip((r - raio_iris + 0.045) / 0.045, 0.0, 1.0)
    iris = iris * (1.0 - 0.55 * limbo[..., None])

    cor = np.where((r < raio_pupila)[..., None], cor_pupila[None, None, :],
                    np.where((r < raio_iris)[..., None], iris, esclera))
    cor = np.clip(cor, 0.0, 1.0)

    frac = np.clip((r - raio_pupila) / max(1e-4, raio_iris - raio_pupila), 0.0, 1.0)
    dentro_iris = (r >= raio_pupila) & (r < raio_iris)
    altura = np.where(dentro_iris, 0.5 * np.sin(ang * 24.0) * frac, 0.0)
    dy, dx = np.gradient(altura)
    forca = 6.0
    nx, ny, nz = -dx * forca, -dy * forca, np.ones_like(altura)
    norma = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / norma, ny / norma, nz / norma
    normal = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1)
    return cor, normal


def material_alpha_scissor(imagem):
    """Cartão com corte de alpha (sem ordenação por transparência): o nó
    Math>GREATER_THAN antes do Alpha do BSDF é o padrão que o exportador
    glTF do Blender 4.5 detecta como `alphaMode=MASK` (ver
    io_scene_gltf2 blender/exp/material/search_node_tree.py::detect_alpha_clip).
    `blend_method`/`alpha_threshold` ficam só para a pré-visualização no
    Blender; quem decide o alphaMode exportado é o grafo de nós.
    """
    nome = "alpha_scissor"
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    m.blend_method = "CLIP"
    m.alpha_threshold = 0.5
    m.use_backface_culling = False
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = imagem
    tex.image.colorspace_settings.name = "sRGB"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    corte = nt.nodes.new("ShaderNodeMath")
    corte.operation = "GREATER_THAN"
    corte.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs["Alpha"], corte.inputs[0])
    nt.links.new(corte.outputs["Value"], bsdf.inputs["Alpha"])

    bsdf.inputs["Roughness"].default_value = 0.55
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30
    return m


def material_esclera(albedo, normal):
    m = D.materials.get("OlhoEsclera") or D.materials.new("OlhoEsclera")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    t_alb = nt.nodes.new("ShaderNodeTexImage")
    t_alb.image = albedo
    t_alb.image.colorspace_settings.name = "sRGB"
    nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Base Color"])

    t_nrm = nt.nodes.new("ShaderNodeTexImage")
    t_nrm.image = normal
    t_nrm.image.colorspace_settings.name = "Non-Color"
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nrm.inputs["Strength"].default_value = 0.6
    nt.links.new(t_nrm.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Roughness"].default_value = 0.20
    return m


def material_cornea():
    """Córnea: `refraction barata` = Transmission Weight alto num casco fino
    (exporta como KHR_materials_transmission no glTF), em vez de um caminho
    de refração recursivo caro — é o dome à frente da íris que dá o brilho
    de vidro sem custo de renderização em tempo real."""
    m = D.materials.get("OlhoCornea") or D.materials.new("OlhoCornea")
    m.use_nodes = True
    m.blend_method = "BLEND"
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.97, 0.98, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.04
    bsdf.inputs["IOR"].default_value = 1.376
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 1.0
    return m


def criar_olhos():
    """Globo ocular em duas peças: esclera+íris (calota com o disco de
    textura) e córnea (calota menor, transmissiva, sobre a íris)."""
    albedo, normal = gerar_texturas_olho()
    p_alb = TEX_DIR / "julia_olho_albedo.jpg"
    p_nrm = TEX_DIR / "julia_olho_normal.jpg"
    img_alb = _salvar_imagem_numpy("julia_olho_albedo", albedo, p_alb, srgb=True)
    img_nrm = _salvar_imagem_numpy("julia_olho_normal", normal, p_nrm, srgb=False)
    mat_esclera = material_esclera(img_alb, img_nrm)
    mat_cornea = material_cornea()

    pecas = []
    for lado, s in (("l", 1.0), ("r", -1.0)):
        cx = s * ROSTO["olho_x"]
        cy = ROSTO["olho_y"] + OLHO["recuo"]
        cz = ROSTO["olho_z"]
        toe = math.radians(OLHO["toe_out_graus"]) * s
        frente = Vector((math.sin(toe), -math.cos(toe), 0.0))

        esclera = _hemisferio(f"olho_esclera_{lado}", (cx, cy, cz), OLHO["raio_esclera"],
                               frente, OLHO["ang_esclera"])
        esclera.data.materials.append(mat_esclera)
        pecas.append(esclera)

        centro_cornea = Vector((cx, cy, cz)) + frente * (OLHO["raio_esclera"] * 0.72)
        cornea = _hemisferio(f"olho_cornea_{lado}", tuple(centro_cornea), OLHO["raio_cornea"],
                              frente, OLHO["ang_cornea"])
        cornea.data.materials.append(mat_cornea)
        pecas.append(cornea)
    log(f"olhos: {len(pecas)} peças (esclera+córnea x2)")
    return pecas


def criar_sobrancelhas_e_cilios(mat, celulas):
    pecas = []
    for lado, s in (("l", 1.0), ("r", -1.0)):
        # Sobrancelha: arco acima da órbita, sobre o arco superciliar esculpido.
        seg = 6
        pontos, larguras, eixos = [], [], []
        x0 = s * (ROSTO["olho_x"] - 0.016)
        x1 = s * (ROSTO["olho_x"] + 0.030)
        for i in range(seg + 1):
            t = i / seg
            x = x0 + (x1 - x0) * t
            arco = math.sin(t * math.pi)
            # y bem à frente do arco superciliar esculpido (que já projeta a
            # pele para fora ~7mm): sem essa folga o cartão entra na pele e
            # cria z-fighting (lido como um retalho sólido no render).
            pontos.append(Vector((x, ROSTO["olho_y"] - 0.016, ROSTO["sobrancelha_z"] - 0.004 + 0.006 * arco)))
            larguras.append(0.013 * (1.0 - 0.30 * abs(t - 0.5) * 2.0))
            eixos.append(Vector((0.0, 0.0, 1.0)))
        obj = _fita(f"sobrancelha_{lado}", pontos, larguras, eixos, celulas["sobrancelha"])
        obj.data.materials.append(mat)
        pecas.append(obj)

        # Cílios: ao longo da pálpebra superior, curva "cat-eye" na ponta externa.
        seg = 6
        pontos, larguras, eixos = [], [], []
        x0 = s * (ROSTO["olho_x"] - 0.028)
        x1 = s * (ROSTO["olho_x"] + 0.032)
        for i in range(seg + 1):
            t = i / seg
            x = x0 + (x1 - x0) * t
            arco = math.sin(t * math.pi)
            y = ROSTO["olho_y"] - 0.010 - 0.006 * (t if s * (x1 - x0) > 0 else 0.0)
            pontos.append(Vector((x, y, ROSTO["olho_z"] + 0.013 + 0.005 * arco)))
            larguras.append(0.009 * (0.35 + 0.65 * arco))
            eixos.append(Vector((0.0, -0.35, 1.0)).normalized())
        obj = _fita(f"cilio_{lado}", pontos, larguras, eixos, celulas["cilio"])
        obj.data.materials.append(mat)
        pecas.append(obj)
    log(f"sobrancelhas + cílios: {len(pecas)} cartões")
    return pecas


def criar_cabelo(mat, celulas):
    """Rabo de cavalo em 5 mechas (leque a partir do elástico) + franja."""
    pecas = []
    rabo = Vector((CABELO["rabo_x"], CABELO["rabo_y"], CABELO["rabo_z"]))
    n_mechas = 5
    seg = 7
    for m_i in range(n_mechas):
        fan_t = (m_i / (n_mechas - 1)) - 0.5   # -0.5 .. 0.5
        ang_fan = fan_t * math.radians(72.0)
        fase = m_i * 1.7
        comp = CABELO["comprimento"] * (1.0 - 0.08 * abs(fan_t))
        pontos, larguras, eixos = [], [], []
        for i in range(seg + 1):
            t = i / seg
            z = rabo.z - comp * t
            y = rabo.y + comp * (0.24 * t + 0.11 * math.sin(t * math.pi))
            x = rabo.x + math.sin(ang_fan) * comp * 0.60 * t + 0.010 * math.sin(t * math.pi * 2.0 + fase)
            pontos.append(Vector((x, y, z)))
            larguras.append(CABELO["largura_base"] * (1 - t) + CABELO["largura_ponta"] * t)
            eixos.append(Vector((math.cos(ang_fan), math.sin(ang_fan) * 0.4, 0.0)).normalized())
        rect = celulas["mecha_a"] if m_i % 2 == 0 else celulas["mecha_b"]
        obj = _fita(f"cabelo_mecha_{m_i:02d}", pontos, larguras, eixos, rect)
        obj.data.materials.append(mat)
        pecas.append(obj)

    # Franja: cartões curtos caindo sobre a testa, bem acima da sobrancelha
    # (curta — não pode encostar na linha do olho).
    n_franja = 6
    largura_total = 0.100
    for i in range(n_franja):
        cx = -largura_total / 2.0 + largura_total * i / (n_franja - 1)
        seg = 4
        comp = 0.032 + 0.006 * math.sin(i * 1.3)
        pontos, larguras, eixos = [], [], []
        for j in range(seg + 1):
            t = j / seg
            z = 1.660 - comp * t
            y = -0.088 + 0.006 * t
            x = cx + 0.007 * math.sin(t * math.pi)
            pontos.append(Vector((x, y, z)))
            larguras.append(0.020 * (1.0 - 0.30 * t))
            eixos.append(Vector((1.0, 0.0, 0.0)))
        rect = celulas["mecha_a"] if i % 2 == 0 else celulas["mecha_b"]
        obj = _fita(f"franja_{i:02d}", pontos, larguras, eixos, rect)
        obj.data.materials.append(mat)
        pecas.append(obj)
    log(f"cabelo: {len(pecas)} cartões (5 mechas + {n_franja} franja)")
    return pecas


def montar_cabelo_e_rosto():
    """Gera o atlas alpha (cabelo/sobrancelha/cílio) e todas as peças novas
    da Fase 3. Retorna a lista de objetos (nenhum é unido ao corpo — cada um
    carrega seu próprio material de cartão/olho)."""
    atlas, celulas = gerar_atlas_cabelo()
    img_atlas = _salvar_imagem_numpy("julia_cabelo_alpha", atlas, TEX_DIR / "julia_cabelo_alpha.png", srgb=True)
    mat_cartao = material_alpha_scissor(img_atlas)

    pecas = []
    pecas += criar_olhos()
    pecas += criar_sobrancelhas_e_cilios(mat_cartao, celulas)
    pecas += criar_cabelo(mat_cartao, celulas)
    return pecas


# -----------------------------------------------------------------------------
# 7. Normalização de escala e contato com o solo
# -----------------------------------------------------------------------------
def normalizar(corpo, extras=(), altura=ALTURA_ALVO, piso=PISO_OFFSET):
    """Escala/posiciona o corpo pela sua própria bbox e aplica a MESMA escala e
    deslocamento em Z a `extras` (olhos/cabelo/sobrancelha/cílio) — todos
    nasceram no mesmo espaço de coordenadas do corpo (origem em (0,0,0)), então
    a transformação rígida os mantém colados ao rosto esculpido."""
    objetos = [corpo] + list(extras)

    ativar(corpo)
    bpy.context.view_layer.update()
    zs = [(corpo.matrix_world @ v.co).z for v in corpo.data.vertices]
    escala = altura / (max(zs) - min(zs))
    for obj in objetos:
        ativar(obj)
        obj.scale = (escala, escala, escala)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    ativar(corpo)
    bpy.context.view_layer.update()
    zs = [(corpo.matrix_world @ v.co).z for v in corpo.data.vertices]
    desloc_z = piso - min(zs)
    for obj in objetos:
        ativar(obj)
        obj.location.z += desloc_z
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return corpo


def metricas(corpo, extras=()):
    def contar(obj):
        me = obj.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        return len(me.vertices), len(me.polygons), tris

    v_c, f_c, t_c = contar(corpo)
    quads = sum(1 for p in corpo.data.polygons if len(p.vertices) == 4)
    zs = [v.co.z for v in corpo.data.vertices]
    xs = [v.co.x for v in corpo.data.vertices]
    ys = [v.co.y for v in corpo.data.vertices]
    # O gate de manifold é só do corpo: cartões de cabelo/sobrancelha/cílio são
    # planos de propósito (toda aresta é de contorno) e os olhos são calotas
    # abertas — nenhum dos dois é "fechado" por natureza, então não entram
    # nessa contagem (mesma leitura usada nos hair-cards de qualquer engine).
    nao_manifold = 0
    bm = bmesh.new()
    bm.from_mesh(corpo.data)
    for e in bm.edges:
        if len(e.link_faces) != 2:
            nao_manifold += 1
    bm.free()

    v_e = f_e = t_e = 0
    for obj in extras:
        vv, ff, tt = contar(obj)
        v_e += vv
        f_e += ff
        t_e += tt

    return {
        "verts_corpo": v_c, "faces_corpo": f_c, "tris_corpo": t_c,
        "verts_extras": v_e, "faces_extras": f_e, "tris_extras": t_e,
        "verts": v_c + v_e,
        "faces": f_c + f_e,
        "tris": t_c + t_e,
        "quads_pct": round(100.0 * quads / max(1, f_c), 1),
        "altura_m": round(max(zs) - min(zs), 4),
        "piso_z_m": round(min(zs), 4),
        "largura_m": round(max(xs) - min(xs), 4),
        "profundidade_m": round(max(ys) - min(ys), 4),
        "arestas_nao_manifold": nao_manifold,
    }


def exportar(corpo, extras=(), nome="heroi_julia_base"):
    mat = material("PeleJulia", (0.74, 0.52, 0.40), rough=0.52)
    corpo.data.materials.clear()
    corpo.data.materials.append(mat)

    bpy.ops.object.select_all(action="DESELECT")
    corpo.select_set(True)
    for obj in extras:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = corpo

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
    densificar_cabeca(corpo)
    esculpir_rosto(corpo)
    juntar(corpo, criar_maos())

    log("Fase 3 — olhos, sobrancelhas, cílios e cabelo")
    extras = montar_cabelo_e_rosto()

    normalizar(corpo, extras)

    m = metricas(corpo, extras)
    glb, blend = exportar(corpo, extras)
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
