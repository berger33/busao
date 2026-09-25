#!/usr/bin/env python3
"""Classifica assets para LOD sem destruir os arquivos-fonte."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'docs/assets_manifest.json').read_text())

def priority(path):
    p=path.lower()
    if 'hero_julia' in p or '/personagens/' in p: return 'P0_HERO'
    if 'bus' in p or 'vehicle' in p or 'car' in p or 'moto' in p: return 'P1_VEHICLES'
    if 'building' in p or 'predio' in p or 'facade' in p: return 'P2_ARCHITECTURE'
    if 'tree' in p or 'arvore' in p or 'veget' in p: return 'P3_VEGETATION'
    return 'P4_PROPS'
items=[]
for a in manifest['assets']:
    a=dict(a); a['priority']=priority(a['path'])
    a['lod_targets']={'lod0':'100%','lod1':'55%','lod2':'22%'}
    a['action']='create_lod_chain' if not a['has_lod'] else 'verify_existing_lods'
    items.append(a)
order={'P0_HERO':0,'P1_VEHICLES':1,'P2_ARCHITECTURE':2,'P3_VEGETATION':3,'P4_PROPS':4}
items.sort(key=lambda x:(order[x['priority']],-x['triangles']))
out={'schema':1,'source':'docs/assets_manifest.json','policy':{'lod1_distance_m':24,'lod2_distance_m':48,'lod_cull_distance_m':85,'preserve_source_assets':True},'items':items,'next_step':'Criar LOD0/LOD1/LOD2 para P0_HERO e P1_VEHICLES'}
(ROOT/'docs/lod_plan.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print('LOD plan:',len(items),'assets | P0/P1:',sum(x['priority'] in ('P0_HERO','P1_VEHICLES') for x in items))
