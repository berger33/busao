# Lote 9B — moradias e comercio do cenario (Blender 4.5 headless).
# Contrato (assets/scene/LEIA-ME.md): frente -Z no Godot = +Y no Blender,
# origem no chao, escala REAL em metros. Casas/loja instanciam sem fit;
# predios escalam X/Y por instancia (2 tamanhos: predio2/predio3).
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
    mesh = o.data
    uv = mesh.uv_layers.new(name="UVMap")
    # UV por projecao no eixo dominante, normalizada pelo bbox (estavel;
    # nao depende da ordem dos loops como o canto-fixo do lote 9A).
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


def frontao(nome, y0, y1, hx, zb, alt, mat):
    """Triangulos do oitão nas faces y0 (normal -Y) e y1 (normal +Y)."""
    L0 = (-hx, y0, zb); R0 = (hx, y0, zb); T0 = (0, y0, zb + alt)
    L1 = (-hx, y1, zb); R1 = (hx, y1, zb); T1 = (0, y1, zb + alt)
    o = K.novo_obj(nome, K.malha(nome, [L0, R0, T0, L1, T1, R1],
                                 [(0, 1, 2), (3, 4, 5)]))
    K.pintar(o, mat)
    return o


def telhado_2aguas(prefixo, lag_x, prof_y, zb, alt, beiral, mat):
    """2 aguas com cumeeira ao longo de Y (oitões em +-Y)."""
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
    """Moldura clara saliente + vidro (sanduiche de 2 caixas)."""
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
    """Folha escura + soleira de concreto."""
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
    """Aplica `mat` so na face -Y (Godot +Z = lado que o jogador ve)."""
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
    # Tint* — albedo branco, o jogo pinta via _tint_glb (amostra so no preview)
    m["tint_parede"] = K.material("TintWall", (1.0, 1.0, 1.0), 0.95)
    m["tint_telhado"] = K.material("TintRoof", (1.0, 1.0, 1.0), 0.85)
    m["tint_trim"] = K.material("TintTrim", (1.0, 1.0, 1.0), 0.5, 0.1)
    m["tint_toldo"] = K.material("TintAwning", (1.0, 1.0, 1.0), 0.62)
    # fixos
    m["vidro"] = K.material("SceneVidro", (0.16, 0.32, 0.36), 0.25, 0.15)
    m["porta"] = K.material("ScenePorta", (0.30, 0.24, 0.26), 0.6)
    m["moldura"] = K.material("SceneMolduraCasa", (0.93, 0.91, 0.85), 0.6)
    m["moldura_azul"] = K.material("SceneMolduraAzul", (0.20, 0.38, 0.62), 0.55)
    m["tijolo"] = K.material("SceneTijolo", (0.62, 0.32, 0.24), 0.95)
    m["laje"] = K.material("SceneLaje", (0.66, 0.64, 0.60), 0.9)
    m["concreto"] = K.material("SceneConcreto9B", (0.62, 0.60, 0.56), 0.9)
    m["ferro"] = K.material("SceneFerro9B", (0.25, 0.25, 0.28), 0.6, 0.6)
    m["ar"] = K.material("SceneArCond", (0.85, 0.84, 0.82), 0.6, 0.1)
    m["caixa_azul"] = K.material("SceneCaixaAzul9B", (0.30, 0.47, 0.63), 0.62)
    m["toldo_branco"] = K.material("SceneToldoBranco", (0.94, 0.92, 0.86), 0.65)
    return m


TINT_KEYS = ("tint_parede", "tint_telhado", "tint_trim", "tint_toldo")


def amostra_tint(M, ligada):
    cor = COR_AMOSTRA if ligada else (1.0, 1.0, 1.0)
    for k in TINT_KEYS:
        inp = M[k].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        if not inp.is_linked:
            inp.default_value = (*cor, 1.0)


