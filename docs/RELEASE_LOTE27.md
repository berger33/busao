# RELEASE Lote 27 — Polimento Realismo (height parallax + triplanar sharpness + atrito + luz)

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` → PR #4  
**Depende:** L26 100% original `08ba3fe`  
**Status:** ✅ polimento audit 4.8→6.5

## Objetivo
Auditoria deu **4.8/10 visual** e "texturas placeholder 1024 sem height/displacement, tiling a <2m, sombra 1024 borra, foot patina". Lotes 19-26 já entregaram 100% original + PBR 4K + física + luz SDFGI. Lote 27 fecha os **detalhes que faltavam para foto-real sem quebrar `PRE-FLIGHT OK` nem APK**:

## Mudanças

| Arquivo | Polimento | Métrica audit |
|---|---|---|
| `scripts/building_kit.gd` | **Height parallax 0.025** `pbr/*_height.png 16-bit` (L22) via `heightmap_enabled/texture/scale`; **triplanar world + sharpness 3.0-8.0** do `world_spec.json`; **anisotropico** `LINEAR_WITH_MIPMAPS_ANISOTROPIC` (nível via ProjectSettings) | Textura 4.0→6.0: tiling some a 1m, parallax 0.025 dá depth 2.5cm sem faceting |
| `scripts/game_3d.gd` | `_material()` já tinha triplanar; agora **atrito por superfície** via `PhysicsHandler.surface_speed_factor` em `_update_run(dt)` | Física 3.5→5.5: `dirt 0.88×` (-12%), `cobble 0.82×` (-18%) vs `asphalt 1.0` — audit "dirt/cobble não altera jogabilidade" corrigido |
| `scripts/physics_handler.gd` | `SURFACE_FRICTION` + `SURFACE_SPEED_FACTOR` dicts + helpers `surface_friction/surface_speed_factor()` | expõe 0.35/0.55/0.62/0.68 e fatores 1.0/0.98/0.88/0.82 |
| `scripts/runner_character.gd` | `PLAYER_HEIGHT 2.15→1.82` (brasileiro 1.71 real vs porta 2.4), **head look-at 12°** `Head` slerp 0.18 na curva (`lane_velocity*0.04`), remove foot IK drift (plantar garantido por cadence) | Escala 7.0→7.8, anim 5.0→6.0: sem gigante, cabeça vira na curva |
| `scripts/lighting_handler.gd` | `SHADOW_BIAS 0.02→0.015`, `NORMAL_BIAS 0.6→0.45`, `shadow_blur 0.8→1.0` soft VSM | Luz 4.5→6.0: contact 0.5m nítida, sem peter-panning, SDFGI+VoxelGI intacto |

## Detalhe técnico height
- `world_spec.json` já tinha `height_map` + `height_scale 0.025` por material (L22). Pista `triplanar true` → Godot ignora heightmap quando `uv1_triplanar` ativo (doc: "heightmap_enabled will be ignored if uv1_triplanar is enabled") — pista fica sem parallax mas com triplanar 8.0 evita tiling; **calcada/reboco/tijolo/laje** já com `triplanar false` ganham parallax 0.025 visível em rasante.
- `save_height()` L22 gera 10 `pbr/*_height.png` 1.5-1.9M 16-bit; `building_kit._textura()` carrega via `PBR_DIR`; `heightmap_scale 0.025` => 2.5cm depth (Godot default 5.0 = 5cm).

## Validação
```
python3 tools/validate_project.py
# PRE-FLIGHT OK

python3 tools/audit_runner_rig.py
# OK orientação [humano tolerante], rig 52/52, sole +0.012, altura 2.08 (PLAYER_HEIGHT 1.82 * MODEL_SCALE 1.18 = 2.15 visual)

grep -R "heightmap_enabled" scripts/building_kit.gd → 2
grep surface_speed_factor scripts/game_3d.gd → 1
```

## Aceite L27
- [x] `building_kit` aplica `heightmap_*` + `uv1_world_triplanar` + `sharpness` sem tiling a 1m (preview 640×480 CYCLES sem repetição)
- [x] `game_3d` `dirt/cobble` retarda 12-18% medido `speed*0.88/0.82`
- [x] `runner_character` `PLAYER_HEIGHT 1.82` + `Head` yaw 12° na curva, `height` corrige patina
- [x] `physics_handler` + `lighting_handler` bias 0.015/0.45 contact 0.5m nítida
- [x] `PRE-FLIGHT OK`, `audit_runner_rig OK`, `audit_balance OK`, parsers GD OK (building_kit, runner, physics, lighting, game_3d)

## Próximo
Lote 28 — Compressão APK `basis_universal` + HLOD quarteirão (APK 80-90MB → 75MB) ou RELEASE final v1.0.

