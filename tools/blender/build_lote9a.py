# Lote 9A — vegetacao e miudezas do cenario (Blender 4.5 headless).
# Contrato (assets/scene/LEIA-ME.md): frente -Z no Godot = +Y no Blender,
# origem no chao, escala REAL em metros (o jogo instancia sem fit).
# Pecas com cor de cenario usam materiais "Tint*" de albedo BRANCO: o jogo
# (_tint_glb em game_3d.gd) aplica a cor accent da fase via override.
# Nos previews, os Tint* recebem uma cor-amostra so para a foto.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
SCENE = str(K.REPO / "assets" / "scene")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(SCENE, exist_ok=True)

TAU = K.TAU
COR_AMOSTRA = (0.91, 0.77, 0.36)  # amarelo mostarda, so para os previews


def caixa(nome, centro, dims, subd=0):
    cx, cy, cz = centro
    dx, dy, dz = (d * 0.5 for d in dims)
    v = [(cx - dx, cy - dy, cz - dz), (cx + dx, cy - dy, cz - dz),
         (cx + dx, cy + dy, cz - dz), (cx - dx, cy + dy, cz - dz),
         (cx - dx, cy - dy, cz + dz), (cx + dx, cy - dy, cz + dz),
         (cx + dx, cy + dy, cz + dz), (cx - dx, cy + dy, cz + dz)]
    # ordem do lote 7 (normais para fora; a ordem antiga invertia todas as faces)
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = K.novo_obj(nome, K.malha(nome, v, f))
    uv = o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = [(0.02, 0.02), (0.98, 0.02), (0.98, 0.98), (0.02, 0.98)][(li - poly.loop_start) % 4]
    if subd:
        mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = subd
    return o


def coluna_entre(nome, A, B, r_base, r_topo_rel=1.0, seg=10):
    """Pilar com base em A e topo em B (eixo qualquer)."""
    v = Vector(B) - Vector(A)
    L = v.length
    p = K.pilar(nome, r_base, r_topo_rel, seg)
    K.sozinho(p)
    p.scale = (1, 1, L)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    p.rotation_mode = 'QUATERNION'
    p.rotation_quaternion = v.to_track_quat('Z', 'Y')
    p.location = Vector(A)
    K.sozinho(p)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    p.rotation_mode = 'XYZ'
    return p


def pilar_em_pe(nome, r_base, r_topo_rel, altura, x=0.0, y=0.0, z0=0.0, seg=12):
    """Pilar vertical com base em (x, y, z0)."""
    p = K.pilar(nome, r_base, r_topo_rel, seg)
    K.sozinho(p)
    p.scale = (1, 1, altura)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    p.location = (x, y, z0)
    K.sozinho(p)
    bpy.ops.object.transform_apply(location=True)
    return p


def ripa(nome, dims, centro, rot_x=0.0, rot_y=0.0, rot_z=0.0):
    """Caixa girada em torno do proprio centro e depois transladada."""
    o = caixa(nome, (0.0, 0.0, 0.0), dims, subd=0)
    if rot_x or rot_y or rot_z:
        K.sozinho(o)
        o.rotation_euler = (rad(rot_x), rad(rot_y), rad(rot_z))
        bpy.ops.object.transform_apply(rotation=True)
    o.location = Vector(centro)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True)
    return o


