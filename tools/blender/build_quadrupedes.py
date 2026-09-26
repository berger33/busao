# Quadrupedes — capivara, cavalo e boi (Blender 4.5 headless).
# Lote 3 dos assets 3D. Padrao do pombo/aves: frente = -Y, origem no chao,
# clips Walk + Idle + (Graze|Lie) — o jogo troca o clip pela pose
# (run->Walk, idle->Idle, crouch->Graze/Lie; ver world_animal.gd).
#
# Rig (14 ossos): Corpo -> Pescoco -> Cabeca, Cauda,
# e 4 pernas: Cox(FE/FD/TR/TD) -> Canel -> Pe (diagonal FE+TR / FD+TD).
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

    M = {k: K.material(especie["id"] + "_" + k, *v) for k, v in especie["mats"].items()}
    an = especie["id"].capitalize()

    # ---------------------------------------------------------------- corpo
    corpo = K.loft(an + "Corpo", especie["secoes"], seg=especie.get("seg", 16))
    K.pintar(corpo, M["corpo"]); add(corpo, "Corpo")

    # ---------------------------------------------------------------- pescoco
    pesc = K.loft(an + "Pescoco", especie["pescoco"], seg=12)
    K.pintar(pesc, M["corpo"]); add(pesc, "Pescoco")

    # ---------------------------------------------------------------- cabeca
    hc, hr = especie["cabeca"]
    add(K.elipsoide(an + "Cabeca", hc, hr), "Cabeca")
    partes[-1][0].data.materials.clear()
    partes[-1][0].data.materials.append(M["cabeca"])
    fc, fr = especie["focinho"]
    add(K.elipsoide(an + "Focinho", fc, fr), "Cabeca")
    partes[-1][0].data.materials.clear()
    partes[-1][0].data.materials.append(M["focinho"])
    # nariz
    nariz = K.elipsoide(an + "Nariz", (fc[0], fc[1] - fr[1] * 0.82, fc[2] + fr[2] * 0.12),
                        (fr[0] * 0.42, fr[1] * 0.30, fr[2] * 0.42), nivel=1)
    K.pintar(nariz, M["focinho"]); add(nariz, "Cabeca")
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        ec = (hc[0] + sx * especie["olho_dx"], hc[1] - especie["olho_dy"], hc[2] + especie["olho_dz"])
        o = K.elipsoide(an + "Olho" + suf, ec, (especie["olho_r"],) * 3, nivel=1)
        K.pintar(o, M["olho"]); add(o, "Cabeca")
    # orelhas: elipsoides suaves (cones ficavam como chapéos planos)
    orl = especie["orelha"]
    for sx, suf in ((1.0, "E"), (-1.0, "D")):
        ec = (hc[0] + sx * orl["dx"], hc[1] + orl["dy"], hc[2] + orl["dz"])
        o = K.elipsoide(an + "Orelha" + suf, ec, orl["r"], nivel=1)
        o.rotation_euler = (rad(orl.get("rx", -8)), sx * rad(orl["tilt"]), 0)
        K.sozinho(o)
        # so rotacao: o objeto ainda tem a origem no centro da orelha
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(o, M["orelha"]); add(o, "Cabeca")
    # extras da especie (chifres, topete, manchas, ubero...)
    for extra in especie.get("extras", []):
        kind = extra[0]
        if kind == "chifre":
            for sx, suf in ((1.0, "E"), (-1.0, "D")):
                ch = K.cone_part(an + "Chifre" + suf, extra[1]["r1"], extra[1]["r2"], extra[1]["prof"], 10)
                K.sozinho(ch)
                ch.location = (sx * extra[1]["dx"], extra[1]["y"], extra[1]["z"])
                ch.rotation_euler = (rad(extra[1].get("rx", -12)), sx * rad(extra[1].get("tilt", 38)), 0)
                bpy.ops.object.transform_apply(rotation=True, location=True)
                K.pintar(ch, M["chifre"]); add(ch, "Cabeca")
        elif kind == "mancha":
            mp = K.elipsoide(an + "Mancha" + str(len(partes)), extra[1], extra[2], nivel=1)
            K.pintar(mp, M["mancha"]); add(mp, "Corpo")
        elif kind == "ubero":
            ub = K.elipsoide(an + "Ubere", extra[1], extra[2], nivel=1)
            K.pintar(ub, M["ubero"]); add(ub, "Corpo")
        elif kind == "crina":
            cr = K.loft(an + "Crina", extra[1], seg=10)
            K.pintar(cr, M["crina"]); add(cr, "Pescoco")
        elif kind == "topete":
            tp = K.elipsoide(an + "Topete", extra[1], extra[2], nivel=1)
            K.pintar(tp, M["crina"]); add(tp, "Cabeca")

    # ---------------------------------------------------------------- cauda
    cauda = K.loft(an + "Cauda", especie["cauda"], seg=10)
    K.pintar(cauda, M["cauda"]); add(cauda, "Cauda")
    if "cauda_tufo" in especie:
        pos, raios = especie["cauda_tufo"]
        tf = K.elipsoide(an + "CaudaTufo", pos, raios)
        K.pintar(tf, M["crina"] if "crina" in M else M["cauda"]); add(tf, "Cauda")

    # ---------------------------------------------------------------- pernas
    # 4 pernas: (suf, x, y, z_coxa_top, z_canela_top, z_ankle) + radios
    L = especie["perna"]
    # Sobreposicao de ~3 cm em cada junta: com o subsurf, pecas que apenas se
    # tocam acabam separadas (juntas abertas). O encostamento oculto garante
    # a fusao visual.
    ov = 0.03
    for (suf, sx, ly) in (("FE", 1.0, L["y_frente"]), ("FD", -1.0, L["y_frente"]),
                          ("TR", 1.0, L["y_tras"]), ("TD", -1.0, L["y_tras"])):
        lx = sx * L["x"]
        zct, zkt = L["z_coxa_top"], L["z_canela_top"]
        h_c = zct - (zkt - ov)
        coxa = K.pilar(an + "Coxa" + suf, L["r_coxa"], 1.18, seg=10)
        K.sozinho(coxa)
        coxa.scale = (1, 1, h_c)
        coxa.location = (lx, ly, zkt - ov)
        bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(coxa, M["corpo"]); add(coxa, "Coxa" + suf)
        h_k = (zkt + ov) - (L["z_ankle"] - ov)
        canela = K.pilar(an + "Canela" + suf, L["r_canela"], 1.35, seg=10)
        K.sozinho(canela)
        canela.scale = (1, 1, h_k)
        canela.location = (lx, ly + (0.006 if "TR" in suf or "TD" in suf else -0.004), L["z_ankle"] - ov)
        bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(canela, M["corpo"]); add(canela, "Canela" + suf)
        pe = K.pilar(an + "Pe" + suf, L["r_pe"], 0.82, seg=10)
        K.sozinho(pe)
        pe.scale = (1, 1, L["h_pe"] + ov * 0.6)
        pe.location = (lx, ly + (0.004 if "TR" in suf or "TD" in suf else -0.002), 0.002)
        bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(pe, M["casca"]); add(pe, "Pe" + suf)

    # ---------------------------------------------------------------- join + rig
    an_obj = K.join_parts(partes)
    an_obj.name = an
    leg = L
    bones = [
        (b[0], b[1], b[2], b[3]) for b in especie["bones"]]
    for (suf, sx, ly) in (("FE", 1.0, leg["y_frente"]), ("FD", -1.0, leg["y_frente"]),
                          ("TR", 1.0, leg["y_tras"]), ("TD", -1.0, leg["y_tras"])):
        lx = sx * leg["x"]
        zct, zkt, za = leg["z_coxa_top"], leg["z_canela_top"], leg["z_ankle"]
        bones.append(("Coxa" + suf,   (lx, ly, zct + 0.01), (lx, ly, zkt), "Corpo"))
        bones.append(("Canela" + suf, (lx, ly, zkt),        (lx, ly, za + 0.005), "Coxa" + suf))
        bones.append(("Pe" + suf,     (lx, ly, za + 0.005), (lx, ly - 0.02, 0.0), "Canela" + suf))
    arm = K.armature(especie["id"], bones)
    K.skin(arm, an_obj)

    # ---------------------------------------------------------------- clips
    A = especie["anim"]
    S = A["S"]
    ciclo = A["ciclo_walk"]
    a = K.new_action(arm, "Walk")
    for f in range(1, ciclo + 2):
        t = (f - 1) / ciclo * K.TAU
        s1, c1 = math.sin(t), math.cos(t)          # par diagonal FE+TR
        s2, c2 = -s1, c1                            # par diagonal FD+TD
        l1 = max(0.0, math.sin(t + 0.9))            # levantamento no balanço
        l2 = max(0.0, math.sin(t + 0.9 + math.pi))
        K.key_rot(arm, "CoxaFE", f, (rad(A["coxa"]) * s1, 0, 0))
        K.key_rot(arm, "CoxaTR", f, (rad(A["coxa"]) * s1 * 0.85, 0, 0))
        K.key_rot(arm, "CoxaFD", f, (rad(A["coxa"]) * s2, 0, 0))
        K.key_rot(arm, "CoxaTD", f, (rad(A["coxa"]) * s2 * 0.85, 0, 0))
        K.key_rot(arm, "CanelaFE", f, (rad(A["canela"]) * l1, 0, 0))
        K.key_rot(arm, "CanelaFD", f, (rad(A["canela"]) * l2, 0, 0))
        K.key_rot(arm, "CanelaTR", f, (-rad(A["canela"]) * l1 * 0.9, 0, 0))
        K.key_rot(arm, "CanelaTD", f, (-rad(A["canela"]) * l2 * 0.9, 0, 0))
        K.key_rot(arm, "PeFE", f, (-rad(A["pe"]) * l1, 0, 0))
        K.key_rot(arm, "PeFD", f, (-rad(A["pe"]) * l2, 0, 0))
        K.key_rot(arm, "PeTR", f, (-rad(A["pe"]) * l1, 0, 0))
        K.key_rot(arm, "PeTD", f, (-rad(A["pe"]) * l2, 0, 0))
        K.key_loc(arm, "Corpo", f, (0, 0, 0.010 * S * math.cos(2 * t)))
        K.key_rot(arm, "Corpo", f, (rad(1.2) * math.sin(2 * t + 0.6), 0, rad(A.get("roll", 0.6)) * math.sin(2 * t)))
        K.key_rot(arm, "Pescoco", f, (rad(2.8) * math.cos(2 * t), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(-2.0) * math.cos(2 * t), 0, 0))
        K.key_rot(arm, "Cauda", f, (rad(5) * math.sin(t), 0, rad(5) * math.sin(t + 0.5)))
    K.linearize(a)

    # Idle: respiracao + cauda (12f)
    a = K.new_action(arm, "Idle")
    C = 12
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        K.key_loc(arm, "Corpo", f, (0, 0, 0.005 * S * math.sin(t)))
        K.key_rot(arm, "Corpo", f, (rad(0.8) * math.sin(t + 1.0), 0, 0))
        K.key_rot(arm, "Pescoco", f, (rad(1.6) * math.sin(t + 0.4), 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(-1.2) * math.sin(t + 0.7), 0, rad(1.0) * math.sin(t * 0.5)))
        K.key_rot(arm, "Cauda", f, (0, 0, rad(5.5) * math.sin(t)))
    K.linearize(a)

    # Graze (cavalo/boi) ou Lie (capivara): pose de crouch do contrato
    g = A["crouch"]
    a = K.new_action(arm, g["nome"])
    C = g.get("ciclo", 16)
    for f in range(1, C + 2):
        t = (f - 1) / C * K.TAU
        mastigar = rad(g.get("mastigar", 2.0)) * math.sin(2 * t)
        K.key_rot(arm, "Pescoco", f, (rad(g["pescoco"]) + mastigar * 0.4, 0, 0))
        K.key_rot(arm, "Cabeca", f, (rad(g["cabeca"]) + mastigar, 0, 0))
        K.key_loc(arm, "Corpo", f, (0, 0, g.get("caida", 0.0)))
        K.key_rot(arm, "Corpo", f, (rad(g.get("inclinacao", 3.0)), 0, 0))
        K.key_rot(arm, "CoxaFE", f, (rad(g.get("coxa_f", -3.0)), 0, rad(g.get("abrir", 2.0))))
        K.key_rot(arm, "CoxaFD", f, (rad(g.get("coxa_f", -3.0)), 0, -rad(g.get("abrir", 2.0))))
        K.key_rot(arm, "CoxaTR", f, (rad(g.get("coxa_t", 3.0)), 0, rad(g.get("abrir", 2.0))))
        K.key_rot(arm, "CoxaTD", f, (rad(g.get("coxa_t", 3.0)), 0, -rad(g.get("abrir", 2.0))))
        K.key_rot(arm, "CanelaFE", f, (rad(g.get("canela_f", 0.0)), 0, 0))
        K.key_rot(arm, "CanelaFD", f, (rad(g.get("canela_f", 0.0)), 0, 0))
        K.key_rot(arm, "CanelaTR", f, (rad(g.get("canela_t", 0.0)), 0, 0))
        K.key_rot(arm, "CanelaTD", f, (rad(g.get("canela_t", 0.0)), 0, 0))
        K.key_rot(arm, "PeFE", f, (rad(g.get("pe_f", 0.0)), 0, 0))
        K.key_rot(arm, "PeFD", f, (rad(g.get("pe_f", 0.0)), 0, 0))
        K.key_rot(arm, "PeTR", f, (rad(g.get("pe_t", 0.0)), 0, 0))
        K.key_rot(arm, "PeTD", f, (rad(g.get("pe_t", 0.0)), 0, 0))
        K.key_rot(arm, "Cauda", f, (0, 0, rad(6.0) * math.sin(t * 0.5 + 1.0)))
    K.linearize(a)

    arm.animation_data.action = D.actions["Walk"]
    K.clear_pose(arm)

    glb = os.path.join(ANIMAIS, especie["id"] + ".glb")
    K.export_glb(glb, [arm, an_obj])
    print("ESPECIE:", especie["id"], "OK")


