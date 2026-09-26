#!/usr/bin/env python3
"""Turnaround comparativo de personagens (Fase 0/1 do docs/PLANO_HEROI_10_10.md).

Renderiza frente / 3-4 / lado / costas de um GLB em fundo neutro, com luz de
estúdio, e grava um PNG único por personagem em tools/blender/out/.

Uso:
  tools/blender/run_bpy.sh tools/blender/render_turnaround.py <glb> <saida.png> [--wire]
"""
import math
import os
import sys
from pathlib import Path

import bpy

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWS = [("frente", 0.0), ("tres_quartos", 40.0), ("lado", 90.0), ("costas", 180.0)]
RES = 520
SAMPLES = 24


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(glb: Path):
    bpy.ops.import_scene.gltf(filepath=str(glb))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        raise SystemExit(f"sem malha em {glb}")
    return objs


def bbox(objs):
    zs, xs, ys = [], [], []
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def estudio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = False
    scene.render.resolution_x = RES
    scene.render.resolution_y = int(RES * 1.6)
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"

    world = bpy.data.worlds.new("Estudio")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.82, 0.84, 0.86, 1.0)
    bg.inputs["Strength"].default_value = 0.45

    key = bpy.data.lights.new("Key", "AREA")
    key.energy = 110
    key.size = 2.2
    key_obj = bpy.data.objects.new("Key", key)
    key_obj.location = (2.4, -3.0, 3.0)
    key_obj.rotation_euler = (math.radians(52), 0, math.radians(38))
    scene.collection.objects.link(key_obj)

    rim = bpy.data.lights.new("Rim", "AREA")
    rim.energy = 70
    rim.size = 1.8
    rim_obj = bpy.data.objects.new("Rim", rim)
    rim_obj.location = (-2.6, 2.4, 2.4)
    rim_obj.rotation_euler = (math.radians(62), 0, math.radians(-140))
    scene.collection.objects.link(rim_obj)


def camera(scene, alvo_z, raio, ang_deg, altura):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 62
    cam = bpy.data.objects.new("Cam", cam_data)
    a = math.radians(ang_deg)
    cam.location = (raio * math.sin(a), -raio * math.cos(a), altura)
    scene.collection.objects.link(cam)
    scene.camera = cam
    dir_vec = bpy.data.objects.new("Alvo", None)
    dir_vec.location = (0, 0, alvo_z)
    scene.collection.objects.link(dir_vec)
    con = cam.constraints.new("TRACK_TO")
    con.target = dir_vec
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return cam


def render(glb: Path, saida: Path):
    limpar()
    scene = bpy.context.scene
    objs = importar(glb)
    (_, _), (_, _), (z0, z1) = bbox(objs)
    altura = z1 - z0
    estudio(scene)

    # chão para a sombra de contato
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, z0))
    chao = bpy.context.active_object
    mat = bpy.data.materials.new("Chao")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.79, 0.81, 1)
    chao.data.materials.append(mat)

    tiles = []
    for nome, ang in VIEWS:
        for o in list(scene.objects):
            if o.type == "CAMERA" or o.name == "Alvo":
                bpy.data.objects.remove(o, do_unlink=True)
        camera(scene, z0 + altura * 0.52, altura * 2.35, ang, z0 + altura * 0.55)
        alvo = OUT_DIR / f"_tile_{nome}.png"
        scene.render.filepath = str(alvo)
        bpy.ops.render.render(write_still=True)
        tiles.append(alvo)

    # Montagem horizontal das 4 vistas
    largura = RES * len(tiles)
    altura_px = int(RES * 1.6)
    montagem = bpy.data.images.new("turnaround", largura, altura_px)
    px = [0.0] * (largura * altura_px * 4)
    for i, t in enumerate(tiles):
        img = bpy.data.images.load(str(t))
        src = list(img.pixels)
        for y in range(altura_px):
            lin_src = y * RES * 4
            lin_dst = (y * largura + i * RES) * 4
            px[lin_dst:lin_dst + RES * 4] = src[lin_src:lin_src + RES * 4]
        bpy.data.images.remove(img)
    montagem.pixels = px
    montagem.filepath_raw = str(saida)
    montagem.file_format = "PNG"
    montagem.save()
    for t in tiles:
        os.remove(t)
    print(f"[turnaround] {saida}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("uso: render_turnaround.py <glb> <saida.png>")
    render(Path(sys.argv[-2]).resolve(), Path(sys.argv[-1]).resolve())
