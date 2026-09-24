# Lote 6 — mobiliario urbano (Blender 4.5 headless).
# Contrato (assets/props/LEIA-ME.md): frente -Z no Godot = +Y no Blender,
# origem no chao, escala REAL em metros (o jogo instancia sem fit).
# Nada aqui e procedural no sentido de "primitiva solta": cada peca e um
# modelo completo exportado como GLB, com materiais PBR proprios.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
PROPS = str(K.REPO / "assets" / "props")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(PROPS, exist_ok=True)

TAU = K.TAU


def caixa(nome, centro, dims, subd=0):
    cx, cy, cz = centro
    dx, dy, dz = (d * 0.5 for d in dims)
    v = [(cx - dx, cy - dy, cz - dz), (cx + dx, cy - dy, cz - dz),
         (cx + dx, cy + dy, cz - dz), (cx - dx, cy + dy, cz - dz),
         (cx - dx, cy - dy, cz + dz), (cx + dx, cy - dy, cz + dz),
         (cx + dx, cy + dy, cz + dz), (cx - dx, cy + dy, cz + dz)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 6, 2)]
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


def ripa(nome, dims, centro, rot_x=0.0, rot_y=0.0):
    """Caixa centrada na origem, rotacionada em torno do proprio centro e
    depois transladada (evita orbitar em torno da origem do mundo)."""
    o = caixa(nome, (0.0, 0.0, 0.0), dims, subd=0)
    if rot_x or rot_y:
        K.sozinho(o)
        o.rotation_euler = (rad(rot_x), rad(rot_y), 0.0)
        bpy.ops.object.transform_apply(rotation=True)
    o.location = Vector(centro)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True)
    return o


def emissivo(mat, cor=(1.0, 1.0, 1.0), forca=2.0):
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*cor, 1.0)
    b.inputs["Emission Strength"].default_value = forca


# ============================================================================
# MATERIAIS
# ============================================================================
def mats():
    m = {}
    m["laranja_borracha"] = K.material("PropLaranjaBorracha", (0.85, 0.33, 0.12), 0.62)
    m["refletivo"] = K.material("PropRefletivo", (0.96, 0.93, 0.85), 0.28)
    emissivo(m["refletivo"], (1.0, 0.95, 0.85), 0.35)
    m["vermelho_hidrante"] = K.material("PropVermelhoHidrante", (0.72, 0.18, 0.16), 0.5)
    m["latao"] = K.material("PropLatao", (0.93, 0.63, 0.27), 0.35, 0.8)
    m["aco_escuro"] = K.material("PropAcoEscuro", (0.24, 0.27, 0.32), 0.4, 0.7)
    m["aco_grafite"] = K.material("PropAcoGrafite", (0.31, 0.34, 0.38), 0.45, 0.55)
    m["madeira"] = K.material("PropMadeira", (0.58, 0.38, 0.24), 0.72)
    m["madeira_clara"] = K.material("PropMadeiraClara", (0.83, 0.62, 0.33), 0.66)
    m["laranja_orelhao"] = K.material("PropLaranjaOrelhao", (0.85, 0.30, 0.10), 0.3)
    m["escuro_fone"] = K.material("PropEscuroFone", (0.13, 0.15, 0.18), 0.5)
    m["verde_lixeira"] = K.material("PropVerdeLixeira", (0.13, 0.45, 0.28), 0.5)
    m["vidro_azul"] = K.material("PropVidroAzul", (0.56, 0.70, 0.77), 0.12)
    m["aluminio"] = K.material("PropAluminio", (0.80, 0.82, 0.84), 0.32, 0.4)
    m["amarelo_faixa"] = K.material("PropAmareloFaixa", (0.93, 0.78, 0.34), 0.5)
    m["azul_placa"] = K.material("PropAzulPlaca", (0.16, 0.32, 0.60), 0.45)
    m["laranja_assento"] = K.material("PropLaranjaAssento", (0.88, 0.45, 0.18), 0.45, 0.35)
    m["vermelho_toldo"] = K.material("PropVermelhoToldo", (0.87, 0.30, 0.33), 0.6)
    m["branco_toldo"] = K.material("PropBrancoToldo", (0.93, 0.91, 0.86), 0.6)
    m["lente_poste"] = K.material("PropLentePoste", (1.0, 0.86, 0.62), 0.3)
    emissivo(m["lente_poste"], (1.0, 0.80, 0.52), 3.0)
    m["borracha_pneu"] = K.material("PropBorrachaPneu", (0.10, 0.11, 0.13), 0.8)
    m["cromo"] = K.material("PropCromo", (0.72, 0.74, 0.76), 0.22, 0.85)
    m["tecla"] = K.material("PropTecla", (0.20, 0.30, 0.34), 0.4)
    emissivo(m["tecla"], (0.35, 0.75, 0.80), 0.5)
    return m


