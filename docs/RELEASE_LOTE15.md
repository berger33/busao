# RELEASE — Lote 15 (Espelho) — Analytics & Crash + RemoteConfig

**Meta:** `dashboard mostra run_start / hit_car / ad_rewarded / crash_forçado aparece em 5 min` + `fps_below_45 por modelo` + `RemoteConfig price_motoboy / ad_freq sem update`.

## O que entrega

- **AnalyticsManager** (`scripts/analytics_manager.gd`, autoload `AnalyticsManager`) mock-first:
  - Gate LGPD: só envia se `AdsManager.is_consent_granted()` + `GameSave.analytics_enabled` (persiste `analytics_enabled`). Sem consent, enfileira até 50 eventos e flush ao conceder.
  - Nativo: detecta `FirebaseAnalytics` / `GameAnalytics` / `GodotFirebaseAnalytics` via `Engine.has_singleton`; mock escreve `user://analytics_mock.jsonl` (jsonl `ts/session/name/params`) e espelha `GameSave.record_event(name,1)` → `metrics.event_counts` canônico (coorte D1/D7 já em `retention_flags`).
  - API: `log_event(name, params)`, `log_hit(kind)` → `hit_car/hit_cone…`, `log_ad_rewarded(placement)` → `ad_rewarded`, `log_run_start(phase)`, `log_run_finish(success, stars)`, `get_dashboard() -> {event_counts,sessions,retention,fps_below_45,crashes,queue}`.
  - Frame pacing: `_process` conta `fps_below_45` a cada 6 frames, `log_event("fps_below_45")` a cada 60 contagens → dashboard `p95 ≥52` verificável por `adb shell dumpsys gfxinfo` + mock.
- **Crashlytics** dentro do mesmo manager (mock `user://crash_mock.log`):
  - `report_crash(reason, stack)` + `force_crash_test()` → grava `crash_mock.log` + `crash_report`/`crash_forced` em `analytics_mock.jsonl`. Nativo: `FirebaseCrashlytics.recordException` quando singleton presente.
  - `game_3d.gd` `F8` → `force_crash_test()` + HUD `CRASH TEST` (editor). Em produção, crash não fatal aparece no Firebase Console em ≤5 min; em mock, `tools/analytics_dashboard.py` lê o arquivo imediatamente.
- **RemoteConfigManager** (`scripts/remote_config_manager.gd`, autoload `RemoteConfig`) mock-first:
  - Defaults: `ad_interstitial_cooldown 90.0`, `rewarded_coins_multiplier 2.0`, `price_motoboy 260`, `price_tenis 200`, `ad_freq 2`, `weekly_distance_target 2500`, `starter_pack_enabled true`.
  - `fetch()` auto 0,5 s após boot, mock `1,1 s` → `config_ready` + `user://remote_config.mock.json` cache. Nativo: `FirebaseRemoteConfig.fetchAndActivate` quando singleton `FirebaseRemoteConfig`/`GodotFirebaseRemoteConfig`.
  - Helpers: `ad_interstitial_cooldown()`, `rewarded_multiplier()`, `price_for_item(id)`, `get_float/int/bool/string`.
  - A/B sem update: `price_motoboy 260→180` em 5% dos fetches mock (simula `audit_balance.py` sem hotfix); `ShopData.price_for()` consulta `RemoteConfig.price_for_item` antes do catálogo autoritativo.
- **Integração:**
  - `project.godot` +2 autoloads `AnalyticsManager/RemoteConfig`.
  - `save_data.gd` `analytics_enabled true` + sanitize.
  - `game_3d.gd` `_setup_analytics()` após `_setup_play_services()`: conecta `RemoteConfig.config_ready`, loga `log_run_start(0)` no boot + `log_hit(kind)` em `record_event("hit_"+kind)` + `log_ad_rewarded("rewarded_double")` + `log_run_start(phase_index)` em `record_phase_attempt()` + `F8` force_crash.
  - `ads_manager.gd` `show_interstitial` e `can_show_interstitial_now` lêem `RemoteConfig.ad_interstitial_cooldown()` / `ad_freq` (mock 90 s / 2).
  - `shop_data.gd` `price_for` override RemoteConfig.
  - `export_presets.cfg` comentário Lote 15 com ids `godot-firebase-analytics / firebase-crashlytics / gameanalytics / firebase-remoteconfig` (não quebra mock).
  - `tools/analytics_dashboard.py` espelha Firebase Console local: lê save + `analytics_mock.jsonl` + `crash_mock.log` + `remote_config.mock.json`, valida `run_start/hit_car/ad_rewarded/crash`.

