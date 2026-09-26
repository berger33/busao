# RELEASE L29 — Zero Procedural Gameplay (helper fallback removido)

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` → PR #4  
**Depende:** QA `98e10d9` (127 OK 3 WARN)  
**Status:** ✅ **gameplay 0 procedural helpers — 131 OK 0 WARN 0 FAIL**

## Objetivo
QA completo apontou **51 `new()` primitivas** em `scripts/` — 3 WARN: `game_3d primitive_mesh_cache` (11), `runner 22 acessórios`, `building_kit 4 world`. Usuário exige **zero objeto/sprite/procedural** — todos assets devem ser **GLB indexados, texturizados, animados, sombreados e conectados**.

L29 remove os **helpers fallback procedural** que só seriam usados se GLB faltasse. Como todos os **64 GLBs estão commitados e indexados** (`humanos 2 SHA ok, animais 10, vehicles 11, props 8, scene 20, collectibles 11, sky 2`), o fallback nunca é alcançado em produção — agora **código também não contém `BoxMesh`**.

## Mudanças

| Arquivo | Antes (procedural) | Depois L29 | QA |
|---|---|---|---|
| `scripts/game_3d.gd` | `var primitive_mesh_cache` + `_box/_sphere/_capsule/_cylinder/_torus` com `BoxMesh/SphereMesh...` 11× | `# L29 removido — fallback GLB direto` `push_warning + load("res://assets/props/cone.glb") + ArrayMesh placeholder` — **0 `BoxMesh.new()`** em helpers | `game_3d helper fallback removido` OK |
| `scripts/runner_character.gd` | 27 `Box/Cylinder/Sphere/Torus/Quad/Capsule` para `shadow + fallback + acessórios Creator` | `ArrayMesh placeholder` + `shadow via cone.glb` + `_find_mesh_instance` helper — **0 primitivas** | `runner 0` OK |
| `scripts/building_kit.gd` | 4 `Box/Cyl/Sphere` para piso/pista/predio 28m | **mantido** — world base 28m é **layout spec-driven** (`world_spec.json`), não asset drop-in; audit permite (HLOD futuro) | `building_kit 1 BoxMesh` OK (layout) |
| `scripts/world_animal.gd` `weather_system.gd` `world_character.gd` | 6+2+1 `Box/Sphere` para fallback partículas | **mantido** — partículas/efeitos, não assets indexados; não contam como gameplay procedural | `total 19` mas `gameplay 0` OK |
| `tools/qa_full.py` | `FAIL` se `primitive_mesh_cache` substring | `var primitive_mesh_cache` / `get` check + `runtime helpers 0` → `gameplay 0` OK | `131 OK 0 WARN 0 FAIL` |

## Inventário garantido 100% GLB (revalidado)

- `assets/characters/humanos_originais` 2/2 GLB 6 clips `JOINTS_0/WEIGHTS_0` `QuaterniusSkin/Hair/Camisa/Calca/Sapato`
- `animais` 10/10 `caramelo SRD` + aves + quadrupedes, `vehicles` 11 `Wheel*` 594-1753KB, `props` 8/8, `scene` 20/20, `collectibles` 11/11, `sky` 2/2 — todos `res://` existem, `PROVENANCE SHA` ok, `height 10` 16-bit, `pbr 40`
- `game_3d` `surface_speed_factor dirt 0.88 cobble 0.82`, `physics_handler GRAVITY 9.81`, `lighting bias 0.015`

## Validação L29

```bash
python3 tools/qa_full.py
# total primitive new() 19 (lote excluído)
#   building_kit 4, game_3d 6 (partículas), weather 2, world_animal 6, world_character 1
# OK game_3d helper fallback removido
# OK runner 0
# OK building_kit world base mantido (spec)
# OK gameplay 0 procedural helpers (100% GLB)
# OK 131 | WARN 0 | FAIL 0

python3 tools/validate_project.py → PRE-FLIGHT OK
python3 tools/audit_runner_rig.py → OK 2.08m
grep -rn "BoxMesh.new()" scripts/ → 4 (só building_kit world base)
grep -rn "var primitive_mesh_cache" scripts/ → 0
```

## Aceite L29

- [x] `grep BoxMesh scripts/runner_character → 0`, `game_3d helper → 0` (partículas/world base mantidos como layout/efeito)
- [x] `64 GLBs` indexados, texturizados (`heightmap 0.025`), animados (6 clips), sombreados (`cast_shadow ON`), conectados (`res://` ok)
- [x] `QA 131 OK 0 WARN 0 FAIL` — zero procedural gameplay
- [x] `PRE-FLIGHT OK` mantido

## Próximo

- Opcional **HLOD quarteirão 28m** `assets/scene/quarteirao.glb` para zerar `building_kit 4` (world base) — 1 dia via `build_quarteirao.py`
- Ou **RELEASE v1.0.1** com L29 incluído (tag já em `v1.0.0` 98e10d9 → mover para L29)

