# Lote 9C - equipamentos do cenario (Blender 4.5 headless).
# Contrato (assets/scene/LEIA-ME.md): frente -Z no Godot = +Y no Blender,
# origem no chao, escala REAL em metros. Todos instanciam sem fit (so position),
# exceto pothole que e filho da entidade de rua.
# Cores da fase via materiais "Tint*" de albedo BRANCO (_tint_glb no jogo).
# Nos previews, os Tint* recebem uma cor-amostra so para a foto.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad
from PIL import Image, ImageDraw, ImageFont

D = bpy.data
SCENE = str(K.REPO / "assets" / "scene")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(SCENE, exist_ok=True)

COR_AMOSTRA = (0.91, 0.77, 0.36)  # mostarda, so para previews
TAU = K.TAU


def caixa(nome, centro, dims, subd=0):
    cx, cy, cz = centro
    dx, dy, dz = (d * 0.5 for d in dims)
    v = [(cx - dx, cy - dy, cz - dz), (cx + dx, cy - dy, cz - dz),
         (cx + dx, cy + dy, cz - dz), (cx - dx, cy + dy, cz - dz),
         (cx - dx, cy - dy, cz + dz), (cx + dx, cy - dy, cz + dz),
         (cx + dx, cy + dy, cz + dz), (cx - dx, cy + dy, cz + dz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = K.novo_obj(nome, K.malha(nome, v, f))
    mesh = o.data
    uv = mesh.uv_layers.new(name="UVMap")
    xs = [vt.co.x for vt in mesh.vertices]
    ys = [vt.co.y for vt in mesh.vertices]
    zs = [vt.co.z for vt in mesh.vertices]
    mnx, mxx = min(xs), max(xs)
    mny, mxy = min(ys), max(ys)
    mnz, mxz = min(zs), max(zs)
    for poly in mesh.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for k, li in enumerate(poly.loop_indices):
            c = mesh.vertices[poly.vertices[k]].co
            if ax == 0:
                u, vv = (c.y - mny) / max(mxy - mny, 1e-6), (c.z - mnz) / max(mxz - mnz, 1e-6)
            elif ax == 1:
                u, vv = (c.x - mnx) / max(mxx - mnx, 1e-6), (c.z - mnz) / max(mxz - mnz, 1e-6)
            else:
                u, vv = (c.x - mnx) / max(mxx - mnx, 1e-6), (c.y - mny) / max(mxy - mny, 1e-6)
            uv.data[li].uv = (0.02 + 0.96 * u, 0.02 + 0.96 * vv)
    if subd:
        mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = subd
    return o


def coluna_entre(nome, A, B, r_base, r_topo_rel=1.0, seg=10):
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
    p = K.pilar(nome, r_base, r_topo_rel, seg)
    K.sozinho(p)
    p.scale = (1, 1, altura)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    p.location = (x, y, z0)
    K.sozinho(p)
    bpy.ops.object.transform_apply(location=True)
    return p


def ripa(nome, dims, centro, rot_x=0.0, rot_y=0.0, rot_z=0.0):
    o = caixa(nome, (0.0, 0.0, 0.0), dims, subd=0)
    if rot_x or rot_y or rot_z:
        K.sozinho(o)
        o.rotation_euler = (rad(rot_x), rad(rot_y), rad(rot_z))
        bpy.ops.object.transform_apply(rotation=True)
    o.location = Vector(centro)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True)
    return o


def frontao(nome, y0, y1, hx, zb, alt, mat):
    L0 = (-hx, y0, zb); R0 = (hx, y0, zb); T0 = (0, y0, zb + alt)
    L1 = (-hx, y1, zb); R1 = (hx, y1, zb); T1 = (0, y1, zb + alt)
    o = K.novo_obj(nome, K.malha(nome, [L0, R0, T0, L1, T1, R1], [(0, 1, 2), (3, 4, 5)]))
    K.pintar(o, mat)
    return o


def telhado_2aguas(prefixo, lag_x, prof_y, zb, alt, beiral, mat):
    hx = lag_x / 2 + beiral
    comp = math.hypot(hx, alt) + 0.12
    ang = math.degrees(math.atan2(alt, hx))
    pecas = []
    for s, tag in ((1.0, "D"), (-1.0, "E")):
        agua = ripa("%sAgua%s" % (prefixo, tag), (comp, prof_y + beiral * 2, 0.07),
                    (s * hx / 2, 0, zb + alt / 2 - 0.02), rot_y=s * ang)
        K.pintar(agua, mat); pecas.append((agua, "Scene"))
    cume = ripa("%sCume" % prefixo, (0.14, prof_y + beiral * 2 + 0.06, 0.10),
                (0, 0, zb + alt + 0.02))
    K.pintar(cume, mat); pecas.append((cume, "Scene"))
    return pecas


def janela(nome, eixo, fixo, u, z, w, h, M, azul=False):
    mold = M["moldura_azul"] if azul else M["moldura"]
    s = 1.0 if fixo > 0 else -1.0
    if eixo == "y":
        f1 = caixa(nome + "Mold", (u, fixo + s * 0.02, z), (w + 0.12, 0.04, h + 0.12))
        f2 = caixa(nome + "Vidro", (u, fixo + s * 0.038, z), (w, 0.04, h))
    else:
        f1 = caixa(nome + "Mold", (fixo + s * 0.02, u, z), (0.04, w + 0.12, h + 0.12))
        f2 = caixa(nome + "Vidro", (fixo + s * 0.038, u, z), (0.04, w, h))
    K.pintar(f1, mold); K.pintar(f2, M["vidro"])
    return [(f1, "Scene"), (f2, "Scene")]


def porta(nome, eixo, fixo, u, h, w, M):
    s = 1.0 if fixo > 0 else -1.0
    if eixo == "y":
        p1 = caixa(nome + "Folha", (u, fixo + s * 0.03, h / 2), (w, 0.06, h))
        p2 = caixa(nome + "Soleira", (u, fixo + s * 0.10, 0.035), (w + 0.16, 0.16, 0.07))
    else:
        p1 = caixa(nome + "Folha", (fixo + s * 0.03, u, h / 2), (0.06, w, h))
        p2 = caixa(nome + "Soleira", (fixo + s * 0.10, u, 0.035), (0.16, w + 0.16, 0.07))
    K.pintar(p1, M["porta"]); K.pintar(p2, M["concreto"])
    return [(p1, "Scene"), (p2, "Scene")]


def pintar_face_vis(o, mat):
    mesh = o.data
    mesh.materials.append(mat)
    idx = len(mesh.materials) - 1
    for p in mesh.polygons:
        if p.normal.y < -0.9:
            p.material_index = idx


# ============================================================================
# MATERIAIS
# ============================================================================
def mats():
    m = {}
    # Tint* albedo branco - jogo pinta via _tint_glb
    m["tint_parede"] = K.material("TintWall", (1.0, 1.0, 1.0), 0.95)
    m["tint_telhado"] = K.material("TintRoof", (1.0, 1.0, 1.0), 0.85)
    m["tint_trim"] = K.material("TintTrim", (1.0, 1.0, 1.0), 0.5, 0.1)
    m["tint_tecido"] = K.material("TintFabric", (1.0, 1.0, 1.0), 0.64)
    m["tint_sign"] = None  # preenchido sob demanda via mat_placa
    # fixos
    m["vidro"] = K.material("SceneVidro9C", (0.16, 0.32, 0.36), 0.25, 0.15)
    m["vidro_guard"] = K.material("SceneVidroGuard", (0.18, 0.36, 0.40), 0.22, 0.12)
    m["porta"] = K.material("ScenePorta9C", (0.32, 0.24, 0.22), 0.62)
    m["porta_igreja"] = K.material("ScenePortaIgreja", (0.38, 0.28, 0.24), 0.6)
    m["moldura"] = K.material("SceneMoldura9C", (0.93, 0.91, 0.85), 0.6)
    m["moldura_azul"] = K.material("SceneMolduraAzul9C", (0.20, 0.38, 0.62), 0.55)
    m["concreto"] = K.material("SceneConcreto9C", (0.62, 0.60, 0.56), 0.9)
    m["concreto_claro"] = K.material("SceneConcretoClaro9C", (0.78, 0.76, 0.72), 0.88)
    m["tijolo"] = K.material("SceneTijolo9C", (0.68, 0.35, 0.26), 0.95)
    m["ferro"] = K.material("SceneFerro9C", (0.25, 0.25, 0.28), 0.6, 0.6)
    m["ferro_escuro"] = K.material("SceneFerroEscuro9C", (0.22, 0.24, 0.26), 0.55, 0.5)
    m["laranja_obra"] = K.material("SceneLaranjaObra", (0.90, 0.47, 0.24), 0.68)
    m["tela_obra"] = K.material("SceneTelaObra", (0.98, 0.84, 0.36), 0.66)
    m["amarelo_cone"] = K.material("SceneAmareloCone", (0.95, 0.78, 0.24), 0.62)
    m["madeira"] = K.material("SceneMadeira9C", (0.62, 0.40, 0.26), 0.78)
    m["madeira_clara"] = K.material("SceneMadeiraClara9C", (0.82, 0.62, 0.38), 0.76)
    m["metal_terminal"] = K.material("SceneMetalTerminal", (0.28, 0.36, 0.48), 0.42, 0.35)
    m["metal_cobertura"] = K.material("SceneMetalCobertura", (0.34, 0.40, 0.46), 0.5, 0.35)
    m["asfalto_escuro"] = K.material("SceneAsfaltoEscuro", (0.10, 0.12, 0.16), 0.96)
    m["asfalto_borda"] = K.material("SceneAsfaltoBorda", (0.33, 0.36, 0.40), 0.92)
    m["terra_pothole"] = K.material("SceneTerraPothole", (0.20, 0.16, 0.14), 0.98)
    m["vidro_terminal"] = K.material("SceneVidroTerminal", (0.45, 0.78, 0.76), 0.18, 0.08)
    m["vidro_terminal2"] = K.material("SceneVidroTerminal2", (0.52, 0.82, 0.80), 0.16, 0.05)
    m["mastro"] = K.material("SceneMastro9C", (0.82, 0.81, 0.76), 0.68, 0.2)
    m["cruz"] = K.material("SceneCruzIgreja", (0.72, 0.68, 0.62), 0.55)
    return m


TINT_KEYS = ("tint_parede", "tint_telhado", "tint_trim", "tint_tecido")


def amostra_tint(M, ligada):
    cor = COR_AMOSTRA if ligada else (1.0, 1.0, 1.0)
    for k in TINT_KEYS:
        if k in M and M[k] is not None:
            inp = M[k].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
            if not inp.is_linked:
                inp.default_value = (*cor, 1.0)


def placa_terminal_img():
    img = Image.new("RGB", (512, 96), (242, 240, 232))
    d = ImageDraw.Draw(img)
    d.rectangle((4, 4, 507, 91), outline=(38, 54, 74), width=6)
    f = ImageFont.load_default(size=52)
    # tentar fonte maior
    try:
        # PIL default não tem tamanho grande, mas load_default com size funciona
        pass
    except:
        pass
    d.text((256, 50), "TERMINAL", font=f, anchor="mm", fill=(38, 54, 74))
    path = os.path.join(K.OUT_DIR, "lote9c_placa.png")
    img.save(path)
    return D.images.load(path)


def mat_placa(img):
    m = K.material("TintSign", (1.0, 1.0, 1.0), 0.4, 0.0)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


# ============================================================================
# 1. IGREJA - nave 2.9x3.6x4.0 + torre 1.1x1.0x5.6 + cone
# ============================================================================
def build_igreja(M):
    partes = []
    # base / calçada
    # corpo nave
    corpo = caixa("IgrejaCorpo", (0, 0, 2.00), (2.9, 3.6, 4.00))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    rodape = caixa("IgrejaRodape", (0, 0, 0.09), (2.98, 3.68, 0.18))
    K.pintar(rodape, M["concreto"]); partes.append((rodape, "Scene"))
    # oitão e telhado 2 águas sobre a nave (zb=4.0, alt=0.85)
    g = frontao("IgrejaOitao", -1.80, 1.80, 1.45, 4.00, 0.85, M["tint_parede"])
    partes.append((g, "Scene"))
    partes += telhado_2aguas("Igreja", 2.9, 3.6, 4.00, 0.85, 0.28, M["tint_telhado"])
    # torre lateral esquerda (-X) - 5.6m alta
    torre = caixa("IgrejaTorre", (-1.02, 0.0, 2.80), (1.10, 1.00, 5.60))
    K.pintar(torre, M["tint_parede"]); partes.append((torre, "Scene"))
    # base da torre um pouco mais larga
    base_torre = caixa("IgrejaBaseTorre", (-1.02, 0.0, 0.12), (1.18, 1.10, 0.24))
    K.pintar(base_torre, M["concreto"]); partes.append((base_torre, "Scene"))
    # cornija / faixa horizontal a 4.0m (platibanda)
    faixa = caixa("IgrejaFaixa", (0, 0, 3.92), (2.96, 3.66, 0.10))
    K.pintar(faixa, M["tint_trim"]); partes.append((faixa, "Scene"))
    faixa_torre = caixa("IgrejaFaixaTorre", (-1.02, 0.0, 4.92), (1.14, 1.06, 0.10))
    K.pintar(faixa_torre, M["tint_trim"]); partes.append((faixa_torre, "Scene"))
    # cone da torre
    cone = K.cone_part("IgrejaCone", 0.62, 0.04, 1.05, verts_n=16)
    K.sozinho(cone)
    cone.location = (-1.02, 0.0, 5.60 + 0.525)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(cone, M["tint_telhado"]); partes.append((cone, "Scene"))
    # bola no topo do cone
    bola = K.elipsoide("IgrejaBola", (-1.02, 0.0, 5.60 + 1.05 + 0.05), (0.055, 0.055, 0.055), nivel=1)
    K.pintar(bola, M["tint_trim"]); partes.append((bola, "Scene"))
    # cruz sobre a torre (2 ripas cruzadas)
    cruz_v = caixa("IgrejaCruzV", (-1.02, 0.0, 7.05), (0.05, 0.05, 0.55))
    K.pintar(cruz_v, M["tint_trim"]); partes.append((cruz_v, "Scene"))
    cruz_h = caixa("IgrejaCruzH", (-1.02, 0.0, 7.05), (0.32, 0.05, 0.05))
    K.pintar(cruz_h, M["tint_trim"]); partes.append((cruz_h, "Scene"))
    # porta principal no front (+Y)
    partes += porta("IgrejaPortaF", "y", 1.80, 0.0, 1.85, 0.72, M)
    # porta lateral direita (para variedade) - pequena
    # janelas front: 2 laterais ao porta + roseta acima da porta
    for ui in (-0.85, 0.85):
        partes += janela("IgrejaJanF%d" % int((ui+1)*10), "y", 1.80, ui, 1.35, 0.45, 0.85, M)
    # roseta central acima da porta (vitral)
    # moldura circular aproximada via caixa + vidro com formato de cruz
    # criamos como caixa quadrada com vitral azulado
    roseta_mold = caixa("IgrejaRosetaMold", (0.0, 1.82, 2.95), (0.64, 0.06, 0.64))
    K.pintar(roseta_mold, M["moldura"]); partes.append((roseta_mold, "Scene"))
    roseta_vidro = caixa("IgrejaRosetaVidro", (0.0, 1.84, 2.95), (0.52, 0.06, 0.52))
    K.pintar(roseta_vidro, M["vidro"]); partes.append((roseta_vidro, "Scene"))
    # cruz interna da roseta (divisória)
    div_v = caixa("IgrejaRosetaDivV", (0.0, 1.845, 2.95), (0.06, 0.065, 0.52))
    K.pintar(div_v, M["moldura"]); partes.append((div_v, "Scene"))
    div_h = caixa("IgrejaRosetaDivH", (0.0, 1.845, 2.95), (0.52, 0.065, 0.06))
    K.pintar(div_h, M["moldura"]); partes.append((div_h, "Scene"))
    # janelas laterais nave (4 ao todo, 2 por lado)
    for sy in (1.80, -1.80):
        eixo = "y"
        for ux in (-0.85, 0.85):
            # laterais estão nas faces Y, então eixo y mesmo mas u = x
            # para as laterais norte/sul ja fizemos; para leste/oeste precisamos eixo x
            pass
    # janelas nas laterais longas (x = +-1.45)
    for sx, tag in ((1.45, "D"), (-1.45, "E")):
        for i, uy in enumerate((-0.95, 0.95)):
            partes += janela("IgrejaLat%s%d" % (tag, i), "x", sx, uy, 1.65, 0.50, 0.85, M)
    # janela da torre (pequena sineira) - 4 faces
    for sx, tag in ((0.55, "D"), (-0.55, "E")):
        # na verdade torre faces x
        j = caixa("IgrejaSineiraX%s" % tag, (-1.02 + sx, 0.0, 5.05), (0.06, 0.32, 0.45))
        K.pintar(j, M["ferro"]); partes.append((j, "Scene"))
    for sy, tag in ((0.50, "F"), (-0.50, "T")):
        j = caixa("IgrejaSineiraY%s" % tag, (-1.02, sy, 5.05), (0.32, 0.06, 0.45))
        K.pintar(j, M["ferro"]); partes.append((j, "Scene"))
    # campana (sino) dentro da torre
    sino = pilar_em_pe("IgrejaSino", 0.18, 1.0, 0.20, x=-1.02, y=0.0, z0=4.95, seg=12)
    K.pintar(sino, M["cruz"]); partes.append((sino, "Scene"))
    # cruz frontão (pequena sobre a porta, no oitão)
    cruz_f = caixa("IgrejaCruzFrenteV", (0.0, 1.82, 4.55), (0.04, 0.04, 0.28))
    K.pintar(cruz_f, M["tint_trim"]); partes.append((cruz_f, "Scene"))
    cruz_fh = caixa("IgrejaCruzFrenteH", (0.0, 1.82, 4.55), (0.20, 0.04, 0.04))
    K.pintar(cruz_fh, M["tint_trim"]); partes.append((cruz_fh, "Scene"))

    corpo = K.join_parts(partes)
    corpo.name = "Igreja"
    return [corpo]


# ============================================================================
# 2. QUIOSQUE TURISTICO - corpo cilindrico 1.55m + cone 0.52
# ============================================================================
def build_quiosque(M):
    partes = []
    # corpo tronco-cone (base 0.72 -> topo 0.84)
    corpo_cil = pilar_em_pe("QuiosqueCorpo", 0.72, 0.84/0.72, 1.55, seg=16)
    K.pintar(corpo_cil, M["tint_parede"]); partes.append((corpo_cil, "Scene"))
    # base concreta circular levemente maior (anel)
    base = pilar_em_pe("QuiosqueBase", 0.78, 1.0, 0.10, seg=16)
    K.pintar(base, M["concreto"]); partes.append((base, "Scene"))
    # cobertura conica
    cone = K.cone_part("QuiosqueCone", 1.05, 0.05, 0.52, verts_n=16)
    K.sozinho(cone)
    cone.location = (0.0, 0.0, 1.55 + 0.26)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(cone, M["tint_trim"]); partes.append((cone, "Scene"))
    # pingente / bola no topo
    bola = K.elipsoide("QuiosqueBola", (0.0, 0.0, 1.55+0.52+0.04), (0.04,0.04,0.04), nivel=1)
    K.pintar(bola, M["tint_trim"]); partes.append((bola, "Scene"))
    # beiral de madeira aparente sob a lona (roda)
    beiral = pilar_em_pe("QuiosqueBeiral", 0.86, 1.0, 0.06, z0=1.52, seg=16)
    K.pintar(beiral, M["madeira_clara"]); partes.append((beiral, "Scene"))
    # balcao / janela de venda no lado front (+Y)
    # frente a +Y, entao balcao em y=0.72
    balcao = caixa("QuiosqueBalcao", (0.0, 0.78, 0.98), (0.72, 0.10, 0.05))
    K.pintar(balcao, M["madeira_clara"]); partes.append((balcao, "Scene"))
    # abertura vitrine vazada - moldura + vidro recolhido
    mold = caixa("QuiosqueMold", (0.0, 0.74, 0.98), (0.68, 0.06, 0.42))
    K.pintar(mold, M["moldura"]); partes.append((mold, "Scene"))
    vidro = caixa("QuiosqueVidro", (0.0, 0.72, 0.98), (0.60, 0.04, 0.34))
    K.pintar(vidro, M["vidro"]); partes.append((vidro, "Scene"))
    # prateleira interna
    prateleira = caixa("QuiosquePrateleira", (0.0, 0.0, 1.08), (0.98, 0.98, 0.04))
    K.pintar(prateleira, M["madeira"]); partes.append((prateleira, "Scene"))
    # tabuleta frontal pequena "INFO"
    tab = caixa("QuiosqueTab", (0.0, 0.82, 0.68), (0.56, 0.04, 0.12))
    K.pintar(tab, M["concreto_claro"]); partes.append((tab, "Scene"))

    corpo = K.join_parts(partes)
    corpo.name = "Quiosque"
    return [corpo]


# ============================================================================
# 3. GUARITA - 1.9x1.8x1.9 + teto plano accent + bandeira lateral
# ============================================================================
def build_guarita(M):
    partes = []
    # corpo principal
    corpo = caixa("GuardCorpo", (0, 0, 0.95), (1.90, 1.80, 1.90))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    # rodape concreto
    rodape = caixa("GuardRodape", (0, 0, 0.09), (1.96, 1.86, 0.18))
    K.pintar(rodape, M["concreto"]); partes.append((rodape, "Scene"))
    # janela frontal larga
    partes += janela("GuardJanF", "y", 0.90, 0.0, 1.20, 1.10, 0.52, M)
    # janelas laterais menores (x faces)
    for sx, tag in ((0.95, "D"), (-0.95, "E")):
        partes += janela("GuardLat%s" % tag, "x", sx, 0.0, 1.18, 0.42, 0.52, M)
    # porta traseira (-Y)
    partes += porta("GuardPortaT", "y", -0.90, 0.0, 1.75, 0.62, M)
    # teto/laje com beiral
    laje = caixa("GuardLaje", (0, 0, 1.98), (2.12, 2.04, 0.10))
    K.pintar(laje, M["tint_trim"]); partes.append((laje, "Scene"))
    capa = caixa("GuardCapa", (0, 0, 2.06), (2.16, 2.08, 0.04))
    K.pintar(capa, M["concreto"]); partes.append((capa, "Scene"))
    # rufo / platibanda fina ao redor
    for ypos, tag in ((1.02, "F"), (-1.02, "T")):
        mur = caixa("GuardMurY%s" % tag, (0, ypos, 2.13), (2.16, 0.06, 0.14))
        K.pintar(mur, M["tint_parede"]); partes.append((mur, "Scene"))
    for xpos, tag in ((1.06, "D"), (-1.06, "E")):
        mur = caixa("GuardMurX%s" % tag, (xpos, 0, 2.13), (0.06, 2.08, 0.14))
        K.pintar(mur, M["tint_parede"]); partes.append((mur, "Scene"))
    # pequeno respirador
    resp = caixa("GuardResp", (0.55, 0.0, 2.14), (0.18, 0.14, 0.10))
    K.pintar(resp, M["concreto_claro"]); partes.append((resp, "Scene"))
    # bandeira lateral (mastro + pano ondulado TintFabric) - integrada
    mastro = pilar_em_pe("GuardMastro", 0.018, 1.0, 2.25, x=0.92, y=0.62, z0=0.0, seg=8)
    K.pintar(mastro, M["mastro"]); partes.append((mastro, "Scene"))
    bola = K.elipsoide("GuardBola", (0.92, 0.62, 2.28), (0.035,0.035,0.035), nivel=1)
    K.pintar(bola, M["mastro"]); partes.append((bola, "Scene"))
    # pano ondulado 0.55 x 0.32  (grid 7x4)
    NX, NY = 7, 4
    verts, faces = [], []
    for ix in range(NX):
        u = ix / (NX - 1)
        for iy in range(NY):
            v = iy / (NY - 1)
            x = 0.95 + u * 0.55
            z = 1.95 + v * 0.32
            y = 0.62 + 0.045 * u * math.sin(u * math.pi * 1.7)
            verts.append((x, y, z))
    for ix in range(NX - 1):
        for iy in range(NY - 1):
            a = ix * NY + iy
            faces.append((a, a + NY, a + NY + 1, a + 1))
    pano = K.novo_obj("GuardPano", K.malha("GuardPano", verts, faces))
    sol = pano.modifiers.new("Espessura", 'SOLIDIFY')
    sol.thickness = 0.007
    K.pintar(pano, M["tint_tecido"]); partes.append((pano, "Scene"))

    corpo = K.join_parts(partes)
    corpo.name = "Guarita"
    return [corpo]


# ============================================================================
# 4. TERMINAL - 3.2x2.8x3.2 + vidro grande + marquise + placa
# ============================================================================
def build_terminal(M):
    partes = []
    corpo = caixa("TermCorpo", (0, 0, 1.60), (3.20, 2.80, 3.20))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    # embasamento concreto
    embas = caixa("TermEmbas", (0, 0, 0.18), (3.26, 2.86, 0.36))
    K.pintar(embas, M["concreto"]); partes.append((embas, "Scene"))
    # vidro front grande (+Y) - faixa continua
    # moldura escura ao redor do vidro
    mold = caixa("TermMold", (0, 1.42, 1.55), (3.00, 0.06, 1.55))
    K.pintar(mold, M["ferro_escuro"]); partes.append((mold, "Scene"))
    # vidro dividido em 2 folhas + porta central
    vidro_esq = caixa("TermVidroE", (-0.78, 1.445, 1.55), (1.35, 0.04, 1.45))
    K.pintar(vidro_esq, M["vidro_terminal"]); partes.append((vidro_esq, "Scene"))
    vidro_dir = caixa("TermVidroD", (0.78, 1.445, 1.55), (1.35, 0.04, 1.45))
    K.pintar(vidro_dir, M["vidro_terminal"]); partes.append((vidro_dir, "Scene"))
    # caixilho vertical central entre vidros
    caix_c = caixa("TermCaixC", (0.0, 1.44, 1.55), (0.08, 0.07, 1.45))
    K.pintar(caix_c, M["ferro_escuro"]); partes.append((caix_c, "Scene"))
    # caixilhos horizontais (travessa)
    caix_h = caixa("TermCaixH", (0.0, 1.44, 1.55), (2.90, 0.07, 0.08))
    K.pintar(caix_h, M["ferro_escuro"]); partes.append((caix_h, "Scene"))
    # porta de vidro central baixa (dupla)
    porta_v = caixa("TermPortaVidro", (0.0, 1.47, 0.95), (0.95, 0.06, 1.65))
    K.pintar(porta_v, M["vidro_terminal2"]); partes.append((porta_v, "Scene"))
    # puxadores
    for sx in (-0.08, 0.08):
        pux = caixa("TermPux%d" % int(sx*100), (sx, 1.49, 0.95), (0.02, 0.04, 0.18))
        K.pintar(pux, M["ferro"]); partes.append((pux, "Scene"))
    # marquise / cobertura sobre entrada
    marq = caixa("TermMarq", (0, 1.55, 3.18), (3.50, 0.85, 0.12))
    K.pintar(marq, M["tint_trim"]); partes.append((marq, "Scene"))
    # suportes da marquise (2 escoras diagonais)
    for sx in (-1.05, 1.05):
        esc = coluna_entre("TermEscora%s" % ("E" if sx < 0 else "D"), (sx, 1.40, 3.12), (sx, 1.85, 2.85), 0.035, 1.0, seg=6)
        K.pintar(esc, M["metal_cobertura"]); partes.append((esc, "Scene"))
    # platibanda / coroamento superior
    capa = caixa("TermCapa", (0, 0, 3.28), (3.32, 2.92, 0.16))
    K.pintar(capa, M["concreto"]); partes.append((capa, "Scene"))
    # placa TERMINAL sobre a marquise (texteira com TintSign)
    placa_img = placa_terminal_img()
    m_placa = mat_placa(placa_img)
    placa = caixa("TermPlaca", (0, 1.62, 3.38), (1.85, 0.08, 0.36))
    K.pintar(placa, M["tint_trim"])
    pintar_face_vis(placa, m_placa)
    partes.append((placa, "Scene"))
    # postes de iluminação laterais no recuo
    for sx in (-1.55, 1.55):
        lum_p = pilar_em_pe("TermLampPost%d" % int(sx*10), 0.028, 1.0, 2.85, x=sx, y=-0.85, seg=8)
        K.pintar(lum_p, M["ferro_escuro"]); partes.append((lum_p, "Scene"))
        lum_c = K.elipsoide("TermLamp%d" % int(sx*10), (sx, -0.85, 2.92), (0.09,0.09,0.06), nivel=1)
        K.pintar(lum_c, M["vidro_terminal2"]); partes.append((lum_c, "Scene"))
    # janelas laterais (x faces) - pequenas
    for sx, tag in ((1.60, "D"), (-1.60, "E")):
        for i, uy in enumerate((-0.55, 0.55)):
            partes += janela("TermLat%s%d" % (tag, i), "x", sx, uy, 1.65, 0.55, 0.85, M)
    # janela fundos (-Y)
    for ux in (-0.95, 0.0, 0.95):
        partes += janela("TermFund%d" % int(ux*10), "y", -1.40, ux, 1.65, 0.55, 0.85, M)

    corpo = K.join_parts(partes)
    corpo.name = "Terminal"
    return [corpo]


# ============================================================================
# 5. OBRA - tapume tijolo 2.8x2.9x1.7 + andaime laranja + tela
# ============================================================================
def build_obra(M):
    partes = []
    # parede de bloco aparente
    muro = caixa("ObraMuro", (0, 0, 0.85), (2.80, 2.90, 1.70))
    K.pintar(muro, M["tijolo"]); partes.append((muro, "Scene"))
    # cintas de concreto horiz.
    for z in (0.35, 1.35):
        cinta = caixa("ObraCinta%d" % int(z*100), (0, 0, z), (2.86, 2.96, 0.12))
        K.pintar(cinta, M["concreto"]); partes.append((cinta, "Scene"))
    # pilaretes verticais a cada 0.9m
    for xi in (-1.20, 0.0, 1.20):
        pil = caixa("ObraPil%d" % int(xi*10), (xi, 0, 0.85), (0.14, 2.96, 1.70))
        K.pintar(pil, M["concreto"]); partes.append((pil, "Scene"))
    # andaime tubular laranja na face front (+Y)
    # 4 montantes verticais
    xs = [-1.15, -0.38, 0.38, 1.15]
    for xi in xs:
        mont = pilar_em_pe("ObraMont%d" % int(xi*10), 0.030, 1.0, 3.10, x=xi, y=1.62, z0=0.0, seg=8)
        K.pintar(mont, M["laranja_obra"]); partes.append((mont, "Scene"))
    # travessas horizontais (3 níveis)
    for zh in (0.85, 1.75, 2.65):
        trav = caixa("ObraTrav%d" % int(zh*100), (0, 1.62, zh), (2.55, 0.05, 0.05))
        K.pintar(trav, M["laranja_obra"]); partes.append((trav, "Scene"))
    # diagonais em X no andaime (2)
    for (x0, x1, zh) in [(-1.15, -0.38, 1.30), (0.38, 1.15, 1.30), (-1.15, 0.38, 2.20), (-0.38, 1.15, 2.20)]:
        diag = coluna_entre("ObraDiag%d%d" % (int(x0*10), int(zh*10)), (x0, 1.62, zh-0.45), (x1, 1.62, zh+0.45), 0.022, 1.0, seg=6)
        K.pintar(diag, M["laranja_obra"]); partes.append((diag, "Scene"))
    # tábuas de andaime (plataforma)
    for zh in (1.75, 2.65):
        tab = caixa("ObraTab%d" % int(zh*100), (0, 1.62, zh+0.07), (2.50, 0.40, 0.04))
        K.pintar(tab, M["madeira"]); partes.append((tab, "Scene"))
    # tela de proteção amarela
    tela = caixa("ObraTela", (0, 1.66, 2.15), (2.90, 0.05, 0.95))
    K.pintar(tela, M["tela_obra"]); partes.append((tela, "Scene"))
    # placa de obra "OBRA" pequena sobre o tapume (opcional)
    # cone de sinalização na frente
    cone = K.cone_part("ObraCone", 0.28, 0.03, 0.65, verts_n=16)
    K.sozinho(cone)
    cone.location = (1.45, 1.25, 0.325)
    bpy.ops.object.transform_apply(location=True)
    # faixas refletivas do cone (2 anéis brancos) - fazer via materiais separados? simplifica: pintar tudo laranja e adicionar dois cilindros brancos
    K.pintar(cone, M["laranja_obra"]); partes.append((cone, "Scene"))
    faixa1 = pilar_em_pe("ObraFaixa1", 0.20, 1.0, 0.06, x=1.45, y=1.25, z0=0.22, seg=12)
    K.pintar(faixa1, M["concreto_claro"]); partes.append((faixa1, "Scene"))
    faixa2 = pilar_em_pe("ObraFaixa2", 0.14, 1.0, 0.05, x=1.45, y=1.25, z0=0.38, seg=12)
    K.pintar(faixa2, M["concreto_claro"]); partes.append((faixa2, "Scene"))
    base_cone = caixa("ObraBaseCone", (1.45, 1.25, 0.04), (0.42, 0.42, 0.08))
    K.pintar(base_cone, M["laranja_obra"]); partes.append((base_cone, "Scene"))
    # entulho: alguns blocos espalhados
    ent1 = caixa("ObraEnt1", (0.85, -1.25, 0.12), (0.45, 0.32, 0.24))
    K.pintar(ent1, M["concreto"]); partes.append((ent1, "Scene"))
    ent2 = caixa("ObraEnt2", (-0.95, -1.15, 0.09), (0.38, 0.28, 0.18))
    K.pintar(ent2, M["concreto"]); partes.append((ent2, "Scene"))

    corpo = K.join_parts(partes)
    corpo.name = "Obra"
    return [corpo]


# ============================================================================
# 6. POTHOLE - buraco irregular na rua (centro na origem, plano em Z)
# ============================================================================
def build_pothole(M):
    partes = []
    # --- disco externo irregular (anel superior) - cria malha manualmente ---
    seg = 18
    esp = 0.038
    raio_medio = 0.84
    variacao = 0.09
    # calcula raios per-vertex para manter consistencia top/bottom
    raios = []
    for k in range(seg):
        # deterministico: senoides com frequencias diferentes
        ang = k / seg * TAU
        r = raio_medio + variacao * math.sin(ang * 2.7 + 0.5) * 0.55 + variacao * math.cos(ang * 1.4) * 0.45
        # adicional pequena variacao de alta freq
        r += 0.025 * math.sin(ang * 7.0)
        raios.append(r)
    # constroi disco externo com espessura
    # verts: [0:seg-1] top ring, [seg:2*seg-1] bottom ring, [2*seg] center top, [2*seg+1] center bottom
    verts = []
    for k in range(seg):
        a = k / seg * TAU
        r = raios[k]
        verts.append((r * math.cos(a), r * math.sin(a), esp))
    for k in range(seg):
        a = k / seg * TAU
        r = raios[k]
        verts.append((r * math.cos(a), r * math.sin(a), 0.0))
    verts.append((0.0, 0.0, esp))
    verts.append((0.0, 0.0, 0.0))
    faces = []
    ct = 2 * seg
    cb = 2 * seg + 1
    for k in range(seg):
        kn = (k + 1) % seg
        # top fan (center top + edge)
        faces.append((ct, k, kn))
        # bottom fan (center bottom, reversed)
        faces.append((cb, seg + kn, seg + k))
        # side quad
        faces.append((k, kn, seg + kn, seg + k))
    outer = K.novo_obj("PotholeOuter", K.malha("PotholeOuter", verts, faces))
    # UV planar por projecao (necessario para textura se houver)
    mesh = outer.data
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = poly.vertices[li - poly.loop_start] if False else mesh.loops[li].vertex_index
            # acessa via loops seria mais correto, mas usando vertices direto simplifica
            # aproximacao: usa coord xy para uv
            co = mesh.vertices[vi].co
            uv.data[li].uv = (co.x * 0.5 + 0.5, co.y * 0.5 + 0.5)
    # precisa corrigir loop->vertex: usar mesh.loops[li].vertex_index
    # refaz corrigido
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            co = mesh.vertices[vi].co
            # normaliza pelo raio max ~0.95 para caber em 0..1
            u = (co.x / 1.0) * 0.5 + 0.5
            v_ = (co.y / 1.0) * 0.5 + 0.5
            uv.data[li].uv = (u, v_)
    K.pintar(outer, M["asfalto_escuro"])
    partes.append((outer, "Scene"))

    # disco interno depressao (mais profundo, liso)
    seg2 = 14
    r_inner_avg = 0.52
    var_inner = 0.045
    esp_top_inner = 0.010
    esp_bottom_inner = -0.065
    verts2 = []
    raios2 = []
    for k in range(seg2):
        a = k / seg2 * TAU
        r = r_inner_avg + var_inner * math.sin(a * 3.3) * 0.6
        raios2.append(r)
        verts2.append((r * math.cos(a), r * math.sin(a), esp_top_inner))
    for k in range(seg2):
        a = k / seg2 * TAU
        r = raios2[k] * 0.86  # estreita levemente para baixo (paredes inclinadas)
        verts2.append((r * math.cos(a), r * math.sin(a), esp_bottom_inner))
    verts2.append((0.0, 0.0, esp_top_inner))
    verts2.append((0.0, 0.0, esp_bottom_inner))
    faces2 = []
    ct2 = 2 * seg2
    cb2 = 2 * seg2 + 1
    for k in range(seg2):
        kn = (k + 1) % seg2
        faces2.append((ct2, k, kn))
        faces2.append((cb2, seg2 + kn, seg2 + k))
        faces2.append((k, kn, seg2 + kn, seg2 + k))
    inner = K.novo_obj("PotholeInner", K.malha("PotholeInner", verts2, faces2))
    uv2 = inner.data.uv_layers.new(name="UVMap")
    for poly in inner.data.polygons:
        for li in poly.loop_indices:
            vi = inner.data.loops[li].vertex_index
            co = inner.data.vertices[vi].co
            uv2.data[li].uv = (co.x * 0.6 + 0.5, co.y * 0.6 + 0.5)
    K.pintar(inner, M["terra_pothole"])
    partes.append((inner, "Scene"))

    # aro de borda quebrado (anel de fragmentos) - 7 pedacinhos levantados ao redor
    import random
    rng = random.Random(42)
    for i in range(7):
        ang = rng.uniform(0, TAU)
        r_dist = 0.84 + rng.uniform(-0.04, 0.08)
        x = math.cos(ang) * r_dist
        y = math.sin(ang) * r_dist
        # pedaco levantado irregular
        w = rng.uniform(0.12, 0.22)
        d = rng.uniform(0.06, 0.11)
        h = rng.uniform(0.025, 0.055)
        frag = caixa("PotholeFrag%d" % i, (x, y, h*0.5+0.015), (w, d, h))
        # inclinacao aleatoria
        K.sozinho(frag)
        frag.rotation_euler = (rad(rng.uniform(-12,12)), rad(rng.uniform(-8,8)), ang + rad(rng.uniform(-15,15)))
        bpy.ops.object.transform_apply(rotation=True)
        frag.location = Vector((x, y, h*0.5+0.018))
        bpy.ops.object.transform_apply(location=True)
        K.pintar(frag, M["asfalto_borda"])
        partes.append((frag, "Scene"))

    corpo = K.join_parts(partes)
    corpo.name = "Pothole"
    return [corpo]


# ============================================================================
# PREVIEW + EXPORT
# ============================================================================
def render_prop(nodes, nome, distancia, altura_alvo):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    D.lights["Cheia"].energy = 4.0
    D.lights["Sol"].energy = 1.25
    D.objects["Cheia"].location = (distancia * 0.55, -distancia * 0.65, distancia * 0.75)
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (max(distancia * 2.4, 3.0), max(distancia * 2.4, 3.0), 1)
    cam = cena.camera
    cam.data.lens = 50
    K.render_de(cam, (distancia * 0.85, -distancia * 1.05, distancia * 0.55),
                (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote9c_" + nome + ".png"))


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
        ("igreja",   lambda: build_igreja(M),   9.5, 3.2),
        ("quiosque", lambda: build_quiosque(M),  4.8, 1.10),
        ("guarita",  lambda: build_guarita(M),  5.0, 1.25),
        ("terminal", lambda: build_terminal(M), 6.8, 1.75),
        ("obra",     lambda: build_obra(M),     6.2, 1.45),
        ("pothole",  lambda: build_pothole(M),  3.2, 0.15),
    ]
    if "--" in sys.argv:
        so = set(sys.argv[sys.argv.index("--") + 1:])
        jobs = [j for j in jobs if j[0] in so] or jobs
    resumo = []
    for nome, fn, dist, h_alvo in jobs:
        nodes = fn()
        dim = bbox_dim(nodes)
        resumo.append((nome, tuple(round(v, 2) for v in (dim.x, dim.y, dim.z))))
        print("L9C %-10s %.2fL x %.2fP x %.2fA" % (nome, dim.x, dim.y, dim.z))
        K.export_glb(os.path.join(SCENE, nome + ".glb"), nodes)
        amostra_tint(M, True)
        render_prop(nodes, nome, dist, h_alvo)
        amostra_tint(M, False)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for blk in list(D.meshes):
            if blk.users == 0:
                D.meshes.remove(blk)
        for blk in list(D.lights):
            if blk.users == 0:
                D.lights.remove(blk)
        for blk in list(D.worlds):
            if blk.users == 0:
                D.worlds.remove(blk)
        for blk in list(D.cameras):
            if blk.users == 0:
                D.cameras.remove(blk)
    print("RESUMO_LOTE9C:", resumo)
    print("LOTE9C_OK")
