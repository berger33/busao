#!/usr/bin/env python3
# Caramelo SRD — vira-lata caramelo brasileiro 100% original Blender headless 4.5
# Substitui o Fox Khronos CC0 em assets/characters/animais/caramelo.glb
# Segue contrato quadrupede: Walk (run), Idle, Lie (play bow) — world_animal.gd mapeia
# run->Walk, idle->Idle, crouch->Lie. Frente = -Y, origem no chao, bbox [0.95,0.72] via GLB_SIZES
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad

D = bpy.data
ANIMAIS = str(K.REPO / "assets" / "characters" / "animais")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(ANIMAIS, exist_ok=True)

caramelo = {
    "id": "caramelo",
    "mats": {
        "corpo":   ((0.78, 0.48, 0.22), 0.78),  # caramelo medio
        "barriga": ((0.82, 0.58, 0.32), 0.82),  # peito/barriga mais claro
        "cabeca":  ((0.72, 0.44, 0.20), 0.76),
        "focinho": ((0.75, 0.50, 0.28), 0.72),
        "orelha":  ((0.55, 0.32, 0.16), 0.74),  # orelha caramelo escuro, ponta preta leve
        "orelha_inner": ((0.45, 0.28, 0.18), 0.78),
        "olho":    ((0.08, 0.06, 0.04), 0.18),
        "nariz":   ((0.06, 0.05, 0.05), 0.35),
        "cauda":   ((0.70, 0.42, 0.19), 0.80),
        "cauda_tufo": ((0.78, 0.48, 0.22), 0.80),
        "casca":   ((0.12, 0.10, 0.09), 0.50),  # patas/unhas escuras
        "coleira": ((0.18, 0.42, 0.65), 0.45),
        "metal":   ((0.92, 0.78, 0.35), 0.30, 0.75),
    },
    "secoes": [
        ( 0.34, 0.38, 0.13, 0.15),  # quadril traseiro
        ( 0.20, 0.40, 0.15, 0.18),  # lombo meio-tras
        ( 0.02, 0.42, 0.16, 0.19),  # meio dorso (mais largo)
        (-0.12, 0.44, 0.15, 0.18),  # peito
        (-0.24, 0.46, 0.13, 0.16),  # peito frontal
    ],
    "pescoco": [
        (-0.24, 0.46, 0.090, 0.105),
        (-0.32, 0.52, 0.082, 0.095),
        (-0.42, 0.58, 0.070, 0.082),
    ],
    "cabeca":  ((0, -0.52, 0.58), (0.095, 0.095, 0.090)),  # cabeca centro e raios
    "focinho": ((0, -0.66, 0.54), (0.065, 0.085, 0.065)),
    "olho_dx": 0.055, "olho_dy": 0.015, "olho_dz": 0.035, "olho_r": 0.014,
    "orelha": {"dx": 0.068, "dy": 0.010, "dz": 0.075, "r": (0.028, 0.055, 0.045), "rx": 18, "tilt": 22},
    "orelha_inner": {"r": (0.015, 0.035, 0.030)},
    "cauda": [
        (0.34, 0.42, 0.032, 0.032),
        (0.44, 0.48, 0.028, 0.028),
        (0.52, 0.52, 0.024, 0.024),
        (0.58, 0.50, 0.020, 0.020),
    ],
    "cauda_tufo": ((0.0, 0.62, 0.52), (0.045, 0.055, 0.065)),
    "extras": [
        # coleira + pingente (DogCollar/Tag para compatibilidade world_animal procedural, mas o GLB já tem coleira)
        ("coleira", {"pos": (0, -0.38, 0.52), "r": 0.058}),
    ],
    "perna": {
        "x": 0.11, "y_frente": -0.20, "y_tras": 0.22,
        "z_coxa_top": 0.36, "z_canela_top": 0.22, "z_ankle": 0.075,
        "r_coxa": 0.055, "r_canela": 0.038, "r_pe": 0.040, "h_pe": 0.065,
    },
    "bones": [
        ("Corpo",   (0,  0.28, 0.42), (0, -0.20, 0.44), None),
        ("Pescoco", (0, -0.20, 0.44), (0, -0.42, 0.56), "Corpo"),
        ("Cabeca",  (0, -0.42, 0.56), (0, -0.60, 0.58), "Pescoco"),
        ("Cauda",   (0,  0.34, 0.42), (0,  0.44, 0.48), "Corpo"),
        ("CaudaPonta", (0, 0.44, 0.48), (0, 0.58, 0.52), "Cauda"),
    ],
    "anim": {
        "S": 1.0, "ciclo_walk": 16, "coxa": 22, "canela": 38, "pe": 18, "roll": 0.9,
        "crouch": {"nome": "Lie", "ciclo": 20, "pescoco": -18, "cabeca": -12, "caida": -0.04,
                    "inclinacao": 6.0, "coxa_f": -38, "coxa_t": -8, "canela_f": 42, "canela_t": 32,
                    "pe_f": -18, "pe_t": -8, "abrir": 4.0, "mastigar": 0},
        "idle_scent": True,
    },
}

