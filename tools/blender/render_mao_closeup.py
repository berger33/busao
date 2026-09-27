#!/usr/bin/env python3
"""Render close-up da mão do herói Júlia.

Uso:
  tools/blender/run_bpy.sh tools/blender/render_mao_closeup.py <glb> <saida.png>
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

RES = 900
SAMPLES = 48


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(glb: Path):
    bpy.ops.import_scene.gltf(filepath=str(glb))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        raise SystemExit(f"sem malha em {glb}")
    return objs


def bbox(objs):
    xs, ys, zs = [], [], []
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def estudio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -1.35
    scene.view_settings.gamma = 1.0
    scene.render.film_transparent = False

    world = bpy.data.worlds.new("Estudio")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.78, 0.80, 0.82, 1.0)
    bg.inputs["Strength"].default_value = 0.20

    for name, loc, energy, size in [
        ("Key", (0.75, -0.95, 1.32), 24, 0.70),
        ("Fill", (-0.65, -0.45, 1.10), 8, 0.95),
        ("Rim", (0.15, 0.75, 1.15), 16, 0.65),
    ]:
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        obj = bpy.data.objects.new(name, light)
        obj.location = loc
        look_at(obj, (0.245, -0.015, 0.82))
        scene.collection.objects.link(obj)


def render(glb: Path, saida: Path, keep_material=False):
    limpar()
    scene = bpy.context.scene
    objs = importar(glb)
    if not keep_material:
        # No GLB base a cor pode vir em espaço diferente dependendo do importador.
        # Para avaliação anatômica da mão, fixamos um material de pele neutro.
        mat = bpy.data.materials.new("PeleCloseup")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.55, 0.31, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.58
        for o in objs:
            o.data.materials.clear()
            o.data.materials.append(mat)
    (x0, x1), (y0, y1), (z0, z1) = bbox(objs)
    # Escolhe a mão no lado +X. A câmera fica levemente na frente e à direita.
    alvo = (x1 - 0.075, -0.020, z0 + (z1 - z0) * 0.48)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 86
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 0.62
    cam_data.dof.aperture_fstop = 7.5
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (alvo[0] + 0.30, alvo[1] - 0.54, alvo[2] + 0.055)
    look_at(cam, alvo)
    scene.collection.objects.link(cam)
    scene.camera = cam

    estudio(scene)
    # Fundo/corpo: chão apenas para rebater luz, fica fora do enquadramento.
    bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0, z0 - 0.001))
    chao = bpy.context.active_object
    mat = bpy.data.materials.new("Chao")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.72, 0.73, 0.75, 1)
    chao.data.materials.append(mat)

    scene.render.filepath = str(saida)
    bpy.ops.render.render(write_still=True)
    print(f"[mao-closeup] {saida}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--keep-material"]
    keep = "--keep-material" in sys.argv
    pngs = [a for a in args if a.lower().endswith(".png")]
    glbs = [a for a in args if a.lower().endswith(".glb")]
    if not glbs or not pngs:
        raise SystemExit("uso: render_mao_closeup.py <glb> <saida.png> [--keep-material]")
    render(Path(glbs[-1]).resolve(), Path(pngs[-1]).resolve(), keep_material=keep)
