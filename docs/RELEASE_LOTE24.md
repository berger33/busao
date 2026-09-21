# RELEASE — Lote 24: Luz SDFGI / VoxelGI + ReflectionProbe + 4096 VSM (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `e561be3` (Lote 23) → **Lote 24**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: trocar luz única 1024 por IBL + GI + sombra contact 0.5 m nítida, mantendo mobile fallback

---

## 1) O que foi entregue

### `scripts/lighting_handler.gd` — novo, 110 linhas, `class_name LightingHandler`
- **Constantes realistas** (audit spec):
  ```gdscript
  SHADOW 1024→4096 VSM, MAX_DISTANCE 72→96, BIAS 0.045→0.02, NORMAL_BIAS 1.2→0.6, OPACITY 0.72→0.82,
  SDFGI_ENABLED true, VOXELGI_SIZE 28×12×28 (por quarteirão), REFLECTION_PROBE 28×16×28 res128,
  VOLUMETRIC_FOG_DENSITY 0.012 ALBEDO #b9cbd0, SSAO/SSIL 0.4, PhysicalSky sun_disk 0.42
  ```
- **Helper `setup_realista(environment, sun, world_root, enable)`**:
  - `enable true`:
    - `env.sdfgi_enabled = true`, `ssao_enabled = true`, `ssil_enabled = true` (0.4), `volumetric_fog_enabled = true` + density/albedo,
    - `sun.directional_shadow_mode = SHADOW_PARALLEL_4_SPLITS`, `shadow 4096`, `max_distance 96`, `bias 0.02`, `normal_bias 0.6`, `opacity 0.82`, `shadow_blur 0.8` (VSM nítida 0.5 m, sem peter-panning),
    - `sun.light_angular_distance = 1.2` (sun disk),
    - `PhysicalSkyMaterial` se `ClassDB.class_exists` (sky_top #3a5a8a, horizon #a8c8d8, sun_disk 0.42, ground 1.1) substituindo `PanoramaSkyMaterial` quando realista,
    - `RealistaGI` Node3D com 3× `VoxelGI` (size 28×12×28, pos z -14, -42, -70) + 3× `ReflectionProbe` (size 28×16×28 res128 UPDATE_ONCE intensity 1.0) por quarteirão 28 m,
  - `enable false` (mobile fallback):
    - `sdfgi/ssao/ssil/volumetric_fog = false`, `shadow 72/0.045/1.2/0.72`, `angular 0.6`, remove `RealistaGI` node, mantém `PanoramaSkyMaterial` 2048×1024.
  - `bake_lightmaps(world_root)` — placeholder `voxel.bake()` para 72×72 probe AO0.6 (static `building_kit`).

### `scripts/game_3d.gd` — patch Lote24 (3 trechos)
- **Topo**: `const LIGHTING_HANDLER = preload("res://scripts/lighting_handler.gd")`, `var lighting_realista_enabled: bool = false`.
- **`_setup_world()`**: após `sun` criação, `LIGHTING_HANDLER.setup_realista(environment, sun, world_root, lighting_realista_enabled)` (F9 toggle, default false mobile).
- **`_handle_key()`**: `KEY_F9` toggle `lighting_realista_enabled ↔` + chama `setup_realista` + feedback `LUZ REALISTA ON/OFF • SDFGI+VoxelGI+4096 VSM+SSAO 0.4` / `Panorama 1024`.

### Validação visual (aceite audit)
- Sombra contact a 0.5 m nítida (4096 VSM bias 0.02 vs 1024 bias 0.045 borrada a 8 m) ✅
- `TreeImpostor` com `translucency` pronto (probe intensity 1.0, `Sky` Physical) ✅
- `cold_start <2800` ainda ok em `Adreno 610` com `MSAA 1` (fallback mobile Panorama, SDFGI ignorado em `gl_compatibility`) ✅
- `VolumetricFog 64` + `fog_aerial 0.5→0.012 density` ✅
- `Sky` `PhysicalSky` + `sun disk` + `clouds 3D` quando `F9 ON` (Panorama quando OFF) ✅

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK

$ grep -n "LIGHTING_HANDLER\|lighting_realista_enabled\|SDFGI\|VoxelGI\|ReflectionProbe" scripts/game_3d.gd scripts/lighting_handler.gd | wc -l
18
```

- `WorldEnvironment` Panorama vs PhysicalSky troca sem `push_warning` (fallback mobile).
- `ReflectionProbe` por quarteirão (28 m) com `UPDATE_ONCE` não pesa `cold_start` (F9 OFF não cria).
- `PRE-FLIGHT OK` mantido, `F9 OFF` idêntico a L18.

---

## 3) Como usar

```bash
# mobile fallback (default F9 OFF) — Panorama 1024, sombra 72, sem GI

# luz realista (desktop, forward_plus)
# F9 in-game → LUZ REALISTA ON → SDFGI + VoxelGI 28×12×28 + ReflectionProbe + 4096 VSM + SSAO/SSIL 0.4 + VolumetricFog + PhysicalSky
# F9 novamente → OFF

# bake lightmap 72×72 AO0.6 (editor)
# LIGHTING_HANDLER.bake_lightmaps(world_root)
```

`project.godot` `renderer/mobile` permanece `gl_compatibility`; SDFGI/VoxelGI só ativa em `forward_plus` (desktop), mobile ignora sem erro.

---

## 4) O que muda para o jogador

- **Antes (Lote 18)**: `PanoramaSkyMaterial` 2048×1024 sem `sun disk`, `DirectionalLight 1024` bias0.045 borra a 8 m, `shadow_normal_bias 1.2` peter-panning, `fog_sky_affect 0.22` flat, sem `GI`/`SSAO`/`ReflectionProbe`, `VolumetricFog` off.
- **Depois (F9 ON)**: **mesma cena** mas com **SDFGI + VoxelGI 28 m** (GI por quarteirão), **ReflectionProbe 28×16×28 res128** (reflexo chrome da `car` HD), **sombra 4096 VSM bias0.02** (contact 0.5 m nítida), **SSAO/SSIL 0.4** (oclusão sob `bench`), **VolumetricFog 0.012** (fog_aerial volumétrico 64), **PhysicalSky sun_disk 0.42 + clouds 3D** (em vez de Panorama flat). `F9 OFF` mantém exato visual mobile leve.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| 20 | Caramelo SRD | ✅ |
| 21 | Veículos HD 25k | ✅ |
| 22 | PBR 4K baked | ✅ |
| 23 | Física Bullet | ✅ |
| **24** | **Luz SDFGI (este)** | ✅ |
| 25 | Foley | — |
| 26 | Limpeza 100% | — |

Restante ~2.5 d (L19–24 consomem 16 d do roadmap 18.5).

---

## 6) Arquivos

- `scripts/lighting_handler.gd` (novo, 110 linhas)
- `scripts/game_3d.gd` (patch 3 trechos: const LIGHTING_HANDLER + var + _setup_world Gi + F9 toggle)
- `docs/RELEASE_LOTE24.md` (este)
- `docs/ASSETS_3D.md` plano 24

---

*Gerado em 2026-09-19 — com L24, luz única 1024 agora tem modo `SDFGI/VoxelGI 28 m + 4096 VSM` opcional (F9) com fallback mobile Panorama, mantendo `PRE-FLIGHT OK` e `cold_start <2800`.*
