#!/usr/bin/env python3
"""Executa os gates estáticos do projeto e gera um relatório único."""
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
def run(script):
    p=subprocess.run([sys.executable,str(ROOT/'tools'/script)],cwd=ROOT,text=True,capture_output=True)
    return {'exit_code':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip(),'passed':p.returncode==0}
def main():
    checks={'hero':run('validate_hero.py'),'lod':run('validate_lod_budget.py'),'surface':run('audit_surface_materials.py'),'assets':run('build_asset_manifest.py')}
    blockers=[]
    if 'blocked' in (ROOT/'docs/lod_gate.json').read_text(): blockers.append('LOD P0/P1 ainda não produzido')
    hero=json.loads((ROOT/'docs/quality_baseline.json').read_text()).get('hero',{})
    if hero.get('mesh_only'): blockers.append('hero mesh-only sem rig/clips')
    blockers += ['FPS/frame time ainda requerem Godot e aparelho Android real']
    report={'schema':1,'checks':checks,'all_static_checks_passed':all(x['passed'] for x in checks.values()),'status':'blocked' if blockers else 'ready','blockers':blockers,'next_step':'Executar Godot em aparelho-alvo e produzir LODs reais'}
    (ROOT/'docs/quality_gate_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('quality gate:',report['status'],'| blockers:',len(blockers))
    return 0
if __name__=='__main__':raise SystemExit(main())
