#!/usr/bin/env python3
"""Gera a heroína Júlia (mesh-only) — ETAPA 1: personagem correta no mundo.

Convenção do pipeline (igual ao elenco GLB de personagens/):
  - Y é o eixo vertical; pés em y=0; altura total ~1.68 m (com cabelo).
  - Personagem encarando +Z (o runtime aplica MODEL_FACING_YAW=PI e ela sai
    olhando para a direção da corrida, -Z).
  - Cada parte vira um nó cuja ORIGEM fica na articulação (pivô) e a malha é
    local a ela — _mesh_rotate() em runner_character.gd balança coxa/canela/
    braço em torno do quadril/joelho/ombro/cotovelo de verdade (antes todos os
    pivôs estavam em (0,0,0) e o membro inteiro orbitava o mundo).
  - Ordem de transformação: rotaciona (Z-up primitivo -> Y-up) -> escala nos
    eixos de MUNDO (x=largura, y=altura, z=profundidade) -> translação. O
    gerador antigo escalava depois de transladar (rosto deformado) e passava a
    altura no eixo Z (boneca deitada no mundo).
  - Nomes de nó EXATOS esperados pelo jogo: LeftThigh, RightThigh, LeftCalf,
    RightCalf, UpperArmL/R, ForearmL/R, Torso (animados) + Pelvis, Neck, Head,
    Nose, EyeWhite, Iris, HairCap, HairSide, HandL/R, SneakerL/R, SoleL/R.
    Pares simétricos (EyeWhite, Iris, HairSide) são UM nó com duas primitivas —
    nomes duplicados faziam o trimesh engolir o lado esquerdo.
"""
from pathlib import Path

import numpy as np
import trimesh

OUT = Path(__file__).resolve().parents[1] / "assets/characters/personagens/hero_julia.glb"

# Altura-alvo da figura pronta (com cabelo). Runtime = 1.68 * MODEL_SCALE(1.03)
# ≈ 1.73 m — dentro da faixa 1.68-1.75 do PLANO_HEROI_REALISTA.
TARGET_H = 1.68
_design_h = 1.955  # topo do HairCap nas unidades de design abaixo
S = TARGET_H / _design_h

parts = []


def mat(name, color, rough=.7):
    return trimesh.visual.material.PBRMaterial(
        name=name, baseColorFactor=(*color, 255), roughnessFactor=rough)


skin = mat('Skin', (0.56, 0.30, 0.20), .58)
shirt = mat('Shirt', (0.70, 0.06, 0.10), .82)
pants = mat('Jeans', (0.035, 0.07, 0.13), .9)
shoe = mat('Sneaker', (0.04, 0.045, 0.05), .72)
hair = mat('Hair', (0.035, 0.012, 0.008), .72)
white = mat('EyeWhite', (.94, .94, .90), .25)
iris = mat('Iris', (.08, .025, .012), .2)
sole = mat('Sole', (.015, .018, .02), .9)

R_UP = trimesh.transformations.rotation_matrix(-np.pi / 2.0, [1, 0, 0])


def part(name, mesh, material, center, pivot, scale=None):
    """Uma peça: gira Z-up para Y-up -> escala em eixos de mundo -> malha local
    ao pivô. center/pivot em unidades de design (Y vertical, rosto para +Z).
    O nó sai com matrix/translation=pivot*S; a malha fica relativa a ele.
    """
    mesh.apply_transform(R_UP)           # cápsula/eixo Z -> vertical Y
    if scale is not None:
        mesh.apply_scale(scale)          # eixos de MUNDO: (largura, altura, profundidade)
    mesh.apply_scale(S)                  # escala global: design -> TARGET_H
    center = np.asarray(center, float) * S
    pivot = np.asarray(pivot, float) * S
    mesh.apply_translation(center - pivot)  # malha local ao pivô
    mesh.visual.material = material
    parts.append((name, mesh, pivot))


def capsule(radius, height):
    return trimesh.creation.capsule(radius=radius, height=height, count=[16, 8])


