# Lote 5 — veiculos (Blender 4.5 headless).
# Contrato do jogo (assets/vehicles/README.md): comprimento no eixo Z com a
# FRENTE para -Z no Godot. No Blender isso equivale a modelar com a frente
# para +Y (o export yup converte (x,y,z)->(x,z,-y)). Origem no chao.
#
# Rodas sao nos separados com eixo no X (geometria "assada", sem rotacao no
# no) e nomes Wheel*/BusWheel*/MotoWheel*: _animate_traffic gira rotation.x.
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


def loft_box(nome, secoes, seg=20, tampas=True, subd=1):
    """Loft com secao super-elipse (caixa arredondada).
    secoes = [(y, cz, meia_largura_x, meia_altura_z, n), ...];
    n = arredondamento (2 = elipse, 5+ = caixa). subd=1: encolhe pouco."""
    verts, faces = [], []
    for (y, cz, w, h, n) in secoes:
        e = 2.0 / n
        for k in range(seg):
            a = k / seg * TAU
            c, s = math.cos(a), math.sin(a)
            x = w * math.copysign(abs(c) ** e, c)
            z = h * math.copysign(abs(s) ** e, s)
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
    # ordem das faces: -Y, +Y (frente), -Z, +Z, -X, +X
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 6, 2)]
    o = K.novo_obj(nome, K.malha(nome, v, f))
    # UVs 0..1 por face (necessario para texturas, ex.: letreiro emissivo)
    uv = o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = [(0.02, 0.02), (0.98, 0.02), (0.98, 0.98), (0.02, 0.98)][(li - poly.loop_start) % 4]
    if subd:
        mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = subd
    return o


def roda(nome, raio, largura, mat_pneu, mat_aro, mat_cubo, duplada=False):
    """Roda com eixo no X (geometria assada): pneu toro + aro + cubo."""
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


def vidros_cabine(nome, secoes, mat):
    o = loft_box(nome, secoes, seg=16)
    K.pintar(o, mat)
    return o


def mat_pintura(nome, cor):
    return K.material(nome, cor, 0.30, 0.55)


def mat_emissivo(nome, cor_base, cor_emissao, energia):
    m = K.material(nome, cor_base, 0.4, 0.0)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*cor_emissao, 1.0)
    b.inputs["Emission Strength"].default_value = energia
    return m


