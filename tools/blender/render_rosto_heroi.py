#!/usr/bin/env python3
"""Render de revisão do rosto da Júlia, em três ângulos de close.

O script é separado do turnaround de corpo inteiro para a validação da Fase 3A
ser honesta: ele mostra só face/pescoço e não deixa roupa ou cabelo distrair da
anatomia facial.

Uso:
  sh tools/blender/run_bpy.sh tools/blender/render_rosto_heroi.py \
    tools/blender/out/heroi_julia_rosto.glb docs/arte_alvo_final/12_fase3_rosto.png
"""
import math
import os
import sys
from pathlib import Path

import bpy

REPO = Path(__file__).resolve().parents[2]
RES = 620
SAMPLES = 32
VIEWS = (("frente", 0.0), ("3_4", 28.0), ("perfil", 72.0))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objs:
        raise SystemExit(f"sem malha em {path}")
    return objs


def studio(scene):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("StudioFace")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.055, 0.070, 0.085, 1.0)
    background.inputs["Strength"].default_value = 0.28

    def area(name, location, energy, size, color):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light_data.color = color
        light = bpy.data.objects.new(name, light_data)
        light.location = location
        scene.collection.objects.link(light)
        return light

    # A frente do modelo é -Y. As três luzes marcam pálpebra, nariz e boca sem
    # achatar o relevo em um estúdio branco.
    area("Key", (-0.42, -0.75, 1.92), 210, 0.38, (1.0, 0.72, 0.53))
    area("Fill", (0.48, -0.58, 1.72), 95, 0.46, (0.46, 0.65, 1.0))
    area("Rim", (-0.35, 0.28, 1.90), 135, 0.32, (1.0, 0.40, 0.24))


def camera(scene, angle_deg):
    target = bpy.data.objects.new("FaceTarget", None)
    target.location = (0.0, -0.035, 1.565)
    scene.collection.objects.link(target)

    camera_data = bpy.data.cameras.new("FaceCamera")
    camera_data.lens = 88
    camera_data.sensor_width = 36
    cam = bpy.data.objects.new("FaceCamera", camera_data)
    angle = math.radians(angle_deg)
    radius = 0.54
    cam.location = (radius * math.sin(angle), -radius * math.cos(angle) - 0.015, 1.59)
    scene.collection.objects.link(cam)
    constraint = cam.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    scene.camera = cam
    return cam, target


def save_triptych(tiles, output):
    width = RES * len(tiles)
    out = bpy.data.images.new("FaceReview", width, RES, alpha=True)
    pixels = [0.0] * (width * RES * 4)
    for i, tile in enumerate(tiles):
        img = bpy.data.images.load(str(tile), check_existing=False)
        source = list(img.pixels)
        for y in range(RES):
            source_line = y * RES * 4
            dest_line = (y * width + i * RES) * 4
            pixels[dest_line:dest_line + RES * 4] = source[source_line:source_line + RES * 4]
        bpy.data.images.remove(img)
    out.pixels = pixels
    out.filepath_raw = str(output)
    out.file_format = "PNG"
    out.save()


def main():
    if len(sys.argv) < 3:
        raise SystemExit("uso: render_rosto_heroi.py <entrada.glb> <saida.png>")
    source = Path(sys.argv[-2]).resolve()
    output = Path(sys.argv[-1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    reset()
    scene = bpy.context.scene
    import_glb(source)
    studio(scene)

    tiles = []
    for name, angle in VIEWS:
        cam, target = camera(scene, angle)
        tile = output.with_name(f"_{output.stem}_{name}.png")
        scene.render.filepath = str(tile)
        bpy.ops.render.render(write_still=True)
        tiles.append(tile)
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.objects.remove(target, do_unlink=True)

    save_triptych(tiles, output)
    for tile in tiles:
        os.remove(tile)
    print(f"[rosto-render] {output}")


if __name__ == "__main__":
    main()
