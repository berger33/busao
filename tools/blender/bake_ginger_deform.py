#!/usr/bin/env python3
"""Bate as ações do control rig em keyframes visuais no armature deformador."""
import bpy, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'assets/characters/source/Ginger+Woman.blend'
OUT=ROOT/'assets/characters/personagens/ginger+woman.glb'
CLIPS=['Idle_Loop','Walk_Loop','Sprint_Loop','Jump_Loop','Crouch_Idle_Loop','Crouch_Fwd_Loop','Landing']

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    arm=next((o for o in bpy.data.objects if o.type=='ARMATURE'),None)
    if arm is None: raise RuntimeError('Armature não encontrado')
    bpy.context.view_layer.objects.active=arm; arm.select_set(True)
    # Todas as deform bones ficam selecionadas; o bake grava a pose visual,
    # eliminando dependência de control bones/constraints no Godot.
    bpy.ops.object.mode_set(mode='POSE')
    for b in arm.data.bones: b.select=True
    bpy.ops.object.mode_set(mode='OBJECT')
    for a in list(bpy.data.actions):
        if a.name not in CLIPS: continue
        arm.animation_data_create(); arm.animation_data.action=a
        start,end=int(a.frame_start),int(a.frame_end)
        bpy.context.scene.frame_start=start; bpy.context.scene.frame_end=end
        bpy.ops.nla.bake(frame_start=start,frame_end=end,step=1,only_selected=False,visual_keying=True,clear_constraints=False,clear_parents=False,bake_types={'POSE'})
        baked=arm.animation_data.action
        if baked: baked.name=a.name
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    for o in bpy.context.scene.objects:
        if o.type in {'MESH','ARMATURE'}: o.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC))
    bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_selection=True,export_animations=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=False,export_animation_mode='ACTIONS')
    print('GINGER DEFORM BAKE OK:',OUT)
if __name__=='__main__': main()