# ============================================================================
# CARRO HATCH (trafego) — vermelho, estilo Gol/Onix. ~4,2 m.
# ============================================================================
def build_hatch():
    K.reset_scene()
    pintura = mat_pintura("hatch_pintura", (0.615, 0.143, 0.158))   # #c83f45-ish
    vidro = K.material("hatch_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("hatch_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("hatch_cromo", (0.80, 0.83, 0.85), 0.22, 0.85)
    escuro = K.material("hatch_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    farol = mat_emissivo("hatch_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("hatch_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)
    placa = K.material("hatch_placa", (0.88, 0.89, 0.90), 0.5, 0.1)

    partes = []
    def add(o, grupo="Chassi"):
        K.pintar(o, pintura) if grupo == "Pintura" else None
        partes.append((o, grupo))

    # corpo inferior (frente = +Y)
    corpo = loft_box("HatchCorpo", [
        (-2.10, 0.50, 0.70, 0.30, 7.0),
        (-1.92, 0.54, 0.81, 0.40, 8.0),
        (-1.20, 0.57, 0.86, 0.43, 9.0),
        (-0.30, 0.58, 0.87, 0.44, 9.0),
        (+0.90, 0.57, 0.86, 0.44, 9.0),
        (+1.70, 0.54, 0.84, 0.41, 8.0),
        (+2.00, 0.49, 0.79, 0.36, 8.0),
        (+2.10, 0.45, 0.70, 0.30, 7.0),
    ], subd=1)
    K.pintar(corpo, pintura); add(corpo)

    # estofamento preto inferior (saias)
    saia = loft_box("HatchSaia", [
        (-2.02, 0.30, 0.74, 0.15, 6.0),
        (-1.90, 0.28, 0.83, 0.14, 7.0),
        (+1.90, 0.28, 0.83, 0.14, 7.0),
        (+2.02, 0.30, 0.74, 0.15, 6.0),
    ], subd=1)
    K.pintar(saia, escuro); add(saia)

    # cabine de vidro (greenhouse) + teto na cor
    cabine = vidros_cabine("HatchVidro", [
        (-1.55, 0.98, 0.66, 0.08, 6.0),
        (-1.35, 1.10, 0.78, 0.24, 7.0),
        (-0.55, 1.20, 0.81, 0.27, 8.0),
        (+0.30, 1.20, 0.81, 0.27, 8.0),
        (+0.88, 1.05, 0.73, 0.16, 7.0),
        (+1.05, 0.97, 0.68, 0.08, 6.0),
    ], vidro)
    cabine.modifiers["Subd"].levels = cabine.modifiers["Subd"].render_levels = 1
    add(cabine)
    teto = loft_box("HatchTeto", [
        (-1.25, 1.36, 0.70, 0.06, 6.0),
        (-0.55, 1.40, 0.77, 0.07, 7.0),
        (+0.30, 1.40, 0.77, 0.07, 7.0),
        (+0.75, 1.34, 0.67, 0.05, 6.0),
    ], subd=1)
    K.pintar(teto, pintura); add(teto)

    # grade + farois embutidos
    grade = caixa("HatchGrade", (0, 2.04, 0.50), (1.10, 0.12, 0.22))
    K.pintar(grade, escuro); add(grade)
    far1 = caixa("HatchFarolE", (-0.58, 2.03, 0.62), (0.36, 0.12, 0.15))
    K.pintar(far1, farol); add(far1)
    far2 = caixa("HatchFarolD", (0.58, 2.03, 0.62), (0.36, 0.12, 0.15))
    K.pintar(far2, farol); add(far2)
    lat1 = caixa("HatchLanternaE", (-0.62, -2.04, 0.68), (0.32, 0.12, 0.17))
    K.pintar(lat1, lanterna); add(lat1)
    lat2 = caixa("HatchLanternaD", (0.62, -2.04, 0.68), (0.32, 0.12, 0.17))
    K.pintar(lat2, lanterna); add(lat2)
    pl1 = caixa("HatchPlacaF", (0, 2.06, 0.32), (0.40, 0.05, 0.13))
    K.pintar(pl1, placa); add(pl1)
    pl2 = caixa("HatchPlacaT", (0, -2.07, 0.36), (0.40, 0.05, 0.13))
    K.pintar(pl2, placa); add(pl2)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        haste = coluna_entre("HatchRetH" + suf, (sx * 0.82, 0.88, 1.02), (sx * 0.94, 0.86, 1.06), 0.015)
        K.pintar(haste, escuro); add(haste)
        m = caixa("HatchRetro" + suf, (sx * 0.98, 0.86, 1.08), (0.10, 0.16, 0.10))
        K.pintar(m, pintura); add(m)

    corpo_junto = K.join_parts(partes)
    corpo_junto.name = "Hatch"
    rodas = []
    for (sx, nome, py) in ((-1, "WheelFL", 1.28), (1, "WheelFR", 1.28), (-1, "WheelRL", -1.32), (1, "WheelRR", -1.32)):
        r = roda(nome, 0.30, 0.20, borracha, cromo, escuro)
        r.location = (sx * 0.78, py, 0.30)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo_junto] + rodas


# ============================================================================
# CARRO SEDAN (estacionado) — prata, estilo Santana/Prisma. ~4,4 m.
# ============================================================================
def build_sedan():
    K.reset_scene()
    pintura = mat_pintura("sedan_pintura", (0.79, 0.80, 0.79))
    vidro = K.material("sedan_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("sedan_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("sedan_cromo", (0.80, 0.83, 0.85), 0.22, 0.85)
    escuro = K.material("sedan_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    farol = mat_emissivo("sedan_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("sedan_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)
    placa = K.material("sedan_placa", (0.88, 0.89, 0.90), 0.5, 0.1)

    partes = []
    def add(o):
        partes.append((o, "Chassi"))

    corpo = loft_box("SedanCorpo", [
        (-2.20, 0.50, 0.70, 0.30, 7.0),
        (-2.02, 0.54, 0.82, 0.40, 8.0),
        (-1.30, 0.57, 0.86, 0.43, 9.0),
        (-0.30, 0.58, 0.87, 0.44, 9.0),
        (+0.90, 0.57, 0.86, 0.44, 9.0),
        (+1.80, 0.54, 0.84, 0.41, 8.0),
        (+2.10, 0.49, 0.79, 0.36, 8.0),
        (+2.20, 0.45, 0.70, 0.30, 7.0),
    ], subd=1)
    K.pintar(corpo, pintura); add(corpo)
    # porta-malas elevado (3 volumes)
    mala = loft_box("SedanMala", [
        (-2.16, 0.90, 0.64, 0.07, 6.0),
        (-1.80, 0.94, 0.76, 0.09, 7.0),
        (-1.05, 0.95, 0.80, 0.10, 8.0),
        (-0.95, 0.94, 0.80, 0.09, 8.0),
    ], subd=1)
    K.pintar(mala, pintura); add(mala)
    saia = loft_box("SedanSaia", [
        (-2.12, 0.30, 0.74, 0.15, 6.0),
        (-2.00, 0.28, 0.83, 0.14, 7.0),
        (+2.00, 0.28, 0.83, 0.14, 7.0),
        (+2.12, 0.30, 0.74, 0.15, 6.0),
    ], subd=1)
    K.pintar(saia, escuro); add(saia)
    cabine = vidros_cabine("SedanVidro", [
        (-1.15, 1.00, 0.64, 0.08, 6.0),
        (-0.95, 1.12, 0.76, 0.24, 7.0),
        (-0.30, 1.21, 0.79, 0.27, 8.0),
        (+0.42, 1.21, 0.79, 0.27, 8.0),
        (+0.95, 1.06, 0.71, 0.16, 7.0),
        (+1.10, 0.98, 0.66, 0.08, 6.0),
    ], vidro)
    cabine.modifiers["Subd"].levels = cabine.modifiers["Subd"].render_levels = 1
    add(cabine)
    teto = loft_box("SedanTeto", [
        (-0.85, 1.35, 0.68, 0.06, 6.0),
        (-0.30, 1.39, 0.75, 0.07, 7.0),
        (+0.42, 1.39, 0.75, 0.07, 7.0),
        (+0.82, 1.33, 0.65, 0.05, 6.0),
    ], subd=1)
    K.pintar(teto, pintura); add(teto)
    grade = caixa("SedanGrade", (0, 2.14, 0.50), (1.10, 0.12, 0.22))
    K.pintar(grade, escuro); add(grade)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("SedanFarol" + suf, (sx * 0.60, 2.13, 0.62), (0.36, 0.12, 0.15))
        K.pintar(f, farol); add(f)
        l = caixa("SedanLanterna" + suf, (sx * 0.64, -2.14, 0.70), (0.32, 0.12, 0.17))
        K.pintar(l, lanterna); add(l)
        haste = coluna_entre("SedanRetH" + suf, (sx * 0.82, 0.98, 1.02), (sx * 0.94, 0.96, 1.06), 0.015)
        K.pintar(haste, escuro); add(haste)
        m = caixa("SedanRetro" + suf, (sx * 0.98, 0.96, 1.08), (0.10, 0.16, 0.10))
        K.pintar(m, pintura); add(m)
    pl1 = caixa("SedanPlacaF", (0, 2.16, 0.32), (0.40, 0.05, 0.13))
    K.pintar(pl1, placa); add(pl1)
    pl2 = caixa("SedanPlacaT", (0, -2.17, 0.56), (0.40, 0.05, 0.13))
    K.pintar(pl2, placa); add(pl2)

    corpo_junto = K.join_parts(partes)
    corpo_junto.name = "Sedan"
    rodas = []
    for (sx, nome, py) in ((-1, "WheelFL", 1.36), (1, "WheelFR", 1.36), (-1, "WheelRL", -1.42), (1, "WheelRR", -1.42)):
        r = roda(nome, 0.30, 0.20, borracha, cromo, escuro)
        r.location = (sx * 0.78, py, 0.30)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo_junto] + rodas


# ============================================================================
# MOTO (obstáculo de rua) — mantém as proporções da moto procedural para o
# motoqueiro sentar certo: rodas r 0,33 em y ±0,65, assento ~0,75.
# ============================================================================
def build_moto():
    K.reset_scene()
    pintura = mat_pintura("moto_pintura", (0.76, 0.16, 0.14))
    borracha = K.material("moto_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("moto_cromo", (0.82, 0.85, 0.86), 0.20, 0.9)
    escuro = K.material("moto_escuro", (0.10, 0.11, 0.13), 0.55, 0.3)
    aro = K.material("moto_aro", (0.60, 0.63, 0.66), 0.3, 0.8)
    farol = mat_emissivo("moto_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.4)
    lanterna = mat_emissivo("moto_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)

    rodas = []
    for (py, nome) in ((0.65, "MotoWheelF"), (-0.65, "MotoWheelR")):
        r = roda(nome, 0.33, 0.13, borracha, aro, escuro)
        r.location = (0, py, 0.33)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)

    partes = []
    def add(o):
        partes.append((o, "Moto"))

    # quadro: tubos ligando coluna de direcao, pedivela e eixo traseiro
    col = (0, 0.40, 0.98)      # topo da coluna (frente)
    bb = (0, -0.06, 0.36)      # central/pedivela
    tras = (0, -0.65, 0.33)    # eixo traseiro
    add(coluna_entre("MotoDown", (0, 0.20, 0.66), bb, 0.030))
    add(coluna_entre("MotoTop", (0, -0.22, 0.94), col, 0.026))
    add(coluna_entre("MotoSeatTube", bb, (0, -0.22, 0.94), 0.026))
    for sx in (-1.0, 1.0):
        add(coluna_entre("MotoSwing%d" % int(sx), (sx * 0.05, -0.12, 0.42), (sx * 0.06, -0.65, 0.33), 0.020))
        add(coluna_entre("MotoFork%d" % int(sx), (sx * 0.07, 0.36, 0.92), (sx * 0.07, 0.65, 0.33), 0.022))
    K.pintar(partes[-1][0], cromo)
    K.pintar(partes[-2][0], cromo)
    for o, _ in partes:
        K.pintar(o, escuro) if not o.data.materials else None
    # tanque
    tanque = K.elipsoide("MotoTanque", (0, 0.10, 0.86), (0.15, 0.34, 0.13), nivel=2)
    K.pintar(tanque, pintura); add(tanque)
    # banco
    banco = K.elipsoide("MotoBanco", (0, -0.30, 0.80), (0.13, 0.30, 0.07), nivel=1)
    K.pintar(banco, escuro); add(banco)
    # para-lama dianteiro (abracando o topo da roda)
    lama = K.elipsoide("MotoLama", (0, 0.66, 0.66), (0.09, 0.26, 0.05), nivel=1)
    lama.rotation_euler = (rad(-30), 0, 0)
    K.sozinho(lama)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(lama, pintura); add(lama)
    # motor
    motor = caixa("MotoMotor", (0, 0.02, 0.44), (0.24, 0.30, 0.26), subd=1)
    K.pintar(motor, escuro); add(motor)
    # escapamento
    esc = coluna_entre("MotoEscape", (0.14, 0.02, 0.40), (0.16, -0.72, 0.36), 0.042, 0.8, 10)
    K.pintar(esc, cromo); add(esc)
    # guidao
    guid = coluna_entre("MotoGuidao", (-0.31, 0.42, 1.04), (0.31, 0.42, 1.04), 0.020)
    K.pintar(guid, cromo); add(guid)
    for sx in (-1.0, 1.0):
        punho = coluna_entre("MotoPunho%d" % int(sx), (sx * 0.26, 0.42, 1.04), (sx * 0.33, 0.42, 1.04), 0.026)
        K.pintar(punho, borracha); add(punho)
    coluna = coluna_entre("MotoColuna", (0, 0.33, 0.88), (0, 0.42, 1.04), 0.024)
    K.pintar(coluna, escuro); add(coluna)
    # farol e lanterna
    fl = K.elipsoide("MotoFarol", (0, 0.55, 0.98), (0.075, 0.06, 0.075), nivel=1)
    K.pintar(fl, farol); add(fl)
    lt = K.elipsoide("MotoLanterna", (0, -0.72, 0.62), (0.05, 0.05, 0.05), nivel=1)
    K.pintar(lt, lanterna); add(lt)
    # rabeta
    rab = K.elipsoide("MotoRabeta", (0, -0.60, 0.68), (0.10, 0.18, 0.06), nivel=1)
    K.pintar(rab, pintura); add(rab)

    corpo = K.join_parts(partes)
    corpo.name = "Moto"
    return [corpo] + rodas


# ============================================================================
# CAMINHAO — cabine avançada + carroceria de madeira (6,4 x 2,7).
# ============================================================================
def build_caminhao():
    K.reset_scene()
    pintura = mat_pintura("truck_pintura", (0.13, 0.34, 0.55))
    vidro = K.material("truck_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material("truck_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("truck_cromo", (0.80, 0.83, 0.85), 0.22, 0.85)
    escuro = K.material("truck_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    madeira = K.material("truck_madeira", (0.45, 0.30, 0.17), 0.78, 0.0)
    madeira_e = K.material("truck_madeira_escura", (0.33, 0.21, 0.11), 0.8, 0.0)
    farol = mat_emissivo("truck_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo("truck_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)

    partes = []
    def add(o):
        partes.append((o, "Chassi"))

    # chassi
    chassi = caixa("TruckChassi", (0, -0.10, 0.62), (0.86, 5.90, 0.22))
    K.pintar(chassi, escuro); add(chassi)
    # cabine (avançada, frente chata)
    cab = loft_box("TruckCabine", [
        (+1.25, 1.30, 1.00, 0.55, 6.0),
        (+1.42, 1.55, 1.08, 0.85, 7.0),
        (+1.55, 1.95, 1.10, 1.05, 8.0),
        (+2.55, 2.05, 1.10, 1.02, 8.0),
        (+2.88, 1.95, 1.08, 0.90, 8.0),
        (+3.02, 1.55, 1.04, 0.62, 7.0),
        (+3.08, 1.10, 0.98, 0.38, 6.0),
    ], subd=1)
    K.pintar(cab, pintura); add(cab)
    # para-brisa: caixa inclinada na frente (topo puxado para tras)
    pb = caixa("TruckParabrisa", (0, 2.92, 2.10), (1.86, 0.10, 0.78))
    pb.rotation_euler = (rad(-10), 0, 0)
    K.sozinho(pb)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(pb, vidro); add(pb)
    # grade e farois
    grade = caixa("TruckGrade", (0, 3.06, 1.30), (1.40, 0.12, 0.46))
    K.pintar(grade, escuro); add(grade)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("TruckFarol" + suf, (sx * 0.76, 3.04, 0.94), (0.34, 0.12, 0.18))
        K.pintar(f, farol); add(f)
        l = caixa("TruckLanterna" + suf, (sx * 1.02, -3.10, 1.20), (0.20, 0.08, 0.14))
        K.pintar(l, lanterna); add(l)
        haste = coluna_entre("TruckRetH" + suf, (sx * 1.10, 2.60, 2.10), (sx * 1.28, 2.50, 2.20), 0.02)
        K.pintar(haste, escuro); add(haste)
        m = caixa("TruckRetro" + suf, (sx * 1.30, 2.48, 2.28), (0.08, 0.14, 0.26))
        K.pintar(m, escuro); add(m)
    # carroceria de madeira: assoalho + fasquias + esteios
    piso = caixa("TruckPiso", (0, -1.05, 1.16), (2.28, 4.10, 0.10))
    K.pintar(piso, madeira_e); add(piso)
    for sx in (-1.0, 1.0):
        for i, zz in enumerate((1.42, 1.66, 1.90, 2.14)):
            fas = caixa("TruckFas%d_%d" % (int(sx), i), (sx * 1.12, -1.05, zz), (0.06, 4.06, 0.16))
            K.pintar(fas, madeira); add(fas)
    for yy in (-3.0, -2.1, -1.2, -0.3, 0.6):
        for sx in (-1.0, 1.0):
            est = caixa("TruckEsteio", (sx * 1.12, yy, 1.72), (0.07, 0.07, 1.12))
            K.pintar(est, madeira_e); add(est)
    portao = caixa("TruckPortao", (0, -3.08, 1.72), (2.24, 0.06, 1.10))
    K.pintar(portao, madeira); add(portao)
    fronteira = caixa("TruckFronteira", (0, 1.02, 1.66), (2.24, 0.06, 1.0))
    K.pintar(fronteira, madeira); add(fronteira)

    corpo = K.join_parts(partes)
    corpo.name = "Truck"
    rodas = []
    for (sx, nome, py, dup) in ((-1, "WheelFL", 2.15, False), (1, "WheelFR", 2.15, False),
                                (-1, "WheelRL", -1.45, True), (1, "WheelRR", -1.45, True)):
        r = roda(nome, 0.48, 0.30, borracha, cromo, escuro, duplada=dup)
        r.location = (sx * 1.02, py, 0.48)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo] + rodas


# ============================================================================
# ONIBUS urbano brasileiro (parametrico no comprimento).
# ============================================================================
def build_onibus(comprimento, amarelo, faixa, destino_txt, nome_base):
    K.reset_scene()
    pintura = mat_pintura(nome_base + "_pintura", amarelo)
    faixa_m = mat_pintura(nome_base + "_faixa", faixa)
    vidro = K.material(nome_base + "_vidro", (0.09, 0.12, 0.16), 0.06, 0.18)
    borracha = K.material(nome_base + "_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    aro = K.material(nome_base + "_aro", (0.62, 0.65, 0.67), 0.3, 0.8)
    escuro = K.material(nome_base + "_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)
    metal = K.material(nome_base + "_metal", (0.80, 0.81, 0.78), 0.4, 0.4)
    farol = mat_emissivo(nome_base + "_farol", (0.95, 0.93, 0.80), (1.0, 0.95, 0.72), 2.2)
    lanterna = mat_emissivo(nome_base + "_lanterna", (0.75, 0.12, 0.14), (1.0, 0.10, 0.08), 2.0)

    L2 = comprimento * 0.5
    partes = []
    def add(o):
        partes.append((o, "Onibus"))

    corpo = loft_box("BusCorpo", [
        (-L2,        1.50, 1.14, 1.02, 6.0),
        (-L2 + 0.30, 1.55, 1.26, 1.30, 8.0),
        (-L2 * 0.45, 1.58, 1.28, 1.36, 9.0),
        (+L2 * 0.42, 1.58, 1.28, 1.36, 9.0),
        (+L2 - 0.72, 1.55, 1.26, 1.32, 8.0),
        (+L2 - 0.22, 1.46, 1.22, 1.20, 7.0),
        (+L2,        1.30, 1.14, 0.96, 6.0),
    ], subd=1)
    K.pintar(corpo, pintura); add(corpo)
    # faixa colorida inferior (sobressai 2 cm)
    faixa_o = loft_box("BusFaixa", [
        (-L2 + 0.05, 0.72, 1.16, 0.16, 6.0),
        (-L2 + 0.35, 0.72, 1.30, 0.17, 8.0),
        (+L2 - 0.60, 0.72, 1.30, 0.17, 8.0),
        (+L2 - 0.10, 0.66, 1.24, 0.15, 6.0),
    ], subd=1)
    K.pintar(faixa_o, faixa_m); add(faixa_o)
    # janela corrida lateral (faixa retangular sobressaindo 2 cm)
    jan = loft_box("BusJanelas", [
        (-L2 + 0.55, 2.08, 1.12, 0.34, 7.0),
        (-L2 + 0.90, 2.08, 1.30, 0.48, 8.0),
        (+L2 - 1.30, 2.08, 1.30, 0.48, 8.0),
        (+L2 - 0.90, 2.04, 1.26, 0.40, 7.0),
    ], subd=1)
    K.pintar(jan, vidro); add(jan)
    # para-brisa inclinado (caixa)
    pb = caixa("BusParabrisa", (0, L2 - 0.30, 2.05), (2.16, 0.10, 0.92))
    pb.rotation_euler = (rad(-12), 0, 0)
    K.sozinho(pb)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    K.pintar(pb, vidro); add(pb)
    # porta dianteira e central (lado -X, como o onibus procedural)
    for yy, sufixo in ((L2 - 1.55, "F"), (-0.55, "M")):
        porta = caixa("BusPorta" + sufixo, (-1.285, yy, 1.30), (0.04, 1.15, 1.90))
        K.pintar(porta, escuro); add(porta)
        pv = caixa("BusPortaVid" + sufixo, (-1.30, yy, 1.92), (0.03, 0.95, 0.72))
        K.pintar(pv, vidro); add(pv)
    # painel de destino com textura emissiva
    painel = caixa("BusDestino", (0, L2 - 0.30, 2.62), (1.50, 0.34, 0.28))
    painel.data.materials.append(escuro)
    painel.data.materials.append(texto_emissivo(nome_base + "_letreiro", destino_txt))
    painel.data.polygons[1].material_index = 1
    add(painel)
    # farois, lanternas, para-choque, ar-condicionado
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        f = caixa("BusFarol" + suf, (sx * 0.82, L2 - 0.06, 0.86), (0.40, 0.12, 0.18))
        K.pintar(f, farol); add(f)
        l = caixa("BusLanterna" + suf, (sx * 0.86, -L2 + 0.06, 0.92), (0.34, 0.10, 0.16))
        K.pintar(l, lanterna); add(l)
    bpc = caixa("BusParaChoque", (0, L2 - 0.02, 0.44), (2.42, 0.16, 0.24))
    K.pintar(bpc, escuro); add(bpc)
    bpt = caixa("BusParaChoqueT", (0, -L2 + 0.02, 0.44), (2.42, 0.16, 0.24))
    K.pintar(bpt, escuro); add(bpt)
    ac = caixa("BusArCond", (0, 0.30, 3.02), (1.30, 2.40, 0.16), subd=1)
    K.pintar(ac, metal); add(ac)
    for sx, suf in ((-1.0, "E"), (1.0, "D")):
        esp = caixa("BusRetro" + suf, (sx * 1.38, L2 - 0.80, 2.30), (0.10, 0.08, 0.26))
        K.pintar(esp, escuro); add(esp)

    corpo_junto = K.join_parts(partes)
    corpo_junto.name = nome_base
    rodas = []
    eixo_f = L2 - 1.45
    eixo_t = -L2 + 1.75
    for (sx, nome, py) in ((-1, "BusWheelFL", eixo_f), (1, "BusWheelFR", eixo_f), (-1, "BusWheelRL", eixo_t), (1, "BusWheelRR", eixo_t)):
        r = roda(nome, 0.48, 0.30, borracha, aro, escuro)
        r.location = (sx * 1.08, py, 0.48)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)
    return [corpo_junto] + rodas


def texto_emissivo(nome, texto):
    """Letreiro de onibus: matriz de pontos ambar sobre fundo preto."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 256, 64
    img = Image.new("RGB", (W, H), (8, 9, 10))
    dr = ImageDraw.Draw(img)
    try:
        fonte = ImageFont.load_default(size=34)
    except TypeError:
        fonte = ImageFont.load_default()
    dr.text((10, 12), texto, font=fonte, fill=(255, 176, 32))
    # pontilhado de LED: mascara escura em grade 4px
    for x in range(0, W, 4):
        dr.line([(x + 3, 0), (x + 3, H)], fill=(12, 13, 14))
    for y in range(0, H, 4):
        dr.line([(0, y + 3), (W, y + 3)], fill=(12, 13, 14))
    caminho = os.path.join(K.OUT_DIR, nome + ".png")
    img.save(caminho)
    bimg = D.images.load(caminho)
    m = D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bimg
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.6
    b.inputs["Roughness"].default_value = 0.5
    return m


# ============================================================================
# BICICLETA (obstáculo de calcada) — mesma geometria da procedural, agora
# com tubos de verdade: frente +Y, rodas em y ±0,52, centro z 0,34.
# ============================================================================
def build_bicicleta():
    K.reset_scene()
    quadro = K.material("bike_quadro", (0.11, 0.34, 0.55), 0.42, 0.55)
    borracha = K.material("bike_borracha", (0.06, 0.07, 0.09), 0.92, 0.0)
    cromo = K.material("bike_cromo", (0.78, 0.81, 0.83), 0.22, 0.85)
    escuro = K.material("bike_escuro", (0.10, 0.11, 0.13), 0.6, 0.2)

    rodas = []
    for (py, nome) in ((0.52, "BikeWheelF"), (-0.52, "BikeWheelR")):
        # pneu + aro + raios finos
        partes_r = []
        bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.048,
                                         major_segments=22, minor_segments=10, location=(0, 0, 0))
        pneu = bpy.context.active_object; pneu.name = nome + "_pneu"
        pneu.rotation_euler = (0, rad(90), 0)
        K.sozinho(pneu)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(pneu, borracha); partes_r.append((pneu, nome))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.286, minor_radius=0.020,
                                         major_segments=20, minor_segments=8, location=(0, 0, 0))
        aro_o = bpy.context.active_object; aro_o.name = nome + "_aro"
        aro_o.rotation_euler = (0, rad(90), 0)
        K.sozinho(aro_o)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(aro_o, cromo); partes_r.append((aro_o, nome))
        for i in range(6):
            a = i / 6.0 * math.pi  # 3 diametros = 6 pontas
            raio = coluna_entre(nome + "_raio%d" % i,
                                (0, 0.27 * math.cos(a), 0.27 * math.sin(a)),
                                (0, -0.27 * math.cos(a), -0.27 * math.sin(a)), 0.006, 1.0, 6)
            K.pintar(raio, cromo); partes_r.append((raio, nome))
        cubo = K.pilar(nome + "_cubo", 0.045, 1.0, 10)
        K.sozinho(cubo)
        cubo.scale = (1, 1, 0.09)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        cubo.rotation_euler = (0, rad(90), 0)
        K.sozinho(cubo)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        cubo.location = (0, 0, -0.045)
        K.sozinho(cubo)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        K.pintar(cubo, escuro); partes_r.append((cubo, nome))
        r = K.join_parts(partes_r)
        r.name = nome
        r.location = (0, py, 0.34)
        K.sozinho(r)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        rodas.append(r)

    partes = []
    def add(o):
        partes.append((o, "Bike"))

    # tubos do quadro (convertidos do espaco do jogo: (x,y,z)->(x,-z,y))
    tubos = [
        ("BikeHead",  (0, 0.44, 0.62), (0, 0.40, 0.98)),
        ("BikeDown",  (0, -0.06, 0.36), (0, 0.40, 0.98)),
        ("BikeSeatT", (0, -0.06, 0.36), (0, -0.20, 1.00)),
        ("BikeTop",   (0, -0.20, 1.00), (0, 0.40, 0.98)),
        ("BikeChainL", (0, -0.06, 0.36), (0, -0.52, 0.34)),
        ("BikeSeatS", (0, -0.20, 0.98), (0, -0.52, 0.34)),
        ("BikeForkL", (0, 0.40, 0.98), (0, 0.52, 0.34)),
    ]
    for nome, A, B in tubos:
        t = coluna_entre(nome, A, B, 0.026)
        K.pintar(t, quadro); add(t)
    for sx in (-1.0, 1.0):
        c = coluna_entre("BikeChain%d" % int(sx), (sx * 0.02, -0.06, 0.36), (sx * 0.02, -0.52, 0.34), 0.012)
        K.pintar(c, cromo); add(c)
        f = coluna_entre("BikeFork%d" % int(sx), (sx * 0.035, 0.40, 0.98), (sx * 0.045, 0.52, 0.34), 0.018)
        K.pintar(f, cromo); add(f)
    # guidao e mesa
    mesa = coluna_entre("BikeMesa", (0, 0.42, 0.99), (0, 0.44, 1.06), 0.020)
    K.pintar(mesa, cromo); add(mesa)
    guid = coluna_entre("BikeGuidao", (-0.26, 0.44, 1.06), (0.26, 0.44, 1.06), 0.018)
    K.pintar(guid, cromo); add(guid)
    for sx in (-1.0, 1.0):
        punho = coluna_entre("BikePunho%d" % int(sx), (sx * 0.22, 0.44, 1.06), (sx * 0.27, 0.44, 1.06), 0.024)
        K.pintar(punho, borracha); add(punho)
    # canote + selim
    canote = coluna_entre("BikeCanote", (0, -0.20, 0.99), (0, -0.22, 1.08), 0.016)
    K.pintar(canote, cromo); add(canote)
    selim = caixa("BikeSelim", (0, -0.22, 1.10), (0.10, 0.30, 0.05), subd=1)
    K.pintar(selim, escuro); add(selim)
    # pedivela + pedais + coroa
    coroa = K.pilar("BikeCoroa", 0.09, 1.0, 14)
    K.sozinho(coroa)
    coroa.scale = (1, 1, 0.02)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    coroa.rotation_euler = (0, rad(90), 0)
    K.sozinho(coroa)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    coroa.location = (0.03, -0.06, 0.35)
    K.sozinho(coroa)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    K.pintar(coroa, cromo); add(coroa)
    for sx, dz in ((1.0, -0.08), (-1.0, 0.08)):
        braco = coluna_entre("BikePediv%d" % int(sx), (0, -0.06, 0.36), (sx * 0.10, -0.06 + dz, 0.36 + dz * 0.5), 0.014)
        K.pintar(braco, cromo); add(braco)
        pedal = caixa("BikePedal%d" % int(sx), (sx * 0.14, -0.06 + dz, 0.36 + dz * 0.5), (0.09, 0.16, 0.02))
        K.pintar(pedal, escuro); add(pedal)

    corpo = K.join_parts(partes)
    corpo.name = "Bicicleta"
    return [corpo] + rodas


# ============================================================================
# PREVIEW — um render por veiculo.
# ============================================================================
def render_veiculo(nodes, nome, distancia, altura_alvo=0.9):
    cena = bpy.context.scene
    K.setup_preview(fundo=(0.42, 0.50, 0.62, 1.0), energia_fundo=0.42)
    # piso maior para veiculos
    for o in list(cena.collection.objects):
        if o.name == "Piso":
            o.scale = (distancia * 2.2, distancia * 2.2, 1)
    cam = cena.camera
    cam.data.lens = 42
    K.render_de(cam, (distancia * 0.82, distancia * 1.05, distancia * 0.52),
                (0, 0, altura_alvo), os.path.join(K.OUT_DIR, "lote5_" + nome + ".png"))


def bbox_z_len(nodes):
    import mathutils
    bb = mathutils.Vector((1e9, 1e9, 1e9)); bt = mathutils.Vector((-1e9, -1e9, -1e9))
    for o in nodes:
        for v in o.bound_box:
            p = o.matrix_world @ mathutils.Vector(v)
            bb = mathutils.Vector((min(bb.x, p.x), min(bb.y, p.y), min(bb.z, p.z)))
            bt = mathutils.Vector((max(bt.x, p.x), max(bt.y, p.y), max(bt.z, p.z)))
    return bt - bb


if __name__ == "__main__":
    jobs = [
        ("car",        build_hatch,     (4.4, 1.55), 6.4, 0.7),
        ("carro",      build_sedan,     (4.4, 1.55), 6.6, 0.7),
        ("motorcycle", build_moto,      (2.1, 1.15), 3.4, 0.6),
        ("truck",      build_caminhao,  (6.4, 2.7),  9.5, 1.2),
        ("bus_traffic", lambda: build_onibus(7.4, (0.86, 0.68, 0.20), (0.12, 0.42, 0.25), "CIRCULAR", "BusTrafego"), (7.4, 3.0), 11.0, 1.4),
        ("onibus",     lambda: build_onibus(8.2, (0.957, 0.749, 0.239), (0.929, 0.388, 0.298), "PONTO FINAL", "Onibus"), (8.2, 3.0), 11.5, 1.4),
        ("bicycle",    build_bicicleta, (1.85, 1.15), 2.6, 0.55),
    ]
    resumo = []
    for nome, fn, alvo, dist, h_alvo in jobs:
        nodes = fn()
        dim = bbox_z_len(nodes)
        # Y do Blender = comprimento; Z = altura
        fit = min(alvo[0] / max(dim.y, 0.001), alvo[1] / max(dim.z, 0.001))
        print("L5 %-12s nativo: %.2fC x %.2fL x %.2fA  (fit %.3f)" % (nome, dim.y, dim.x, dim.z, fit))
        resumo.append((nome, tuple(round(v, 2) for v in (dim.y, dim.x, dim.z)), round(fit, 3)))
        caminho = K.export_glb(os.path.join(VEIC, nome + ".glb"), nodes)
        render_veiculo(nodes, nome, dist, h_alvo)
    print("RESUMO_LOTE5:", resumo)
    print("LOTE5_OK")
