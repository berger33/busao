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
    for p in me.polygons:
        p.use_smooth = True
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    return o


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
    me = D.meshes.new(nome)
    verts, faces = [], []
    exp = 0.62  # seção retângulo-arredondado, não cilindro
    for t, rx, ry, yoff in perfis:
        z = cz - comprimento * t
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
    densificar_cabeca(corpo)
    esculpir_rosto(corpo)
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
