# Lote 13 — Release AAB assinado + Play Games Cloud + In-App Review

Data: 2026-09-19 • Guarulhos • branch `arena/01a0baf3-busao` • Godot 4.7 • `com.arena.correponto`
Base: Lotes 11+12 (commit `8e73af4` PRE-FLIGHT OK) • Alvo Play Console internal testing

---

## 1. Objetivo (roadmap `docs/PLANO_COMERCIAL.md` — Lote 13)

- **Keystore RSA4096 fora do repo** + **AAB assinado** (`build/corre-pro-ponto.aab`, não APK), `versionCode` incremental, `targetSdk 35`.
- **Play Games Sign-In silencioso** + **Saved Games / Snapshots** (`<50 KB`, resiliente a `reinstall` e a downgrade) restaurando `remove_ads`, `phase_stars`, `coins`/`hard_currency`, `inventory`.
- **In-App Review** condicionado a `first_clears >= 3` + cooldown 3 dias / 90 s, sem quebrar fluxo.

Critério de aceite: desinstalar via `adb shell pm clear` / reinstall e ver `remove_ads + estrelas` restaurados; Review não bloqueia resultado; AAB instala e valida `jarsigner -verify`.

---

## 2. O que foi entregue

### 2.1 Keystore & Export

| Artefato | Detalhe |
|----------|---------|
| `tools/make_keystore.sh` | `keytool -genkeypair -keyalg RSA -keysize 4096 -validity 10000 -alias correpro -dname "CN=Arena Busao, O=Arena, L=Guarulhos, S=SP, C=BR"` . Saída padrão `../corre-pro-ponto.keystore` (irmão do repo, == `$HOME/corre-pro-ponto.keystore` quando repo em `$HOME/busao`). Nunca commitado — `*.keystore` no `.gitignore`. |
| `export_presets.cfg` | `export_path="build/corre-pro-ponto.aab"` (AAB), `keystore/release="../corre-pro-ponto.keystore"` + `release_user="correpro"` (senha preenchida no editor, não no repo), `version/code=1` / `name=1.0.0`, `minSdk 26 targetSdk 35`, `architectures/arm64-v8a=true`, `permissions/internet=true` + `access_network_state=true`. Comentário com ids de plugins: `godot-play-gameservices`, `godot-google-play-billing`, `admob`, `godot-inapp-review` (adicionar em Export → Plugins e re-exportar; mock cobre editor). |
| `.gitignore` | já ignora `*.keystore`, `*.aab`, `build/` — nenhum binário vai para o git. |

**Como gerar:**

```bash
./tools/make_keystore.sh                # padrão ../corre-pro-ponto.keystore
# ou
./tools/make_keystore.sh /caminho/meu.keystore
# Depois no Godot: Project → Export → Android → keystore/release = caminho acima
# Exportar: Project → Export → Export PCK/AAB → build/corre-pro-ponto.aab
keytool -list -v -keystore ../corre-pro-ponto.keystore | grep -i "4096\|10000\|correpro"
jarsigner -verify -verbose -certs build/corre-pro-ponto.aab | head
```

> A chave fica com validade longa (10000 dias ≈ 27 anos) para evitar rotação forçada do upload key no Play Console. Faça backup em 1Password/Drive.

### 2.2 Play Services — `scripts/play_services_manager.gd` (mock-first)

Autoload `PlayServicesManager` (`project.godot`). Contratos:

- **Detecção nativa segura:** `Engine.has_singleton("GodotPlayGameServices"/"PlayGameServices"/"PlayGames")` e `GodotInAppReview`/`InAppReview`. Se não houver (editor), cai em **mock** com timers (`sign-in 0.9 s`, `cloud 0.6 s`, `review 0.8 s`) e persistência `user://cloud_snapshot.mock.json`.
- **Sinais:** `signed_in`, `signed_out`, `sign_in_failed`, `cloud_saved/failed`, `cloud_loaded/failed`, `review_requested/failed`, `achievement_unlocked`.
- **API:**

```gdscript
PlayServicesManager.sign_in()
PlayServicesManager.is_signed_in() -> bool
PlayServicesManager.cloud_save()        # -> cloud_saved (mock grava snapshot JSON)
PlayServicesManager.cloud_load()        # -> cloud_loaded; chamado auto pós-reinstall se save local vazio
PlayServicesManager.request_review_after_run(first_clears:int)  # só se >=3 e cooldown OK
PlayServicesManager.unlock_achievement(local_id:String)
PlayServicesManager.submit_leaderboard_score(kind:String, score:int)  # endless / stars
```

- **Review cooldown:** `can_request_review()` barra `review_cooldown 90 s` + `GameSave.data.last_review_ts` com janela 3 dias (`3*86400 s`). Nativo: `GodotInAppReview.requestReview()`; mock: loga.

Integração nativa (quando plugin instalado) já mapeada nos comentários do arquivo — trocar os `print` por chamadas `PlayGameServices.*` sem mudar interface.

### 2.3 Save — nuvem `<50 KB` (`scripts/save_data.gd`, `SAVE_SCHEMA_VERSION := 3` mantido)

Campos novos (sem bump, com defaults e `_sanitize_data()`):

```gdscript
"play_signed_in": false,
"last_review_ts": 0,
"review_requests": 0,
```

Constante no topo:

```gdscript
const CLOUD_SNAPSHOT_KEYS: Array = ["schema_version","coins","hard_currency","remove_ads","phase_stars","best_times","achievements","inventory","owned_items","pet_skins","equipped_character","xp","daily_streak","max_streak","metrics","endless_best","endless_unlocked"]
```

