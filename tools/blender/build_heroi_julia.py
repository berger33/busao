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
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

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
# A cabeça própria (~9k tris) e as orelhas entram no orçamento: o corpo cede
# densidade (era 7.600) para o total continuar dentro do gate 24k-46k.
QUADRIFLOW_FACES = 6000

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
        no(f"punho_{lado}", _braco(1.00), 0.031)
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
# 3b. Mãos: 5 dedos separados (o Skin do corpo só entrega a palma como bloco)
# -----------------------------------------------------------------------------
DEDOS = [
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
        (0.00, largura * 0.40, espessura * 0.46),
        (0.30, largura * 0.50, espessura * 0.50),
        (0.72, largura * 0.50, espessura * 0.45),
        (1.00, largura * 0.46, espessura * 0.38),
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
    largura = 0.082
    espessura = 0.030
    comprimento = 0.060
    for lado, s in (("l", 1.0), ("r", -1.0)):
        px_ = s * (X_PUNHO + 0.004)
        py_ = -0.012
        z_punho = Z_PUNHO - 0.004
        pecas.append(_laje_palma(f"palma_{lado}", (px_, py_, z_punho),
                                 largura, espessura, comprimento))
        z_nos = z_punho - comprimento

        for nome, dx, dy, comp, raio in DEDOS:
            x = px_ + s * dx
            y = py_ + dy
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
    log(f"peças unidas ao corpo: {len(corpo.data.polygons)} faces")
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


# =============================================================================
# 7. Validação geométrica do rosto (gate numérico — não dependemos do olho)
# =============================================================================
def validar_rosto(corpo, extras):
    """Mede o resultado contra faixas anatômicas. Retorna dict de gates."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bvh_pele = BVHTree.FromObject(corpo, dg)

    def pele_frontal(x, z):
        hit = bvh_pele.ray_cast(Vector((x, -0.35, z)), Vector((0.0, 1.0, 0.0)), 0.60)
        return hit[0]

    # dados da pele (só cabeça)
    cab = [v.co.copy() for v in corpo.data.vertices if v.co.z > 1.49]
    z_topo = max(v.z for v in cab)
    # queixo = ponto mais baixo À FRENTE (y < -0.057 exclui a garganta, que
    # fica a ~-0.05; antes o gate media a garganta e dava queixo 13 mm baixo)
    z_queixo = min(v.z for v in cab if abs(v.x) < 0.02 and v.y < -0.057)
    larg = [v.x for v in cab if abs(v.z - CABECA["z_olho"]) < 0.006]
    prof_f = [v.y for v in cab if abs(v.z - CABECA["z_olho"]) < 0.006 and abs(v.x) < 0.02]

    g = {}

    # 1) nariz mais avançado que a testa/sobrancelha
    nariz_tip = min((v.y for v in cab if 1.552 < v.z < 1.562 and abs(v.x) < 0.006), default=0)
    brow = min((v.y for v in cab if 1.628 < v.z < 1.640 and abs(v.x) < 0.05), default=0)
    testa = min((v.y for v in cab if 1.60 < v.z < 1.675 and abs(v.x) < 0.04), default=0)
    g["nariz_avanca"] = (nariz_tip < brow - 0.006) and (nariz_tip < testa - 0.008)
    g["nariz_medidas"] = f"tip={-nariz_tip:.4f} brow={-brow:.4f} testa={-testa:.4f}"

    # 2) olhos na linha média do crânio
    iris = next(o for o in extras if o.name.startswith("iris_"))
    z_iris = sum(v.co.z for v in iris.data.vertices) / len(iris.data.vertices)
    meio = (z_queixo + z_topo) / 2.0
    g["olho_linha_media"] = abs(z_iris - meio) < 0.008
    g["olho_medidas"] = f"iris_z={z_iris:.4f} meio={meio:.4f} queixo={z_queixo:.4f} topo={z_topo:.4f}"

    # 3) mandíbula fina (o trapézio não engole o queixo)
    banda = [abs(v.x) for v in cab if abs(v.z - 1.515) < 0.005]
    g["mandibula"] = max(banda, default=1) < 0.075
    g["mandibula_medidas"] = f"larg_1.515={2 * max(banda, default=0):.4f}"

    # 4) proporções do crânio na linha dos olhos
    w_olho = (max(larg) - min(larg)) if larg else 0
    d_olho = -min(prof_f) if prof_f else 0
    g["cranio_proporcoes"] = (0.132 <= w_olho <= 0.162) and (0.068 <= d_olho <= 0.086)
    g["cranio_medidas"] = f"larg={w_olho:.4f} frente={d_olho:.4f}"

    # 5) olho recuado na órbita, polo à frente da pele
    for lado, s in (("l", 1.0), ("r", -1.0)):
        scl = next(o for o in extras if o.name == f"esclera_{lado}")
        c = scl.matrix_world @ (sum((v.co for v in scl.data.vertices), Vector())
                                / len(scl.data.vertices))
        p_orb = pele_frontal(s * CABECA["olho_x"], c.z)
        dist_orb = (c - p_orb).length if p_orb else 1.0
        g[f"olho_orbita_{lado}"] = 0.006 <= dist_orb <= 0.012
        g[f"olho_orbita_{lado}_medidas"] = f"centro->pele={dist_orb:.4f}"

    # 6) pálpebra abraça o globo
    for nome in ("palpebra_sup_l", "palpebra_inf_l"):
        pal = next(o for o in extras if o.name == nome)
        scl = next(o for o in extras if o.name == "esclera_l")
        c = scl.matrix_world @ (sum((v.co for v in scl.data.vertices), Vector())
                                / len(scl.data.vertices))
        r_alvo = CABECA["olho_r"] + 0.0019
        ds = [(pal.data.vertices[i].co - c).length for i in range(0, len(pal.data.vertices), 3)]
        na_globo = sum(1 for d in ds if abs(d - r_alvo) < 0.0016)
        g[f"{nome}_globo"] = na_globo >= 5
        g[f"{nome}_globo_medidas"] = f"bordas_no_globo={na_globo}/6"

    # 7) sobrancelha/lábio a menos de 2,2 mm da pele (nada flutuando)
    def aderencia(nome):
        o = next(x for x in extras if x.name == nome)
        pior = 0.0
        n_sem = 0
        for v in o.data.vertices:
            p = pele_frontal(v.co.x, v.co.z)
            if p is not None:
                pior = max(pior, abs((p - v.co).y))
            else:
                n_sem += 1
        return pior, n_sem

    for nome in ("sobrancelha_l", "labio_superior", "labio_inferior", "linha_boca"):
        pior, n_sem = aderencia(nome)
        g[f"{nome}_pele"] = pior < 0.0022 and n_sem == 0
        g[f"{nome}_pele_medidas"] = f"desvio={pior:.4f} sem_hit={n_sem}"

    # 8) orelha: saltando do lado da cabeça (medida na pele, onde foi unida)
    # o crânio sem orelha tem meia-largura <= 0.0745; orelha passa disso
    sal = max((abs(v.x) for v in cab if 1.596 < v.z < 1.624), default=0)
    lateral_sem_orelha = max((abs(v.x) for v in cab if abs(v.z - 1.570) < 0.004), default=0)
    z_orelha_topo = max((v.z for v in cab if abs(v.x) > 0.0765), default=0)
    z_orelha_base = min((v.z for v in cab if abs(v.x) > 0.0765), default=0)
    alt_orelha = z_orelha_topo - z_orelha_base
    g["orelha_existe"] = alt_orelha > 0.040
    g["orelha_saliencia"] = (sal - lateral_sem_orelha) >= 0.006
    g["orelha_medidas"] = (f"altura={alt_orelha:.4f} saliencia={sal - lateral_sem_orelha:.4f} "
                           f"base_sem_orelha={lateral_sem_orelha:.4f}")

    # 9) calota cobre o couro: raios de fora para dentro
    cabelo_objs = [o for o in extras if o.name.startswith(("calota", "franja", "costeleta", "rabo"))]
    bvhs_cabelo = [BVHTree.FromObject(o, dg) for o in cabelo_objs]
    C = _centro_cranio(corpo)
    furos, amostras = 0, 0
    for j in range(24):
        theta = j / 24 * TAU
        for k in range(5):
            phi = 0.18 + k * 0.20
            st, ct = math.sin(phi), math.cos(phi)
            d = Vector((st * math.sin(theta), -st * math.cos(theta), ct))
            origem = C + d * 0.40
            hit_pele = bvh_pele.ray_cast(origem, -d, 0.70)
            if hit_pele[0] is not None and hit_pele[0].z > _linha_cabelo_z(theta) - 0.004:
                amostras += 1
                melhor = None
                for bv in bvhs_cabelo:
                    hit_cab = bv.ray_cast(origem, -d, 0.70)
                    if hit_cab[0] is not None:
                        melhor = hit_cab[3] if melhor is None else min(melhor, hit_cab[3])
                if melhor is None or melhor > hit_pele[3] + 0.001:
                    furos += 1
    g["calota_cobre"] = amostras > 0 and furos == 0
    g["calota_medidas"] = f"amostras={amostras} furos={furos}"

    # 10) franja não cobre os olhos
    franjas = [o for o in extras if o.name.startswith("franja_")]
    z_min_franja = min((v.co.z for o in franjas for v in o.data.vertices), default=0)
    g["franja_livre"] = z_min_franja > CABECA["z_olho"] + 0.024
    g["franja_medidas"] = f"ponta_min={z_min_franja:.4f} (olho {CABECA['z_olho']:.4f})"

    # 11) rabo: 5 mechas NA NUCA (z 1.44–1.70, atrás y>0.03)
    mechas = [o for o in extras if o.name.startswith("rabo_mecha_")]
    zs = [v.co.z for o in mechas for v in o.data.vertices]
    ys = [v.co.y for o in mechas for v in o.data.vertices]
    no_lugar = bool(mechas) and 1.42 < min(zs) < 1.53 and 1.59 < max(zs) < 1.71 \
        and min(ys) > 0.03
    g["rabo_mechas"] = len(mechas) == 5 and no_lugar
    g["rabo_medidas"] = (f"n={len(mechas)} z=[{min(zs):.3f},{max(zs):.3f}] "
                         f"y=[{min(ys):.3f},{max(ys):.3f}]")

    # 12) cílios presos na borda da pálpebra (comparação POR OLHO)
    cilios = [o for o in extras if o.name.startswith("cilio_") and o.name.endswith("_l")]
    pal_sup = next(o for o in extras if o.name == "palpebra_sup_l")
    borda = [pal_sup.data.vertices[i].co for i in range(0, len(pal_sup.data.vertices), 3)]
    pior = 0.0
    for c in cilios:
        r0 = c.data.vertices[0].co
        pior = max(pior, min((r0 - b).length for b in borda))
    g["cilios_borda"] = len(cilios) == 4 and pior < 0.0004
    g["cilios_medidas"] = f"n_esq={len(cilios)} pior_dist={pior:.5f}"

    g["gate_rosto"] = all(v for k, v in g.items() if isinstance(v, bool))
    log("validação do rosto:")
    for k, v in g.items():
        if isinstance(v, bool):
            log(f"  {'OK    ' if v else 'FALHOU'} {k}: {g.get(k + '_medidas', '')}")
    return g


# -----------------------------------------------------------------------------
# 8. Métricas e export
# -----------------------------------------------------------------------------
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
    mat = material("PeleJulia", (0.63, 0.45, 0.35), rough=0.55)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

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

    log("Fase 3 rebuild — cabeça paramétrica + orelhas")
    cabeca = criar_cabeca()
    orelhas = criar_orelhas()
    juntar(corpo, [cabeca] + orelhas + criar_maos())
    normalizar(corpo)

    extras = criar_rosto_e_cabelo(corpo)

    m = metricas(corpo)
    val = validar_rosto(corpo, extras)
    m["fase3_objetos"] = len(extras)
    m["rabo_mechas"] = len([o for o in extras if o.name.startswith("rabo_mecha_")])
    m["tris_fase3_extras"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in extras)
    m["tris_glb_total"] = m["tris"] + m["tris_fase3_extras"]
    m["texturas_procedurais_fase3"] = ["julia_cabelo_alpha.png", "julia_iris_color.png", "julia_iris_normal_radial.png"]
    m["alpha_mode"] = "MASK (alpha cutoff 0.5)"
    m.update({k: v for k, v in val.items()})
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
