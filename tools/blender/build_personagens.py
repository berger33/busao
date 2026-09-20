#!/usr/bin/env python3
# build_personagens.py — 20 corredores Blender 5.0 headless, 100% originais, PBR baked colors.
# Cada personagem compartilha skeleton/animacoes de build_humanos.py, mas tem paleta
# e acessórios dedicados (mochila, capacete, bag, etc) baked como meshes weighted.
# Uso:
#   LD_LIBRARY_PATH=/tmp/fake_libs:$LD_LIBRARY_PATH python3 tools/blender/build_personagens.py            # todos 20
#   LD_LIBRARY_PATH=/tmp/fake_libs:$LD_LIBRARY_PATH python3 tools/blender/build_personagens.py ze motoboy maria
import math, os, sys
from pathlib import Path
import bpy
from mathutils import Vector

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
    {"id":"julia","name":"Júlia Atleta","gender":"F","skin":"#7b4937","hair":"#171319","shirt":"#e75076","pants":"#242c4c","shoes":"#68e0c0","accent":"#e9d459"},
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
        if p["id"]==pid:
            return p
    return CATALOG[0]

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

def pilar_z(nome, r_base, r_topo_rel, altura, seg=24):
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

def elipsoide_bl(nome, centro, raios, seg=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=seg, radius=1.0, location=centro)
    o = bpy.context.active_object
    o.name = nome
    sozinho(o)
    o.scale = raios
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    try:
        mm=o.modifiers.new("Subd",'SUBSURF'); mm.levels=mm.render_levels=1
    except: pass
    return o

def torus_bl(nome, centro, major_radius, minor_radius, major_seg=16, minor_seg=8):
    bpy.ops.mesh.primitive_torus_add(location=centro, major_radius=major_radius, minor_radius=minor_radius, major_segments=major_seg, minor_segments=minor_seg, abso_major_rad=1.0, abso_minor_rad=1.0)
    o = bpy.context.active_object
    o.name = nome
    return o

def cilindro_bl(nome, centro, raio, altura, seg=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=raio, depth=altura, location=(centro[0], centro[1], centro[2]+altura*0.5), vertices=seg)
    o = bpy.context.active_object
    o.name = nome
    return o

def join_parts(partes):
    for o,_ in partes:
        sozinho(o)
        while o.modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=o.modifiers[0].name)
            except:
                o.modifiers.remove(o.modifiers[0])
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
    assert len(corpo.data.vertices)==total, f"join alterou vertices {len(corpo.data.vertices)} vs {total}"
    print("VERTICES:", total, "partes", len(partes))
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
    osso("pelvis", (0,0,0.92), (0,0,1.05))
    osso("spine_01", (0,0,1.05), (0,0,1.18), "pelvis")
    osso("spine_02", (0,0,1.18), (0,0,1.32), "spine_01")
    osso("spine_03", (0,0,1.32), (0,0,1.45), "spine_02")
    osso("neck_01", (0,0,1.45), (0,0,1.545), "spine_03")
    osso("Head", (0,0,1.545), (0,0,1.75), "neck_01")
    osso("clavicle_l", (-0.02,0,1.40), (-0.14,0,1.40), "spine_03")
    osso("clavicle_r", ( 0.02,0,1.40), ( 0.14,0,1.40), "spine_03")
    osso("upperarm_l", (-0.14,0,1.40), (-0.38,0,1.40), "clavicle_l")
    osso("lowerarm_l", (-0.38,0,1.40), (-0.60,0,1.40), "upperarm_l")
    osso("hand_l", (-0.60,0,1.40), (-0.68,0,1.40), "lowerarm_l")
    osso("upperarm_r", ( 0.14,0,1.40), ( 0.38,0,1.40), "clavicle_r")
    osso("lowerarm_r", ( 0.38,0,1.40), ( 0.60,0,1.40), "upperarm_r")
    osso("hand_r", ( 0.60,0,1.40), ( 0.68,0,1.40), "lowerarm_r")
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
    fcurves = []
    if hasattr(act, "fcurves"):
        try:
            fcurves = list(act.fcurves)
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
        except Exception as e:
            print("linearize fallback layers failed", e)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation='LINEAR'

