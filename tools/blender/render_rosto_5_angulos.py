#!/usr/bin/env python3
"""Renderiza 5 fotos de validação do rosto da heroína Júlia.

Uso:
  tools/blender/run_bpy.sh tools/blender/render_rosto_5_angulos.py \
      tools/blender/out/heroi_julia_pbr.glb docs/arte_alvo_final --prefix rosto_fase3

Gera cinco PNGs em ângulos diferentes e um contato horizontal. A câmera fica a
2 m do alvo (gate da Fase 3) com focal longa para close de rosto sem distorção.
"""
import argparse
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWS = [
    ("perfil_esq", -72.0),
    ("tres_quartos_esq", -36.0),
    ("frente", 0.0),
    ("tres_quartos_dir", 36.0),
    ("perfil_dir", 72.0),
]


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


def face_target(objs):
    (x0, x1), (y0, y1), (z0, z1) = bbox(objs)
    h = z1 - z0
    # Centro anatômico do rosto completo (olhos+nariz+boca), não da franja.
    return Vector((0.0, y0 + (y1 - y0) * 0.18, z0 + h * 0.914))


def look_at(cam, target):
    vazio = bpy.data.objects.new(f"Alvo_{cam.name}", None)
    vazio.location = target
    bpy.context.scene.collection.objects.link(vazio)
    con = cam.constraints.new("TRACK_TO")
    con.target = vazio
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"


def estudio(scene, res_x, res_y, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = -0.85
    scene.view_settings.gamma = 1.0

    world = bpy.data.worlds.new("EstudioRosto")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.70, 0.72, 0.74, 1.0)
    bg.inputs["Strength"].default_value = 0.24

    luzes = [
        ("Key", (2.0, -2.2, 2.6), 120, 1.6),
        ("Fill", (-1.8, -1.9, 1.7), 24, 2.4),
        ("Rim", (-2.1, 1.8, 2.3), 42, 1.8),
        ("EyeCatch", (0.0, -1.4, 1.70), 12, 0.22),
    ]
    for nome, loc, energy, size in luzes:
        l = bpy.data.lights.new(nome, "AREA")
        l.energy = energy
        l.size = size
        o = bpy.data.objects.new(nome, l)
        o.location = loc
        scene.collection.objects.link(o)
        direction = Vector((0, -0.06, 1.58)) - Vector(loc)
        o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera_para(scene, target, yaw_deg, distancia=2.0):
    cam_data = bpy.data.cameras.new(f"Cam_{yaw_deg:+.0f}")
    cam_data.lens = 190
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = distancia
    cam_data.dof.aperture_fstop = 8.0
    cam = bpy.data.objects.new(cam_data.name, cam_data)
    a = math.radians(yaw_deg)
    # Frente do personagem = -Y. Altura 2 cm acima do alvo para ver pálpebras.
    cam.location = target + Vector((math.sin(a) * distancia, -math.cos(a) * distancia, 0.018))
    scene.collection.objects.link(cam)
    scene.camera = cam
    look_at(cam, target)
    return cam


def renderizar(glb: Path, out_dir: Path, prefix: str, res_x: int, res_y: int, samples: int):
    limpar()
    scene = bpy.context.scene
    objs = importar(glb)
    target = face_target(objs)
    print(f"[rosto5] alvo: ({target.x:.3f}, {target.y:.3f}, {target.z:.3f})")
    estudio(scene, res_x, res_y, samples)
    out_dir.mkdir(parents=True, exist_ok=True)

    saidas = []
    for i, (nome, yaw) in enumerate(VIEWS, start=1):
        for o in list(scene.objects):
            if o.type == "CAMERA" or o.name.startswith("Alvo_Cam_"):
                bpy.data.objects.remove(o, do_unlink=True)
        camera_para(scene, target, yaw)
        saida = out_dir / f"{prefix}_{i}_{nome}.png"
        scene.render.filepath = str(saida)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        bpy.ops.render.render(write_still=True)
        print(f"[rosto5] {saida}")
        saidas.append(saida)

    # Contato horizontal com as 5 fotos, para revisão rápida no viewer.
    largura = res_x * len(saidas)
    contato = bpy.data.images.new(f"{prefix}_contato", largura, res_y)
    px = [0.0] * (largura * res_y * 4)
    for i, caminho in enumerate(saidas):
        img = bpy.data.images.load(str(caminho))
        src = list(img.pixels)
        for y in range(res_y):
            lin_src = y * res_x * 4
            lin_dst = (y * largura + i * res_x) * 4
            px[lin_dst:lin_dst + res_x * 4] = src[lin_src:lin_src + res_x * 4]
        bpy.data.images.remove(img)
    contato.pixels = px
    contato_path = out_dir / f"{prefix}_contato_5_angulos.png"
    contato.filepath_raw = str(contato_path)
    contato.file_format = "PNG"
    contato.save()
    print(f"[rosto5] contato {contato_path}")
    return saidas, contato_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("out_dir")
    ap.add_argument("--prefix", default="rosto_fase3")
    ap.add_argument("--res-x", type=int, default=780)
    ap.add_argument("--res-y", type=int, default=960)
    ap.add_argument("--samples", type=int, default=40)
    args = ap.parse_args([a for a in sys.argv[1:] if not a.endswith(".py")])
    renderizar(Path(args.glb).resolve(), Path(args.out_dir).resolve(), args.prefix,
               args.res_x, args.res_y, args.samples)


if __name__ == "__main__":
    main()