# ============================================================================
# MATERIAIS
# ============================================================================
def mats():
    m = {}
    m["casca"] = K.material("SceneCasca", (0.38, 0.25, 0.16), 0.95)
    m["casca_palmeira"] = K.material("SceneCascaPalmeira", (0.50, 0.33, 0.22), 0.9)
    m["folha"] = K.material("SceneFolha", (0.24, 0.52, 0.22), 0.76)
    m["folha_palmeira"] = K.material("SceneFolhaPalmeira", (0.24, 0.67, 0.46), 0.84)
    m["coco"] = K.material("SceneCoco", (0.45, 0.30, 0.16), 0.8)
    m["azul_caixa"] = K.material("SceneAzulCaixa", (0.30, 0.47, 0.63), 0.62)
    m["aco_caixa"] = K.material("SceneAcoCaixa", (0.46, 0.33, 0.24), 0.9, 0.1)
    m["madeira_varal"] = K.material("SceneMadeiraVaral", (0.35, 0.29, 0.26), 0.9)
    m["corda"] = K.material("SceneCorda", (0.65, 0.63, 0.60), 0.95)
    m["roupa_vermelha"] = K.material("SceneRoupaVermelha", (0.90, 0.43, 0.39), 0.8)
    m["roupa_azul"] = K.material("SceneRoupaAzul", (0.36, 0.61, 0.82), 0.8)
    m["roupa_amarela"] = K.material("SceneRoupaAmarela", (0.90, 0.77, 0.31), 0.8)
    m["roupa_verde"] = K.material("SceneRoupaVerde", (0.51, 0.79, 0.62), 0.8)
    m["mastro"] = K.material("SceneMastro", (0.82, 0.81, 0.76), 0.68, 0.2)
    m["tint_tecido"] = K.material("TintFabric", (1.0, 1.0, 1.0), 0.64)
    m["tint_tinta"] = K.material("TintPaint", (1.0, 1.0, 1.0), 0.38)
    m["tint_metal"] = K.material("TintMetal", (1.0, 1.0, 1.0), 0.45, 0.35)
    m["aco_outdoor"] = K.material("SceneAcoOutdoor", (0.22, 0.25, 0.30), 0.5, 0.15)
    m["moldura"] = K.material("SceneMoldura", (0.16, 0.18, 0.22), 0.55, 0.2)
    m["madeira_barraca"] = K.material("SceneMadeiraBarraca", (0.85, 0.55, 0.26), 0.76)
    m["madeira_escura"] = K.material("SceneMadeiraEscura", (0.45, 0.30, 0.20), 0.8)
    m["pele"] = K.material("ScenePele", (0.72, 0.47, 0.35), 0.7)
    m["camisa"] = K.material("SceneCamisa", (0.93, 0.92, 0.88), 0.75)
    m["bone"] = K.material("SceneBone", (0.80, 0.25, 0.22), 0.7)
    m["fruta_laranja"] = K.material("SceneFrutaLaranja", (0.95, 0.55, 0.15), 0.55)
    m["fruta_verde"] = K.material("SceneFrutaVerde", (0.45, 0.70, 0.25), 0.55)
    m["fruta_vermelha"] = K.material("SceneFrutaVermelha", (0.85, 0.20, 0.20), 0.55)
    return m


TINT_KEYS = ("tint_tecido", "tint_tinta", "tint_metal")


def amostra_tint(M, ligada):
    cor = COR_AMOSTRA if ligada else (1.0, 1.0, 1.0)
    for k in TINT_KEYS:
        M[k].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*cor, 1.0)


