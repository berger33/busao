#!/usr/bin/env python3
# Humano original Blender 4.5 headless — substitui Quaternius por modelo do zero.
# Gera dois GLBs riggados/skinned (M/F) + animacoes, escala ~1.75m, skeleton
# compativel com runner_character.gd (pelvis, spine_01..03, neck_01, Head,
# clavicle, upperarm, lowerarm, hand, thigh, calf, foot, ball).
# Uso: tools/blender/run_bpy.sh tools/blender/build_humanos.py
import math, os
from pathlib import Path
import bpy
from mathutils import Vector

D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = str(REPO / "tools" / "blender" / "out")
OUT_HUMANOS = str(REPO / "assets" / "characters" / "humanos_originais")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(OUT_HUMANOS, exist_ok=True)

TAU = math.tau
def rad(d): return math.radians(d)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene

def novo_obj(nome, me):
    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
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

def material(nome, cor, rough=0.62, metal=0.0):
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

def caixa(nome, centro, dims):
    cx, cy, cz = centro
    dx, dy, dz = (d*0.5 for d in dims)
    v = [(cx-dx, cy-dy, cz-dz),(cx+dx, cy-dy, cz-dz),(cx+dx, cy+dy, cz-dz),(cx-dx, cy+dy, cz-dz),
         (cx-dx, cy-dy, cz+dz),(cx+dx, cy-dy, cz+dz),(cx+dx, cy+dy, cz+dz),(cx-dx, cy+dy, cz+dz)]
    f = [(0,1,2,3),(7,6,5,4),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]
    me = malha(nome, v, f)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = [(0,0),(1,0),(1,1),(0,1)][(li-poly.loop_start)%4]
    o = novo_obj(nome, me)
    try:
        sozinho(o)
        bpy.ops.object.shade_smooth()
        mm = o.modifiers.new("BevelMild", 'BEVEL')
        mm.width = 0.012
        mm.segments = 2
        mm.limit_method = 'ANGLE'
        mm.angle_limit = rad(45)
    except: pass
    return o

def pilar_z(nome, r_base, r_topo_rel, altura, seg=24): # refinado 24 segs (era 12 blocado)
    verts, faces = [], []
    rt = r_base * r_topo_rel
    for k in range(seg):
        a = k/seg*TAU
        verts.append((r_base*math.cos(a), r_base*math.sin(a), 0.0))
    for k in range(seg):
        a = k/seg*TAU
        verts.append((rt*math.cos(a), rt*math.sin(a), altura))
    for k in range(seg):
        k2=(k+1)%seg
        faces.append((k, k2, seg+k2, seg+k))
    cb=len(verts); verts.append((0,0,0))
    ct=len(verts); verts.append((0,0,altura))
    for k in range(seg):
        k2=(k+1)%seg
        faces.append((cb,k2,k))
        faces.append((ct, seg+k, seg+k2))
    me = malha(nome, verts, faces)
    o = novo_obj(nome, me)
    return o

def elipsoide_bl(nome, centro, raios, seg=3): # ico 3 niveis (era 2)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=seg, radius=1.0, location=centro)
    o = bpy.context.active_object
    o.name = nome
    sozinho(o)
    o.scale = raios
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mm=o.modifiers.new("Subd",'SUBSURF'); mm.levels=mm.render_levels=1
    return o

def join_parts(partes):
    for o,_ in partes:
        sozinho(o)
        while o.modifiers:
            bpy.ops.object.modifier_apply(modifier=o.modifiers[0].name)
    contagens=[len(o.data.vertices) for o,_ in partes]
    sozinho(partes[0][0])
    for o,_ in partes:
        o.select_set(True)
    bpy.context.view_layer.objects.active=partes[0][0]
    bpy.ops.object.join()
    corpo=bpy.context.active_object
    try:
        sozinho(corpo)
        bpy.ops.object.shade_smooth()
        for poly in corpo.data.polygons:
            poly.use_smooth = True
    except: pass
    total=sum(contagens)
    assert len(corpo.data.vertices)==total, "join alterou vertices"
    print("VERTICES:", total)
    idx=0
    for (_,grupo), n in zip(partes, contagens):
        vg=corpo.vertex_groups.get(grupo) or corpo.vertex_groups.new(name=grupo)
        vg.add(list(range(idx, idx+n)), 1.0, 'REPLACE')
        idx+=n
    return corpo

