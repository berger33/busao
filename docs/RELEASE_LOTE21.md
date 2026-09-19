# RELEASE — Lote 21: Veículos HD 25k (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `0b1d759` (Lote 20) → **Lote 21**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: substituir os 7 GLBs do Lote 5 por versão HD 25k (seg 28 + Subd 2) e manter 4 variantes recolore sem baking

---

## 1) O que foi entregue

### Veículos HD — `tools/blender/build_lote21_hd.py` (novo, ~430 linhas, reusa `kit_base.py`)
- **Geometria HD**: `hd_loft_box` com `seg=28` (era 20), `Bevel width 0.012 × 2 seg`, `Subsurf nível 2` (era 1). Casco super-elipse em 7–9 seções por veículo, topo/capô/parabrisa com curvatura contínua, vidro curvo separado.
- **Rodas HD**: cilindro 28 vértices + 12 loopcuts, `BikeWheel`/`Wheel`/`BusWheel`/`MotoWheel` com eixo em **X** (compatível com `_animate_traffic` que gira `rotation.x`). Diâmetro 0.62 (carro) a 0.68 (ônibus), largura 0.22–0.28, material borracha Principled rough 0.90 + pneu com 5 anéis.
- **Detalhes novos**:
  - **Maçaneta côncava recess** (caixa 0.05×0.015 recess 0.008) + friso lateral cromo (0.02 espessura) na porta,
  - **Interior visível**: bancos (quatro prismas + encosto), volante torus e painel preto fosco atrás do vidro escuro (transmission 0.75),
  - **Espelhos** cubo + haste cromo,
  - **Faróis/lanternas emissivos** (Emission Strength 0.35 / 0.22) + placa branca,
  - **Ônibus**: 6 fileiras de bancos (12 assentos), letreiro **512×128** emissivo 3.2 (`texto_emissivo_hd` com PIL, “PONTO FINAL” / “CIRCULAR”), vidros duplos, portas no lado -X com batente.
- **Materiais HD**: `PinturaHD` Principled BaseColor + Rough 0.32 + **Coat Weight 0.35 / Coat Roughness 0.25** (clearcoat), `CromoHD` metal 1.0 rough 0.14, `VidroHD` transmission 0.75, `BorrachaHD`, `FarolHD` emissivo, `LanternaHD`. Sem textura externa — cores sólidas PBR.
- **Export**: 7 GLBs + 4 variantes recolore (11 arquivos) em `assets/vehicles/`:

| GLB | Tamanho | Materiais | Nós | Prims | verts | SHA-12 |
|---|---|---|---|---|---|---|
| `car.glb` (hatch vermelho 0.615,0.143,0.158) | 1 609 364 B (1572 K) | 9 | 5 | 20 | ~91k | f036a45d7d53 |
| `car_azul.glb` (azul 0.14,0.28,0.68) | 1 609 324 B | 9 | 5 | 20 | ~91k | 1ba8497d90ac |
| `car_prata.glb` (prata 0.76,0.77,0.79) | 1 609 324 B | 9 | 5 | 20 | ~91k | 1f7654f30fa0 |
| `carro.glb` (sedan prata) | 1 795 700 B (1754 K) | 9 | 5 | 20 | ~101k | b6f31275c89a |
| `motorcycle.glb` (preta 0.13) | 430 568 B (420 K) | 6 | 3 | 11 | ~24k | ac0f15397b90 |
| `motorcycle_verde.glb` (verde 0.14,0.52,0.22) | 430 528 B | 6 | 3 | 11 | ~24k | 623ba01811db |
| `truck.glb` (azul 0.13,0.34,0.55) | 959 156 B (937 K) | 10 | 5 | 21 | ~54k | 8b6fc2f8aaad |
| `truck_vermelho.glb` (vermelho 0.70,0.14,0.13) | 959 116 B | 10 | 5 | 21 | ~54k | ff3691af9d88 |
| `bus_traffic.glb` (7.4 m amarelo CIRCULAR) | 1 395 396 B (1363 K) | 11 | 5 | 21 | ~78k | 4d6a45d9ccba |
| `onibus.glb` (8.2 m amarelo PONTO FINAL) | 1 386 892 B (1354 K) | 11 | 5 | 21 | ~78k | a6a5add782ae |
| `bicycle.glb` | 609 060 B (595 K) | 5 | 3 | 12 | ~34k | be1339260ab3 |

  - **Frente -Z**, origem no chão, `GLB_FIT` preservado (car 4.4×1.55, truck 6.4×2.7, bus_traffic 7.4×3.0, onibus 8.2×3.0, bicycle 1.85×1.15) — `_fit_model` em `game_3d.gd` continua sem alteração.
  - Rodas mantêm nomes `Wheel*`/`BusWheel*`/`MotoWheel*`/`BikeWheel*` para `_animate_traffic`.
  - Comando: `tools/blender/run_bpy.sh tools/blender/build_lote21_hd.py` (Blender 4.5 headless) → 7 renders `tools/blender/out/lote21_*.png` (~315 KB cada, Cycles 24sp, fundo 0.42,0.50,0.62, lente 42).
  - **Variantes recolore**: não mais baked 256² Lote 6; agora cópia HD + **patch JSON `baseColorFactor`** (Python `struct` rewrite GLB, chunk JSON repadded espaços) troca `hatch_hd_pintura`/`truck_hd_pintura`/`moto_hd_pintura`.

