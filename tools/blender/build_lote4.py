# Lote 4 — macaco e caranguejo (Blender 4.5 headless).
# Padrao dos lotes anteriores: frente = -Y, origem no chao, clips
# Walk + Idle + Lie (crouch) — o jogo troca o clip pela pose
# (run->Walk, idle->Idle, crouch->Lie; ver world_animal.gd).
#
# Macaco: meio-ereto, cauda enrolada. Rig de 10 ossos:
#   Corpo -> Pescoco -> Cabeca, Cauda -> CaudaPonta, BrazoE/D, PernaE/D.
# Caranguejo: casco em cupula, pinças e 3 patas por lado. Rig de 9 ossos:
#   Corpo, PincaE/D, Pata{E,D}{1,2,3}.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
ANIMAIS = str(K.REPO / "assets" / "characters" / "animais")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(ANIMAIS, exist_ok=True)


def coluna_entre(nome, A, B, r_base, r_topo_rel, seg=10):
    """Pilar com a base em A e o topo em B (eixo qualquer).
    Atencao: transform_apply SEMPRE com os tres argumentos explicitos
    (os defaults True do bpy aplicam tudo que vc nao pedir)."""
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


# ============================================================================
# MACACO — meio-ereto (sagui), pelagem castanha, focinho e peito claros,
# cauda longa enrolada por cima das costas.
# Native: ~0,85 m de nariz a cauda x ~1,04 m de altura.
# ============================================================================
def build_macaco() -> None:
    K.reset_scene()
    partes = []
    def add(o, grupo):
        partes.append((o, grupo))

    M = {
        "pelo":   K.material("macaco_pelo",   (0.431, 0.322, 0.212), 0.85),
        "rosto":  K.material("macaco_rosto",  (0.788, 0.608, 0.471), 0.75),
        "peito":  K.material("macaco_peito",  (0.830, 0.680, 0.520), 0.75),
        "escuro": K.material("macaco_escuro", (0.141, 0.106, 0.102), 0.60),
        "olho":   K.material("macaco_olho",   (0.063, 0.075, 0.110), 0.20),
    }

    # ---------------------------------------------------------------- corpo
    corpo = K.loft("MacacoCorpo", [
        ( 0.220, 0.420, 0.130, 0.140),
        ( 0.100, 0.500, 0.175, 0.185),
        (-0.040, 0.600, 0.195, 0.200),
        (-0.140, 0.700, 0.175, 0.190),
        (-0.200, 0.780, 0.130, 0.140),
    ], seg=14)
    K.pintar(corpo, M["pelo"]); add(corpo, "Corpo")
    # peito claro
    peito = K.elipsoide("MacacoPeito", (-0.02, -0.145, 0.560), (0.105, 0.065, 0.140), nivel=1)
    K.pintar(peito, M["peito"]); add(peito, "Corpo")
    # barriga
    bari = K.elipsoide("MacacoBarriga", (0, 0.020, 0.420), (0.150, 0.100, 0.130), nivel=1)
    K.pintar(bari, M["peito"]); add(bari, "Corpo")

    # ---------------------------------------------------------------- pescoco
    pesc = K.loft("MacacoPescoco", [
        (-0.180, 0.820, 0.095, 0.095),
        (-0.230, 0.880, 0.085, 0.085),
    ], seg=10)
    K.pintar(pesc, M["pelo"]); add(pesc, "Pescoco")

    # ---------------------------------------------------------------- cabeca
    hc, hr = (0, -0.270, 0.930), (0.115, 0.125, 0.110)
    add(K.elipsoide("MacacoCabeca", hc, hr), "Cabeca")
    partes[-1][0].data.materials.clear()
    partes[-1][0].data.materials.append(M["pelo"])
    # rosto (mancha clara frontal)
    rosto = K.elipsoide("MacacoRosto", (0, -0.345, 0.910), (0.085, 0.060, 0.090), nivel=1)
    K.pintar(rosto, M["rosto"]); add(rosto, "Cabeca")
    # focinho
    foc = K.elipsoide("MacacoFocinho", (0, -0.395, 0.875), (0.055, 0.050, 0.050), nivel=1)
    K.pintar(foc, M["rosto"]); add(foc, "Cabeca")
    # narinas
    for sx in (1.0, -1.0):
        n = K.elipsoide("MacacoNarina%d" % int(sx), (sx * 0.020, -0.435, 0.885), (0.007, 0.006, 0.008), nivel=1)
        K.pintar(n, M["escuro"]); add(n, "Cabeca")
    # olhos
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        o = K.elipsoide("MacacoOlho" + suf, (sx * 0.055, -0.368, 0.955), (0.015, 0.012, 0.016), nivel=1)
        K.pintar(o, M["olho"]); add(o, "Cabeca")
    # orelhas arredondadas
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        oe = K.elipsoide("MacacoOrelha" + suf, (sx * 0.115, -0.245, 0.975), (0.022, 0.045, 0.055), nivel=1)
        oe.rotation_euler = (0, sx * rad(12), 0)
        K.sozinho(oe)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(oe, M["pelo"]); add(oe, "Cabeca")
        oi = K.elipsoide("MacacoOrelhaInner" + suf, (sx * 0.135, -0.245, 0.975), (0.010, 0.028, 0.038), nivel=1)
        oi.rotation_euler = (0, sx * rad(12), 0)
        K.sozinho(oi)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(oi, M["rosto"]); add(oi, "Cabeca")

    # ---------------------------------------------------------------- cauda (2 trechos)
    ca1 = K.loft("MacacoCauda", [
        ( 0.240, 0.440, 0.028, 0.028),
        ( 0.350, 0.510, 0.024, 0.024),
    ], seg=8)
    K.pintar(ca1, M["pelo"]); add(ca1, "Cauda")
    ca2 = K.loft("MacacoCaudaPonta", [
        ( 0.350, 0.510, 0.022, 0.022),
        ( 0.420, 0.630, 0.018, 0.018),
        ( 0.400, 0.750, 0.014, 0.014),
        ( 0.330, 0.800, 0.012, 0.012),
    ], seg=8)
    K.pintar(ca2, M["pelo"]); add(ca2, "CaudaPonta")
    tufo = K.elipsoide("MacacoCaudaTufo", (0.0, 0.315, 0.820), (0.016, 0.014, 0.016), nivel=1)
    K.pintar(tufo, M["pelo"]); add(tufo, "CaudaPonta")

    # ---------------------------------------------------------------- bracos
    ombros = {"E": (0.135, -0.130, 0.780), "D": (-0.135, -0.130, 0.780)}
    punhos = {"E": (0.160, -0.210, 0.400), "D": (-0.160, -0.210, 0.400)}
    for suf, sx in (("E", 1.0), ("D", -1.0)):
        bra = coluna_entre("MacacoBraco" + suf, ombros[suf], punhos[suf], 0.045, 0.76, seg=10)
        K.pintar(bra, M["pelo"]); add(bra, "Braco" + suf)
        mao = K.elipsoide("MacacoMao" + suf, (sx * 0.162, -0.225, 0.355), (0.038, 0.048, 0.052), nivel=1)
        K.pintar(mao, M["rosto"]); add(mao, "Braco" + suf)

    # ---------------------------------------------------------------- pernas
    quadris = {"E": (0.095, 0.100, 0.380), "D": (-0.095, 0.100, 0.380)}
    tornozelos = {"E": (0.105, 0.075, 0.050), "D": (-0.105, 0.075, 0.050)}
    for suf, sx in (("E", 1.0), ("D", -1.0)):
        per = coluna_entre("MacacoPerna" + suf, quadris[suf], tornozelos[suf], 0.050, 0.85, seg=10)
        K.pintar(per, M["pelo"]); add(per, "Perna" + suf)
        pe = K.elipsoide("MacacoPe" + suf, (sx * 0.108, 0.030, 0.040), (0.048, 0.075, 0.040), nivel=1)
        K.pintar(pe, M["escuro"]); add(pe, "Perna" + suf)

    # ---------------------------------------------------------------- join + rig
    an_obj = K.join_parts(partes)
    an_obj.name = "Macaco"
    bones = [
        ("Corpo",      (0,  0.200, 0.400), (0, -0.200, 0.720), None),
        ("Pescoco",    (0, -0.160, 0.800), (0, -0.250, 0.900), "Corpo"),
        ("Cabeca",     (0, -0.250, 0.900), (0, -0.380, 0.950), "Pescoco"),
        ("Cauda",      (0,  0.240, 0.440), (0,  0.350, 0.510), "Corpo"),
        ("CaudaPonta", (0,  0.350, 0.510), (0,  0.360, 0.700), "Cauda"),
        ("BracoE",     ( 0.135, -0.130, 0.780), ( 0.160, -0.210, 0.400), "Corpo"),
        ("BracoD",     (-0.135, -0.130, 0.780), (-0.160, -0.210, 0.400), "Corpo"),
        ("PernaE",     ( 0.095,  0.100, 0.380), ( 0.105,  0.075, 0.075), "Corpo"),
        ("PernaD",     (-0.095,  0.100, 0.380), (-0.105,  0.075, 0.075), "Corpo"),
    ]
    arm = K.armature("macaco", bones)
    K.skin(arm, an_obj)

    # ---------------------------------------------------------------- Walk
    a = K.new_action(arm, "Walk")
    ciclo = 16
    for f in range(1, ciclo + 2):
        t = (f - 1) / ciclo * K.TAU
        sE, sD = math.sin(t), -math.sin(t)
        K.key_rot(arm, "PernaE", f, (rad(18) * sE, 0, 0))
        K.key_rot(arm, "PernaD", f, (rad(18) * sD, 0, 0))
        # membros dianteiros na contra-fase da perna do mesmo lado
        K.key_rot(arm, "BracoE", f, (rad(14) * -sE, 0, rad(4) * math.cos(t)))
        K.key_rot(arm, "BracoD", f, (rad(14) * -sD, 0, -rad(4) * math.cos(t)))
        K.key_loc(arm, "Corpo", f, (0, 0, 0.008 * math.cos(2 * t)))
        K.key_rot(arm, "Corpo", f, (0, 0, rad(0.8) * math.sin(2 * t)))
        K.key_rot(arm, "Pescoco", f, (rad(3.0) * math.cos(2 * t), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(-2.5) * math.cos(2 * t), 0, 0))
        K.key_rot(arm, "Cauda", f, (rad(6.0) * math.sin(t), 0, rad(5.0) * math.sin(t + 0.5)))
        K.key_rot(arm, "CaudaPonta", f, (rad(7.0) * math.sin(t + 0.4), 0, rad(6.0) * math.sin(t + 0.9)))
    K.linearize(a)

    # ---------------------------------------------------------------- Idle
    a = K.new_action(arm, "Idle")
    C = 16
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        K.key_loc(arm, "Corpo", f, (0, 0, 0.004 * math.sin(t)))
        K.key_rot(arm, "Corpo", f, (rad(1.2) * math.sin(t + 1.0), 0, 0))
        K.key_rot(arm, "Pescoco", f, (rad(2.0) * math.sin(t + 0.4), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(-1.5) * math.sin(t + 0.7), 0, rad(4.0) * math.sin(t + 2.0)))
        K.key_rot(arm, "BracoE", f, (rad(2.0) * math.sin(t + 0.3), 0, 0))
        K.key_rot(arm, "BracoD", f, (rad(2.0) * math.sin(t + 0.9), 0, 0))
        K.key_rot(arm, "Cauda", f, (0, 0, rad(5.0) * math.sin(t)))
        K.key_rot(arm, "CaudaPonta", f, (0, 0, rad(6.0) * math.sin(t + 0.8)))
    K.linearize(a)

    # ---------------------------------------------------------------- Lie (crouch: agachado, cauda enrolada, espiando)
    a = K.new_action(arm, "Lie")
    C = 16
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        K.key_loc(arm, "Corpo", f, (0, 0, -0.120))
        K.key_rot(arm, "Corpo", f, (rad(16), 0, 0))
        K.key_rot(arm, "PernaE", f, (rad(30), 0, rad(7)))
        K.key_rot(arm, "PernaD", f, (rad(30), 0, -rad(7)))
        K.key_rot(arm, "BracoE", f, (rad(52), 0, -rad(5) + rad(2) * math.sin(t)))
        K.key_rot(arm, "BracoD", f, (rad(52), 0, rad(5) + rad(2) * math.sin(t + 1.0)))
        K.key_rot(arm, "Pescoco", f, (rad(-28) + rad(2.5) * math.sin(t), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(14), 0, rad(5) * math.sin(t + 1.5)))
        K.key_rot(arm, "Cauda", f, (rad(-34) + rad(3) * math.sin(t), 0, 0))
        K.key_rot(arm, "CaudaPonta", f, (rad(-30) + rad(4) * math.sin(t + 0.7), 0, rad(3) * math.sin(t)))
    K.linearize(a)

    arm.animation_data.action = D.actions["Walk"]
    K.clear_pose(arm)

    glb = os.path.join(ANIMAIS, "macaco.glb")
    K.export_glb(glb, [arm, an_obj])
    print("ESPECIE: macaco OK")


