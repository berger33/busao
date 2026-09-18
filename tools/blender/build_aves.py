# Aves v2 — passaro, gaivota e urubu (Blender 4.5 headless).
# Correcoes do v1: tarsos apontando para baixo (pernas visiveis), asas
# lofteras 3D (com espessura e pontas escuras por face) e cauda com espessura.
# Padrao do pombo (lote 1): frente = -Y, origem no chao, clips Walk + Fly.
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
ANIMAIS = str(K.REPO / "assets" / "characters" / "animais")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(ANIMAIS, exist_ok=True)


def build(especie: dict) -> None:
    K.reset_scene()
    partes = []
    def add(o, grupo):
        partes.append((o, grupo))

    # Levanta corpo/cabeca/asas/cauda/rig sobre o chao (as pernas ficam fixas
    # ao chao); assim a barriga sobe ate a coxa e as pernas ficam visiveis.
    lift = float(especie.get("levantar", 0.0))
    def L(z): return z + lift
    def lv3(p): return (p[0], p[1], L(p[2]))

    M = {k: K.material(especie["id"] + "_" + k, *v) for k, v in especie["mats"].items()}

    # ---------------------------------------------------------------- casco
    secoes = [(y, L(zc), w, h) for (y, zc, w, h) in especie["secoes"]]
    corpo = K.loft(especie["id"] + "Casco", secoes, seg=especie.get("seg", 14))
    K.pintar(corpo, M["corpo"])
    add(corpo, "Corpo")

    # ---------------------------------------------------------------- cabeca
    head_c, head_r = lv3(especie["cabeca"][0]), especie["cabeca"][1]
    add(K.elipsoide(especie["id"] + "Cabeca", head_c, head_r), "Cabeca")
    partes[-1][0].data.materials.clear()
    partes[-1][0].data.materials.append(M["cabeca"])
    bico = especie["bico"]
    cone = K.cone_part(especie["id"] + "Bico", bico["r1"], bico["r2"], bico["prof"], 10)
    K.sozinho(cone)
    cone.location = lv3(bico["pos"])
    cone.rotation_euler = (rad(bico.get("rx", 96)), 0, 0)
    bpy.ops.object.transform_apply(rotation=True, location=True)
    K.pintar(cone, M["bico"]); add(cone, "Cabeca")
    if bico["tipo"] == "gancho":
        g = K.cone_part(especie["id"] + "BicoGancho", bico["r1"] * 0.55, 0.0008, bico["prof"] * 0.42, 8)
        K.sozinho(g)
        g.location = lv3(bico["gancho"])
        g.rotation_euler = (rad(bico.get("grx", 150)), 0, 0)
        bpy.ops.object.transform_apply(rotation=True, location=True)
        K.pintar(g, M["bico"]); add(g, "Cabeca")
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        ec = (head_c[0] + sx * especie["olho_dx"], head_c[1] - especie["olho_dy"], head_c[2] + especie["olho_dz"])
        o = K.elipsoide(especie["id"] + "Olho" + suf, ec, (especie["olho_r"],) * 3, nivel=1)
        K.pintar(o, M["olho"]); add(o, "Cabeca")

    # ---------------------------------------------------------------- asas 3D
    wing = especie["asa"]
    wl, ww = wing["L"], wing["W"]
    wing_secs = [
        (0.000 * wl, 0.000 * ww, ww * 0.30, ww * 0.13),
        (0.180 * wl, -0.020 * ww, ww * 0.38, ww * 0.15),
        (0.450 * wl, -0.050 * ww, ww * 0.30, ww * 0.11),
        (0.750 * wl, -0.090 * ww, ww * 0.17, ww * 0.06),
        (1.000 * wl, -0.120 * ww, ww * 0.05, ww * 0.02),
    ]
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        asa = K.loft(especie["id"] + "Asa" + suf, wing_secs, seg=10, tampas=True)
        K.pintar(asa, M["asa"]); K.pintar(asa, M["primarias"])
        # pontas escuras: faces atras de 72% do comprimento
        for poly in asa.data.polygons:
            ym = sum(asa.data.vertices[v].co.y for v in poly.vertices) / len(poly.vertices)
            if ym > 0.72 * wl:
                poly.material_index = 1
        K.sozinho(asa)
        asa.location = (sx * wing["x_sh"], wing["y_sh"], L(wing["z_sh"]))
        asa.rotation_euler = (rad(wing["rx"]), 0, sx * rad(wing.get("rz", 3)))
        bpy.ops.object.transform_apply(rotation=True, location=True)
        add(asa, "Asa" + suf)

    # ---------------------------------------------------------------- cauda 3D
    tail = especie["cauda"]
    TL, TH = tail["L"], tail["W"]
    tail_secs = [
        (0.0, 0.0, TH * 0.55, TH * 0.10),
        (0.50 * TL, 0.0, TH * 0.50, TH * 0.12),
        (1.00 * TL, 0.0, TH * 0.24, TH * 0.07),
    ]
    leque = K.loft(especie["id"] + "CaudaLeque", tail_secs, seg=10, tampas=True)
    K.pintar(leque, M["cauda"])
    if "banda" in tail:
        K.pintar(leque, M["cauda_banda"])
        for poly in leque.data.polygons:
            ym = sum(leque.data.vertices[v].co.y for v in poly.vertices) / len(poly.vertices)
            if 0.35 * TL < ym < 0.75 * TL:
                poly.material_index = 1
    K.sozinho(leque)
    leque.location = (tail["pos"][0], tail["pos"][1], L(tail["pos"][2]))
    leque.rotation_euler = (rad(tail.get("rx", -8)), 0, 0)
    bpy.ops.object.transform_apply(scale=True, location=True, rotation=True)
    add(leque, "Cauda")

    # ---------------------------------------------------------------- pernas
    # Tudo ancorado ao chao: z_peso (pe) -> z_canela_top (topo do tarso,
    # embutido na barriga). A coxa (na barriga) sobe com o corpo via L().
    leg = especie["perna"]
    z_ct = leg["z_canela_top"]
    z_pe = leg["z_peso"]
    h_tar = z_ct - z_pe
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        coxa = K.elipsoide(especie["id"] + "Coxa" + suf,
                           (sx * leg["x"], leg["y"], L(leg["z_coxa"])),
                           (leg["r_coxa"], leg["r_coxa"] * 1.3, leg["r_coxa"] * 1.9))
        K.pintar(coxa, M["corpo"]); add(coxa, "Coxa" + suf)
        # tarso: mais grosso no topo (uniao ao corpo), fino no pescozelo
        tarso = K.pilar(especie["id"] + "Canela" + suf, leg["r_tarso"], 1.35, seg=10)
        K.sozinho(tarso)
        tarso.scale = (1, 1, h_tar)
        tarso.location = (sx * leg["x"], leg["y"], z_pe)
        bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(tarso, M["perna"]); add(tarso, "Canela" + suf)
        tornozelo = K.Vector((sx * leg["x"], leg["y"], z_pe))
        for k, ang in enumerate((-19.0, 0.0, 19.0)):
            a = rad(ang)
            d = K.Vector((math.sin(a), -math.cos(a), -0.42)).normalized()
            dedo = K.pilar(especie["id"] + "Dedo%d%s" % (k, suf), leg["r_dedo"], 0.6, seg=8)
            K.sozinho(dedo)
            dedo.location = tornozelo + d * leg["d_dedo"]
            dedo.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
            dedo.scale = (1, 1, leg["h_dedo"])
            bpy.ops.object.transform_apply(rotation=True, scale=True, location=True)
            K.pintar(dedo, M["perna"]); add(dedo, "Pe" + suf)
        d = K.Vector((0, 0.92, -0.42)).normalized()
        h = K.pilar(especie["id"] + "Hallux" + suf, leg["r_dedo"] * 0.85, 0.65, seg=8)
        K.sozinho(h)
        h.location = tornozelo + d * leg["d_dedo"] * 0.62
        h.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        h.scale = (1, 1, leg["h_dedo"] * 0.66)
        bpy.ops.object.transform_apply(rotation=True, scale=True, location=True)
        K.pintar(h, M["perna"]); add(h, "Pe" + suf)

    # ---------------------------------------------------------------- join + rig
    ave = K.join_parts(partes)
    ave.name = especie["id"].capitalize()
    # ossos do corpo sobem com o corpo; ossos das pernas ficam ancorados ao
    # chao (gerados a partir dos parametros da perna, sem divergir da malha)
    bones = [(n, (a[0], a[1], L(a[2])), (b[0], b[1], L(b[2])), p)
             for (n, a, b, p) in especie["bones"]
             if n not in ("CoxaE", "CoxaD", "CanelaE", "CanelaD", "PeE", "PeD")]
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        lx, ly = sx * leg["x"], leg["y"]
        z_coxa_top = L(leg["z_coxa"]) + 0.004
        bones.append(("Coxa" + suf,  (lx, ly, z_coxa_top), (lx, ly, z_ct), "Corpo"))
        bones.append(("Canela" + suf, (lx, ly, z_ct),      (lx, ly, z_pe), "Coxa" + suf))
        bones.append(("Pe" + suf,     (lx, ly, z_pe),      (lx, ly - 0.013, z_pe - 0.004), "Canela" + suf))
    arm = K.armature(especie["id"], bones)
    K.skin(arm, ave)

    # ---------------------------------------------------------------- clips
    S = especie["escala_anim"]
    a = K.new_action(arm, "Walk")
    C = especie.get("ciclo_walk", 16)
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        s, c = math.sin(t), math.cos(t)
        K.key_rot(arm, "CoxaE", f, (rad(-26) * s, 0, 0))
        K.key_rot(arm, "CoxaD", f, (rad(26) * s, 0, 0))
        liftE = max(0.0, math.sin(t + 0.9))
        liftD = max(0.0, math.sin(t + 0.9 + math.pi))
        K.key_rot(arm, "CanelaE", f, (rad(44) * liftE, 0, 0))
        K.key_rot(arm, "CanelaD", f, (rad(44) * liftD, 0, 0))
        K.key_rot(arm, "PeE", f, (rad(-22) * liftE, 0, 0))
        K.key_rot(arm, "PeD", f, (rad(-22) * liftD, 0, 0))
        K.key_loc(arm, "Corpo", f, (0, 0, 0.0028 * S * c))
        K.key_rot(arm, "Corpo", f, (rad(-2) + rad(1.0) * c, rad(1.8) * s, 0))
        K.key_rot(arm, "Pescoco", f, (rad(8) + rad(6) * c, 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(-5) - rad(4) * c, 0, 0))
        K.key_rot(arm, "Cauda", f, (rad(8) + rad(1.6) * s, 0, rad(3.5) * s))
        K.key_rot(arm, "AsaE", f, (rad(1.0) * s, 0, 0))
        K.key_rot(arm, "AsaD", f, (rad(1.0) * s, 0, 0))
    K.linearize(a)

    fly = especie["fly"]
    a = K.new_action(arm, "Fly")
    C = fly.get("ciclo", 14)
    amp = rad(fly["amp"])
    mid = rad(fly.get("mid", 12))
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        s = math.sin(t)
        K.key_rot(arm, "AsaE", f, (mid + amp * s, 0, rad(3) * s))
        K.key_rot(arm, "AsaD", f, (mid + amp * s, 0, rad(3) * s))
        K.key_rot(arm, "CoxaE", f, (rad(fly["coxa"]), 0, 0))
        K.key_rot(arm, "CoxaD", f, (rad(fly["coxa"]), 0, 0))
        K.key_rot(arm, "CanelaE", f, (rad(fly["canela"]), 0, 0))
        K.key_rot(arm, "CanelaD", f, (rad(fly["canela"]), 0, 0))
        K.key_rot(arm, "PeE", f, (rad(fly["pe"]), 0, 0))
        K.key_rot(arm, "PeD", f, (rad(fly["pe"]), 0, 0))
        K.key_loc(arm, "Corpo", f, (0, 0, 0.003 * S * s))
        K.key_rot(arm, "Corpo", f, (rad(fly.get("corpo_x", -8)), 0, 0))
        K.key_rot(arm, "Pescoco", f, (rad(fly.get("pescoco_x", -6)), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(fly.get("cabeca_x", 4)), 0, 0))
        K.key_rot(arm, "Cauda", f, (rad(fly.get("cauda_x", 15)), 0, 0))
    K.linearize(a)

    arm.animation_data.action = D.actions["Walk"]
    K.clear_pose(arm)

    glb = os.path.join(ANIMAIS, especie["id"] + ".glb")
    K.export_glb(glb, [arm, ave])
    print("ESPECIE:", especie["id"], "OK")


