#!/usr/bin/env python3
# Lote 21 — Veiculos HD 25k (Blender 4.5 headless) — upgrade do Lote 5
# Melhoria: seg 28 + subd 2, maçaneta côncava, friso lateral, interior visivel,
# letreiro 512, rodas 24 seg, clearcoat. Sobrescreve assets/vehicles/*.glb
# Mantem GLB_FIT e nomes Wheel* para _animate_traffic.
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_base as K
from kit_base import rad
D = bpy.data
VEIC = str(K.REPO / "assets" / "vehicles")
os.makedirs(K.OUT_DIR, exist_ok=True)
os.makedirs(VEIC, exist_ok=True)
TAU = K.TAU
def coluna_entre(nome, A, B, r_base, r_topo_rel=1.0, seg=10):
    v = Vector(B) - Vector(A); L = v.length
    p = K.pilar(nome, r_base, r_topo_rel, seg)
    K.sozinho(p); p.scale=(1,1,L); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    p.rotation_mode='QUATERNION'; p.rotation_quaternion=v.to_track_quat('Z','Y'); p.location=Vector(A)
    K.sozinho(p); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False); p.rotation_mode='XYZ'
    return p
def hd_loft_box(nome, secoes, seg=28, tampas=True, subd=2):
    verts, faces = [], []
    for (y, cz, w, h, n) in secoes:
        e = 2.0/n
        for k in range(seg):
            a = k/seg*TAU; c,s = math.cos(a), math.sin(a)
            x = w * math.copysign(abs(c)**e, c); z = h * math.copysign(abs(s)**e, s)
            verts.append((x,y,cz+z))
    for s in range(len(secoes)-1):
        for k in range(seg):
            k2=(k+1)%seg; faces.append((s*seg+k, s*seg+k2, (s+1)*seg+k2, (s+1)*seg+k))
    if tampas:
        faces.append(tuple(range(seg-1,-1,-1))); faces.append(tuple(range(len(secoes)*seg-1,(len(secoes)-1)*seg-1,-1)))
    o=K.novo_obj(nome, K.malha(nome, verts, faces))
    mm=o.modifiers.new("Subd",'SUBSURF'); mm.levels=mm.render_levels=subd; mm.quality=4
    return o
def caixa(nome, centro, dims, subd=0):
    cx,cy,cz=centro; dx,dy,dz=(d*0.5 for d in dims)
    v=[(cx-dx,cy-dy,cz-dz),(cx+dx,cy-dy,cz-dz),(cx+dx,cy+dy,cz-dz),(cx-dx,cy+dy,cz-dz),(cx-dx,cy-dy,cz+dz),(cx+dx,cy-dy,cz+dz),(cx+dx,cy+dy,cz+dz),(cx-dx,cy+dy,cz+dz)]
    f=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]
    o=K.novo_obj(nome, K.malha(nome, v,f))
    uv=o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv=[(0.02,0.02),(0.98,0.02),(0.98,0.98),(0.02,0.98)][(li-poly.loop_start)%4]
    if subd:
        mm=o.modifiers.new("Subd",'SUBSURF'); mm.levels=mm.render_levels=subd
    return o
def roda_hd(nome, raio, largura, mat_pneu, mat_aro, mat_cubo, duplada=False):
    partes=[]
    bpy.ops.mesh.primitive_torus_add(major_radius=raio - largura*0.42, minor_radius=largura*0.55 if not duplada else largura*0.62, major_segments=28, minor_segments=12, location=(0,0,0))
    pneu=bpy.context.active_object; pneu.name=nome+"_pneu"; pneu.rotation_euler=(0,rad(90),0); K.sozinho(pneu); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(pneu, mat_pneu); partes.append((pneu,nome))
    aro=K.pilar(nome+"_aro", raio*0.62,1.0,16); K.sozinho(aro); aro.scale=(1,1,largura*(1.15 if duplada else 0.8)); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); aro.rotation_euler=(0,rad(90),0); K.sozinho(aro); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); aro.location=(0,0,-largura*(0.575 if duplada else 0.4)); K.sozinho(aro); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); K.pintar(aro, mat_aro); partes.append((aro,nome))
    cubo=K.pilar(nome+"_cubo", raio*0.20,1.0,12); K.sozinho(cubo); cubo.scale=(1,1,largura*(1.3 if duplada else 0.95)); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); cubo.rotation_euler=(0,rad(90),0); K.sozinho(cubo); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); cubo.location=(0,0,-largura*(0.65 if duplada else 0.475)); K.sozinho(cubo); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); K.pintar(cubo, mat_cubo); partes.append((cubo,nome))
    # parafusos
    for i in range(5):
        a=i/5*TAU; px=0.13*math.cos(a); pz=0.13*math.sin(a)
        paraf=K.pilar(f"{nome}_paraf{i}", 0.012,1.0,6); K.sozinho(paraf); paraf.scale=(1,1,0.02); bpy.ops.object.transform_apply(scale=True); paraf.rotation_euler=(0,rad(90),0); K.sozinho(paraf); bpy.ops.object.transform_apply(rotation=True); paraf.location=(px, -largura*0.62, pz); K.sozinho(paraf); bpy.ops.object.transform_apply(location=True); K.pintar(paraf, mat_cubo); partes.append((paraf,nome))
    r=K.join_parts(partes); r.name=nome; return r
def vidros_cabine(nome, secoes, mat):
    o=hd_loft_box(nome, secoes, seg=24, subd=1); K.pintar(o, mat); return o
