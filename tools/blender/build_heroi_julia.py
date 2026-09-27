#!/usr/bin/env python3
"""Herói 10/10 — corpo base + Fase 3 da heroína Júlia (rebuild do rosto).

Plano: docs/PLANO_HEROI_10_10.md (Fases 1 e 3 — corpo, rosto, olhos e cabelo).
Referência visual: docs/arte_alvo_final/6_model_sheet_heroi.png

Por que um script novo em vez de corrigir `build_humanos.py`: aquele pipeline
gera membros por revolução de anéis (tubos lofted), sem edge loops de
deformação e com UV que estica em qualquer bake. Aqui o corpo nasce de um
esqueleto de arestas + modificador Skin (volume orgânico contínuo), passa por
Subdivision e é **retopologizado por QuadriFlow** em quads distribuídos.

REBUILD DO ROSTO (26/09): a primeira versão da Fase 3 esculpia o rosto no
MESMO tubo do Skin do corpo com pincéis gaussianos e pendurava ~26 peças
(lábios, pálpebras, cílios, franja) em coordenadas Y fixas que não
correspondiam à superfície real da pele — os lábios flutuavam 5 cm à frente
da cara, o queixo afundava no trapézio, as "orelhas" eram um pincel gaussiano
centrado FORA da cabeça e o cabelo eram 6 aletas atrás com o topo careca.

Agora:
  * O grafo do Skin termina no PESCOÇO — a cabeça é um **loft paramétrico
    próprio** (`criar_cabeca`) com perfis explícitos de largura/frente/costas
    por altura: mandíbula, queixo, lábios, nariz, testa e occipital nascem da
    geometria, com os olhos na LINHA MÉDIA do crânio.
  * Orelhas são malhas de verdade (base + hélice + lóbulo) encaixadas no
    lado da cabeça e fazem parte da pele (recebem o bake).
  * TODA a mobília do rosto (globo ocular, pálpebras, sobrancelhas, cílios,
    lábios, narinas, franja) é posicionada por **raycast contra a malha final
    normalizada** (BVHTree) — nada pode flutuar ou enterrar por construção.
  * Cabelo: calota contínua cobrindo o couro (5-9 mm da pele, borda serrada
    por alpha), franja lateral penteada sobre a testa, costeletas na frente
    das orelhas e rabo de cavalo volumétrico de 5 mechas + elástico.
  * `validar_rosto` mede o resultado (perfil nasal, linha dos olhos, órbita,
    aderência de cada peça à pele, saliência da orelha, cobertura da calota)
    e reprova o build se qualquer medida sair da faixa anatômica.

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

from julia_head_v2 import build_corrected_head

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
TRIS_ALVO = 56000           # corpo + rosto/olhos/cabelo geométricos V2
TRIS_MIN, TRIS_MAX = 40000, 72000
QUADRIFLOW_FACES = 7600    # quads -> ~32k tris depois dos loops de junta e das mãos

# --- Proporções (metros, personagem em pé, Z para cima, frente = -Y) ---------
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
def esqueleto_corpo():
    """Retorna (vertices, arestas, raios) do grafo que vira volume no Skin.

    A cadeia TERMINA no pescoço: a cabeça é construída à parte
    (`criar_cabeca`). No primeiro passe da Fase 3 a cabeça eram 4 nós a mais
    deste grafo — o Skin gerava um tubo e o queixo afundava no trapézio.
    """
    nos = {}

    def no(nome, pos, raio):
        nos[nome] = (Vector(pos), raio)
        return nome

    # Tronco (cadeia central)
    no("pelvis", (0.0, 0.010, Z_QUADRIL), 0.108)
    no("cintura", (0.0, 0.000, Z_CINTURA), 0.093)
    no("costela", (0.0, -0.008, Z_COSTELA), 0.107)
    no("peito", (0.0, -0.012, Z_PEITO), 0.115)
    no("ombro_c", (0.0, -0.006, Z_OMBRO), 0.112)
    no("pescoco", (0.0, 0.006, Z_PESCOCO), 0.050)
    # Topo do pescoço: a cabeça do loft (raio ~0.047 ali) encaixa por dentro
    # e a tampa arredondada do Skin fica escondida dentro do crânio.
    no("pescoco_topo", (0.0, 0.008, 1.500), 0.056)

    arestas = [
        ("pelvis", "cintura"), ("cintura", "costela"), ("costela", "peito"),
        ("peito", "ombro_c"), ("ombro_c", "pescoco"),
        ("pescoco", "pescoco_topo"),
    ]

    for lado, s in (("l", 1.0), ("r", -1.0)):
        # Braço: clavícula -> ombro -> cotovelo -> punho. Todos os nós sobre a
        # MESMA reta ombro→punho (A-pose com ~6° de abertura).
        def _braco(t):
            x = X_OMBRO + (X_PUNHO - X_OMBRO) * t
            z = (Z_OMBRO - 0.014) + (Z_PUNHO - (Z_OMBRO - 0.014)) * t
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
        skin_layer[i].radius = (r, r)
    skin_layer[idx["pelvis"]].use_root = True

    sub = obj.modifiers.new("Subsurf", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2

    bpy.ops.object.modifier_apply(modifier="Skin")
    bpy.ops.object.modifier_apply(modifier="Subsurf")
    log(f"base skin+subsurf: {len(obj.data.polygons)} faces")
    return obj


# -----------------------------------------------------------------------------
# 2. Seções anatômicas do CORPO (a cabeça tem pipeline próprio na seção 4)
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
        largura_tronco = 0.135
        feather = 0.055
        m_tronco = 1.0 - min(1.0, max(0.0, (abs(x) - largura_tronco) / feather))

        if Z_VIRILHA < z < Z_OMBRO + 0.02 and m_tronco > 0.0:
            t = (z - Z_VIRILHA) / (Z_OMBRO + 0.02 - Z_VIRILHA)
            largura = 1.0 + (0.06 + 0.16 * math.sin(math.pi * min(1.0, t * 1.15))) * m_tronco
            profundidade = 1.0 - (0.07 - 0.07 * t) * m_tronco
            v.co.x = x * largura
            v.co.y = y * profundidade
            if Z_CINTURA - 0.10 < z < Z_CINTURA + 0.09:
                k = 1.0 - 0.13 * m_tronco * math.cos((z - Z_CINTURA) / 0.10 * math.pi * 0.5)
                v.co.x *= k
                v.co.y *= k * (1.0 - 0.02 * m_tronco)

        if Z_VIRILHA - 0.02 < z < Z_QUADRIL + 0.05:
            v.co.x *= 1.05

        # Pés: achatar no eixo Z, alargar a planta e endireitar o peito do pé
        if z < Z_TORNOZELO:
            t_pe = 1.0 - max(0.0, (z - Z_PE) / max(1e-4, Z_TORNOZELO - Z_PE))
            v.co.z = Z_PE + (z - Z_PE) * 0.50
            v.co.x *= 1.0 + 0.22 * t_pe
            if y < -0.03:
                v.co.x *= 1.12

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
    """Corrective Smooth: tira o facetado do QuadriFlow sem encolher o volume."""
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


# =============================================================================
# 4. CABEÇA PARAMÉTRICA (rebuild da Fase 3)
# =============================================================================
# Marcos em espaço de build (Z para cima, frente = -Y). Cabeça de 0,225 m:
# queixo z=1.507, topo z=1.732, OLHOS na linha média do crânio (z=1.6195).
CABECA = {
    "z_topo": 1.732,
    "z_queixo": 1.507,
    "z_olho": 1.6195,      # (queixo+topo)/2 — linha média, como num rosto real
    "olho_x": 0.0305,
    "olho_r": 0.0118,
    "z_boca": 1.5415,
    "z_brow": 1.633,
    "z_nariz_base": 1.563,
    "z_nariz_ponta": 1.557,
    "orelha_z": 1.6105,    # centro; topo na linha da sobrancelha
    "cabelo_z_frente": 1.676,
}

# Perfis do loft: meia-largura X, extensão frontal e traseira por altura.
# Valores em metros; interpolação linear entre pontos. A mandíbula, o queixo,
# a testa que recua e o occipital estão TODOS aqui — o que o Skin do corpo
# não conseguia formar.
PERFIL_LARGURA = [
    (1.420, 0.0465), (1.460, 0.0495), (1.500, 0.0565), (1.530, 0.0655),
    (1.560, 0.0705), (1.600, 0.0735), (1.635, 0.0745), (1.665, 0.0730),
    (1.700, 0.0645), (1.725, 0.0470), (1.732, 0.0200),
]
PERFIL_FRENTE = [
    (1.420, 0.0455), (1.460, 0.0470), (1.500, 0.0520), (1.530, 0.0585),
    (1.560, 0.0655), (1.580, 0.0700), (1.600, 0.0730), (1.620, 0.0755),
    (1.633, 0.0765), (1.645, 0.0770), (1.660, 0.0775), (1.678, 0.0765),
    (1.695, 0.0730), (1.710, 0.0650), (1.725, 0.0480), (1.732, 0.0260),
]
PERFIL_COSTAS = [
    (1.420, 0.0490), (1.460, 0.0550), (1.500, 0.0615), (1.540, 0.0735),
    (1.580, 0.0870), (1.620, 0.0985), (1.650, 0.1025), (1.680, 0.0960),
    (1.710, 0.0820), (1.725, 0.0560), (1.732, 0.0260),
]

# Dorso do nariz: amplitude por altura (o nariz NÃO está no PERFIL_FRENTE —
# é campo próprio para poder ser estreito e pontudo). ORDENADO CRESCENTE em z.
PONTE_NARIZ = [
    (1.5535, 0.0), (1.558, 0.0205), (1.565, 0.0205), (1.575, 0.0185),
    (1.585, 0.0145), (1.595, 0.0105), (1.605, 0.0070), (1.615, 0.0045),
    (1.626, 0.0025),
]

# Pincéis do rosto (gaussianas elípticas): (cx, cz, rx, rz, amp).
# amp > 0 empurra para a frente (-Y); amp < 0 afunda.
PINCEIS_ROSTO = [
    # ponta do nariz
    (0.0, 1.557, 0.0105, 0.0075, 0.0065),
    # asas do nariz (±)
    (0.0130, 1.5595, 0.0080, 0.0085, 0.0060),
    (-0.0130, 1.5595, 0.0080, 0.0085, 0.0060),
    # narinas (fundinho sob as asas)
    (0.0105, 1.5535, 0.0060, 0.0042, -0.0030),
    (-0.0105, 1.5535, 0.0060, 0.0042, -0.0030),
    # filtro (sulco entre nariz e lábio)
    (0.0, 1.551, 0.0050, 0.0065, -0.0015),
    # lábio superior (com arco de cupido) e inferior
    (0.0, 1.5455, 0.0170, 0.0058, 0.0065),
    (0.0, 1.5365, 0.0140, 0.0062, 0.0075),
    # linha da boca (entra)
    (0.0, 1.5415, 0.0160, 0.0030, -0.0028),
    # queixo e sulco mentolabial
    (0.0, 1.516, 0.0145, 0.0105, 0.0065),
    (0.0, 1.527, 0.0110, 0.0055, -0.0030),
    # órbitas (fundem para o globo assentar)
    (0.0305, 1.6195, 0.0175, 0.0125, -0.0062),
    (-0.0305, 1.6195, 0.0175, 0.0125, -0.0062),
    # arco supraciliar
    (0.031, 1.6325, 0.0210, 0.0068, 0.0032),
    (-0.031, 1.6325, 0.0210, 0.0068, 0.0032),
    # maçãs do rosto
    (0.053, 1.600, 0.0170, 0.0150, 0.0038),
    (-0.053, 1.600, 0.0170, 0.0150, 0.0038),
    # glabela/radix (depressão entre testa e nariz)
    (0.0, 1.622, 0.0110, 0.0080, -0.0024),
]


def _perfil(pontos, z):
    """Interpolação linear numa tabela (z, valor) ordenada."""
    if z <= pontos[0][0]:
        return pontos[0][1]
    if z >= pontos[-1][0]:
        return pontos[-1][1]
    lo, hi = 0, len(pontos) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if pontos[mid][0] <= z:
            lo = mid
        else:
            hi = mid
    (z0, v0), (z1, v1) = pontos[lo], pontos[hi]
    t = (z - z0) / max(1e-9, z1 - z0)
    return v0 + (v1 - v0) * t


def _gauss2(dx, dz, rx, rz):
    return math.exp(-((dx / rx) ** 2 + (dz / rz) ** 2) * 2.2)


def _campo_rosto(z, x):
    """Deslocamento frontal (m) do rosto na altura z e lateral x."""
    d = 0.0
    # dorso do nariz (largura cresce na ponta — o lóbulo é mais largo)
    rx_ponte = 0.0085 + 0.0040 * max(0.0, min(1.0, (1.585 - z) / 0.020))
    if 1.5490 <= z <= 1.6280 and abs(x) < 0.030:
        d += _perfil(PONTE_NARIZ, z) * _gauss2(x, 0.0, rx_ponte, 1.0)
    for cx, cz, rx, rz, amp in PINCEIS_ROSTO:
        if abs(x - cx) < rx * 2.2 and abs(z - cz) < rz * 2.2:
            w = _gauss2(x - cx, z - cz, rx, rz)
            if w > 0.003:
                d += amp * w
    # arco de cupido: vale discreto no centro do lábio superior
    if 1.540 < z < 1.551 and abs(x) < 0.017:
        d -= 0.0065 * 0.35 * math.exp(-((x / 0.0050) ** 2) * 2.2) * _gauss2(0, z - 1.5455, 1, 0.0058)
    return d


def _largura_cabeca(z):
    """Meia-largura analítica da cabeça (para encaixar as orelhas)."""
    return _perfil(PERFIL_LARGURA, z)


def criar_cabeca():
    """Loft da cabeça: anéis horizontais (z) × segmentos (ângulo).

    Cada anel é uma superelipse com meia-largura W(z), extensão frontal F(z)
    (+campo do rosto) e traseira B(z). Resultado: crânio ovalado com occipital,
    mandíbula afinando até o queixo, testa que recua — e os marcos (nariz,
    lábios, órbitas) vêm do MESMO campo usado depois para pendurar a mobília.
    """
    N = 48
    # anéis: denso na zona do rosto, mais espaçado no pescoço/topo
    zs = set()
    zs.update(round(1.420 + i * 0.005, 5) for i in range(17))     # pescoço
    zs.update(round(1.500 + i * 0.0033, 5) for i in range(51))    # rosto
    zs.update(round(1.665 + i * 0.0042, 5) for i in range(17))    # coroa
    zs.update({1.507, 1.516, 1.527, 1.5365, 1.5415, 1.5455, 1.551,
               1.5535, 1.557, 1.5595, 1.563, 1.6195, 1.6325, 1.678, 1.732})
    zs = sorted(z for z in zs if 1.420 <= z <= 1.732)

    verts, faces = [], []

    def anel(z):
        w = _largura_cabeca(z)
        f_base = _perfil(PERFIL_FRENTE, z)
        b = _perfil(PERFIL_COSTAS, z)
        pontos = []
        for j in range(N):
            a = j / N * TAU
            ca, sa = math.cos(a), math.sin(a)
            x = w * sa
            if ca >= 0.0:                        # metade traseira
                y = b * (ca ** 1.15)
            else:                                # metade frontal
                frente = f_base + _campo_rosto(z, x)
                y = -frente * ((-ca) ** 1.15)
            pontos.append((x, y, z))
        return pontos

    grade = [anel(z) for z in zs]
    for linha in grade:
        verts.extend(linha)
    n_c = len(verts)                              # polo da coroa
    verts.append((0.0, 0.008, 1.7335))
    n_b = len(verts)                              # polo da base (dentro do pescoço)
    verts.append((0.0, 0.001, 1.4120))

    for r in range(len(grade) - 1):
        for j in range(N):
            jn = (j + 1) % N
            v0 = r * N + j
            faces.append((v0, r * N + jn, (r + 1) * N + jn, (r + 1) * N + j))
    for j in range(N):                            # coroa
        jn = (j + 1) % N
        faces.append((n_c, (len(grade) - 1) * N + jn, (len(grade) - 1) * N + j))
    for j in range(N):                            # base
        jn = (j + 1) % N
        faces.append((n_b, j, jn))

    me = D.meshes.new("CabecaJulia")
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = D.objects.new("CabecaJulia", me)
    bpy.context.scene.collection.objects.link(obj)
    log(f"cabeça loft: {len(me.polygons)} faces, {len(zs)} anéis")

    # densifica só a zona nariz+boca para o campo ler sem facetas
    bm = bmesh.new()
    bm.from_mesh(me)
    zona = [f for f in bm.faces
            if abs(f.calc_center_median().x) < 0.030
            and 1.538 < f.calc_center_median().z < 1.606]
    if zona:
        bmesh.ops.subdivide_edges(
            bm, edges=list({e for f in zona for e in f.edges}),
            cuts=1, use_grid_fill=True,
        )
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    log(f"cabeça densificada: {len(me.polygons)} faces")
    return obj


# -----------------------------------------------------------------------------
# 4b. Orelhas de verdade (base + hélice + concha), encaixadas no lado da cabeça
# -----------------------------------------------------------------------------
def _esfera_orelha(nome, seg=18, aneis=12):
    """Elipsoide achatado da orelha, com concha afundada e topo mais estreito."""
    hx, hy, hz = 0.0155, 0.0285, 0.0080   # largura, altura, espessura
    verts, faces = [], []
    for i in range(aneis):
        v = -1.0 + 2.0 * i / (aneis - 1)          # -1..1 (altura)
        ry = math.sqrt(max(0.0, 1.0 - v * v))
        # topo da orelha mais estreito que o lóbulo
        wx = hx * (1.0 - 0.28 * max(0.0, v) ** 2)
        wz = hz * ry
        for j in range(seg):
            a = j / seg * TAU
            x = wx * ry * math.cos(a)
            y = hy * v
            z = wz * math.sin(a)
            # concha: fundo raso na face externa, abaixo do centro
            if z > 0:
                g = _gauss2(x - 0.002, y + 0.002, 0.010, 0.014)
                z -= 0.0042 * g
            verts.append((x, y, z))
    n_polos = len(verts)
    verts.append((0.0, -hy, 0.0))
    verts.append((0.0, hy, 0.0))
    for i in range(aneis - 1):
        for j in range(seg):
            jn = (j + 1) % seg
            v0 = i * seg + j
            faces.append((v0, i * seg + jn, (i + 1) * seg + jn, (i + 1) * seg + j))
    for j in range(seg):
        jn = (j + 1) % seg
        faces.append((n_polos, j, jn))
        faces.append((n_polos + 1, (aneis - 1) * seg + jn, (aneis - 1) * seg + j))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def _tubo_helice(nome, lados=6, passos=30):
    """Hélice: tubo fechado correndo pela borda da orelha (pula o lóbulo)."""
    a_el, b_el, r_tubo = 0.0132, 0.0258, 0.0024
    z_h = 0.0062
    # arco de -55° (frente-baixo, trágus) dando a volta por cima até 235°
    a0, a1 = math.radians(-55), math.radians(235)
    verts, faces = [], []
    for i in range(passos):
        t = i / (passos - 1)
        ang = a0 + (a1 - a0) * t
        cx = a_el * math.cos(ang)
        cy = b_el * math.sin(ang)
        # tangente da elipse
        tx, ty = -a_el * math.sin(ang), b_el * math.cos(ang)
        tl = math.hypot(tx, ty)
        nx, ny = tx / tl, ty / tl
        for k in range(lados):
            b = k / lados * TAU
            # seção no plano (normal da elipse, Z local)
            dx = nx * math.cos(b) * r_tubo
            dy = ny * math.cos(b) * r_tubo
            dz = math.sin(b) * r_tubo
            verts.append((cx + dx, cy + dy, z_h + dz))
    for i in range(passos - 1):
        for k in range(lados):
            kn = (k + 1) % lados
            v0 = i * lados + k
            faces.append((v0, i * lados + kn, (i + 1) * lados + kn, (i + 1) * lados + k))
    # tampas (precisa ser fechada: o gate de manifold conta arestas soltas)
    for polo, i in ((len(verts), 0), (len(verts) + 1, passos - 1)):
        verts.append((a_el * math.cos(a0 if polo == len(verts) else a1),
                      b_el * math.sin(a0 if polo == len(verts) else a1), z_h))
    p0 = len(verts) - 2
    for k in range(lados):
        kn = (k + 1) % lados
        faces.append((p0, kn, k))
        faces.append((p0 + 1, (passos - 1) * lados + k, (passos - 1) * lados + kn))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def criar_orelhas():
    """Duas orelhas posicionadas no lado da cabeça, com topo recolhido para
    dentro (o lado da cabeça é curvo) e lóbulo encostado."""
    pecas = []
    # orientação primária: largura->(0,1,0), altura->(0,0,1), espessura->(1,0,0)
    M_ori = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    for lado, s in (("l", 1.0), ("r", -1.0)):
        base = _esfera_orelha(f"orelha_base_{lado}")
        helice = _tubo_helice(f"orelha_helice_{lado}")
        zc = CABECA["orelha_z"]
        xc = 0.0735
        yc = 0.0035
        for o in (base, helice):
            ativar(o)
            if s < 0:  # orelha direita = espelho (winding corrigido abaixo)
                o.scale = (-1.0, 1.0, 1.0)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                me = o.data
                bm = bmesh.new()
                bm.from_mesh(me)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                bm.to_mesh(me)
                bm.free()
            o.rotation_euler = M_ori.to_euler()
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            # inclina o topo para trás ~12° e abre a base para fora ~8°
            o.rotation_euler = (-s * math.radians(12.0), -s * math.radians(8.0), 0.0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            o.location = (s * xc, yc, zc)
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        # recolhe o topo e o lóbulo para DENTRO da pele (o lado é curvo):
        # sem isso a borda da orelha flutuava longe da cabeça
        for o in (base, helice):
            me = o.data
            for v in me.vertices:
                dz_topo = v.co.z - (zc + 0.018)
                dz_base = (zc - 0.018) - v.co.z
                puxa = 0.0
                if dz_topo > 0:
                    puxa = max(puxa, min(1.0, dz_topo / 0.012) * 0.0032)
                if dz_base > 0:
                    puxa = max(puxa, min(1.0, dz_base / 0.012) * 0.0038)
                if puxa > 0:
                    v.co.x -= s * puxa
            me.update()
        pecas.extend([base, helice])
    log(f"orelhas: {len(pecas)} malhas")
    return pecas


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


# =============================================================================
# 6. MOBÍLIA DO ROSTO + CABELO — tudo pendurado por raycast na malha final
# =============================================================================
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


def _mesh(nome, verts, faces, mat, uvs=None, smooth=True, refs=None):
    me = D.meshes.new(nome)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    # normais consistentes (recalc); a direção "para fora" é garantida por refs
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if uvs:
        _assign_uv_from_vertex_uvs(me, uvs)
    for p in me.polygons:
        p.use_smooth = smooth
    if refs:
        # casca aberta (calota, franja, mechas): recalc só torna consistente,
        # não garante "para fora" — vira TUDO se o dot médio der negativo
        refs = [Vector(r) for r in refs]
        bm = bmesh.new()
        bm.from_mesh(me)
        tot = 0.0
        for f in bm.faces:
            c = f.calc_center_median()
            ref = min(refs, key=lambda p: (p - c).length_squared) if len(refs) > 1 else refs[0]
            tot += f.normal.dot(c - ref)
        if tot < 0.0:
            for f in bm.faces:
                f.normal_flip()
        bm.to_mesh(me)
        bm.free()
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _pele_frontal(bvh, x, z, origem=-0.35):
    """Raycast frontal (+Y) na pele: retorna (ponto, normal) ou (None, None)."""
    hit = bvh.ray_cast(Vector((x, origem, z)), Vector((0.0, 1.0, 0.0)), 0.60)
    if hit[0] is None:
        return None, None
    return hit[0], hit[1].normalized()


def _ponto_na_pele(bvh, x, z, offset=0.0005, origem=-0.35):
    p, n = _pele_frontal(bvh, x, z, origem)
    if p is None:
        raise SystemExit(f"[heroi] raycast da pele falhou em (x={x:.3f}, z={z:.3f})")
    return p + n * offset, n


def _fita_na_pele(nome, pontos_xz, larguras, mat, bvh, offset=0.0005):
    """Fita que ACOMPANHA a pele: cada vértice sai de um raycast frontal."""
    if isinstance(larguras, (int, float)):
        larguras = [float(larguras)] * len(pontos_xz)
    verts, uvs = [], []
    for i, (x, z) in enumerate(pontos_xz):
        p, n = _ponto_na_pele(bvh, x, z, offset)
        # direção de largura no plano da cara: perpendicular ao trajeto ~X
        tang = Vector((1.0, 0.0, 0.0)) if i in (0, len(pontos_xz) - 1) else Vector((1.0, 0.0, 0.0))
        wdir = n.cross(tang)
        if wdir.length < 1e-6:
            wdir = Vector((0.0, 0.0, 1.0))
        wdir.normalize()
        if wdir.z < 0:
            wdir = -wdir
        hw = larguras[i]
        verts.append(p - wdir * hw)
        verts.append(p + wdir * hw)
        t = i / (len(pontos_xz) - 1)
        uvs.append((0.0, t))
        uvs.append((1.0, t))
    faces = []
    for i in range(len(pontos_xz) - 1):
        faces.append((2 * i, 2 * i + 1, 2 * (i + 1) + 1, 2 * (i + 1)))
    return _mesh(nome, verts, faces, mat, uvs)


def _grade_na_pele(nome, xs, zs, mat, bvh, offset=0.0004):
    """Grade (x × z) projetada na pele pela frente — casca de lábio etc."""
    verts, uvs = [], []
    for z in zs:
        for x in xs:
            p, n = _ponto_na_pele(bvh, x, z, offset)
            verts.append(p)
            uvs.append((x, z))
    faces = []
    for r in range(len(zs) - 1):
        for c in range(len(xs) - 1):
            a = r * len(xs) + c
            faces.append((a, a + 1, a + len(xs) + 1, a + len(xs)))
    return _mesh(nome, verts, faces, mat, uvs)


def _disco_orientado(nome, centro, normal, rx, rz, mat, seg=20):
    """Disco elíptico num plano qualquer (narina)."""
    n = normal.normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = n.cross(ref).normalized()
    w = n.cross(u).normalized()
    verts, uvs = [centro], [(0.5, 0.5)]
    for i in range(seg):
        a = i / seg * TAU
        verts.append(centro + u * (rx * math.cos(a)) + w * (rz * math.sin(a)))
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    faces = [(0, i + 1, 1 + ((i + 1) % seg)) for i in range(seg)]
    return _mesh(nome, verts, faces, mat, uvs)


def _quad_duplo(nome, p0, p1, p2, p3, mat, uvs=((0, 0), (1, 0), (1, 1), (0, 1)),
                refs=None):
    """Card de cabelo/cílio (o material é doubleSided; refs garante a normal
    apontando para fora da cabeça — sem isso o card sombreia ao contrário)."""
    return _mesh(nome, [p0, p1, p2, p3], [(0, 1, 2, 3), (3, 2, 1, 0)], mat,
                 list(uvs), refs=refs)


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
            dark = 0.72 + 0.28 * limbal
            if r < 0.28:                      # pupila no próprio mapa
                base_r, base_g, base_b = 0.006, 0.005, 0.004
            pix_c.extend((base_r * dark, base_g * dark, base_b * dark, 1.0))
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


def _iris_sobre_globo(nome, centro, raio, olhar, r_iris, mat, seg=28):
    """Íris como calota esférica COLADA no globo (não pode flutuar)."""
    g = olhar.normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(g.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    u = g.cross(ref).normalized()
    w = g.cross(u).normalized()
    verts, uvs = [centro + g * (raio + 0.0002)], [(0.5, 0.5)]
    for i, rr in enumerate((0.55, 1.0)):
        for j in range(seg):
            a = j / seg * TAU
            desvio = (u * math.cos(a) + w * math.sin(a)) * (rr * r_iris / raio)
            d = (g + desvio)
            d.normalize()
            verts.append(centro + d * (raio + 0.0002))
            uvs.append((0.5 + 0.5 * rr * math.cos(a), 0.5 + 0.5 * rr * math.sin(a)))
    faces = [(0, 1 + j, 1 + ((j + 1) % seg)) for j in range(seg)]
    for rr in range(1):
        s0 = 1 + rr * seg
        s1 = 1 + (rr + 1) * seg
        for j in range(seg):
            faces.append((s0 + j, s0 + ((j + 1) % seg), s1 + ((j + 1) % seg), s1 + j))
    return _mesh(nome, verts, faces, mat, uvs)


def material_cabelo_alpha():
    """Textura de fios (u = ao redor, v = no sentido do fio) com borda serrada
    e modo MASK — alpha scissor, mobile-safe, sem ordenação."""
    img = D.images.new("julia_cabelo_alpha", width=256, height=512, alpha=True)
    px = []
    # variação por fio (u): brilho e comprimento da serrilha
    import random
    rnd = random.Random(7)
    fios = []
    for k in range(24):
        fios.append({
            "brilho": 0.75 + 0.5 * rnd.random(),
            "corte": 0.80 + 0.14 * rnd.random(),
            "onda": rnd.uniform(0.0, math.tau),
        })
    for y in range(512):
        v = y / 511.0
        for x in range(256):
            u = x / 255.0
            fi = min(23, int(u * 24))
            f = fios[fi]
            # fio levemente ondulado
            uo = min(1.0, max(0.0, u + 0.012 * math.sin(v * 9.0 + f["onda"])))
            no_fio = math.sqrt(24.0 * uo) % 1.0 < 0.62
            base = 0.055 + 0.045 * f["brilho"] * (0.6 + 0.4 * math.sin(v * 6.0 + f["onda"]))
            r_ = base * 1.45
            g_ = base * 0.78
            b_ = base * 0.42
            if no_fio:
                r_ *= 1.25
                g_ *= 1.20
                b_ *= 1.10
            # alpha: opaco na raiz, ponta serrada por fio
            a = 1.0 if v < f["corte"] else (0.0 if v > f["corte"] + 0.045 else
                                            0.5 + 0.5 * math.sin((v - f["corte"]) / 0.045 * math.pi))
            if v < 0.03:
                a = 1.0
            px.extend((min(1.0, r_), min(1.0, g_), min(1.0, b_), a))
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


# ---- Olhos ------------------------------------------------------------------
def _criar_olho(lado, s, mats, bvh):
    """Globo recuado na órbita + íris colada + córnea + pálpebras que nascem
    NO globo e pousam NA pele (raycast) + cílios na borda da pálpebra."""
    pecas = []
    esclera, iris, cornea, pele, escuro = mats
    ex, ez = s * CABECA["olho_x"], CABECA["z_olho"]
    r = CABECA["olho_r"]

    # fundo da órbita pela pele real
    p_orb, n_orb = _ponto_na_pele(bvh, ex, ez, 0.0)
    centro = p_orb - n_orb * (r - 0.0026)      # polo 2,6 mm à frente da pele
    olhar = Vector((s * 0.045, -1.0, -0.05)).normalized()

    # esclera: esfera completa (o resto fica dentro da órbita)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12,
                                         location=tuple(centro), radius=r)
    scl = bpy.context.object
    scl.name = f"esclera_{lado}"
    ativar(scl)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scl.data.materials.append(esclera)
    pecas.append(scl)

    # íris: calota colada no globo, olhando 4,5° para o nariz
    pecas.append(_iris_sobre_globo(f"iris_{lado}", centro, r, olhar, 0.0056, iris))

    # córnea: mesma esfera avançada 1,6 mm — bulge só na região da íris
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10,
                                         location=tuple(centro + olhar * 0.0016), radius=r)
    co = bpy.context.object
    co.name = f"cornea_{lado}"
    ativar(co)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co.data.materials.append(cornea)
    pecas.append(co)

    # base ortonormal do olho (u = horizontal, w = vertical)
    u = olhar.cross(Vector((0.0, 0.0, 1.0))).normalized()
    w = u.cross(olhar).normalized()
    r_sup = r + 0.0019        # pálpebra a 1,9 mm do globo
    # fissura palpebral (da comissura interna à externa), em (u, w) metros
    sup_pts = [(-0.0145, 0.0012), (-0.0090, 0.0050), (-0.0025, 0.0059),
               (0.0040, 0.0052), (0.0095, 0.0036), (0.0145, 0.0004)]
    inf_pts = [(-0.0145, -0.0006), (-0.0090, -0.0042), (-0.0025, -0.0056),
               (0.0040, -0.0049), (0.0095, -0.0033), (0.0145, -0.0016)]
    lid_pts = {}

    def ponto_globo(du, dw, raio):
        d = olhar + u * (du / raio) + w * (dw / raio)
        d.normalize()
        return centro + d * raio

    for nome, pts, sobe in (("sup", sup_pts, 1.0), ("inf", inf_pts, -1.0)):
        verts, uvs = [], []
        for i, (du, dw) in enumerate(pts):
            borda = ponto_globo(du, dw, r_sup)                 # no globo
            meio = ponto_globo(du, dw + sobe * 0.0028, r_sup)  # 6° acima
            # pouso na pele: raycast frontal no (x, z) do meio
            p_pele, n_pele = _ponto_na_pele(bvh, meio.x, meio.z, 0.0006)
            verts.extend([borda, meio, p_pele])
            t = i / (len(pts) - 1)
            uvs.extend([(t, 0.0), (t, 0.5), (t, 1.0)])
            lid_pts[(nome, i)] = (borda, meio, p_pele, n_pele)
        faces = []
        for i in range(len(pts) - 1):
            a = i * 3
            faces.append((a, a + 1, a + 4, a + 3))       # borda->meio
            faces.append((a + 1, a + 2, a + 5, a + 4))   # meio->pele
        pecas.append(_mesh(f"palpebra_{nome}_{lado}", verts, faces, pele, uvs))

    # cílios: lâminas na BORDA da pálpebra superior (mesmos vértices — sem flutuar)
    for i in (1, 2, 3, 4):
        borda, meio, _, _ = lid_pts[("sup", i)]
        raio_v = (borda - centro).normalized()
        tang = w.cross(raio_v).normalized()
        L = 0.0034
        ponta = borda + raio_v * (L * 0.62) + Vector((0.0, 0.0, L * 0.55)) \
                + tang * (s * L * 0.18)
        p0 = borda - tang * 0.00035
        p1 = borda + tang * 0.00035
        pecas.append(_quad_duplo(f"cilio_{i}_{lado}", p0, p1,
                                 ponta + tang * 0.00018, ponta - tang * 0.00018, escuro,
                                 refs=[centro - olhar * 0.03]))
    return pecas, centro, olhar


# ---- Lábios, boca, narinas, sobrancelhas ------------------------------------
def _criar_face_extras(mats, bvh):
    pecas = []
    pele, escuro = mats
    labios = _mat_principled("LabiosJulia", (0.42, 0.155, 0.125), 0.5)
    boca = _mat_principled("LinhaBocaJulia", (0.10, 0.032, 0.026), 0.74)
    narina = _mat_principled("NarinaJulia", (0.05, 0.021, 0.016), 0.85)
    sobr = _mat_principled("SobrancelhaJulia", (0.16, 0.09, 0.05), 0.62)

    # cascas dos lábios: grades projetadas na pele ESCULPIDA (o volume já está
    # na geometria da cabeça; a casca só dá a cor)
    xs_sup = [x * 0.0185 for x in (-1.0, -0.6, -0.25, 0.0, 0.25, 0.6, 1.0)]
    zs_sup = [1.5405, 1.5430, 1.5455, 1.5478]
    pecas.append(_grade_na_pele("labio_superior", xs_sup, zs_sup, labios, bvh, 0.00035))
    xs_inf = [x * 0.0155 for x in (-1.0, -0.6, -0.25, 0.0, 0.25, 0.6, 1.0)]
    zs_inf = [1.5352, 1.5378, 1.5403]
    pecas.append(_grade_na_pele("labio_inferior", xs_inf, zs_inf, labios, bvh, 0.00035))

    # linha da boca: fita escura no sulco
    pecas.append(_fita_na_pele(
        "linha_boca",
        [(-0.0165, 1.5415), (-0.0100, 1.5411), (0.0, 1.5410),
         (0.0100, 1.5411), (0.0165, 1.5415)],
        [0.0005, 0.0009, 0.0011, 0.0009, 0.0005], boca, bvh, 0.00025))

    # narinas: discos orientados pela normal da pele sob as asas do nariz
    for s, lado in ((1.0, "l"), (-1.0, "r")):
        p, n = _ponto_na_pele(bvh, s * 0.0105, 1.5535, 0.00015)
        n = (n + Vector((0.0, -0.25, -0.55))).normalized()
        pecas.append(_disco_orientado(f"narina_{lado}", p, n, 0.0030, 0.0016, narina))

    # sobrancelhas em arco, a 0,7 mm da pele, com taper
    for s, lado in ((1.0, "l"), (-1.0, "r")):
        arco = [(0.0165, 1.6290), (0.0260, 1.6330), (0.0345, 1.6362),
                (0.0425, 1.6368), (0.0495, 1.6345)]
        pecas.append(_fita_na_pele(
            f"sobrancelha_{lado}", [(s * x, z) for x, z in arco],
            [0.0022, 0.0034, 0.0042, 0.0036, 0.0024], sobr, bvh, 0.0007))
    return pecas


# ---- Cabelo: calota + franja + costeletas + rabo -----------------------------
def _linha_cabelo_z(theta):
    """Altura da linha do cabelo por azimute (0 = frente, pi = nuca)."""
    t = abs(math.atan2(math.sin(theta), math.cos(theta)))
    pts = [(0.0, 1.6765), (0.6, 1.669), (1.2, 1.651), (1.7, 1.613), (math.pi, 1.598)]
    return _perfil(pts, t)


def _catmull_rom(pontos, t):
    """Catmull-Rom por uma lista de Vectors, t em [0, 1]."""
    n = len(pontos) - 1
    x = t * n
    i = min(n - 1, int(x))
    f = x - i
    p0 = pontos[max(0, i - 1)]
    p1 = pontos[i]
    p2 = pontos[i + 1]
    p3 = pontos[min(n, i + 2)]
    return (p1 + (p2 - p0) * 0.5 * f
            + (p0 - p1 * 2.5 + p2 * 2.0 - p3 * 0.5) * f * f
            + (-p0 * 0.5 + p1 * 1.5 - p2 * 1.5 + p3 * 0.5) * f * f * f)


def _centro_cranio(corpo):
    """Centro interno do crânio (origem dos raios da calota), pós-normalização."""
    z_topo = max(v.co.z for v in corpo.data.vertices if v.co.z > 1.49)
    return Vector((0.0, 0.020, z_topo - 0.112))


def _criar_cabelo(cabelo_mat, bvh_pele, centro_cabeca):
    """Calota contínua (cobre o couro TODO), franja penteada de lado,
    costeletas na frente das orelhas e rabo de cavalo volumétrico."""
    pecas = []
    M, ROWS = 56, 6
    C = Vector(centro_cabeca)

    def dir_esferico(theta, phi):
        st, ct = math.sin(phi), math.cos(phi)
        return Vector((st * math.sin(theta), -st * math.cos(theta), ct))

    # acha o ângulo da linha do cabelo varrendo phi para cada azimute
    # (phi medido a partir do topo; varre até ~112° para alcançar a nuca)
    phi_max = {}
    for j in range(M):
        theta = j / M * TAU
        z_alvo = _linha_cabelo_z(theta)
        prev_phi, prev_z = 0.0, None
        achou = 1.6
        for k in range(1, 41):
            phi = k / 40.0 * 1.95
            d = dir_esferico(theta, phi)
            hit = bvh_pele.ray_cast(C + d * 0.40, -d, 0.70)
            if hit[0] is not None:
                z_hit = hit[0].z
                if z_hit <= z_alvo:
                    if prev_z is None:
                        achou = phi
                    else:
                        frac = (prev_z - z_alvo) / max(1e-6, prev_z - z_hit)
                        frac = max(0.0, min(1.0, frac))
                        achou = prev_phi + (phi - prev_phi) * frac
                    break
                prev_phi, prev_z = phi, z_hit
        phi_max[j] = max(0.14, achou)

    # grade da calota: polo no topo + anéis até a borda
    verts, uvs, faces = [], [], []
    for i in range(1, ROWS + 1):
        t = i / ROWS
        for j in range(M):
            theta = j / M * TAU
            phi = phi_max[j] * (0.14 + 0.86 * t)
            d = dir_esferico(theta, phi)
            hit = bvh_pele.ray_cast(C + d * 0.40, -d, 0.70)
            if hit[0] is None:
                raise SystemExit(f"[heroi] calota: sem hit theta={theta:.2f} phi={phi:.2f}")
            p, n = hit[0], hit[1].normalized()
            # volume: mais alto no topo; coque do rabo acima da nuca
            offset = 0.0045 + 0.0035 * (1.0 - t) ** 1.5
            th_norm = abs(math.atan2(math.sin(theta), math.cos(theta))) / math.pi
            if t > 0.55 and th_norm > 0.62:
                offset += 0.0035 * (th_norm - 0.62) / 0.38
            verts.append(p + n * offset)
            uvs.append((j / M, t))
    n_pol = len(verts)
    coroa_hit = bvh_pele.ray_cast(C + Vector((0, 0, 1)) * 0.40, Vector((0, 0, -1)), 0.70)
    verts.append(coroa_hit[0] + coroa_hit[1] * 0.0095)
    uvs.append((0.5, 0.0))
    for j in range(M):
        jn = (j + 1) % M
        faces.append((n_pol, jn, j))
    for i in range(ROWS - 1):
        for j in range(M):
            jn = (j + 1) % M
            a = i * M + j
            faces.append((a, a + 1, (i + 1) * M + jn, (i + 1) * M + j))
    pecas.append(_mesh("calota_cabelo", verts, faces, cabelo_mat, uvs, refs=[C]))

    # borda da calota (anel externo) por índice de azimute
    borda = {j: Vector(verts[(ROWS - 1) * M + j]) for j in range(M)}

    # franja: cards da BORDA da calota descendo sobre a testa, penteando p/ +X
    def theta_de(j):
        t = j / M * TAU
        return t if t <= math.pi else t - TAU

    js = sorted((j for j in range(M) if -1.0 <= theta_de(j) <= 0.9), key=theta_de)
    n_fr = 0
    for k in range(0, len(js) - 1, 2):
        j0, j1 = js[k], js[k + 1]
        r0, r1 = borda[j0].copy(), borda[j1].copy()
        th_n = min(1.0, abs(theta_de(j0 + 1)) / 0.95)
        varredura = 0.020 * max(0.0, 1.0 - th_n)
        z_tip = 1.6485 + 0.0050 * th_n

        def ponta(rx):
            x_t = rx + varredura * (0.4 + 0.6 * abs(rx) / 0.08)
            p, _ = _ponto_na_pele(bvh_pele, x_t, z_tip, 0.0042)
            return p

        t0, t1 = ponta(r0.x), ponta(r1.x)
        m0 = (r0 + t0) * 0.5 + (t0 - r0).normalized() * 0.0008
        m1 = (r1 + t1) * 0.5 + (t1 - r1).normalized() * 0.0008
        nome = f"franja_{n_fr}"
        n_fr += 1
        pecas.append(_mesh(
            nome,
            [r0, r1, m1, m0, t0, t1],
            [(0, 1, 2, 3), (3, 2, 5, 4)],
            cabelo_mat,
            uvs=[(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.0, 0.5), (0.0, 1.0), (1.0, 1.0)],
            refs=[C],
        ))

    # costeletas: mecha na frente de cada orelha ( segue o lado da cara,
    # não a borda da calota, para o raycast sempre achar a pele)
    for s, lado in ((1.0, "l"), (-1.0, "r")):
        j_alvo = int(round((0.5 - s * 0.285) % 1.0 * M)) % M
        r0 = borda[j_alvo].copy()
        r1 = borda[(j_alvo + 1) % M].copy()
        x_face = s * 0.062
        p0, _ = _ponto_na_pele(bvh_pele, x_face, 1.600, 0.0035)
        p1, _ = _ponto_na_pele(bvh_pele, x_face * 0.988, 1.598, 0.0035)
        q0, _ = _ponto_na_pele(bvh_pele, x_face * 0.962, 1.583, 0.0028)
        q1, _ = _ponto_na_pele(bvh_pele, x_face * 0.950, 1.581, 0.0028)
        pecas.append(_mesh(
            f"costeleta_{lado}",
            [r0, r1, p1, p0, q0, q1],
            [(0, 1, 2, 3), (3, 2, 5, 4)],
            cabelo_mat,
            uvs=[(0.0, 0.0), (1.0, 0.0), (1.0, 0.55), (0.0, 0.55), (0.0, 1.0), (1.0, 1.0)],
            refs=[C],
        ))

    # rabo de cavalo: 5 mechas tubulares + elástico
    ctrl = [Vector((0.0, 0.070, 1.648)), Vector((0.0, 0.103, 1.632)),
            Vector((0.0, 0.122, 1.598)), Vector((0.0, 0.124, 1.555)),
            Vector((0.0, 0.117, 1.515)), Vector((0.0, 0.108, 1.478))]
    offsets = [(-0.019, -0.004), (-0.010, 0.003), (0.0, 0.006),
               (0.010, 0.003), (0.019, -0.004)]
    LADOS_TUBO, ANEIS = 10, 9
    centros_mecha = []
    for i, (ox, oy) in enumerate(offsets):
        verts, uvs, faces = [], [], []
        fase = i * 1.9
        pontos = []
        for k in range(ANEIS):
            t = k / (ANEIS - 1)
            p = _catmull_rom(ctrl, t).copy()
            conv = max(0.22, 1.0 - 0.62 * t)
            p.x += ox * conv + 0.0042 * math.sin(t * TAU * 1.35 + fase)
            p.z += 0.006 * math.sin(t * TAU * 1.1 + i * 1.3)
            pontos.append(p)
        centros_mecha.append(pontos)
        for k, p in enumerate(pontos):
            t = k / (ANEIS - 1)
            tang = (pontos[min(ANEIS - 1, k + 1)] - pontos[max(0, k - 1)]).normalized()
            ref = Vector((1.0, 0.0, 0.0))
            if abs(tang.dot(ref)) > 0.9:
                ref = Vector((0.0, 0.0, 1.0))
            n1 = tang.cross(ref).normalized()
            n2 = tang.cross(n1).normalized()
            a = 0.0092 * (1.0 - 0.60 * t)
            b = 0.0120 * (1.0 - 0.62 * t)
            for q in range(LADOS_TUBO):
                ang = q / LADOS_TUBO * TAU
                verts.append(p + n1 * (a * math.cos(ang)) + n2 * (b * math.sin(ang)))
                uvs.append((q / LADOS_TUBO, t))
        # tampas (fechadas: sem aresta solta)
        pol_a = len(verts)
        verts.append(pontos[0])
        verts.append(pontos[-1] - (pontos[-1] - pontos[-2]).normalized() * 0.002)
        uvs.append((0.5, 0.0))
        uvs.append((0.5, 1.0))
        for q in range(LADOS_TUBO):
            qn = (q + 1) % LADOS_TUBO
            faces.append((pol_a, qn, q))
            faces.append((pol_a + 1, (ANEIS - 1) * LADOS_TUBO + q, (ANEIS - 1) * LADOS_TUBO + qn))
        for k in range(ANEIS - 1):
            for q in range(LADOS_TUBO):
                qn = (q + 1) % LADOS_TUBO
                a0 = k * LADOS_TUBO + q
                faces.append((a0, k * LADOS_TUBO + qn, (k + 1) * LADOS_TUBO + qn, (k + 1) * LADOS_TUBO + q))
        pecas.append(_mesh(f"rabo_mecha_{i+1}", verts, faces, cabelo_mat, uvs,
                           refs=pontos))

    # elástico: anel tubular ao redor do feixe no 2º anel das mechas
    tie = _mat_principled("RaboElastico", (0.09, 0.035, 0.02), 0.55)
    centro_tie = Vector((0.0, 0.0, 0.0))
    for pts in centros_mecha:
        centro_tie += pts[1]
    centro_tie = centro_tie / len(centros_mecha)
    tang_tie = (centros_mecha[2][2] - centro_tie).normalized()
    ref = Vector((1.0, 0.0, 0.0))
    n1 = tang_tie.cross(ref).normalized()
    n2 = tang_tie.cross(n1).normalized()
    verts, uvs, faces = [], [], []
    SEG, LAD = 30, 6
    for j in range(SEG):
        ang = j / SEG * TAU
        cx = centro_tie + n1 * (0.0275 * math.cos(ang)) + n2 * (0.0150 * math.sin(ang))
        tx = -n1 * math.sin(ang) + n2 * math.cos(ang)
        for k in range(LAD):
            b = k / LAD * TAU
            verts.append(cx + tx * (0.0038 * math.cos(b)) + tang_tie * (0.0038 * math.sin(b)))
            uvs.append((j / SEG, k / LAD))
    for j in range(SEG):
        jn = (j + 1) % SEG
        for k in range(LAD):
            kn = (k + 1) % LAD
            faces.append((j * LAD + k, j * LAD + kn, jn * LAD + kn, jn * LAD + k))
    pecas.append(_mesh("rabo_elastico", verts, faces, tie, uvs, refs=[centro_tie]))
    return pecas


def criar_rosto_e_cabelo(corpo):
    """Pendura TODO o conjunto do rosto/cabelo na malha normalizada, por raycast."""
    pecas = []
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_pele = BVHTree.FromObject(corpo, dg)

    pele = material("PeleJulia", (0.63, 0.45, 0.35), rough=0.55)
    esclera = _mat_principled("Olho_Esclera", (0.86, 0.84, 0.80), 0.32)
    iris = _iris_material()
    cornea = _mat_principled("Olho_Cornea_RefractionBarata", (0.92, 0.98, 1.0), 0.025,
                             transmission=0.55, alpha=0.34)
    escuro = _mat_principled("Sobrancelha_Cilios", (0.05, 0.020, 0.010), 0.7)

    pecas.extend(_criar_face_extras((pele, escuro), bvh_pele))
    mats_olho = (esclera, iris, cornea, pele, escuro)
    olhos = []
    for lado, s in (("l", 1.0), ("r", -1.0)):
        partes, centro, olhar = _criar_olho(lado, s, mats_olho, bvh_pele)
        pecas.extend(partes)
        olhos.append(centro)
    del olhos

    cabelo = material_cabelo_alpha()
    pecas.extend(_criar_cabelo(cabelo, bvh_pele, _centro_cranio(corpo)))
    log("Fase 3 rebuild: rosto com órbitas/pálpebras/cílios/sobrancelhas/lábios, "
        "orelhas na pele, calota de cabelo + franja + rabo volumétrico")
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

    # Rosto e cabelo V2 ficam separados para preservar materiais próprios.
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
    log("Fase 1 — corpo base da heroína Júlia (Skin termina no pescoço)")
    corpo = criar_base_skin()
    moldar_secoes(corpo)
    retopo(corpo)
    suavizar(corpo)
    loops_de_deformacao(corpo)
    densificar_cabeca(corpo)
    # A cabeça V1 era uma extensão do modificador Skin: formato bulboso,
    # feições desenhadas como cards e cabelo em placas. Mantemos apenas o
    # volume interno para continuidade do pescoço e construímos a cabeça V2
    # com anatomia e geometria próprias após normalizar o corpo.
    juntar(corpo, criar_maos())
    normalizar(corpo)
    build_corrected_head(corpo)

    m = metricas(corpo)
    extras = [o for o in bpy.context.scene.objects if o.type == "MESH" and o != corpo]
    m["face_hair_objects"] = len(extras)
    m["ponytail_curls"] = len([o for o in extras if o.name.startswith("RaboCacho_")])
    m["tris_face_hair_extras"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in extras)
    m["tris_glb_total"] = m["tris"] + m["tris_face_hair_extras"]
    m["face_v2"] = {
        "ears": 2,
        "separate_eyelids": 4,
        "separate_eyes": True,
        "eyelashes": 8,
        "volumetric_curly_hair": True,
        "mouth_geometry": True,
    }
    m["alpha_mode"] = "OPAQUE (cabelo geométrico; sem cards)"
    glb, blend = exportar(corpo)
    m["glb_kb"] = round(glb.stat().st_size / 1024, 1)
    m["gate_tris"] = TRIS_MIN <= m["tris_glb_total"] <= TRIS_MAX
    m["gate_altura"] = 1.70 <= m["altura_m"] <= 1.75
    m["gate_piso"] = abs(m["piso_z_m"] - PISO_OFFSET) < 0.005
    m["gate_manifold"] = m["arestas_nao_manifold"] == 0
    m["gate"] = all(m[k] for k in ("gate_tris", "gate_altura", "gate_piso",
                                   "gate_manifold", "gate_rosto"))

    (OUT_DIR / "heroi_julia_metrics.json").write_text(json.dumps(m, indent=2))
    log(json.dumps(m, indent=2))
    log(f"GLB: {glb}")
    log(f"BLEND: {blend}")
    return 0 if m["gate"] else 1




if __name__ == "__main__":
    sys.exit(main())