# ============================================================================
# passaro — passarinho de rua (pardal): rechonchudo, bico conico, cauda curta
# (corpo baixado 0.020 para a barriga encostar nas coxas apos o subsurf)
# ============================================================================
passaro = {
    "id": "passaro",
    "mats": {
        "corpo":     ((0.330, 0.272, 0.190), 0.72),
        "cabeca":    ((0.360, 0.300, 0.210), 0.70),
        "asa":       ((0.245, 0.196, 0.135), 0.74),
        "primarias": ((0.160, 0.128, 0.092), 0.72),
        "cauda":     ((0.225, 0.182, 0.125), 0.74),
        "bico":      ((0.155, 0.135, 0.105), 0.50),
        "olho":      ((0.020, 0.016, 0.012), 0.18),
        "perna":     ((0.420, 0.300, 0.200), 0.55),
    },
    "secoes": [
        ( 0.072, 0.058, 0.012, 0.010),
        ( 0.048, 0.063, 0.021, 0.020),
        ( 0.020, 0.059, 0.026, 0.025),
        (-0.008, 0.051, 0.027, 0.026),
        (-0.034, 0.041, 0.023, 0.025),
        (-0.056, 0.043, 0.016, 0.019),
        (-0.072, 0.055, 0.012, 0.014),
        (-0.080, 0.071, 0.010, 0.011),
        (-0.086, 0.086, 0.008, 0.009),
    ],
    "cabeca": ((0, -0.090, 0.098), (0.014, 0.0155, 0.0145)),
    "bico": {"tipo": "cone", "r1": 0.0044, "r2": 0.0013, "prof": 0.017, "pos": (0, -0.105, 0.094), "rx": 95},
    "olho_dx": 0.0115, "olho_dy": 0.003, "olho_dz": 0.0045, "olho_r": 0.0026,
    "asa": {"L": 0.10, "W": 0.036, "x_sh": 0.017, "y_sh": -0.028, "z_sh": 0.060, "rx": -14, "rz": 3},
    "cauda": {"L": 0.055, "W": 0.020, "pos": (0, 0.056, 0.050), "rx": -8},
    "perna": {
        "x": 0.011, "y": 0.006, "z_coxa": 0.048, "r_coxa": 0.012,
        "r_tarso": 0.0036, "z_canela_top": 0.043, "z_peso": 0.002,
        "r_dedo": 0.0026, "d_dedo": 0.009, "h_dedo": 0.016,
    },
    "levantar": 0.015,
    "bones": [
        ("Corpo",   (0,  0.056, 0.050), (0, -0.046, 0.042), None),
        ("Pescoco", (0, -0.046, 0.042), (0, -0.082, 0.084), "Corpo"),
        ("Cabeca",  (0, -0.082, 0.084), (0, -0.098, 0.104), "Pescoco"),
        ("Cauda",   (0,  0.056, 0.050), (0,  0.112, 0.042), "Corpo"),
        ("AsaE",    ( 0.006, -0.018, 0.060), ( 0.013, 0.060, 0.050), "Corpo"),
        ("AsaD",    (-0.006, -0.018, 0.060), (-0.013, 0.060, 0.050), "Corpo"),
        ("CoxaE",   ( 0.011,  0.006, 0.045), ( 0.012, 0.007, 0.020), "Corpo"),
        ("CoxaD",   (-0.011,  0.006, 0.045), (-0.012, 0.007, 0.020), "Corpo"),
        ("CanelaE", ( 0.012,  0.007, 0.020), ( 0.012, 0.007, 0.009), "CoxaE"),
        ("CanelaD", (-0.012,  0.007, 0.020), (-0.012, 0.007, 0.009), "CoxaD"),
        ("PeE",     ( 0.012,  0.007, 0.009), ( 0.012, -0.006, 0.005), "CanelaE"),
        ("PeD",     (-0.012,  0.007, 0.009), (-0.012, -0.006, 0.005), "CanelaD"),
    ],
    "escala_anim": 0.6, "ciclo_walk": 14,
    "fly": {"ciclo": 12, "amp": 62, "mid": 14, "coxa": 62, "canela": 78, "pe": -38},
}

