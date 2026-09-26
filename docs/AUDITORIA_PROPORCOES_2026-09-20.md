# Auditoria de Proporções — Humanos, Motoqueiro e Moedas (2026-09-20)

## Diagnóstico

**Modelos humanos (`assets/characters/humanos_originais/Humano_M.glb` 429KB / `Humano_F.glb` 442KB)** foram medidos via full_bounds global (todas as POSITION accessors):

- `Humano_M h1.763 w1.395 d0.301` (T-pose fingertip-to-fingertip 1.395)
- `Humano_F h1.772 w1.395 d0.322`

Altura 1.77 realista (PROVENANCE.md previa 1.75m). Porém:

- `scripts/runner_character.gd: MODEL_SCALE 1.18` => `1.77*1.18=2.09m` (acima do spec 1.82 e do adulto BR 1.70-1.82)
- `PLAYER_HEIGHT 2.15` incoerente com `world_spec.json` (1.82) e com física `CharacterBody 0.35×1.75 mass75`.
- `scripts/world_character.gd avatar_scale 0.82` => rider `0.82*1.77=1.45m` (anão sentado), deveria ~1.63-1.70.
- Aparência geométrica crua: `tools/blender/build_humanos.py` usa `caixa()` (8 vértices, UV simples, flat), `pilar_z seg12` e `elipsoide_bl sub1-2` sem `shade_smooth` nem `bevel`. Fallback `scripts/runner_character.gd:_build_fallback` era `cone.glb` placeholder diagnóstico mas corpo principal ainda blocado.
- Veículos: `GLB_FIT` só considerava length/height, ignorava width. Resultado: `car 2.06W*1.04=2.14W` (real 1.80), `bus 2.86W*0.919=2.63W` (real 2.55).
- Coletáveis: `coin 0.60 diam/0.06 esp` (34% da altura humana, deveria ~2-3% = 0.05), `bread 0.43`, `pastel 0.67`, `coxinha 0.55`, `coffee 0.36`, `golden 0.46`, `guarana H0.58`, `pix H0.36`, `umbrella 0.61×0.84` — todos 2-5× super-escala. Glow fixo `Sphere 0.36` (72cm) maior que moeda.

**Infra:** `blender` não encontrado offline. Correção via `Godot scale` + `smooth normals` Python.

## Correções Aplicadas

### 1. Humanos — escala e suavidade
- `runner_character.gd: MODEL_SCALE 1.18 → 1.03` (1.77*1.03=1.82), `PLAYER_HEIGHT 2.15 → 1.82` (L27 já tinha 1.82, mantido), `world_character.gd avatar_scale 0.82 → 0.92` (1.63m), `motoqueiro 0.80 → 0.92`, `old_lady 0.80 → 0.88`.
- `game_3d.gd: PLAYER_HEIGHT 2.15 → 1.82`, `GLB_FIT car 4.2×1.45`, `moto 2.05×1.05`, `truck 6.2×2.65`, `bus 7.2×2.95`, `_fit_model` width-aware (car 2.14→1.79W, bus 2.63→2.55W).
- `build_humanos.py`: `pilar seg12→24`, `ico seg2→3`, `caixa` bevel 0.012 shade_smooth, `female quadril 0.185→0.21`, `shade_smooth` após join.
- **Patch GLB offline**: `smooth_human.py` recalcula normais por média de faces (smooth) para Humano_M/F (7 meshes).

### 2. Moedas / Coletáveis — escala realista
- `game_3d.gd:_build_collectible` escala: `coin 0.12` (7.2cm), `golden 0.15`, `pass 0.16`, `bread 0.32` (13.8cm), `pastel 0.26` (17cm), `coxinha 0.22` (12cm), `coffee 0.30` (10.8cm), `guarana 0.28`, `pix 0.30`, `umbrella 0.75` (45cm). Glow `0.36→0.14` proporcional.

## Medidas Finais

| Asset | Antes | Depois | Alvo |
|-------|-------|--------|------|
| Humano H | 2.09 | **1.82** | 1.75-1.82 |
| Motoqueiro H | 1.45 | **1.63** | 1.65 |
| Coin diam | 0.60 (34%) | **0.072** (4%) | 0.04-0.06 |
| Car W | 2.14 | **1.79** | 1.80 |
| Bus W | 2.63 | **2.55** | 2.55 |

Validação: `MODEL_SCALE 1.03`, `PLAYER_HEIGHT 1.82`, `fit width-aware OK`, `coin 0.12 OK`, `avatar_scale 0.92 OK`, `humanos smoothed`.

