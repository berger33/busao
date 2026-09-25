# Pombo v2 — corpo loftero (casco unico por secoes de espinha), asa como
# painel dobrado, cauda em leque, pernas com juntas. Blender 4.5 headless.
# Frente do modelo = -Y (=> +Z no glTF/Godot). Clips: Walk (16f), Idle (48f).
import bpy, math, os
from pathlib import Path
from mathutils import Vector

D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = os.environ.get("POMBO_OUT_DIR", str(REPO / "tools" / "blender" / "out"))
OUT_GLB = os.environ.get("POMBO_OUT_GLB", str(REPO / "assets" / "characters" / "animais" / "pombo.glb"))
OUT_BLEND = os.path.join(OUT_DIR, "pombo.blend")
PREV_A = os.path.join(OUT_DIR, "prev_34.png")
PREV_B = os.path.join(OUT_DIR, "prev_lado.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)

TAU = math.tau
def rad(d): return math.radians(d)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def novo_obj(nome, me):
    o = D.objects.new(nome, me)
    scene.collection.objects.link(o)
    return o

def malha(nome, verts, faces):
    me = D.meshes.new(nome)
    me.from_pydata(verts, [], faces)
    me.update()
    return me

def sozinho(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o

MATS = {}
def material(nome, cor, rough=0.62, metal=0.0):
    m = D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    MATS[nome] = m
    return m

def pintar(o, mat):
    o.data.materials.append(mat)

cinza_corpo = material("Corpo",     (0.290, 0.315, 0.365), 0.68)
cinza_peito = material("Peito",     (0.470, 0.480, 0.495), 0.72)
cinza_asa   = material("Asa",       (0.235, 0.258, 0.305), 0.64)
pena_prim   = material("Primarias", (0.130, 0.148, 0.185), 0.58)
pena_cauda  = material("Cauda",     (0.215, 0.235, 0.275), 0.60)
ponta_cauda = material("PontaCauda",(0.62, 0.625, 0.62),  0.64)
cabeca_m    = material("Cabeca",    (0.245, 0.268, 0.315), 0.62)
pescoco_m   = material("Pescoco",   (0.105, 0.235, 0.165), 0.28, metal=0.15)
bico_m      = material("Bico",      (0.085, 0.088, 0.100), 0.42)
ceroma_m    = material("Ceroma",    (0.72, 0.70, 0.63),    0.52)
olho_iris   = material("Iris",      (0.55, 0.27, 0.06),    0.12)
olho_pupila = material("Pupila",    (0.008, 0.007, 0.006), 0.06)
perna_m     = material("Pernas",    (0.45, 0.21, 0.17),    0.50)
garra_m     = material("Garras",    (0.075, 0.065, 0.058), 0.35)

partes = []   # (objeto, grupo_osso) — ordem define faixas de vertices
def add(o, grupo):
    partes.append((o, grupo))

# ---------------------------------------------------------------- casco (loft)
# secoes ao longo da espinha: (y, z_centro, meia_largura_x, meia_altura_z)
SECOES = [
    ( 0.108, 0.112, 0.019, 0.015),   # base da cauda
    ( 0.072, 0.120, 0.035, 0.030),
    ( 0.030, 0.114, 0.043, 0.038),
    (-0.012, 0.100, 0.045, 0.042),
    (-0.052, 0.084, 0.037, 0.040),   # peito
    (-0.086, 0.088, 0.026, 0.030),
    (-0.110, 0.108, 0.019, 0.021),   # pescoco baixo
    (-0.128, 0.136, 0.015, 0.016),
    (-0.140, 0.166, 0.012, 0.013),  # pescoco alto
]
SEG = 14
def casco():
    verts, faces = [], []
    for (y, cz, w, h) in SECOES:
        for k in range(SEG):
            a = k / SEG * TAU
            verts.append((w * math.cos(a), y, cz + h * math.sin(a)))
    for s in range(len(SECOES) - 1):
        for k in range(SEG):
            k2 = (k + 1) % SEG
            faces.append((s * SEG + k, s * SEG + k2, (s + 1) * SEG + k2, (s + 1) * SEG + k))
    faces.append(tuple(range(SEG - 1, -1, -1)))                       # traseira
    faces.append(tuple(range(len(SECOES) * SEG - 1, (len(SECOES) - 1) * SEG - 1, -1)))  # frente
    return malha("Casco", verts, faces)

corpo_o = novo_obj("CascoPombo", casco())
m = corpo_o.modifiers.new("Subd", 'SUBSURF'); m.levels = m.render_levels = 2; m.quality = 4
pintar(corpo_o, cinza_corpo)
pintar(corpo_o, pescoco_m)
pintar(corpo_o, cinza_peito)
# pinta por face: pescoço verde (seções traseiras), peito claro (baixo-frontal)
NFACE_LATERAIS = (len(SECOES) - 1) * SEG
for poly in corpo_o.data.polygons:
    if poly.index >= NFACE_LATERAIS:
        poly.material_index = 0    # tampas: cinza
        continue
    s = poly.index // SEG          # faixa de secao (0..len-2)
    k = poly.index % SEG
    a_mid = (k + 0.5) / SEG * TAU
    y_mid = (SECOES[s][0] + SECOES[s + 1][0]) * 0.5
    z_mid = (SECOES[s][1] + SECOES[s + 1][1]) * 0.5 + SECOES[s][3] * math.sin(a_mid)
    if -0.124 < y_mid <= -0.068:
        poly.material_index = 1    # pescoco verde iridescente
    if -0.088 < y_mid <= -0.028 and math.sin(a_mid) < -0.02:
        poly.material_index = 2    # peito claro
add(corpo_o, "CASCO")

# ---------------------------------------------------------------- cabeca
def elipsoide(nome, centro, raios, nivel=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=centro)
    o = bpy.context.active_object
    o.name = nome
    sozinho(o)
    o.scale = raios
    bpy.ops.object.transform_apply(scale=True)
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = nivel; mm.quality = 4
    return o

add(elipsoide("CabecaM", (0, -0.150, 0.186), (0.0215, 0.0245, 0.0225)), "Cabeca"); pintar(partes[-1][0], cabeca_m)
bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.0046, radius2=0.0009,
                                depth=0.019, location=(0, -0.176, 0.181))
bico = bpy.context.active_object; bico.name = "Bico"
sozinho(bico)
bico.rotation_euler = (rad(96), 0, 0)
bpy.ops.object.transform_apply(rotation=True)
add(bico, "Cabeca"); pintar(bico, bico_m)
add(elipsoide("Ceroma", (0, -0.1685, 0.193), (0.0046, 0.0056, 0.0034), nivel=1), "Cabeca"); pintar(partes[-1][0], ceroma_m)
for sx, suf in ((1.0, "E"), (-1.0, "D")):
    add(elipsoide("Iris" + suf, (sx * 0.0175, -0.148, 0.1935), (0.0044, 0.0044, 0.0044), nivel=1), "Cabeca"); pintar(partes[-1][0], olho_iris)
    add(elipsoide("Pupila" + suf, (sx * 0.0202, -0.1485, 0.1935), (0.0026, 0.0028, 0.0028), nivel=1), "Cabeca"); pintar(partes[-1][0], olho_pupila)

# ---------------------------------------------------------------- asa dobrada (painel unico + pontas de penas)
def pena(nome, comprimento, meia_largura, ponta=0.35):
    w = meia_largura
    verts = [(-w, -comprimento * 0.28, 0), (w, -comprimento * 0.28, 0),
             (w * 0.92, comprimento * 0.30, 0), (-w * 0.92, comprimento * 0.30, 0),
             (w * ponta, comprimento, 0), (-w * ponta, comprimento, 0)]
    faces = [(0, 1, 2, 3), (3, 2, 4), (2, 1, 4), (0, 3, 5), (3, 4, 5)]
    o = novo_obj(nome, malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = 1
    return o

def asa(sx, suf):
    # painel dobrado: gota larga do ombro ate alem da cauda, abraçando o flanco
    painel = pena("AsaPainel" + suf, 0.148, 0.026, ponta=0.30)
    sozinho(painel)
    painel.location = (sx * 0.040, -0.062, 0.118)
    painel.rotation_euler = (rad(-16), sx * rad(3), sx * rad(-4))
    bpy.ops.object.transform_apply(rotation=True, location=True)
    add(painel, "Asa"); pintar(painel, cinza_asa)
    # 5 pontas de primarias visiveis sob a ponta do painel
    for i in range(5):
        t = i / 4.0
        o = pena("Prim%d%s" % (i, suf), 0.040 - 0.008 * t, 0.0068 * (1 - 0.35 * t))
        sozinho(o)
        o.location = (sx * (0.046 + 0.007 * t), 0.030 + 0.016 * i, 0.106 - 0.005 * i)
        o.rotation_euler = (rad(-10), 0, sx * rad(-8 - 2.0 * i))
        bpy.ops.object.transform_apply(rotation=True, location=True)
        add(o, "Asa"); pintar(o, pena_prim)
    # coberteiras: 2 camadas curtas perto do ombro
    for i in range(3):
        o = pena("Cob%d%s" % (i, suf), 0.052, 0.012, ponta=0.7)
        sozinho(o)
        o.location = (sx * (0.036 + 0.006 * i), -0.038 + 0.022 * i, 0.126 - 0.003 * i)
        o.rotation_euler = (rad(-8), 0, sx * rad(2))
        bpy.ops.object.transform_apply(rotation=True, location=True)
        add(o, "Asa"); pintar(o, cinza_asa if i == 0 else pena_prim)
asa(1.0, "E")
asa(-1.0, "D")

# ---------------------------------------------------------------- cauda (leque unico + banda branca)
leque = pena("CaudaLeque", 0.082, 0.012, ponta=1.0)
sozinho(leque)
leque.scale = (2.3, 1, 1)   # abre em leque no x local
leque.location = (0, 0.086, 0.108)
leque.rotation_euler = (rad(-8), 0, 0)
bpy.ops.object.transform_apply(rotation=True, scale=True, location=True)
add(leque, "Cauda"); pintar(leque, pena_cauda)
banda = elipsoide("BandaCauda", (0, 0.158, 0.100), (0.024, 0.009, 0.0020), nivel=1)
add(banda, "Cauda"); pintar(partes[-1][0], ponta_cauda)

# ---------------------------------------------------------------- pernas
def pilar(nome, r_base, r_topo_rel, seg=10):
    verts, faces = [], []
    rt = r_base * r_topo_rel
    for k in range(seg):
        a = k / seg * TAU
        verts.append((r_base * math.cos(a), r_base * math.sin(a), 0.0))
    for k in range(seg):
        a = k / seg * TAU
        verts.append((rt * math.cos(a), rt * math.sin(a), 1.0))
    for k in range(seg):
        k2 = (k + 1) % seg
        faces.append((k, k2, seg + k2, seg + k))
    faces.append(tuple(range(seg - 1, -1, -1)))
    faces.append(tuple(range(seg, 2 * seg)))
    o = novo_obj(nome, malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = 1
    return o

def perna(sx, suf):
    coxa = elipsoide("Coxa" + suf, (sx * 0.017, 0.010, 0.092), (0.012, 0.015, 0.020))
    add(coxa, "Coxa" + suf); pintar(coxa, cinza_peito)
    tarso = pilar("Canela" + suf, 0.0031, 0.75, seg=10)
    sozinho(tarso)
    tarso.scale = (1, 1, 0.052)
    tarso.location = (sx * 0.019, 0.011, 0.064)   # de 0.064 a 0.012
    bpy.ops.object.transform_apply(scale=True, location=True)
    add(tarso, "Canela" + suf); pintar(tarso, perna_m)
    tornozelo = Vector((sx * 0.019, 0.011, 0.013))
    for k, ang in enumerate((-19.0, 0.0, 19.0)):
        a = rad(ang)
        d = Vector((math.sin(a), -math.cos(a), -0.42)).normalized()
        o = pilar("Dedo%d%s" % (k, suf), 0.0024, 0.62, seg=8)
        sozinho(o)
        o.location = tornozelo + d * 0.012
        o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        o.scale = (1, 1, 0.021)
        bpy.ops.object.transform_apply(rotation=True, scale=True, location=True)
        add(o, "Pe" + suf); pintar(o, perna_m)
        garra = elipsoide("Garra%d%s" % (k, suf), tuple(tornozelo + d * 0.0245), (0.0013, 0.0022, 0.0013), nivel=1)
        garra.rotation_euler = (rad(-22), 0, -a)
        add(garra, "Pe" + suf); pintar(garra, garra_m)
    d = Vector((0, 0.92, -0.42)).normalized()
    o = pilar("Hallux" + suf, 0.0021, 0.65, seg=8)
    sozinho(o)
    o.location = tornozelo + d * 0.008
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    o.scale = (1, 1, 0.014)
    bpy.ops.object.transform_apply(rotation=True, scale=True, location=True)
    add(o, "Pe" + suf); pintar(o, perna_m)
perna(1.0, "E")
perna(-1.0, "D")

# ---------------------------------------------------------------- join + grupos
for o, _ in partes:
    sozinho(o)
    while o.modifiers:
        bpy.ops.object.modifier_apply(modifier=o.modifiers[0].name)
contagens = [len(o.data.vertices) for o, _ in partes]
sozinho(partes[0][0])
for o, _ in partes:
    o.select_set(True)
bpy.context.view_layer.objects.active = partes[0][0]
bpy.ops.object.join()
passaro = bpy.context.active_object
passaro.name = "Pombo"
total = sum(contagens)
assert len(passaro.data.vertices) == total, "join alterou vertices!"
print("VERTICES:", total)

faixas = {}
idx = 0
for (o, grupo), n in zip(partes, contagens):
    faixas.setdefault(grupo, []).append((idx, idx + n))
    idx += n

# CASCO reparte-se entre Corpo/Pescoco/Cabeca por y
faixas_finais = {}
for grupo, segs in faixas.items():
    if grupo == "CASCO":
        continue
    faixas_finais.setdefault(grupo, []).extend(segs)
casco_segs = faixas.get("CASCO", [])
def reparte_casco(lim1, lim2):
    """faixas do casco por y: <lim1 -> Corpo, [lim1,lim2) -> Pescoco, >=lim2 -> Cabeca"""
    return ("CASCO_SPLIT", casco_segs, lim1, lim2)

for nome_grupo, segs in faixas_finais.items():
    vg = passaro.vertex_groups.new(name=nome_grupo)
    for a, b_ in segs:
        vg.add(list(range(a, b_)), 1.0, 'REPLACE')

# divide o casco de fato (agora com indices conhecidos)
for nome in ("Corpo", "Pescoco", "Cabeca"):
    if passaro.vertex_groups.get(nome) is None:
        passaro.vertex_groups.new(name=nome)
vg_corpo = passaro.vertex_groups["Corpo"]
vg_pescoco = passaro.vertex_groups["Pescoco"]
vg_cabeca = passaro.vertex_groups["Cabeca"]
LIM1, LIM2 = -0.070, -0.122
for a, b_ in casco_segs:
    for vi in range(a, b_):
        y = passaro.data.vertices[vi].co.y
        alvo = vg_corpo if y > LIM1 else (vg_pescoco if y > LIM2 else vg_cabeca)
        alvo.add([vi], 1.0, 'ADD')

# blend suave: faixa de transicao corpo<->pescoco e coxa<->corpo
for a, b_ in casco_segs:
    for vi in range(a, b_):
        y = passaro.data.vertices[vi].co.y
        if -0.058 >= y > -0.082:
            w = min(1.0, max(0.0, (-0.058 - y) / 0.024))
            vg_corpo.add([vi], 1.0 - w * 0.6, 'REPLACE')
            vg_pescoco.add([vi], w * 0.6, 'ADD')
for suf in ("E", "D"):
    vg_coxa = passaro.vertex_groups.get("Coxa" + suf)
    if vg_coxa is None:
        continue
    for a, b_ in faixas_finais["Coxa" + suf]:
        for vi in range(a, b_):
            v = passaro.data.vertices[vi]
            if v.co.z > 0.090:
                vg_coxa.add([vi], 0.35, 'REPLACE')
                vg_corpo.add([vi], 0.65, 'ADD')

# ---------------------------------------------------------------- armature
arm_data = D.armatures.new("PomboRig")
arm = D.objects.new("Armature", arm_data)
scene.collection.objects.link(arm)
sozinho(arm)
bpy.ops.object.mode_set(mode='EDIT')

def osso(nome, head, tail, parent=None):
    b = arm_data.edit_bones.new(nome)
    b.head = head; b.tail = tail; b.roll = 0.0
    if parent:
        b.parent = arm_data.edit_bones[parent]
    return b

osso("Corpo",   (0,  0.085, 0.105), (0, -0.070, 0.095))
osso("Pescoco", (0, -0.070, 0.095), (0, -0.125, 0.160), "Corpo")
osso("Cabeca",  (0, -0.125, 0.160), (0, -0.155, 0.190), "Pescoco")
osso("Cauda",   (0,  0.085, 0.105), (0,  0.168, 0.092), "Corpo")
osso("AsaE",    ( 0.006, -0.030, 0.118), ( 0.040, 0.080, 0.100), "Corpo")
osso("AsaD",    (-0.006, -0.030, 0.118), (-0.040, 0.080, 0.100), "Corpo")
osso("CoxaE",   ( 0.017, 0.010, 0.085), ( 0.019, 0.011, 0.052), "Corpo")
osso("CoxaD",   (-0.017, 0.010, 0.085), (-0.019, 0.011, 0.052), "Corpo")
osso("CanelaE", ( 0.019, 0.011, 0.052), ( 0.019, 0.011, 0.014), "CoxaE")
osso("CanelaD", (-0.019, 0.011, 0.052), (-0.019, 0.011, 0.014), "CoxaD")
osso("PeE",     ( 0.019, 0.011, 0.014), ( 0.019, -0.010, 0.009), "CanelaE")
osso("PeD",     (-0.019, 0.011, 0.014), (-0.019, -0.010, 0.009), "CanelaD")
bpy.ops.object.mode_set(mode='OBJECT')

passaro.parent = arm
mod = passaro.modifiers.new("Skin", 'ARMATURE')
mod.object = arm

# ---------------------------------------------------------------- acoes
def chavear_rot(pbnome, frame, euler):
    pb = arm.pose.bones[pbnome]
    pb.rotation_euler = euler
    pb.keyframe_insert('rotation_euler', frame=frame)

def chavear_loc(pbnome, frame, loc):
    pb = arm.pose.bones[pbnome]
    pb.location = loc
    pb.keyframe_insert('location', frame=frame)

bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones:
    pb.rotation_mode = 'XYZ'

CICLO = 16
def acao_walk():
    a = D.actions.new("Walk")
    arm.animation_data_create()
    arm.animation_data.action = a
    for f in range(1, CICLO + 2):
        t = (f - 1) / CICLO * TAU
        s, c = math.sin(t), math.cos(t)
        chavear_rot("CoxaE", f, (rad(-28) * s, 0, 0))
        chavear_rot("CoxaD", f, (rad(28) * s, 0, 0))
        liftE = max(0.0, math.sin(t + 0.9))
        liftD = max(0.0, math.sin(t + 0.9 + math.pi))
        chavear_rot("CanelaE", f, (rad(46) * liftE, 0, 0))
        chavear_rot("CanelaD", f, (rad(46) * liftD, 0, 0))
        chavear_rot("PeE", f, (rad(-24) * liftE, 0, 0))
        chavear_rot("PeD", f, (rad(-24) * liftD, 0, 0))
        chavear_loc("Corpo", f, (0, 0, 0.0032 * c))
        chavear_rot("Corpo", f, (rad(-2) + rad(1.0) * c, rad(1.8) * s, 0))
        chavear_rot("Pescoco", f, (rad(8) + rad(6) * c, 0, 0))
        chavear_rot("Cabeca", f, (rad(-5) - rad(4) * c, 0, 0))
        chavear_rot("Cauda", f, (rad(8) + rad(1.6) * s, 0, rad(3.5) * s))
        chavear_rot("AsaE", f, (rad(1.0) * s, 0, 0))
        chavear_rot("AsaD", f, (rad(1.0) * s, 0, 0))
    for fc in a.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return a

def acao_idle():
    a = D.actions.new("Idle")
    arm.animation_data_create()
    arm.animation_data.action = a
    FIM = 48
    for f in range(1, FIM + 2):
        t = (f - 1) / FIM * TAU
        peck = max(0.0, math.sin((f - 30) / 6.0 * math.pi)) if 24 <= f <= 36 else 0.0
        chavear_rot("Pescoco", f, (rad(2) * math.sin(2 * t), 0, rad(22) * math.sin(t)))
        chavear_rot("Cabeca", f, (rad(26) * peck, 0, rad(-16) * math.sin(t)))
        chavear_loc("Corpo", f, (0, 0, 0.0016 * math.sin(2 * t)))
        chavear_rot("Corpo", f, (rad(-2) + rad(0.5) * math.sin(2 * t), 0, 0))
        chavear_rot("Cauda", f, (rad(8), 0, rad(2.2) * math.sin(t + 1)))
    return a

walk = acao_walk()
idle = acao_idle()
arm.animation_data.action = walk
try:
    trilha = arm.animation_data.nla_tracks.new()
    trilha.name = "IdleGuard"
    strip = trilha.strips.new("Idle", 1, idle)
except Exception as e:
    print("NLA:", e)

bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- luz/cam/preview
mundo = D.worlds.new("Mundo")
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.38, 0.45, 0.58, 1.0)
mundo.node_tree.nodes["Background"].inputs[1].default_value = 0.38
scene.world = mundo

sol = D.lights.new("Sol", 'SUN')
sol.energy = 1.7
sol.angle = rad(12)
sol_o = D.objects.new("Sol", sol)
scene.collection.objects.link(sol_o)
sol_o.rotation_euler = (rad(48), 0, rad(-38))

cheia = D.lights.new("Cheia", 'AREA')
cheia.energy = 9
cheia.size = 0.8
cheia_o = D.objects.new("Cheia", cheia)
scene.collection.objects.link(cheia_o)
cheia_o.location = (-0.30, -0.35, 0.35)
cheia_o.rotation_euler = (rad(55), 0, rad(-50))

import bmesh
piso_me = D.meshes.new("Piso")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
bm.to_mesh(piso_me); bm.free()
piso = novo_obj("Piso", piso_me)
pmat = D.materials.new("Piso"); pmat.use_nodes = True
pmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.50, 0.47, 1)
pmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
piso.data.materials.append(pmat)

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.render.resolution_x = 900
scene.render.resolution_y = 720
scene.view_settings.view_transform = 'Standard'

cam_data = D.cameras.new("Cam")
cam_data.lens = 85
cam_obj = D.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def render_de(loc, alvo, caminho):
    cam_obj.location = loc
    cam_obj.rotation_euler = (Vector(alvo) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = caminho
    bpy.ops.render.render(write_still=True)

render_de((0.40, -0.52, 0.28), (0, -0.02, 0.10), PREV_A)
render_de((0.05, -0.68, 0.18), (0, 0.0, 0.09), PREV_B)

# ---------------------------------------------------------------- export GLB
bpy.ops.object.select_all(action='DESELECT')
for o in (arm, passaro):
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB,
    export_format='GLB',
    export_apply=True,
    export_animations=True,
    export_skins=True,
    export_yup=True,
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False,
    export_animation_mode='ACTIONS',
    use_selection=True,
)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("PRONTO:", OUT_GLB, os.path.getsize(OUT_GLB), "bytes")