# ============================================================================
# capivara — grande, barril, cabeca quadrada, pernas curtas, sem cauda visivel
# (1,2 m de nariz a quadril; dorso 0,68 m)
# ============================================================================
capivara = {
    "id": "capivara",
    "mats": {
        "corpo":   ((0.430, 0.310, 0.200), 0.80),
        "cabeca":  ((0.380, 0.270, 0.175), 0.78),
        "focinho": ((0.330, 0.235, 0.155), 0.72),
        "orelha":  ((0.300, 0.210, 0.140), 0.75),
        "olho":    ((0.030, 0.024, 0.018), 0.20),
        "cauda":   ((0.400, 0.290, 0.185), 0.80),
        "casca":   ((0.160, 0.130, 0.110), 0.55),
    },
    "secoes": [
        ( 0.400, 0.400, 0.150, 0.190),
        ( 0.300, 0.420, 0.210, 0.250),
        ( 0.120, 0.430, 0.235, 0.270),
        (-0.100, 0.435, 0.235, 0.265),
        (-0.280, 0.440, 0.215, 0.250),
        (-0.360, 0.460, 0.160, 0.210),
    ],
    "pescoco": [
        (-0.340, 0.470, 0.130, 0.150),
        (-0.430, 0.500, 0.105, 0.125),
        (-0.500, 0.520, 0.090, 0.110),
    ],
    "cabeca":  ((0, -0.545, 0.545), (0.105, 0.145, 0.115)),
    "focinho": ((0, -0.665, 0.505), (0.085, 0.100, 0.085)),
    "olho_dx": 0.075, "olho_dy": 0.020, "olho_dz": 0.045, "olho_r": 0.013,
    "orelha": {"dx": 0.068, "dy": -0.015, "dz": 0.105, "r": (0.015, 0.022, 0.040), "rx": -12, "tilt": 16},
    "cauda": [
        (0.380, 0.430, 0.035, 0.035),
        (0.440, 0.400, 0.022, 0.024),
    ],
    "perna": {
        "x": 0.155, "y_frente": -0.24, "y_tras": 0.26,
        "z_coxa_top": 0.360, "z_canela_top": 0.240, "z_ankle": 0.070,
        "r_coxa": 0.085, "r_canela": 0.058, "r_pe": 0.052, "h_pe": 0.068,
    },
    "bones": [
        ("Corpo",   (0,  0.340, 0.430), (0, -0.300, 0.440), None),
        ("Pescoco", (0, -0.300, 0.460), (0, -0.490, 0.530), "Corpo"),
        ("Cabeca",  (0, -0.490, 0.530), (0, -0.620, 0.560), "Pescoco"),
        ("Cauda",   (0,  0.340, 0.430), (0,  0.460, 0.380), "Corpo"),
    ],
    "anim": {
        "S": 0.8, "ciclo_walk": 20, "coxa": 13, "canela": 30, "pe": 16, "roll": 0.3,
        "crouch": {"nome": "Lie", "ciclo": 16, "pescoco": 30, "cabeca": 14, "caida": 0.10,
                    "inclinacao": 5.0, "coxa_f": 18, "coxa_t": -14, "canela_f": 34, "canela_t": -34,
                    "pe_f": -20, "pe_t": -14, "abrir": 3.0, "mastigar": 1.2},
    },
}