# ============================================================================
# CARANGUEJO — casco em cupula vermelho-laranja, olhos em hastes, pinças
# grandes na frente e 3 patas por lado. Native: ~0,45 m x ~0,34 m
# (largura ~0,81 m incluindo as pinças).
# ============================================================================
def build_caranguejo() -> None:
    K.reset_scene()
    partes = []
    def add(o, grupo):
        partes.append((o, grupo))

    M = {
        "casco":   K.material("caranguejo_casco",  (0.851, 0.416, 0.247), 0.55),
        "pinca":   K.material("caranguejo_pinca",  (0.878, 0.471, 0.290), 0.50),
        "barriga": K.material("caranguejo_barriga",(0.900, 0.550, 0.380), 0.60),
        "escuro":  K.material("caranguejo_escuro", (0.141, 0.106, 0.102), 0.45),
    }

    # ---------------------------------------------------------------- casco
    casco = K.elipsoide("CrabCasco", (0, 0, 0.145), (0.290, 0.200, 0.125))
    K.pintar(casco, M["casco"]); add(casco, "Corpo")
    barriga = K.elipsoide("CrabBarriga", (0, 0.020, 0.055), (0.210, 0.170, 0.050), nivel=1)
    K.pintar(barriga, M["barriga"]); add(barriga, "Corpo")
    # bochechas
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        bo = K.elipsoide("CrabBochecha" + suf, (sx * 0.190, -0.160, 0.100), (0.070, 0.065, 0.050), nivel=1)
        K.pintar(bo, M["casco"]); add(bo, "Corpo")
    # olhos em hastes
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        haste = coluna_entre("CrabOlhoHaste" + suf, (sx * 0.065, -0.160, 0.200),
                             (sx * 0.068, -0.170, 0.262), 0.011, 0.8, seg=8)
        K.pintar(haste, M["casco"]); add(haste, "Corpo")
        olho = K.elipsoide("CrabOlho" + suf, (sx * 0.070, -0.175, 0.275), (0.020, 0.020, 0.020), nivel=1)
        K.pintar(olho, M["escuro"]); add(olho, "Corpo")

    # ---------------------------------------------------------------- pincas
    ombro_p = {"E": (0.200, -0.150, 0.120), "D": (-0.200, -0.150, 0.120)}
    carpo_p = {"E": (0.300, -0.220, 0.095), "D": (-0.300, -0.220, 0.095)}
    for suf, sx in (("E", 1.0), ("D", -1.0)):
        braco = coluna_entre("CrabPincaBraco" + suf, ombro_p[suf], carpo_p[suf], 0.032, 1.35, seg=10)
        K.pintar(braco, M["pinca"]); add(braco, "Pinca" + suf)
        carpo = K.elipsoide("CrabPincaCarpo" + suf, (sx * 0.315, -0.230, 0.095),
                            (0.052, 0.048, 0.046), nivel=1)
        K.pintar(carpo, M["pinca"]); add(carpo, "Pinca" + suf)
        # dedos da pinça (boca entreaberta)
        ded1 = K.elipsoide("CrabPincaDedo1" + suf, (sx * 0.365, -0.275, 0.075),
                           (0.048, 0.040, 0.022), nivel=1)
        ded1.rotation_euler = (0, 0, sx * rad(18))
        K.sozinho(ded1)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(ded1, M["pinca"]); add(ded1, "Pinca" + suf)
        ded2 = K.elipsoide("CrabPincaDedo2" + suf, (sx * 0.360, -0.275, 0.125),
                           (0.045, 0.037, 0.020), nivel=1)
        ded2.rotation_euler = (0, 0, sx * rad(-22))
        K.sozinho(ded2)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(ded2, M["pinca"]); add(ded2, "Pinca" + suf)

    # ---------------------------------------------------------------- patas (3 por lado, 2 segmentos)
    patas = {
        "1": ((0.280, -0.060, 0.090), (0.330, -0.040, 0.115), (0.360, -0.090, 0.012)),
        "2": ((0.280,  0.060, 0.090), (0.335,  0.080, 0.115), (0.370,  0.030, 0.012)),
        "3": ((0.170,  0.180, 0.090), (0.220,  0.200, 0.110), (0.260,  0.150, 0.012)),
    }
    for lado in ("E", "D"):
        sgn = 1.0 if lado == "E" else -1.0
        for rank, (base, joelho, ponta) in patas.items():
            suf = lado + rank
            base2 = (sgn * base[0], base[1], base[2])
            joelho2 = (sgn * joelho[0], joelho[1], joelho[2])
            ponta2 = (sgn * ponta[0], ponta[1], ponta[2])
            sup = coluna_entre("CrabPataSup" + suf, base2, joelho2, 0.016, 0.85, seg=8)
            K.pintar(sup, M["pinca"]); add(sup, "Pata" + suf)
            inf = coluna_entre("CrabPataInf" + suf, joelho2, ponta2, 0.012, 0.8, seg=8)
            K.pintar(inf, M["pinca"]); add(inf, "Pata" + suf)

    # ---------------------------------------------------------------- join + rig
    an_obj = K.join_parts(partes)
    an_obj.name = "Caranguejo"
    bones = [
        ("Corpo",   (0,  0.180, 0.150), (0, -0.180, 0.150), None),
        ("PincaE",  ( 0.200, -0.150, 0.120), ( 0.315, -0.230, 0.095), "Corpo"),
        ("PincaD",  (-0.200, -0.150, 0.120), (-0.315, -0.230, 0.095), "Corpo"),
        ("PataE1",  ( 0.280, -0.060, 0.090), ( 0.360, -0.090, 0.012), "Corpo"),
        ("PataE2",  ( 0.280,  0.060, 0.090), ( 0.370,  0.030, 0.012), "Corpo"),
        ("PataE3",  ( 0.170,  0.180, 0.090), ( 0.260,  0.150, 0.012), "Corpo"),
        ("PataD1",  (-0.280, -0.060, 0.090), (-0.360, -0.090, 0.012), "Corpo"),
        ("PataD2",  (-0.280,  0.060, 0.090), (-0.370,  0.030, 0.012), "Corpo"),
        ("PataD3",  (-0.170,  0.180, 0.090), (-0.260,  0.150, 0.012), "Corpo"),
    ]
    arm = K.armature("caranguejo", bones)
    K.skin(arm, an_obj)

    # ---------------------------------------------------------------- Walk (garra de tesoura)
    a = K.new_action(arm, "Walk")
    ciclo = 16
    fases = {"1": 0.0, "2": 0.55, "3": 1.10}
    for f in range(1, ciclo + 2):
        t = (f - 1) / ciclo * K.TAU
        for lado, sgn in (("E", 0.0), ("D", math.pi)):
            for rank in ("1", "2", "3"):
                ph = sgn + fases[rank]
                K.key_rot(arm, "Pata" + lado + rank, f, (rad(11) * math.sin(t + ph), 0, 0))
        K.key_loc(arm, "Corpo", f, (0, 0, 0.003 * math.cos(2 * t)))
        K.key_rot(arm, "Corpo", f, (0, 0, rad(2.2) * math.sin(2 * t)))
        # pincas erguidas; a esquerda faz a saudação
        K.key_rot(arm, "PincaE", f, (rad(-14), 0, rad(12) * math.sin(2 * t)))
        K.key_rot(arm, "PincaD", f, (rad(-14), 0, rad(5) * math.sin(2 * t + 1.0)))
    K.linearize(a)

    # ---------------------------------------------------------------- Idle
    a = K.new_action(arm, "Idle")
    C = 12
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        K.key_loc(arm, "Corpo", f, (0, 0, 0.002 * math.sin(t)))
        K.key_rot(arm, "Corpo", f, (0, 0, rad(1.2) * math.sin(t)))
        K.key_rot(arm, "PincaE", f, (rad(-14), 0, rad(10) * math.sin(t)))
        K.key_rot(arm, "PincaD", f, (rad(-14), 0, rad(4) * math.sin(t + 1.2)))
    K.linearize(a)

    # ---------------------------------------------------------------- Lie (crouch: corpo abaixado, patas dobradas)
    a = K.new_action(arm, "Lie")
    C = 16
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        K.key_loc(arm, "Corpo", f, (0, 0, -0.055))
        K.key_rot(arm, "Corpo", f, (rad(2) + rad(1.5) * math.sin(t), 0, 0))
        for lado, sgn in (("E", 0.0), ("D", math.pi)):
            for rank, drop in (("1", 34), ("2", 30), ("3", 26)):
                K.key_rot(arm, "Pata" + lado + rank, f,
                          (rad(-drop) + rad(3) * math.sin(t + sgn + fases[rank]), 0, 0))
        K.key_rot(arm, "PincaE", f, (rad(-26), 0, rad(6) * math.sin(t)))
        K.key_rot(arm, "PincaD", f, (rad(-26), 0, rad(6) * math.sin(t + 1.0)))
    K.linearize(a)

    arm.animation_data.action = D.actions["Walk"]
    K.clear_pose(arm)

    glb = os.path.join(ANIMAIS, "caranguejo.glb")
    K.export_glb(glb, [arm, an_obj])
    print("ESPECIE: caranguejo OK")


build_macaco()
build_caranguejo()

# ---------------------------------------------------------------- previews
for nome, h, lente, dist in (("macaco", 1.05, 50, 2.70), ("caranguejo", 0.32, 50, 1.25)):
    K.reset_scene()
    cam = K.setup_preview()
    cam.data.lens = lente
    bpy.ops.import_scene.gltf(filepath=os.path.join(ANIMAIS, nome + ".glb"))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    if arm.animation_data:
        arm.animation_data.action = None
        for t in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(t)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    K.render_de(cam, (dist * 0.72, -dist, h * 0.62), (0, 0.0, h * 0.52),
                os.path.join(K.OUT_DIR, "prev_%s.png" % nome))
    K.render_de(cam, (dist * 0.12, -dist, h * 0.55), (0, 0.15, h * 0.50),
                os.path.join(K.OUT_DIR, "prev_%s_b.png" % nome))
    print("PREVIEW:", nome)
print("LOTE 4 PRONTO")