def build(especie: dict) -> None:
    K.reset_scene()
    partes = []
    def add(o, grupo):
        partes.append((o, grupo))
    M = {}
    for k, v in especie["mats"].items():
        if len(v) == 2:
            col, rough = v
            metal = 0.0
        else:
            col, rough, metal = v
        M[k] = K.material(especie["id"] + "_" + k, col, rough, metal)
    an = especie["id"].capitalize()
    # corpo
    corpo = K.loft(an + "Corpo", especie["secoes"], seg=16)
    K.pintar(corpo, M["corpo"]); add(corpo, "Corpo")
    # barriga clara (elipsoide ventral)
    barr = K.elipsoide(an + "Barriga", (0, 0.02, 0.32), (0.11, 0.18, 0.09), nivel=1)
    K.pintar(barr, M["barriga"]); add(barr, "Corpo")
    # pescoco
    pesc = K.loft(an + "Pescoco", especie["pescoco"], seg=10)
    K.pintar(pesc, M["corpo"]); add(pesc, "Pescoco")
    # cabeca
    hc, hr = especie["cabeca"]
    add(K.elipsoide(an + "Cabeca", hc, hr), "Cabeca")
    partes[-1][0].data.materials.clear(); partes[-1][0].data.materials.append(M["cabeca"])
    fc, fr = especie["focinho"]
    add(K.elipsoide(an + "Focinho", fc, fr), "Cabeca")
    partes[-1][0].data.materials.clear(); partes[-1][0].data.materials.append(M["focinho"])
    # nariz
    nariz = K.elipsoide(an + "Nariz", (fc[0], fc[1] - fr[1]*0.78, fc[2] + fr[2]*0.10), (fr[0]*0.38, fr[1]*0.28, fr[2]*0.38), nivel=1)
    K.pintar(nariz, M["nariz"]); add(nariz, "Cabeca")
    # olhos
    for sx, suf in ((1.0,"E"), (-1.0,"D")):
        ec = (hc[0] + sx*especie["olho_dx"], hc[1] - especie["olho_dy"], hc[2] + especie["olho_dz"])
        o = K.elipsoide(an + "Olho" + suf, ec, (especie["olho_r"],)*3, nivel=1)
        K.pintar(o, M["olho"]); add(o, "Cabeca")
        # brilho
        br = K.elipsoide(an + "Brilho" + suf, (ec[0]+0.004, ec[1]-0.004, ec[2]+0.006), (0.004,0.004,0.004), nivel=1)
        mat_br = K.material(an+"brilho", (0.92,0.92,0.95), 0.15)
        K.pintar(br, mat_br); add(br, "Cabeca")
    # orelhas caidas (caramelo tem orelha semi-ereta, ponta dobrada)
    orl = especie["orelha"]
    orl_inner = especie.get("orelha_inner", {"r": (0.015,0.035,0.030)})
    for sx, suf in ((1.0,"E"), (-1.0,"D")):
        ec = (hc[0] + sx*orl["dx"], hc[1] + orl["dy"], hc[2] + orl["dz"])
        o = K.elipsoide(an + "Orelha" + suf, ec, orl["r"], nivel=1)
        o.rotation_euler = (rad(orl.get("rx",18)), sx*rad(orl["tilt"]), rad(5))
        K.sozinho(o); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(o, M["orelha"]); add(o, "Cabeca")
        # inner
        ei = K.elipsoide(an + "OrelhaInner" + suf, (ec[0]+sx*0.006, ec[1]-0.004, ec[2]-0.008), orl_inner["r"], nivel=1)
        ei.rotation_euler = (rad(orl.get("rx",18)), sx*rad(orl["tilt"]), rad(5))
        K.sozinho(ei); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        K.pintar(ei, M["orelha_inner"]); add(ei, "Cabeca")
        # ponta escura
        ponta = K.elipsoide(an + "OrelhaPonta" + suf, (ec[0]+sx*0.010, ec[1]+0.025, ec[2]-0.035), (0.018,0.020,0.025), nivel=1)
        mat_ponta = K.material(an+"orelha_ponta", (0.32,0.20,0.12), 0.72)
        K.pintar(ponta, mat_ponta); add(ponta, "Cabeca")
    # cauda
    cauda = K.loft(an + "Cauda", especie["cauda"], seg=10)
    K.pintar(cauda, M["cauda"]); add(cauda, "Cauda")
    if "cauda_tufo" in especie:
        pos, raios = especie["cauda_tufo"]
        tf = K.elipsoide(an + "CaudaTufo", pos, raios)
        K.pintar(tf, M["cauda_tufo"]); add(tf, "CaudaPonta")
    # coleira + pingente (para ficar igual ao procedural DogCollar/Tag)
    # torus coleira
    coleira_pos = (-0.01, -0.38, 0.50)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.010, major_segments=18, minor_segments=8, location=coleira_pos)
    co = bpy.context.active_object; co.name = an+"Coleira"
    K.pintar(co, M["coleira"]); add(co, "Pescoco")
    # pingente dourado pendente
    ping = K.elipsoide(an+"Pingente", (0, -0.38, 0.43), (0.022,0.018,0.008), nivel=1)
    K.pintar(ping, M["metal"]); add(ping, "Pescoco")

    # pernas
    L = especie["perna"]
    ov = 0.03
    for (suf, sx, ly) in (("FE",1.0,L["y_frente"]),("FD",-1.0,L["y_frente"]),("TR",1.0,L["y_tras"]),("TD",-1.0,L["y_tras"])):
        lx = sx*L["x"]
        zct, zkt = L["z_coxa_top"], L["z_canela_top"]
        h_c = zct - (zkt - ov)
        coxa = K.pilar(an + "Coxa" + suf, L["r_coxa"], 1.18, seg=10)
        K.sozinho(coxa); coxa.scale=(1,1,h_c); coxa.location=(lx,ly,zkt-ov); bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(coxa, M["corpo"]); add(coxa, "Coxa"+suf)
        h_k = (zkt+ov) - (L["z_ankle"]-ov)
        canela = K.pilar(an + "Canela"+suf, L["r_canela"], 1.35, seg=10)
        K.sozinho(canela); canela.scale=(1,1,h_k); canela.location=(lx, ly + (0.006 if "TR" in suf or "TD" in suf else -0.004), L["z_ankle"]-ov); bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(canela, M["corpo"]); add(canela, "Canela"+suf)
        pe = K.pilar(an + "Pe"+suf, L["r_pe"], 0.82, seg=10)
        K.sozinho(pe); pe.scale=(1,1,L["h_pe"]+ov*0.6); pe.location=(lx, ly + (0.004 if "TR" in suf or "TD" in suf else -0.002), 0.002); bpy.ops.object.transform_apply(scale=True, location=True)
        K.pintar(pe, M["casca"]); add(pe, "Pe"+suf)
        # unhas
        for nx in (0,):
            unha = K.elipsoide(an+f"Unha{suf}", (lx, ly-0.018, 0.015), (0.012,0.018,0.010), nivel=1)
            K.pintar(unha, M["casca"]); add(unha, "Pe"+suf)

    # join + rig
    an_obj = K.join_parts(partes)
    an_obj.name = an
    leg = L
    bones = [(b[0],b[1],b[2],b[3]) for b in especie["bones"]]
    for (suf,sx,ly) in (("FE",1.0,leg["y_frente"]),("FD",-1.0,leg["y_frente"]),("TR",1.0,leg["y_tras"]),("TD",-1.0,leg["y_tras"])):
        lx = sx*leg["x"]
        zct,zkt,za = leg["z_coxa_top"], leg["z_canela_top"], leg["z_ankle"]
        bones.append(("Coxa"+suf, (lx,ly,zct+0.01), (lx,ly,zkt), "Corpo"))
        bones.append(("Canela"+suf, (lx,ly,zkt), (lx,ly,za+0.005), "Coxa"+suf))
        bones.append(("Pe"+suf, (lx,ly,za+0.005), (lx,ly-0.02,0.0), "Canela"+suf))
    arm = K.armature(especie["id"], bones)
    K.skin(arm, an_obj)

    # clips
    A = especie["anim"]
    S = A["S"]
    ciclo = A["ciclo_walk"]
    a = K.new_action(arm, "Walk")
    for f in range(1, ciclo+2):
        t=(f-1)/ciclo*K.TAU
        s1,c1=math.sin(t), math.cos(t)
        s2,c2=-s1,c1
        l1=max(0.0, math.sin(t+0.9))
        l2=max(0.0, math.sin(t+0.9+math.pi))
        K.key_rot(arm,"CoxaFE",f,(rad(A["coxa"])*s1,0,0))
        K.key_rot(arm,"CoxaTR",f,(rad(A["coxa"])*s1*0.88,0,0))
        K.key_rot(arm,"CoxaFD",f,(rad(A["coxa"])*s2,0,0))
        K.key_rot(arm,"CoxaTD",f,(rad(A["coxa"])*s2*0.88,0,0))
        K.key_rot(arm,"CanelaFE",f,(rad(A["canela"])*l1,0,0))
        K.key_rot(arm,"CanelaFD",f,(rad(A["canela"])*l2,0,0))
        K.key_rot(arm,"CanelaTR",f,(-rad(A["canela"])*l1*0.92,0,0))
        K.key_rot(arm,"CanelaTD",f,(-rad(A["canela"])*l2*0.92,0,0))
        K.key_rot(arm,"PeFE",f,(-rad(A["pe"])*l1,0,0))
        K.key_rot(arm,"PeFD",f,(-rad(A["pe"])*l2,0,0))
        K.key_rot(arm,"PeTR",f,(-rad(A["pe"])*l1,0,0))
        K.key_rot(arm,"PeTD",f,(-rad(A["pe"])*l2,0,0))
        K.key_loc(arm,"Corpo",f,(0,0,0.010*S*math.cos(2*t)))
        K.key_rot(arm,"Corpo",f,(rad(1.2)*math.sin(2*t+0.6),0,rad(A.get("roll",0.9))*math.sin(2*t)))
        K.key_rot(arm,"Pescoco",f,(rad(2.6)*math.cos(2*t),0,0))
        K.key_rot(arm,"Cabeca",f,(rad(-1.8)*math.cos(2*t),0,0))
        K.key_rot(arm,"Cauda",f,(rad(8)*math.sin(t+0.2),0,rad(12)*math.sin(t)))
        K.key_rot(arm,"CaudaPonta",f,(rad(10)*math.sin(t+0.6),0,rad(14)*math.sin(t+0.3)))
    K.linearize(a)

    a=K.new_action(arm,"Idle")
    C=16
    for f in range(1,C+2):
        t=(f-1)/C*K.TAU
        K.key_loc(arm,"Corpo",f,(0,0,0.004*S*math.sin(t)))
        K.key_rot(arm,"Corpo",f,(rad(0.7)*math.sin(t+1.0),0,0))
        K.key_rot(arm,"Pescoco",f,(rad(1.4)*math.sin(t+0.4),0,0))
        K.key_rot(arm,"Cabeca",f,(rad(-1.0)*math.sin(t+0.7),0,rad(6)*math.sin(t*0.6)))
        # fareja: leve virada cabeça
        K.key_rot(arm,"Cauda",f,(0,0,rad(9)*math.sin(t)))
        K.key_rot(arm,"CaudaPonta",f,(0,0,rad(11)*math.sin(t+0.7)))
        # orelha balanço leve
    K.linearize(a)

    # Lie = play bow (crouch do caramelo): peito no chão, traseiro alto, cabeça baixa, cauda balançando
    g=A["crouch"]
    a=K.new_action(arm,g["nome"])
    C=g.get("ciclo",20)
    for f in range(1,C+2):
        t=(f-1)/C*K.TAU
        K.key_rot(arm,"Pescoco",f,(rad(g["pescoco"])+math.sin(t*1.2)*0.02,0,0))
        K.key_rot(arm,"Cabeca",f,(rad(g["cabeca"])+math.sin(t*1.4)*0.015,0,0))
        K.key_loc(arm,"Corpo",f,(0,0,g.get("caida",-0.04)))
        K.key_rot(arm,"Corpo",f,(rad(g.get("inclinacao",6.0)),0,0))
        K.key_rot(arm,"CoxaFE",f,(rad(g.get("coxa_f",-38)),0,rad(g.get("abrir",4.0))))
        K.key_rot(arm,"CoxaFD",f,(rad(g.get("coxa_f",-38)),0,-rad(g.get("abrir",4.0))))
        K.key_rot(arm,"CoxaTR",f,(rad(g.get("coxa_t",-8)),0,rad(g.get("abrir",4.0))))
        K.key_rot(arm,"CoxaTD",f,(rad(g.get("coxa_t",-8)),0,-rad(g.get("abrir",4.0))))
        K.key_rot(arm,"CanelaFE",f,(rad(g.get("canela_f",42)),0,0))
        K.key_rot(arm,"CanelaFD",f,(rad(g.get("canela_f",42)),0,0))
        K.key_rot(arm,"CanelaTR",f,(rad(g.get("canela_t",32)),0,0))
        K.key_rot(arm,"CanelaTD",f,(rad(g.get("canela_t",32)),0,0))
        K.key_rot(arm,"PeFE",f,(rad(g.get("pe_f",-18)),0,0))
        K.key_rot(arm,"PeFD",f,(rad(g.get("pe_f",-18)),0,0))
        K.key_rot(arm,"PeTR",f,(rad(g.get("pe_t",-8)),0,0))
        K.key_rot(arm,"PeTD",f,(rad(g.get("pe_t",-8)),0,0))
        # cauda balançando mesmo em reverência
        K.key_rot(arm,"Cauda",f,(rad(4)*math.sin(t*1.8),0,rad(14)*math.sin(t*2.2)))
        K.key_rot(arm,"CaudaPonta",f,(rad(6)*math.sin(t*1.8+0.5),0,rad(16)*math.sin(t*2.2+0.4)))
    K.linearize(a)

    # Run extra (opcional, mas world_animal mapeia run->Walk de qq forma; fornecemos Run idêntico a Walk mais rápido)
    a=K.new_action(arm,"Run")
    for f in range(1, ciclo+2):
        t=(f-1)/ciclo*K.TAU*1.3
        s1=math.sin(t); s2=-s1
        l1=max(0.0, math.sin(t+0.9)); l2=max(0.0, math.sin(t+0.9+math.pi))
        K.key_rot(arm,"CoxaFE",f,(rad(A["coxa"]*1.15)*s1,0,0)); K.key_rot(arm,"CoxaTR",f,(rad(A["coxa"]*1.05)*s1,0,0))
        K.key_rot(arm,"CoxaFD",f,(rad(A["coxa"]*1.15)*s2,0,0)); K.key_rot(arm,"CoxaTD",f,(rad(A["coxa"]*1.05)*s2,0,0))
        K.key_rot(arm,"CanelaFE",f,(rad(A["canela"]*1.1)*l1,0,0)); K.key_rot(arm,"CanelaFD",f,(rad(A["canela"]*1.1)*l2,0,0))
        K.key_rot(arm,"Cauda",f,(rad(10)*math.sin(t),0,rad(14)*math.sin(t+0.2)))
    K.linearize(a)

    arm.animation_data.action = D.actions["Walk"]
    K.clear_pose(arm)
    glb = os.path.join(ANIMAIS, especie["id"] + ".glb")
    K.export_glb(glb, [arm, an_obj])
    print("ESPECIE:", especie["id"], "OK", os.path.getsize(glb))

if __name__=="__main__":
    build(caramelo)
