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

Em sandboxes sem bibliotecas X11/GL do sistema, o import do bpy resolve com
stubs vazios (`gcc -shared -fPIC -o libGL.so.1 stub.c`) expostos via
`LD_LIBRARY_PATH` — o modo background nao toca neles.
