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

## Regenerar os quadrúpedes do lote 3 (capivara, cavalo, boi)

```bash
sh tools/blender/run_bpy.sh tools/blender/build_quadrupedes.py
```

Mesmo kit `kit_base.py`, mas com pernas articuladas: corpo/pescoco em loft,
cabeça/focinho/olhos/orelhas em elipsoides, 4 pernas em 3 segmentos
(Coxa → Canela → Pe) com **sobreposição de 3 cm nas juntas** — com subsurf,
peças que apenas se tocam ficam separadas. Cauda + tufo por espécie
(crina e topete no cavalo; chifres, manchas e úbere no boi).

Rig de **16 ossos**: `Corpo → Pescoco → Cabeca` + `Cauda` + 4 pernas
(`Coxa/Canela/Pe` por pé). Clips por espécie:

- capivara: `Idle` (respiração + cauda, 12f), `Lie` (deitada, 16f),
  `Walk` (diagonais FE+TR / FD+TD, 16f)
- cavalo: `Idle`, `Graze` (pastando: cabeça no chão + mastigar), `Walk`
- boi: `Idle`, `Graze`, `Walk` (ciclo mais lento, bob maior)

**Regra do exportador glTF (importante para os lotes 4+):** com
`export_animation_mode='ACTIONS'`, só sai clip que já foi atribuído ao
armature pelo menos uma vez (`animation_data.action = clip`). O script
atribui cada clip antes de exportar e devolve o default no final — sem isso
o glTF exporter **descarta o clip em silêncio**.

Outra pegadinha do bpy: `bpy.ops.object.transform_apply` tem defaults
`location=True, rotation=True, scale=True` — passar só
`transform_apply(scale=True)` aplica o location junto (a origem da peça
vai para 0,0,0 e qualquer rotação feita depois orbita a peça em torno da
origem do mundo). Sempre passe os três argumentos explicitamente.

Duração total: ~45 s (Cycles CPU 640x480, 6 previews).

Em sandboxes sem bibliotecas X11/GL do sistema, o import do bpy resolve com
stubs `.so` em `/home/user/blender-stubs` expostos via `LD_LIBRARY_PATH` —
o modo headless (Cycles CPU) nao toca em GL/X de verdade. O venv e os stubs
ficam FORA do repo e podem ser limpos entre sessoes; para reconstruir tudo
(venv + stubs, com a lista de simbolos extraida dos proprio .so do bpy):

```bash
sh tools/blender/make_env.sh
```