### Validação GLB
```bash
$ python3 -c "import struct,json; d=open('assets/vehicles/car.glb','rb').read(); jl=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+jl].rstrip(b' ').decode()); print(j['materials'][0]['pbrMetallicRoughness']['baseColorFactor'])"
[0.615..., 0.143..., 0.158..., 1]
$ python3 tools/validate_project.py
PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, balance/economy/save checks, SVG/PNG textures, WAV and feedback audio assets
```

### Integração mundo
- Nenhuma mudança em `scripts/game_3d.gd` / `world_spawner.gd`: `VEHICLE_VARIANTS` (`car→car_azul/prata`, `truck→truck_vermelho`, `motorcycle→motorcycle_verde`) e `_pick_vehicle_variant()` continuam sorteando `hash(kind+entities.size()+phase_index)`. `_optional_model`/`_fit_model` já tratam drop-in.
- `docs/ASSETS_3D.md` §3 atualizado para **Lote 21 HD** (tabela com tamanhos/mats/verts, referência `build_lote21_hd.py`, variantes via patch JSON) + plano de lotes linha **21**.
- `CREDITS.md` atualizado: **Veículos (Lote 21 HD — sobrescreve Lote 5)** com descrição completa e tamanhos.
- Previews HD: `tools/blender/out/lote21_*.png` (7) → `docs/media/vehicle_hd_*.png` (11 com variantes copiadas).

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK
$ ls -lh assets/vehicles/*.glb
# 11 GLBs HD, total ~12.5 MB (era ~4.6 MB Lote 5/6)
$ python3 -c "import hashlib,pathlib; [print(pathlib.Path(p).name, hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]) for p in sorted(pathlib.Path('assets/vehicles').glob('*.glb'))]"
```

- `check_paths` verde: 11 GLBs existem, `GLB_FIT` contém 6 entradas.
- `check_3d` contrato intacto; rodas `Wheel*` verificadas em `_animate_traffic`.
- 100% original Blender para veículos agora (Lote 5/6 substituídos); nenhum CC0 de terceiros no trânsito visível.

---

## 3) Como regenerar

```bash
tools/blender/run_bpy.sh tools/blender/build_lote21_hd.py
# opcional: repatch variantes se editar cores
python3 - << 'PY'
import struct,json
from pathlib import Path
def patch(src,dst,idx,col): ...
PY
python3 tools/validate_project.py
```

Render HD: `K.setup_preview` + `K.render_de` (Cycles 24 samples) em `build_lote21_hd.py:render_veiculo`.

---

## 4) O que muda para o jogador

- **Antes (Lote 5)**: hatch/sedan low-poly seg20 subd1, rodas 22 seg, sem interior, letreiro 256×64 energia 2.6, variantes baked 256², maçaneta flat.
- **Depois (Lote 21 HD)**: **mesmas silhuetas porém HD 25k** — casco seg28 subd2 com Bevel (cantos arredondados), **clearcoat 0.35** (brilho automotivo), **maçaneta côncava recess + friso cromo**, **interior visível** (bancos/volante) pelo vidro escuro, **letreiro 512×128 energia 3.2** (legível a distância), **rodas 28 seg/12 cortes** (rolagem mais suave), **6 fileiras de bancos no ônibus**. Trafego agora tem reflexo e profundidade; tamanho em jogo idêntico (`GLB_FIT`), sem mudança de gameplay.
- **Variantes**: antes bake PIL 256²; agora **mesma malha HD** recolore `baseColorFactor` — azul/prata/vermelho/verde mantêm HD, sem pixelização.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| 20 | Caramelo SRD | ✅ |
| **21** | **Veículos HD 25k (este)** | ✅ |
| 22 | PBR 4K baked (asfalto/madeira/vidro) | — |
| 23 | Física Bullet | — |
| 24 | Luz SDFGI | — |
| 25 | Foley | — |
| 26 | Limpeza 100% | — |

Restante ~10 dias (L19–21 consomem 8 dias do roadmap 18.5).

---

## 6) Arquivos

- `tools/blender/build_lote21_hd.py` (novo, HD)
- `assets/vehicles/*.glb` (11 sobrescritos — 7 bases HD + 4 variantes patch JSON)
- `tools/blender/out/lote21_*.png` (7 renders) + `docs/media/vehicle_hd_*.png` (11 previews)
- `docs/ASSETS_3D.md`, `CREDITS.md`, `docs/RELEASE_LOTE21.md` (este)

---

*Gerado em 2026-09-19 — com L19 (humano) + L20 (caramelo) + L21 (veículos HD 25k), os três pilares visíveis do gameplay (ator, fauna e trânsito) são 100% Blender do zero em HD; 0% CC0 de terceiros no quadro principal.*