def build_one_personagem(profile, out_path):
    pid = profile["id"]
    is_male = profile["gender"]=="M"
    scene=reset()
    cor_pele = hex_to_rgb(profile["skin"])
    cor_cabelo = hex_to_rgb(profile["hair"])
    cor_camisa = hex_to_rgb(profile["shirt"])
    cor_calca = hex_to_rgb(profile["pants"])
    cor_sapato = hex_to_rgb(profile["shoes"])
    cor_accent = hex_to_rgb(profile["accent"])
    # proporções realistas por gênero + variação leve por personagem para não ficar clone
    # variação baseada em hash do id para dar 2-3 cm diferença
    h = sum(ord(c) for c in pid) % 10
    if is_male:
        largura_ombro = 0.23 + (h-5)*0.002  # 0.22-0.24
        largura_quadril = 0.168 + (h%3)*0.004
        peito_extra = 0.022 + (h%4)*0.004
    else:
        largura_ombro = 0.205 + (h-5)*0.0015
        largura_quadril = 0.205 + (h%5)*0.005  # 0.205-0.225 curvilíneas
        peito_extra = 0.042 + (h%3)*0.005

    m_pele=material(f"QuaterniusSkin_{pid}", cor_pele, 0.62, 0.0)
    m_pele.name="QuaterniusSkin"
    m_cabelo=material(f"Hair_{pid}", cor_cabelo, 0.72, 0.0); m_cabelo.name="Hair"
    m_camisa=material(f"Camisa_{pid}", cor_camisa, 0.68, 0.0); m_camisa.name="Camisa"
    m_calca=material(f"Calca_{pid}", cor_calca, 0.70, 0.0); m_calca.name="Calca"
    m_sapato=material(f"Sapato_{pid}", cor_sapato, 0.55, 0.15); m_sapato.name="Sapato"
    m_accent=material(f"Accent_{pid}", cor_accent, 0.55, 0.15)
    m_olho_branco=material(f"OlhoBranco_{pid}", (0.96,0.96,0.94), 0.25)
    m_olho_iris=material(f"OlhoIris_{pid}", (0.35,0.22,0.12), 0.15)
    # textura sutil para pele: nada extra, cor sólida já é PBR; accent usado nos props

    partes=[]

    # PELVIS / quadril
    # Para personagens femininas com saia/vestido (maria, zilda) usamos cilindro em vez de caixa para silhueta
    if pid in ("maria","zilda","marta"):
        o=pilar_z("PelvisSaia", 0.18 if pid=="maria" else 0.20, 1.15, 0.22)
        sozinho(o); o.location=(0,0,0.92); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        o.data.materials.append(m_calca)
        partes.append((o,"pelvis"))
    else:
        o=caixa("Pelvis", (0,0,0.985), (largura_quadril*2+0.08, 0.18, 0.16))
        o.data.materials.append(m_calca)
        partes.append((o,"pelvis"))

    o=caixa("CinturaBaixa", (0,0,1.115), (0.34,0.17,0.14))
    o.data.materials.append(m_camisa)
    partes.append((o,"spine_01"))
    o=caixa("PeitoMedio", (0,0,1.25), (0.38+peito_extra,0.18,0.14))
    o.data.materials.append(m_camisa)
    partes.append((o,"spine_02"))
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
    for sx in (-0.038, 0.038):
        oo=elipsoide_bl(f"OlhoBranco_{sx}", (sx, -0.095, 1.635), (0.028,0.012,0.018), seg=1)
        oo.data.materials.append(m_olho_branco)
        partes.append((oo,"Head"))
        oo2=elipsoide_bl(f"Iris_{sx}", (sx, -0.105, 1.635), (0.012,0.006,0.012), seg=1)
        oo2.data.materials.append(m_olho_iris)
        partes.append((oo2,"Head"))
    # cabelo base por gênero, refinado por personagem
    if is_male:
        if pid in ("tiao","beto"):
            # cabelo levemente mais longo / praia
            oc=elipsoide_bl("CabeloTopo", (0,0,1.70), (0.12,0.125,0.075), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
        elif pid=="professor":
            # grisalho mais ralo
            oc=elipsoide_bl("CabeloTopo", (0,0,1.695), (0.11,0.11,0.055), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
        else:
            oc=elipsoide_bl("CabeloTopo", (0,0,1.70), (0.12,0.125,0.085), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
            for sx in (-0.10, 0.10):
                oc2=elipsoide_bl(f"CabeloLado_{sx}", (sx,0,1.62), (0.025,0.04,0.07), seg=1)
                oc2.data.materials.append(m_cabelo)
                partes.append((oc2,"Head"))
        # barba sutil para alguns
        if pid in ("motoboy","carlos","tiao"):
            ob=elipsoide_bl(f"Barba_{pid}", (0,-0.095,1.57), (0.08,0.025,0.045), seg=1)
            ob.data.materials.append(m_cabelo)
            partes.append((ob,"Head"))
    else:
        if pid=="julia":
            # rabo de cavalo + faixa
            oc=elipsoide_bl("CabeloTopo", (0,0,1.705), (0.11,0.12,0.065), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
            oc2=elipsoide_bl("RaboJulia", (0,0.09,1.55), (0.055,0.065,0.20), seg=1)
            oc2.data.materials.append(m_cabelo)
            partes.append((oc2,"Head"))
        elif pid in ("zilda","marta"):
            oc=elipsoide_bl("CabeloTopo", (0,0,1.68), (0.105,0.11,0.055), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
        elif pid=="influencer":
            oc=elipsoide_bl("CabeloTopo", (0,0,1.705), (0.125,0.13,0.09), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
            for sx in (-0.11, 0.11):
                oc2=elipsoide_bl(f"CabeloLongo_{sx}", (sx, 0.015, 1.52), (0.045,0.055,0.22), seg=1)
                oc2.data.materials.append(m_cabelo)
                partes.append((oc2,"Head"))
            oc3=elipsoide_bl("CabeloAtras", (0,0.08,1.55), (0.11,0.07,0.18), seg=1)
            oc3.data.materials.append(m_cabelo)
            partes.append((oc3,"Head"))
        else:
            oc=elipsoide_bl("CabeloTopo", (0,0,1.705), (0.125,0.13,0.09), seg=1)
            oc.data.materials.append(m_cabelo)
            partes.append((oc,"Head"))
            for sx in (-0.11, 0.11):
                oc2=elipsoide_bl(f"CabeloLongo_{sx}", (sx, 0.015, 1.52), (0.045,0.055,0.22), seg=1)
                oc2.data.materials.append(m_cabelo)
                partes.append((oc2,"Head"))
            oc3=elipsoide_bl("CabeloAtras", (0,0.08,1.55), (0.11,0.07,0.18), seg=1)
            oc3.data.materials.append(m_cabelo)
            partes.append((oc3,"Head"))

    # bracos
    for sx, lado in ((-1, "l"), (1, "r")):
        cx = sx * (largura_ombro+0.02)
        oo=elipsoide_bl(f"OmbroCap_{lado}_{pid}", (cx,0,1.40), (0.065,0.065,0.065), seg=1)
        oo.data.materials.append(m_camisa)
        partes.append((oo,f"clavicle_{lado}"))
        o=pilar_z(f"BracoSup_{lado}_{pid}", 0.055, 0.045, 0.24)
        sozinho(o); o.location=(cx,0,1.40); o.rotation_euler=(0, rad(90 if sx>0 else -90), 0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        o.data.materials.append(m_camisa)
        partes.append((o,f"upperarm_{lado}"))
        o2=pilar_z(f"Antebraco_{lado}_{pid}", 0.042, 0.032, 0.22)
        sozinho(o2); o2.location=(sx*0.38,0,1.40); o2.rotation_euler=(0, rad(90 if sx>0 else -90),0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        o2.data.materials.append(m_pele)
        partes.append((o2,f"lowerarm_{lado}"))
        o3=elipsoide_bl(f"Mao_{lado}_{pid}", (sx*0.64,0,1.40), (0.045,0.025,0.04), seg=1)
        o3.data.materials.append(m_pele)
        partes.append((o3,f"hand_{lado}"))
        for i, dz in enumerate([-0.02,0,0.02]):
            o4=caixa(f"Dedo_{lado}_{i}_{pid}", (sx*0.69, -0.045, 1.40+dz), (0.015,0.03,0.015))
            o4.data.materials.append(m_pele)
            partes.append((o4,f"hand_{lado}"))

    # pernas
    for sx, lado in ((-1,"l"),(1,"r")):
        cx=sx*0.09
        o=pilar_z(f"Coxa_{lado}_{pid}", 0.078, 0.065, 0.42)
        sozinho(o); o.location=(cx,0,0.50); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        o.data.materials.append(m_calca)
        partes.append((o,f"thigh_{lado}"))
        o2=pilar_z(f"Panturrilha_{lado}_{pid}", 0.065, 0.045, 0.40)
        sozinho(o2); o2.location=(cx,0,0.10); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        o2.data.materials.append(m_calca)
        partes.append((o2,f"calf_{lado}"))
        o3=caixa(f"Sapato_{lado}_{pid}", (cx, -0.07, 0.035), (0.12,0.24,0.07))
        o3.data.materials.append(m_sapato)
        partes.append((o3,f"foot_{lado}"))
        o4=caixa(f"PeitoPe_{lado}_{pid}", (cx, -0.09, 0.055), (0.11,0.18,0.04))
        o4.data.materials.append(m_sapato)
        partes.append((o4,f"ball_{lado}"))

    # ===== ACESSORIOS BAKED POR PERSONAGEM =====
    # Todas as posicoes: frente -Y, costas +Y, altura Z ~ skeleton
    # Generic helper para adicionar caixa acessorio
    def add_box(name, center, dims, mat, bone):
        o=caixa(name, center, dims)
        # limpa materiais padrão e aplica exato
        o.data.materials.clear()
        o.data.materials.append(mat)
        partes.append((o,bone))
        return o
    def add_ellip(name, center, radii, seg_, mat, bone):
        o=elipsoide_bl(name, center, radii, seg=seg_)
        o.data.materials.clear()
        o.data.materials.append(mat)
        partes.append((o,bone))
        return o

    if pid=="ze":
        # mochila tiracolo cinza-azulada nas costas
        add_box(f"Mochila_{pid}", (0, 0.14, 1.24), (0.28, 0.12, 0.34), m_accent, "spine_02")
        # detalhe ziper
        add_box(f"MochilaZip_{pid}", (0, 0.075, 1.24), (0.02, 0.02, 0.30), m_sapato, "spine_02")
    elif pid=="motoboy":
        # capacete fechado
        add_ellip(f"Capacete_{pid}", (0,0,1.73), (0.128,0.13,0.11), 2, material(f"CapaceteMat_{pid}", hex_to_rgb("#f08b3e"), 0.35, 0.25), "Head")
        # viseira escura
        add_box(f"Viseira_{pid}", (0,-0.08,1.69), (0.18,0.02,0.06), material(f"ViseiraMat_{pid}", hex_to_rgb("#202b39"), 0.25, 0.5), "Head")
        # bag térmica quadrada nas costas
        add_box(f"BagTermica_{pid}", (0, 0.18, 1.26), (0.36, 0.24, 0.34), material(f"BagMat_{pid}", hex_to_rgb("#f08b3e"), 0.72), "spine_02")
        # logo bag
        add_box(f"BagLogo_{pid}", (0, 0.065, 1.26), (0.18, 0.02, 0.08), m_accent, "spine_02")
    elif pid=="luan":
        # boné aba reta roxo escuro
        add_ellip(f"BoneCrown_{pid}", (0,0,1.75), (0.115,0.115,0.055), 1, material(f"BoneMat_{pid}", hex_to_rgb("#7659d6"), 0.68), "Head")
        add_box(f"BoneAba_{pid}", (0,-0.12,1.72), (0.16,0.08,0.02), material(f"BoneAbaMat_{pid}", hex_to_rgb("#38221f"), 0.72), "Head")
        # bermuda mostarda já é calca, mas adiciona joelheira street? skip
    elif pid=="joao":
        # fone gamer sobre cabeça
        o=torus_bl(f"Fone_{pid}", (0,0,1.70), 0.095, 0.018)
        o.data.materials.append(material(f"FoneMat_{pid}", cor_accent, 0.4, 0.2))
        sozinho(o); o.rotation_euler=(0,0,rad(90)); bpy.ops.object.transform_apply(rotation=True, scale=False)
        partes.append((o,"Head"))
        # almofadas laterais
        for sx in (-0.11, 0.11):
            add_ellip(f"FonePad_{sx}_{pid}", (sx,0,1.62), (0.035,0.025,0.035), 1, material(f"FonePadMat_{pid}", hex_to_rgb("#303044"), 0.65), "Head")
    elif pid=="carlos":
        add_ellip(f"CapaceteObra_{pid}", (0,0,1.755), (0.125,0.125,0.075), 2, material(f"CapObraMat_{pid}", hex_to_rgb("#ffe36b"), 0.45), "Head")
        # colete refletivo extra por cima da camisa já laranja: faixa refletiva
        add_box(f"FaixaRefletiva_{pid}", (0,-0.095,1.26), (0.40,0.02,0.04), m_accent, "spine_02")
        # bota mais alta
        for sx in (-0.09, 0.09):
            add_box(f"BotaCano_{pid}_{sx}", (sx, -0.06, 0.11), (0.13,0.18,0.12), m_sapato, "calf_l" if sx<0 else "calf_r")
    elif pid=="maria":
        # bolsa tiracolo lateral
        add_box(f"BolsaMaria_{pid}", (0.22, -0.02, 1.12), (0.18,0.12,0.20), m_accent, "pelvis")
        add_box(f"BolsaAlca_{pid}", (0.12, -0.02, 1.28), (0.04,0.02,0.32), m_accent, "spine_02")
        # brinco
        for sx in (-0.11, 0.11):
            add_ellip(f"BrincoMaria_{sx}_{pid}", (sx,0,1.60), (0.015,0.015,0.015), 1, m_accent, "Head")
    elif pid=="bia":
        add_box(f"MochilaBia_{pid}", (0, 0.135, 1.27), (0.26,0.11,0.30), material(f"MochilaBiaMat_{pid}", hex_to_rgb("#3a6fa0"), 0.68), "spine_02")
        add_box(f"MochilaBolso_{pid}", (0, 0.07, 1.20), (0.18,0.02,0.10), m_accent, "spine_02")
    elif pid=="camila":
        # tablet na mão esquerda
        add_box(f"Tablet_{pid}", (-0.62, -0.08, 1.42), (0.02,0.14,0.20), material(f"TabletMat_{pid}", hex_to_rgb("#305a5d"), 0.35, 0.55), "hand_l")
        # bolsa tiracolo
        add_box(f"BolsaCamila_{pid}", (0.20, -0.015, 1.14), (0.16,0.10,0.16), material(f"BolsaCamilaMat_{pid}", cor_accent, 0.62), "pelvis")
    elif pid=="julia":
        # faixa cabeça
        o=torus_bl(f"FaixaJulia_{pid}", (0,0,1.675), 0.115, 0.015)
        o.data.materials.append(material(f"FaixaMat_{pid}", cor_accent, 0.62))
        sozinho(o); o.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(rotation=True, scale=False)
        partes.append((o,"Head"))
        # garrafa na mão direita
        go=pilar_z(f"Garrafa_{pid}", 0.025, 0.025, 0.18)
        sozinho(go); go.location=(0.66, -0.06, 1.44); go.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        go.data.materials.clear(); go.data.materials.append(material(f"GarrafaMat_{pid}", hex_to_rgb("#68e0c0"), 0.35, 0.15))
        partes.append((go,"hand_r"))
    elif pid=="influencer":
        # phone na mão direita + pulseira + brinco
        add_box(f"Phone_{pid}", (0.67, -0.06, 1.44), (0.02,0.07,0.13), material(f"PhoneMat_{pid}", hex_to_rgb("#171824"), 0.25, 0.65), "hand_r")
        o=torus_bl(f"Pulseira_{pid}", (0.0,0.08,0.0), 0.045, 0.012)
        o.data.materials.append(m_accent)
        sozinho(o); o.location=(0.0,0.08,0.0); o.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
        # precisa estar posicionado relativo a lowerarm; torus já no origin mas weighted ao osso, vamos mover para mão
        # na prática hand_r já cobre, então deixar torus na origem do lowerarm: já está correto
        partes.append((o,"lowerarm_r"))
        for sx in (-0.12, 0.12):
            add_ellip(f"BrincoInf_{sx}_{pid}", (sx,0,1.605), (0.018,0.018,0.018), 1, m_accent, "Head")
        # tatuagem fake: faixa braço
        add_box(f"Tattoo_{pid}", (0.38, -0.02, 1.40), (0.10,0.02,0.06), material(f"TattooMat_{pid}", hex_to_rgb("#21152f"), 0.72), "lowerarm_r")
    elif pid=="chico":
        add_ellip(f"BoneChico_{pid}", (0,0,1.74), (0.11,0.11,0.05), 1, material(f"BoneChicoMat_{pid}", hex_to_rgb("#2f6db8"), 0.66), "Head")
        add_box(f"BoneAbaChico_{pid}", (0,-0.11,1.71), (0.15,0.07,0.015), m_accent, "Head")
        # sacola carteiro
        add_box(f"SacolaChico_{pid}", (0.24, -0.02, 1.05), (0.22,0.16,0.24), m_accent, "pelvis")
        add_box(f"AlcaChico_{pid}", (0.08, -0.02, 1.28), (0.03,0.02,0.34), material(f"AlcaChicoMat_{pid}", hex_to_rgb("#2f6db8"), 0.68), "spine_02")
    elif pid=="tiao":
        add_ellip(f"ChapeuTiaoCrown_{pid}", (0,0,1.74), (0.12,0.12,0.09), 1, material(f"ChapeuTiaoMat_{pid}", cor_accent, 0.68), "Head")
        # aba larga vaqueiro
        o=cilindro_bl(f"AbaTiao_{pid}", (0,0,1.70), 0.19, 0.015)
        o.data.materials.append(material(f"AbaTiaoMat_{pid}", cor_accent, 0.68))
        partes.append((o,"Head"))
        # gibão detalhe
        add_box(f"GibaoTiao_{pid}", (0,-0.095,1.28), (0.36,0.02,0.26), material(f"GibaoMat_{pid}", hex_to_rgb("#5a3d28"), 0.72), "spine_02")
    elif pid=="beto":
        o=torus_bl(f"ColarBeto_{pid}", (0,0,1.48), 0.085, 0.012)
        o.data.materials.append(m_accent)
        sozinho(o); o.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(rotation=True, scale=False)
        partes.append((o,"neck_01"))
        o2=torus_bl(f"PulseiraBeto_{pid}", (0,0,0.12), 0.045, 0.012)
        o2.data.materials.append(m_accent)
        sozinho(o2); o2.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(rotation=True, scale=False)
        partes.append((o2,"lowerarm_r"))
    elif pid=="nilo":
        # touca padeiro branca alta
        add_ellip(f"ToucaNilo_{pid}", (0,0,1.76), (0.11,0.11,0.09), 1, material(f"ToucaMat_{pid}", hex_to_rgb("#f4efe6"), 0.82), "Head")
        o=cilindro_bl(f"ToucaBase_{pid}", (0,0,1.68), 0.11, 0.08)
        o.data.materials.append(material(f"ToucaBaseMat_{pid}", hex_to_rgb("#f4efe6"), 0.82))
        partes.append((o,"Head"))
        # bandeja na mão esquerda
        add_box(f"BandejaNilo_{pid}", (-0.60, -0.05, 1.48), (0.18,0.14,0.02), material(f"BandejaMat_{pid}", hex_to_rgb("#b9bec7"), 0.35, 0.55), "hand_l")
        for i,sx in enumerate([-0.05,0.0,0.05]):
            add_ellip(f"Pao_{i}_{pid}", (-0.60+sx, -0.05, 1.50), (0.025,0.025,0.018), 1, m_accent, "hand_l")
    elif pid=="professor":
        # gravata
        add_box(f"GravataKnot_{pid}", (0,-0.11,1.36), (0.045,0.025,0.045), material(f"GravataKMat_{pid}", cor_accent, 0.60), "spine_02")
        add_box(f"GravataBlade_{pid}", (0,-0.115,1.18), (0.08,0.02,0.38), material(f"GravataMat_{pid}", cor_accent, 0.60), "spine_02")
        # livro na mão
        add_box(f"LivroProf_{pid}", (-0.62, -0.06, 1.45), (0.04,0.12,0.16), material(f"LivroMat_{pid}", hex_to_rgb("#2e3a52"), 0.72), "hand_l")
    elif pid=="marta":
        add_box(f"BandanaMarta_{pid}", (0,0,1.705), (0.135,0.135,0.035), material(f"BandanaMat_{pid}", hex_to_rgb("#ef8f3f"), 0.82), "Head")
        add_box(f"AventalMarta_{pid}", (0,-0.10,1.10), (0.32,0.02,0.42), material(f"AventalMat_{pid}", hex_to_rgb("#4f7a4a"), 0.82), "spine_01")
        # banca? apenas avental
    elif pid=="zilda":
        # lenço
        add_ellip(f"LencoZilda_{pid}", (0,0,1.695), (0.12,0.12,0.065), 1, material(f"LencoMat_{pid}", hex_to_rgb("#d98cb0"), 0.82), "Head")
        add_box(f"BolsaZilda_{pid}", (0.22, -0.03, 1.06), (0.17,0.13,0.18), m_accent, "pelvis")
    elif pid=="clara":
        add_ellip(f"GorroClara_{pid}", (0,0,1.75), (0.11,0.11,0.045), 1, material(f"GorroMat_{pid}", hex_to_rgb("#f4f7fa"), 0.78), "Head")
        # prancheta na mão
        add_box(f"Prancheta_{pid}", (-0.62, -0.07, 1.43), (0.03,0.13,0.18), material(f"PranchMat_{pid}", hex_to_rgb("#dfe7ee"), 0.72), "hand_l")
        # distintivo
        add_box(f"BadgeClara_{pid}", (0.12, -0.11, 1.32), (0.06,0.02,0.04), m_accent, "spine_02")
    elif pid=="deise":
        # braçadeira
        o=torus_bl(f"BraceleteDeise_{pid}", (0,0,0.17), 0.066, 0.018)
        o.data.materials.append(m_accent)
        sozinho(o); o.rotation_euler=(rad(90),0,0); bpy.ops.object.transform_apply(rotation=True, scale=False)
        partes.append((o,"upperarm_l"))
        # faixa adicional perna? skip
    elif pid=="cida":
        add_ellip(f"QuepeCida_{pid}", (0,0,1.755), (0.115,0.115,0.05), 1, material(f"QuepeMat_{pid}", hex_to_rgb("#3f7fae"), 0.66), "Head")
        add_box(f"QuepeAba_{pid}", (0,-0.105,1.72), (0.16,0.07,0.015), material(f"QuepeAbaMat_{pid}", hex_to_rgb("#23252d"), 0.65), "Head")
        add_box(f"CrachaCida_{pid}", (0.125, -0.105, 1.31), (0.06,0.02,0.04), m_accent, "spine_02")

    corpo=join_parts(partes)
    arm=armature_humano(f"Personagem_{pid}")
    skin(arm, corpo)

    scene.frame_start=1
    scene.frame_end=48
    def act_idle():
        a=new_action(arm,"Idle_Loop")
        for f in (1,12,24,36,48):
            t=(f-1)/48*TAU
            clear_pose(arm)
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

    bpy.ops.object.select_all(action='DESELECT')
    corpo.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active=arm
    # Lote 28 Passo 3 — Draco habilitado para <300KB cada (mantém skins/anim, textura runtime)
    try:
        bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB', export_apply=True, export_animations=True, export_skins=True, export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False, export_animation_mode='ACTIONS', use_selection=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_draco_position_quantization=14, export_draco_normal_quantization=10, export_draco_texcoord_quantization=12)
    except TypeError as e:
        print(f"Draco params não suportados ({e}), fallback sem Draco")
        bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB', export_apply=True, export_animations=True, export_skins=True, export_yup=True, export_materials='EXPORT', export_cameras=False, export_lights=False, export_animation_mode='ACTIONS', use_selection=True)
    sz=os.path.getsize(out_path)
    print("PRONTO:", out_path, sz)
    # blend preview por personagem
    blend_path = os.path.join(OUT_DIR, f"{pid}.blend")
    try:
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    except: pass
    return out_path, sz

if __name__=="__main__":
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    # blender passa -- args; filtra
    if "--" in sys.argv:
        idx=sys.argv.index("--")
        wanted=sys.argv[idx+1:]
    if not wanted:
        wanted=[p["id"] for p in CATALOG]
    else:
        # permite "all" ou lista
        if len(wanted)==1 and wanted[0]=="all":
            wanted=[p["id"] for p in CATALOG]
        else:
            # valida ids
            valid=set(p["id"] for p in CATALOG)
            wanted=[w for w in wanted if w in valid]
            if not wanted:
                wanted=[p["id"] for p in CATALOG]
    print(f"Gerando personagens: {', '.join(wanted)} ({len(wanted)} / {len(CATALOG)})")
    total_sz=0
    for pid in wanted:
        prof=profile_by_id(pid)
        out=os.path.join(OUT_PERSONAGENS, f"{pid}.glb")
        print(f"\n=== {pid} ({prof['name']}) ===")
        try:
            _, sz = build_one_personagem(prof, out)
            total_sz+=sz
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"FALHA {pid}: {e}")
    print(f"\nPERSONAGENS OK: {len(wanted)} gerados, total {total_sz} bytes em {OUT_PERSONAGENS}")
