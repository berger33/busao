# Lote 8 — coletaveis + ceu (Blender 4.5 headless).
# Contrato:
#   * coletaveis (assets/collectibles/*.glb): modelos CENTRADOS na origem
#     (o jogo instancia a ~1,25 m de altura e gira o node pai em Y; o centro
#     do volume e a "anca" do giro). Escala 1:1, frente para -Y no Blender
#     (= +Z no Godot, virada para o jogador).
#   * ceu (assets/sky_fx/*.glb): mesmo contrato; o jogo gira o node em Y.
# Nada aqui e primitiva solta em runtime: cada peca e um GLB PBR completo.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
COL = str(K.REPO / "assets" / "collectibles")
SKY = str(K.REPO / "assets" / "sky_fx")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(COL, exist_ok=True)
os.makedirs(SKY, exist_ok=True)
TAU = K.TAU


# ------------------------------------------------------------------ geometria
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


def tronco(nome, r_base, r_topo, z0, h, seg=18):
    o = K.pilar(nome, r_base, (r_topo / r_base) if r_base > 0 else 0.0, seg=seg)
    K.sozinho(o)
    o.scale = (1, 1, h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.location = (0, 0, z0)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return o


def esfera(nome, centro, raios, nivel=2):
    return K.elipsoide(nome, centro, raios, nivel=nivel)


def revolucao(nome, perfil, seg=28):
    """Lathe ao longo de Z. perfil = [(z, r), ...] da base ao topo."""
    verts, faces = [], []
    for (z, r) in perfil:
        for k in range(seg):
            a = k / seg * TAU
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for s in range(len(perfil) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((s * seg + k, s * seg + k2, (s + 1) * seg + k2, (s + 1) * seg + k))
    if perfil[0][1] > 1e-4:
        cb = len(verts); verts.append((0, 0, perfil[0][0]))
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((cb, k2, k))
    if perfil[-1][1] > 1e-4:
        ct = len(verts); verts.append((0, 0, perfil[-1][0]))
        base = len(perfil) - 1
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((ct, base * seg + k, base * seg + k2))
    return K.novo_obj(nome, K.malha(nome, verts, faces))


def cilindro_bpy(nome, raio, altura, z0=0.0, seg=48):
    """Cilindro do proprio Blender (tem UVs usaveis na lateral e nas tampas)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=raio, depth=altura, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = nome
    o.location = (0, 0, z0)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return o


def centraliza(obj):
    """Desloca (e aplica) o objeto para que o centro da bbox fique na origem."""
    K.sozinho(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = obj.data
    mm = [1e9, 1e9, 1e9]; MM = [-1e9, -1e9, -1e9]
    for v in me.vertices:
        for i in range(3):
            mm[i] = min(mm[i], v.co[i]); MM[i] = max(MM[i], v.co[i])
    cen = Vector(((mm[0] + MM[0]) / 2, (mm[1] + MM[1]) / 2, (mm[2] + MM[2]) / 2))
    obj.location = -cen
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)


def bbox_dim(nodes):
    bb = Vector((1e9, 1e9, 1e9)); bt = Vector((-1e9, -1e9, -1e9))
    for o in nodes:
        for v in o.bound_box:
            p = o.matrix_world @ Vector(v)
            for i in range(3):
                bb[i] = min(bb[i], p[i]); bt[i] = max(bt[i], p[i])
    return bt - bb


# ------------------------------------------------------------------ texturas
def fonte(tamanho):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:
        return ImageFont.load_default()


def texto_centro(d, txt, cx, y, fonte_, fill):
    bb = d.textbbox((0, 0), txt, font=fonte_)
    w = bb[2] - bb[0]
    d.text((cx - w / 2, y), txt, font=fonte_, fill=fill)


def textura(nome, W, H, desenha, metal=0.0, rough=0.5, emissao=0.0):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    desenha(d, W, H)
    caminho = os.path.join(K.OUT_DIR, nome + ".png")
    img.save(caminho)
    bimg = D.images.load(caminho)
    m = D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bimg
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emissao > 0.0:
        m.node_tree.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emissao
    return m


def cara_frontal(obj, mat_idx):
    """Atribui mat_idx ao(s) poligono(s) da frente (Blender -Y)."""
    me = obj.data
    me.update()
    for p in me.polygons:
        if p.center.y < -1e-4:  # poligono da face frontal
            p.material_index = mat_idx
    return obj


# ------------------------------------------------------------------ materiais
def mats():
    m = {}
    m["ouro"] = K.material("C8Ouro", (0.93, 0.66, 0.18), 0.28, 1.0)
    m["ouro_esc"] = K.material("C8OuroEsc", (0.70, 0.46, 0.13), 0.34, 1.0)
    m["aco"] = K.material("C8Aco", (0.55, 0.58, 0.62), 0.35, 0.6)
    m["aco_esc"] = K.material("C8AcoEsc", (0.24, 0.27, 0.32), 0.42, 0.55)
    m["vidro"] = K.material("C8Vidro", (0.62, 0.74, 0.80), 0.10, 0.0)
    m["borracha"] = K.material("C8Borracha", (0.10, 0.11, 0.13), 0.8)
    m["xicara"] = K.material("C8Xicara", (0.94, 0.92, 0.88), 0.42)
    m["cafe"] = K.material("C8Cafe", (0.30, 0.19, 0.12), 0.18)
    m["kraft"] = K.material("C8Kraft", (0.71, 0.52, 0.36), 0.72)
    m["paozinho"] = K.material("C8Paozinho", (0.93, 0.72, 0.40), 0.48)
    m["paozinho_esc"] = K.material("C8PaozinhoEsc", (0.80, 0.56, 0.25), 0.55)
    m["massa"] = K.material("C8Massa", (0.90, 0.62, 0.32), 0.52)
    m["massa_esc"] = K.material("C8MassaEsc", (0.78, 0.48, 0.22), 0.58)
    m["cana"] = K.material("C8Cana", (0.32, 0.58, 0.30), 0.55)
    m["cana_no"] = K.material("C8CanaNo", (0.22, 0.46, 0.20), 0.5)
    m["folha"] = K.material("C8Folha", (0.36, 0.66, 0.30), 0.62)
    m["frango"] = K.material("C8Frango", (0.86, 0.56, 0.22), 0.5)
    m["frango_claro"] = K.material("C8FrangoClaro", (0.95, 0.72, 0.38), 0.6)
    m["garrafa"] = K.material("C8Garrafa", (0.10, 0.42, 0.28), 0.22)
    m["pet_verde"] = K.material("C8PetVerde", (0.08, 0.32, 0.20), 0.15)
    m["tampa_meta"] = K.material("C8TampaMeta", (0.82, 0.84, 0.86), 0.30, 0.75)
    m["azul_toldo"] = K.material("C8AzulToldo", (0.16, 0.40, 0.75), 0.55)
    m["hastes"] = K.material("C8Hastes", (0.75, 0.77, 0.80), 0.4, 0.5)
    m["branco_aviao"] = K.material("C8BrancoAviao", (0.92, 0.93, 0.95), 0.35)
    m["azul_aviao"] = K.material("C8AzulAviao", (0.15, 0.30, 0.58), 0.4)
    m["drone"] = K.material("C8Drone", (0.35, 0.40, 0.48), 0.45, 0.2)
    m["rotor"] = K.material("C8Rotor", (0.80, 0.84, 0.88), 0.35)
    m["lente"] = K.material("C8Lente", (0.15, 0.17, 0.20), 0.18)
    return m


# ------------------------------------------------------------------ build
def build_coin(M):
    R, E = 0.30, 0.06
    o = cilindro_bpy("Moeda", R, E, seg=64)
    o.rotation_euler.x = rad(-90)   # eixo Z -> +Y (tampas viram frente/tras)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    def face_frontal(d, W, H):
        d.rectangle([0, 0, W, H], fill=(216, 168, 66))
        d.ellipse([int(W * 0.04)] * 2 + [int(W * 0.96)] * 2, outline=(120, 84, 26), width=max(2, W // 48))
        d.ellipse([int(W * 0.10)] * 2 + [int(W * 0.90)] * 2, outline=(150, 108, 38), width=max(2, W // 96))
        f1, f2 = fonte(int(W * 0.16)), fonte(int(W * 0.44))
        texto_centro(d, "R$", W / 2, int(H * 0.16), f1, (140, 100, 34))
        texto_centro(d, "0,25", W / 2, int(H * 0.34), f2, (120, 84, 26))

    def face_tras(d, W, H):
        d.rectangle([0, 0, W, H], fill=(212, 162, 62))
        d.ellipse([int(W * 0.04)] * 2 + [int(W * 0.96)] * 2, outline=(118, 82, 24), width=max(2, W // 48))
        d.ellipse([int(W * 0.12)] * 2 + [int(W * 0.88)] * 2, outline=(148, 106, 36), width=max(1, W // 96))
        f1, f2 = fonte(int(W * 0.22)), fonte(int(W * 0.16))
        texto_centro(d, "BRASIL", W / 2, int(H * 0.30), f1, (120, 84, 26))
        texto_centro(d, "2026", W / 2, int(H * 0.58), f2, (120, 84, 26))

    frente = textura("C8MoedaFrente", 256, 256, face_frontal, metal=0.9, rough=0.32, emissao=0.25)
    tras = textura("C8MoedaTras", 256, 256, face_tras, metal=0.9, rough=0.32, emissao=0.25)
    me = o.data
    me.materials.append(M["ouro"])
    me.materials.append(frente)
    me.materials.append(tras)
    me.update()
    for p in me.polygons:
        if p.center.y < -E * 0.4:
            p.material_index = 1   # frente (valor)
        elif p.center.y > E * 0.4:
            p.material_index = 2   # tras (BRASIL)
        else:
            p.material_index = 0   # borda serrilhada
    centraliza(o)
    o.name = "Moeda"
    return [o]


def build_golden(M):
    corpo = caixa("Bilhete", (0, 0, 0), (0.46, 0.05, 0.30), subd=0)

    def face_f(d, W, H):
        d.rectangle([0, 0, W, H], fill=(238, 190, 70))
        d.rectangle([int(W * 0.06)] * 2 + [int(W * 0.94)] * 2, outline=(150, 106, 36), width=max(2, W // 40))
        # estrela de 5 pontas
        cx, cy, R1, R2 = W / 2, int(H * 0.38), int(H * 0.30), int(H * 0.12)
        pts = []
        for i in range(10):
            rr = R1 if i % 2 == 0 else R2
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=(255, 214, 96), outline=(150, 106, 36))
        f1 = fonte(int(H * 0.16))
        texto_centro(d, "PREMIADO", W / 2, int(H * 0.72), f1, (150, 106, 36))

    def face_t(d, W, H):
        d.rectangle([0, 0, W, H], fill=(224, 172, 60))
        f1 = fonte(int(H * 0.18))
        texto_centro(d, "BUSÃO", W / 2, int(H * 0.42), f1, (130, 92, 30))

    frente = textura("C8BilheteF", 256, 168, face_f, metal=0.9, rough=0.3, emissao=0.55)
    tras = textura("C8BilheteT", 256, 168, face_t, metal=0.9, rough=0.3, emissao=0.4)
    corpo.data.materials.append(M["ouro_esc"])
    corpo.data.materials.append(frente)
    corpo.data.materials.append(tras)
    cara_frontal(corpo, 1)
    # face de tras = +Y
    corpo.data.update()
    for p in corpo.data.polygons:
        if p.center.y > 1e-4:
            p.material_index = 2
    centraliza(corpo)
    corpo.name = "BilheteDourado"
    return [corpo]


def build_coffee(M):
    partes = []
    copo = tronco("Copo", 0.155, 0.185, -0.155, 0.31, seg=24)
    K.pintar(copo, M["xicara"]); partes.append((copo, "Prop"))
    base = tronco("CopoBase", 0.13, 0.155, -0.175, 0.03, seg=24)
    K.pintar(base, M["xicara"]); partes.append((base, "Prop"))
    faixa = tronco("CopoFaixa", 0.162, 0.168, -0.08, 0.12, seg=24)
    K.pintar(faixa, M["kraft"]); partes.append((faixa, "Prop"))
    tampa = tronco("Tampa", 0.19, 0.192, 0.155, 0.035, seg=28)
    K.pintar(tampa, M["cafe"]); partes.append((tampa, "Prop"))
    teto = tronco("TampaTeto", 0.175, 0.175, 0.19, 0.012, seg=28)
    K.pintar(teto, M["cafe"]); partes.append((teto, "Prop"))
    boca = tronco("TampaBoca", 0.02, 0.02, 0.205, 0.012, seg=10)
    K.pintar(boca, M["cafe"]); partes.append((boca, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "Cafe"
    return [corpo]


def build_bread(M):
    partes = []
    base = esfera("PaoBase", (0, 0, 0), (0.235, 0.21, 0.185), nivel=2)
    K.pintar(base, M["paozinho"]); partes.append((base, "Prop"))
    # manchas de forno
    for (x, y, z, s) in ((0.10, 0.10, 0.10, 0.10), (-0.11, -0.08, 0.12, 0.09), (0.0, -0.12, -0.06, 0.08)):
        mancha = esfera("PaoMancha", (x, y, z), (s, s * 0.7, s * 0.7), nivel=1)
        K.pintar(mancha, M["paozinho_esc"]); partes.append((mancha, "Prop"))
    # sulco central
    sulco = caixa("PaoSulco", (0, 0, 0.03), (0.05, 0.30, 0.02), subd=0)
    sulco.rotation_euler.z = rad(28)
    K.pintar(sulco, M["paozinho_esc"]); partes.append((sulco, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "PaoDeQueijo"
    return [corpo]


def build_pastel(M):
    partes = []
    massa = esfera("PastelMassa", (0, 0, 0), (0.33, 0.185, 0.115), nivel=2)
    K.pintar(massa, M["massa"]); partes.append((massa, "Prop"))
    # crimpado: gominhos nas bordas longas
    for i in range(6):
        t = -1.0 + 2.0 * i / 5.0
        for sinal in (1.0, -1.0):
            gomo = esfera("PastelGomo", (t * 0.29, sinal * 0.175, 0.10), (0.05, 0.035, 0.028), nivel=1)
            K.pintar(gomo, M["massa_esc"]); partes.append((gomo, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "Pastel"
    return [corpo]


def build_sugarcane(M):
    partes = []
    for side in (-0.09, 0.0, 0.09):
        z0 = -0.235
        for (seg_z, seg_h) in ((z0, 0.10), (z0 + 0.115, 0.02), (z0 + 0.175, 0.10), (z0 + 0.29, 0.02)):
            raio = 0.048 if seg_h < 0.05 else 0.047
            node = tronco("CanaNo" if seg_h < 0.05 else "CanaTalo", raio, raio, 0.0, seg_h, seg=14)
            node.location = (side, 0, seg_z)
            K.sozinho(node)
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
            K.pintar(node, M["cana_no"] if seg_h < 0.05 else M["cana"]); partes.append((node, "Prop"))
    # folhas no topo
    for i, ang in enumerate(range(0, 360, 60)):
        folha = caixa("CanaFolha", (0, 0, 0), (0.05, 0.22, 0.012), subd=0)
        K.sozinho(folha)
        folha.rotation_euler = (rad(30), 0, rad(ang))
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        folha.location = (0, 0, 0.24)
        K.sozinho(folha)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        K.pintar(folha, M["folha"]); partes.append((folha, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "CaldoDeCana"
    return [corpo]


def build_pass(M):
    corpo = caixa("ValeTransporte", (0, 0, 0), (0.46, 0.04, 0.30), subd=0)

    def face_f(d, W, H):
        d.rectangle([0, 0, W, H], fill=(16, 52, 110))
        d.rectangle([0, 0, W, int(H * 0.20)], fill=(250, 200, 60))
        d.rectangle([0, int(H * 0.80), W, H], fill=(250, 200, 60))
        f1, f2, f3 = fonte(int(H * 0.13)), fonte(int(H * 0.26)), fonte(int(H * 0.10))
        texto_centro(d, "VALE-TRANSPORTE", W / 2, int(H * 0.02), f1, (16, 40, 84))
        texto_centro(d, "BUSÃO", W / 2, int(H * 0.32), f2, (250, 250, 250))
        texto_centro(d, "SÃO PAULO", W / 2, int(H * 0.66), f3, (150, 200, 235))

    def face_t(d, W, H):
        d.rectangle([0, 0, W, H], fill=(16, 52, 110))
        d.rectangle([int(W * 0.10), int(H * 0.10), int(W * 0.90), int(H * 0.15)], fill=(240, 240, 240))
        f1 = fonte(int(H * 0.06))
        texto_centro(d, "PRENDA AQUI", W / 2, int(H * 0.55), f1, (120, 140, 180))

    frente = textura("C8ValeF", 256, 168, face_f, rough=0.4)
    tras = textura("C8ValeT", 256, 168, face_t, rough=0.4)
    corpo.data.materials.append(frente)
    corpo.data.materials.append(tras)
    cara_frontal(corpo, 0)
    corpo.data.update()
    for p in corpo.data.polygons:
        if p.center.y > 1e-4:
            p.material_index = 1
    centraliza(corpo)
    corpo.name = "ValeTransporte"
    return [corpo]


def build_coxinha(M):
    perfil = [(0.0, 0.185), (0.14, 0.275), (0.30, 0.245), (0.46, 0.165),
              (0.60, 0.095), (0.72, 0.045), (0.82, 0.012)]
    corpo = revolucao("Coxinha", perfil, seg=30)
    K.pintar(corpo, M["frango"])
    bico = esfera("CoxinhaBico", (0, 0, 0.86), (0.035, 0.035, 0.05), nivel=1)
    K.pintar(bico, M["frango_claro"])
    corpo = K.join_parts([(corpo, "Prop"), (bico, "Prop")])
    centraliza(corpo)
    # coxinha real e teardrop moderada (altura ~0,62 m, largura ~0,55 m)
    K.sozinho(corpo)
    corpo.scale = (1, 1, 0.68)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    corpo.name = "Coxinha"
    return [corpo]


def build_guarana(M):
    partes = []
    corpo = cilindro_bpy("GuaranaCorpo", 0.115, 0.46, seg=36)
    K.pintar(corpo, M["garrafa"]); partes.append((corpo, "Prop"))
    pescoco = tronco("GuaranaPescoco", 0.055, 0.085, 0.205, 0.10, seg=24)
    K.pintar(pescoco, M["pet_verde"]); partes.append((pescoco, "Prop"))
    tampa = tronco("GuaranaTampa", 0.052, 0.05, 0.305, 0.05, seg=20)
    K.pintar(tampa, M["tampa_meta"]); partes.append((tampa, "Prop"))

    def rotulo(d, W, H):
        d.rectangle([0, 0, W, H], fill=(244, 240, 232))
        d.rectangle([0, 0, W, int(H * 0.30)], fill=(210, 30, 34))
        d.rectangle([0, int(H * 0.72), W, H], fill=(14, 96, 58))
        f1, f2 = fonte(int(H * 0.26)), fonte(int(H * 0.14))
        texto_centro(d, "GUARANA", W / 2, int(H * 0.02), f1, (250, 250, 250))
        texto_centro(d, "REFRIGERANTE", W / 2, int(H * 0.78), f2, (240, 250, 240))

    rot = tronco("GuaranaRotulo", 0.118, 0.118, -0.02, 0.16, seg=36)
    m_rot = textura("C8GuaranaRotulo", 256, 96, rotulo, rough=0.5)
    rot.data.materials.append(m_rot)
    partes.append((rot, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "Guarana"
    return [corpo]


def build_pix(M):
    partes = []
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    corpo = bpy.context.active_object
    corpo.name = "PixCorpo"
    corpo.scale = (0.20, 0.015, 0.32)
    K.sozinho(corpo)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type='BEVEL')
    corpo.modifiers["Bevel"].width = 0.012
    corpo.modifiers["Bevel"].segments = 2
    K.sozinho(corpo)
    bpy.ops.object.modifier_apply(modifier="Bevel")
    K.pintar(corpo, M["drone"]); partes.append((corpo, "Prop"))

    def tela(d, W, H):
        d.rectangle([0, 0, W, H], fill=(8, 34, 45))
        for i in range(1, 6):
            d.rectangle([0, i * H / 6, W, i * H / 6], fill=(10, 44, 58))
        f1 = fonte(int(H * 0.42))
        texto_centro(d, "PIX", W / 2, int(H * 0.10), f1, (120, 240, 210))
        f2 = fonte(int(H * 0.13))
        texto_centro(d, "TURBO", W / 2, int(H * 0.66), f2, (150, 220, 200))

    vidro = caixa("PixTela", (0, -0.016, 0.0), (0.185, 0.004, 0.295), subd=0)
    m_tela = textura("C8PixTela", 256, 160, tela, rough=0.2, emissao=1.6)
    vidro.data.materials.append(m_tela)
    cara_frontal(vidro, 0)
    # a tela fica na face frontal (-Y): o poligono de tras nao existe (caixa tem so a capa frontal usada)
    partes.append((vidro, "Prop"))
    # camera
    cam = esfera("PixCam", (-0.07, -0.02, -0.18), (0.022, 0.02, 0.022), nivel=1)
    K.pintar(cam, M["lente"]); partes.append((cam, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "PixTurbo"
    return [corpo]


def build_umbrella(M):
    partes = []
    R = 0.30
    perfil = [(0.0, R), (0.02, R), (0.07, R * 1.01), (0.16, R * 0.97),
              (0.24, R * 0.78), (0.30, R * 0.5), (0.335, 0.02)]
    copa = revolucao("GuardaChuvaCopa", perfil, seg=36)
    K.pintar(copa, M["azul_toldo"]); partes.append((copa, "Prop"))
    for i in range(8):
        a = i * TAU / 8
        raio = R * 1.0
        # nervura inclinada do centro ate a borda da copa
        v = Vector((raio * math.cos(a), raio * math.sin(a), -0.30))
        col = K.pilar("GuardaNerv", 0.006, 1.0, seg=6)
        K.sozinho(col); col.scale = (1, 1, v.length)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        col.rotation_mode = 'QUATERNION'
        col.rotation_quaternion = v.to_track_quat('Z', 'Y')
        col.location = Vector((0.0, 0.0, 0.30))
        K.sozinho(col)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        col.rotation_mode = 'XYZ'
        K.pintar(col, M["hastes"]); partes.append((col, "Prop"))
    mastro = tronco("GuardaMastro", 0.016, 0.016, -0.34, 0.36, seg=12)
    K.pintar(mastro, M["hastes"]); partes.append((mastro, "Prop"))
    ponteira = tronco("GuardaPonteira", 0.02, 0.0, 0.335, 0.06, seg=12)
    K.pintar(ponteira, M["hastes"]); partes.append((ponteira, "Prop"))
    tampao = esfera("GuardaTampao", (0, 0, 0.35), (0.028, 0.028, 0.03), nivel=1)
    K.pintar(tampao, M["hastes"]); partes.append((tampao, "Prop"))
    # cabo em gancho
    gancho = esfera("GuardaCabo", (0, 0, -0.40), (0.02, 0.02, 0.05), nivel=1)
    K.pintar(gancho, M["aco_esc"]); partes.append((gancho, "Prop"))
    corpo = K.join_parts(partes)
    centraliza(corpo)
    corpo.name = "GuardaChuva"
    return [corpo]


# ------------------------------------------------------------------ ceu
def build_aviao(M):
    partes = []
    # fuselagem: loftero ao longo de Y (bico em -Y, cauda em +Y)
    secoes = [(-1.15, 0, 0.10, 0.10), (-0.80, 0, 0.17, 0.17), (-0.10, 0, 0.185, 0.185),
              (0.55, 0, 0.16, 0.16), (0.98, 0, 0.10, 0.10)]
    fus = K.loft("AviaoFus", secoes, seg=18, tampas=True)
    K.pintar(fus, M["branco_aviao"]); partes.append((fus, "Prop"))
    # asa principal (baixa, recuada)
    asa = caixa("AviaoAsa", (0.02, 0.05, 0.22), (2.15, 0.13, 0.48), subd=0)
    K.sozinho(asa)
    asa.rotation_euler.z = rad(3)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(asa, M["branco_aviao"]); partes.append((asa, "Prop"))
    # estabilizador horizontal
    stab = caixa("AviaoStab", (0, 0.95, 0.40), (1.05, 0.09, 0.30), subd=0)
    K.pintar(stab, M["branco_aviao"]); partes.append((stab, "Prop"))
    # deriva
    deriva = caixa("AviaoDeriva", (0, 0.92, 0.16), (0.09, 0.44, 0.26), subd=0)
    K.sozinho(deriva)
    deriva.rotation_euler.z = rad(14)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(deriva, M["azul_aviao"]); partes.append((deriva, "Prop"))
    # leme (faixa azul na deriva ja basta); motores
    for sx in (1.0, -1.0):
        mot = tronco("AviaoMotor", 0.055, 0.045, 0.0, 0.26, seg=14)
        mot.location = (sx * 0.42, 0.05, 0.16)
        K.sozinho(mot)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        K.pintar(mot, M["aco_esc"]); partes.append((mot, "Prop"))
    # faixa azul na barriga
    faixa = caixa("AviaoBarriga", (0, -0.02, 0.02), (0.30, 0.02, 0.02), subd=0)
    K.pintar(faixa, M["azul_aviao"]); partes.append((faixa, "Prop"))
    corpo = K.join_parts(partes)
    corpo.name = "Aviao"
    centraliza(corpo)
    return [corpo]


def build_drone(M):
    partes = []
    corpo = caixa("DroneCorpo", (0, 0.02, -0.03), (0.34, 0.16, 0.52), subd=1)
    K.pintar(corpo, M["drone"]); partes.append((corpo, "Prop"))
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        braco = caixa("DroneBraco", (sx * 0.185, sy * 0.185, 0.06), (0.38, 0.03, 0.03), subd=0)
        K.pintar(braco, M["drone"]); partes.append((braco, "Prop"))
        motor = tronco("DroneMotor", 0.045, 0.04, 0.14, 0.05, seg=12)
        motor.location = (sx * 0.36, sy * 0.36, 0.0)
        K.sozinho(motor)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        K.pintar(motor, M["aco_esc"]); partes.append((motor, "Prop"))
        rot = tronco("DroneRot", 0.145, 0.145, 0.19, 0.012, seg=20)
        rot.location = (sx * 0.36, sy * 0.36, 0.0)
        K.sozinho(rot)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        K.pintar(rot, M["rotor"]); partes.append((rot, "Prop"))
    # camera embaixo
    gimbal = tronco("DroneGimbal", 0.03, 0.03, 0.0, 0.04, seg=10)
    gimbal.location = (0, 0.0, -0.30)
    K.sozinho(gimbal)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    K.pintar(gimbal, M["aco_esc"]); partes.append((gimbal, "Prop"))
    cam = esfera("DroneCam", (0, 0.0, -0.36), (0.028, 0.028, 0.028), nivel=1)
    K.pintar(cam, M["lente"]); partes.append((cam, "Prop"))
    # trens de pouso
    for sx in (0.23, -0.23):
        skid = caixa("DroneSkid", (sx, -0.14, -0.10), (0.03, 0.20, 0.03), subd=0)
        K.sozinho(skid)
        skid.rotation_euler.z = rad(-30)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(skid, M["aco"]); partes.append((skid, "Prop"))
    corpo = K.join_parts(partes)
    corpo.name = "Drone"
    centraliza(corpo)
    return [corpo]


# ------------------------------------------------------------------ preview + export
def preview(nodes, nome, dist, alvo_z):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    D.lights["Cheia"].energy = 4.0
    D.lights["Sol"].energy = 1.25
    cena.cycles.samples = 18
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (max(dist * 2.4, 3.0), max(dist * 2.4, 3.0), 1)
    cam = cena.camera
    cam.data.lens = 60
    K.render_de(cam, (dist * 0.85, -dist * 1.05, dist * 0.55), (0, 0, alvo_z),
                os.path.join(K.OUT_DIR, "lote8_" + nome + ".png"))


if __name__ == "__main__":
    K.reset_scene()
    M = mats()
    coletaveis = [
        ("coin", build_coin, 1.5),
        ("golden", build_golden, 1.5),
        ("coffee", build_coffee, 1.5),
        ("bread", build_bread, 1.6),
        ("pastel", build_pastel, 1.6),
        ("sugarcane", build_sugarcane, 1.6),
        ("pass", build_pass, 1.5),
        ("coxinha", build_coxinha, 1.6),
        ("guarana", build_guarana, 1.6),
        ("pix", build_pix, 1.5),
        ("umbrella", build_umbrella, 1.9),
    ]
    ceu = [
        ("aviao", build_aviao, 4.2),
        ("drone", build_drone, 2.4),
    ]
    resumo = []
    for nome, fn, dist in coletaveis + ceu:
        nodes = fn(M)
        dim = bbox_dim(nodes)
        resumo.append((nome, tuple(round(v, 2) for v in (dim.x, dim.y, dim.z))))
        print("L8 %-10s L%.2f P%.2f A%.2f" % (nome, dim.x, dim.y, dim.z))
        destino = SKY if nome in ("aviao", "drone") else COL
        K.export_glb(os.path.join(destino, nome + ".glb"), nodes)
        preview(nodes, nome, dist, 0.0)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    print("RESUMO_LOTE8:", resumo)
    print("LOTE8_OK")