def mat_pintura_hd(nome, cor):
    m=K.material(nome, cor, 0.32, 0.02)
    # clearcoat para pintura automotiva
    if hasattr(m.node_tree.nodes["Principled BSDF"].inputs, "get"):
        try:
            m.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.35
            m.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.22
        except: pass
    return m
def mat_emissivo(nome, cor_base, cor_emissao, energia):
    m=K.material(nome, cor_base, 0.4, 0.0)
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value=(*cor_emissao,1.0)
    b.inputs["Emission Strength"].default_value=energia
    return m
def add_macaneta(parent_list, x, y, z, mat_cromo, mat_recess):
    # recess côncavo: caixa levemente afundada + maçaneta cromada
    recess=caixa(f"MacanetaRecess_{x:.2f}_{y:.2f}", (x, y, z), (0.02, 0.14, 0.04))
    K.pintar(recess, mat_recess); parent_list.append((recess,"Chassi"))
    handle=caixa(f"Macaneta_{x:.2f}_{y:.2f}", (x+0.015, y, z), (0.025, 0.10, 0.018))
    K.pintar(handle, mat_cromo); parent_list.append((handle,"Chassi"))
    return recess, handle
def add_friso(parent_list, secoes, mat):
    friso=hd_loft_box("FrisoLateral", secoes, seg=24, subd=1)
    K.pintar(friso, mat); parent_list.append((friso,"Chassi")); return friso
