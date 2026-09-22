#!/usr/bin/env python3
"""Gera baseline estático reproduzível da qualidade gráfica do projeto."""
from pathlib import Path
import json, re, hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/quality_baseline.json"

def files(ext):
    return [p for p in ROOT.rglob(f"*{ext}") if ".git" not in p.parts and "tools_py" not in p.parts]

def total_size(items):
    return sum(p.stat().st_size for p in items)

def sha(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def main():
    glbs=files('.glb'); textures=[p for e in ['.png','.jpg','.jpeg','.webp'] for p in files(e)]
    hero=ROOT/'assets/characters/personagens/hero_julia.glb'
    project=(ROOT/'project.godot').read_text(errors='ignore')
    runner=(ROOT/'scripts/runner_character.gd').read_text(errors='ignore')
    baseline={
      'schema':1,
      'source':'tools/quality_baseline.py',
      'assets':{'glb_count':len(glbs),'glb_bytes':total_size(glbs),'texture_count':len(textures),'texture_bytes':total_size(textures)},
      'renderer':{'method':re.search(r'renderer/rendering_method="([^"]+)',project).group(1) if re.search(r'renderer/rendering_method="([^"]+)',project) else 'unknown','msaa_3d':re.search(r'msaa_3d=(\d+)',project).group(1) if re.search(r'msaa_3d=(\d+)',project) else 'unknown'},
      'hero':{'exists':hero.exists(),'bytes':hero.stat().st_size if hero.exists() else 0,'sha256':sha(hero) if hero.exists() else None,'mesh_only':hero.exists() and b'Idle_Loop' not in hero.read_bytes(),'runner_accepts_mesh_only':'mesh-only' in runner},
      'known_blockers':['hero rig/animation pending','no runtime FPS measurement in sandbox','facade and ground close-up validation pending','Android device matrix pending'],
      'next_step':'Etapa 2 — heroína jogável com rig e animações'
    }
    OUT.write_text(json.dumps(baseline,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(baseline,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
