#!/usr/bin/env python3
# build_personagens.py — 20 corredores Blender 4.5 headless, 100% originais, PBR baked colors.
# Cada personagem compartilha skeleton/animacoes de build_humanos.py, com malhas continuas
# organicas, pernas anatomicas, tenis de corrida esculpidos e UVs sem sobreposicao.
import math, os, sys
from pathlib import Path
import bpy

D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = str(REPO / "tools" / "blender" / "out")
OUT_PERSONAGENS = str(REPO / "assets" / "characters" / "personagens")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(OUT_PERSONAGENS, exist_ok=True)

TAU = math.tau
def rad(d): return math.radians(d)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2],16)/255.0, int(h[2:4],16)/255.0, int(h[4:6],16)/255.0)

# CATALOG espelhando scripts/character_data.gd (cores exatas)
CATALOG = [
    {"id":"ze","name":"Zé Atrasado","gender":"M","skin":"#b87655","hair":"#211b1a","shirt":"#e55359","pants":"#263a55","shoes":"#f3ca55","accent":"#55c4c8"},
    {"id":"motoboy","name":"Rafa Motoboy","gender":"M","skin":"#70452f","hair":"#17171d","shirt":"#f08b3e","pants":"#202b39","shoes":"#e5e9df","accent":"#43d6bd"},
    {"id":"luan","name":"Luan do Skate","gender":"M","skin":"#d08b63","hair":"#38221f","shirt":"#7659d6","pants":"#d5a45f","shoes":"#f3eee0","accent":"#ed6aa0"},
    {"id":"joao","name":"João Gamer","gender":"M","skin":"#e1a47b","hair":"#3a2630","shirt":"#2f9fe2","pants":"#303044","shoes":"#8de5d0","accent":"#b88cff"},
    {"id":"carlos","name":"Carlos da Obra","gender":"M","skin":"#8d5837","hair":"#211a18","shirt":"#ee793d","pants":"#56606c","shoes":"#5e3828","accent":"#ffe36b"},
    {"id":"maria","name":"Maria do Bairro","gender":"F","skin":"#6c3e2d","hair":"#1d1517","shirt":"#e58aab","pants":"#5b4070","shoes":"#f2c65a","accent":"#68c6b1"},
    {"id":"bia","name":"Bia Estudante","gender":"F","skin":"#c98463","hair":"#4c2d24","shirt":"#f2f0e5","pants":"#3a6fa0","shoes":"#ec6b6a","accent":"#f5c85a"},
    {"id":"camila","name":"Camila do Negócio","gender":"F","skin":"#a96246","hair":"#24191a","shirt":"#46b6a3","pants":"#305a5d","shoes":"#f0b84e","accent":"#f27a5b"},
    {"id":"julia","name":"Júlia Atleta","gender":"F","skin":"#a66b52","hair":"#171319","shirt":"#eb618c","pants":"#1e1e26","shoes":"#f5f5f7","accent":"#e9d459"},
    {"id":"influencer","name":"Nina Creator","gender":"F","skin":"#d49b7b","hair":"#291b2c","shirt":"#171824","pants":"#4f7897","shoes":"#171a26","accent":"#d7b9e9"},
    {"id":"chico","name":"Chico Carteiro","gender":"M","skin":"#8a5a3c","hair":"#1c1614","shirt":"#2f6db8","pants":"#22314a","shoes":"#2b2b33","accent":"#ffd23e"},
    {"id":"tiao","name":"Tião Vaqueiro","gender":"M","skin":"#6e452c","hair":"#191210","shirt":"#a8672f","pants":"#5a3d28","shoes":"#3a2617","accent":"#d9b06a"},
    {"id":"beto","name":"Beto Praiano","gender":"M","skin":"#c98a5e","hair":"#7a5c34","shirt":"#35c4b0","pants":"#e0d29a","shoes":"#f2efe6","accent":"#ff8c42"},
    {"id":"nilo","name":"Nilo Padeiro","gender":"M","skin":"#e3ad82","hair":"#3d2b1f","shirt":"#f4efe6","pants":"#cfd4da","shoes":"#4b4f57","accent":"#e0993e"},
    {"id":"professor","name":"Professor Everaldo","gender":"M","skin":"#7f5236","hair":"#8e8e94","shirt":"#eae4d6","pants":"#2e3a52","shoes":"#26221f","accent":"#b8864f"},
    {"id":"marta","name":"Dona Marta da Feira","gender":"F","skin":"#9c6647","hair":"#2a1c1e","shirt":"#ef8f3f","pants":"#4f7a4a","shoes":"#d8c9a8","accent":"#f5d76e"},
    {"id":"zilda","name":"Vovó Zilda","gender":"F","skin":"#caa07b","hair":"#d8d5cf","shirt":"#d98cb0","pants":"#6a4f7c","shoes":"#3a2e2a","accent":"#8fd4c2"},
    {"id":"clara","name":"Enfermeira Clara","gender":"F","skin":"#d9a583","hair":"#5b3a29","shirt":"#f4f7fa","pants":"#dfe7ee","shoes":"#eef1f5","accent":"#e05263"},
    {"id":"deise","name":"Deise Craque","gender":"F","skin":"#75492f","hair":"#1f1719","shirt":"#f6c945","pants":"#1f4f8f","shoes":"#245c3f","accent":"#2fa36b"},
    {"id":"cida","name":"Motorista Cida","gender":"F","skin":"#8d5c3e","hair":"#241a1c","shirt":"#3f7fae","pants":"#2b3f5e","shoes":"#23252d","accent":"#f6c945"},
]