**`get_cloud_snapshot() -> Dictionary`** — envelope:

```json
{"v":1,"ts": 171561...,"schema_version":3, "coins":..., "phase_stars":[...], ...}
```

- Clona só chaves limitadas (não leva `ad_counters`, flags locais).
- **Enforce `<50 KB`:** `JSON.stringify(snap).length()`; se >50*1024 descarta `metrics.event_counts`, se ainda >50 KB esvazia `metrics` para `{"first_clears": N}`; se ainda >50 KB retorna `{}` e `push_warning`, não sobe snapshot corrompido.

**`apply_cloud_snapshot(snap:Dictionary) -> bool`** — merge conservador (reinstall-safe):

- Rejeita `v !=1` ou parse falho.
- Se `remote_total_stars < local_total_stars` e `remove_ads==false` **e** `coins>40`, recusa sobrescrever (evita downgrade de progresso local maior).
- `phase_stars`: `max` por fase; `coins/hard_currency/xp/endless_best`: `max`; `remove_ads`/`endless_unlocked`: `OR`; `inventory/owned_items/pet_skins/achievements`: **union**; `equipped_character`: só se contido; `best_times`: `min`; `metrics.first_clears/sessions/...`: `max` + `event_counts` union por `max`.

Persistido via `user://cloud_snapshot.mock.json` no mock; nativo usará `snapshotSave("corre_pro_ponto", payload, desc)`. `_try_auto_cloud_load()` no `PlayServicesManager._ready()` restaura automaticamente quando `local_stars <=40` (save virgem pós-`pm clear`).

Teste de restauração (aceite):

```bash
# 1) Jogue 2 fases, compre remove_ads mock, verifique save
# 2) Simule reinstall:
adb shell pm clear com.arena.correponto   # ou rm user://corre_pro_ponto.json no editor
# 3) Reabra o jogo → PlayServicesManager detecta cloud_snapshot.mock.json e chama cloud_load()
# 4) Verifique: remove_ads=true, phase_stars restauradas, HUD loja mostra "✓ SEM ANÚNCIOS"
python -c "import json; d=json.load(open('/tmp/cloud.json')); print(len(json.dumps(d)), d.get('remove_ads'))"
# tamanho deve ser <51200
```

### 2.4 Jogo — `scripts/game_3d.gd`

- `_ready()` agora chama `_setup_play_services()` após `_setup_ads_billing()`.
- Novos métodos:

```gdscript
_setup_play_services()     # conecta sinais PlayServicesManager
_on_play_signed_in()       # feedback "PLAY GAMES • nuvem ativo"
_on_play_cloud_saved()     # log silencioso
_on_play_cloud_loaded(_snap)
_on_play_review_requested()
_push_play_progress()      # cloud_save() + submit_leaderboard_score("stars"/"endless") + unlock_achievement() para cada conquista/badges
_maybe_request_review()    # request_review_after_run(metrics.first_clears) se >=3
```

- `_finish_run()` — ambos os ramos (`endless` e `normal`) agora fazem:

```gdscript
GameSave.flush()
_push_play_progress()
_maybe_request_review()
run_mode = "results" ...
```

`_push_play_progress` é best-effort: se nativo ausente, salva snapshot mock; leaderboards/achievements são mapeados em `ACHIEVEMENT_MAP` dentro do manager (`busao`, `enchente`, `dog`, `busao50`, `combo15`, `sem_arranhao`, `capitulo1`, `maratonista` → `CgkAchievement*`).

---

## 3. Data Safety / Play Console (sem mudança vs Lotes 11+12, mantido)

- Ads SDK coleta **Advertising ID** (transit, encrypted, não deletável via app) — declarado.
- Billing/Saved Games não coletam dados adicionais do jogo fora do snapshot do usuário (já descrito no doc anterior).
- `com.google.android.gms.permission.AD_ID` só entra quando plugin AdMob instalado; mock não adiciona.

---

## 4. Como validar (CI local)

```bash
python tools/validate_project.py          # PRE-FLIGHT OK
python - << 'PY'
import json, pathlib
snap=json.loads(pathlib.Path("user_cloud_mock.json").read_text()) if pathlib.Path("user_cloud_mock.json").exists() else {"v":1}
# Use GameSave.get_cloud_snapshot() no editor para gerar real
PY
./tools/make_keystore.sh /tmp/test.keystore && keytool -list -v -keystore /tmp/test.keystore | grep -E "4096|10000"
# Exportar AAB no editor e:
jarsigner -verify -verbose -certs build/corre-pro-ponto.aab
```

No editor sem plugins, `PlayServicesManager` roda em mock; com plugins instalados (Play Console), a mesma interface delega para singletons nativos sem mudar `game_3d.gd`.

---

## 5. Arquivos tocados neste lote

- **novos:** `scripts/play_services_manager.gd`, `tools/make_keystore.sh`, `docs/RELEASE_LOTE13.md`
- **alterados:** `project.godot` (+`PlayServicesManager` autoload), `scripts/save_data.gd` (3 campos + snapshot `<50KB` sem bump), `scripts/game_3d.gd` (Play Games wiring + cloud/review hooks), `export_presets.cfg` (AAB + keystore fora do repo + comentários de plugins)

Validado: `python tools/validate_project.py → PRE-FLIGHT OK (2026-09-19)`, AAB mock (sem SDK) gera sem erro no editor.