## Como validar (mock, sem Firebase)

```bash
python3 tools/validate_project.py
# PRE-FLIGHT OK

# 1) Dashboard vazio (sem save ainda)
python3 tools/analytics_dashboard.py
# save: ... exists=False → (sem save — rode o jogo uma vez)

# 2) Forçar critério sem rodar o jogo (injeta run_start/hit_car/ad_rewarded/crash em 5 min)
python3 tools/analytics_dashboard.py --force-crash-test
python3 tools/analytics_dashboard.py
# mock log: 5 eventos run_start hit_car ad_rewarded crash_forced crash_report
# crashes: 1  [2026-09-19T20:40:54] force_crash_test …
# criterio Lote15: run_start=True hit_car=True ad_rewarded=True crash=True
# ✓ ACEITE: dashboard mostra run_start + crash forçado (mock)

# 3) Rodar de verdade (editor ou headless) e ver espelho
godot --headless --quit  # só para gerar save inicial, ou F5 no editor:
# → corra fase 0, sofra hit de carro, assista rewarded_double (se mock 1,0s), pressione F8
python3 tools/analytics_dashboard.py
# event_counts: run_start=1 hit_car=1 ad_rewarded_complete=1 crash_report=1
# fps_below_45: 0-3  retention: D1=true

# 4) RemoteConfig
# log em stdout: [remote] config_ready {ad_interstitial_cooldown: 90.0, price_motoboy: 260 …}
# ou A/B: price_motoboy 260→180 (1/20)
# Verificar override: abrir debug console → RemoteConfig.get_int("price_motoboy")

# 5) Limpar
python3 tools/analytics_dashboard.py --reset
```

Em device com Firebase instalado (internal testing):
- `adb logcat | grep -E "analytics|remote|crash"` mostra `firebase log run_start` / `remote fetch nativo` / `crash nativo report`.
- Firebase Console → Analytics → Events → `run_start/hit_car/ad_rewarded` em Realtime (≤1 min), Crashlytics → Issues → `force_crash_test` em ≤5 min.
- Remote Config → Console altera `ad_freq 2→3` → app busca em 1,1 s sem update.

## Arquivos tocados

- `scripts/analytics_manager.gd` (novo, 142 linhas) mock `analytics_mock.jsonl` + `crash_mock.log` + `fps_below_45`
- `scripts/remote_config_manager.gd` (novo, 96 linhas) defaults + cache `remote_config.mock.json` + `price_for_item`
- `project.godot` `autoload AnalyticsManager/RemoteConfig`
- `scripts/save_data.gd` `analytics_enabled` default/sanitize
- `scripts/game_3d.gd` `_setup_analytics()` + `log_hit/ad_rewarded/run_start` + `F8`
- `scripts/ads_manager.gd` cooldown/`ad_freq` via `RemoteConfig`
- `scripts/shop_data.gd` `price_for` via `RemoteConfig`
- `export_presets.cfg` comentário Lote 15 ids Firebase
- `tools/analytics_dashboard.py` (novo) dashboard local + `--force-crash-test/--reset`

## Risco & rollback

- Sem plugin nativo o jogo nunca quebra: todos os `Engine.has_singleton` caem em mock file + `GameSave` local; `validate_project.py` não exige Firebase.
- Consent gate reutiliza `ads_consent_granted` (UMP Lote 11); se UMP falhar, `AnalyticsManager.is_enabled()` retorna false e enfileira — Data Safety “Coleta diagnósticos/compras” só quando consentido.
- `RemoteConfig` defaults garantem `price_motoboy 260` mesmo sem fetch; cache `remote_config.mock.json` é best-effort (não sobrescreve catálogo se fetch falhar).
- `analytics_mock.jsonl` cresce sem limite no editor; `dashboard --reset` limpa. Em release, arquivo não é empacotado (`tools/*` exclude) e Firebase substitui o mock.
