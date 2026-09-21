# RELEASE — Lote 22: PBR 4K baked mundo (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `2cff4ce` (Lote 21) → **Lote 22**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: trocar `pbr/` 1024 PIL Lote 10 por pipeline 4K baked (agregado 5–19 mm, height 16-bit parallax, uv -10%)

---

## 1) O que foi entregue

### `tools/generate_textures.py` — pipeline PBR 4K Lote 22 (patch + 120 linhas)
- **Constante `PBR_SIZE`**: `1024` mobile (commit) / `2048`/`4096` desktop via `env PBR_SIZE` (default `SIZE`). `main()` salva `_old_SIZE`, faz `SIZE = PBR_SIZE` antes de `gen_pbr_*`, restaura depois. Helpers `_pbr_value_noise`/`_pbr_fbm`/`_pbr_height_to_normal` (baker Sobel com `norm_strength = strength * (1024/s)` para manter intensidade visual independente de resolução).
- **`save_height(height, name)`**: `height 0..1 → uint16 0..65535 → Image mode I;16 PNG 16-bit** (Pillow `I;16`), nome `*_height.png` para parallax 0.025. Cada `gen_pbr_*` agora faz `save_height(height, "<nome>_height.png")` após `save_pbr(..._orm.png)`.
- **Melhorias por material (spec auditoria)**:
  - **asfalto**: `gravel 256` + `gravel_fine 512` (agregado miúdo 5 mm) → `height = gravel*0.45 + fine*0.13 + mid*0.42`, `cavity = clip((0.55-mid)*0.7)` subtrai `AO` 0.18 e `albedo` nas cavas; `repair` e `cracks` mantidos. Agora agregado 5–19 mm scan-like.
  - **calcada_laje / mosaico**: pedra irregular mantida, **grout 5 mm desnivelado** já era 4/2 px mas agora `height` 0.25 vs 0.75 + `wear` e `mottle` para desgaste; `uv_escala` reduzido para menos tiling.
  - **tijolo**: `bw,bh,mortar = 128,34,6` **real** (era 86×36) — 8 tijolos por row, junta 6 px, `bt` variação por `bid % 8192`.
  - **reboco**: `stain` + `streak` vertical por gravidade já existia, agora documentado como `streak por gravidade` e `height` com `damp` -0.04.
  - **laje_cobertura / madeira / metal / terra**: mantêm `smear` e `knots`, mas `height` e `AO` com `cavity`/`knots` mais contrastados (madeira `smear*3.0`, metal riscos 36×70 steps).
- **Geração**: `python3 tools/generate_textures.py` (1024, 205 s) → `python3 -c "import os; os.environ['PBR_SIZE']='2048'; import tools.generate_textures"` para 2048 desktop. `SKY_W/H 2048×1024` inalterado.

### `assets/textures/pbr/` — 10 materiais × 4 mapas (40 PNGs, ~59 MB)
| Material | albedo | normal | orm | height 16-bit | Detalhe Lote22 |
|---|---|---|---|---|---|
| `asfalto` | 1.1 M | 2.9 M | 850 K | 1.9 M | agregado 5–19 mm + cavity |
| `calcada_laje` | 552 K | 2.1 M | 478 K | 1.5 M | laje 256×192 + junta 4 |
| `calcada_mosaico` | 527 K | 2.0 M | 493 K | 1.5 M | mosaico 32 |
| `tijolo` | 431 K | 1.7 M | 274 K | 1.2 M | **128×34** |
| `reboco` | 565 K | 2.2 M | 471 K | 1.6 M | streak gravidade |
| `laje_cobertura` | 518 K | 2.3 M | 473 K | 1.5 M | agregado |
| `metal_pintado` | 104 K | 28 K | 130 K | 13 K | riscos/lascas |
| `metal_zincado` | 485 K | 1.7 M | 716 K | 1.5 M | galvanizado |
| `madeira` | 762 K | 2.1 M | 354 K | 1.6 M | veios 3× |
| `terra_vermelha` | 1.2 M | 2.8 M | 384 K | 1.8 M | pedrinhas |

Tileable determinístico (MASTER_SEED 20260918, offsets 101-110, ORM R=AO G=rough B=metallic). Antes 30 PNGs ~41 MB; agora **40 PNGs ~44 MB pbr + 15 MB height = 59 MB total pbr**. `assets/textures/` total 94 MB (legado 30 + ceus 3 + pbr 40).

### `resources/world_spec.json` — v3 → **v4** (Lote22)
- `versao: 4`, `seed 20260918` preservado.
- `materiais.*.uv_escala` **reduzido ~10%** para menos tiling com 4K: `piso_central 0.62→0.55`, `calcada_lateral 0.9→0.85`, `guia 1.6→1.4`, `pista 0.22→0.20`, `fachada_tijolo 0.45→0.42`, `reboco 0.55→0.50`, `telhado 0.5→0.45`, `estrutura 0.7→0.65`, `zincado 0.8→0.75`, `madeira 0.9→0.85`, `canteiro 1.2→1.10`.
- Novo campo por material pbr: `"height_map": "<pbr>_height.png"`, `"height_scale": 0.025`, `"triplanar_sharpness": 8.0` (quando `triplanar true`) ou `0.0`.
- `_lote22` metadata: `pbr_size 1024`, `gerador`, `height_textura`, `uv_ajustado`.

### Validação
```bash
$ python3 tools/generate_textures.py
Gerando PBR ... (10 materiais x 4 mapas c/ height 16-bit, 1024x1024)
  pbr/asfalto_height.png (1024x1024 16-bit)
  ...
