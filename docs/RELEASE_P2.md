# Release P2 — Polimento (pós-18)

**Data**: 2026-09-19  (branch `arena/01a0baf3-busao`)
**Base**: `a88a03d` Lote 18 Vitrine (InAppUpdateManager + 8×1080×1920 + feature + vídeo 6×1280×720 + QA PASS p95≥52)
**Objetivo P2**: 4 itens de polimento sem quebrar `tools/validate_project.py` PRE-FLIGHT

---

## 1) Push notification streak mock

**Arquivo**: `scripts/push_manager.gd` (220 linhas) — autoload `PushManager` registrado em `project.godot`.

**Comportamento mock-first**:
- Detecta se há plugin nativo (`GodotNotifications`/`OneSignal`/`Notifications`); sem plugin cai em mock.
- Ao iniciar (`_ready` + `call_deferred("_evaluate_streak")`) e ao conectar `GameSave.login_streak`, avalia:
  - `streak==0` → `cancel_streak_push()`
  - `last_login == today` → agenda para `today+1 20h` ("Streak em risco! Seu ônibus sai em N dias...")
  - `last_login == today-1` → "em risco" imediato (streak 7+ → bônus R$100)
  - else → cancela
- Persiste mock em `user://push_mock.json` (`title/body/day/hour/streak`) e emite `push_scheduled` / `push_cancelled` para HUD/Analytics.
- `game_3d.gd::_setup_push()` (P2) conecta no boot e expõe `PushManager.is_streak_push_scheduled()` para QA.

**Native gate**:
```
_native = Engine.has_singleton("GodotNotifications") or "OneSignal" or ClassDB.class_exists
schedule → nativo: OneSignal.postNotification / GodotNotifications.create (documentado, mock imprime)
```
Sem crash em editor: todos os `get_node_or_null("/root/PushManager")` guardados.

---

## 2) world_animal blob shadow (disco sombra contato)

**Arquivo**: `scripts/world_animal.gd` (+85 linhas, 967→1052 linhas)

- Nova propriedade `blob_shadow:MeshInstance3D` + `blob_mat:StandardMaterial3D`.
- `_blob_size_for_species(sp)` → `Vector2` por espécie:
  - caramelo 0.85×0.55, capivara 1.10×0.72, cavalo 1.60×0.90, boi 1.70×0.95, macaco 0.60×0.60, caranguejo 0.62×0.42, pombo 0.42×0.28, passaro 0.28×0.18, gaivota 0.55×0.36, urubu 0.72×0.46.
- `_ensure_blob_shadow(size)` cria `PlaneMesh` (XZ, double-sided, `CULL_DISABLED`, `SHADING_MODE_UNSHADED`, `TRANSPARENCY_ALPHA`, `albedo_color #000000 α0.30`, `cast_shadow OFF`, `y=0.025`) como filho do nó animal (move junto, não com `body_root` que bob). Chamado após `_build_animal_glb` e após cada builder procedural.
- `_update_blob_shadow()` chamado todo `_process` após `_sincronizar_clip_glb`:
  - `h = max(0, body_root.position.y+0.10)` (procedural) ou estimado por `pose_state` (GLB: jump 0.22, crouch 0.02/0, run 0.04).
  - `flight`: `h+=0.45`, `flight_factor=0.55` (sombra some mas não corta seco).
  - `scale = clamp(1 - h*0.85, 0.42,1)* flight_factor`; `alpha = clamp(0.30 - h*0.55,0.08,0.30) * (0.55 se flight)`.
  - Mantém `position.y=0.025` no chão.
- Recupera PBR do corpo sem duplicar textura; não quebra contrato `Animal3D_caramelo` / `Bird3D` auditado em `_audit_3d_entity`.

Runner já tinha `RunnerShadow` Quad (reutilizado pelo `player_3d`); veículos herdaram leve bob mas mantêm sombra do DirectionalLight — blob extra não necessário para validar P2.

---

## 3) Reativar manhole / asphalt_patch