# ============================================================================
# 1. PALMEIRA (palm): tronco 2,7 m + 6 folhas + flecha + 3 cocos
# ============================================================================
def build_palmeira(M):
    partes = []
    tronco = pilar_em_pe("PalmTronco", 0.15, 0.67, 2.7, seg=12)
    K.pintar(tronco, M["casca_palmeira"]); partes.append((tronco, "Scene"))
    # aneis do tronco (3 toros achatados = nos da palmeira)
    for i, z in enumerate((0.7, 1.4, 2.1)):
        r = 0.15 - (0.15 - 0.10) * (z / 2.7)
        bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.005, minor_radius=0.022,
                                         major_segments=12, minor_segments=6,
                                         location=(0, 0, z))
        anel = bpy.context.active_object
        anel.name = "PalmAnel%d" % i
        K.pintar(anel, M["casca_palmeira"]); partes.append((anel, "Scene"))
    # copa: 6 folhas arqueadas + flecha central
    for i in range(6):
        folha = K.painel_pena("PalmFolha%d" % i, 1.15, 0.22)
        K.sozinho(folha)
        # deita a folha (aponta +Y) com queda de 28 graus...
        folha.rotation_euler = (rad(-20), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
        # ...e distribui em torno do tronco
        K.sozinho(folha)
        folha.rotation_euler = (0, 0, rad(i * 60))
        bpy.ops.object.transform_apply(rotation=True)
        folha.location = (0, 0, 2.72)
        K.sozinho(folha)
        bpy.ops.object.transform_apply(location=True)
        K.pintar(folha, M["folha_palmeira"]); partes.append((folha, "Scene"))
        # nervura central da folha
        ang = rad(i * 60)
        dx, dy = -math.sin(ang), math.cos(ang)
        nerv = coluna_entre("PalmNerv%d" % i, (dx * 0.08, dy * 0.08, 2.70),
                            (dx * 1.00, dy * 1.00, 2.36), 0.018, 0.5, seg=6)
        K.pintar(nerv, M["folha_palmeira"]); partes.append((nerv, "Scene"))
    flecha = K.painel_pena("PalmFlecha", 0.8, 0.10)
    K.sozinho(flecha)
    flecha.rotation_euler = (rad(78), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    K.sozinho(flecha)
    flecha.rotation_euler = (0, 0, rad(30))
    bpy.ops.object.transform_apply(rotation=True)
    flecha.location = (0, 0, 2.72)
    K.sozinho(flecha)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(flecha, M["folha_palmeira"]); partes.append((flecha, "Scene"))
    for i in range(3):
        ang = rad(i * 120 + 30)
        coco = K.elipsoide("PalmCoco%d" % i, (0.13 * math.cos(ang), 0.13 * math.sin(ang), 2.62),
                           (0.09, 0.09, 0.10), nivel=1)
        K.pintar(coco, M["coco"]); partes.append((coco, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Palmeira"
    return [corpo]


# ============================================================================
# 2. ARVORE (tree): tronco urbano 2.5m + galhos ramificados + copas densas
# ============================================================================
def build_arvore(M):
    partes = []
    # Tronco de calcada com 2.5 m de altura livre para pedestres
    tronco = pilar_em_pe("TreeTronco", 0.20, 0.70, 2.5, seg=16)
    K.pintar(tronco, M["casca"]); partes.append((tronco, "Scene"))
    # Galhos principais ramificados
    galhos = [
        ((0, 0, 1.8), (0.55, 0.20, 2.7), 0.08, 0.6),
        ((0, 0, 1.9), (-0.50, -0.25, 2.8), 0.075, 0.6),
        ((0, 0, 2.1), (0.15, 0.55, 3.0), 0.07, 0.6),
        ((0, 0, 2.2), (-0.20, -0.50, 2.9), 0.07, 0.6),
    ]
    for i, (A, B, r, rt) in enumerate(galhos):
        g = coluna_entre("TreeGalho%d" % i, A, B, r, rt, seg=8)
        K.pintar(g, M["casca"]); partes.append((g, "Scene"))
    copas = [
        (0.60, 0.25, 3.00, 1.10, 1.05, 0.85),
        (-0.55, -0.30, 3.10, 1.05, 1.10, 0.82),
        (0.18, 0.60, 3.30, 1.15, 1.10, 0.90),
        (-0.20, -0.55, 3.20, 1.05, 1.02, 0.85),
        (0.00, 0.00, 3.80, 1.25, 1.20, 1.05),
    ]
    for i, (x, y, z, rx, ry, rz) in enumerate(copas):
        copa = K.elipsoide("TreeCopa%d" % i, (x, y, z), (rx, ry, rz), nivel=2)
        K.pintar(copa, M["folha"]); partes.append((copa, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Arvore"
    return [corpo]


# ============================================================================
# 3. CAIXA D'AGUA (water_tank): cavalete + 4 pes + travessas + tampa
# ============================================================================
def build_caixa_dagua(M):
    partes = []
    ALT = 2.9  # centro do bojo, igual a procedural
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            pe = pilar_em_pe("CaixaPe%c%c" % ("D" if sx > 0 else "E", "F" if sy > 0 else "T"),
                             0.08, 1.0, ALT - 0.42, x=sx * 0.35, y=sy * 0.25, seg=8)
            K.pintar(pe, M["aco_caixa"]); partes.append((pe, "Scene"))
    # travessas em X nas laterais (lados X) e barra tras/frente
    for sx in (1.0, -1.0):
        for s in (1.0, -1.0):
            trav = coluna_entre("CaixaTrav%c%d" % ("D" if sx > 0 else "E", s),
                                (sx * 0.35, s * 0.25, 0.35), (sx * 0.35, -s * 0.25, 1.60),
                                0.03, 1.0, seg=6)
            K.pintar(trav, M["aco_caixa"]); partes.append((trav, "Scene"))
    for sy in (1.0, -1.0):
        barra = ripa("CaixaBarra%c" % ("F" if sy > 0 else "T"), (0.78, 0.06, 0.06),
                     (0, sy * 0.25, 1.62))
        K.pintar(barra, M["aco_caixa"]); partes.append((barra, "Scene"))
    bojo = pilar_em_pe("CaixaBojo", 0.55, 1.0, 0.85, z0=ALT - 0.425, seg=20)
    K.pintar(bojo, M["azul_caixa"]); partes.append((bojo, "Scene"))
    tampa = K.cone_part("CaixaTampa", 0.58, 0.06, 0.26, verts_n=20)
    K.sozinho(tampa)
    tampa.location = (0, 0, ALT + 0.425 + 0.13)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(tampa, M["azul_caixa"]); partes.append((tampa, "Scene"))
    respiro = pilar_em_pe("CaixaRespiro", 0.05, 1.0, 0.10, z0=ALT + 0.425 + 0.24, seg=8)
    K.pintar(respiro, M["aco_caixa"]); partes.append((respiro, "Scene"))
    ladrão = coluna_entre("CaixaLadrao", (0.0, -0.50, ALT - 0.30), (0.0, -0.62, ALT - 0.55),
                          0.025, 1.0, seg=6)
    K.pintar(ladrão, M["aco_caixa"]); partes.append((ladrão, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "CaixaDagua"
    return [corpo]


# ============================================================================
# 4. VARAL (clothesline): 2 mastros + corda + 4 roupas
# ============================================================================
def build_varal(M):
    partes = []
    for sx in (1.0, -1.0):
        mastro = pilar_em_pe("VaralMastro%c" % ("D" if sx > 0 else "E"),
                             0.035, 1.0, 2.1, x=sx * 0.9, seg=8)
        K.pintar(mastro, M["madeira_varal"]); partes.append((mastro, "Scene"))
        # mao-francesa no topo do mastro
        mao = ripa("VaralMao%c" % ("D" if sx > 0 else "E"), (0.05, 0.30, 0.05),
                   (sx * 0.9, 0.0, 2.02))
        K.pintar(mao, M["madeira_varal"]); partes.append((mao, "Scene"))
    corda = ripa("VaralCorda", (1.9, 0.025, 0.025), (0, 0, 1.85))
    K.pintar(corda, M["corda"]); partes.append((corda, "Scene"))
    roupas = ["roupa_vermelha", "roupa_azul", "roupa_amarela", "roupa_verde"]
    for i in range(4):
        roupa = ripa("VaralRoupa%d" % i, (0.30, 0.04, 0.38),
                     (-0.63 + i * 0.42, -0.02, 1.62), rot_z=(-3 if i % 2 else 3))
        K.pintar(roupa, M[roupas[i]]); partes.append((roupa, "Scene"))
        for dx in (-0.11, 0.11):
            preg = ripa("VaralPreg%d%c" % (i, "D" if dx > 0 else "E"), (0.025, 0.05, 0.06),
                        (-0.63 + i * 0.42 + dx, -0.02, 1.83))
            K.pintar(preg, M["madeira_escura"]); partes.append((preg, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Varal"
    return [corpo]


# ============================================================================
# 5. BANDEIRA (flag): mastro 2,7 m + pano ondulado (TintFabric)
# ============================================================================
def build_bandeira(M):
    partes = []
    mastro = pilar_em_pe("FlagMastro", 0.025, 1.0, 2.7, seg=8)
    K.pintar(mastro, M["mastro"]); partes.append((mastro, "Scene"))
    bola = K.elipsoide("FlagBola", (0, 0, 2.73), (0.045, 0.045, 0.045), nivel=1)
    K.pintar(bola, M["mastro"]); partes.append((bola, "Scene"))
    # pano 0,72 x 0,38 ondulado ao vento (grade 9x5, onda cresce p/ a ponta)
    NX, NY = 9, 5
    verts, faces = [], []
    for ix in range(NX):
        u = ix / (NX - 1)
        for iy in range(NY):
            v = iy / (NY - 1)
            x = 0.03 + u * 0.72
            z = 2.19 + v * 0.38
            y = 0.055 * u * math.sin(u * math.pi * 1.5)
            verts.append((x, y, z))
    for ix in range(NX - 1):
        for iy in range(NY - 1):
            a = ix * NY + iy
            faces.append((a, a + NY, a + NY + 1, a + 1))
    pano = K.novo_obj("FlagPano", K.malha("FlagPano", verts, faces))
    sol = pano.modifiers.new("Espessura", 'SOLIDIFY')
    sol.thickness = 0.008
    K.pintar(pano, M["tint_tecido"]); partes.append((pano, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Bandeira"
    return [corpo]


# ============================================================================
# 6. OUTDOOR (billboard): poste 3,8 m + painel 2,25x1,15 (TintPaint)
# ============================================================================
def build_outdoor(M):
    partes = []
    poste = pilar_em_pe("OutPoste", 0.04, 1.0, 3.8, seg=10)
    K.pintar(poste, M["aco_outdoor"]); partes.append((poste, "Scene"))
    sapata = caixa("OutSapata", (0, 0, 0.10), (0.34, 0.34, 0.20))
    K.pintar(sapata, M["moldura"]); partes.append((sapata, "Scene"))
    travessa = ripa("OutTravessa", (1.60, 0.07, 0.07), (0, 0, 3.02))
    K.pintar(travessa, M["aco_outdoor"]); partes.append((travessa, "Scene"))
    for sx in (1.0, -1.0):
        escora = coluna_entre("OutEscora%c" % ("D" if sx > 0 else "E"),
                              (0, 0, 2.55), (sx * 0.72, 0, 3.06), 0.028, 1.0, seg=6)
        K.pintar(escora, M["aco_outdoor"]); partes.append((escora, "Scene"))
    # moldura (fundo escuro maior) + painel tintavel na frente E atras
    moldura = caixa("OutMoldura", (0, 0, 3.65), (2.35, 0.06, 1.25))
    K.pintar(moldura, M["moldura"]); partes.append((moldura, "Scene"))
    for sy, tag in ((0.045, "F"), (-0.045, "T")):
        painel = caixa("OutPainel%c" % tag, (0, sy, 3.65), (2.25, 0.03, 1.15))
        K.pintar(painel, M["tint_tinta"]); partes.append((painel, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Outdoor"
    return [corpo]


# ============================================================================
# 7. PORTAO (gate): 1,8 x 1,7 m metalico (TintMetal)
# ============================================================================
def build_portao(M):
    partes = []
    for sx in (1.0, -1.0):
        pilastra = caixa("GatePilastra%c" % ("D" if sx > 0 else "E"),
                         (sx * 0.94, 0, 0.90), (0.10, 0.10, 1.80))
        K.pintar(pilastra, M["tint_metal"]); partes.append((pilastra, "Scene"))
        bola = K.elipsoide("GateBola%c" % ("D" if sx > 0 else "E"),
                           (sx * 0.94, 0, 1.83), (0.055, 0.055, 0.055), nivel=1)
        K.pintar(bola, M["tint_metal"]); partes.append((bola, "Scene"))
    for z in (0.18, 1.58):
        trilho = ripa("GateTrilho%d" % int(z * 100), (1.80, 0.05, 0.07), (0, 0, z))
        K.pintar(trilho, M["tint_metal"]); partes.append((trilho, "Scene"))
    for i in range(7):
        barra = pilar_em_pe("GateBarra%d" % i, 0.018, 1.0, 1.42,
                            x=-0.77 + i * (1.54 / 6), z0=0.16, seg=6)
        K.pintar(barra, M["tint_metal"]); partes.append((barra, "Scene"))
        ponta = K.cone_part("GatePonta%d" % i, 0.026, 0.004, 0.09, verts_n=6)
        K.sozinho(ponta)
        ponta.location = (-0.77 + i * (1.54 / 6), 0, 1.62)
        bpy.ops.object.transform_apply(location=True)
        K.pintar(ponta, M["tint_metal"]); partes.append((ponta, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Portao"
    return [corpo]


# ============================================================================
# 8. BARRACA DE MERCADO (market_stall): balcao + toldo + vendedor + frutas
# ============================================================================
def build_barraca(M):
    partes = []
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            pe = ripa("StallPe%c%c" % ("D" if sx > 0 else "E", "F" if sy > 0 else "T"),
                      (0.07, 0.07, 0.55), (sx * 0.68, sy * 0.42, 0.275))
            K.pintar(pe, M["madeira_escura"]); partes.append((pe, "Scene"))
    corpo_b = caixa("StallCorpo", (0, 0, 0.56), (1.50, 1.00, 0.62))
    K.pintar(corpo_b, M["madeira_barraca"]); partes.append((corpo_b, "Scene"))
    # fasquias na frente (+Y = -Z no jogo) e tampo do balcao
    for i in range(3):
        ripa_f = ripa("StallRip%d" % i, (1.54, 0.03, 0.14), (0, 0.505, 0.38 + i * 0.19))
        K.pintar(ripa_f, M["madeira_escura"]); partes.append((ripa_f, "Scene"))
    tampo = caixa("StallTampo", (0, 0, 1.14), (1.60, 1.10, 0.06))
    K.pintar(tampo, M["madeira_escura"]); partes.append((tampo, "Scene"))
    # toldo em 4 varas + lona tintavel
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            vara = pilar_em_pe("StallVara%c%c" % ("D" if sx > 0 else "E", "F" if sy > 0 else "T"),
                               0.02, 1.0, 0.80, x=sx * 0.78, y=sy * 0.50, z0=1.17, seg=6)
            K.pintar(vara, M["madeira_escura"]); partes.append((vara, "Scene"))
    lona = ripa("StallLona", (1.75, 1.15, 0.06), (0, 0, 2.00), rot_x=-4)
    K.pintar(lona, M["tint_tecido"]); partes.append((lona, "Scene"))
    # vendedor: busto atras do balcao (base enterrada no balcao para assentar)
    torso = caixa("StallTorso", (0, -0.28, 1.32), (0.42, 0.28, 0.50), subd=1)
    K.pintar(torso, M["camisa"]); partes.append((torso, "Scene"))
    cabeca = K.elipsoide("StallCabeca", (0, -0.28, 1.69), (0.14, 0.14, 0.15), nivel=1)
    K.pintar(cabeca, M["pele"]); partes.append((cabeca, "Scene"))
    copa_bone = K.elipsoide("StallBone", (0, -0.28, 1.80), (0.145, 0.145, 0.09), nivel=1)
    K.pintar(copa_bone, M["bone"]); partes.append((copa_bone, "Scene"))
    aba = ripa("StallAba", (0.20, 0.16, 0.025), (0, -0.13, 1.77))
    K.pintar(aba, M["bone"]); partes.append((aba, "Scene"))
    # 2 caixas de fruta no balcao
    for i, (mat_fruta, x) in enumerate((("fruta_laranja", -0.42), ("fruta_verde", 0.42))):
        engradado = caixa("StallEng%d" % i, (x, 0.18, 1.23), (0.44, 0.34, 0.12))
        K.pintar(engradado, M["madeira_escura"]); partes.append((engradado, "Scene"))
        for a in range(3):
            for b in range(2):
                fruta = K.elipsoide("StallFruta%d%c%c" % (i, "ABC"[a], "AB"[b]),
                                    (x - 0.12 + a * 0.12, 0.13 + b * 0.11, 1.33),
                                    (0.05, 0.05, 0.05), nivel=1)
                K.pintar(fruta, M[mat_fruta]); partes.append((fruta, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "BarracaMercado"
    return [corpo]


# ============================================================================
# PREVIEW + EXPORT
# ============================================================================
def render_prop(nodes, nome, distancia, altura_alvo):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    D.lights["Cheia"].energy = 4.0
    D.lights["Sol"].energy = 1.25
    # a Cheia nasce colada na origem: para pecas altas ela vira um holofote
    # no chao — reposiciona proporcional a distancia da camera
    D.objects["Cheia"].location = (distancia * 0.55, -distancia * 0.65, distancia * 0.75)
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (max(distancia * 2.4, 3.0), max(distancia * 2.4, 3.0), 1)
    cam = cena.camera
    cam.data.lens = 50
    K.render_de(cam, (distancia * 0.85, -distancia * 1.05, distancia * 0.55),
                (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote9a_" + nome + ".png"))


def bbox_dim(nodes):
    import mathutils
    bb = mathutils.Vector((1e9, 1e9, 1e9)); bt = mathutils.Vector((-1e9, -1e9, -1e9))
    for o in nodes:
        for v in o.bound_box:
            p = o.matrix_world @ mathutils.Vector(v)
            bb = mathutils.Vector((min(bb.x, p.x), min(bb.y, p.y), min(bb.z, p.z)))
            bt = mathutils.Vector((max(bt.x, p.x), max(bt.y, p.y), max(bt.z, p.z)))
    return bt - bb


if __name__ == "__main__":
    K.reset_scene()
    M = mats()
    jobs = [
        ("palmeira",     build_palmeira,     5.2, 1.70),
        ("arvore",       build_arvore,       4.4, 1.40),
        ("caixa_dagua",  build_caixa_dagua,  5.4, 1.70),
        ("varal",        build_varal,        3.4, 1.00),
        ("bandeira",     build_bandeira,     4.2, 1.40),
        ("outdoor",      build_outdoor,      6.4, 2.10),
        ("portao",       build_portao,       3.2, 0.90),
        ("barraca",      build_barraca,      3.8, 1.10),
    ]
    alvo_nome = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].startswith("-") and not sys.argv[-1].endswith(".py") else None
    if alvo_nome:
        jobs = [j for j in jobs if j[0] == alvo_nome]
    resumo = []
    for nome, fn, dist, h_alvo in jobs:
        nodes = fn(M)
        dim = bbox_dim(nodes)
        resumo.append((nome, tuple(round(v, 2) for v in (dim.x, dim.y, dim.z))))
        print("L9A %-11s %.2fL x %.2fP x %.2fA" % (nome, dim.x, dim.y, dim.z))
        K.export_glb(os.path.join(SCENE, nome + ".glb"), nodes)
        amostra_tint(M, True)
        render_prop(nodes, nome, dist, h_alvo)
        amostra_tint(M, False)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    print("RESUMO_LOTE9A:", resumo)
    print("LOTE9A_OK")