def profile_by_id(pid):
    for p in CATALOG:
        if p["id"] == pid:
            return p
    return CATALOG[0]

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
        r_xy = math.cos(phi)
        for i in range(u_seg):
            theta = i / u_seg * TAU
            x = cx + rx * r_xy * math.cos(theta)
            y = cy + ry * r_xy * math.sin(theta)
            verts.append((x, y, z))
    verts.append((cx, cy, cz + rz))
    south_idx = 0
    north_idx = len(verts) - 1
    
    for i in range(u_seg):
        i_next = (i + 1) % u_seg
        faces.append((south_idx, 1 + i, 1 + i_next))
        
    for j in range(v_seg - 2):
        row0 = 1 + j * u_seg
        row1 = 1 + (j + 1) * u_seg
        for i in range(u_seg):
            i_next = (i + 1) % u_seg
            faces.append((row0 + i, row1 + i, row1 + i_next, row0 + i_next))
            
    top_row = 1 + (v_seg - 2) * u_seg
    for i in range(u_seg):
        i_next = (i + 1) % u_seg
        faces.append((north_idx, top_row + i_next, top_row + i))

    me.from_pydata(verts, [], faces)
    me.update()
    
    uv_layer = me.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    face_idx = 0
    for i in range(u_seg):
        poly = me.polygons[face_idx]
        uv_data[poly.loop_indices[0]].uv = ((i + 0.5) / u_seg, 0.0)
        uv_data[poly.loop_indices[1]].uv = (i / u_seg, 1.0 / v_seg)
        uv_data[poly.loop_indices[2]].uv = ((i + 1) / u_seg, 1.0 / v_seg)
        face_idx += 1
        
    for j in range(v_seg - 2):
        v_low = (j + 1) / v_seg
        v_high = (j + 2) / v_seg
        for i in range(u_seg):
            poly = me.polygons[face_idx]
            uv_data[poly.loop_indices[0]].uv = (i / u_seg, v_low)
            uv_data[poly.loop_indices[1]].uv = (i / u_seg, v_high)
            uv_data[poly.loop_indices[2]].uv = ((i + 1) / u_seg, v_high)
            uv_data[poly.loop_indices[3]].uv = ((i + 1) / u_seg, v_low)
            face_idx += 1
            
    for i in range(u_seg):
        poly = me.polygons[face_idx]
        uv_data[poly.loop_indices[0]].uv = ((i + 0.5) / u_seg, 1.0)
        uv_data[poly.loop_indices[1]].uv = ((i + 1) / u_seg, 1.0 - 1.0 / v_seg)
        uv_data[poly.loop_indices[2]].uv = (i / u_seg, 1.0 - 1.0 / v_seg)
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

