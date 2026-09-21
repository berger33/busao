#!/usr/bin/env python3
# Humano original Blender 4.5 headless — substitui Quaternius por modelo do zero.
# Gera dois GLBs riggados/skinned (M/F) + animacoes, escala ~1.75m, skeleton
# compativel com runner_character.gd (pelvis, spine_01..03, neck_01, Head,
# clavicle, upperarm, lowerarm, hand, thigh, calf, foot, ball).
# Uso: tools/blender/run_bpy.sh tools/blender/build_humanos.py
import math, os
from pathlib import Path
import bpy

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

def material(nome, cor, rough=0.62, metal=0.0):
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

def sozinho(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o

def loft_tube(nome, rings, mat=None, close_bottom=False, close_top=False):
    me = D.meshes.new(nome)
    verts, faces = [], []
    seg = rings[0][5]
    n_rings = len(rings)
    for i, (cx, cy, cz, rx, ry, _) in enumerate(rings):
        for k in range(seg):
            a = k / seg * TAU
            x = cx + rx * math.cos(a)
            y = cy + ry * math.sin(a)
            z = cz
            verts.append((x, y, z))
            
    for i in range(n_rings - 1):
        v0 = i * seg
        v1 = (i + 1) * seg
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((v0 + k, v0 + k_next, v1 + k_next, v1 + k))
            
    if close_bottom:
        cb = len(verts)
        verts.append((rings[0][0], rings[0][1], rings[0][2]))
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((cb, k, k_next))
            
    if close_top:
        ct = len(verts)
        verts.append((rings[-1][0], rings[-1][1], rings[-1][2]))
        top_start = (n_rings - 1) * seg
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((ct, top_start + k_next, top_start + k))

    me.from_pydata(verts, [], faces)
    me.update()
    
    uv_layer = me.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    face_idx = 0
    for i in range(n_rings - 1):
        v_low = i / max(1, n_rings - 1)
        v_high = (i + 1) / max(1, n_rings - 1)
        for k in range(seg):
            u_low = k / seg
            u_high = (k + 1) / seg
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (u_low, v_low)
            uv_data[poly.loop_indices[1]].uv = (u_high, v_low)
            uv_data[poly.loop_indices[2]].uv = (u_high, v_high)
            uv_data[poly.loop_indices[3]].uv = (u_low, v_high)
            face_idx += 1
            
    if close_bottom:
        for k in range(seg):
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (0.5, 0.0)
            uv_data[poly.loop_indices[1]].uv = (k / seg, 0.0)
            uv_data[poly.loop_indices[2]].uv = ((k + 1) / seg, 0.0)
            face_idx += 1
            
    if close_top:
        for k in range(seg):
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (0.5, 1.0)
            uv_data[poly.loop_indices[1]].uv = ((k + 1) / seg, 1.0)
            uv_data[poly.loop_indices[2]].uv = (k / seg, 1.0)
            face_idx += 1

    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o

def loft_limb_x(nome, rings, mat=None, close_start=False, close_end=False):
    me = D.meshes.new(nome)
    verts, faces = [], []
    seg = rings[0][5]
    n_rings = len(rings)
    for i, (cx, cy, cz, ry, rz, _) in enumerate(rings):
        for k in range(seg):
            a = k / seg * TAU
            x = cx
            y = cy + ry * math.cos(a)
            z = cz + rz * math.sin(a)
            verts.append((x, y, z))
            
    for i in range(n_rings - 1):
        v0 = i * seg
        v1 = (i + 1) * seg
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((v0 + k, v0 + k_next, v1 + k_next, v1 + k))
            
    if close_start:
        cb = len(verts)
        verts.append((rings[0][0], rings[0][1], rings[0][2]))
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((cb, k, k_next))
            
    if close_end:
        ct = len(verts)
        verts.append((rings[-1][0], rings[-1][1], rings[-1][2]))
        top_start = (n_rings - 1) * seg
        for k in range(seg):
            k_next = (k + 1) % seg
            faces.append((ct, top_start + k_next, top_start + k))

    me.from_pydata(verts, [], faces)
    me.update()
    
    uv_layer = me.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    face_idx = 0
    for i in range(n_rings - 1):
        v_low = i / max(1, n_rings - 1)
        v_high = (i + 1) / max(1, n_rings - 1)
        for k in range(seg):
            u_low = k / seg
            u_high = (k + 1) / seg
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (u_low, v_low)
            uv_data[poly.loop_indices[1]].uv = (u_high, v_low)
            uv_data[poly.loop_indices[2]].uv = (u_high, v_high)
            uv_data[poly.loop_indices[3]].uv = (u_low, v_high)
            face_idx += 1

    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o

def elipsoide_uv(nome, centro, raios, mat=None, u_seg=16, v_seg=12):
    me = D.meshes.new(nome)
    verts, faces = [], []
    cx, cy, cz = centro
    rx, ry, rz = raios
    
    verts.append((cx, cy, cz - rz))
    for j in range(1, v_seg):
        phi = -math.pi/2.0 + math.pi * j / v_seg
        z = cz + rz * math.sin(phi)
        cos_phi = math.cos(phi)
        for i in range(u_seg):
            theta = i / u_seg * TAU
            x = cx + rx * cos_phi * math.cos(theta)
            y = cy + ry * cos_phi * math.sin(theta)
            verts.append((x, y, z))
    verts.append((cx, cy, cz + rz))
    
    # Polo sul
    for i in range(u_seg):
        i_next = (i + 1) % u_seg
        faces.append((0, 1 + i_next, 1 + i))
        
    # Aneis intermediarios
    for j in range(v_seg - 2):
        r0 = 1 + j * u_seg
        r1 = 1 + (j + 1) * u_seg
        for i in range(u_seg):
            i_next = (i + 1) % u_seg
            faces.append((r0 + i, r0 + i_next, r1 + i_next, r1 + i))
            
    # Polo norte
    top_idx = len(verts) - 1
    r_last = 1 + (v_seg - 2) * u_seg
    for i in range(u_seg):
        i_next = (i + 1) % u_seg
        faces.append((top_idx, r_last + i, r_last + i_next))

    me.from_pydata(verts, [], faces)
    me.update()
    
    uv_layer = me.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    face_idx = 0
    # Polo sul UV
    for i in range(u_seg):
        poly = me.polygons[face_idx]
        uv_data[poly.loop_indices[0]].uv = (0.5, 0.0)
        uv_data[poly.loop_indices[1]].uv = ((i + 1) / u_seg, 1.0 / v_seg)
        uv_data[poly.loop_indices[2]].uv = (i / u_seg, 1.0 / v_seg)
        face_idx += 1
        
    for j in range(v_seg - 2):
        v_low = (j + 1) / v_seg
        v_high = (j + 2) / v_seg
        for i in range(u_seg):
            u_low = i / u_seg
            u_high = (i + 1) / u_seg
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (u_low, v_low)
            uv_data[poly.loop_indices[1]].uv = (u_high, v_low)
            uv_data[poly.loop_indices[2]].uv = (u_high, v_high)
            uv_data[poly.loop_indices[3]].uv = (u_low, v_high)
            face_idx += 1
            
    for i in range(u_seg):
        poly = me.polygons[face_idx]
        uv_data[poly.loop_indices[0]].uv = (0.5, 1.0)
        uv_data[poly.loop_indices[1]].uv = (i / u_seg, (v_seg - 1) / v_seg)
        uv_data[poly.loop_indices[2]].uv = ((i + 1) / u_seg, (v_seg - 1) / v_seg)
        face_idx += 1

    o = D.objects.new(nome, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o

def join_parts(partes):
    for o, _ in partes:
        sozinho(o)
        while o.modifiers:
            bpy.ops.object.modifier_apply(modifier=o.modifiers[0].name)
    contagens = [len(o.data.vertices) for o, _ in partes]
    for o, _ in partes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = partes[0][0]
    bpy.ops.object.join()
    corpo = bpy.context.active_object
    try:
        sozinho(corpo)
        bpy.ops.object.shade_smooth()
        for poly in corpo.data.polygons:
            poly.use_smooth = True
    except: pass
    total = sum(contagens)
    assert len(corpo.data.vertices) == total
    idx = 0
    for (_, grupo), n in zip(partes, contagens):
        vg = corpo.vertex_groups.get(grupo) or corpo.vertex_groups.new(name=grupo)
        vg.add(list(range(idx, idx + n)), 1.0, 'REPLACE')
        idx += n
    _blend_joint_weights(corpo)
    return corpo

def _blend_joint_weights(corpo):
    vgs = {vg.name: vg for vg in corpo.vertex_groups}
    for v in corpo.data.vertices:
        co = v.co
        z = co.z
        ax = abs(co.x)
        # Joelho (Z entre 0.44 e 0.56)
        if 0.44 <= z <= 0.56:
            t = (z - 0.44) / 0.12
            lado = "l" if co.x < 0 else "r"
            vg_thigh = vgs.get(f"thigh_{lado}")
            vg_calf = vgs.get(f"calf_{lado}")
            if vg_thigh and vg_calf:
                vg_calf.add([v.index], 1.0 - t, 'ADD')
                vg_thigh.add([v.index], t, 'ADD')
        # Tornozelo (Z entre 0.08 e 0.12)
        elif 0.08 <= z <= 0.12:
            t = (z - 0.08) / 0.04
            lado = "l" if co.x < 0 else "r"
            vg_calf = vgs.get(f"calf_{lado}")
            vg_foot = vgs.get(f"foot_{lado}")
            if vg_calf and vg_foot:
                vg_foot.add([v.index], 1.0 - t, 'ADD')
                vg_calf.add([v.index], t, 'ADD')
        # Cotovelo (|X| entre 0.34 e 0.42, Z ~ 1.40)
        elif 1.30 <= z <= 1.50 and 0.34 <= ax <= 0.42:
            t = (ax - 0.34) / 0.08
            lado = "l" if co.x < 0 else "r"
            vg_upper = vgs.get(f"upperarm_{lado}")
            vg_lower = vgs.get(f"lowerarm_{lado}")
            if vg_upper and vg_lower:
                vg_upper.add([v.index], 1.0 - t, 'ADD')
                vg_lower.add([v.index], t, 'ADD')
        # Cintura baixa (Z entre 1.02 e 1.10)
        elif 1.02 <= z <= 1.10:
            t = (z - 1.02) / 0.08
            vg_pelvis = vgs.get("pelvis")
            vg_spine1 = vgs.get("spine_01")
            if vg_pelvis and vg_spine1:
                vg_pelvis.add([v.index], 1.0 - t, 'ADD')
                vg_spine1.add([v.index], t, 'ADD')

def armature_humano(nome):
    arm_data = D.armatures.new(nome + "Rig")
    arm = D.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    sozinho(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    def osso(n, head, tail, parent=None):
        b = arm_data.edit_bones.new(n)
        b.head = head; b.tail = tail; b.roll = 0
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b
    osso("pelvis", (0, 0, 0.92), (0, 0, 1.05))
    osso("spine_01", (0, 0, 1.05), (0, 0, 1.18), "pelvis")
    osso("spine_02", (0, 0, 1.18), (0, 0, 1.32), "spine_01")
    osso("spine_03", (0, 0, 1.32), (0, 0, 1.45), "spine_02")
    osso("neck_01", (0, 0, 1.45), (0, 0, 1.545), "spine_03")
    osso("Head", (0, 0, 1.545), (0, 0, 1.75), "neck_01")
    osso("clavicle_l", (-0.02, 0, 1.40), (-0.14, 0, 1.40), "spine_03")
    osso("clavicle_r", (0.02, 0, 1.40), (0.14, 0, 1.40), "spine_03")
    osso("upperarm_l", (-0.14, 0, 1.40), (-0.38, 0, 1.40), "clavicle_l")
    osso("lowerarm_l", (-0.38, 0, 1.40), (-0.60, 0, 1.40), "upperarm_l")
    osso("hand_l", (-0.60, 0, 1.40), (-0.68, 0, 1.40), "lowerarm_l")
    osso("upperarm_r", (0.14, 0, 1.40), (0.38, 0, 1.40), "clavicle_r")
    osso("lowerarm_r", (0.38, 0, 1.40), (0.60, 0, 1.40), "upperarm_r")
    osso("hand_r", (0.60, 0, 1.40), (0.68, 0, 1.40), "lowerarm_r")
    for lado, sx in (("l", -0.68), ("r", 0.68)):
        for nome_dedo in ("thumb", "index", "middle", "ring", "pinky"):
            for i in (1, 2, 3):
                n0 = f"{nome_dedo}_0{i}_{lado}"
                head = (sx, 0.0 - (0.02 if nome_dedo == "thumb" else 0.0), 1.40 - 0.015 * i)
                tail = (sx + (0.02 if lado == "r" else -0.02), 0.0, 1.40 - 0.015 * (i + 0.5))
                parent = f"hand_{lado}" if i == 1 else f"{nome_dedo}_0{i-1}_{lado}"
                try:
                    osso(n0, head, tail, parent)
                except: pass
    osso("thigh_l", (-0.09, 0, 0.92), (-0.09, 0, 0.50), "pelvis")
    osso("calf_l", (-0.09, 0, 0.50), (-0.09, 0, 0.10), "thigh_l")
    osso("foot_l", (-0.09, 0, 0.10), (-0.09, -0.09, 0.03), "calf_l")
    osso("ball_l", (-0.09, -0.09, 0.03), (-0.09, -0.16, 0.025), "foot_l")
    osso("thigh_r", (0.09, 0, 0.92), (0.09, 0, 0.50), "pelvis")
    osso("calf_r", (0.09, 0, 0.50), (0.09, 0, 0.10), "thigh_r")
    osso("foot_r", (0.09, 0, 0.10), (0.09, -0.09, 0.03), "calf_r")
    osso("ball_r", (0.09, -0.09, 0.03), (0.09, -0.16, 0.025), "foot_r")
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, mesh):
    mesh.parent = arm
    mod = mesh.modifiers.new("Skin", 'ARMATURE')
    mod.object = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    bpy.ops.object.mode_set(mode='OBJECT')

def key_rot(arm, bn, frame, euler):
    pb = arm.pose.bones[bn]
    pb.rotation_euler = euler
    pb.keyframe_insert('rotation_euler', frame=frame)

def key_loc(arm, bn, frame, loc):
    pb = arm.pose.bones[bn]
    pb.location = loc
    pb.keyframe_insert('location', frame=frame)

def clear_pose(arm):
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')

def new_action(arm, nome):
    a = D.actions.new(nome)
    arm.animation_data_create()
    arm.animation_data.action = a
    return a

def linearize(act):
    fcurves = []
    if hasattr(act, "fcurves"):
        try: fcurves = list(act.fcurves)
        except: fcurves = []
    if not fcurves and hasattr(act, "layers"):
        try:
            for layer in act.layers:
                for strip in layer.strips:
                    if hasattr(strip, "channelbags"):
                        for bag in strip.channelbags:
                            fcurves.extend(list(bag.fcurves))
                    elif hasattr(strip, "fcurves"):
                        fcurves.extend(list(strip.fcurves))
        except: pass
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

def build_one(is_male, out_path):
    scene = reset()
    if is_male:
        cor_pele = (0.82, 0.62, 0.48)
        cor_cabelo = (0.14, 0.10, 0.08)
        cor_camisa = (0.85, 0.22, 0.22)
        cor_calca = (0.15, 0.18, 0.26)
        cor_sapato = (0.18, 0.16, 0.15)
        largura_ombro = 0.225
        largura_quadril = 0.168
        peito_extra = 0.015
    else:
        # Atleta feminina com proporcoes e cores identicas a abb89707
        cor_pele = (0.82, 0.64, 0.52)
        cor_cabelo = (0.14, 0.10, 0.08)
        cor_camisa = (0.92, 0.38, 0.55) # rosa/coral esportivo
        cor_calca = (0.12, 0.12, 0.15)  # legging de compressao preta
        cor_sapato = (0.96, 0.96, 0.97) # tenis esportivo branco
        largura_ombro = 0.190
        largura_quadril = 0.195
        peito_extra = 0.035

    m_pele = material("QuaterniusSkin", cor_pele, 0.60, 0.0); m_pele.name = "QuaterniusSkin"
    m_cabelo = material("Hair", cor_cabelo, 0.75, 0.0); m_cabelo.name = "Hair"
    m_camisa = material("Camisa", cor_camisa, 0.72, 0.0); m_camisa.name = "Camisa"
    m_calca = material("Calca", cor_calca, 0.65, 0.0); m_calca.name = "Calca"
    m_sapato = material("Sapato", cor_sapato, 0.48, 0.0); m_sapato.name = "Sapato"
    m_olho_branco = material("OlhoBranco", (0.96, 0.96, 0.94), 0.25)
    m_olho_iris = material("OlhoIris", (0.35, 0.22, 0.12), 0.15)

    partes = []

    # 1. Pelvis e Torso
    rings_pelvis = [
        (0, 0.005, 0.90, largura_quadril * 0.90, 0.125, 16),
        (0, 0.005, 0.98, largura_quadril, 0.132, 16),
        (0, 0.000, 1.05, largura_quadril * 0.88, 0.118, 16),
    ]
    o_pelvis = loft_tube("Pelvis", rings_pelvis, m_calca, close_bottom=True)
    partes.append((o_pelvis, "pelvis"))

    rings_torso = [
        (0, 0.000, 1.05, largura_quadril * 0.88, 0.118, 16),
        (0, 0.000, 1.13, largura_quadril * 0.80 if not is_male else 0.165, 0.106, 16),
        (0, -0.005, 1.22, largura_ombro * 0.85, 0.116, 16),
        (0, -0.015 if not is_male else -0.005, 1.30, largura_ombro * 0.92 + peito_extra, 0.128 if not is_male else 0.118, 16),
        (0, -0.005, 1.38, largura_ombro, 0.118, 16),
        (0, 0.000, 1.44, largura_ombro * 0.70, 0.095, 16),
    ]
    o_torso = loft_tube("CamisetaCorpo", rings_torso, m_camisa, close_top=True)
    partes.append((o_torso, "spine_02"))

    # Pescoco
    rings_neck = [
        (0, 0.005, 1.44, 0.052, 0.052, 16),
        (0, 0.005, 1.53, 0.046, 0.046, 16),
    ]
    o_neck = loft_tube("Pescoco", rings_neck, m_pele)
    partes.append((o_neck, "neck_01"))

    # Cabeca
    o_head = elipsoide_uv("Cabeca", (0, -0.015, 1.62), (0.105, 0.115, 0.122), m_pele, 16, 12)
    partes.append((o_head, "Head"))

    # Olhos
    for sx in (-0.038, 0.038):
        oo = elipsoide_uv(f"OlhoBranco_{sx}", (sx, -0.110, 1.635), (0.022, 0.010, 0.014), m_olho_branco, 12, 8)
        partes.append((oo, "Head"))
        oo2 = elipsoide_uv(f"Iris_{sx}", (sx, -0.117, 1.635), (0.011, 0.005, 0.011), m_olho_iris, 12, 8)
        partes.append((oo2, "Head"))

    # Cabelo
    if is_male:
        o_hair_cap = elipsoide_uv("CabeloTouca", (0, 0.005, 1.66), (0.115, 0.124, 0.090), m_cabelo, 16, 12)
        partes.append((o_hair_cap, "Head"))
    else:
        # Rabo de cavalo atletico com elastico (identico a ref abb89707)
        o_hair_cap = elipsoide_uv("CabeloTouca", (0, 0.005, 1.66), (0.115, 0.124, 0.095), m_cabelo, 16, 12)
        partes.append((o_hair_cap, "Head"))
        rings_tie = [(0, 0.105, 1.64, 0.026, 0.026, 12), (0, 0.115, 1.64, 0.028, 0.028, 12)]
        o_tie = loft_tube("ElasticoCabelo", rings_tie, m_camisa)
        partes.append((o_tie, "Head"))
        rings_ponytail = [
            (0, 0.115, 1.64, 0.028, 0.028, 12),
            (0, 0.145, 1.62, 0.038, 0.040, 12),
            (0, 0.170, 1.57, 0.036, 0.036, 12),
            (0, 0.185, 1.50, 0.030, 0.028, 12),
            (0, 0.190, 1.42, 0.020, 0.018, 12),
            (0, 0.185, 1.35, 0.008, 0.008, 12),
        ]
        o_ponytail = loft_tube("RaboCavalo", rings_ponytail, m_cabelo, close_top=True)
        partes.append((o_ponytail, "Head"))

    # 2. Bracos e Maos
    for sx, lado in ((-1, "l"), (1, "r")):
        o_deltoid = elipsoide_uv(f"OmbroManga_{lado}", (sx * (largura_ombro - 0.01), 0, 1.40), (0.058, 0.058, 0.062), m_camisa, 14, 10)
        partes.append((o_deltoid, f"clavicle_{lado}"))
        
        rings_upperarm = [
            (sx * (largura_ombro - 0.01), 0, 1.40, 0.044, 0.044, 12),
            (sx * (largura_ombro + 0.09), 0, 1.40, 0.042, 0.042, 12),
            (sx * 0.38, 0, 1.40, 0.038, 0.038, 12),
        ]
        o_upper = loft_limb_x(f"BracoSup_{lado}", rings_upperarm, m_camisa)
        partes.append((o_upper, f"upperarm_{lado}"))
        
        rings_lowerarm = [
            (sx * 0.38, 0, 1.40, 0.038, 0.038, 12),
            (sx * 0.48, 0, 1.40, 0.034, 0.034, 12),
            (sx * 0.58, 0, 1.40, 0.028, 0.028, 12),
        ]
        o_lower = loft_limb_x(f"Antebraco_{lado}", rings_lowerarm, m_pele)
        partes.append((o_lower, f"lowerarm_{lado}"))
        
        o_hand = elipsoide_uv(f"Mao_{lado}", (sx * 0.63, -0.015, 1.40), (0.038, 0.026, 0.032), m_pele, 12, 8)
        partes.append((o_hand, f"hand_{lado}"))
        o_thumb = elipsoide_uv(f"Polegar_{lado}", (sx * 0.62, -0.035, 1.405), (0.016, 0.020, 0.016), m_pele, 10, 6)
        partes.append((o_thumb, f"hand_{lado}"))

    # 3. Pernas continuas e Tenis de Corrida
    for sx, lado in ((-1, "l"), (1, "r")):
        cx = sx * (largura_quadril * 0.52 if not is_male else 0.10)
        rings_leg = [
            (cx, 0.000, 0.92, 0.076, 0.082, 16),
            (cx, 0.000, 0.82, 0.071, 0.076, 16),
            (cx, 0.000, 0.70, 0.063, 0.066, 16),
            (cx, -0.003, 0.58, 0.055, 0.056, 16),
            (cx, -0.010, 0.50, 0.052, 0.052, 16),
            (cx, -0.004, 0.44, 0.048, 0.048, 16),
            (cx, 0.012, 0.36, 0.058, 0.064, 16),
            (cx, 0.008, 0.26, 0.050, 0.054, 16),
            (cx, 0.003, 0.16, 0.041, 0.044, 16),
            (cx, 0.000, 0.095, 0.043, 0.043, 16),
        ]
        o_leg = loft_tube(f"Perna_{lado}", rings_leg, m_calca)
        partes.append((o_leg, f"thigh_{lado}"))
        
        rings_sock = [
            (cx, 0.000, 0.095, 0.044, 0.044, 16),
            (cx, 0.000, 0.070, 0.045, 0.045, 16),
        ]
        o_sock = loft_tube(f"Meia_{lado}", rings_sock, m_sapato)
        partes.append((o_sock, f"foot_{lado}"))
        
        rings_shoe_upper = [
            (cx, 0.035, 0.070, 0.044, 0.046, 16),
            (cx, -0.020, 0.062, 0.046, 0.052, 16),
            (cx, -0.080, 0.048, 0.047, 0.058, 16),
            (cx, -0.145, 0.036, 0.042, 0.046, 16),
            (cx, -0.170, 0.032, 0.026, 0.026, 16),
        ]
        o_shoe_upper = loft_tube(f"TenisCabedal_{lado}", rings_shoe_upper, m_sapato, close_bottom=True, close_top=True)
        partes.append((o_shoe_upper, f"foot_{lado}"))
        
        rings_midsole = [
            (cx, -0.050, 0.000, 0.048, 0.125, 16),
            (cx, -0.050, 0.015, 0.050, 0.128, 16),
            (cx, -0.050, 0.032, 0.048, 0.126, 16),
        ]
        o_midsole = loft_tube(f"TenisEntressola_{lado}", rings_midsole, m_sapato, close_bottom=True, close_top=True)
        partes.append((o_midsole, f"foot_{lado}"))
        
        o_ball = elipsoide_uv(f"TenisBiqueira_{lado}", (cx, -0.155, 0.022), (0.044, 0.040, 0.022), m_sapato, 12, 8)
        partes.append((o_ball, f"ball_{lado}"))

    # Unifica
    corpo = join_parts(partes)
    arm = armature_humano("Humano")
    skin(arm, corpo)

    # 6 Animacoes
    scene.frame_start = 1
    scene.frame_end = 48

    def act_idle():
        a = new_action(arm, "Idle_Loop")
        for f in (1, 12, 24, 36, 48):
            t = (f - 1) / 48 * TAU
            clear_pose(arm)
            key_rot(arm, "spine_01", f, (rad(1.5), 0, 0))
            key_rot(arm, "spine_02", f, (rad(1.2) * math.sin(t), 0, rad(0.6) * math.cos(t * 0.5)))
            key_rot(arm, "spine_03", f, (rad(0.8) * math.sin(t), 0, 0))
            key_rot(arm, "Head", f, (rad(1.0) * math.sin(t * 0.7), rad(0.6) * math.cos(t), 0))
            key_rot(arm, "upperarm_l", f, (rad(-74), 0, rad(10) + rad(1.5) * math.sin(t)))
            key_rot(arm, "upperarm_r", f, (rad(-74), 0, -rad(10) - rad(1.5) * math.sin(t)))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(22) + rad(1.0) * math.sin(t)))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(22) - rad(1.0) * math.sin(t)))
            key_loc(arm, "pelvis", f, (0, 0, 0.004 * math.sin(t)))
        linearize(a)
        return a

    def act_walk():
        a = new_action(arm, "Walk_Loop")
        C = 24
        for f in range(1, C + 2):
            t = (f - 1) / C * TAU
            s = math.sin(t); c = math.cos(t)
            clear_pose(arm)
            key_rot(arm, "thigh_l", f, (rad(26) * s, 0, 0))
            key_rot(arm, "thigh_r", f, (rad(-26) * s, 0, 0))
            key_rot(arm, "calf_l", f, (rad(40) * max(0, math.sin(t + 0.9)), 0, 0))
            key_rot(arm, "calf_r", f, (rad(40) * max(0, math.sin(t + 0.9 + math.pi)), 0, 0))
            key_rot(arm, "foot_l", f, (rad(-12) * max(0, math.sin(t + 0.9)), 0, 0))
            key_rot(arm, "foot_r", f, (rad(-12) * max(0, math.sin(t + 0.9 + math.pi)), 0, 0))
            key_rot(arm, "upperarm_l", f, (rad(-74), 0, rad(10) - rad(22) * s))
            key_rot(arm, "upperarm_r", f, (rad(-74), 0, -rad(10) + rad(22) * s))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(30) - rad(8) * s))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(30) + rad(8) * s))
            key_rot(arm, "spine_01", f, (rad(2.0), 0, 0))
            key_rot(arm, "spine_02", f, (0, rad(1.8) * s, 0))
            key_loc(arm, "pelvis", f, (0, 0, 0.008 * math.cos(2 * t)))
        linearize(a)
        return a

    def act_sprint():
        a = new_action(arm, "Sprint_Loop")
        C = 16
        for f in range(1, C + 2):
            t = (f - 1) / C * TAU
            s = math.sin(t); c = math.cos(t)
            clear_pose(arm)
            key_rot(arm, "spine_01", f, (rad(7.5), 0, 0))
            key_rot(arm, "spine_02", f, (rad(3.0) * c, rad(2.5) * s, 0))
            key_rot(arm, "spine_03", f, (0, rad(1.5) * s, 0))
            key_rot(arm, "thigh_l", f, (rad(42) * s, 0, 0))
            key_rot(arm, "thigh_r", f, (rad(-42) * s, 0, 0))
            key_rot(arm, "calf_l", f, (rad(65) * max(0, math.sin(t + 0.85)), 0, 0))
            key_rot(arm, "calf_r", f, (rad(65) * max(0, math.sin(t + 0.85 + math.pi)), 0, 0))
            key_rot(arm, "foot_l", f, (rad(-18) * max(0, math.sin(t + 0.85)), 0, 0))
            key_rot(arm, "foot_r", f, (rad(-18) * max(0, math.sin(t + 0.85 + math.pi)), 0, 0))
            key_rot(arm, "upperarm_l", f, (rad(-75), 0, rad(12) - rad(42) * s))
            key_rot(arm, "upperarm_r", f, (rad(-75), 0, -rad(12) + rad(42) * s))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(80) - rad(15) * s))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(80) + rad(15) * s))
            key_loc(arm, "pelvis", f, (0, 0, 0.016 * math.cos(2 * t)))
        linearize(a)
        return a

    def act_jump():
        a = new_action(arm, "Jump_Loop")
        keys = [
            (1,  -32,  50,   8, -75, 45),
            (4,  -18,  25, -25, -75, 60),
            (7,   22,  55,  35, -75, 80),
            (10, -12,  20,  15, -75, 50),
            (12, -28,  45,   8, -75, 45),
        ]
        for f, th, cf, az, ax, el in keys:
            clear_pose(arm)
            key_rot(arm, "thigh_l", f, (rad(th), 0, 0))
            key_rot(arm, "thigh_r", f, (rad(th), 0, 0))
            key_rot(arm, "calf_l", f, (rad(cf), 0, 0))
            key_rot(arm, "calf_r", f, (rad(cf), 0, 0))
            key_rot(arm, "spine_01", f, (rad(10), 0, 0))
            key_rot(arm, "upperarm_l", f, (rad(ax), 0, rad(12) + rad(az)))
            key_rot(arm, "upperarm_r", f, (rad(ax), 0, -rad(12) - rad(az)))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(el)))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(el)))
            key_loc(arm, "pelvis", f, (0, 0, 0.04 if f == 7 else 0.0))
        linearize(a)
        return a

    def act_crouch_idle():
        a = new_action(arm, "Crouch_Idle_Loop")
        for f in (1, 24, 48):
            t = (f - 1) / 48 * TAU
            clear_pose(arm)
            key_rot(arm, "thigh_l", f, (rad(-46), 0, 0))
            key_rot(arm, "thigh_r", f, (rad(-46), 0, 0))
            key_rot(arm, "calf_l", f, (rad(68), 0, 0))
            key_rot(arm, "calf_r", f, (rad(68), 0, 0))
            key_rot(arm, "spine_01", f, (rad(16) + rad(1.0) * math.sin(t), 0, 0))
            key_rot(arm, "spine_02", f, (rad(8), 0, 0))
            key_rot(arm, "upperarm_l", f, (rad(-72), 0, rad(16)))
            key_rot(arm, "upperarm_r", f, (rad(-72), 0, -rad(16)))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(70)))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(70)))
        linearize(a)
        return a

    def act_crouch_fwd():
        a = new_action(arm, "Crouch_Fwd_Loop")
        C = 20
        for f in range(1, C + 2):
            t = (f - 1) / C * TAU
            s = math.sin(t); c = math.cos(t)
            clear_pose(arm)
            key_rot(arm, "thigh_l", f, (rad(-42) + rad(16) * s, 0, 0))
            key_rot(arm, "thigh_r", f, (rad(-42) - rad(16) * s, 0, 0))
            key_rot(arm, "calf_l", f, (rad(60) + rad(14) * max(0, math.sin(t + 0.7)), 0, 0))
            key_rot(arm, "calf_r", f, (rad(60) + rad(14) * max(0, math.sin(t + 0.7 + math.pi)), 0, 0))
            key_rot(arm, "spine_01", f, (rad(20), 0, 0))
            key_rot(arm, "upperarm_l", f, (rad(-72), 0, rad(16) - rad(20) * s))
            key_rot(arm, "upperarm_r", f, (rad(-72), 0, -rad(16) + rad(20) * s))
            key_rot(arm, "lowerarm_l", f, (0, 0, rad(75) - rad(10) * s))
            key_rot(arm, "lowerarm_r", f, (0, 0, -rad(75) + rad(10) * s))
            key_loc(arm, "pelvis", f, (0, 0, 0.006 * c))
        linearize(a)
        return a

    act_idle()
    act_walk()
    act_sprint()
    act_jump()
    act_crouch_idle()
    act_crouch_fwd()

    # export Draco-compressed
    bpy.ops.object.select_all(action='DESELECT')
    corpo.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        export_apply=True,
        export_animations=True,
        export_skins=True,
        export_yup=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
        export_animation_mode='ACTIONS',
        export_draco_mesh_compression_enable=False,  # Godot 4 não suporta KHR_draco_mesh_compression (mesh invisível)
        use_selection=True
    )
    print("PRONTO:", out_path, os.path.getsize(out_path))
    blend_path = os.path.join(OUT_DIR, ("humano_%s.blend" % ("M" if is_male else "F")))
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    return out_path

if __name__ == "__main__":
    for is_male, nome in [(True, "Humano_M.glb"), (False, "Humano_F.glb")]:
        build_one(is_male, os.path.join(OUT_HUMANOS, nome))
    print("HUMANOS OK")