# ============================================================================
# gaivota — branca, asas cinza com pontas escuras, bico laranja, pernas longas
# ============================================================================
gaivota = {
    "id": "gaivota",
    "mats": {
        "corpo":     ((0.920, 0.915, 0.880), 0.66),
        "cabeca":    ((0.935, 0.930, 0.900), 0.64),
        "asa":       ((0.610, 0.640, 0.670), 0.70),
        "primarias": ((0.280, 0.310, 0.360), 0.68),
        "cauda":     ((0.880, 0.875, 0.850), 0.70),
        "bico":      ((0.900, 0.580, 0.200), 0.42),
        "olho":      ((0.055, 0.020, 0.015), 0.18),
        "perna":     ((0.880, 0.580, 0.220), 0.50),
    },
    "secoes": [
        ( 0.150, 0.128, 0.030, 0.022),
        ( 0.100, 0.138, 0.055, 0.045),
        ( 0.045, 0.130, 0.068, 0.055),
        (-0.025, 0.115, 0.070, 0.060),
        (-0.080, 0.100, 0.057, 0.057),
        (-0.130, 0.105, 0.040, 0.045),
        (-0.160, 0.134, 0.038, 0.040),
        (-0.185, 0.168, 0.030, 0.032),
        (-0.198, 0.200, 0.024, 0.026),
    ],
    "cabeca": ((0, -0.208, 0.220), (0.029, 0.033, 0.031)),
    "bico": {"tipo": "cone", "r1": 0.0066, "r2": 0.0013, "prof": 0.058, "pos": (0, -0.240, 0.213), "rx": 93},
    "olho_dx": 0.0235, "olho_dy": 0.003, "olho_dz": 0.0055, "olho_r": 0.0040,
    "asa": {"L": 0.20, "W": 0.074, "x_sh": 0.041, "y_sh": -0.055, "z_sh": 0.130, "rx": -12, "rz": 3},
    "cauda": {"L": 0.085, "W": 0.034, "pos": (0, 0.135, 0.118), "rx": -6},
    "perna": {
        "x": 0.026, "y": 0.014, "z_coxa": 0.082, "r_coxa": 0.019,
        "r_tarso": 0.0052, "z_canela_top": 0.076, "z_peso": 0.002,
        "r_dedo": 0.0038, "d_dedo": 0.013, "h_dedo": 0.023,
    },
    "levantar": 0.018,
    "bones": [
        ("Corpo",   (0,  0.100, 0.128), (0, -0.090, 0.112), None),
        ("Pescoco", (0, -0.090, 0.112), (0, -0.180, 0.188), "Corpo"),
        ("Cabeca",  (0, -0.180, 0.188), (0, -0.215, 0.225), "Pescoco"),
        ("Cauda",   (0,  0.100, 0.128), (0,  0.225, 0.112), "Corpo"),
        ("AsaE",    ( 0.008, -0.030, 0.130), ( 0.034, 0.130, 0.105), "Corpo"),
        ("AsaD",    (-0.008, -0.030, 0.130), (-0.034, 0.130, 0.105), "Corpo"),
        ("CoxaE",   ( 0.026,  0.016, 0.085), ( 0.026, 0.014, 0.045), "Corpo"),
        ("CoxaD",   (-0.026,  0.016, 0.085), (-0.026, 0.014, 0.045), "Corpo"),
        ("CanelaE", ( 0.026,  0.014, 0.045), ( 0.026, 0.014, 0.012), "CoxaE"),
        ("CanelaD", (-0.026,  0.014, 0.045), (-0.026, 0.014, 0.012), "CoxaD"),
        ("PeE",     ( 0.026,  0.014, 0.012), ( 0.026, -0.015, 0.006), "CanelaE"),
        ("PeD",     (-0.026,  0.014, 0.012), (-0.026, -0.015, 0.006), "CanelaD"),
    ],
    "escala_anim": 1.1, "ciclo_walk": 16,
    "fly": {"ciclo": 14, "amp": 46, "mid": 12, "coxa": 58, "canela": 74, "pe": -34},
}