# ============================================================================
# cavalo — alazao, crina escura, pernas longas, pescoço em S
# (1,85 m de nariz a cauda; cangalote 1,50 m)
# ============================================================================
cavalo = {
    "id": "cavalo",
    "mats": {
        "corpo":   ((0.300, 0.195, 0.120), 0.78),
        "cabeca":  ((0.320, 0.210, 0.135), 0.76),
        "focinho": ((0.420, 0.310, 0.220), 0.70),
        "orelha":  ((0.250, 0.160, 0.100), 0.74),
        "olho":    ((0.030, 0.024, 0.018), 0.20),
        "cauda":   ((0.100, 0.065, 0.045), 0.80),
        "crina":   ((0.110, 0.070, 0.048), 0.82),
        "casca":   ((0.055, 0.045, 0.040), 0.50),
    },
    "secoes": [
        ( 0.440, 1.060, 0.220, 0.290),
        ( 0.320, 1.100, 0.290, 0.350),
        ( 0.120, 1.060, 0.315, 0.375),
        (-0.100, 1.080, 0.310, 0.365),
        (-0.300, 1.120, 0.290, 0.370),
        (-0.420, 1.220, 0.200, 0.290),
    ],
    "pescoco": [
        (-0.400, 1.200, 0.160, 0.200),
        (-0.500, 1.300, 0.125, 0.155),
        (-0.600, 1.400, 0.100, 0.125),
    ],
    "cabeca":  ((0, -0.680, 1.470), (0.105, 0.175, 0.105)),
    "focinho": ((0, -0.825, 1.400), (0.064, 0.115, 0.070)),
    "olho_dx": 0.075, "olho_dy": 0.045, "olho_dz": 0.045, "olho_r": 0.014,
    "orelha": {"dx": 0.052, "dy": 0.020, "dz": 0.115, "r": (0.013, 0.030, 0.052), "rx": -18, "tilt": 10},
    "cauda": [
        (0.420, 1.300, 0.035, 0.050),
        (0.520, 1.050, 0.028, 0.040),
        (0.580, 0.800, 0.024, 0.034),
    ],
    "cauda_tufo": ((0.0, 0.620, 0.660), (0.045, 0.090, 0.110)),
    "extras": [
        ("crina", [
            (-0.400, 1.475, 0.026, 0.085),
            (-0.500, 1.565, 0.024, 0.075),
            (-0.600, 1.645, 0.022, 0.060),
        ]),
        ("topete", (0, -0.730, 1.600), (0.045, 0.060, 0.050)),
    ],
    "perna": {
        "x": 0.185, "y_frente": -0.30, "y_tras": 0.30,
        "z_coxa_top": 1.160, "z_canela_top": 0.600, "z_ankle": 0.160,
        "r_coxa": 0.085, "r_canela": 0.048, "r_pe": 0.052, "h_pe": 0.158,
    },
    "bones": [
        ("Corpo",   (0,  0.380, 1.100), (0, -0.380, 1.120), None),
        ("Pescoco", (0, -0.380, 1.180), (0, -0.600, 1.420), "Corpo"),
        ("Cabeca",  (0, -0.600, 1.420), (0, -0.760, 1.520), "Pescoco"),
        ("Cauda",   (0,  0.380, 1.300), (0,  0.560, 0.820), "Corpo"),
    ],
    "anim": {
        "S": 1.3, "ciclo_walk": 24, "coxa": 20, "canela": 42, "pe": 22, "roll": 1.0,
        "crouch": {"nome": "Graze", "ciclo": 16, "pescoco": 56, "cabeca": 18, "inclinacao": 4.0,
                    "coxa_f": -4, "coxa_t": 4, "canela_f": 5, "canela_t": -4, "abrir": 3.0,
                    "mastigar": 2.2},
    },
}