def armature_humano(nome):
    arm_data=D.armatures.new(nome+"Rig")
    arm=D.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    sozinho(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    def osso(n, head, tail, parent=None):
        b=arm_data.edit_bones.new(n)
        b.head=head; b.tail=tail; b.roll=0
        if parent:
            b.parent=arm_data.edit_bones[parent]
        return b
    # pelvis root
    osso("pelvis", (0,0,0.92), (0,0,1.05))
    osso("spine_01", (0,0,1.05), (0,0,1.18), "pelvis")
    osso("spine_02", (0,0,1.18), (0,0,1.32), "spine_01")
    osso("spine_03", (0,0,1.32), (0,0,1.45), "spine_02")
    osso("neck_01", (0,0,1.45), (0,0,1.545), "spine_03")
    osso("Head", (0,0,1.545), (0,0,1.75), "neck_01")
    # claviculas
    osso("clavicle_l", (-0.02,0,1.40), (-0.14,0,1.40), "spine_03")
    osso("clavicle_r", ( 0.02,0,1.40), ( 0.14,0,1.40), "spine_03")
    # bracos
    osso("upperarm_l", (-0.14,0,1.40), (-0.38,0,1.40), "clavicle_l")
    osso("lowerarm_l", (-0.38,0,1.40), (-0.60,0,1.40), "upperarm_l")
    osso("hand_l", (-0.60,0,1.40), (-0.68,0,1.40), "lowerarm_l")
    osso("upperarm_r", ( 0.14,0,1.40), ( 0.38,0,1.40), "clavicle_r")
    osso("lowerarm_r", ( 0.38,0,1.40), ( 0.60,0,1.40), "upperarm_r")
    osso("hand_r", ( 0.60,0,1.40), ( 0.68,0,1.40), "lowerarm_r")
    # dedos simplificados (para REGION_BONES nao falhar)
    for lado, sx in (("l", -0.68), ("r", 0.68)):
        for nome_dedo in ("thumb","index","middle","ring","pinky"):
            for i in (1,2,3):
                n0 = f"{nome_dedo}_0{i}_{lado}"
                head = (sx, 0.0 - (0.02 if nome_dedo=="thumb" else 0.0), 1.40 - 0.015*i)
                tail = (sx + (0.02 if lado=="r" else -0.02), 0.0, 1.40 -0.015*(i+0.5))
                parent = f"hand_{lado}" if i==1 else f"{nome_dedo}_0{i-1}_{lado}"
                try:
                    osso(n0, head, tail, parent)
                except: pass
    # pernas
    osso("thigh_l", (-0.09,0,0.92), (-0.09,0,0.50), "pelvis")
    osso("calf_l", (-0.09,0,0.50), (-0.09,0,0.10), "thigh_l")
    osso("foot_l", (-0.09,0,0.10), (-0.09,-0.09,0.03), "calf_l")
    osso("ball_l", (-0.09,-0.09,0.03), (-0.09,-0.16,0.025), "foot_l")
    osso("thigh_r", ( 0.09,0,0.92), ( 0.09,0,0.50), "pelvis")
    osso("calf_r", ( 0.09,0,0.50), ( 0.09,0,0.10), "thigh_r")
    osso("foot_r", ( 0.09,0,0.10), ( 0.09,-0.09,0.03), "calf_r")
    osso("ball_r", ( 0.09,-0.09,0.03), ( 0.09,-0.16,0.025), "foot_r")
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, mesh):
    mesh.parent=arm
    mod=mesh.modifiers.new("Skin",'ARMATURE')
    mod.object=arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.rotation_mode='XYZ'
    bpy.ops.object.mode_set(mode='OBJECT')

def key_rot(arm, bn, frame, euler):
    pb=arm.pose.bones[bn]
    pb.rotation_euler=euler
    pb.keyframe_insert('rotation_euler', frame=frame)

def key_loc(arm, bn, frame, loc):
    pb=arm.pose.bones[bn]
    pb.location=loc
    pb.keyframe_insert('location', frame=frame)

def clear_pose(arm):
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')

def new_action(arm, nome):
    a=D.actions.new(nome)
    arm.animation_data_create()
    arm.animation_data.action=a
    return a

