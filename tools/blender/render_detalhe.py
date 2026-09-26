#!/usr/bin/env python3
"""Close-ups de detalhe da heroína (mão, rosto) a partir do GLB.

Complementa o render_turnaround.py (4 vistas de corpo inteiro) com enquadramentos
apertados para avaliar gates de detalhe: dedos separados, palma em laje, rosto
esculpido. Encontra a região alvo por heurística geométrica — na Fase 2 o GLB
ainda não tem rig/vertex groups para consultar.

Uso:
  tools/blender/run_bpy.sh tools/blender/render_detalhe.py <glb> <saida.png> \
      --alvo mao|rosto [--res 960] [--samples 64]
"""
import argparse
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_turnaround as rt  # reutiliza estudio() e importar()


def alvo_mao(objs):
    """Mão em +X: vértices externos na faixa de altura do punho (35–58% da altura)."""
    (_, _), (_, _), (z0, z1) = rt.bbox(objs)
    h = z1 - z0
    xs = [abs((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices]
    xmax = max(xs)
    pts = [
        (o.matrix_world @ v.co)
        for o in objs
        for v in o.data.vertices
        if (o.matrix_world @ v.co).x > 0.80 * xmax
        and z0 + 0.33 * h < (o.matrix_world @ v.co).z < z0 + 0.58 * h
    ]
    if not pts:
        raise SystemExit("regiao da mao (+X) vazia")
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    cz = sum(p.z for p in pts) / len(pts)
    return cx, cy, cz


def alvo_rosto(objs):
    """Rosto: metade frontal (-Y) do topo da cabeça (acima de 88% da altura)."""
    (_, _), (_, _), (z0, z1) = rt.bbox(objs)
    h = z1 - z0
    pts = [
        (o.matrix_world @ v.co)
        for o in objs
        for v in o.data.vertices
        if (o.matrix_world @ v.co).z > z0 + 0.88 * h and (o.matrix_world @ v.co).y < 0.0
    ]
    if not pts:
        raise SystemExit("regiao do rosto vazia (frente deveria ser -Y)")
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    cz = sum(p.z for p in pts) / len(pts)
    return cx, cy, cz


ALVOS = {
    "mao": (alvo_mao, (0.30, -0.26, 0.06), 70.0, 0.44),
    "rosto": (alvo_rosto, (0.12, -0.40, 0.02), 85.0, 0.46),
}


def render(glb: Path, saida: Path, nome_alvo: str, res: int, samples: int):
    rt.limpar()
    scene = bpy.context.scene
    objs = rt.importar(glb)
    achador, offset, lens, _ = ALVOS[nome_alvo]

    cx, cy, cz = achador(objs)
    print(f"[detalhe] alvo {nome_alvo}: centro ({cx:.3f}, {cy:.3f}, {cz:.3f})")

    rt.estudio(scene)
    scene.cycles.samples = samples
    scene.render.resolution_x = res
    scene.render.resolution_y = int(res * 832 / 960)  # proporção 12:10.4 ≈ close 4:3.5
    scene.render.film_transparent = True  # PNG RGBA, sem chão

    cam_data = bpy.data.cameras.new("CamDetalhe")
    cam_data.lens = lens
    cam = bpy.data.objects.new("CamDetalhe", cam_data)
    cam.location = (cx + offset[0], cy + offset[1], cz + offset[2])
    scene.collection.objects.link(cam)

    alvo = bpy.data.objects.new("AlvoDetalhe", None)
    alvo.location = (cx, cy, cz)
    scene.collection.objects.link(alvo)
    con = cam.constraints.new("TRACK_TO")
    con.target = alvo
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    scene.camera = cam

    scene.render.filepath = str(saida)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print(f"[detalhe] {saida}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("saida")
    ap.add_argument("--alvo", choices=sorted(ALVOS), default="mao")
    ap.add_argument("--res", type=int, default=960)
    ap.add_argument("--samples", type=int, default=64)
    args = ap.parse_args([a for a in sys.argv[1:] if not a.endswith(".py")])
    render(Path(args.glb).resolve(), Path(args.saida).resolve(),
           args.alvo, args.res, args.samples)


if __name__ == "__main__":
    main()
