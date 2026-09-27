#!/usr/bin/env python3
"""Herói 10/10 — corpo base + rosto/cabelo/olhos da heroína Júlia.

Plano: docs/PLANO_HEROI_10_10.md (Fases 1 e 3).
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
# 4d. Fase 3 — rosto final: olhos, pálpebras, sobrancelhas/cílios e cabelo
# -----------------------------------------------------------------------------
def _mat_principled(nome, cor, rough=0.5, transmission=0.0, alpha=1.0):
    """Material PBR simples usado nas peças pequenas do rosto.

    Mantém o nome estável para a auditoria do GLB e para leitura humana no
    Blender.  A córnea usa transmissão/IOR barata; cabelo continua em alpha
    scissor (ver material_cabelo_alpha()).
    """
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*cor, alpha)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Alpha"].default_value = alpha
        if transmission and "Transmission Weight" in b.inputs:
            b.inputs["Transmission Weight"].default_value = transmission
            b.inputs["IOR"].default_value = 1.38
        if "Alpha" in b.inputs and alpha < 1.0:
            if hasattr(m, "blend_method"):
                m.blend_method = "BLEND"
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "BLENDED"
    m.diffuse_color = (*cor, alpha)
    m.use_backface_culling = False
    return m


def _card(nome, pontos, mat, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    """Quad frente-e-verso. Cards espaçados em profundidade para evitar shimmer."""
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


def _strip_xz(nome, pontos, largura, mat, uv_repeat=1.0):
    """Fita orgânica no plano XZ (normal voltada para a câmera/frente -Y).

    Usada em pálpebras, sobrancelhas e lábios. Diferente dos antigos quads
    retangulares, segue uma curva com largura pequena, então não corta o olho
    como uma barra preta no close.
    """
    pts = [Vector(p) for p in pontos]
    verts, faces = [], []
    npts = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - p
        elif i == npts - 1:
            t = p - pts[i - 1]
        else:
            t = pts[i + 1] - pts[i - 1]
        perp = Vector((-t.z, 0.0, t.x))
        if perp.length < 1e-6:
            perp = Vector((0.0, 0.0, 1.0))
        perp.normalize()
        verts.append(tuple(p + perp * (largura * 0.5)))
        verts.append(tuple(p - perp * (largura * 0.5)))
    for i in range(npts - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for f in me.polygons:
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            step = vi // 2
            side = vi % 2
            uv.data[li].uv = (step / max(1, npts - 1) * uv_repeat, float(side))
        f.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def _taper_card(nome, top, bottom, largura_top, largura_bottom, mat, eixo_largura=(1, 0, 0)):
    """Card de cabelo afunilado entre topo e ponta."""
    top = Vector(top); bottom = Vector(bottom)
    w = Vector(eixo_largura)
    if w.length < 1e-6:
        w = Vector((1, 0, 0))
    w.normalize()
    pts = [
        tuple(top - w * largura_top * 0.5),
        tuple(top + w * largura_top * 0.5),
        tuple(bottom + w * largura_bottom * 0.5),
        tuple(bottom - w * largura_bottom * 0.5),
    ]
    return _card(nome, pts, mat)


def _save_pack_image(img, caminho: Path, *, srgb=True):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.filepath_raw = str(caminho)
    img.file_format = "PNG"
    img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    img.save()
    img.pack()
    return img


def material_cabelo_alpha():
    """Máscara binária embutida; glTF exporta MASK, nunca BLEND/alpha sorting."""
    img = D.images.new("julia_cabelo_alpha", width=192, height=384, alpha=True)
    px = []
    for y in range(384):
        v = y / 383.0
        for x in range(192):
            u = x / 191.0
            # Taper: largo na raiz, fino nas pontas. Alpha sempre 0/1 para
            # alpha-scissor estável em mobile e sem shimmer por sorting.
            largura = 0.045 + 0.28 * (1.0 - v) ** 0.70
            centro = 0.5 + 0.020 * math.sin(v * 8.0)
            dentro = abs(u - centro) < largura
            fio = (math.sin(u * 86.0 + v * 37.0) > -0.84) or (math.sin(u * 39.0 - v * 19.0) > 0.52)
            a = 1.0 if dentro and fio else 0.0
            # Castanho escuro com fios quentes, já no mesmo mapa da máscara.
            brilho = 0.55 + 0.45 * math.sin(u * 29.0 + v * 9.0) ** 2
            r = 0.052 + 0.050 * brilho
            g = 0.022 + 0.022 * brilho
            b = 0.010 + 0.012 * brilho
            px.extend((r, g, b, a))
    img.pixels.foreach_set(px)
    _save_pack_image(img, REPO / "assets" / "textures" / "heroi" / "julia_cabelo_alpha.png")

    m = D.materials.get("CabeloJulia_alpha_scissor") or D.materials.new("CabeloJulia_alpha_scissor")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    # O exporter glTF só mantém alphaMode=MASK de forma confiável quando o
    # alpha passa por comparação explícita; alpha direto vira BLEND e reabre
    # o problema de ordenação/shimmer nos cards em mobile.
    clip = nt.nodes.new("ShaderNodeMath")
    clip.operation = "GREATER_THAN"
    clip.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs["Alpha"], clip.inputs[0])
    nt.links.new(clip.outputs[0], b.inputs["Alpha"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Roughness"].default_value = 0.72
    if hasattr(m, "blend_method"):
        m.blend_method = "CLIP"
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    m.alpha_threshold = 0.5
    m.use_transparency_overlap = False
    m.use_backface_culling = False
    m.diffuse_color = (0.07, 0.028, 0.014, 1.0)
    return m


def material_iris_radial():
    """Íris verde-castanha com mapa normal radial real (exportável no glTF)."""
    tex_dir = REPO / "assets" / "textures" / "heroi"
    color = D.images.new("julia_iris_color", width=128, height=128, alpha=True)
    normal = D.images.new("julia_iris_normal", width=128, height=128, alpha=False)
    cp, npix = [], []
    for y in range(128):
        yy = (y + 0.5) / 128.0 * 2.0 - 1.0
        for x in range(128):
            xx = (x + 0.5) / 128.0 * 2.0 - 1.0
            r = math.sqrt(xx * xx + yy * yy)
            ang = math.atan2(yy, xx)
            dentro = r <= 1.0
            anel = 0.5 + 0.5 * math.sin(42.0 * r + 10.0 * math.sin(ang * 5.0))
            raios = 0.5 + 0.5 * math.sin(22.0 * ang + 18.0 * r)
            ring_dark = 1.0 - 0.60 * max(0.0, min(1.0, (r - 0.78) / 0.18))
            pupil = 1.0 if r < 0.28 else 0.0
            if dentro:
                base_r = 0.030 + 0.020 * anel
                base_g = 0.110 + 0.085 * raios
                base_b = 0.065 + 0.035 * anel
                base_r *= ring_dark; base_g *= ring_dark; base_b *= ring_dark
                if pupil:
                    base_r *= 0.08; base_g *= 0.08; base_b *= 0.08
                cp.extend((base_r, base_g, base_b, 1.0))
                # Normal tangencial radial sutil, em tangent space.
                amp = 0.18 * (1.0 - min(1.0, r)) * (0.35 + 0.65 * anel)
                nx = math.cos(ang) * amp
                ny = math.sin(ang) * amp
                nz = max(0.0, math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny)))
                npix.extend((0.5 + nx * 0.5, 0.5 + ny * 0.5, nz, 1.0))
            else:
                cp.extend((0.0, 0.0, 0.0, 0.0))
                npix.extend((0.5, 0.5, 1.0, 1.0))
    color.pixels.foreach_set(cp)
    normal.pixels.foreach_set(npix)
    _save_pack_image(color, tex_dir / "julia_iris_color.png", srgb=True)
    _save_pack_image(normal, tex_dir / "julia_iris_normal.png", srgb=False)

    m = D.materials.get("Olho_Iris_NormalRadial") or D.materials.new("Olho_Iris_NormalRadial")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex_c = nt.nodes.new("ShaderNodeTexImage")
    tex_c.image = color
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = normal
    tex_n.image.colorspace_settings.name = "Non-Color"
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nrm.inputs["Strength"].default_value = 0.38
    nt.links.new(tex_n.outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.34
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    m.use_backface_culling = False
    return m


def _olho(nome, loc, escala, mat, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(8, seg // 2), location=loc)
    o = bpy.context.object
    o.name = nome
    o.scale = escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.append(mat)
    return o


def _cilios(nome, s, mat):
    """Leque curto de cílios superiores; geometria opaca, sem alpha sorting."""
    pts_base = []
    for t in (0.12, 0.32, 0.54, 0.76, 0.92):
        x = s * (0.016 + 0.040 * t)
        z = 1.594 + 0.0035 * math.sin(math.pi * t)
        pts_base.append((x, -0.1165, z))
    verts, faces = [], []
    for i, p in enumerate(pts_base):
        t = i / max(1, len(pts_base) - 1)
        p = Vector(p)
        tip = p + Vector((s * (0.0012 + 0.0018 * t), -0.0010, 0.0018 + 0.0012 * t))
        base_w = 0.00075 * (1.0 - 0.35 * t)
        verts.extend([tuple(p + Vector((base_w, 0, 0))), tuple(p - Vector((base_w, 0, 0))), tuple(tip)])
        j = i * 3
        faces.append((j, j + 1, j + 2))
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def criar_olhos_e_cards():
    pecas = []
    pele_det = _mat_principled("PeleJulia_Detalhe", (0.48, 0.255, 0.175), 0.56)
    esclera = _mat_principled("Olho_Esclera", (0.86, 0.88, 0.84), 0.30)
    iris = material_iris_radial()
    pupila = _mat_principled("Olho_Pupila", (0.004, 0.003, 0.002), 0.18)
    cornea = _mat_principled("Olho_Cornea_RefractionBarata", (0.92, 0.98, 1.0), 0.025, 0.72, alpha=0.18)
    escuro = _mat_principled("Sobrancelha_Cilios", (0.035, 0.014, 0.006), 0.74)
    labios = _mat_principled("LabiosJulia", (0.34, 0.135, 0.115), 0.58)
    boca = _mat_principled("SulcoBoca_Narinas", (0.050, 0.018, 0.014), 0.82)

    for lado, s in (("l", 1.0), ("r", -1.0)):
        # O olho foi trazido ~3 cm para frente contra a versão anterior; agora
        # a córnea fica na frente da face e não escondida atrás da malha da bochecha.
        cx, cy, cz = s * 0.032, -0.106, 1.590
        pecas.append(_olho(f"esclera_{lado}", (cx, cy, cz), (0.0148, 0.0060, 0.0068), esclera, 24))
        pecas.append(_olho(f"iris_{lado}", (cx, -0.1130, cz), (0.0048, 0.00055, 0.0048), iris, 20))
        pecas.append(_olho(f"pupila_{lado}", (cx, -0.11355, cz), (0.00205, 0.00034, 0.00205), pupila, 16))
        pecas.append(_olho(f"cornea_{lado}", (cx, -0.11405, cz), (0.0054, 0.00080, 0.0054), cornea, 20))

        # Pálpebras em arcos finos (não quads retangulares).
        pecas.append(_strip_xz(f"palpebra_sup_{lado}", [
            (s * 0.016, -0.1155, 1.592), (s * 0.026, -0.1160, 1.598),
            (s * 0.040, -0.1160, 1.598), (s * 0.052, -0.1155, 1.593),
        ], 0.0030, pele_det))
        pecas.append(_strip_xz(f"palpebra_inf_{lado}", [
            (s * 0.017, -0.1150, 1.586), (s * 0.032, -0.1154, 1.582),
            (s * 0.047, -0.1154, 1.584), (s * 0.053, -0.1150, 1.588),
        ], 0.0022, pele_det))
        pecas.append(_strip_xz(f"sobrancelha_{lado}", [
            (s * 0.013, -0.118, 1.610), (s * 0.030, -0.119, 1.618),
            (s * 0.050, -0.119, 1.616), (s * 0.063, -0.118, 1.611),
        ], 0.0036, escuro))
        pecas.append(_cilios(f"cilios_{lado}", s, escuro))

    # Lábios e fenda: dão leitura de boca a 2 m sem depender só do relevo do bake.
    pecas.append(_strip_xz("labio_superior", [
        (-0.030, -0.109, 1.528), (-0.014, -0.111, 1.533), (0.0, -0.112, 1.531),
        (0.014, -0.111, 1.533), (0.030, -0.109, 1.528),
    ], 0.0062, labios))
    pecas.append(_strip_xz("labio_inferior", [
        (-0.027, -0.108, 1.519), (-0.012, -0.110, 1.514), (0.0, -0.111, 1.513),
        (0.012, -0.110, 1.514), (0.027, -0.108, 1.519),
    ], 0.0068, labios))
    pecas.append(_strip_xz("sulco_boca", [
        (-0.028, -0.113, 1.524), (-0.010, -0.114, 1.523), (0.0, -0.1145, 1.523),
        (0.010, -0.114, 1.523), (0.028, -0.113, 1.524),
    ], 0.0018, boca))

    # Narinas discretas (micro elipses escuras) em vez de só sulcos do normal map.
    for lado, s in (("l", 1.0), ("r", -1.0)):
        pecas.append(_olho(f"narina_{lado}", (s * 0.0095, -0.115, 1.548), (0.0021, 0.00032, 0.00115), boca, 12))

    cabelo = material_cabelo_alpha()
    # Franja curta, acima dos olhos; mantém leitura facial no close.
    franjas = [
        ("franja_1", (-0.066, -0.112, 1.700), (-0.058, -0.118, 1.650), 0.014, 0.004),
        ("franja_2", (-0.041, -0.116, 1.708), (-0.034, -0.121, 1.638), 0.016, 0.004),
        ("franja_3", (-0.014, -0.118, 1.711), (-0.010, -0.123, 1.648), 0.014, 0.003),
        ("franja_4", (0.020, -0.116, 1.706), (0.030, -0.121, 1.642), 0.016, 0.004),
        ("franja_5", (0.052, -0.112, 1.697), (0.061, -0.117, 1.655), 0.014, 0.004),
    ]
    for nome, top, bottom, wt, wb in franjas:
        pecas.append(_taper_card(nome, top, bottom, wt, wb, cabelo, eixo_largura=(1, 0, 0)))

    # Calota em cards longos sobre topo/laterais; sem esfera sólida de cabelo.
    for i, x in enumerate((-0.070, -0.047, -0.024, 0.000, 0.024, 0.047, 0.070), start=1):
        pecas.append(_card(f"calota_top_{i}", [
            (x - 0.014, -0.040, 1.710), (x + 0.014, -0.040, 1.710),
            (x + 0.016, 0.060, 1.620), (x - 0.016, 0.060, 1.620),
        ], cabelo))
    for lado, s in (("l", 1.0), ("r", -1.0)):
        pecas.append(_taper_card(f"mecha_lateral_{lado}_1", (s * 0.078, -0.070, 1.680),
                                 (s * 0.090, -0.034, 1.550), 0.026, 0.010, cabelo, eixo_largura=(0, 0, 1)))
        pecas.append(_taper_card(f"mecha_lateral_{lado}_2", (s * 0.088, -0.020, 1.650),
                                 (s * 0.098, 0.010, 1.520), 0.024, 0.010, cabelo, eixo_largura=(0, 0, 1)))

    # Rabo de cavalo: exatamente 5 mechas, com afastamento de 4 mm em Y para não
    # haver coplanaridade/shimmer quando a personagem corre a 60 FPS.
    for i in range(5):
        off = (i - 2) * 0.014
        pecas.append(_taper_card(f"rabo_mecha_{i+1}",
                                 (off, 0.083 + i * 0.004, 1.625),
                                 (off * 0.55, 0.145 + i * 0.009, 1.430 - 0.012 * (i % 2)),
                                 0.042, 0.016, cabelo, eixo_largura=(1, 0, 0)))

    # Elástico discreto do rabo — geometria opaca, custo mínimo.
    elastico = _mat_principled("ElasticoRabo", (0.015, 0.010, 0.009), 0.66)
    pecas.append(_strip_xz("elastico_rabo", [
        (-0.034, 0.079, 1.626), (-0.012, 0.078, 1.620), (0.012, 0.078, 1.620), (0.034, 0.079, 1.626),
    ], 0.006, elastico))

    log("Fase 3: rosto final com olhos separados, íris normal radial, pálpebras/arcos, cílios/sobrancelhas e cabelo alpha-scissor (rabo=5 mechas)")
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
    m["fase3_tris"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in extras)
    m["tris_total_glb"] = m["tris"] + m["fase3_tris"]
    m["rabo_mechas"] = len([o for o in extras if o.name.startswith("rabo_mecha_")])
    m["alpha_mode"] = "MASK (alpha cutoff 0.5)"
    glb, blend = exportar(corpo)
    m["glb_kb"] = round(glb.stat().st_size / 1024, 1)
    # O teto de triângulos vale para o GLB inteiro; as arestas não-manifold são
    # auditadas no corpo, porque os cards de cabelo/cílios são planos por design.
    m["gate_tris"] = TRIS_MIN <= m["tris_total_glb"] <= TRIS_MAX
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