def build_one_personagem(profile, out_path):
    pid = profile["id"]
    is_male = profile["gender"] == "M"
    scene = reset()
    cor_pele = hex_to_rgb(profile["skin"])
    cor_cabelo = hex_to_rgb(profile["hair"])
    cor_camisa = hex_to_rgb(profile["shirt"])
    cor_calca = hex_to_rgb(profile["pants"])
    cor_sapato = hex_to_rgb(profile["shoes"])
    cor_accent = hex_to_rgb(profile["accent"])
    
    # Proporcoes realistas por genero
    h = sum(ord(c) for c in pid) % 10
    if is_male:
        largura_ombro = 0.225 + (h - 5) * 0.002
        largura_quadril = 0.168 + (h % 3) * 0.004
        peito_extra = 0.015
    else:
        largura_ombro = 0.190 + (h - 5) * 0.0015
        largura_quadril = 0.195 + (h % 5) * 0.004
        peito_extra = 0.035

    m_pele = material(f"QuaterniusSkin_{pid}", cor_pele, 0.60, 0.0)
    m_pele.name = "QuaterniusSkin"
    m_cabelo = material(f"Hair_{pid}", cor_cabelo, 0.75, 0.0); m_cabelo.name = "Hair"
    m_camisa = material(f"Camisa_{pid}", cor_camisa, 0.72, 0.0); m_camisa.name = "Camisa"
    m_calca = material(f"Calca_{pid}", cor_calca, 0.65, 0.0); m_calca.name = "Calca"
    m_sapato = material(f"Sapato_{pid}", cor_sapato, 0.48, 0.0); m_sapato.name = "Sapato"
    m_accent = material(f"Accent_{pid}", cor_accent, 0.55, 0.15)
    m_olho_branco = material(f"OlhoBranco_{pid}", (0.96, 0.96, 0.94), 0.25)
    m_olho_iris = material(f"OlhoIris_{pid}", (0.35, 0.22, 0.12), 0.15)

    partes = []

    # 1. TORSO CONTINUO E ANATOMICO
    # Pelvis
    rings_pelvis = [
        (0, 0.005, 0.90, largura_quadril * 0.90, 0.125, 16),
        (0, 0.005, 0.98, largura_quadril, 0.132, 16),
        (0, 0.000, 1.05, largura_quadril * 0.88, 0.118, 16),
    ]
    o_pelvis = loft_tube("Pelvis", rings_pelvis, m_calca, close_bottom=True)
    partes.append((o_pelvis, "pelvis"))

    # Torso
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

    # Cabelo e Aderecos Especificos
    if pid == "julia":
        # Rabo de cavalo atletico com elastico (ref abb89707)
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
    else:
        o_hair_cap = elipsoide_uv("CabeloTouca", (0, 0.005, 1.66), (0.115, 0.124, 0.090), m_cabelo, 16, 12)
        partes.append((o_hair_cap, "Head"))
        if not is_male:
            # mecha lateral feminina
            for sx in (-0.10, 0.10):
                oc2 = elipsoide_uv(f"CabeloLado_{sx}", (sx, 0.02, 1.58), (0.025, 0.055, 0.10), m_cabelo, 12, 8)
                partes.append((oc2, "Head"))
        elif pid in ("motoboy", "carlos", "tiao"):
            ob = elipsoide_uv(f"Barba_{pid}", (0, -0.095, 1.57), (0.08, 0.025, 0.045), m_cabelo, 12, 8)
            partes.append((ob, "Head"))

    # 2. BRACOS E MAOS
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

    # 3. PERNAS CONTINUAS E TENIS DE CORRIDA ESCULPIDO
    for sx, lado in ((-1, "l"), (1, "r")):
        cx = sx * (largura_quadril * 0.52 if not is_male else 0.10)
        rings_leg = [
            (cx, 0.000, 0.92, 0.076, 0.082, 16),
            (cx, 0.000, 0.82, 0.071, 0.076, 16),
            (cx, 0.000, 0.70, 0.063, 0.066, 16),
            (cx, -0.003, 0.58, 0.055, 0.056, 16),
            (cx, -0.010, 0.50, 0.052, 0.052, 16), # patela do joelho
            (cx, -0.004, 0.44, 0.048, 0.048, 16),
            (cx, 0.012, 0.36, 0.058, 0.064, 16),  # gastrocnemio
            (cx, 0.008, 0.26, 0.050, 0.054, 16),
            (cx, 0.003, 0.16, 0.041, 0.044, 16),  # tendao aquiles
            (cx, 0.000, 0.095, 0.043, 0.043, 16), # tornozelo
        ]
        o_leg = loft_tube(f"Perna_{lado}", rings_leg, m_calca)
        partes.append((o_leg, f"thigh_{lado}"))
        
        # Meia esportiva
        rings_sock = [
            (cx, 0.000, 0.095, 0.044, 0.044, 16),
            (cx, 0.000, 0.070, 0.045, 0.045, 16),
        ]
        o_sock = loft_tube(f"Meia_{lado}", rings_sock, m_sapato)
        partes.append((o_sock, f"foot_{lado}"))
        
        # Tenis cabedal
        rings_shoe_upper = [
            (cx, 0.035, 0.070, 0.044, 0.046, 16),
            (cx, -0.020, 0.062, 0.046, 0.052, 16),
            (cx, -0.080, 0.048, 0.047, 0.058, 16),
            (cx, -0.145, 0.036, 0.042, 0.046, 16),
            (cx, -0.170, 0.032, 0.026, 0.026, 16),
        ]
        o_shoe_upper = loft_tube(f"TenisCabedal_{lado}", rings_shoe_upper, m_sapato, close_bottom=True, close_top=True)
        partes.append((o_shoe_upper, f"foot_{lado}"))
        
        # Entressola grossa de amortecimento branca em EVA (base em z = 0.000 m)
        rings_midsole = [
            (cx, -0.050, 0.000, 0.048, 0.125, 16),
            (cx, -0.050, 0.015, 0.050, 0.128, 16),
            (cx, -0.050, 0.032, 0.048, 0.126, 16),
        ]
        o_midsole = loft_tube(f"TenisEntressola_{lado}", rings_midsole, m_sapato, close_bottom=True, close_top=True)
        partes.append((o_midsole, f"foot_{lado}"))
        
        # Ponta de apoio (ball of foot)
        o_ball = elipsoide_uv(f"TenisBiqueira_{lado}", (cx, -0.155, 0.022), (0.044, 0.040, 0.022), m_sapato, 12, 8)
        partes.append((o_ball, f"ball_{lado}"))

    # Acessorios unicos por personagem (mochila, bolsa, chapeu etc)
    if pid == "motoboy":
        # Capacete com viseira
        o_cap = elipsoide_uv("CapaceteMoto", (0, -0.005, 1.66), (0.125, 0.130, 0.115), m_accent, 16, 12)
        partes.append((o_cap, "Head"))
        # Bag de entrega nas costas
        rings_bag = [(0, 0.13, 1.10, 0.15, 0.08, 12), (0, 0.13, 1.36, 0.15, 0.08, 12)]
        o_bag = loft_tube("BagMoto", rings_bag, m_accent, close_bottom=True, close_top=True)
        partes.append((o_bag, "spine_02"))
    elif pid == "carlos":
        # Capacete de obra
        o_cap = elipsoide_uv("CapaceteObra", (0, 0, 1.68), (0.125, 0.128, 0.075), m_accent, 16, 12)
        partes.append((o_cap, "Head"))
    elif pid == "bia":
        # Mochila escolar nas costas
        rings_bag = [(0, 0.12, 1.12, 0.13, 0.07, 12), (0, 0.12, 1.34, 0.13, 0.07, 12)]
        o_bag = loft_tube("MochilaBia", rings_bag, m_accent, close_bottom=True, close_top=True)
        partes.append((o_bag, "spine_02"))
    elif pid == "chico":
        # Bone carteiro
        o_cap = elipsoide_uv("BoneChico", (0, 0, 1.68), (0.115, 0.118, 0.055), m_camisa, 14, 10)
        partes.append((o_cap, "Head"))

    # Unifica todas as partes
    corpo = join_parts(partes)
    arm = armature_humano("Humano")
    skin(arm, corpo)

    # 6 Animacoes Biomecanicas
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
        for f in range(1, C + 1):
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
        for f in range(1, C + 1):
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
            (1, -32, 50, 8, -75, 45),
            (4, -18, 25, -25, -75, 60),
            (7, 22, 55, 35, -75, 80),
            (10, -12, 20, 15, -75, 50),
            (12, -28, 45, 8, -75, 45),
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
        for f in range(1, C + 1):
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

    sozinho(arm)
    corpo.select_set(True)
    bpy.context.view_layer.objects.active = arm

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=False,
        export_skins=True,
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_materials='EXPORT',
        export_draco_mesh_compression_enable=False,  # Godot 4 não suporta KHR_draco_mesh_compression (mesh invisível)
    )
    sz = os.path.getsize(out_path)
    print("Export OK:", out_path, "Size:", sz)
    return out_path, sz

if __name__ == "__main__":
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        wanted = sys.argv[idx + 1:]
    if not wanted:
        wanted = [p["id"] for p in CATALOG]
    else:
        if len(wanted) == 1 and wanted[0] == "all":
            wanted = [p["id"] for p in CATALOG]
        else:
            valid = set(p["id"] for p in CATALOG)
            wanted = [w for w in wanted if w in valid]
            if not wanted:
                wanted = [p["id"] for p in CATALOG]
    print(f"Gerando personagens: {', '.join(wanted)} ({len(wanted)} / {len(CATALOG)})")
    total_sz = 0
    for pid in wanted:
        prof = profile_by_id(pid)
        out = os.path.join(OUT_PERSONAGENS, f"{pid}.glb")
        print(f"\n=== {pid} ({prof['name']}) ===")
        try:
            _, sz = build_one_personagem(prof, out)
            total_sz += sz
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"FALHA {pid}: {e}")
    print(f"\nPERSONAGENS OK: {len(wanted)} gerados, total {total_sz} bytes em {OUT_PERSONAGENS}")
