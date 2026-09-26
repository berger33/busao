# Lote 6 — variantes de veiculos (Blender 4.5 headless) + texturas baked simples.
# Gera 4 GLBs variantes com cores/rodas alternativas, mantendo o mesmo contrato
# do Lote 5 (frente -Z, origem no chao, nos Wheel* com eixo X, GLB_FIT).
# As variantes sao drop-ins opcionais: o jogo sorteia entre a base e as
# variantes se o arquivo existir (ver game_3d.gd _vehicle_variant).
# Rodas com textura baked simples: gera uma imagem 256x256 de roda com faixa
# e aplica como textura emissiva leve para diferenciar.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
VEIC = str(K.REPO / "assets" / "vehicles")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(VEIC, exist_ok=True)
TAU = K.TAU

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

def loft_box(nome, secoes, seg=20, tampas=True, subd=1):
    verts, faces = [], []
    for (y, cz, meia_largura_x, meia_altura_z, n) in secoes:
        e = 2.0 / n
        for k in range(seg):
            a = k / seg * TAU
            c, s = math.cos(a), math.sin(a)
            x = meia_largura_x * math.copysign(abs(c) ** e, c)
            z = meia_altura_z * math.copysign(abs(s) ** e, s)
            verts.append((x, y, cz + z))
    for s in range(len(secoes) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((s * seg + k, s * seg + k2, (s + 1) * seg + k2, (s + 1) * seg + k))
    if tampas:
        faces.append(tuple(range(seg - 1, -1, -1)))
        faces.append(tuple(range(len(secoes) * seg - 1, (len(secoes) - 1) * seg - 1, -1)))
    o = K.novo_obj(nome, K.malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = subd; mm.quality = 4
    return o

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

def roda(nome, raio, largura, mat_pneu, mat_aro, mat_cubo, duplada=False):
    partes = []
    bpy.ops.mesh.primitive_torus_add(major_radius=raio - largura * 0.42,
                                     minor_radius=largura * 0.55 if not duplada else largura * 0.62,
                                     major_segments=22, minor_segments=10, location=(0, 0, 0))
    pneu = bpy.context.active_object; pneu.name = nome + "_pneu"
    pneu.rotation_euler = (0, rad(90), 0)
    K.sozinho(pneu)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(pneu, mat_pneu); partes.append((pneu, nome))
    aro = K.pilar(nome + "_aro", raio * 0.62, 1.0, 14)
    K.sozinho(aro)
    aro.scale = (1, 1, largura * (1.15 if duplada else 0.8))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    aro.rotation_euler = (0, rad(90), 0)
    K.sozinho(aro)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    aro.location = (0, 0, -largura * (0.575 if duplada else 0.4))
    K.sozinho(aro)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    K.pintar(aro, mat_aro); partes.append((aro, nome))
    cubo = K.pilar(nome + "_cubo", raio * 0.20, 1.0, 10)
    K.sozinho(cubo)
    cubo.scale = (1, 1, largura * (1.3 if duplada else 0.95))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cubo.rotation_euler = (0, rad(90), 0)
    K.sozinho(cubo)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    cubo.location = (0, 0, -largura * (0.65 if duplada else 0.475))
    K.sozinho(cubo)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    K.pintar(cubo, mat_cubo); partes.append((cubo, nome))
    r = K.join_parts(partes)
    r.name = nome
    return r

def mat_pintura(nome, cor):
    return K.material(nome, cor, 0.30, 0.55)
def mat_emissivo(nome, cor_base, cor_emissao, energia):
    m = K.material(nome, cor_base, 0.4, 0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*cor_emissao, 1.0)
    b.inputs["Emission Strength"].default_value = energia
    return m

def textura_roda_baked(nome, cor_base, faixa):
    # textura simples 256x256 para roda: fundo cor_base + faixa circular
    from PIL import Image, ImageDraw
    W = H = 256
    img = Image.new("RGB", (W, H), tuple(int(c*255) for c in cor_base))
    dr = ImageDraw.Draw(img)
    # faixa
    dr.ellipse([W*0.25, H*0.25, W*0.75, H*0.75], fill=tuple(int(c*255) for c in faixa), width=0)
    dr.ellipse([W*0.35, H*0.35, W*0.65, H*0.65], fill=tuple(int(c*255) for c in cor_base))
    # parafusos
    for ang in [0, 72, 144, 216, 288]:
        x = W*0.5 + math.cos(math.radians(ang))*W*0.18
        y = H*0.5 + math.sin(math.radians(ang))*H*0.18
        dr.ellipse([x-6, y-6, x+6, y+6], fill=(30,30,35))
    caminho = os.path.join(K.OUT_DIR, nome + ".png")
    img.save(caminho)
    bimg = D.images.load(caminho)
    m = D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bimg
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Metallic"].default_value = 0.15
    return m

# ============================================================================
# VARIANTE HATCH AZUL (frente +Y, mesmo loft do Lote 5, cor azul)
# ============================================================================
def build_hatch_azul():
    K.reset_scene()
    pintura = mat_pintura("hatch_azul_pintura", (0.14, 0.28, 0.68))
    vidro = K.material("hatch_azul_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("hatch_azul_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("hatch_azul_cromo", (0.80, 0.83, 0.85), 0.22, 0.85)
    escuro = K.material("hatch_azul_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    farol = mat_emissivo("hatch_azul_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("hatch_azul_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)
    placa = K.material("hatch_azul_placa", (0.88, 0.89, 0.90), 0.5, 0.1)
    partes = []
    def add(o): partes.append((o, "Chassi"))
    corpo = loft_box("HatchAzulCorpo", [(-2.10, 0.50, 0.70, 0.30, 7.0),(-1.92, 0.54, 0.81, 0.40, 8.0),(-1.20, 0.57, 0.86, 0.43, 9.0),(-0.30, 0.58, 0.87, 0.44, 9.0),(+0.90, 0.57, 0.86, 0.44, 9.0),(+1.70, 0.54, 0.84, 0.41, 8.0),(+2.00, 0.49, 0.79, 0.36, 8.0),(+2.10, 0.45, 0.70, 0.30, 7.0)], subd=1)
    K.pintar(corpo, pintura); add(corpo)
    saia = loft_box("HatchAzulSaia", [(-2.02, 0.30, 0.74, 0.15, 6.0),(-1.90, 0.28, 0.83, 0.14, 7.0),(+1.90, 0.28, 0.83, 0.14, 7.0),(+2.02, 0.30, 0.74, 0.15, 6.0)], subd=1)
    K.pintar(saia, escuro); add(saia)
    cabine = loft_box("HatchAzulVidro", [(-1.55, 0.98, 0.66, 0.08, 6.0),(-1.35, 1.10, 0.78, 0.24, 7.0),(-0.55, 1.20, 0.81, 0.27, 8.0),(+0.30, 1.20, 0.81, 0.27, 8.0),(+0.88, 1.05, 0.73, 0.16, 7.0),(+1.05, 0.97, 0.68, 0.08, 6.0)], seg=16)
    cabine.modifiers["Subd"].levels = cabine.modifiers["Subd"].render_levels = 1
    K.pintar(cabine, vidro); add(cabine)
    teto = loft_box("HatchAzulTeto", [(-1.25, 1.36, 0.70, 0.06, 6.0),(-0.55, 1.40, 0.77, 0.07, 7.0),(+0.30, 1.40, 0.77, 0.07, 7.0),(+0.75, 1.34, 0.67, 0.05, 6.0)], subd=1)
    K.pintar(teto, pintura); add(teto)
    grade = caixa("HatchAzulGrade", (0, 2.04, 0.50), (1.10, 0.12, 0.22))
    K.pintar(grade, escuro); add(grade)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("HatchAzulFarol"+suf, (sx*0.58, 2.03, 0.62), (0.36, 0.12, 0.15))
        K.pintar(f, farol); add(f)
        l = caixa("HatchAzulLanterna"+suf, (sx*0.62, -2.04, 0.68), (0.32, 0.12, 0.17))
        K.pintar(l, lanterna); add(l)
        haste = coluna_entre("HatchAzulRetH"+suf, (sx*0.82, 0.88, 1.02), (sx*0.94, 0.86, 1.06), 0.015)
        K.pintar(haste, escuro); add(haste)
        m = caixa("HatchAzulRetro"+suf, (sx*0.98, 0.86, 1.08), (0.10, 0.16, 0.10))
        K.pintar(m, pintura); add(m)
    pl1 = caixa("HatchAzulPlacaF", (0, 2.06, 0.32), (0.40, 0.05, 0.13))
    K.pintar(pl1, placa); add(pl1)
    pl2 = caixa("HatchAzulPlacaT", (0, -2.07, 0.36), (0.40, 0.05, 0.13))
    K.pintar(pl2, placa); add(pl2)
    corpo_junto = K.join_parts(partes)
    corpo_junto.name = "HatchAzul"
    rodas = []
    # rodas com aro texturizado baked
    mat_aro_baked = textura_roda_baked("hatch_azul_aro_tex", (0.78,0.81,0.83), (0.14,0.28,0.68))
    for (sx, nome, py) in ((-1, "WheelFL", 1.28), (1, "WheelFR", 1.28), (-1, "WheelRL", -1.32), (1, "WheelRR", -1.32)):
        r = roda(nome, 0.30, 0.20, borracha, mat_aro_baked, escuro)
        r.location = (sx*0.78, py, 0.30)
        K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo_junto] + rodas

def build_hatch_prata():
    K.reset_scene()
    pintura = mat_pintura("hatch_prata_pintura", (0.76, 0.76, 0.77))
    vidro = K.material("hatch_prata_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("hatch_prata_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    escuro = K.material("hatch_prata_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    farol = mat_emissivo("hatch_prata_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("hatch_prata_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)
    placa = K.material("hatch_prata_placa", (0.88, 0.89, 0.90), 0.5, 0.1)
    # rodas pretas para diferenciar da azul
    cromo_preto = K.material("hatch_prata_aro", (0.12, 0.12, 0.13), 0.45, 0.2)
    partes = []
    def add(o): partes.append((o, "Chassi"))
    corpo = loft_box("HatchPrataCorpo", [(-2.10, 0.50, 0.70, 0.30, 7.0),(-1.92, 0.54, 0.81, 0.40, 8.0),(-1.20, 0.57, 0.86, 0.43, 9.0),(-0.30, 0.58, 0.87, 0.44, 9.0),(+0.90, 0.57, 0.86, 0.44, 9.0),(+1.70, 0.54, 0.84, 0.41, 8.0),(+2.00, 0.49, 0.79, 0.36, 8.0),(+2.10, 0.45, 0.70, 0.30, 7.0)], subd=1)
    K.pintar(corpo, pintura); add(corpo)
    saia = loft_box("HatchPrataSaia", [(-2.02, 0.30, 0.74, 0.15, 6.0),(-1.90, 0.28, 0.83, 0.14, 7.0),(+1.90, 0.28, 0.83, 0.14, 7.0),(+2.02, 0.30, 0.74, 0.15, 6.0)], subd=1)
    K.pintar(saia, escuro); add(saia)
    cabine = loft_box("HatchPrataVidro", [(-1.55, 0.98, 0.66, 0.08, 6.0),(-1.35, 1.10, 0.78, 0.24, 7.0),(-0.55, 1.20, 0.81, 0.27, 8.0),(+0.30, 1.20, 0.81, 0.27, 8.0),(+0.88, 1.05, 0.73, 0.16, 7.0),(+1.05, 0.97, 0.68, 0.08, 6.0)], seg=16)
    cabine.modifiers["Subd"].levels = cabine.modifiers["Subd"].render_levels = 1
    K.pintar(cabine, vidro); add(cabine)
    teto = loft_box("HatchPrataTeto", [(-1.25, 1.36, 0.70, 0.06, 6.0),(-0.55, 1.40, 0.77, 0.07, 7.0),(+0.30, 1.40, 0.77, 0.07, 7.0),(+0.75, 1.34, 0.67, 0.05, 6.0)], subd=1)
    K.pintar(teto, pintura); add(teto)
    grade = caixa("HatchPrataGrade", (0, 2.04, 0.50), (1.10, 0.12, 0.22))
    K.pintar(grade, escuro); add(grade)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("HatchPrataFarol"+suf, (sx*0.58, 2.03, 0.62), (0.36, 0.12, 0.15))
        K.pintar(f, farol); add(f)
        l = caixa("HatchPrataLanterna"+suf, (sx*0.62, -2.04, 0.68), (0.32, 0.12, 0.17))
        K.pintar(l, lanterna); add(l)
    pl1 = caixa("HatchPrataPlacaF", (0, 2.06, 0.32), (0.40, 0.05, 0.13))
    K.pintar(pl1, placa); add(pl1)
    pl2 = caixa("HatchPrataPlacaT", (0, -2.07, 0.36), (0.40, 0.05, 0.13))
    K.pintar(pl2, placa); add(pl2)
    corpo_junto = K.join_parts(partes)
    corpo_junto.name = "HatchPrata"
    rodas = []
    for (sx, nome, py) in ((-1, "WheelFL", 1.28), (1, "WheelFR", 1.28), (-1, "WheelRL", -1.32), (1, "WheelRR", -1.32)):
        r = roda(nome, 0.30, 0.20, borracha, cromo_preto, escuro)
        r.location = (sx*0.78, py, 0.30)
        K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo_junto] + rodas

def build_truck_vermelho():
    K.reset_scene()
    pintura = mat_pintura("truck_vm_pintura", (0.70, 0.14, 0.13))
    vidro = K.material("truck_vm_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("truck_vm_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("truck_vm_cromo", (0.80, 0.83, 0.85), 0.22, 0.85)
    escuro = K.material("truck_vm_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    madeira = K.material("truck_vm_madeira", (0.45, 0.30, 0.17), 0.78, 0.0)
    madeira_e = K.material("truck_vm_madeira_e", (0.33, 0.21, 0.11), 0.8, 0.0)
    farol = mat_emissivo("truck_vm_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("truck_vm_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)
    partes = []
    def add(o): partes.append((o, "Chassi"))
    chassi = caixa("TruckVmChassi", (0, -0.10, 0.62), (0.86, 5.90, 0.22))
    K.pintar(chassi, escuro); add(chassi)
    cab = loft_box("TruckVmCabine", [(+1.25, 1.30, 1.00, 0.55, 6.0),(+1.42, 1.55, 1.08, 0.85, 7.0),(+1.55, 1.95, 1.10, 1.05, 8.0),(+2.55, 2.05, 1.10, 1.02, 8.0),(+2.88, 1.95, 1.08, 0.90, 8.0),(+3.02, 1.55, 1.04, 0.62, 7.0),(+3.08, 1.10, 0.98, 0.38, 6.0)], subd=1)
    K.pintar(cab, pintura); add(cab)
    pb = caixa("TruckVmParabrisa", (0, 2.92, 2.10), (1.86, 0.10, 0.78))
    pb.rotation_euler = (rad(-10), 0, 0)
    K.sozinho(pb); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(pb, vidro); add(pb)
    grade = caixa("TruckVmGrade", (0, 3.06, 1.30), (1.40, 0.12, 0.46))
    K.pintar(grade, escuro); add(grade)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("TruckVmFarol"+suf, (sx*0.76, 3.04, 0.94), (0.34, 0.12, 0.18))
        K.pintar(f, farol); add(f)
        haste = coluna_entre("TruckVmRetH"+suf, (sx*1.10, 2.60, 2.10), (sx*1.28, 2.50, 2.20), 0.02)
        K.pintar(haste, escuro); add(haste)
        m = caixa("TruckVmRetro"+suf, (sx*1.30, 2.48, 2.28), (0.08, 0.14, 0.26))
        K.pintar(m, escuro); add(m)
    piso = caixa("TruckVmPiso", (0, -1.05, 1.16), (2.28, 4.10, 0.10))
    K.pintar(piso, madeira_e); add(piso)
    for sx in (-1.0, 1.0):
        for i, zz in enumerate((1.42, 1.66, 1.90, 2.14)):
            fas = caixa("TruckVmFas%d_%d"%(int(sx),i), (sx*1.12, -1.05, zz), (0.06, 4.06, 0.16))
            K.pintar(fas, madeira); add(fas)
    portao = caixa("TruckVmPortao", (0, -3.08, 1.72), (2.24, 0.06, 1.10))
    K.pintar(portao, madeira); add(portao)
    corpo = K.join_parts(partes)
    corpo.name = "TruckVermelho"
    rodas = []
    for (sx, nome, py, dup) in ((-1, "WheelFL", 2.15, False), (1, "WheelFR", 2.15, False), (-1, "WheelRL", -1.45, True), (1, "WheelRR", -1.45, True)):
        r = roda(nome, 0.48, 0.30, borracha, cromo, escuro, duplada=dup)
        r.location = (sx*1.02, py, 0.48)
        K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo] + rodas

def build_moto_verde():
    K.reset_scene()
    pintura = mat_pintura("moto_vd_pintura", (0.14, 0.52, 0.22))
    borracha = K.material("moto_vd_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("moto_vd_cromo", (0.82, 0.85, 0.86), 0.20, 0.9)
    escuro = K.material("moto_vd_escuro", (0.10, 0.11, 0.13), 0.55, 0.3)
    aro = K.material("moto_vd_aro", (0.60, 0.63, 0.66), 0.3, 0.8)
    farol = mat_emissivo("moto_vd_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.4)
    rodas = []
    for (py, nome) in ((0.65, "MotoWheelF"), (-0.65, "MotoWheelR")):
        r = roda(nome, 0.33, 0.13, borracha, aro, escuro)
        r.location = (0, py, 0.33)
        K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    partes = []
    def add(o): partes.append((o, "Moto"))
    col = (0, 0.40, 0.98); bb = (0, -0.06, 0.36); tras = (0, -0.65, 0.33)
    add(coluna_entre("MotoVdDown", (0, 0.20, 0.66), bb, 0.030))
    add(coluna_entre("MotoVdTop", (0, -0.22, 0.94), col, 0.026))
    add(coluna_entre("MotoVdSeat", bb, (0, -0.22, 0.94), 0.026))
    for sx in (-1.0, 1.0):
        add(coluna_entre("MotoVdSwing%d"%int(sx), (sx*0.05, -0.12, 0.42), (sx*0.06, -0.65, 0.33), 0.020))
        add(coluna_entre("MotoVdFork%d"%int(sx), (sx*0.07, 0.36, 0.92), (sx*0.07, 0.65, 0.33), 0.022))
    tanque = K.elipsoide("MotoVdTanque", (0, 0.10, 0.86), (0.15, 0.34, 0.13), nivel=2)
    K.pintar(tanque, pintura); add(tanque)
    banco = K.elipsoide("MotoVdBanco", (0, -0.30, 0.80), (0.13, 0.30, 0.07), nivel=1)
    K.pintar(banco, escuro); add(banco)
    motor = caixa("MotoVdMotor", (0, 0.02, 0.44), (0.24, 0.30, 0.26), subd=1)
    K.pintar(motor, escuro); add(motor)
    guid = coluna_entre("MotoVdGuidao", (-0.31, 0.42, 1.04), (0.31, 0.42, 1.04), 0.020)
    K.pintar(guid, cromo); add(guid)
    corpo = K.join_parts(partes)
    corpo.name = "MotoVerde"
    return [corpo] + rodas

def render_veiculo(nodes, nome, distancia, altura_alvo=0.9):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (distancia*2.2, distancia*2.2, 1)
    cam = cena.camera
    cam.data.lens = 42
    K.render_de(cam, (distancia*0.82, distancia*1.05, distancia*0.52), (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote6_"+nome+".png"))

def bbox_z_len(nodes):
    import mathutils
    bb = mathutils.Vector((1e9,1e9,1e9)); bt = mathutils.Vector((-1e9,-1e9,-1e9))
    for o in nodes:
        for v in o.bound_box:
            p = o.matrix_world @ mathutils.Vector(v)
            bb = mathutils.Vector((min(bb.x,p.x), min(bb.y,p.y), min(bb.z,p.z)))
            bt = mathutils.Vector((max(bt.x,p.x), max(bt.y,p.y), max(bt.z,p.z)))
    return bt-bb

if __name__ == "__main__":
    jobs = [
        ("car_azul", build_hatch_azul, (4.4,1.55), 6.4, 0.7),
        ("car_prata", build_hatch_prata, (4.4,1.55), 6.4, 0.7),
        ("truck_vermelho", build_truck_vermelho, (6.4,2.7), 9.5, 1.2),
        ("motorcycle_verde", build_moto_verde, (2.1,1.15), 3.4, 0.6),
    ]
    resumo=[]
    for nome, fn, alvo, dist, h in jobs:
        nodes = fn()
        dim = bbox_z_len(nodes)
        fit = min(alvo[0]/max(dim.y,0.001), alvo[1]/max(dim.z,0.001))
        print("L6 %-18s nativo: %.2fC x %.2fL x %.2fA (fit %.3f)" % (nome, dim.y, dim.x, dim.z, fit))
        resumo.append((nome, tuple(round(v,2) for v in (dim.y, dim.x, dim.z)), round(fit,3)))
        caminho = K.export_glb(os.path.join(VEIC, nome+".glb"), nodes)
        render_veiculo(nodes, nome, dist, h)
    print("RESUMO_LOTE6:", resumo)
    print("LOTE6_OK")
