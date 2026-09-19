# Kit base para modelar assets 3D por codigo (Blender 4.5 headless).
# Reusa a tecnica do build_pombo.py (corpo loftero por secoes, partes com
# grupos de vertices, rig, clips e export GLB). Rodar via:
#   tools/blender/run_bpy.sh tools/blender/<script>.py
import bpy, math, os
from pathlib import Path
from mathutils import Vector

D = bpy.data
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = str(REPO / "tools" / "blender" / "out")

TAU = math.tau
def rad(d): return math.radians(d)

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

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene

MATS = {}
def material(nome, cor, rough=0.62, metal=0.0):
    m = D.materials.get(nome) or D.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    MATS[nome] = m
    return m

def pintar(o, mat):
    o.data.materials.append(mat)

# ------------------------------------------------------------------ geometria
def loft(nome, secoes, seg=14, tampas=True):
    """Corpo loftero: secoes = [(y, z_centro, meia_largura_x, meia_altura_z), ...]
    do fim (cauda) para a frente (peito/cabeca)."""
    verts, faces = [], []
    for (y, cz, w, h) in secoes:
        for k in range(seg):
            a = k / seg * TAU
            verts.append((w * math.cos(a), y, cz + h * math.sin(a)))
    for s in range(len(secoes) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((s * seg + k, s * seg + k2, (s + 1) * seg + k2, (s + 1) * seg + k))
    if tampas:
        faces.append(tuple(range(seg - 1, -1, -1)))
        faces.append(tuple(range(len(secoes) * seg - 1, (len(secoes) - 1) * seg - 1, -1)))
    o = novo_obj(nome, malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = 2; mm.quality = 4
    return o

def elipsoide(nome, centro, raios, nivel=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=centro)
    o = bpy.context.active_object
    o.name = nome
    sozinho(o)
    o.scale = raios
    # Atencao: transform_apply tem defaults True para location/rotation.
    # Aplicar location aqui colocaria a origem do objeto no mundo (0,0,0) e
    # qualquer rotacao feita depois orbitaria a peca em torno da origem.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = nivel; mm.quality = 4
    return o

def pilar(nome, r_base, r_topo_rel, seg=10):
    """Cilindro cônico unitario (base no plano z=0, topo em z=1).
    As tampas usam vertice central + leque de triangulos: com n-gons, o
    subsurf colapsa a tampa e pincha a ponta (pernas viravam espetas)."""
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
    cb = len(verts); verts.append((0.0, 0.0, 0.0))
    ct = len(verts); verts.append((0.0, 0.0, 1.0))
    for k in range(seg):
        k2 = (k + 1) % seg
        faces.append((cb, k2, k))             # base, normal -Z
        faces.append((ct, seg + k, seg + k2))  # topo, normal +Z
    o = novo_obj(nome, malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = 1
    return o

def painel_pena(nome, comprimento, meia_largura, ponta=0.35):
    w = meia_largura
    verts = [(-w, -comprimento * 0.28, 0), (w, -comprimento * 0.28, 0),
             (w * 0.92, comprimento * 0.30, 0), (-w * 0.92, comprimento * 0.30, 0),
             (w * ponta, comprimento, 0), (-w * ponta, comprimento, 0)]
    faces = [(0, 1, 2, 3), (3, 2, 4), (2, 1, 4), (0, 3, 5), (3, 4, 5)]
    o = novo_obj(nome, malha(nome, verts, faces))
    mm = o.modifiers.new("Subd", 'SUBSURF'); mm.levels = mm.render_levels = 1
    return o

def cone_part(nome, r1, r2, profundidade, verts_n=10):
    bpy.ops.mesh.primitive_cone_add(vertices=verts_n, radius1=r1, radius2=r2,
                                    depth=profundidade, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = nome
    sozinho(o)
    return o

# ------------------------------------------------------------------ montagem
def join_parts(partes):
    """partes = [(objeto, grupo), ...]. Aplica modificadores, junta em um
    unico objeto e cria grupos de vertices (um por grupo de partes)."""
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
    corpo = bpy.context.active_object
    total = sum(contagens)
    assert len(corpo.data.vertices) == total, "join alterou vertices!"
    idx = 0
    for (_, grupo), n in zip(partes, contagens):
        vg = corpo.vertex_groups.get(grupo) or corpo.vertex_groups.new(name=grupo)
        vg.add(list(range(idx, idx + n)), 1.0, 'REPLACE')
        idx += n
    print("VERTICES:", total)
    return corpo

def armature(nome, ossos):
    """ossos = [(nome, head, tail, parent|None), ...]"""
    arm_data = D.armatures.new(nome + "Rig")
    arm = D.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    sozinho(arm)
    bpy.ops.object.mode_set(mode='EDIT')
    for (nm, head, tail, parent) in ossos:
        b = arm_data.edit_bones.new(nm)
        b.head = head; b.tail = tail; b.roll = 0.0
        if parent:
            b.parent = arm_data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, mesh_obj):
    mesh_obj.parent = arm
    mod = mesh_obj.modifiers.new("Skin", 'ARMATURE')
    mod.object = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    bpy.ops.object.mode_set(mode='OBJECT')

def key_rot(arm, pbnome, frame, euler):
    pb = arm.pose.bones[pbnome]
    pb.rotation_euler = euler
    pb.keyframe_insert('rotation_euler', frame=frame)

def key_loc(arm, pbnome, frame, loc):
    pb = arm.pose.bones[pbnome]
    pb.location = loc
    pb.keyframe_insert('location', frame=frame)

def clear_pose(arm):
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')

def new_action(arm, nome, first_action=True):
    a = D.actions.new(nome)
    arm.animation_data_create()
    if first_action:
        arm.animation_data.action = a
    return a

def linearize(action):
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

def export_glb(caminho, nodes, preview_blend=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in nodes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = nodes[0]
    bpy.ops.export_scene.gltf(
        filepath=caminho, export_format='GLB', export_apply=True,
        export_animations=True, export_skins=True, export_yup=True,
        export_materials='EXPORT', export_cameras=False, export_lights=False,
        export_animation_mode='ACTIONS', use_selection=True,
    )
    if preview_blend:
        bpy.ops.wm.save_as_mainfile(filepath=preview_blend)
    print("PRONTO:", caminho, os.path.getsize(caminho), "bytes")
    return caminho

# ------------------------------------------------------------------ preview
def setup_preview(fundo=(0.38, 0.45, 0.58, 1.0), energia_fundo=0.38):
    mundo = D.worlds.new("Mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = fundo
    mundo.node_tree.nodes["Background"].inputs[1].default_value = energia_fundo
    bpy.context.scene.world = mundo
    sol = D.lights.new("Sol", 'SUN'); sol.energy = 1.7; sol.angle = rad(12)
    sol_o = D.objects.new("Sol", sol); bpy.context.scene.collection.objects.link(sol_o)
    sol_o.rotation_euler = (rad(48), 0, rad(-38))
    cheia = D.lights.new("Cheia", 'AREA'); cheia.energy = 9; cheia.size = 0.8
    cheia_o = D.objects.new("Cheia", cheia); bpy.context.scene.collection.objects.link(cheia_o)
    cheia_o.location = (-0.30, -0.35, 0.35)
    cheia_o.rotation_euler = (rad(55), 0, rad(-50))
    import bmesh
    piso_me = D.meshes.new("Piso"); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bm.to_mesh(piso_me); bm.free()
    piso = novo_obj("Piso", piso_me)
    pmat = D.materials.new("PisoMat"); pmat.use_nodes = True
    pmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.50, 0.47, 1)
    pmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    piso.data.materials.append(pmat)
    cam_data = D.cameras.new("Cam"); cam_data.lens = 85
    cam = D.objects.new("Camera", cam_data); bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.samples = 24
    bpy.context.scene.render.resolution_x = 640
    bpy.context.scene.render.resolution_y = 480
    bpy.context.scene.view_settings.view_transform = 'Standard'
    return cam

def render_de(cam, loc, alvo, caminho):
    cam.location = loc
    cam.rotation_euler = (Vector(alvo) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.render.filepath = caminho
    bpy.ops.render.render(write_still=True)