def linearize(act):
    # Blender 4.5: act.fcurves ; 5.0: action.layers -> strips -> channelbags -> fcurves
    fcurves = []
    if hasattr(act, "fcurves"):
        try:
            fcurves = list(act.fcurves)
        except: fcurves = []
    if not fcurves and hasattr(act, "layers"):
        try:
            for layer in act.layers:
                for strip in layer.strips:
                    # Blender 5: strip.channelbags
                    if hasattr(strip, "channelbags"):
                        for bag in strip.channelbags:
                            fcurves.extend(list(bag.fcurves))
                    elif hasattr(strip, "fcurves"):
                        fcurves.extend(list(strip.fcurves))
                    elif hasattr(strip, "action"):
                        # fallback
                        pass
        except Exception as e:
            print("linearize fallback layers failed", e)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation='LINEAR'

def build_one(is_male, out_path):
    scene=reset()
    # materiais — nomes mantidos para tintagem existir
    # pele com nome QuaterniusSkin para reaproveitar _apply_skin_tint
    if is_male:
        cor_pele=(0.82,0.62,0.48)
        cor_cabelo=(0.18,0.13,0.11)
        cor_camisa=(0.85,0.22,0.22)  # vermelho vivo
        cor_calca=(0.16,0.24,0.42)
        cor_sapato=(0.18,0.15,0.12)
        largura_ombro=0.23
        largura_quadril=0.17
        peito_extra=0.025
    else:
        cor_pele=(0.80,0.60,0.47)
        cor_cabelo=(0.22,0.15,0.18)
        cor_camisa=(0.92,0.38,0.62)
        cor_calca=(0.32,0.28,0.55)
        cor_sapato=(0.85,0.72,0.22)
        largura_ombro=0.205
        largura_quadril=0.21 # quadril mais largo (era 0.185 quadrado)
        peito_extra=0.045
    # nomes: QuaterniusSkin para pele, hair para cabelo, etc para palette detectar
    m_pele=material("QuaterniusSkin", cor_pele, 0.62, 0.0)
    m_pele.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*cor_pele,1)
    # para tintagem funcionar, manter resource_name com QuaterniusSkin
    m_pele.name="QuaterniusSkin"
    m_cabelo=material("Hair", cor_cabelo, 0.72, 0.0); m_cabelo.name="Hair"
    m_camisa=material("Camisa", cor_camisa, 0.68, 0.0); m_camisa.name="Camisa"
    m_calca=material("Calca", cor_calca, 0.70, 0.0); m_calca.name="Calca"
    m_sapato=material("Sapato", cor_sapato, 0.55, 0.15); m_sapato.name="Sapato"
    m_olho_branco=material("OlhoBranco", (0.96,0.96,0.94), 0.25)
    m_olho_iris=material("OlhoIris", (0.35,0.22,0.12), 0.15)
    m_labio=material("Labio", (0.68,0.32,0.32), 0.45)

    partes=[]

    # --- PELVIS / quadril (calca)
    o=caixa("Pelvis", (0,0,0.985), (largura_quadril*2+0.08, 0.18, 0.16))
    o.data.materials.append(m_calca)
    partes.append((o,"pelvis"))
    # spine01 cintura baixa (camisa cobre parcialmente)
    o=caixa("CinturaBaixa", (0,0,1.115), (0.34,0.17,0.14))
    o.data.materials.append(m_camisa)
    partes.append((o,"spine_01"))
    # spine02 peito medio
    o=caixa("PeitoMedio", (0,0,1.25), (0.38+peito_extra,0.18,0.14))
    o.data.materials.append(m_camisa)
    partes.append((o,"spine_02"))
    # spine03 ombros
    o=caixa("Ombros", (0,0,1.385), (largura_ombro*2+0.04,0.19,0.15))
    o.data.materials.append(m_camisa)
    partes.append((o,"spine_03"))
    # pescoco
    o=pilar_z("Pescoco", 0.055, 0.045, 0.095)
    sozinho(o); o.location=(0,0,1.45); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    o.data.materials.append(m_pele)
    partes.append((o,"neck_01"))
    # cabeca
    o=elipsoide_bl("Cabeca", (0,0,1.625), (0.115,0.12,0.135), seg=2)
    o.data.materials.append(m_pele)
    partes.append((o,"Head"))
    # queixo/labio leve?
    # olhos
    for sx in (-0.038, 0.038):
        oo=elipsoide_bl(f"OlhoBranco_{sx}", (sx, -0.095, 1.635), (0.028,0.012,0.018), seg=1)
        oo.data.materials.append(m_olho_branco)
        partes.append((oo,"Head"))
        oo2=elipsoide_bl(f"Iris_{sx}", (sx, -0.105, 1.635), (0.012,0.006,0.012), seg=1)
        oo2.data.materials.append(m_olho_iris)
        partes.append((oo2,"Head"))
    # sobrancelha simples como faixa
    # cabelo
    if is_male:
        # cabelo curto buzz - capa superior
        oc=elipsoide_bl("CabeloTopo", (0,0,1.70), (0.12,0.125,0.085), seg=1)
        oc.data.materials.append(m_cabelo)
        partes.append((oc,"Head"))
        # laterais curtas
        for sx in (-0.10, 0.10):
            oc2=elipsoide_bl(f"CabeloLado_{sx}", (sx,0,1.62), (0.025,0.04,0.07), seg=1)
            oc2.data.materials.append(m_cabelo)
            partes.append((oc2,"Head"))
    else:
        oc=elipsoide_bl("CabeloTopo", (0,0,1.705), (0.125,0.13,0.09), seg=1)
        oc.data.materials.append(m_cabelo)
        partes.append((oc,"Head"))
        # franja e laterais longas
        for sx in (-0.11, 0.11):
            oc2=elipsoide_bl(f"CabeloLongo_{sx}", (sx, 0.015, 1.52), (0.045,0.055,0.22), seg=1)
            oc2.data.materials.append(m_cabelo)
            partes.append((oc2,"Head"))
            # coque/rabo?
        oc3=elipsoide_bl("CabeloAtras", (0,0.08,1.55), (0.11,0.07,0.18), seg=1)
        oc3.data.materials.append(m_cabelo)
        partes.append((oc3,"Head"))

    # bracos — clavicula/ombro caps
    for sx, lado in ((-1, "l"), (1, "r")):
        cx = sx * (largura_ombro+0.02)
        # ombro esférico camisa
        oo=elipsoide_bl(f"OmbroCap_{lado}", (cx,0,1.40), (0.065,0.065,0.065), seg=1)
        oo.data.materials.append(m_camisa)
        partes.append((oo,f"clavicle_{lado}"))
        # upperarm camisa manga curta
        o=pilar_z(f"BracoSup_{lado}", 0.055, 0.045, 0.24)
        sozinho(o); o.location=(cx,0,1.40); o.rotation_euler=(0, rad(90 if sx>0 else -90), 0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        # after rotate, move to midpoint? pillar base at origin; after rotate Y 90, Z becomes X. Base at shoulder, length along X. Good.
        # But need to offset: pillar base at shoulder, so location stays at shoulder.
        o.data.materials.append(m_camisa)
        partes.append((o,f"upperarm_{lado}"))
        # lowerarm pele
        o2=pilar_z(f"Antebraco_{lado}", 0.042, 0.032, 0.22)
        sozinho(o2); o2.location=(sx*0.38,0,1.40); o2.rotation_euler=(0, rad(90 if sx>0 else -90),0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        o2.data.materials.append(m_pele)
        partes.append((o2,f"lowerarm_{lado}"))
        # mao
        o3=elipsoide_bl(f"Mao_{lado}", (sx*0.64,0,1.40), (0.045,0.025,0.04), seg=1)
        o3.data.materials.append(m_pele)
        partes.append((o3,f"hand_{lado}"))
        # dedos simples como caixas finas
        for i, dz in enumerate([-0.02,0,0.02]):
            o4=caixa(f"Dedo_{lado}_{i}", (sx*0.69, -0.045, 1.40+dz), (0.015,0.03,0.015))
            o4.data.materials.append(m_pele)
            partes.append((o4,f"hand_{lado}"))

    # pernas
    for sx, lado in ((-1,"l"),(1,"r")):
        cx=sx*0.09
        # coxa calca
        o=pilar_z(f"Coxa_{lado}", 0.078, 0.065, 0.42)
        sozinho(o); o.location=(cx,0,0.50); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        # pillar base at 0, top at 0.42; location at 0.50 puts base at 0.50 top at 0.92 — correto
        o.data.materials.append(m_calca)
        partes.append((o,f"thigh_{lado}"))
        # panturrilha calca
        o2=pilar_z(f"Panturrilha_{lado}", 0.065, 0.045, 0.40)
        sozinho(o2); o2.location=(cx,0,0.10); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        o2.data.materials.append(m_calca)
        partes.append((o2,f"calf_{lado}"))
        # pe/sapato
        # sola
        o3=caixa(f"Sapato_{lado}", (cx, -0.07, 0.035), (0.12,0.24,0.07))
        o3.data.materials.append(m_sapato)
        partes.append((o3,f"foot_{lado}"))
        # palmilha/bico
        o4=caixa(f"PeitoPe_{lado}", (cx, -0.09, 0.055), (0.11,0.18,0.04))
        o4.data.materials.append(m_sapato)
        partes.append((o4,f"ball_{lado}"))

    corpo=join_parts(partes)
    arm=armature_humano("Humano")
    skin(arm, corpo)
    # centraliza? mart keep ground at 0
    # armature position at origin, mesh already at correct height
    # criar animacoes
    scene.frame_start=1
    scene.frame_end=48
    # ensure pose mode
    def act_idle():
        a=new_action(arm,"Idle_Loop")
        for f in (1,12,24,36,48):
            t=(f-1)/48*TAU
            clear_pose(arm)
            # leve resp e peso
            key_rot(arm,"spine_02",f,(rad(1.2)*math.sin(t),0, rad(0.6)*math.cos(t*0.5)))
            key_rot(arm,"spine_03",f,(rad(0.8)*math.sin(t),0,0))
            key_rot(arm,"Head",f,(rad(1.0)*math.sin(t*0.7), rad(0.6)*math.cos(t),0))
            key_rot(arm,"upperarm_l",f,(rad(-4)*math.sin(t),0,0))
            key_rot(arm,"upperarm_r",f,(rad(4)*math.sin(t),0,0))
            key_loc(arm,"pelvis",f,(0,0,0.004*math.sin(t)))
        linearize(a)
        return a
    def act_walk():
        a=new_action(arm,"Walk_Loop")
        C=24
        for f in range(1,C+2):
            t=(f-1)/C*TAU
            s=math.sin(t); c=math.cos(t)
            clear_pose(arm)
            key_rot(arm,"thigh_l",f,(rad(28)*s,0,0))
            key_rot(arm,"thigh_r",f,(rad(-28)*s,0,0))
            key_rot(arm,"calf_l",f,(rad(42)*max(0, math.sin(t+0.9)),0,0))
            key_rot(arm,"calf_r",f,(rad(42)*max(0, math.sin(t+0.9+math.pi)),0,0))
            key_rot(arm,"foot_l",f,(rad(-14)*max(0, math.sin(t+0.9)),0,0))
            key_rot(arm,"foot_r",f,(rad(-14)*max(0, math.sin(t+0.9+math.pi)),0,0))
            key_rot(arm,"upperarm_l",f,(rad(-22)*s,0,0))
            key_rot(arm,"upperarm_r",f,(rad(22)*s,0,0))
            key_rot(arm,"lowerarm_l",f,(rad(-8)*s,0,0))
            key_rot(arm,"lowerarm_r",f,(rad(8)*s,0,0))
            key_rot(arm,"spine_02",f,(0, rad(1.2)*s,0))
            key_loc(arm,"pelvis",f,(0,0,0.006*c))
        linearize(a)
        return a
    def act_sprint():
        a=new_action(arm,"Sprint_Loop")
        C=16
        for f in range(1,C+2):
            t=(f-1)/C*TAU
            s=math.sin(t); c=math.cos(t)
            clear_pose(arm)
            key_rot(arm,"thigh_l",f,(rad(38)*s,0,0))
            key_rot(arm,"thigh_r",f,(rad(-38)*s,0,0))
            key_rot(arm,"calf_l",f,(rad(58)*max(0, math.sin(t+0.8)),0,0))
            key_rot(arm,"calf_r",f,(rad(58)*max(0, math.sin(t+0.8+math.pi)),0,0))
            key_rot(arm,"upperarm_l",f,(rad(-42)*s,0,0))
            key_rot(arm,"upperarm_r",f,(rad(42)*s,0,0))
            key_rot(arm,"lowerarm_l",f,(rad(-18)*s,0,0))
            key_rot(arm,"lowerarm_r",f,(rad(18)*s,0,0))
            key_rot(arm,"spine_02",f,(rad(4)*c,0,0))
            key_loc(arm,"pelvis",f,(0,0,0.009*c))
        linearize(a)
        return a
    def act_jump():
        a=new_action(arm,"Jump_Loop")
        # 1 crouch, 6 apex, 10 land
        keys=[(1, -18, -34, 22),(4, -26, -46, 28),(7, 18, 12, -8),(10, -10, -20, 10)]
        for f, th, cf, af in keys:
            clear_pose(arm)
            # need to key at specific frame; we simulate via manual
            pass
        # simplificado: loop basico
        for f in (1,6,10):
            t=(f-1)/10
            clear_pose(arm)
            crouch = -22*math.sin(math.pi*t) if t<0.5 else -8*math.sin(math.pi*(1-t))
            key_rot(arm,"thigh_l",f,(rad(crouch),0,0))
            key_rot(arm,"thigh_r",f,(rad(crouch),0,0))
            key_rot(arm,"calf_l",f,(rad(-crouch*1.4),0,0))
            key_rot(arm,"calf_r",f,(rad(-crouch*1.4),0,0))
            key_rot(arm,"upperarm_l",f,(rad(20+ 12*t),0,0))
            key_rot(arm,"upperarm_r",f,(rad(20+ 12*t),0,0))
            key_loc(arm,"pelvis",f,(0,0,0.02*math.sin(math.pi*t)))
        linearize(D.actions["Jump_Loop"])
        return D.actions["Jump_Loop"]
    def act_crouch_idle():
        a=new_action(arm,"Crouch_Idle_Loop")
        for f in (1,24,48):
            t=(f-1)/48*TAU
            clear_pose(arm)
            key_rot(arm,"thigh_l",f,(rad(-46),0,0))
            key_rot(arm,"thigh_r",f,(rad(-46),0,0))
            key_rot(arm,"calf_l",f,(rad(68),0,0))
            key_rot(arm,"calf_r",f,(rad(68),0,0))
            key_rot(arm,"spine_02",f,(rad(18)+rad(1.2)*math.sin(t),0,0))
            key_rot(arm,"upperarm_l",f,(rad(-12),0,0))
            key_rot(arm,"upperarm_r",f,(rad(-12),0,0))
        linearize(a)
        return a
    def act_crouch_fwd():
        a=new_action(arm,"Crouch_Fwd_Loop")
        C=20
        for f in range(1,C+2):
            t=(f-1)/C*TAU
            s=math.sin(t); c=math.cos(t)
            clear_pose(arm)
            key_rot(arm,"thigh_l",f,(rad(-42)+rad(14)*s,0,0))
            key_rot(arm,"thigh_r",f,(rad(-42)-rad(14)*s,0,0))
            key_rot(arm,"calf_l",f,(rad(60)+rad(12)*max(0, math.sin(t+0.7)),0,0))
            key_rot(arm,"calf_r",f,(rad(60)+rad(12)*max(0, math.sin(t+0.7+math.pi)),0,0))
            key_rot(arm,"upperarm_l",f,(rad(-18)*s,0,0))
            key_rot(arm,"upperarm_r",f,(rad(18)*s,0,0))
            key_loc(arm,"pelvis",f,(0,0,0.004*c))
        linearize(a)
        return a

    act_idle()
    act_walk()
    act_sprint()
    # ensure Jump etc after Walk/Sprint keep actions
    # create jump etc manually with proper key loops
    # Jump simple
    a=new_action(arm,"Jump_Loop")
    for f, cro in [(1,-28),(4,-44),(7,14),(10,-18)]:
        clear_pose(arm)
        key_rot(arm,"thigh_l",f,(rad(cro),0,0)); key_rot(arm,"thigh_r",f,(rad(cro),0,0))
        key_rot(arm,"calf_l",f,(rad(-cro*1.25),0,0)); key_rot(arm,"calf_r",f,(rad(-cro*1.25),0,0))
        key_rot(arm,"upperarm_l",f,(rad(22),0,0)); key_rot(arm,"upperarm_r",f,(rad(22),0,0))
        key_loc(arm,"pelvis",f,(0,0,0.03 if f==7 else 0))
    linearize(a)
    act_crouch_idle()
    act_crouch_fwd()

    # export
    # ensure selection
    bpy.ops.object.select_all(action='DESELECT')
    corpo.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active=arm
    # GLB com animacoes
    bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB', export_apply=True, export_animations=True, export_skins=True, export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False, export_animation_mode='ACTIONS', use_selection=True)
    print("PRONTO:", out_path, os.path.getsize(out_path))
    # blend preview
    blend_path = os.path.join(OUT_DIR, ("humano_%s.blend"%("M" if is_male else "F")))
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    return out_path

if __name__=="__main__":
    for is_male, nome in [(True,"Humano_M.glb"),(False,"Humano_F.glb")]:
        build_one(is_male, os.path.join(OUT_HUMANOS, nome))
        # also also generate .res placeholder? We'll generate later via Godot? For validator we keep quaternius .res, so not needed here.
    print("HUMANOS OK")