# ============================================================================
# boi — gado de cria: corpo profundo, ubere, chifres curtos, focinho largo
# (1,95 m; dorso 1,44 m)
# ============================================================================
boi = {
    "id": "boi",
    "mats": {
        "corpo":   ((0.800, 0.715, 0.575), 0.82),
        "cabeca":  ((0.780, 0.690, 0.555), 0.80),
        "focinho": ((0.760, 0.545, 0.480), 0.66),
        "orelha":  ((0.720, 0.620, 0.480), 0.80),
        "olho":    ((0.035, 0.030, 0.024), 0.20),
        "cauda":   ((0.660, 0.580, 0.460), 0.84),
        "chifre":  ((0.860, 0.820, 0.700), 0.42),
        "mancha":  ((0.360, 0.255, 0.175), 0.82),
        "ubero":   ((0.760, 0.545, 0.470), 0.60),
        "casca":   ((0.100, 0.085, 0.075), 0.55),
    },
    "secoes": [
        ( 0.460, 1.020, 0.230, 0.300),
        ( 0.340, 1.050, 0.310, 0.400),
        ( 0.140, 1.020, 0.340, 0.430),
        (-0.100, 1.040, 0.335, 0.420),
        (-0.320, 1.080, 0.310, 0.410),
        (-0.450, 1.140, 0.220, 0.330),
    ],
    "pescoco": [
        (-0.430, 1.150, 0.170, 0.210),
        (-0.530, 1.240, 0.135, 0.165),
        (-0.630, 1.320, 0.110, 0.135),
    ],
    "cabeca":  ((0, -0.710, 1.380), (0.110, 0.160, 0.115)),
    "focinho": ((0, -0.840, 1.300), (0.095, 0.110, 0.095)),
    "olho_dx": 0.080, "olho_dy": 0.040, "olho_dz": 0.040, "olho_r": 0.016,
    "orelha": {"dx": 0.095, "dy": 0.010, "dz": 0.090, "r": (0.038, 0.050, 0.028), "rx": 10, "tilt": 50},
    "cauda": [
        (0.440, 1.260, 0.032, 0.045),
        (0.540, 1.000, 0.026, 0.038),
        (0.600, 0.760, 0.022, 0.032),
    ],
    "cauda_tufo": ((0.0, 0.640, 0.600), (0.040, 0.080, 0.100)),
    "extras": [
        ("chifre", {"r1": 0.030, "r2": 0.008, "prof": 0.17, "dx": 0.095, "y": -0.700, "z": 1.520, "tilt": 34, "rx": -10}),
        ("mancha", (-0.200, 0.300, 1.150), (0.160, 0.200, 0.190)),
        ("mancha", (0.260, -0.200, 0.900), (0.150, 0.180, 0.170)),
        ("ubero", (0, 0.300, 0.560), (0.100, 0.150, 0.115)),
    ],
    "perna": {
        "x": 0.190, "y_frente": -0.30, "y_tras": 0.32,
        "z_coxa_top": 1.100, "z_canela_top": 0.560, "z_ankle": 0.140,
        "r_coxa": 0.100, "r_canela": 0.062, "r_pe": 0.062, "h_pe": 0.138,
    },
    "bones": [
        ("Corpo",   (0,  0.400, 1.050), (0, -0.400, 1.080), None),
        ("Pescoco", (0, -0.400, 1.120), (0, -0.620, 1.340), "Corpo"),
        ("Cabeca",  (0, -0.620, 1.340), (0, -0.770, 1.420), "Pescoco"),
        ("Cauda",   (0,  0.400, 1.260), (0,  0.580, 0.780), "Corpo"),
    ],
    "anim": {
        "S": 1.4, "ciclo_walk": 22, "coxa": 16, "canela": 34, "pe": 20, "roll": 0.5,
        "crouch": {"nome": "Graze", "ciclo": 16, "pescoco": 58, "cabeca": 20, "inclinacao": 5.0,
                    "coxa_f": -4, "coxa_t": 5, "canela_f": 5, "canela_t": -5, "abrir": 3.5,
                    "mastigar": 2.6},
    },
}

for esp in (capivara, cavalo, boi):
    build(esp)

# ---------------------------------------------------------------- previews
# Rest pose (pernas plantadas) — nao o ciclo de caminhada. A camera fica a
# ~2.6x a altura do animal e olha o centro: cabe a silhueta inteira.
for nome, h in (("capivara", 0.72), ("cavalo", 1.65), ("boi", 1.62)):
    dist = h * 2.6
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
    K.render_de(cam, (dist * 0.72, -dist, h * 0.62), (0, 0.0, h * 0.52), os.path.join(K.OUT_DIR, "prev_%s.png" % nome))
    K.render_de(cam, (dist * 0.12, -dist, h * 0.55), (0, 0.15, h * 0.50), os.path.join(K.OUT_DIR, "prev_%s_b.png" % nome))
    print("PREVIEW:", nome)
print("QUADRUPEDES PRONTOS")
