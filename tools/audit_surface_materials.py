#!/usr/bin/env python3
"""Audita mapas de superfície sem abrir o editor Godot."""
from pathlib import Path
import json,struct
ROOT=Path(__file__).resolve().parents[1]
SURF={'asfalto':['asfalto_realista.png','asfalto_normal.png','asfalto_roughness.png','asfalto_brasil.svg'],'calcada':['calcada_realista.png','calcada_normal.png','calcada_roughness.png','calcada_portuguesa.svg']}
def png_size(p):
    b=p.read_bytes(); return struct.unpack('>II',b[16:24]) if b[:8]==b'\x89PNG\r\n\x1a\n' else None
out={'schema':1,'surfaces':{},'findings':[]}
for kind,names in SURF.items():
    items=[]
    for name in names:
        p=ROOT/'assets/textures'/name
        item={'file':str(p.relative_to(ROOT)),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else 0}
        if p.exists() and p.suffix.lower()=='.png': item['size']=png_size(p)
        items.append(item)
    out['surfaces'][kind]=items
    missing=[x['file'] for x in items if not x['exists']]
    if missing: out['findings'].append({'severity':'error','surface':kind,'missing':missing})
    if not missing and not any(x['file'].endswith('normal.png') for x in items): out['findings'].append({'severity':'warn','surface':kind,'issue':'normal map ausente'})
out['next_step']='Adicionar macro variation e decal de desgaste por quarteirão após validar os mapas existentes'
(ROOT/'docs/surface_material_audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print('surface audit:',len(out['findings']),'finding(s)')
