# Assets gerados por Blender headless (bpy)

Os GLBs desta pipeline sao modelados por codigo (sem download externo).
Requisitos: `pip install bpy==4.5.14` (Python 3.11) — o mesmo Blender LTS
used no sandbox; roda 100% headless.

## Regenerar o pombo

```bash
python3 tools/blender/build_pombo.py
```

Escreve `assets/characters/animais/pombo.glb` (rig + clipes Walk/Idle) e
previews PNG em `tools/blender/out/` (variaveis `POMBO_OUT_GLB` e
`POMBO_OUT_DIR` sobrescrevem os destinos).

## Regenerar as aves do lote 2 (passaro, gaivota, urubu)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_aves.py
```

Kit compartilhado em `kit_base.py` (corpo loftero, asas, rig de 12 ossos,
clips Walk + Fly). Escreve `assets/characters/animais/{passaro,gaivota,
urubu}.glb` com resting e Walk assentados no chao (o `Fly` e a pose de voo)
e previews PNG em `tools/blender/out/` (duas angulacoes por ave). Duracao
total: ~45 s em Cycles CPU 640x480.

O drop-in no jogo: `scripts/world_animal.gd` escala cada GLB pelos tamanhos
de `BIRD_PROFILES` (`glb_comprimento`/`glb_altura`), assenta no chao e, no
voo, toca o clip `fly` em loop (`behavior_mode == "flight"`); no chao, o
clip `walk`/`trot`.

Em sandboxes sem bibliotecas X11/GL do sistema, o import do bpy resolve com
stubs vazios (`gcc -shared -fPIC -o libGL.so.1 stub.c`) expostos via
`LD_LIBRARY_PATH` — o modo background nao toca neles.