# ============================================================================
# 1. CONE DE SINALIZACAO
# ============================================================================
def build_cone(M):
    partes = []
    base = caixa("ConeBase", (0, 0, 0.025), (0.55, 0.55, 0.05), subd=0)
    K.pintar(base, M["laranja_borracha"]); partes.append((base, "Prop"))
    ALT = 0.88
    r0, r1 = 0.19, 0.19 * 0.045
    corpo = K.pilar("ConeCorpo", r0, r1 / r0, seg=24)
    K.sozinho(corpo)
    corpo.scale = (1, 1, ALT)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    corpo.location = (0, 0, 0.045)
    K.sozinho(corpo)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(corpo, M["laranja_borracha"]); partes.append((corpo, "Prop"))

    def raio_em(z):  # perfil do cone
        return r0 + (r1 - r0) * (z / ALT)

    for zc in (0.30, 0.58):
        h = 0.085
        rb, rt = raio_em(zc - 0.045) + 0.013, raio_em(zc - 0.045 + h) + 0.013
        faixa = K.pilar("ConeFaixa", rb, rt / rb, seg=24)
        K.sozinho(faixa)
        faixa.scale = (1, 1, h)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        faixa.location = (0, 0, zc)
        K.sozinho(faixa)
        bpy.ops.object.transform_apply(location=True)
        K.pintar(faixa, M["refletivo"]); partes.append((faixa, "Prop"))
    topo = K.elipsoide("ConeTopo", (0, 0, 0.045 + ALT), (0.014, 0.014, 0.02), nivel=1)
    K.pintar(topo, M["laranja_borracha"]); partes.append((topo, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Cone"
    return [corpo_final]


# ============================================================================
# 2. HIDRANTE
# ============================================================================
def build_hidrante(M):
    partes = []

    def p(nome, r, rel, h, z, mat, seg=12):
        o = K.pilar(nome, r, rel, seg=seg)
        K.sozinho(o)
        o.scale = (1, 1, h)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        o.location = (0, 0, z)
        K.sozinho(o)
        bpy.ops.object.transform_apply(location=True)
        K.pintar(o, mat); partes.append((o, "Prop"))
        return o

    p("HidFlange", 0.21, 1.0, 0.07, 0.0, M["aco_escuro"])
    base = K.elipsoide("HidBase", (0, 0, 0.10), (0.185, 0.185, 0.075), nivel=2)
    K.pintar(base, M["vermelho_hidrante"]); partes.append((base, "Prop"))
    p("HidCorpo", 0.175, 0.88, 0.52, 0.12, M["vermelho_hidrante"])
    p("HidPescoco", 0.115, 0.9, 0.14, 0.62, M["vermelho_hidrante"])
    domo = K.elipsoide("HidDomo", (0, 0, 0.79), (0.125, 0.125, 0.085), nivel=2)
    K.pintar(domo, M["vermelho_hidrante"]); partes.append((domo, "Prop"))
    p("HidTampa", 0.055, 0.8, 0.07, 0.86, M["latao"])
    # saidas laterais (bocais) + tampas de latao
    for sx in (1.0, -1.0):
        cano = coluna_entre("HidBocal", (sx * 0.15, 0, 0.40), (sx * 0.33, 0, 0.40), 0.075)
        K.pintar(cano, M["vermelho_hidrante"]); partes.append((cano, "Prop"))
        tampa = coluna_entre("HidTampaBocal", (sx * 0.33, 0, 0.40), (sx * 0.372, 0, 0.40), 0.098)
        K.pintar(tampa, M["latao"]); partes.append((tampa, "Prop"))
    # volante frontal (registro)
    haste = coluna_entre("HidHaste", (0, 0.165, 0.30), (0, 0.24, 0.30), 0.042)
    K.pintar(haste, M["latao"]); partes.append((haste, "Prop"))
    volante = coluna_entre("HidVolante", (0, 0.238, 0.30), (0, 0.262, 0.30), 0.062)
    K.pintar(volante, M["latao"]); partes.append((volante, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Hidrante"
    return [corpo_final]


# ============================================================================
# 3. ORELHAO (telefone publico)
# ============================================================================
def build_orelhao(M):
    import bmesh
    partes = []
    pe = K.pilar("OrelhaoPe", 0.16, 1.0, seg=12)
    K.sozinho(pe)
    pe.scale = (1, 1, 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    K.pintar(pe, M["aco_escuro"]); partes.append((pe, "Prop"))
    coluna = K.pilar("OrelhaoColuna", 0.055, 1.0, seg=12)
    K.sozinho(coluna)
    coluna.scale = (1, 1, 1.46)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    coluna.location = (0, 0, 0.04)
    K.sozinho(coluna)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(coluna, M["aco_grafite"]); partes.append((coluna, "Prop"))

    # Casca: esfera com a regiao frontal-inferior recortada (abertura real),
    # assim o aparelho fica visivel dentro do "ovo" aberto.
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=22, v_segments=16, radius=1.0)
    corta = [f for f in bm.faces
             if f.calc_center_median().y < -0.18 and f.calc_center_median().z < 0.35]
    bmesh.ops.delete(bm, geom=corta, context='FACES')
    me = D.meshes.new("OrelhaoCasca")
    bm.to_mesh(me); bm.free()
    casca = K.novo_obj("OrelhaoCasca", me)
    casca.scale = (0.44, 0.38, 0.54)
    K.sozinho(casca)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    casca.rotation_euler.x = rad(-10)
    K.sozinho(casca)
    bpy.ops.object.transform_apply(rotation=True)
    casca.location = (0, 0.06, 1.88)
    K.sozinho(casca)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(casca, M["laranja_orelhao"]); partes.append((casca, "Prop"))

    # aparelho telefonico dentro da abertura
    aparelho = ripa("OrelhaoAparelho", (0.28, 0.14, 0.42), (0, -0.02, 1.56))
    K.pintar(aparelho, M["escuro_fone"]); partes.append((aparelho, "Prop"))
    teclado = ripa("OrelhaoTeclado", (0.22, 0.02, 0.26), (0, -0.10, 1.60), rot_x=-30)
    K.pintar(teclado, M["tecla"]); partes.append((teclado, "Prop"))
    # fone (monofone) preso na lateral interna da abertura
    fone = coluna_entre("OrelhaoFone", (-0.13, -0.06, 1.72), (-0.13, -0.10, 1.50), 0.028)
    K.pintar(fone, M["escuro_fone"]); partes.append((fone, "Prop"))
    for zz, yy in ((1.73, -0.055), (1.49, -0.095)):
        orelha = K.elipsoide("OrelhaoFonePonta", (-0.13, yy, zz), (0.045, 0.045, 0.038), nivel=1)
        K.pintar(orelha, M["escuro_fone"]); partes.append((orelha, "Prop"))
    # placa de moedas / cartao ao lado do teclado
    placa = ripa("OrelhaoPlaca", (0.10, 0.02, 0.15), (0.16, -0.09, 1.56), rot_x=-30)
    K.pintar(placa, M["latao"]); partes.append((placa, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Orelhao"
    return [corpo_final]


# ============================================================================
# 4. BANCO DE PRACA (comprimento no eixo X; assento abre para -Y)
# ============================================================================
def build_banco(M):
    partes = []
    for sx in (1.0, -1.0):
        pe = coluna_entre("BancoPe", (sx * 0.68, -0.17, 0.02), (sx * 0.68, -0.17, 0.47), 0.030)
        K.pintar(pe, M["aco_escuro"]); partes.append((pe, "Prop"))
        traseiro = coluna_entre("BancoMontante", (sx * 0.68, 0.15, 0.02), (sx * 0.68, 0.22, 1.02), 0.030)
        K.pintar(traseiro, M["aco_escuro"]); partes.append((traseiro, "Prop"))
        suporte = coluna_entre("BancoSuporte", (sx * 0.68, -0.22, 0.44), (sx * 0.68, 0.18, 0.44), 0.026)
        K.pintar(suporte, M["aco_escuro"]); partes.append((suporte, "Prop"))
        travessa = coluna_entre("BancoTravessa", (sx * 0.68, -0.17, 0.10), (sx * 0.68, 0.15, 0.10), 0.022)
        K.pintar(travessa, M["aco_escuro"]); partes.append((travessa, "Prop"))
    # tres ripas de assento + duas de encosto (inclinadas)
    for i, y in enumerate((-0.14, 0.005, 0.15)):
        ripa_a = ripa("BancoRipaAssento%d" % i, (1.72, 0.13, 0.035), (0, y, 0.465))
        K.pintar(ripa_a, M["madeira"]); partes.append((ripa_a, "Prop"))
    for i, (y, z) in enumerate(((0.235, 0.68), (0.27, 0.90))):
        ripa_e = ripa("BancoRipaEncosto%d" % i, (1.72, 0.15, 0.032), (0, y, z), rot_x=-13)
        K.pintar(ripa_e, M["madeira"]); partes.append((ripa_e, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Banco"
    return [corpo_final]


# ============================================================================
# 5. LIXEIRA DE RUA (tambor suspenso em poste)
# ============================================================================
def build_lixeira(M):
    partes = []
    pe = caixa("LixeiraPe", (0, 0, 0.03), (0.30, 0.30, 0.06), subd=0)
    K.pintar(pe, M["aco_escuro"]); partes.append((pe, "Prop"))
    poste = caixa("LixeiraPoste", (0, 0.16, 0.53), (0.07, 0.07, 1.0), subd=0)
    K.pintar(poste, M["aco_escuro"]); partes.append((poste, "Prop"))
    braco = caixa("LixeiraBraco", (0, 0.06, 1.01), (0.06, 0.26, 0.06), subd=0)
    K.pintar(braco, M["aco_escuro"]); partes.append((braco, "Prop"))
    tambor = K.pilar("LixeiraTambor", 0.19, 0.94, seg=14)
    K.sozinho(tambor)
    tambor.scale = (1, 1, 0.54)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tambor.location = (0, -0.08, 0.46)
    K.sozinho(tambor)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(tambor, M["verde_lixeira"]); partes.append((tambor, "Prop"))
    aro = K.pilar("LixeiraAro", 0.20, 1.0, seg=14)
    K.sozinho(aro)
    aro.scale = (1, 1, 0.045)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    aro.location = (0, -0.08, 0.965)
    K.sozinho(aro)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(aro, M["aco_escuro"]); partes.append((aro, "Prop"))
    boca = K.pilar("LixeiraBoca", 0.165, 1.0, seg=14)
    K.sozinho(boca)
    boca.scale = (1, 1, 0.012)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    boca.location = (0, -0.08, 1.005)
    K.sozinho(boca)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(boca, M["escuro_fone"]); partes.append((boca, "Prop"))
    # simbolo de reciclagem: placa simples em relevo na frente (-Y) do tambor
    sim = ripa("LixeiraSimbolo", (0.14, 0.012, 0.14), (0, -0.278, 0.74), rot_x=0)
    K.pintar(sim, M["branco_toldo"]); partes.append((sim, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Lixeira"
    return [corpo_final]


# ============================================================================
# 6. POSTE DE ILUMINACAO (braco para +X, como o builder do jogo)
# ============================================================================
def build_poste(M):
    partes = []
    base = K.pilar("PosteBase", 0.095, 0.78, seg=12)
    K.sozinho(base)
    base.scale = (1, 1, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    K.pintar(base, M["aco_grafite"]); partes.append((base, "Prop"))
    fuste = K.pilar("PosteFuste", 0.055, 0.60, seg=12)
    K.sozinho(fuste)
    fuste.scale = (1, 1, 3.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fuste.location = (0, 0, 0.10)
    K.sozinho(fuste)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(fuste, M["aco_grafite"]); partes.append((fuste, "Prop"))
    anel = K.pilar("PosteAnel", 0.062, 1.0, seg=12)
    K.sozinho(anel)
    anel.scale = (1, 1, 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    anel.location = (0, 0, 2.90)
    K.sozinho(anel)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(anel, M["aco_escuro"]); partes.append((anel, "Prop"))
    braco1 = coluna_entre("PosteBraco1", (0, 0, 3.34), (0.34, 0, 3.56), 0.034)
    K.pintar(braco1, M["aco_grafite"]); partes.append((braco1, "Prop"))
    braco2 = coluna_entre("PosteBraco2", (0.34, 0, 3.56), (0.78, 0, 3.60), 0.028)
    K.pintar(braco2, M["aco_grafite"]); partes.append((braco2, "Prop"))
    luminaria = caixa("PosteLuminaria", (0.90, 0, 3.60), (0.22, 0.56, 0.10), subd=0)
    K.pintar(luminaria, M["aco_grafite"]); partes.append((luminaria, "Prop"))
    lente = caixa("PosteLente", (0.90, 0, 3.545), (0.16, 0.44, 0.02))
    K.pintar(lente, M["lente_poste"]); partes.append((lente, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "Poste"
    return [corpo_final]


# ============================================================================
# 7. PONTO DE ONIBUS (abrigo; abertura para -Y; eixo longo em X)
# ============================================================================
def build_ponto(M):
    partes = []
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            col = coluna_entre("PontoColuna", (sx * 1.15, sy * 0.45, 0), (sx * 1.15, sy * 0.45, 2.32), 0.042)
            K.pintar(col, M["aco_grafite"]); partes.append((col, "Prop"))
    teto = caixa("PontoTeto", (0, 0, 2.36), (2.70, 1.20, 0.07), subd=0)
    K.pintar(teto, M["aluminio"]); partes.append((teto, "Prop"))
    testa = caixa("PontoTesta", (0, -0.58, 2.29), (2.74, 0.10, 0.20), subd=0)
    K.pintar(testa, M["amarelo_faixa"]); partes.append((testa, "Prop"))
    vidro_fundo = caixa("PontoVidroFundo", (0, 0.43, 1.42), (2.28, 0.03, 1.42))
    K.pintar(vidro_fundo, M["vidro_azul"]); partes.append((vidro_fundo, "Prop"))
    for sx in (1.0, -1.0):
        vidro_lado = caixa("PontoVidroLado", (sx * 1.11, 0.06, 1.48), (0.03, 0.74, 1.30))
        K.pintar(vidro_lado, M["vidro_azul"]); partes.append((vidro_lado, "Prop"))
    # banco interno laranja (estilo SPTrans)
    for sx in (0.75, -0.75):
        pe_b = coluna_entre("PontoBancoPe", (sx, 0.30, 0), (sx, 0.30, 0.42), 0.028)
        K.pintar(pe_b, M["aco_escuro"]); partes.append((pe_b, "Prop"))
    assento = caixa("PontoAssento", (0, 0.28, 0.45), (1.80, 0.32, 0.05), subd=0)
    K.pintar(assento, M["laranja_assento"]); partes.append((assento, "Prop"))
    # placa de sinalizacao no poste frontal esquerdo
    mastro = coluna_entre("PontoMastro", (-1.15, -0.45, 2.32), (-1.15, -0.45, 2.85), 0.025)
    K.pintar(mastro, M["aco_grafite"]); partes.append((mastro, "Prop"))
    placa = caixa("PontoPlaca", (-1.15, -0.45, 2.95), (0.42, 0.04, 0.52), subd=0)
    K.pintar(placa, M["azul_placa"]); partes.append((placa, "Prop"))
    faixa_placa = caixa("PontoPlacaFaixa", (-1.15, -0.465, 2.80), (0.42, 0.02, 0.09))
    K.pintar(faixa_placa, M["branco_toldo"]); partes.append((faixa_placa, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "PontoDeOnibus"
    return [corpo_final]


# ============================================================================
# 8. CARRINHO DE CAMELO (abertura para -Y)
# ============================================================================
def build_carrinho(M):
    partes = []
    corpo = caixa("CameloCorpo", (0, 0.05, 0.62), (1.40, 0.85, 0.85), subd=0)
    K.pintar(corpo, M["madeira"]); partes.append((corpo, "Prop"))
    tampo = caixa("CameloTampo", (0, 0.05, 1.08), (1.56, 0.96, 0.06), subd=0)
    K.pintar(tampo, M["madeira_clara"]); partes.append((tampo, "Prop"))
    # porta de vidro frontal (vitrine)
    vitrine = caixa("CameloVitrine", (0, -0.39, 0.80), (0.90, 0.03, 0.40))
    K.pintar(vitrine, M["vidro_azul"]); partes.append((vitrine, "Prop"))
    # rodas atras (eixo no X)
    for sx in (1.0, -1.0):
        pneu = coluna_entre("CameloPneu", (sx * 0.47, 0.34, 0.28), (sx * 0.58, 0.34, 0.28), 0.175)
        K.pintar(pneu, M["borracha_pneu"]); partes.append((pneu, "Prop"))
        cubo = coluna_entre("CameloCubo", (sx * 0.465, 0.34, 0.28), (sx * 0.585, 0.34, 0.28), 0.052)
        K.pintar(cubo, M["latao"]); partes.append((cubo, "Prop"))
    # pes dianteiros
    for sx in (1.0, -1.0):
        pe = coluna_entre("CameloPe", (sx * 0.55, -0.30, 0.0), (sx * 0.55, -0.30, 0.24), 0.026)
        K.pintar(pe, M["aco_escuro"]); partes.append((pe, "Prop"))
    # varas do toldo + toldo listrado
    for sx in (1.0, -1.0):
        vara = coluna_entre("CameloVara", (sx * 0.62, -0.32, 1.10), (sx * 0.62, -0.32, 2.02), 0.020)
        K.pintar(vara, M["cromo"]); partes.append((vara, "Prop"))
    toldo = ripa("CameloToldo", (1.74, 1.10, 0.045), (0, -0.14, 2.06), rot_x=-7)
    K.pintar(toldo, M["vermelho_toldo"]); partes.append((toldo, "Prop"))
    for i in range(3):
        lista = ripa("CameloLista%d" % i, (0.26, 1.12, 0.05), (-0.56 + 0.56 * i, -0.145, 2.058), rot_x=-7)
        K.pintar(lista, M["branco_toldo"]); partes.append((lista, "Prop"))
    # pega traseira
    pega = coluna_entre("CameloPega", (-0.50, 0.50, 0.98), (0.50, 0.50, 0.98), 0.018)
    K.pintar(pega, M["cromo"]); partes.append((pega, "Prop"))
    corpo_final = K.join_parts(partes)
    corpo_final.name = "CarrinhoCamelo"
    return [corpo_final]


# ============================================================================
# PREVIEW + EXPORT
# ============================================================================
def render_prop(nodes, nome, distancia, altura_alvo):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    D.lights["Cheia"].energy = 4.0
    D.lights["Sol"].energy = 1.25
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (max(distancia * 2.4, 3.0), max(distancia * 2.4, 3.0), 1)
    cam = cena.camera
    cam.data.lens = 50
    K.render_de(cam, (distancia * 0.85, -distancia * 1.05, distancia * 0.55),
                (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote6_" + nome + ".png"))


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
        ("cone",     build_cone,     1.7, 0.45),
        ("hidrante", build_hidrante, 2.0, 0.45),
        ("orelhao",  build_orelhao,  3.4, 1.15),
        ("banco",    build_banco,    3.0, 0.50),
        ("lixeira",  build_lixeira,  2.2, 0.55),
        ("poste",    build_poste,    5.2, 1.90),
        ("ponto",    build_ponto,    5.4, 1.30),
        ("carrinho", build_carrinho, 3.6, 1.10),
    ]
    resumo = []
    for nome, fn, dist, h_alvo in jobs:
        nodes = fn(M)
        dim = bbox_dim(nodes)
        resumo.append((nome, tuple(round(v, 2) for v in (dim.x, dim.y, dim.z))))
        print("L6 %-9s %.2fL x %.2fP x %.2fA" % (nome, dim.x, dim.y, dim.z))
        K.export_glb(os.path.join(PROPS, nome + ".glb"), nodes)
        render_prop(nodes, nome, dist, h_alvo)
        # cena totalmente limpa para o proximo asset (piso/luzes/camera vao junto;
        # o setup_preview recria tudo na iteracao seguinte)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    print("RESUMO_LOTE6:", resumo)
    print("LOTE6_OK")