def placa_mercearia():
    """Textura PIL da placa da loja: fundo branco x tinta = cor da fase."""
    img = Image.new("RGB", (512, 96), (242, 240, 232))
    d = ImageDraw.Draw(img)
    d.rectangle((4, 4, 507, 91), outline=(38, 54, 74), width=6)
    f = ImageFont.load_default(size=58)
    d.text((256, 50), "MERCEARIA", font=f, anchor="mm", fill=(38, 54, 74))
    path = os.path.join(K.OUT_DIR, "lote9b_placa.png")
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
# 1-2. CASA (residencial) / COLONIAL — 2.6 x 3.1 x 2.65 + telhado 2 aguas
# ============================================================================
def build_casa(M, colonial=False):
    tag = "Col" if colonial else "Casa"
    partes = []
    corpo = caixa(tag + "Corpo", (0, 0, 1.325), (2.6, 3.1, 2.65))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    rodape = caixa(tag + "Rodape", (0, 0, 0.09), (2.66, 3.16, 0.18))
    K.pintar(rodape, M["concreto"]); partes.append((rodape, "Scene"))
    g = frontao(tag + "Oitao", -1.55, 1.55, 1.3, 2.65, 0.85, M["tint_parede"])
    partes.append((g, "Scene"))
    partes += telhado_2aguas(tag, 2.6, 3.1, 2.65, 0.85, 0.28, M["tint_telhado"])
    for sy, t in ((1.0, "F"), (-1.0, "T")):
        partes += porta(tag + "Porta" + t, "y", sy * 1.55, 0.0, 1.9, 0.66, M)
        for i, u in enumerate((-0.75, 0.75)):
            partes += janela(tag + "Jan%s%d" % (t, i), "y", sy * 1.55, u, 1.55,
                             0.62, 0.8, M, azul=colonial)
    for sx, t in ((1.0, "D"), (-1.0, "E")):
        for i, u in enumerate((-0.75, 0.75)):
            partes += janela(tag + "Lat%s%d" % (t, i), "x", sx * 1.3, u, 1.55,
                             0.62, 0.8, M, azul=colonial)
    if colonial:
        # faixa accent + cunhais claros nos cantos
        faixa = caixa(tag + "Faixa", (0, 0, 2.10), (2.66, 3.16, 0.09))
        K.pintar(faixa, M["tint_trim"]); partes.append((faixa, "Scene"))
        for sx in (1.0, -1.0):
            for sy in (1.0, -1.0):
                cunha = caixa(tag + "Cun%c%c" % ("D" if sx > 0 else "E",
                                                "F" if sy > 0 else "T"),
                              (sx * 1.3, sy * 1.55, 1.325), (0.14, 0.14, 2.65))
                K.pintar(cunha, M["moldura"]); partes.append((cunha, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Colonial" if colonial else "Casa"
    return [corpo]


# ============================================================================
# 3. CASA FAVELA — tijolo aparente + laje + vergalhoes + toldo
# ============================================================================
def build_casa_favela(M):
    partes = []
    corpo = caixa("FavCorpo", (0, 0, 1.325), (2.6, 3.1, 2.65))
    K.pintar(corpo, M["tijolo"]); partes.append((corpo, "Scene"))
    laje = caixa("FavLaje", (0, 0, 2.72), (2.9, 3.4, 0.14))
    K.pintar(laje, M["tint_telhado"]); partes.append((laje, "Scene"))
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            v = pilar_em_pe("FavVerg%c%c" % ("D" if sx > 0 else "E",
                                            "F" if sy > 0 else "T"),
                            0.012, 1.0, 0.5, x=sx * 1.1, y=sy * 1.3, z0=2.79, seg=6)
            K.pintar(v, M["ferro"]); partes.append((v, "Scene"))
    for sy, t in ((1.0, "F"), (-1.0, "T")):
        partes += porta("FavPorta" + t, "y", sy * 1.55, -0.55, 1.9, 0.62, M)
        partes += janela("FavJan" + t, "y", sy * 1.55, 0.65, 1.55, 0.6, 0.75, M)
        toldo = ripa("FavToldo" + t, (1.2, 0.55, 0.05), (0, sy * 1.77, 1.97),
                     rot_x=-sy * 29)
        K.pintar(toldo, M["tint_toldo"]); partes.append((toldo, "Scene"))
    for sx, t in ((1.0, "D"), (-1.0, "E")):
        partes += janela("FavLat" + t, "x", sx * 1.3, 0.0, 1.55, 0.55, 0.7, M)
    corpo = K.join_parts(partes)
    corpo.name = "CasaFavela"
    return [corpo]


# ============================================================================
# 4-5. PREDIO — andares x 2.6 m + platibanda ( authored 3.0 x 3.8 )
# ============================================================================
def build_predio(M, andares):
    tag = "Pred%d" % andares
    H = andares * 2.6
    partes = []
    corpo = caixa(tag + "Corpo", (0, 0, H / 2), (3.0, 3.8, H))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    base = caixa(tag + "Base", (0, 0, 0.15), (3.06, 3.86, 0.30))
    K.pintar(base, M["concreto"]); partes.append((base, "Scene"))
    for i in range(andares):
        z = i * 2.6 + 1.5
        us = (-0.95, 0.95) if i == 0 else (-0.95, 0.0, 0.95)
        for sy, t in ((1.0, "F"), (-1.0, "T")):
            for j, u in enumerate(us):
                partes += janela("%sJ%d%s%d" % (tag, i, t, j), "y", sy * 1.9, u, z,
                                 0.7, 1.0, M)
        for sx, t in ((1.0, "D"), (-1.0, "E")):
            for j, u in enumerate((-0.95, 0.95)):
                partes += janela("%sL%d%s%d" % (tag, i, t, j), "x", sx * 1.5, u, z,
                                 0.7, 1.0, M)
    # terreo: portas + marquises nos dois lados Y
    for sy, t in ((1.0, "F"), (-1.0, "T")):
        partes += porta(tag + "Port" + t, "y", sy * 1.9, 0.0, 2.1, 0.9, M)
        marq = caixa(tag + "Marq" + t, (0, sy * 2.12, 2.32), (1.6, 0.5, 0.08))
        K.pintar(marq, M["concreto"]); partes.append((marq, "Scene"))
    # coroamento accent + platibanda + ar-condicionado + caixa d'agua
    coroa = caixa(tag + "Coroa", (0, 0, H - 0.55), (3.08, 3.88, 0.22))
    K.pintar(coroa, M["tint_trim"]); partes.append((coroa, "Scene"))
    capa = caixa(tag + "Capa", (0, 0, H - 0.08), (3.14, 3.94, 0.16))
    K.pintar(capa, M["concreto"]); partes.append((capa, "Scene"))
    for sy in (1.0, -1.0):
        mureta = caixa(tag + "Mur%c" % ("F" if sy > 0 else "T"),
                       (0, sy * 1.88, H + 0.17), (3.14, 0.10, 0.50))
        K.pintar(mureta, M["tint_parede"]); partes.append((mureta, "Scene"))
        ar = caixa(tag + "Ar%c" % ("F" if sy > 0 else "T"),
                   (-0.95, sy * 2.0, 2.6 + 1.5), (0.6, 0.22, 0.4))
        K.pintar(ar, M["ar"]); partes.append((ar, "Scene"))
    for sx in (1.0, -1.0):
        mureta = caixa(tag + "Mur%c" % ("D" if sx > 0 else "E"),
                       (sx * 1.52, 0, H + 0.17), (0.10, 3.94, 0.50))
        K.pintar(mureta, M["tint_parede"]); partes.append((mureta, "Scene"))
    bojo = pilar_em_pe(tag + "Bojo", 0.4, 1.0, 0.7, x=0.7, y=0.8, z0=H, seg=14)
    K.pintar(bojo, M["caixa_azul"]); partes.append((bojo, "Scene"))
    tampa = K.cone_part(tag + "Tampa", 0.44, 0.05, 0.22, verts_n=14)
    K.sozinho(tampa)
    tampa.location = (0.7, 0.8, H + 0.7 + 0.11)
    bpy.ops.object.transform_apply(location=True)
    K.pintar(tampa, M["caixa_azul"]); partes.append((tampa, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Predio%d" % andares
    return [corpo]


# ============================================================================
# 6. LOJA — vitrine + toldo + placa MERCEARIA + porta lateral
# ============================================================================
def build_loja(M):
    partes = []
    corpo = caixa("LojaCorpo", (0, 0, 1.225), (2.5, 3.0, 2.45))
    K.pintar(corpo, M["tint_parede"]); partes.append((corpo, "Scene"))
    rodape = caixa("LojaRodape", (0, 0, 0.09), (2.56, 3.06, 0.18))
    K.pintar(rodape, M["concreto"]); partes.append((rodape, "Scene"))
    capa = caixa("LojaCapa", (0, 0, 2.50), (2.62, 3.12, 0.10))
    K.pintar(capa, M["concreto"]); partes.append((capa, "Scene"))
    for sy, t in ((1.0, "F"), (-1.0, "T")):
        partes += janela("LojaVitr" + t, "y", sy * 1.5, -0.38, 0.95, 1.45, 0.85, M)
        partes += porta("LojaPorta" + t, "y", sy * 1.5, 0.88, 1.9, 0.55, M)
        toldo = ripa("LojaToldo" + t, (2.6, 0.7, 0.05), (0, sy * 1.8, 1.9),
                     rot_x=-sy * 26.6)
        K.pintar(toldo, M["tint_toldo"]); partes.append((toldo, "Scene"))
        babado = caixa("LojaBabado" + t, (0, sy * 2.08, 1.72), (2.6, 0.04, 0.14))
        K.pintar(babado, M["toldo_branco"]); partes.append((babado, "Scene"))
    for sx, t in ((1.0, "D"), (-1.0, "E")):
        partes += janela("LojaLat" + t, "x", sx * 1.25, 0.0, 1.5, 0.7, 0.7, M)
    # placa de cobertura com letreiro (textura so na face visivel -Y)
    for px in (-0.6, 0.6):
        poste = caixa("LojaPoste%c" % ("D" if px > 0 else "E"),
                      (px, 0, 2.72), (0.06, 0.06, 0.35))
        K.pintar(poste, M["ferro"]); partes.append((poste, "Scene"))
    placa = caixa("LojaPlaca", (0, 0, 2.85), (1.65, 0.08, 0.32))
    K.pintar(placa, M["tint_trim"])
    pintar_face_vis(placa, mat_placa(placa_mercearia()))
    partes.append((placa, "Scene"))
    corpo = K.join_parts(partes)
    corpo.name = "Loja"
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
    # no chao — reposiciona proporcional a distancia da camera (licao 9A)
    D.objects["Cheia"].location = (distancia * 0.55, -distancia * 0.65, distancia * 0.75)
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (max(distancia * 2.4, 3.0), max(distancia * 2.4, 3.0), 1)
    cam = cena.camera
    cam.data.lens = 50
    K.render_de(cam, (distancia * 0.85, -distancia * 1.05, distancia * 0.55),
                (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote9b_" + nome + ".png"))


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
        ("casa",        lambda: build_casa(M, False), 4.6, 1.6),
        ("casa_favela", lambda: build_casa_favela(M), 4.6, 1.6),
        ("colonial",    lambda: build_casa(M, True),  4.6, 1.6),
        ("predio2",     lambda: build_predio(M, 2),   8.5, 2.8),
        ("predio3",     lambda: build_predio(M, 3),   14.0, 3.6),
        ("loja",        lambda: build_loja(M),        4.8, 1.5),
    ]
    if "--" in sys.argv:  # ex.: run_bpy.sh build_lote9b.py -- loja predio3
        so = set(sys.argv[sys.argv.index("--") + 1:])
        jobs = [j for j in jobs if j[0] in so] or jobs
    resumo = []
    for nome, fn, dist, h_alvo in jobs:
        nodes = fn()
        dim = bbox_dim(nodes)
        resumo.append((nome, tuple(round(v, 2) for v in (dim.x, dim.y, dim.z))))
        print("L9B %-11s %.2fL x %.2fP x %.2fA" % (nome, dim.x, dim.y, dim.z))
        K.export_glb(os.path.join(SCENE, nome + ".glb"), nodes)
        amostra_tint(M, True)
        render_prop(nodes, nome, dist, h_alvo)
        amostra_tint(M, False)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    print("RESUMO_LOTE9B:", resumo)
    print("LOTE9B_OK")