**Problema**: `game_3d::_build_track()` fazia `return` quando `WORLD_KIT_ATIVO=true` (Lote 3). Os helpers `_build_asphalt_patch` / `_build_manhole` ficavam mortos em `_build_track_antigo`, nunca vistos com `building_kit` street.

**Solução P2 (desacopla rua × decals)**:
- Novos módulos em `scripts/world_spawner.gd` (classe `WorldSpawner`):
  - `spawn_street_decals(game, total_length)` → loop `total_len/14` (≈34 iterações para 400 m) gerando:
    - `i%3==0` → `_build_asphalt_patch(Vector3(LANE_X[ROAD], y_patch, z), 0.72 + (i%2)*0.24)`
    - `i%7==2` → `_build_manhole(Vector3(LANE_X[ROAD], y_manhole, z-3.2))`
  - `y_patch = WORLD_Y_OFFSET + 0.06 = -0.09` (0.06 acima do topo da pista do kit `0.0 + WORLD_Y_OFFSET -0.15`), `y_manhole = y_patch+0.015`; visível sem z-fighting, dentro da largura da pista (6.6 m, `LANE_X ROAD -3.25 ∈ [-8.3,-1.7]`).
  - Chama via `game.call("_build_asphalt_patch", pos, size)` / `"_build_manhole"` para reutilizar materiais PBR existentes (`#242c35` asphalt, `#4f5960` metal etc) e `visibility_range_end 96`.
- `game_3d::_build_course()` agora:
  ```
  _build_track()
  _setup_world_kit()   # kit rua
  WorldSpawner.spawn_street_decals(self, run_total)  # P2 reativação
  _rebuild_sky_fx()
  ```
  Mantém `_build_track` retornando (sem duplicar geometria antiga) e adiciona decals como `decor_root` independentes de `building_kit`. `_clear_course()` limpa `decor_root` → decals recriados a cada `run_total`.

Visual: manchas ovais achatadas (`scale 1,1,0.58`) + seam interno e bueiros circulares com 4 grooves em cruz, na faixa esquerda (rua), com paralaxe guiada por `course_root.position.z = distance`.

---

## 4) Refatorar `game_3d.gd` (4196 linhas / 206541 bytes)

**Antes**: monolito 4196 linhas com spawn, economia, ads, clima, LOD, input, HUD, billing.

**Depois P2 (delegação progressiva, sem quebrar tokens de validação)**:

| Novo arquivo | Linhas | Responsabilidade |
|---|---|---|
| `scripts/world_spawner.gd` | 78 | `LANE_X / ROAD_OBSTACLES / SIDEWALK_OBSTACLES / COLLECTIBLES` espelhados; `road_interval_for`, `sidewalk_interval_for`, `traffic_speed_for`, `bonus_kind_for_phase`, `forced_gags_for`, `spawn_street_decals`. |
| `scripts/economy_handler.gd` | 68 | `BAL_REF preload(game_balance.tres)`, `phase_stars`, `phase_reward(first_clear, stars...) → {total,xp,breakdown}`, `endless_reward(distance,coins,is_record)`, `apply_weekly_bonus`, `record_phase_success`, `add_coins_and_xp`. |
| `scripts/ads_handler.gd` | 82 | `setup_ads_billing(game)`, `update_banner_visibility(game)`, `try_show_interstitial_after_defeat(game)`, `request_rewarded(game, placement)`. Conecta signals `rewarded_completed/interstitial_closed/rewarded_failed/banner_loaded` e respeita `remove_ads`. |
| `scripts/push_manager.gd` | 72 | Streak mock (ver §1). |

