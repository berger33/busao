#!/usr/bin/env python3
"""Render close-up da mão/antebraço da heroína Júlia.

Uso:
  tools/blender/run_bpy.sh tools/blender/render_hand_closeup.py <glb> <saida.png> [l|r]

O render é usado como gate visual rápido para a correção de braços/mãos: palma
sem bloco quadrado aparente, dedos contínuos/arredondados e punho encaixado no
antebraço.
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(glb: Path):
    bpy.ops.import_scene.gltf(filepath=str(glb))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        raise SystemExit(f"sem malha em {glb}")
    return objs


def bounds_vertices(objs, side: str):
    sx = 1 if side == "r" else -1
    pts = []
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            if 0.70 <= w.z <= 0.95 and sx * w.x > 0.15:
                pts.append(w)
    if not pts:
        raise SystemExit("não encontrei vértices da mão para o close-up")
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)), (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    )


def look_at(cam, alvo):
    direction = alvo - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def estudio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 36
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1040
    scene.render.resolution_y = 780
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -1.15
    scene.view_settings.gamma = 1.0
    scene.render.film_transparent = False

    world = bpy.data.worlds.new("EstudioClose")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.64, 0.66, 1)
    bg.inputs["Strength"].default_value = 0.22

    for name, loc, rot, energy, size in [
        ("Key", (0.8, -1.6, 1.4), (60, 0, 28), 38, 1.1),
        ("Soft", (-0.7, -1.0, 1.0), (62, 0, -40), 16, 1.7),
        ("Rim", (0.8, 0.9, 1.2), (70, 0, 150), 24, 0.9),
    ]:
        l = bpy.data.lights.new(name, "AREA")
        l.energy = energy
        l.size = size
        o = bpy.data.objects.new(name, l)
        o.location = loc
        o.rotation_euler = tuple(math.radians(a) for a in rot)
        scene.collection.objects.link(o)


def render(glb: Path, saida: Path, side="r"):
    limpar()
    scene = bpy.context.scene
    objs = importar(glb)
    centro, bb = bounds_vertices(objs, side)
    estudio(scene)

    # plano cinza bem atrás só para leitura de silhueta; sem cruzar com o corpo
    bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0.22, 0.84), rotation=(math.radians(90), 0, 0))
    fundo = bpy.context.active_object
    mat = bpy.data.materials.new("Fundo")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.70, 0.71, 0.73, 1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    fundo.data.materials.append(mat)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 0.245
    cam = bpy.data.objects.new("Cam", cam_data)
    # câmera quase frontal, ligeiramente lateral para ver volume dos dedos
    sx = 1 if side == "r" else -1
    cam.location = (centro.x + sx * 0.030, centro.y - 0.72, centro.z + 0.030)
    scene.collection.objects.link(cam)
    scene.camera = cam
    look_at(cam, centro + Vector((sx * 0.010, -0.006, -0.006)))

    scene.render.filepath = str(saida)
    bpy.ops.render.render(write_still=True)
    print(f"[hand-closeup] {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("uso: render_hand_closeup.py <glb> <saida.png> [l|r]")
    args = [a for a in sys.argv[1:] if not a.endswith(".py")]
    side = args[2] if len(args) >= 3 else "r"
    if side not in ("l", "r"):
        raise SystemExit("side deve ser l ou r")
    render(Path(args[0]).resolve(), Path(args[1]).resolve(), side)
