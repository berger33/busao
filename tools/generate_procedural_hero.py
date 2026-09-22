#!/usr/bin/env python3
"""Gera uma heroína humana mesh-only quando o Blender não está disponível.
É um fallback visual: proporções anatômicas, volumes arredondados e detalhes
faciais, exportados em GLB para validação dentro do jogo.
"""
from pathlib import Path
import sys
sys.path.insert(0, "/home/user/tools_py")
import trimesh
import numpy as np

OUT = Path(__file__).parents[1] / "assets/characters/personagens/hero_julia.glb"
parts = []

def mat(name, color, rough=.7):
    return trimesh.visual.material.PBRMaterial(name=name, baseColorFactor=(*color,255), roughnessFactor=rough)
skin=mat('Skin',(0.56,0.30,0.20),.58); shirt=mat('Shirt',(0.70,0.06,0.10),.82)
pants=mat('Jeans',(0.035,0.07,0.13),.9); shoe=mat('Sneaker',(0.04,0.045,0.05),.72)
hair=mat('Hair',(0.035,0.012,0.008),.72); white=mat('EyeWhite',(.94,.94,.90),.25)
iris=mat('Iris',(.08,.025,.012),.2); sole=mat('Sole',(.015,.018,.02),.9)

def add(mesh, material, pos=(0,0,0), scale=None, name='Part'):
    # trimesh cria cápsulas/cilindros no eixo Z; o jogo usa Y como vertical.
    # Sem esta conversão o personagem aparece deitado no corredor.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2.0, [1, 0, 0]))
    mesh.apply_translation(pos)
    if scale is not None: mesh.apply_scale(scale)
    mesh.visual.material=material; mesh.metadata['name']=name; parts.append(mesh)

def capsule(radius, height): return trimesh.creation.capsule(radius=radius, height=height, count=[16,8])
def sph(r): return trimesh.creation.icosphere(subdivisions=2, radius=r)
def cyl(r, h): return trimesh.creation.cylinder(radius=r, height=h, sections=20)
# 1.70m natural proportions, origin at feet. Y is vertical.
# legs: thighs and calves with subtle taper, pelvis and torso
add(capsule(.115,.52),pants,(-.105,.0,.70),name='LeftThigh'); add(capsule(.115,.52),pants,(.105,0,.70),name='RightThigh')
add(capsule(.085,.45),pants,(-.105,0,.29),name='LeftCalf'); add(capsule(.085,.45),pants,(.105,0,.29),name='RightCalf')
add(sph(.20),pants,(0,0,.98),scale=(1.0,.72,.72),name='Pelvis')
add(capsule(.22,.55),shirt,(0,0,1.28),scale=(1.0,.72,1.0),name='Torso')
# neck and head, with face projecting toward -Z (camera)
add(cyl(.075,.13),skin,(0,0,1.62),name='Neck'); add(sph(.145),skin,(0,0,1.78),scale=(.92,.90,1.02),name='Head')
add(sph(.045),skin,(0,-.13,1.77),scale=(.65,.45,.72),name='Nose')
for x in (-.052,.052):
    add(sph(.027),white,(x,-.125,1.825),scale=(1,.35,.78),name='EyeWhite')
    add(sph(.012),iris,(x,-.143,1.825),name='Iris')
# hair cap + side volume
add(sph(.153),hair,(0,.005,1.86),scale=(1.0,.98,.62),name='HairCap')
for x in (-.13,.13): add(sph(.055),hair,(x,.01,1.79),scale=(.65,.8,1.5),name='HairSide')
# arms in relaxed running-ready pose, hands separate
for x,side in ((-.265,'L'),(.265,'R')):
    add(capsule(.07,.38),shirt,(x,0,1.38),scale=(1,.9,1),name='UpperArm'+side)
    add(capsule(.055,.34),skin,(x,0,1.10),scale=(1,.9,1),name='Forearm'+side)
    add(sph(.065),skin,(x,0,0.88),scale=(.8,.6,1.0),name='Hand'+side)
# shoes with sole and toe volume
for x,side in ((-.105,'L'),(.105,'R')):
    add(sph(.12),shoe,(x,-.045,.065),scale=(.82,1.45,.42),name='Sneaker'+side)
    add(sph(.122),sole,(x,-.05,.025),scale=(.84,1.48,.18),name='Sole'+side)
scene=trimesh.Scene()
for i,p in enumerate(parts): scene.add_geometry(p, node_name=p.metadata.get('name',f'Part{i}'))
OUT.parent.mkdir(parents=True, exist_ok=True)
scene.export(OUT, file_type='glb')
print(f'generated {OUT} ({OUT.stat().st_size} bytes, {len(parts)} parts)')
