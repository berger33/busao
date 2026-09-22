#!/usr/bin/env python3
"""Gera inventário de GLBs para controlar orçamento mobile e LOD."""
from pathlib import Path
import json, struct

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets_manifest.json'
COMPONENT={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}

def glb_doc(p):
    raw=p.read_bytes()
    if raw[:4]!=b'glTF': return {}
    size,typ=struct.unpack_from('<II',raw,12)
    if typ!=0x4e4f534a:return {}
    return json.loads(raw[20:20+size])

def main():
    assets=[]
    for p in sorted(ROOT.rglob('*.glb')):
        if '.git' in p.parts: continue
        doc=glb_doc(p); tris=verts=materials=0
        for m in doc.get('meshes',[]):
            for prim in m.get('primitives',[]):
                attrs=prim.get('attributes',{}); count=0
                if 'POSITION' in attrs:
                    acc=doc.get('accessors',[{}])[attrs['POSITION']]; count=acc.get('count',0); verts+=count
                idx=prim.get('indices');
                if idx is not None: tris+=doc.get('accessors',[{}])[idx].get('count',0)//3
                else: tris+=count//3
                materials += 1 if prim.get('material') is not None else 0
        name=p.stem.lower()
        assets.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'meshes':len(doc.get('meshes',[])),'vertices':verts,'triangles':tris,'materials':materials,'has_lod':any(x in name for x in ('lod0','lod1','lod2','_low','_mid')),'status':'review' if tris>60000 or materials>8 else 'ok'})
    report={'schema':1,'budgets':{'mobile_high':{'triangles':1200000,'draw_calls':180,'texture_mb':180},'mobile_balanced':{'triangles':800000,'draw_calls':140,'texture_mb':140},'compatibility':{'triangles':500000,'draw_calls':100,'texture_mb':100}},'asset_count':len(assets),'assets':assets,'summary':{'review_count':sum(a['status']=='review' for a in assets),'lod_named_count':sum(a['has_lod'] for a in assets)},'next_step':'Otimizar assets review e criar LODs reais para personagens e veículos'}
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(report['summary'],ensure_ascii=False))
if __name__=='__main__':main()
