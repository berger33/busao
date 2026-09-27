#!/usr/bin/env python3
"""Herói 10/10 — corpo base + Fase 3 da heroína Júlia.

Plano: docs/PLANO_HEROI_10_10.md (Fases 1 e 3 — corpo, rosto, olhos e cabelo).
Referência visual: docs/arte_alvo_final/6_model_sheet_heroi.png

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
  heroi_julia_base.glb     corpo/rosto/olhos/cabelo sem rig (Fase 4 adiciona armature)
  heroi_julia_base.blend   cena para iteração
  heroi_julia_metrics.json métricas dos gates geométricos + Fase 3

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
        no(f"punho_{lado}", _braco(1.00), 0.024)
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
# 4b. Mãos: 5 dedos separados, contínuos e arredondados
# -----------------------------------------------------------------------------
# A primeira versão resolvia o gate "tem 5 dedos", mas ainda lia como mão de
# boneco: palma em bloco com tampa reta e 3 cápsulas soltas por dedo. Esta versão
# gera cada dedo como UM tubo orgânico contínuo, com estreitamento nos nós e ponta
# arredondada; a palma é um volume superelíptico que entra no antebraço para
# esconder a emenda. O resultado é mais limpo para rig/skin depois e elimina as
# faixas escuras de AO que apareciam entre falanges separadas.
DEDOS = [
    # (nome, offset_x_na_palma, offset_y, comprimento, raio_x, raio_y)
    ("index",  0.023, -0.004, 0.068, 0.0067, 0.0082),
    ("middle", 0.007, -0.006, 0.074, 0.0071, 0.0086),
    ("ring",  -0.009, -0.005, 0.068, 0.0067, 0.0081),
    ("pinky", -0.024, -0.002, 0.055, 0.0059, 0.0072),
]
POLEGAR = ("thumb", 0.034, -0.002, 0.054, 0.0078, 0.0090)


def _base_perpendicular(tangente: Vector):
    """Dois eixos estáveis perpendiculares à tangente do tubo."""
    t = Vector(tangente)
    if t.length < 1e-6:
        t = Vector((0.0, 0.0, -1.0))
    t.normalize()
    # prefere o eixo global X para a largura dos dedos; quando paralelo demais,
    # troca para Y. Mantém as mãos espelhadas sem torção brusca.
    ref = Vector((1.0, 0.0, 0.0))
    if abs(t.dot(ref)) > 0.86:
        ref = Vector((0.0, 1.0, 0.0))
    n1 = ref - t * ref.dot(t)
    n1.normalize()
    n2 = t.cross(n1)
    n2.normalize()
    return n1, n2


def _tubo_organico(nome, centros, raios, seg=14, fechar_inicio=True, fechar_fim=True):
    """Tubo elíptico ao longo de uma sequência de centros.

    `raios` é uma lista de (rx, ry). A malha é fechada nas pontas para manter
    gate não-manifold = 0, mas as bases dos dedos/palma ficam sobrepostas dentro
    da palma/antebraço e não aparecem no render.
    """
    me = D.meshes.new(nome)
    verts, faces = [], []
    centros = [Vector(c) for c in centros]
    for i, c in enumerate(centros):
        if i == 0:
            tang = centros[1] - centros[0]
        elif i == len(centros) - 1:
            tang = centros[-1] - centros[-2]
        else:
            tang = centros[i + 1] - centros[i - 1]
        n1, n2 = _base_perpendicular(tang)
        rx, ry = raios[i]
        for k in range(seg):
            a = k / seg * TAU
            verts.append(tuple(c + n1 * (rx * math.cos(a)) + n2 * (ry * math.sin(a))))
    for i in range(len(centros) - 1):
        v0, v1 = i * seg, (i + 1) * seg
        for k in range(seg):
            kn = (k + 1) % seg
            faces.append((v0 + k, v0 + kn, v1 + kn, v1 + k))
    if fechar_inicio:
        ci = len(verts)
        verts.append(tuple(centros[0]))
        for k in range(seg):
            faces.append((ci, (k + 1) % seg, k))
    if fechar_fim:
        cf = len(verts)
        verts.append(tuple(centros[-1]))
        base = (len(centros) - 1) * seg
        for k in range(seg):
            faces.append((cf, base + k, base + (k + 1) % seg))
    me.from_pydata(verts, [], faces)
    me.update()
    for f in me.polygons:
        f.use_smooth = True
    obj = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _laje_palma(nome, centro, largura, espessura, comprimento, seg=18):
    """Palma anatômica arredondada, sem tampa quadrada visível.

    A versão com contorno recortado deixava triângulos/fendas no close-up. Esta
    mantém uma superelipse lisa (boa para rig e bake), estreita no punho e nos
    nós, e os nós dos dedos são adicionados como pequenas almofadas elipsoides em
    `criar_maos()` para quebrar a borda reta sem criar artefatos.
    """
    cx, cy, cz = centro
    perfis = [
        (-0.18, largura * 0.25, espessura * 0.34,  0.003),  # entra no antebraço
        ( 0.00, largura * 0.34, espessura * 0.42,  0.001),
        ( 0.24, largura * 0.48, espessura * 0.52, -0.001),
        ( 0.58, largura * 0.52, espessura * 0.50, -0.002),
        ( 0.86, largura * 0.48, espessura * 0.44, -0.003),
        ( 1.00, largura * 0.40, espessura * 0.32, -0.004),  # linha dos nós
    ]
    verts, faces = [], []
    exp = 0.62  # seção retângulo-arredondado, não cilindro
    for t, rx, ry, yoff in perfis:
        z = cz - comprimento * t
        y_c = cy - 0.0035 * math.sin(math.pi * min(1.0, t))
        # Superellipse suave: palma mais cheia no dorso e menos cilíndrica.
        for k in range(seg):
            a = k / seg * TAU
            ca, sa = math.cos(a), math.sin(a)
            x = math.copysign(abs(ca) ** exp, ca) * rx
            y = math.copysign(abs(sa) ** exp, sa) * ry
            verts.append((cx + x, cy + yoff + y, z))
    for i in range(len(perfis) - 1):
        v0, v1 = i * seg, (i + 1) * seg
        for k in range(seg):
            kn = (k + 1) % seg
            faces.append((v0 + k, v0 + kn, v1 + kn, v1 + k))
    ci = len(verts)
    verts.append((cx, cy + perfis[0][3], cz - comprimento * perfis[0][0]))
    cf = len(verts)
    verts.append((cx, cy + perfis[-1][3], cz - comprimento * perfis[-1][0]))
    last = (len(perfis) - 1) * seg
    for k in range(seg):
        kn = (k + 1) % seg
        faces.append((ci, kn, k))
        faces.append((cf, last + k, last + kn))
    me.from_pydata(verts, [], faces)
    me.update()
    for f in me.polygons:
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _elipsoide(nome, centro, raios, seg_u=14, seg_v=7):
    """Elipsoide pequeno para nós dos dedos/polpa, fechado e suave.

    Usa polos únicos (não anéis degenerados) para manter gate não-manifold = 0.
    """
    cx, cy, cz = centro
    rx, ry, rz = raios
    verts, faces = [], []
    top = len(verts)
    verts.append((cx, cy, cz + rz))
    # anéis intermediários, sem duplicar os polos
    for i in range(1, seg_v):
        v = i / seg_v
        phi = math.pi / 2 - v * math.pi
        cp, sp = math.cos(phi), math.sin(phi)
        for j in range(seg_u):
            a = j / seg_u * TAU
            verts.append((cx + rx * cp * math.cos(a), cy + ry * cp * math.sin(a), cz + rz * sp))
    bottom = len(verts)
    verts.append((cx, cy, cz - rz))
    # topo
    first = 1
    for j in range(seg_u):
        jn = (j + 1) % seg_u
        faces.append((top, first + j, first + jn))
    # faixas intermediárias
    ring_count = seg_v - 1
    for r in range(ring_count - 1):
        a = 1 + r * seg_u
        b = 1 + (r + 1) * seg_u
        for j in range(seg_u):
            jn = (j + 1) % seg_u
            faces.append((a + j, a + jn, b + jn, b + j))
    # base
    last = 1 + (ring_count - 1) * seg_u
    for j in range(seg_u):
        jn = (j + 1) % seg_u
        faces.append((bottom, last + jn, last + j))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    for f in me.polygons:
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _dedo_continuo(nome, base, comprimento, rx, ry, curva_y=-0.012, seg=14):
    """Dedo inteiro, com nós discretos e ponta arredondada, sem falanges soltas."""
    bx, by, bz = base
    # t, raio relativo. Os vales em 0.32/0.66 marcam articulações sem quebrar a
    # malha; a sequência final fecha como polpa arredondada.
    perfil = [
        (0.00, 1.10), (0.10, 1.03), (0.30, 0.88),
        (0.43, 0.98), (0.62, 0.85), (0.76, 0.92),
        # ponta em semiesfera: mais anéis com queda curta, sem cone pontudo
        (0.88, 0.80), (0.93, 0.70), (0.970, 0.48),
        (0.992, 0.22), (1.000, 0.035),
    ]
    centros, raios = [], []
    for t, escala in perfil:
        # dedos relaxados: descem e avançam milímetros para frente, com leve
        # curvatura para dentro da palma (sem pose de garra).
        y = by + curva_y * (t ** 1.25)
        z = bz - comprimento * t
        centros.append((bx, y, z))
        raios.append((rx * escala, ry * escala))
    return _tubo_organico(nome, centros, raios, seg=seg)


def _polegar_continuo(nome, base, lado, comprimento, rx, ry, seg=14):
    """Polegar como tubo angulado lateral/frente, não cilindro colado."""
    bx, by, bz = base
    pts = [
        (bx,                    by,          bz),
        (bx + lado * 0.010,     by - 0.009,  bz - comprimento * 0.20),
        (bx + lado * 0.020,     by - 0.020,  bz - comprimento * 0.48),
        (bx + lado * 0.027,     by - 0.031,  bz - comprimento * 0.76),
        (bx + lado * 0.030,     by - 0.035,  bz - comprimento * 0.96),
        (bx + lado * 0.031,     by - 0.036,  bz - comprimento),
    ]
    esc = [1.06, 1.00, 0.92, 0.76, 0.40, 0.06]
    return _tubo_organico(nome, pts, [(rx * e, ry * e) for e in esc], seg=seg)


def criar_maos():
    """Palma + 5 dedos por mão, com proporção e encaixe visual no antebraço."""
    pecas = []
    largura = 0.080      # ~8 cm: palma estilizada, não pá quadrada
    espessura = 0.028
    comprimento = 0.067  # punho -> linha dos nós
    for lado, s in (("l", 1.0), ("r", -1.0)):
        px_ = s * (X_PUNHO + 0.002)
        py_ = -0.012
        # Entra 14 mm no antebraço; o cap da palma fica escondido e não aparece
        # como placa reta sob o punho.
        z_punho = Z_PUNHO + 0.014
        pecas.append(_laje_palma(
            f"palma_{lado}", (px_, py_, z_punho), largura, espessura, comprimento
        ))
        z_nos = z_punho - comprimento

        for nome, dx, dy, comp, rx, ry in DEDOS:
            # A base fica alguns mm dentro da palma para soldar visualmente e
            # impedir frestas escuras na linha dos nós.
            x = px_ + s * dx
            y = py_ + dy
            z = z_nos + 0.012
            # pequena almofada do nó do dedo: mascara a borda da palma e dá
            # leitura de mão real sem precisar boolean/soldagem destrutiva.
            pecas.append(_elipsoide(
                f"knuckle_{nome}_{lado}",
                (x, y - 0.004, z_nos + 0.010),
                (rx * 1.28, 0.0105, 0.0105),
            ))
            pecas.append(_dedo_continuo(
                f"{nome}_{lado}", (x, y, z), comp, rx, ry, curva_y=-0.010
            ))

        nome, dx, dy, comp, rx, ry = POLEGAR
        pecas.append(_polegar_continuo(
            f"{nome}_{lado}",
            (px_ + s * dx, py_ + dy - 0.001, z_punho - 0.026),
            s,
            comp,
            rx,
            ry,
        ))
    return pecas


def juntar(corpo, pecas):
    ativar(corpo)
    for p in pecas:
        p.select_set(True)
    bpy.context.view_layer.objects.active = corpo
    bpy.ops.object.join()
    # Remove normais facetadas residuais nas peças adicionadas.
    for poly in corpo.data.polygons:
        poly.use_smooth = True
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
# 4d. Fase 3 — rosto completo, olhos e cabelo em cards alpha-scissor
# -----------------------------------------------------------------------------
def _mat_principled(nome, cor, rough=0.5, transmission=0.0, alpha=1.0, metallic=0.0):
    """Material Principled simples, compatível com Blender 4.5 e glTF."""
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        if "Base Color" in b.inputs:
            b.inputs["Base Color"].default_value = (*cor, alpha)
        if "Roughness" in b.inputs:
            b.inputs["Roughness"].default_value = rough
        if "Metallic" in b.inputs:
            b.inputs["Metallic"].default_value = metallic
        if "Alpha" in b.inputs:
            b.inputs["Alpha"].default_value = alpha
        if transmission and "Transmission Weight" in b.inputs:
            b.inputs["Transmission Weight"].default_value = transmission
        if transmission and "IOR" in b.inputs:
            b.inputs["IOR"].default_value = 1.38
    m.diffuse_color = (*cor, alpha)
    if alpha < 1.0:
        # Só a córnea usa blend; cabelo continua MASK/alpha scissor abaixo.
        if hasattr(m, "blend_method"):
            m.blend_method = "BLEND"
        if hasattr(m, "use_screen_refraction"):
            m.use_screen_refraction = True
        if hasattr(m, "show_transparent_back"):
            m.show_transparent_back = False
    return m


def _assign_uv_from_vertex_uvs(me, vertex_uvs):
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = vertex_uvs[me.loops[li].vertex_index]
    return uv


def _card(nome, pontos, mat, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    """Quad frente-e-verso. Cards ficam com alpha scissor, sem ordenação."""
    me = D.meshes.new(nome)
    me.from_pydata(pontos, [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop, co in zip(me.uv_layers.active.data, uvs):
        loop.uv = co
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _poly_strip(nome, centros, larguras, mat):
    """Ribbon/card curvo em XZ: usado em pálpebras, sobrancelhas, lábios e fios."""
    if isinstance(larguras, (int, float)):
        larguras = [float(larguras)] * len(centros)
    pts = [Vector(c) for c in centros]
    verts, faces, uvs = [], [], []
    total = [0.0]
    for i in range(1, len(pts)):
        total.append(total[-1] + (pts[i] - pts[i - 1]).length)
    comp = max(total[-1], 1e-5)
    for i, c in enumerate(pts):
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tan = pts[-1] - pts[-2]
        else:
            tan = pts[i + 1] - pts[i - 1]
        # Perpendicular estável no plano frontal (X/Z). Se o segmento for muito
        # horizontal, ainda mantemos uma espessura vertical visual.
        perp = Vector((-tan.z, 0.0, tan.x))
        if perp.length < 1e-6:
            perp = Vector((0.0, 0.0, 1.0))
        perp.normalize()
        hw = larguras[i]
        verts.append(tuple(c - perp * hw))
        verts.append(tuple(c + perp * hw))
        t = total[i] / comp
        uvs.append((0.0, t))
        uvs.append((1.0, t))
    for i in range(len(pts) - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    _assign_uv_from_vertex_uvs(me, uvs)
    for f in me.polygons:
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _ellipse_disc(nome, centro, rx, rz, mat, seg=32, escala_x=1.0, escala_z=1.0):
    """Disco oval voltado para -Y (frente): pupila, narinas e brilho ocular."""
    cx, cy, cz = centro
    verts = [(cx, cy, cz)]
    uvs = [(0.5, 0.5)]
    for i in range(seg):
        a = i / seg * TAU
        x = cx + rx * math.cos(a) * escala_x
        z = cz + rz * math.sin(a) * escala_z
        verts.append((x, cy, z))
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    faces = [(0, i + 1, 1 + ((i + 1) % seg)) for i in range(seg)]
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    _assign_uv_from_vertex_uvs(me, uvs)
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _lip_surface(nome, upper, mat, width=0.0275, cols=28, rows=5):
    """Superfície curva dos lábios (2D patch com volume), não card chapado."""
    verts, faces, uvs = [], [], []
    line_z = 1.5248
    for r in range(rows):
        t = r / (rows - 1)
        for c in range(cols + 1):
            xn = -1.0 + 2.0 * c / cols
            taper = max(0.0, 1.0 - abs(xn) ** 2.2)
            x = width * xn
            if upper:
                # Cupid bow: dois picos suaves e vale discreto no centro.
                peak = math.exp(-((abs(xn) - 0.48) / 0.28) ** 2)
                center_dip = math.exp(-(xn / 0.20) ** 2)
                bottom = line_z + 0.0009 * taper
                top = line_z + 0.0028 + 0.0043 * peak - 0.0015 * center_dip
                z = bottom * (1.0 - t) + top * t
                y = -0.1122 - 0.0030 * math.sin(math.pi * t) * taper
            else:
                top = line_z - 0.0012 + 0.00035 * taper
                bottom = line_z - 0.0088 * (0.28 + 0.72 * taper)
                z = top * (1.0 - t) + bottom * t
                y = -0.1120 - 0.0038 * math.sin(math.pi * t) * taper
            verts.append((x, y, z))
            uvs.append((c / cols, t))
    for r in range(rows - 1):
        for c in range(cols):
            a = r * (cols + 1) + c
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    _assign_uv_from_vertex_uvs(me, uvs)
    for f in me.polygons:
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _iris_material():
    """Íris verde-castanha com mapa de cor e normal radial 128² embarcados."""
    mat = D.materials.new("Olho_Iris_NormalRadial")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.34

    w = h = 128
    color = D.images.new("julia_iris_color", width=w, height=h, alpha=False)
    normal = D.images.new("julia_iris_normal_radial", width=w, height=h, alpha=False)
    pix_c, pix_n = [], []
    for y in range(h):
        v = y / (h - 1)
        yy = (v - 0.5) * 2.0
        for x in range(w):
            u = x / (w - 1)
            xx = (u - 0.5) * 2.0
            r = min(1.0, math.sqrt(xx * xx + yy * yy))
            a = math.atan2(yy, xx)
            spokes = 0.5 + 0.5 * math.sin(a * 26.0 + r * 18.0)
            rings = 0.5 + 0.5 * math.sin(r * 54.0)
            limbal = 1.0 - max(0.0, (r - 0.78) / 0.22)
            base_g = 0.28 + 0.22 * spokes + 0.10 * rings
            base_r = 0.075 + 0.065 * rings + 0.035 * spokes
            base_b = 0.055 + 0.075 * spokes
            # Anel escuro externo e pupila no próprio mapa, além do disco preto.
            # Valores mais claros que o primeiro passe: a íris precisa permanecer
            # verde/castanha legível por trás da córnea no close a 2 m.
            dark = 0.72 + 0.28 * limbal
            pupil = 1.0 if r < 0.24 else 0.0
            if pupil:
                base_r, base_g, base_b = 0.006, 0.005, 0.004
            pix_c.extend((base_r * dark, base_g * dark, base_b * dark, 1.0))
            # Tangent-space normal: sulcos radiais finos, codificados em RGB.
            groove = math.sin(a * 34.0 + r * 22.0) * (1.0 - r) * 0.22
            nx = math.cos(a) * groove
            ny = math.sin(a) * groove
            nz = max(0.20, math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny)))
            pix_n.extend((0.5 + nx * 0.5, 0.5 + ny * 0.5, 0.5 + nz * 0.5, 1.0))
    color.pixels.foreach_set(pix_c)
    normal.pixels.foreach_set(pix_n)
    normal.colorspace_settings.name = "Non-Color"
    tex_dir = REPO / "assets" / "textures" / "heroi"
    tex_dir.mkdir(parents=True, exist_ok=True)
    color.filepath_raw = str(tex_dir / "julia_iris_color.png")
    color.file_format = "PNG"
    color.save(); color.pack()
    normal.filepath_raw = str(tex_dir / "julia_iris_normal_radial.png")
    normal.file_format = "PNG"
    normal.save(); normal.pack()

    t_col = nt.nodes.new("ShaderNodeTexImage")
    t_col.image = color
    nt.links.new(t_col.outputs["Color"], b.inputs["Base Color"])
    t_nrm = nt.nodes.new("ShaderNodeTexImage")
    t_nrm.image = normal
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nrm.inputs["Strength"].default_value = 0.62
    nt.links.new(t_nrm.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], b.inputs["Normal"])
    return mat


def _iris_disc(nome, centro, rx, rz, mat, seg=48, rings=5):
    """Disco levemente convexo da íris, com UV radial para o normal map."""
    cx, cy, cz = centro
    verts, uvs = [(cx, cy - 0.0006, cz)], [(0.5, 0.5)]
    for ri in range(1, rings + 1):
        r = ri / rings
        for i in range(seg):
            a = i / seg * TAU
            dome = -0.00055 * (1.0 - r * r)
            groove = -0.00012 * math.sin(a * 18.0 + r * 20.0) * (1.0 - r)
            x = cx + rx * r * math.cos(a)
            y = cy + dome + groove
            z = cz + rz * r * math.sin(a)
            verts.append((x, y, z))
            uvs.append((0.5 + 0.5 * r * math.cos(a), 0.5 + 0.5 * r * math.sin(a)))
    faces = []
    for i in range(seg):
        faces.append((0, 1 + i, 1 + ((i + 1) % seg)))
    for ri in range(1, rings):
        start0 = 1 + (ri - 1) * seg
        start1 = 1 + ri * seg
        for i in range(seg):
            faces.append((start0 + i, start0 + ((i + 1) % seg),
                          start1 + ((i + 1) % seg), start1 + i))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    _assign_uv_from_vertex_uvs(me, uvs)
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def material_cabelo_alpha():
    """Máscara binária embutida; glTF exporta MASK, nunca BLEND/alpha sorting."""
    img = D.images.new("julia_cabelo_alpha", width=256, height=512, alpha=True)
    px = []
    for y in range(512):
        v = y / 511.0
        for x in range(256):
            u = x / 255.0
            # A geometria já desenha o cacho; a alpha só recorta borda/taper e
            # alguns vazios internos grossos. Isso evita o shimmer que aparecia
            # quando a máscara alternava fios de 1 px.
            half = 0.48 * (1.0 - 0.30 * v) + 0.035 * math.sin(v * 12.0)
            edge_noise = 0.020 * math.sin(v * 38.0 + u * 11.0)
            dentro = abs(u - 0.5) < (half + edge_noise)
            sulco = abs(math.sin((u * 5.0 + v * 2.2) * math.pi)) < 0.055 and 0.10 < v < 0.90
            a = 1.0 if dentro and not sulco else 0.0
            streak = 0.55 + 0.45 * math.sin(u * 23.0 + v * 9.0) ** 2
            base = 0.050 + 0.030 * streak
            # castanho escuro com reflexos quentes, ainda opaco para alpha-scissor
            px.extend((base * 1.45, base * 0.78, base * 0.42, a))
    img.pixels.foreach_set(px)
    tex_dir = REPO / "assets" / "textures" / "heroi"
    tex_dir.mkdir(parents=True, exist_ok=True)
    img.filepath_raw = str(tex_dir / "julia_cabelo_alpha.png")
    img.file_format = "PNG"
    img.save()
    img.pack()

    m = D.materials.new("CabeloJulia_alpha_scissor")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    clip = nt.nodes.new("ShaderNodeMath")
    clip.operation = "GREATER_THAN"
    clip.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs["Alpha"], clip.inputs[0])
    nt.links.new(clip.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.70
    if hasattr(m, "blend_method"):
        m.blend_method = "CLIP"
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    m.alpha_threshold = 0.5
    m.use_transparency_overlap = False
    m.diffuse_color = (0.07, 0.032, 0.018, 1.0)
    return m


def _criar_face_extras(pele, escuro):
    """Lábios, linha da boca e narinas: o close passa a ler um rosto completo."""
    pecas = []
    labios = _mat_principled("LabiosJulia", (0.34, 0.125, 0.108), 0.54)
    boca = _mat_principled("LinhaBocaJulia", (0.045, 0.012, 0.010), 0.84)
    narina = _mat_principled("NarinaJulia", (0.030, 0.014, 0.012), 0.88)

    y = -0.113
    # Boca menor e mais arredondada: superfície curva com volume (não card chapado).
    pecas.append(_lip_surface("labio_superior", True, labios))
    pecas.append(_lip_surface("labio_inferior", False, labios))
    pecas.append(_poly_strip("linha_boca", [(-0.025, y, 1.5246), (-0.013, y - 0.0005, 1.5241),
                                            (0.000, y - 0.0007, 1.5239), (0.013, y - 0.0005, 1.5241),
                                            (0.025, y, 1.5246)],
                           0.00065, boca))
    # Narinas elípticas sob a ponta do nariz; discretas, mas legíveis em close.
    for s in (-1.0, 1.0):
        pecas.append(_ellipse_disc(f"narina_{'l' if s > 0 else 'r'}", (s * 0.0100, -0.118, 1.553),
                                   0.0031, 0.00155, narina, seg=20, escala_z=0.72))
    return pecas


def _criar_olho(lado, s, mats):
    pecas = []
    esclera, iris, cornea, preto, pele, escuro = mats
    cx, cz = s * 0.0345, 1.588
    # Globo ocular: esclera separada e córnea separada; iris/pupila são discos
    # frontais, então o olhar fica legível a 2 m e não "escapa" para baixo.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, location=(cx, -0.081, cz))
    scl = bpy.context.object
    scl.name = f"esclera_{lado}"
    scl.scale = (0.0245, 0.0090, 0.0142)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scl.data.materials.append(esclera)
    pecas.append(scl)

    pecas.append(_iris_disc(f"iris_{lado}", (cx, -0.0915, cz), 0.0095, 0.0098, iris))
    pecas.append(_ellipse_disc(f"pupila_{lado}", (cx, -0.0924, cz), 0.0029, 0.0031, preto, seg=28))
    pecas.append(_ellipse_disc(f"brilho_olho_{lado}", (cx - s * 0.0032, -0.0929, cz + 0.0037),
                               0.0018, 0.0012, _mat_principled("BrilhoOlhoJulia", (1.0, 0.96, 0.86), 0.18), seg=14))

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(cx, -0.0930, cz))
    co = bpy.context.object
    co.name = f"cornea_{lado}"
    co.scale = (0.0122, 0.0022, 0.0122)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    co.data.materials.append(cornea)
    pecas.append(co)

    outer = s * 0.058
    mid = s * 0.036
    inner = s * 0.014
    # Pálpebras modeladas como fitas finas de pele; próximas ao globo para ler
    # como dobra anatômica, não como blocos flutuantes.
    pecas.append(_poly_strip(f"palpebra_sup_{lado}", [(outer, -0.101, 1.589), (s * 0.048, -0.103, 1.595),
                                                      (mid, -0.104, 1.599), (s * 0.024, -0.103, 1.596),
                                                      (inner, -0.101, 1.590)],
                             [0.0016, 0.0021, 0.0026, 0.0021, 0.0015], pele))
    pecas.append(_poly_strip(f"palpebra_inf_{lado}", [(outer, -0.099, 1.581), (s * 0.048, -0.101, 1.578),
                                                      (mid, -0.102, 1.577), (s * 0.024, -0.101, 1.579),
                                                      (inner, -0.099, 1.582)],
                             [0.0012, 0.0017, 0.0020, 0.0017, 0.0012], pele))
    # Sobrancelha em arco com taper nas pontas — grossa o bastante para leitura,
    # mas sem a silhueta retangular do primeiro passe.
    pecas.append(_poly_strip(f"sobrancelha_{lado}", [(outer, -0.106, 1.614), (s * 0.050, -0.108, 1.620),
                                                     (s * 0.040, -0.109, 1.623), (s * 0.028, -0.109, 1.622),
                                                     (s * 0.018, -0.107, 1.619), (inner, -0.105, 1.616)],
                             [0.0020, 0.0028, 0.0034, 0.0032, 0.0025, 0.0017], escuro))
    # Cílios: linha superior e pequenas lâminas, reduzidas para não virar "grades".
    pecas.append(_poly_strip(f"cilios_{lado}", [(outer, -0.107, 1.591), (s * 0.048, -0.109, 1.596),
                                                (mid, -0.110, 1.598), (s * 0.024, -0.109, 1.596),
                                                (inner, -0.107, 1.592)],
                             [0.00075, 0.00095, 0.00115, 0.00095, 0.00070], escuro))
    lash_pts = [(0.055, 1.593), (0.047, 1.597), (0.039, 1.599), (0.030, 1.598), (0.021, 1.594)]
    for i, (ax, az) in enumerate(lash_pts, 1):
        x = s * ax
        pecas.append(_card(f"cilio_{i}_{lado}", [(x - s * 0.00035, -0.111, az), (x + s * 0.00035, -0.111, az),
                                                  (x + s * 0.0024, -0.112, az + 0.0053), (x + s * 0.0016, -0.112, az + 0.0056)],
                           escuro))
    return pecas


def _criar_cabelo(cabelo):
    pecas = []
    # Franja: cachos laterais e mechas curtas no topo — não encobrem os olhos.
    franjas = [
        ("franja_lateral_l", [(-0.070, -0.094, 1.690), (-0.083, -0.104, 1.655), (-0.072, -0.108, 1.615), (-0.088, -0.106, 1.570)], 0.010),
        ("franja_lateral_r", [(0.070, -0.094, 1.690), (0.083, -0.104, 1.655), (0.072, -0.108, 1.615), (0.088, -0.106, 1.570)], 0.010),
        # mechas centrais mais curtas: dão franja sem tapar expressão/olhos.
        ("franja_1", [(-0.045, -0.098, 1.704), (-0.055, -0.104, 1.682), (-0.045, -0.106, 1.662), (-0.052, -0.105, 1.648)], 0.0075),
        ("franja_2", [(-0.006, -0.101, 1.709), (-0.014, -0.107, 1.690), (-0.004, -0.109, 1.672), (-0.010, -0.107, 1.658)], 0.0065),
        ("franja_3", [(0.036, -0.100, 1.706), (0.048, -0.106, 1.685), (0.038, -0.108, 1.665), (0.046, -0.106, 1.650)], 0.0065),
    ]
    for nome, pts, w in franjas:
        pecas.append(_poly_strip(nome, pts, [w, w * 0.92, w * 0.78, w * 0.52], cabelo))

    # Calota/volume da cabeça: seis cards largos, próximos do couro cabeludo.
    for i in range(6):
        a = -1.15 + i * 0.46
        b = a + 0.62
        pts = [(0.085 * math.sin(a), 0.010, 1.703),
               (0.095 * math.sin((a + b) * 0.5), 0.034, 1.665),
               (0.092 * math.sin(b), 0.060, 1.592)]
        pecas.append(_poly_strip(f"calota_{i+1}", pts, [0.022, 0.028, 0.018], cabelo))

    # Rabo de cavalo: exatamente 5 mechas, cada uma sinuosa, saindo do elástico.
    for i in range(5):
        off = (i - 2) * 0.017
        fase = i * 0.73
        pts = []
        for j in range(7):
            t = j / 6.0
            x = off + 0.018 * math.sin(t * TAU * 1.15 + fase) * (0.35 + 0.65 * t)
            y = 0.074 + 0.057 * t + 0.006 * math.sin(t * TAU + fase)
            z = 1.638 - 0.225 * t + 0.020 * math.sin(t * TAU * 1.4 + fase) * (1.0 - 0.25 * t)
            pts.append((x, y, z))
        pecas.append(_poly_strip(f"rabo_mecha_{i+1}", pts,
                                 [0.016, 0.017, 0.016, 0.014, 0.012, 0.010, 0.007], cabelo))
    return pecas


def criar_olhos_e_cards():
    pecas = []
    pele = D.materials.get("PeleJulia") or material("PeleJulia", (0.74, 0.52, 0.40))
    esclera = _mat_principled("Olho_Esclera", (0.82, 0.86, 0.82), 0.30)
    iris = _iris_material()
    cornea = _mat_principled("Olho_Cornea_RefractionBarata", (0.92, 0.98, 1.0), 0.025,
                             transmission=0.55, alpha=0.34)
    escuro = _mat_principled("Sobrancelha_Cilios", (0.030, 0.012, 0.006), 0.74)
    preto = _mat_principled("PupilaJulia", (0.004, 0.003, 0.002), 0.42)

    pecas.extend(_criar_face_extras(pele, escuro))
    mats = (esclera, iris, cornea, preto, pele, escuro)
    for lado, s in (("l", 1.0), ("r", -1.0)):
        pecas.extend(_criar_olho(lado, s, mats))

    cabelo = material_cabelo_alpha()
    pecas.extend(_criar_cabelo(cabelo))
    log("Fase 3: rosto completo com lábios/narinas, olhos separados, pálpebras, sobrancelhas/cílios e cabelo alpha-scissor")
    return pecas


# -----------------------------------------------------------------------------
# 5. Normalização de escala e contato com o solo
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

    # Fase 3 mantém olhos/cards como objetos separados para materiais próprios.
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.select_set(True)
    bpy.context.view_layer.objects.active = obj
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
    normalizar(corpo)
    criar_olhos_e_cards()

    m = metricas(corpo)
    extras = [o for o in bpy.context.scene.objects if o.type == "MESH" and o != corpo]
    m["fase3_objetos"] = len(extras)
    m["rabo_mechas"] = len([o for o in extras if o.name.startswith("rabo_mecha_")])
    m["tris_fase3_extras"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in extras)
    m["tris_glb_total"] = m["tris"] + m["tris_fase3_extras"]
    m["texturas_procedurais_fase3"] = ["julia_cabelo_alpha.png", "julia_iris_color.png", "julia_iris_normal_radial.png"]
    m["alpha_mode"] = "MASK (alpha cutoff 0.5)"
    glb, blend = exportar(corpo)
    m["glb_kb"] = round(glb.stat().st_size / 1024, 1)
    m["gate_tris"] = TRIS_MIN <= m["tris_glb_total"] <= TRIS_MAX
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