def sph(r):
    return trimesh.creation.icosphere(subdivisions=2, radius=r)


def cyl(r, h):
    return trimesh.creation.cylinder(radius=r, height=h, sections=20)


# ---------------- corpo: pernas, quadril, tronco ----------------
# pivôs reais: quadril .93 / joelho .47 / cintura 1.00 / ombro 1.55 / cotovelo 1.27
for x, side in ((-.105, 'Left'), (.105, 'Right')):
    part(f'{side}Thigh', capsule(.115, .52), pants,
         (x, .70, 0), (x, .93, 0))
    part(f'{side}Calf', capsule(.085, .45), pants,
         (x, .31, 0), (x, .47, 0))
part('Pelvis', sph(.20), pants, (0, .98, 0), (0, .98, 0), scale=(1.0, .72, .72))
part('Torso', capsule(.22, .55), shirt, (0, 1.28, 0), (0, 1.00, 0),
     scale=(1.0, 1.0, .72))

# ---------------- pescoço, cabeça, rosto para +Z ----------------
part('Neck', cyl(.075, .13), skin, (0, 1.62, 0), (0, 1.56, 0))
part('Head', sph(.145), skin, (0, 1.78, 0), (0, 1.62, 0),
     scale=(.92, 1.02, .90))
part('Nose', sph(.045), skin, (0, 1.77, .13), (0, 1.77, .13),
     scale=(.65, .72, .45))
# olhos/íris: um nó por nome (dois lados = duas primitivas na MESMA malha)
eyes = trimesh.util.concatenate([
    sph(.027).apply_translation((x, 0, 0)) for x in (-.052, .052)])
part('EyeWhite', eyes, white, (0, 1.825, .125), (0, 1.825, .125),
     scale=(1, .78, .35))
irises = trimesh.util.concatenate([
    sph(.012).apply_translation((x, 0, 0)) for x in (-.052, .052)])
part('Iris', irises, iris, (0, 1.825, .143), (0, 1.825, .143))

# ---------------- cabelo (volume atrás do rosto) ----------------
part('HairCap', sph(.153), hair, (0, 1.86, -.01), (0, 1.86, -.01),
     scale=(1.0, .62, .98))
sides = trimesh.util.concatenate([
    sph(.055).apply_translation((x, 0, 0)) for x in (-.13, .13)])
part('HairSide', sides, hair, (0, 1.78, -.02), (0, 1.78, -.02),
     scale=(.65, 1.5, .8))

# ---------------- braços (pivô ombro/cotovelo/punho) ----------------
for x, side in ((-.265, 'L'), (.265, 'R')):
    part(f'UpperArm{side}', capsule(.07, .38), shirt,
         (x, 1.38, 0), (x, 1.55, 0), scale=(1, 1, .9))
    part(f'Forearm{side}', capsule(.055, .34), skin,
         (x, 1.10, 0), (x, 1.27, 0))
    part(f'Hand{side}', sph(.065), skin,
         (x, .88, 0), (x, .95, 0), scale=(.8, 1.0, .6))

# ---------------- tênis com sola e bico (dedos para +Z) ----------------
for x, side in ((-.105, 'L'), (.105, 'R')):
    part(f'Sneaker{side}', sph(.12), shoe,
         (x, .05, .045), (x, .05, .045), scale=(.82, .42, 1.45))
    part(f'Sole{side}', sph(.122), sole,
         (x, .02, .05), (x, .02, .05), scale=(.84, .18, 1.48))

scene = trimesh.Scene()
for name, mesh, pivot in parts:
    scene.add_geometry(
        mesh, node_name=name,
        transform=trimesh.transformations.translation_matrix(pivot))

OUT.parent.mkdir(parents=True, exist_ok=True)
scene.export(OUT, file_type='glb')
print(f'hero_julia.glb gerado: {OUT} ({OUT.stat().st_size} bytes, escala {S:.3f})')