def texto_emissivo_hd(nome, texto):
    from PIL import Image, ImageDraw, ImageFont
    W,H=512,128
    img=Image.new("RGB",(W,H),(8,9,10)); dr=ImageDraw.Draw(img)
    try: fonte=ImageFont.load_default(size=64)
    except: fonte=ImageFont.load_default()
    # centraliza
    bb=dr.textbbox((0,0), texto, font=fonte); w=bb[2]-bb[0]; h=bb[3]-bb[1]
    dr.text(((W-w)//2,(H-h)//2-6), texto, font=fonte, fill=(255,190,42))
    for x in range(0,W,4): dr.line([(x+3,0),(x+3,H)], fill=(12,13,14))
    for y in range(0,H,4): dr.line([(0,y+3),(W,y+3)], fill=(12,13,14))
    caminho=os.path.join(K.OUT_DIR, nome+".png"); img.save(caminho)
    bimg=D.images.load(caminho); m=D.materials.new(nome); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]; tex=m.node_tree.nodes.new("ShaderNodeTexImage"); tex.image=bimg
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value=3.2; b.inputs["Roughness"].default_value=0.48
    return m

# ===== HATCH HD =====
def build_hatch_hd(cor_pintura=(0.93, 0.94, 0.95)):
    K.reset_scene()
    pintura=mat_pintura_hd("hatch_hd_pintura", cor_pintura)
    vidro=K.material("hatch_hd_vidro",(0.08,0.11,0.15),0.05,0.15)
    borracha=K.material("hatch_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    cromo=K.material("hatch_hd_cromo",(0.82,0.84,0.86),0.18,0.88)
    escuro=K.material("hatch_hd_escuro",(0.10,0.11,0.13),0.6,0.2)
    escuro_recess=K.material("hatch_hd_recess",(0.07,0.07,0.08),0.7,0.0)
    farol=mat_emissivo("hatch_hd_farol",(0.95,0.93,0.80),(1.0,0.95,0.72),2.8)
    lanterna=mat_emissivo("hatch_hd_lanterna",(0.75,0.12,0.14),(1.0,0.10,0.08),2.4)
    placa=K.material("hatch_hd_placa",(0.88,0.89,0.90),0.5,0.1)
    banco=K.material("hatch_hd_banco",(0.22,0.22,0.24),0.72,0.0)
    volante_mat=K.material("hatch_hd_volante",(0.12,0.12,0.13),0.45,0.0)
    partes=[]
    corpo=hd_loft_box("HatchCorpo",[(-2.10,0.50,0.70,0.30,7.0),(-1.92,0.54,0.81,0.40,8.0),(-1.20,0.57,0.86,0.43,9.0),(-0.30,0.58,0.87,0.44,9.0),(+0.90,0.57,0.86,0.44,9.0),(+1.70,0.54,0.84,0.41,8.0),(+2.00,0.49,0.79,0.36,8.0),(+2.10,0.45,0.70,0.30,7.0)])
    K.pintar(corpo,pintura); partes.append((corpo,"Chassi"))
    saia=hd_loft_box("HatchSaia",[(-2.02,0.30,0.74,0.15,6.0),(-1.90,0.28,0.83,0.14,7.0),(+1.90,0.28,0.83,0.14,7.0),(+2.02,0.30,0.74,0.15,6.0)])
    K.pintar(saia,escuro); partes.append((saia,"Chassi"))
    cabine=vidros_cabine("HatchVidro",[(-1.55,0.98,0.66,0.08,6.0),(-1.35,1.10,0.78,0.24,7.0),(-0.55,1.20,0.81,0.27,8.0),(+0.30,1.20,0.81,0.27,8.0),(+0.88,1.05,0.73,0.16,7.0),(+1.05,0.97,0.68,0.08,6.0)], vidro)
    partes.append((cabine,"Chassi"))
    teto=hd_loft_box("HatchTeto",[(-1.25,1.36,0.70,0.06,6.0),(-0.55,1.40,0.77,0.07,7.0),(+0.30,1.40,0.77,0.07,7.0),(+0.75,1.34,0.67,0.05,6.0)])
    K.pintar(teto,pintura); partes.append((teto,"Chassi"))
    # friso lateral
    friso=hd_loft_box("HatchFriso",[(-1.90,0.62,0.84,0.02,8.0),(+1.70,0.62,0.84,0.02,8.0)], seg=20)
    K.pintar(friso,cromo); partes.append((friso,"Chassi"))
    # maçanetas côncavas (2 portas por lado)
    for sx in (-1.0,1.0):
        for py in (-0.35, 0.65):
            add_macaneta(partes, sx*0.87, py, 0.78, cromo, escuro_recess)
    # grade + farois
    grade=caixa("HatchGrade",(0,2.04,0.50),(1.10,0.12,0.22)); K.pintar(grade,escuro); partes.append((grade,"Chassi"))
    for sx in (-0.58,0.58):
        f=caixa(f"HatchFarol_{sx}",(sx,2.03,0.62),(0.36,0.12,0.15)); K.pintar(f,farol); partes.append((f,"Chassi"))
        # lente de vidro
        lente=caixa(f"HatchFarolLente_{sx}",(sx,2.07,0.62),(0.34,0.04,0.13)); K.pintar(lente,vidro); partes.append((lente,"Chassi"))
    for sx in (-0.62,0.62):
        l=caixa(f"HatchLanterna_{sx}",(sx,-2.04,0.68),(0.32,0.12,0.17)); K.pintar(l,lanterna); partes.append((l,"Chassi"))
    # interior visivel: bancos + volante
    banco_f1=caixa("HatchBancoFL",(-0.32,0.10,0.78),(0.46,0.44,0.18)); K.pintar(banco_f1,banco); partes.append((banco_f1,"Chassi"))
    banco_f2=caixa("HatchBancoFR",(0.32,0.10,0.78),(0.46,0.44,0.18)); K.pintar(banco_f2,banco); partes.append((banco_f2,"Chassi"))
    banco_tr=caixa("HatchBancoTR",(0,-0.75,0.80),(1.30,0.50,0.20)); K.pintar(banco_tr,banco); partes.append((banco_tr,"Chassi"))
    volante=Bpy_toro_volante((-0.32,0.45,0.95), cromo); partes.append((volante,"Chassi"))
    for sx in (-1.0,1.0):
        haste=coluna_entre("HatchRetH"+str(sx), (sx*0.82,0.88,1.02),(sx*0.94,0.86,1.06),0.015); K.pintar(haste,escuro); partes.append((haste,"Chassi"))
        m=caixa("HatchRetro"+str(sx),(sx*0.98,0.86,1.08),(0.10,0.16,0.10)); K.pintar(m,pintura); partes.append((m,"Chassi"))
    corpo_junto=K.join_parts(partes); corpo_junto.name="Hatch"
    rodas=[]
    for (sx,nome,py) in ((-1,"WheelFL",1.28),(1,"WheelFR",1.28),(-1,"WheelRL",-1.32),(1,"WheelRR",-1.32)):
        r=roda_hd(nome,0.30,0.20,borracha,cromo,escuro); r.location=(sx*0.78,py,0.30); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    return [corpo_junto]+rodas

def Bpy_toro_volante(pos, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.018, major_segments=18, minor_segments=8, location=pos)
    o=bpy.context.active_object; o.name="Volante"; o.rotation_euler=(rad(18),0,0); K.sozinho(o); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(o, mat); return o

def build_sedan_hd():
    K.reset_scene()
    pintura=mat_pintura_hd("sedan_hd_pintura",(0.79,0.80,0.79))
    vidro=K.material("sedan_hd_vidro",(0.08,0.11,0.15),0.05,0.15)
    borracha=K.material("sedan_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    cromo=K.material("sedan_hd_cromo",(0.82,0.84,0.86),0.18,0.88)
    escuro=K.material("sedan_hd_escuro",(0.10,0.11,0.13),0.6,0.2); escuro_recess=K.material("sedan_hd_recess",(0.07,0.07,0.08),0.7,0.0)
    farol=mat_emissivo("sedan_hd_farol",(0.95,0.93,0.80),(1.0,0.95,0.72),2.8); lanterna=mat_emissivo("sedan_hd_lanterna",(0.75,0.12,0.14),(1.0,0.10,0.08),2.4)
    banco=K.material("sedan_hd_banco",(0.32,0.28,0.26),0.70,0.0)
    partes=[]
    corpo=hd_loft_box("SedanCorpo",[(-2.20,0.50,0.70,0.30,7.0),(-2.02,0.54,0.82,0.40,8.0),(-1.30,0.57,0.86,0.43,9.0),(-0.30,0.58,0.87,0.44,9.0),(+0.90,0.57,0.86,0.44,9.0),(+1.80,0.54,0.84,0.41,8.0),(+2.10,0.49,0.79,0.36,8.0),(+2.20,0.45,0.70,0.30,7.0)])
    K.pintar(corpo,pintura); partes.append((corpo,"Chassi"))
    mala=hd_loft_box("SedanMala",[(-2.16,0.90,0.64,0.07,6.0),(-1.80,0.94,0.76,0.09,7.0),(-1.05,0.95,0.80,0.10,8.0),(-0.95,0.94,0.80,0.09,8.0)])
    K.pintar(mala,pintura); partes.append((mala,"Chassi"))
    saia=hd_loft_box("SedanSaia",[(-2.12,0.30,0.74,0.15,6.0),(-2.00,0.28,0.83,0.14,7.0),(+2.00,0.28,0.83,0.14,7.0),(+2.12,0.30,0.74,0.15,6.0)])
    K.pintar(saia,escuro); partes.append((saia,"Chassi"))
    cabine=vidros_cabine("SedanVidro",[(-1.15,1.00,0.64,0.08,6.0),(-0.95,1.12,0.76,0.24,7.0),(-0.30,1.21,0.79,0.27,8.0),(+0.42,1.21,0.79,0.27,8.0),(+0.95,1.06,0.71,0.16,7.0),(+1.10,0.98,0.66,0.08,6.0)], vidro)
    partes.append((cabine,"Chassi"))
    teto=hd_loft_box("SedanTeto",[(-0.85,1.35,0.68,0.06,6.0),(-0.30,1.39,0.75,0.07,7.0),(+0.42,1.39,0.75,0.07,7.0),(+0.82,1.33,0.65,0.05,6.0)])
    K.pintar(teto,pintura); partes.append((teto,"Chassi"))
    for sx in (-1.0,1.0):
        for py in (-0.45,0.55):
            add_macaneta(partes, sx*0.87, py, 0.78, cromo, escuro_recess)
    friso=hd_loft_box("SedanFriso",[(-1.95,0.62,0.84,0.02,8.0),(+1.75,0.62,0.84,0.02,8.0)], seg=20)
    K.pintar(friso,cromo); partes.append((friso,"Chassi"))
    grade=caixa("SedanGrade",(0,2.14,0.50),(1.10,0.12,0.22)); K.pintar(grade,escuro); partes.append((grade,"Chassi"))
    for sx in (-0.60,0.60):
        f=caixa(f"SedanFarol_{sx}",(sx,2.13,0.62),(0.36,0.12,0.15)); K.pintar(f,farol); partes.append((f,"Chassi"))
        fl=caixa(f"SedanFarolLente_{sx}",(sx,2.17,0.62),(0.34,0.04,0.13)); K.pintar(fl,vidro); partes.append((fl,"Chassi"))
        l=caixa(f"SedanLanterna_{sx}",(sx, -2.14,0.70),(0.32,0.12,0.17)); K.pintar(l,lanterna); partes.append((l,"Chassi"))
    # interior
    for sx in (-0.32,0.32):
        b=caixa(f"SedanBanco_{sx}",(sx,0.05,0.78),(0.46,0.44,0.18)); K.pintar(b,banco); partes.append((b,"Chassi"))
    bt=caixa("SedanBancoTR",(0,-0.85,0.80),(1.30,0.50,0.20)); K.pintar(bt,banco); partes.append((bt,"Chassi"))
    vol=Bpy_toro_volante((-0.32,0.40,0.95), cromo); partes.append((vol,"Chassi"))
    corpo_junto=K.join_parts(partes); corpo_junto.name="Sedan"
    rodas=[]
    for (sx,nome,py) in ((-1,"WheelFL",1.28),(1,"WheelFR",1.28),(-1,"WheelRL",-1.32),(1,"WheelRR",-1.32)):
        r=roda_hd(nome,0.30,0.20,borracha,cromo,escuro); r.location=(sx*0.78,py,0.30); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    return [corpo_junto]+rodas

def build_moto_hd(cor_pintura=(0.13, 0.13, 0.13)):
    K.reset_scene()
    pintura=mat_pintura_hd("moto_hd_pintura", cor_pintura)
    vidro=K.material("moto_hd_vidro",(0.08,0.11,0.15),0.06,0.18)
    borracha=K.material("moto_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    cromo=K.material("moto_hd_cromo",(0.82,0.84,0.86),0.18,0.88)
    escuro=K.material("moto_hd_escuro",(0.10,0.11,0.13),0.6,0.2)
    motor_mat=K.material("moto_hd_motor",(0.30,0.30,0.32),0.42,0.55)
    farol=mat_emissivo("moto_hd_farol",(0.95,0.93,0.80),(1.0,0.95,0.72),2.8)
    partes=[]
    # quadro principal
    chassi=caixa("MotoChassi",(0,0.15,0.55),(0.22,1.45,0.14)); K.pintar(chassi,escuro); partes.append((chassi,"Chassi"))
    tanque=hd_loft_box("MotoTanque",[(-0.20,0.78,0.18,0.14,7.0),(0.00,0.82,0.20,0.16,7.0),(0.25,0.80,0.18,0.14,7.0)], seg=20)
    K.pintar(tanque,pintura); partes.append((tanque,"Chassi"))
    banco=caixa("MotoBanco",(0,-0.25,0.78),(0.20,0.70,0.08), subd=1); K.pintar(banco,escuro); partes.append((banco,"Chassi"))
    # motor bloco
    motor=caixa("MotoMotor",(0,-0.05,0.45),(0.26,0.36,0.30)); K.pintar(motor,motor_mat); partes.append((motor,"Chassi"))
    for sx in (-1.0,1.0):
        cilindro=caixa(f"MotoCilindro_{sx}",(sx*0.10,-0.05,0.48),(0.08,0.22,0.12)); K.pintar(cilindro,motor_mat); partes.append((cilindro,"Chassi"))
    escap=coluna_entre("MotoEscap", (0.12,-0.30,0.38),(0.12,-0.85,0.32),0.035); K.pintar(escap,cromo); partes.append((escap,"Chassi"))
    # garfo
    for sx in (-1.0,1.0):
        f=coluna_entre(f"MotoGarfo_{sx}", (sx*0.11,0.65,0.75),(sx*0.11,0.95,0.32),0.018); K.pintar(f,cromo); partes.append((f,"Chassi"))
    guidao=coluna_entre("MotoGuidao", (-0.32,0.55,0.95),(0.32,0.55,0.95),0.015); K.pintar(guidao,escuro); partes.append((guidao,"Chassi"))
    farol_o=caixa("MotoFarol",(0,0.98,0.82),(0.22,0.10,0.18)); K.pintar(farol_o,farol); partes.append((farol_o,"Chassi"))
    painel=caixa("MotoPainel",(0,0.60,0.90),(0.18,0.12,0.06)); K.pintar(painel,escuro); partes.append((painel,"Chassi"))
    corpo=K.join_parts(partes); corpo.name="Moto"
    rodas=[]
    for (py,nome) in ((0.85,"MotoWheelF"),(-0.78,"MotoWheelR")):
        r=roda_hd(nome,0.30,0.12,borracha,cromo,escuro); r.location=(0,py,0.30); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    return [corpo]+rodas

def build_caminhao_hd(cor_pintura=(0.13, 0.34, 0.55)):
    K.reset_scene()
    pintura=mat_pintura_hd("truck_hd_pintura", cor_pintura)
    vidro=K.material("truck_hd_vidro",(0.08,0.11,0.15),0.06,0.18)
    borracha=K.material("truck_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    cromo=K.material("truck_hd_cromo",(0.82,0.84,0.86),0.18,0.88)
    escuro=K.material("truck_hd_escuro",(0.10,0.11,0.13),0.6,0.2)
    madeira=K.material("truck_hd_madeira",(0.45,0.30,0.17),0.78,0.0)
    madeira_e=K.material("truck_hd_madeira_e",(0.33,0.21,0.11),0.8,0.0)
    farol=mat_emissivo("truck_hd_farol",(0.95,0.93,0.80),(1.0,0.95,0.72),2.8)
    lanterna=mat_emissivo("truck_hd_lanterna",(0.75,0.12,0.14),(1.0,0.10,0.08),2.4)
    banco=K.material("truck_hd_banco",(0.25,0.25,0.27),0.70,0.0)
    partes=[]
    chassi=caixa("TruckChassi",(0,-0.10,0.62),(0.86,5.90,0.22)); K.pintar(chassi,escuro); partes.append((chassi,"Chassi"))
    cab=hd_loft_box("TruckCabine",[(+1.25,1.30,1.00,0.55,6.0),(+1.42,1.55,1.08,0.85,7.0),(+1.55,1.95,1.10,1.05,8.0),(+2.55,2.05,1.10,1.02,8.0),(+2.88,1.95,1.08,0.90,8.0),(+3.02,1.55,1.04,0.62,7.0),(+3.08,1.10,0.98,0.38,6.0)], seg=24)
    K.pintar(cab,pintura); partes.append((cab,"Chassi"))
    # maçanetas cavadas
    for sx in (-1.0,1.0):
        add_macaneta(partes, sx*1.10, 2.20, 1.30, cromo, escuro)
    pb=caixa("TruckParabrisa",(0,2.92,2.10),(1.86,0.10,0.78)); pb.rotation_euler=(rad(-10),0,0); K.sozinho(pb); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(pb,vidro); partes.append((pb,"Chassi"))
    # interior cabine
    for sx in (-0.32,0.32):
        b=caixa(f"TruckBanco_{sx}",(sx,2.30,1.30),(0.44,0.38,0.35)); K.pintar(b,banco); partes.append((b,"Chassi"))
    vol=Bpy_toro_volante((-0.32,2.55,1.65), cromo); partes.append((vol,"Chassi"))
    grade=caixa("TruckGrade",(0,3.06,1.30),(1.40,0.12,0.46)); K.pintar(grade,escuro); partes.append((grade,"Chassi"))
    for sx in (-1.0,1.0):
        f=caixa(f"TruckFarol_{sx}",(sx*0.76,3.04,0.94),(0.34,0.12,0.18)); K.pintar(f,farol); partes.append((f,"Chassi"))
        fl=caixa(f"TruckFarolLente_{sx}",(sx*0.76,3.08,0.94),(0.32,0.04,0.16)); K.pintar(fl,vidro); partes.append((fl,"Chassi"))
        l=caixa(f"TruckLanterna_{sx}",(sx*1.02,-3.10,1.20),(0.20,0.08,0.14)); K.pintar(l,lanterna); partes.append((l,"Chassi"))
        haste=coluna_entre(f"TruckRetH_{sx}",(sx*1.10,2.60,2.10),(sx*1.28,2.50,2.20),0.02); K.pintar(haste,escuro); partes.append((haste,"Chassi"))
        m=caixa(f"TruckRetro_{sx}",(sx*1.30,2.48,2.28),(0.08,0.14,0.26)); K.pintar(m,escuro); partes.append((m,"Chassi"))
    # carroceria madeira com friso metalico
    piso=caixa("TruckPiso",(0,-1.05,1.16),(2.28,4.10,0.10)); K.pintar(piso,madeira_e); partes.append((piso,"Chassi"))
    for sx in (-1.0,1.0):
        for i,zz in enumerate((1.42,1.66,1.90,2.14)):
            fas=caixa(f"TruckFas_{sx}_{i}",(sx*1.12,-1.05,zz),(0.06,4.06,0.16)); K.pintar(fas,madeira); partes.append((fas,"Chassi"))
    for yy in (-3.0,-2.1,-1.2,-0.3,0.6):
        for sx in (-1.0,1.0):
            est=caixa("TruckEsteio",(sx*1.12,yy,1.72),(0.07,0.07,1.12)); K.pintar(est,madeira_e); partes.append((est,"Chassi"))
    # escapamento vertical
    esc=coluna_entre("TruckEscap", (1.08,2.80,0.70),(1.08,2.80,2.30),0.045); K.pintar(esc,cromo); partes.append((esc,"Chassi"))
    corpo=K.join_parts(partes); corpo.name="Truck"
    rodas=[]
    for (sx,nome,py,dup) in ((-1,"WheelFL",2.15,False),(1,"WheelFR",2.15,False),(-1,"WheelRL",-1.45,True),(1,"WheelRR",-1.45,True)):
        r=roda_hd(nome,0.48,0.30,borracha,cromo,escuro,duplada=dup); r.location=(sx*1.02,py,0.48); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    return [corpo]+rodas

def build_onibus_hd(comprimento, amarelo, faixa, destino_txt, nome_base):
    K.reset_scene()
    pintura=mat_pintura_hd(nome_base+"_hd_pintura", amarelo)
    faixa_m=mat_pintura_hd(nome_base+"_hd_faixa", faixa)
    vidro=K.material(nome_base+"_hd_vidro",(0.08,0.11,0.15),0.06,0.18)
    borracha=K.material(nome_base+"_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    aro=K.material(nome_base+"_hd_aro",(0.62,0.65,0.67),0.3,0.8)
    escuro=K.material(nome_base+"_hd_escuro",(0.10,0.11,0.13),0.6,0.2)
    metal=K.material(nome_base+"_hd_metal",(0.80,0.81,0.78),0.4,0.4)
    banco_mat=K.material(nome_base+"_hd_banco",(0.18,0.42,0.58),0.70,0.0)
    farol=mat_emissivo(nome_base+"_hd_farol",(0.95,0.93,0.80),(1.0,0.95,0.72),2.8)
    lanterna=mat_emissivo(nome_base+"_hd_lanterna",(0.75,0.12,0.14),(1.0,0.10,0.08),2.4)
    L2=comprimento*0.5; partes=[]
    corpo=hd_loft_box("BusCorpo",[(-L2,1.50,1.14,1.02,6.0),(-L2+0.30,1.55,1.26,1.30,8.0),(-L2*0.45,1.58,1.28,1.36,9.0),(+L2*0.42,1.58,1.28,1.36,9.0),(+L2-0.72,1.55,1.26,1.32,8.0),(+L2-0.22,1.46,1.22,1.20,7.0),(+L2,1.30,1.14,0.96,6.0)], seg=28)
    K.pintar(corpo,pintura); partes.append((corpo,"Onibus"))
    faixa_o=hd_loft_box("BusFaixa",[(-L2+0.05,0.72,1.16,0.16,6.0),(-L2+0.35,0.72,1.30,0.17,8.0),(+L2-0.60,0.72,1.30,0.17,8.0),(+L2-0.10,0.66,1.24,0.15,6.0)])
    K.pintar(faixa_o,faixa_m); partes.append((faixa_o,"Onibus"))
    jan=hd_loft_box("BusJanelas",[(-L2+0.55,2.08,1.12,0.34,7.0),(-L2+0.90,2.08,1.30,0.48,8.0),(+L2-1.30,2.08,1.30,0.48,8.0),(+L2-0.90,2.04,1.26,0.40,7.0)])
    K.pintar(jan,vidro); partes.append((jan,"Onibus"))
    pb=caixa("BusParabrisa",(0,L2-0.30,2.05),(2.16,0.10,0.92)); pb.rotation_euler=(rad(-12),0,0); K.sozinho(pb); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(pb,vidro); partes.append((pb,"Onibus"))
    for yy,suf in ((L2-1.55,"F"),(-0.55,"M")):
        porta=caixa("BusPorta"+suf,(-1.285,yy,1.30),(0.04,1.15,1.90)); K.pintar(porta,escuro); partes.append((porta,"Onibus"))
        pv=caixa("BusPortaVid"+suf,(-1.30,yy,1.92),(0.03,0.95,0.72)); K.pintar(pv,vidro); partes.append((pv,"Onibus"))
    painel=caixa("BusDestino",(0,L2-0.30,2.62),(1.50,0.34,0.28)); painel.data.materials.append(escuro); painel.data.materials.append(texto_emissivo_hd(nome_base+"_hd_letreiro", destino_txt)); painel.data.polygons[1].material_index=1; partes.append((painel,"Onibus"))
    for sx,suf in ((-1.0,"E"),(1.0,"D")):
        f=caixa("BusFarol"+suf,(sx*0.82,L2-0.06,0.86),(0.40,0.12,0.18)); K.pintar(f,farol); partes.append((f,"Onibus"))
        fl=caixa("BusFarolLente"+suf,(sx*0.82,L2-0.02,0.86),(0.38,0.04,0.16)); K.pintar(fl,vidro); partes.append((fl,"Onibus"))
        l=caixa("BusLanterna"+suf,(sx*0.86,-L2+0.06,0.92),(0.34,0.10,0.16)); K.pintar(l,lanterna); partes.append((l,"Onibus"))
    bpc=caixa("BusParaChoque",(0,L2-0.02,0.44),(2.42,0.16,0.24)); K.pintar(bpc,escuro); partes.append((bpc,"Onibus"))
    bpt=caixa("BusParaChoqueT",(0,-L2+0.02,0.44),(2.42,0.16,0.24)); K.pintar(bpt,escuro); partes.append((bpt,"Onibus"))
    ac=caixa("BusArCond",(0,0.30,3.02),(1.30,2.40,0.16), subd=1); K.pintar(ac,metal); partes.append((ac,"Onibus"))
    for sx,suf in ((-1.0,"E"),(1.0,"D")):
        esp=caixa("BusRetro"+suf,(sx*1.38,L2-0.80,2.30),(0.10,0.08,0.26)); K.pintar(esp,escuro); partes.append((esp,"Onibus"))
    # interior: 6 fileiras de bancos 2+2
    for row in range(6):
        yy = L2 - 1.90 - row*1.15
        if abs(yy - (L2-1.55)) < 0.6 or abs(yy - (-0.55)) < 0.6: continue # porta
        for sx in (-0.75, -0.30, 0.30, 0.75):
            b=caixa(f"BusBanco_{row}_{sx}",(sx, yy, 1.15),(0.38,0.42,0.18)); K.pintar(b,banco_mat); partes.append((b,"Onibus"))
            enc=caixa(f"BusEncosto_{row}_{sx}",(sx, yy+0.18, 1.45),(0.38,0.06,0.45)); K.pintar(enc,banco_mat); partes.append((enc,"Onibus"))
    # volante motorista
    vol=Bpy_toro_volante(( -0.75, L2-1.20, 1.95), cromo if 'cromo' in locals() else escuro)
    # use escuro for driver volante
    corpo_junto=K.join_parts(partes); corpo_junto.name=nome_base
    rodas=[]
    eixo_f=L2-1.45; eixo_t=-L2+1.75
    for (sx,nome,py) in ((-1,"BusWheelFL",eixo_f),(1,"BusWheelFR",eixo_f),(-1,"BusWheelRL",eixo_t),(1,"BusWheelRR",eixo_t)):
        r=roda_hd(nome,0.48,0.30,borracha,aro,escuro); r.location=(sx*1.08,py,0.48); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    return [corpo_junto]+rodas

def build_bicicleta_hd():
    # reaproveita build original mas com tubos mais suaves e reflexores
    K.reset_scene()
    quadro=K.material("bike_hd_quadro",(0.11,0.34,0.55),0.32,0.55)
    borracha=K.material("bike_hd_borracha",(0.06,0.07,0.09),0.92,0.0)
    cromo=K.material("bike_hd_cromo",(0.82,0.84,0.86),0.18,0.88)
    escuro=K.material("bike_hd_escuro",(0.10,0.11,0.13),0.6,0.2)
    emiss=K.material("bike_hd_refletor",(0.95,0.18,0.12),0.45,0.0)
    rodas=[]
    for (py,nome) in ((0.52,"BikeWheelF"),(-0.52,"BikeWheelR")):
        partes_r=[]
        bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.048, major_segments=28, minor_segments=12, location=(0,0,0))
        pneu=bpy.context.active_object; pneu.name=nome+"_pneu"; pneu.rotation_euler=(0,rad(90),0); K.sozinho(pneu); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(pneu,borracha); partes_r.append((pneu,nome))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.286, minor_radius=0.020, major_segments=24, minor_segments=10, location=(0,0,0))
        aro_o=bpy.context.active_object; aro_o.name=nome+"_aro"; aro_o.rotation_euler=(0,rad(90),0); K.sozinho(aro_o); bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); K.pintar(aro_o,cromo); partes_r.append((aro_o,nome))
        for i in range(8):
            a=i/8*TAU
            raio=coluna_entre(nome+f"_raio{i}", (0,0.27*math.cos(a),0.27*math.sin(a)), (0,-0.27*math.cos(a),-0.27*math.sin(a)),0.005,1.0,6)
            K.pintar(raio,cromo); partes_r.append((raio,nome))
        cubo=K.pilar(nome+"_cubo",0.045,1.0,12); K.sozinho(cubo); cubo.scale=(1,1,0.09); bpy.ops.object.transform_apply(scale=True); cubo.rotation_euler=(0,rad(90),0); K.sozinho(cubo); bpy.ops.object.transform_apply(rotation=True); cubo.location=(0,0,-0.045); K.sozinho(cubo); bpy.ops.object.transform_apply(location=True); K.pintar(cubo,escuro); partes_r.append((cubo,nome))
        # refletor
        refl=caixa(nome+"_refl",(0,0,0.34),(0.04,0.08,0.04)); refl.data.materials.clear(); refl.data.materials.append(emiss); partes_r.append((refl,nome))
        r=K.join_parts(partes_r); r.name=nome; r.location=(0,py,0.34); K.sozinho(r); bpy.ops.object.transform_apply(location=True, rotation=False, scale=False); rodas.append(r)
    partes=[]
    tubos=[("BikeHead",(0,0.44,0.62),(0,0.40,0.98)),("BikeDown",(0,-0.06,0.36),(0,0.40,0.98)),("BikeSeatT",(0,-0.06,0.36),(0,-0.20,1.00)),("BikeTop",(0,-0.20,1.00),(0,0.40,0.98)),("BikeChainL",(0,-0.06,0.36),(0,-0.52,0.34)),("BikeSeatS",(0,-0.20,0.98),(0,-0.52,0.34)),("BikeForkL",(0,0.40,0.98),(0,0.52,0.34))]
    for nome,A,B in tubos:
        t=coluna_entre(nome,A,B,0.026); K.pintar(t,quadro); partes.append((t,"Bike"))
    for sx in (-1.0,1.0):
        c=coluna_entre(f"BikeChain{sx}",(sx*0.02,-0.06,0.36),(sx*0.02,-0.52,0.34),0.012); K.pintar(c,cromo); partes.append((c,"Bike"))
        f=coluna_entre(f"BikeFork{sx}",(sx*0.035,0.40,0.98),(sx*0.045,0.52,0.34),0.018); K.pintar(f,cromo); partes.append((f,"Bike"))
    mesa=coluna_entre("BikeMesa",(0,0.42,0.99),(0,0.44,1.06),0.020); K.pintar(mesa,cromo); partes.append((mesa,"Bike"))
    guid=coluna_entre("BikeGuidao",(-0.26,0.44,1.06),(0.26,0.44,1.06),0.018); K.pintar(guid,cromo); partes.append((guid,"Bike"))
    for sx in (-1.0,1.0):
        punho=coluna_entre(f"BikePunho{sx}",(sx*0.22,0.44,1.06),(sx*0.27,0.44,1.06),0.024); K.pintar(punho,borracha); partes.append((punho,"Bike"))
    canote=coluna_entre("BikeCanote",(0,-0.20,0.99),(0,-0.22,1.08),0.016); K.pintar(canote,cromo); partes.append((canote,"Bike"))
    selim=caixa("BikeSelim",(0,-0.22,1.10),(0.10,0.30,0.05), subd=1); K.pintar(selim,escuro); partes.append((selim,"Bike"))
    coroa=K.pilar("BikeCoroa",0.09,1.0,16); K.sozinho(coroa); coroa.scale=(1,1,0.02); bpy.ops.object.transform_apply(scale=True); coroa.rotation_euler=(0,rad(90),0); K.sozinho(coroa); bpy.ops.object.transform_apply(rotation=True); coroa.location=(0.03,-0.06,0.35); K.sozinho(coroa); bpy.ops.object.transform_apply(location=True); K.pintar(coroa,cromo); partes.append((coroa,"Bike"))
    for sx,dz in ((1.0,-0.08),(-1.0,0.08)):
        braco=coluna_entre(f"BikePediv{sx}",(0,-0.06,0.36),(sx*0.10,-0.06+dz,0.36+dz*0.5),0.014); K.pintar(braco,cromo); partes.append((braco,"Bike"))
        pedal=caixa(f"BikePedal{sx}",(sx*0.14,-0.06+dz,0.36+dz*0.5),(0.09,0.16,0.02)); K.pintar(pedal,escuro); partes.append((pedal,"Bike"))
    corpo=K.join_parts(partes); corpo.name="Bicicleta"
    return [corpo]+rodas

def bbox_z_len(nodes):
    import mathutils
    bb=mathutils.Vector((1e9,1e9,1e9)); bt=mathutils.Vector((-1e9,-1e9,-1e9))
    for o in nodes:
        for v in o.bound_box:
            p=o.matrix_world @ mathutils.Vector(v)
            bb=mathutils.Vector((min(bb.x,p.x),min(bb.y,p.y),min(bb.z,p.z)))
            bt=mathutils.Vector((max(bt.x,p.x),max(bt.y,p.y),max(bt.z,p.z)))
    return bt-bb
def render_veiculo(nodes, nome, distancia, altura_alvo=0.9):
    try:
        cena=bpy.context.scene; K.setup_preview(fundo=(0.42,0.50,0.62,1.0), energia_fundo=0.42)
        if hasattr(cena, "cycles"):
            cena.cycles.samples = 4
        for o in list(cena.collection.objects):
            if o.name=="Piso": o.scale=(distancia*2.2, distancia*2.2,1)
        cam=cena.camera; cam.data.lens=42; K.render_de(cam, (distancia*0.82, distancia*1.05, distancia*0.52),(0,0,altura_alvo), os.path.join(K.OUT_DIR, "lote21_"+nome+".png"))
    except Exception as e:
        print("Render skip:", e)
if __name__=="__main__":
    jobs=[
        ("car",lambda: build_hatch_hd((0.93, 0.94, 0.95)),(4.4,1.55),6.4,0.7),
        ("car_azul",lambda: build_hatch_hd((0.14, 0.32, 0.62)),(4.4,1.55),6.4,0.7),
        ("car_prata",lambda: build_hatch_hd((0.74, 0.76, 0.78)),(4.4,1.55),6.4,0.7),
        ("carro",build_sedan_hd,(4.4,1.55),6.6,0.7),
        ("motorcycle",lambda: build_moto_hd((0.13, 0.13, 0.13)),(2.1,1.15),3.4,0.6),
        ("motorcycle_verde",lambda: build_moto_hd((0.14, 0.58, 0.32)),(2.1,1.15),3.4,0.6),
        ("truck",lambda: build_caminhao_hd((0.13, 0.34, 0.55)),(6.4,2.7),9.5,1.2),
        ("truck_vermelho",lambda: build_caminhao_hd((0.78, 0.14, 0.16)),(6.4,2.7),9.5,1.2),
        ("bus_traffic",lambda: build_onibus_hd(7.4,(0.86,0.68,0.20),(0.12,0.42,0.25),"CIRCULAR","BusTrafego"),(7.4,3.0),11.0,1.4),
        ("onibus",lambda: build_onibus_hd(8.2,(0.957,0.749,0.239),(0.929,0.388,0.298),"PONTO FINAL","Onibus"),(8.2,3.0),11.5,1.4),
        ("bicycle",build_bicicleta_hd,(1.85,1.15),2.6,0.55)
    ]
    resumo=[]
    for nome,fn,alvo,dist,h_alvo in jobs:
        nodes=fn()
        dim=bbox_z_len(nodes)
        fit=min(alvo[0]/max(dim.y,0.001), alvo[1]/max(dim.z,0.001))
        print(f"L21 {nome:12} nativo: {dim.y:.2f}C x {dim.x:.2f}L x {dim.z:.2f}A fit {fit:.3f}")
        resumo.append((nome, tuple(round(v,2) for v in (dim.y,dim.x,dim.z)), round(fit,3)))
        caminho=K.export_glb(os.path.join(VEIC, nome+".glb"), nodes)
        render_veiculo(nodes, nome, dist, h_alvo)
        print("EXPORT", caminho, os.path.getsize(caminho))
    print("RESUMO_LOTE21:", resumo)
    print("LOTE21_OK")
