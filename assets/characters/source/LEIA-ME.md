# `assets/characters/source/` — berço de assets-fonte (fora do runtime)

Arquivos daqui **não são carregados pelo jogo**: são fonte/Work-In-Progress que
ainda não cumpriram o contrato de runtime dos personagens
(`assets/characters/personagens/`, teto de **500 KB** por GLB, sem Draco —
o Godot 4 não decodifica `KHR_draco_mesh_compression`).

## Ginger (`ginger+woman.glb`, `Ginger+Woman.blend`)

| Item | Estado |
| --- | --- |
| `Ginger+Woman.blend` | fonte via Git LFS (37,9 MB) |
| `ginger+woman.glb` | export rigged: 1,88 MB, 7 malhas, 1 skin, **7 clipes** (`Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop`, `Crouch_Idle_Loop`, `Crouch_Fwd_Loop`, `Landing`) com 177 canais cada |
| Contrato de runtime | **não cumprido** — 1,88 MB > 500 KB |

O peso está nas animações, não na malha: ~453 KB de rotações (VEC4 float32) +
~317 KB de índices de keyframe + 228 KB de JSON (1.239 canais). Para voltar ao
runtime é preciso re-bakear com menos canais/keys, por exemplo:

```bash
blender --background --python tools/blender/bake_ginger_deform.py   # re-bake do deform
blender --background --python tools/blender/animate_ginger.py        # clipes
python3 tools/validate_ginger.py                                     # contrato dos 7 clipes
```

Depois: mover o GLB para `assets/characters/personagens/`, readicionar a entrada
no catálogo (`scripts/character_data.gd`, que hoje fecha em 20 personagens —
10 M e 10 F, como cobra `tools/validate_project.py`), atualizar a expectativa do
validador para 21, rodar `python3 tools/rebaseline_provenance.py` e os portões.

**Histórico:** a Ginger entrou no catálogo em `61a2640` e o commit `f9ddf1a`
("Make Ginger sole character") reduziu temporariamente o elenco a ela
(`CharacterData.all()` filtrada + `inventory = ["ginger"]` na sanitização do
save). Esse modo foi **revertido** na promoção para a `main` porque quebrava o
contrato de 20 personagens, derrubava a loja/elenco para 1 opção e sobrescrevia
o save do jogador. O encadeamento dos hooks (`runner_character.gd`,
`tools/validate_ginger.py`) foi preservado para o trabalho continuar.

## Herói 10/10 (`heroi_julia/`)

Pipeline *Herói 10/10* (`docs/PLANO_HEROI_10_10.md`), reconstruído do zero em
26/09/2026 (ver `docs/execucao/HEROI_REBUILD_2026-09-26.md`). Não é asset de
runtime: o jogo segue usando `personagens/hero_julia.glb` (placeholder) até a
Fase 6.

| Item | Estado |
| --- | --- |
| `heroi_julia_base.glb` / `.blend` | Fase 1: corpo esculpido (Skin+QuadriFlow, 35.952 tris, 92,1% quads, 1,72 m, 0 não-manifold) **+ rosto esculpido** (órbita, nariz, boca, queixo, orelhas — Fase 3 parcial, sem cabelo) |
| `heroi_julia_pbr.glb` / `.blend` | Fase 2: UV (atlas 61,2%) + bake albedo 2K / normal 1K / ORM 1K embutidos — **1.672 KB** (teto do plano: 2.048 KB), gate verde |
| `*_metrics.json` | Métricas dos gates das Fases 1 e 2 |
| Contrato de runtime | **não cumprido** — sem rig (Fase 4), sem clipes (Fase 5), sem roupa (Fase 6); 1,67 MB > 500 KB |

Reproduzir (o `tools/blender/out/` é regenerável e gitignored; estas cópias
existem para não perder o estado entre sessões):

```sh
sh tools/blender/make_env.sh                                              # venv bpy 4.5
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py            # Fase 1 (~7 s)
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24   # Fase 2 (~13 min, 2 núcleos)
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py tools/blender/out/heroi_julia_pbr.glb tools/blender/out/turnaround.png
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py tools/blender/out/heroi_julia_pbr.glb tools/blender/out/mao.png --alvo mao
```
