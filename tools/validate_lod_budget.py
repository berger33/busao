#!/usr/bin/env python3
"""Gate de LOD: impede declarar assets otimizados sem evidência de cadeia LOD."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'docs/lod_plan.json').read_text())
p0p1=[x for x in plan['items'] if x['priority'] in ('P0_HERO','P1_VEHICLES')]
missing=[x['path'] for x in p0p1 if not x['has_lod']]
print('P0/P1:',len(p0p1),'| com LOD:',len(p0p1)-len(missing),'| pendentes:',len(missing))
for p in missing[:12]: print('PENDING',p)
# O gate é informativo até os GLBs derivados serem produzidos; não mascara o backlog.
(Path(ROOT/'docs/lod_gate.json')).write_text(json.dumps({'schema':1,'status':'blocked' if missing else 'pass','priority_assets':len(p0p1),'missing_lod':missing,'next_action':'Gerar GLB LOD0/LOD1/LOD2 via Blender ou ferramenta de decimação compatível'},indent=2,ensure_ascii=False)+'\n')
