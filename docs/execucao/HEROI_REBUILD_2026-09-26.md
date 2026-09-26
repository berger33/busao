# Herói 10/10 — reconstrução do GLB da Fase 1+2 e turnaround fresco (2026-09-26)

**Pedido:** reconstruir o GLB da heroína no sandbox (ambiente bpy do zero) e
renderizar um turnaround atual. Docs anteriores: `HEROI_FASE0_FASE1.md`,
`HEROI_FASE2.md`. Plano: `docs/PLANO_HEROI_10_10.md`.

## Ambiente (sandbox novo, recriado em ~25 s)

`sh tools/blender/make_env.sh` — venv com `bpy==4.5.14 LTS` + stubs X11/GL.
Notas operacionais desta sessão:

- o venv ficou em `/home/user/.venv` com symlink `/home/user/venv-blender`,
  para o caminho que `run_bpy.sh` espera continuar válido sem persistir
  centenas de MB de dependências entre sessões;
- teste: `bpy OK 4.5.14 LTS` via `run_bpy.sh`.

## Fase 1 — `build_heroi_julia.py` (7 s)

| Métrica | Valor | Gate |
| --- | --- | --- |
| Triângulos | **35.952** | ✅ (24k–46k) |
| Faces (quads) | 18.065 (92,1% quads) | ✅ |
| Altura | 1,720 m | ✅ |
| Sola (z mín) | 0,012 m | ✅ |
| Arestas não-manifold | 0 | ✅ |
| GLB base | 634,6 KB | — |

### Descoberta: o script já passou da Fase 2 documentada

O `build_heroi_julia.py` versionado contém a seção **4c. Rosto (Fase 3)** —
`densificar_cabeca()` + `esculpir_rosto()` com pincéis gaussianos (órbitas
escavadas, arco superciliar, nariz, lábios, queixo, maçãs, orelhas). Isso não
estava em `HEROI_FASE2.md` (que dizia "corpo continua sem rosto"). Consequência
prática: **a malha cresceu ~10%** contra o último estado documentado
(35.952 tris vs 32.760) e o bake da Fase 2 cobre rosto no albedo.

Ainda **não** há (continuam sendo Fase 3): globos oculares/pálpebras como
peças, cabelo em cards, sobrancelhas/mechas.

## Fase 2 — `bake_heroi_julia.py --res 2048 --samples 24` (~13 min, 2 núcleos)

| Item | Valor | Gate |
| --- | --- | --- |
| Cobertura do atlas UV | 61,2% | ✅ (≥45%) |
| Albedo | 2.048², 385,9 KB | ✅ |
| Normal | 1.024², 164,3 KB | — |
| ORM | 1.024², 244,1 KB | — |
| Desvios-padrão | albedo 0,361 · normal 0,250 · rough 0,345 | ✅ (não chapado) |
| **GLB final** | **1.672,5 KB** | ✅ (≤2.048) |

Texturas regeneradas em `assets/textures/heroi/` (as commitadas eram do estado
sem rosto — as novas são as corretas para a malha atual; não são referenciadas
em runtime, o GLB embute as próprias).

## Renders (Cycles CPU, estúdio do `render_turnaround.py`)

- `docs/arte_alvo_final/12_turnaround_fase2.png` — 4 vistas
  (frente/3-4/lado/costas), 2.048 amostras somadas;
- `docs/arte_alvo_final/13_mao_detalhe_fase2.png` — close da mão em +X
  (alvo encontrado por heurística: centro (0,287, −0,020, 0,871) m):
  palma em laje + 4 dedos nascendo dentro dela + polegar lateral;
- `docs/arte_alvo_final/14_rosto_detalhe.png` — close do rosto
  (centro (−0,001, −0,061, 1,636) m): primeira evidência renderizada da
  escultura facial da seção 4c.

Novo utilitário **`tools/blender/render_detalhe.py`** (versionado): closes de
`mao`/`rosto` de qualquer GLB, enquadramento automático por heurística
geométrica (o GLB ainda não tem rig/vertex groups), PNG RGBA transparente.

## Artefatos persistidos

`tools/blender/out/` é gitignored e efêmero. Para o estado sobreviver entre
sessões, as saídas foram copiadas para **`assets/characters/source/heroi_julia/`**
(berço de WIP com `.gdignore`, mesma convenção da Ginger):

- `heroi_julia_base.glb/.blend` + métricas (Fase 1 + rosto);
- `heroi_julia_pbr.glb/.blend` + métricas (Fase 2, texturizado).

O contrato de runtime **não mudou**: o jogo continua no placeholder
`personagens/hero_julia.glb` até a Fase 6 (`validate_hero.py` → `HERO OK
MESH-ONLY`).

## Validação

- `python3 tools/validate_hero.py` → `HERO OK MESH-ONLY` (runtime intacto);
- `python3 tools/validate_project.py` → `PRE-FLIGHT OK`.

## Próximo passo

Fechar a **Fase 3**: globos oculares na órbita + pálpebras, cabelo em cards com
alpha (o rosto esculpido já está na malha e no bake). Depois Fase 4 (armature
60 ossos + skinning — os nomes `thumb/index/middle/ring/pinky_01..03_l|r` já
existem nas mãos à espera do rig).

## Reproduzir

```sh
sh tools/blender/make_env.sh
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py --res 2048 --samples 24
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py \
   tools/blender/out/heroi_julia_pbr.glb tools/blender/out/turnaround.png
sh tools/blender/run_bpy.sh tools/blender/render_detalhe.py \
   tools/blender/out/heroi_julia_pbr.glb tools/blender/out/mao.png --alvo mao
```