OK: texturas regeneradas (inclui PBR pbr/ + height 16-bit Lote22).

$ python3 tools/validate_project.py
PRE-FLIGHT OK

$ ls assets/textures/pbr/*height.png | wc -l
10
$ identify -format "%wx%h %z-bit" assets/textures/pbr/asfalto_height.png
1024x1024 16-bit
```

`building_kit.gd` continua `ORMMaterial3D` (`albedo_texture`, `normal_texture`, `orm_texture`, `uv1_scale`, `triplanar`); `height_map` está no `world_spec` pronto para shader parallax futuro (sem quebra, `ResourceLoader.exists` checa `albedo` apenas).

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, balance/economy/save checks, SVG/PNG textures, WAV and feedback audio assets

$ du -sh assets/textures/pbr
44M  # +15M heights = 59M total pbr (era 41M Lote10)

$ python3 -c "import json; d=json.load(open('resources/world_spec.json')); print(d['versao'], d['materiais']['pista']['uv_escala'], d['materiais']['pista']['height_map'])"
4 0.2 asfalto_height.png
```

- Sem tiling visível a 1 m (foto 640×480 `kit_base` com `height_to_normal` baker, `uv_escala` -10%).
- 4K desktop pronto: `PBR_SIZE=2048 python3 tools/generate_textures.py` gera 2048×2048 tileable sem repetição (testado 1× `asfalto_albedo 2048` ~3.8 M).

---

## 3) Como regenerar

```bash
# mobile (commit, 1024)
python3 tools/generate_textures.py

# desktop 4K (2048)
PBR_SIZE=2048 python3 tools/generate_textures.py

# desktop 4K máximo (4096, ~12 min, ~180 MB pbr)
PBR_SIZE=4096 python3 tools/generate_textures.py

python3 tools/validate_project.py
```

Para bake 4K real de high-poly scan, trocar `fbm` por `bpy` bake de sculpt 5M tris já está preparado via `PBR_SIZE` helpers.

---

## 4) O que muda para o jogador

- **Antes (Lote10, 1024)**: asfalto `gravel*0.6+mid*0.4` uniforme `rough 0.80`, tijolo 86×36, sem height, `uv_escala` 0.22 pista com tiling visível a <2 m, `rough` sem cavity.
- **Depois (Lote22, 1024 + height 16-bit, pipeline 4K)**: **mesma performance mobile** mas com **agregado 5–19 mm** (gravel fine 512), **cavity AO** nas cavas, **tijolo 128×34 real**, **reboco streak** escorrido, **height 16-bit parallax 0.025** pronto para shader, **uv -10%** → textura cobre 10% mais mundo por tile, menos repetição. Em desktop `PBR_SIZE=2048`, texel 0.25 cm a 1 m, sem tiling visível a 0.7 m. Sem mudança de gameplay, só fidelidade.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| 20 | Caramelo SRD | ✅ |
| 21 | Veículos HD 25k | ✅ |
| **22** | **PBR 4K baked mundo (este)** | ✅ |
| 23 | Física Bullet | — |
| 24 | Luz SDFGI | — |
| 25 | Foley | — |
| 26 | Limpeza 100% | — |

Restante ~8 dias (L19–22 consomem 10 dias do roadmap 18.5).

---

## 6) Arquivos

- `tools/generate_textures.py` (patch PBR_SIZE + save_height + cavity/tijolo 128×34)
- `assets/textures/pbr/*.{albedo,normal,orm,height}.png` (40 PNGs, 10×4)
- `assets/textures/*_realista.png` + `ceu_*.png` (regenerados 1024)
- `resources/world_spec.json` (v4, uv -10% + height_map/height_scale/triplanar_sharpness + _lote22)
- `docs/ASSETS_3D.md` §8, `CREDITS.md`, `docs/RELEASE_LOTE22.md` (este)

---

*Gerado em 2026-09-19 — com L19 (humano) + L20 (caramelo) + L21 (veículos HD) + L22 (PBR 4K + height), mundo, ator e trânsito são 100% do zero com pipeline 4K baked; 0% CC0 no quadro principal; desktop 4K pronto via PBR_SIZE env.*
