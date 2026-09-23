#!/usr/bin/env python3
"""Valida o contrato GLB da Ginger para o runtime Godot."""
from pathlib import Path
import struct,json
p=Path(__file__).resolve().parents[1]/'assets/characters/personagens/ginger+woman.glb'
required={'Idle_Loop','Walk_Loop','Sprint_Loop','Jump_Loop','Crouch_Idle_Loop','Crouch_Fwd_Loop','Landing'}
if not p.exists(): raise SystemExit('GINGER PENDING: GLB ausente')
b=p.read_bytes(); n,t=struct.unpack_from('<II',b,12); d=json.loads(b[20:20+n]); anim={a.get('name') for a in d.get('animations',[])}; missing=required-anim
print(f'GINGER GLB OK: {len(b)} bytes | skins {len(d.get("skins",[]))} | animações {len(anim)}')
print('clips:', ', '.join(sorted(anim)))
if missing: print('PENDENTES:', ', '.join(sorted(missing)))