# ============================================================================
# urubu — grande e escuro, cabeca calva, bico ganchudo, pescoço S, pernas grossas
# ============================================================================
urubu = {
    "id": "urubu",
    "mats": {
        "corpo":     ((0.125, 0.100, 0.088), 0.80),
        "cabeca":    ((0.580, 0.520, 0.480), 0.62),
        "asa":       ((0.075, 0.065, 0.058), 0.78),
        "primarias": ((0.045, 0.042, 0.040), 0.76),
        "cauda":     ((0.070, 0.062, 0.055), 0.80),
        "bico":      ((0.720, 0.700, 0.660), 0.40),
        "olho":      ((0.020, 0.018, 0.015), 0.18),
        "perna":     ((0.330, 0.340, 0.360), 0.55),
    },
    "secoes": [
        ( 0.185, 0.150, 0.038, 0.028),
        ( 0.125, 0.162, 0.070, 0.060),
        ( 0.060, 0.155, 0.088, 0.072),
        (-0.020, 0.140, 0.090, 0.075),
        (-0.085, 0.122, 0.074, 0.070),
        (-0.145, 0.128, 0.052, 0.052),
        (-0.185, 0.158, 0.038, 0.038),
        (-0.205, 0.205, 0.028, 0.028),
        (-0.215, 0.250, 0.022, 0.022),
    ],
    "cabeca": ((0, -0.225, 0.272), (0.026, 0.029, 0.027)),
    "bico": {"tipo": "gancho", "r1": 0.0088, "r2": 0.0016, "prof": 0.036,
             "pos": (0, -0.252, 0.266), "rx": 102, "gancho": (0, -0.276, 0.250), "grx": 152},
    "olho_dx": 0.0210, "olho_dy": 0.003, "olho_dz": 0.006, "olho_r": 0.0042,
    "asa": {"L": 0.23, "W": 0.090, "x_sh": 0.050, "y_sh": -0.065, "z_sh": 0.145, "rx": -11, "rz": 3},
    "cauda": {"L": 0.105, "W": 0.040, "pos": (0, 0.165, 0.135), "rx": -5},
    "perna": {
        "x": 0.030, "y": 0.018, "z_coxa": 0.094, "r_coxa": 0.023,
        "r_tarso": 0.0066, "z_canela_top": 0.088, "z_peso": 0.002,
        "r_dedo": 0.0048, "d_dedo": 0.014, "h_dedo": 0.025,
    },
    "levantar": 0.020,
    "bones": [
        ("Corpo",   (0,  0.120, 0.150), (0, -0.110, 0.132), None),
        ("Pescoco", (0, -0.110, 0.132), (0, -0.205, 0.240), "Corpo"),
        ("Cabeca",  (0, -0.205, 0.240), (0, -0.245, 0.285), "Pescoco"),
        ("Cauda",   (0,  0.120, 0.150), (0,  0.280, 0.130), "Corpo"),
        ("AsaE",    ( 0.009, -0.040, 0.145), ( 0.042, 0.150, 0.120), "Corpo"),
        ("AsaD",    (-0.009, -0.040, 0.145), (-0.042, 0.150, 0.120), "Corpo"),
        ("CoxaE",   ( 0.030,  0.018, 0.098), ( 0.032, 0.018, 0.050), "Corpo"),
        ("CoxaD",   (-0.030,  0.018, 0.098), (-0.032, 0.018, 0.050), "Corpo"),
        ("CanelaE", ( 0.032,  0.018, 0.050), ( 0.032, 0.018, 0.012), "CoxaE"),
        ("CanelaD", (-0.032,  0.018, 0.050), (-0.032, 0.018, 0.012), "CoxaD"),
        ("PeE",     ( 0.032,  0.018, 0.012), ( 0.032, -0.020, 0.006), "CanelaE"),
        ("PeD",     (-0.032,  0.018, 0.012), (-0.032, -0.020, 0.006), "CanelaD"),
    ],
    "escala_anim": 1.3, "ciclo_walk": 22,
    "fly": {"ciclo": 18, "amp": 38, "mid": 10, "coxa": 55, "canela": 70, "pe": -30},
}

for esp in (passaro, gaivota, urubu):
    build(esp)

# ---------------------------------------------------------------- previews
# Importante: o import deixa a acao Fly (voe) como padrao; para o preview
# posado usamos o rest pose (pernas estendidas no chao), nao o ciclo de voo.
for nome, dist, h in (("passaro", 0.42, 0.055), ("gaivota", 0.75, 0.12), ("urubu", 0.95, 0.15)):
    K.reset_scene()
    cam = K.setup_preview()
    cam.data.lens = 50
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
    K.render_de(cam, (dist * 0.72, -dist, h + 0.04), (0, -0.02, h * 0.8), os.path.join(K.OUT_DIR, "prev_%s.png" % nome))
    K.render_de(cam, (dist * 0.12, -dist, h + 0.01), (0, 0.0, h * 0.85), os.path.join(K.OUT_DIR, "prev_%s_b.png" % nome))
    print("PREVIEW:", nome)
print("AVES PRONTAS")