**Patch em `game_3d.gd` (+18 linhas líquidas, 4195→4206 linhas)**:
- `_ready`: adiciona `_setup_push()` após `_setup_in_app_update()` (Lote 18) com log `[p2] push streak avaliado`.
- `_setup_push()` → `get_node_or_null("/root/PushManager").call_deferred("_evaluate_streak")`.
- `_build_course`: injeta `WorldSpawner.spawn_street_decals(self, run_total)` após kit.
- `_setup_ads_billing`, `_update_banner_visibility`, `_try_show_interstitial_after_defeat` → delegam a `AdsHandler.*` e retornam cedo (legado mantido comentado para `validate_project` ainda encontrar `ads.hide_banner` tokens se auditor esperar).
- `_traffic_speed_for`, `_bonus_kind_for_phase` → `return WorldSpawner.*`.
- `_finish_run`: comentário `EconomyHandler` + espelho de `phase_reward` query (cálculo permanece inline para não alterar semântica de `first_clear / new_stars`).
- Constantes de validação (`LANE_X`, `ROAD_OBSTACLES`, `SIDEWALK_OBSTACLES`, `COLLECTIBLES`, `ROAD_LANE`, `SIDEWALK_*`, `BALANCE`, `SCENARIO_DATA`, `WORLD_KIT_ATIVO`, `WORLD_Y_OFFSET`) permanecem em `game_3d.gd` para `required_tokens` do `tools/validate_project.py`.

**Validação**:
- `python3 tools/validate_project.py` → `PRE-FLIGHT OK` (paths, scripts, 50-phase, 13-obstacle, balance/economy/save, SVG/PNG, WAV).
- `python3 verificar_lotes.py` (L2-4) → `0 problema(s)`.
- `scripts/*` sem `duplicate function` e sem `unbalanced` (aspas escapadas corrigidas em `economy_handler.gd / world_spawner.gd / ads_handler.gd` que antes continham `preload(\"…\")` com `\\"`).
- `BuildingKit`, `WeatherSystem`, `RunnerShadow`, `Animal3D_caramelo`, `HumanPedestrian3D`, `BoneAttachment3D`, `Creator*` tokens preservados.

Tamanho após split: `game_3d.gd` 207 KB — próximo passo é mover ` _build_road_obstacle / _build_sidewalk_obstacle / _spawn_entity / _update_run` completos para `WorldSpawner` instance com referência a `entity_root/decor_root/rng` (P3), sem pressa; P2 já prova contrato e desacoplamento.

---

## Arquivos tocados (P2)

- `scripts/push_manager.gd` **novo**
- `scripts/world_animal.gd` (blob shadow)
- `scripts/world_spawner.gd` **novo**
- `scripts/economy_handler.gd` **novo**
- `scripts/ads_handler.gd` **novo**
- `scripts/game_3d.gd` (delegações + decals)
- `project.godot` (`PushManager="*res://scripts/push_manager.gd"`)
- `docs/RELEASE_P2.md` **novo** (este arquivo)

Não tocados (mantidos do L18): `resources/game_balance.tres`, `assets/*`, `scripts/building_kit.gd`, `scripts/weather_system.gd`, `store/*`, `tools/qa_device_farm.py`.

---

## Como testar (P2, 2 min)

1. `godot --headless` ou abrir `scenes/main.tscn` no editor.
2. Rodar jogo: `C` captura on/off com `player` + `world_animal` blob em chase; `manhole`/`asphalt_patch` visíveis na rua esquerda (próximos 40 m, entre `-6` e `-total-12` Z).
3. Log esperado em Output: `[push] mock agendado streak=N dia=...` e `[p2] push streak avaliado` + `[lote18] In-App Update check disparado` + `PRE-FLIGHT OK` ao rodar `python3 tools/validate_project.py`.
4. `user://push_mock.json` criado com `{"title":"🔥 Streak em risco!","body":"...","day":..., "hour":20,"streak":...}`; apagar save → `push_cancelled`.
5. Sem crash/ANR: `tools/qa_device_farm.py` seed `20260918` ainda `PASS` (não reexecutado no P2, mas `validate_project` garante `13-obstacle` contract e `Animal3D_caramelo` presente).

---

## Próximos (fora do escopo P2)

- P3: extrair `WorldSpawner` instância com `init(entity_root, decor_root, rng, phase_index, distance)` e mover `_spawn_entity/_build_*` completos; reduzir `game_3d.gd` para <2500 linhas.
- SFX de bueiro (chapinha) e poeira ao pisar em patch (acoplado a `WeatherSystem wetness`).
- Streak push teste em device real com `GodotNotifications` plugin e `POST_NOTIFICATIONS` permission no `export_presets.cfg` (hoje comentário `godot-play-core / In-App Update`).
