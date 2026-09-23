#!/usr/bin/env python3
"""Cria locomocao procedural fisicamente plausivel na Ginger e exporta GLB.
Execute no Blender local, na raiz do projeto:
 blender --background --python tools/blender/animate_ginger.py
"""
import bpy, os, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'assets/characters/source/Ginger+Woman.blend'
OUT=ROOT/'assets/characters/personagens/ginger+woman.glb'
FPS=30

def find_armature():
    arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
    if not arms: raise RuntimeError('Nenhum armature encontrado na Ginger')
    return arms[0]

def pick(arm, *names):
    for n in names:
        if arm.pose.bones.get(n): return n
    low={b.name.lower():b.name for b in arm.pose.bones}
    for n in names:
        for k,v in low.items():
            if n.lower() in k: return v
    return None

def map_bones(arm):
    return {k:pick(arm,*v) for k,v in {
      'root':('root','Root','Master'), 'pelvis':('pelvis','Pelvis','Hips','Hips_CTRL'),
      'spine':('spine_02','Spine2','Spine','Chest'), 'head':('Head','head'),
      'thigh_l':('thigh_l','Thigh.L','UpperLeg.L','LeftUpLeg'), 'thigh_r':('thigh_r','Thigh.R','UpperLeg.R','RightUpLeg'),
      'calf_l':('calf_l','Calf.L','LowerLeg.L','LeftLeg'), 'calf_r':('calf_r','Calf.R','LowerLeg.R','RightLeg'),
      'foot_l':('foot_l','Foot.L','LeftFoot'), 'foot_r':('foot_r','Foot.R','RightFoot'),
      'arm_l':('upperarm_l','UpperArm.L','LeftArm'), 'arm_r':('upperarm_r','UpperArm.R','RightArm'),
      'fore_l':('lowerarm_l','LowerArm.L','LeftForeArm'), 'fore_r':('lowerarm_r','LowerArm.R','RightForeArm')}.items()}

def reset(arm):
    for b in arm.pose.bones:
        b.rotation_mode='XYZ'; b.rotation_euler=(0,0,0); b.location=(0,0,0)

def rot(arm,n,f,x=0,y=0,z=0):
    if n and arm.pose.bones.get(n):
        b=arm.pose.bones[n]; b.rotation_mode='XYZ'; b.rotation_euler=(math.radians(x),math.radians(y),math.radians(z)); b.keyframe_insert('rotation_euler',frame=f)

def loc(arm,n,f,z=0):
    if n and arm.pose.bones.get(n):
        arm.pose.bones[n].location=(0,0,z); arm.pose.bones[n].keyframe_insert('location',frame=f)

def action(arm,name,end,fn):
    a=bpy.data.actions.get(name) or bpy.data.actions.new(name); a.use_fake_user=True; arm.animation_data_create(); arm.animation_data.action=a; a.frame_start=1; a.frame_end=end
    for f in range(1,end+1): reset(arm); fn(f,(f-1)/end*math.tau)
    for c in a.fcurves:
        for k in c.keyframe_points: k.interpolation='BEZIER'

def main():
    if not SRC.exists(): raise RuntimeError('Arquivo fonte ausente: '+str(SRC))
    bpy.ops.wm.open_mainfile(filepath=str(SRC)); arm=find_armature(); m=map_bones(arm)
    action(arm,'Idle_Loop',60,lambda f,t:(rot(arm,m['spine'],f,x=1.3*math.sin(t)),loc(arm,m['pelvis'],f,z=.006*math.sin(t))))
    def run(f,t,amp=25):
        s=math.sin(t); a=math.sin(t+math.pi); rot(arm,m['thigh_l'],f,x=amp*s); rot(arm,m['thigh_r'],f,x=-amp*s); rot(arm,m['calf_l'],f,x=amp*.45*max(0,-s)); rot(arm,m['calf_r'],f,x=amp*.45*max(0,s)); rot(arm,m['arm_l'],f,x=amp*1.1*a,z=10); rot(arm,m['arm_r'],f,x=-amp*1.1*a,z=-10)
    action(arm,'Walk_Loop',30,lambda f,t:run(f,t,25)); action(arm,'Sprint_Loop',24,lambda f,t:(rot(arm,m['spine'],f,x=12),run(f,t,42)))
    def jump(f,t):
        h=0.62*math.sin(math.pi*(f-1)/35); loc(arm,m['root'],f,z=max(0,h)); rot(arm,m['thigh_l'],f,x=-28); rot(arm,m['thigh_r'],f,x=-28); rot(arm,m['calf_l'],f,x=45); rot(arm,m['calf_r'],f,x=45)
    action(arm,'Jump_Loop',36,jump)
    def crouch(f,t):
        s=math.sin(t); rot(arm,m['thigh_l'],f,x=-48+8*s); rot(arm,m['thigh_r'],f,x=-48-8*s); rot(arm,m['calf_l'],f,x=70); rot(arm,m['calf_r'],f,x=70); rot(arm,m['spine'],f,x=20)
    action(arm,'Crouch_Idle_Loop',30,crouch); action(arm,'Crouch_Fwd_Loop',30,crouch)
    action(arm,'Landing',18,lambda f,t:(rot(arm,m['thigh_l'],f,x=-18),rot(arm,m['thigh_r'],f,x=-18),rot(arm,m['spine'],f,x=8)))
    action(arm,'Turn_Left',18,lambda f,t:rot(arm,m['root'],f,y=-35*math.sin(math.pi*(f-1)/17)))
    action(arm,'Turn_Right',18,lambda f,t:rot(arm,m['root'],f,y=35*math.sin(math.pi*(f-1)/17)))
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    for o in bpy.context.scene.objects:
        if o.type in {'MESH','ARMATURE'}: o.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC)); bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_selection=True,export_animations=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=False,export_animation_mode='ACTIONS')
    print('GINGER ANIMADA:',OUT)
if __name__=='__main__': main()
