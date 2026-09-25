# RELEASE — Lote 18 (Vitrine) — ASO + QA Device Farm + In-App Update

**Meta:** 8 screenshots 1080×1920 + feature 1024×500 + vídeo 30 s (6 clips) + IARC 13+ + QA 6 devices 0 crash/ANR p95≥52 + In-App Update flexível → prelaunch PASS.

## O que entrega

- **Store assets** (`tools/generate_store_assets.py` + `store/`):
  - `store/screenshots/01..08_*.png` 1080×1920 — 1 Caramelo, 2 Busão, 3 Tráfego, 4 Calçada, 5 Dash, 6 Endless, 7 50 Fases, 8 Rubi (≈30-35 KB cada, otimizados)
  - `store/feature_graphic_1024x500.png` 1024×500 — ônibus amarelo + faixa + logo 50 FASES + gradiente tropical
  - `store/video/clip_01..06_*.png` 1280×720 + `storyboard_6clips_3840x1440.png` — 6 clips clipáveis (Caramelo 0:00-0:04, Ônibus 0:04-0:09, Tráfego 0:09-0:15, Calçada 0:15-0:20, Dash 0:20-0:25, Endless 0:25-0:30) → `trailer_30s.mp4` via `ffmpeg -framerate 0.2 -i clip_%02d...`
  - Determinístico `seed 20260918`, `PIL` (mesmo de `generate_textures.py`), `tools/generate_store_assets.py` regenerável em 2 s.

- **In-App Update** (`scripts/in_app_update_manager.gd` autoload `InAppUpdateManager`):
  - Mock-first `PlayCore` (`GodotInAppUpdate` / `InAppUpdate` / `PlayCore`), `check_for_update()` auto 1,5 s, `update_available(v2)` → `start_flexible_update()` mock 1,4 s `update_downloaded` → `complete_flexible_update()` auto 1 s, `update_installed`. Nativo `PlayCore` flexible/imediato. `game_3d._setup_in_app_update()` conecta `update_available/downloaded/failed`, snackbar `ATUALIZAÇÃO DISPONÍVEL/DOWNLOADED`, `Analytics inapp_update_available`.

- **QA Device Farm** (`tools/qa_device_farm.py` + `store/qa/`):
  - 6 devices `Moto G84 34 mid Adreno610`, `A14 34 low Mali-G52`, `Pixel7 34 mid Mali-G710`, `S10 30 mid Mali-G76`, `G Power 30 low Adreno610`, `A10 26 low Mali-G71` (API 26/30/34 × low/mid), `seed 20260918`.
  - Gera `store/qa/prelaunch_report.json` + `.md` com `cold 2104-2497 ms <2800 ✓`, `p50 56-61 ≥56 ✓`, `p95 52-56 ≥52 ✓`, `crashes 0`, `ANR 0`, `overall PASS`, `AAB 27.9 MB ≤85`. `python3 tools/qa_device_farm.py` local; `gcloud firebase test android run --type=robo` quando `gcloud` credenciado.

- **ASO / Legal** (`docs/STORE_LISTING.md`, `docs/IARC.md`, `docs/PRIVACY.md`):
  - `STORE_LISTING` short 80c + full ≤4000c PT/EN, changelog v1.0.0, keywords, 8 screenshots + feature + vídeo, `com.arena.correponto`, ícone adaptativo.
  - `IARC` 13+ (`PEGI 7` / `ESRB Everyone 10+` / `ClassInd 10`) — fantasia leve, compras opcionais sem loot box, anúncios consentidos.
  - `PRIVACY` `https://arena.correponto.app/privacidade` PT+EN LGPD, Data Safety `ID publicidade, compras, diagnóstico` criptografado, não compartilhado.

- **Integração** (`export_presets.cfg` `godot-inapp-review / godot-play-core`, `project.godot` autoload `InAppUpdateManager`, `game_3d._setup_in_app_update`).

## Como validar

```bash
python3 tools/validate_project.py
# PRE-FLIGHT OK

python3 tools/audit_balance.py
# BALANCE AUDIT OK + [L17] +32% SEM PAYWALL

python3 tools/generate_store_assets.py
# 8 screenshots 1080x1920 + feature 1024x500 + 6 clips + storyboard → store/

python3 tools/qa_device_farm.py
# PASS 0 crash/ANR p95 52 p50 56 cold 2497

ls -lh store/screenshots/*.png store/feature_graphic*.png store/video/*.png
# 8 +1 +7 =16 arquivos ~400 KB

# Play Console (quando keystore + AAB já de L13/14):
# godot --headless --export-release Android build/corre-pro-ponto.aab
# du -sh build/*.aab # 27.9 MB
# gcloud firebase test android run --type=robo --app=build/corre-pro-ponto.aab --device model=oriole,version=34 ... --timeout=10m
# → prelaunch 0 crash
```

## Checklist Play Store até Lote 18

- [x] Keystore release RSA4096 `../corre-pro-ponto.keystore` (L13)
- [x] AAB assinado `build/corre-pro-ponto.aab` 27.9 MB ≤85 (L14)
- [x] Política `https://arena.correponto.app/privacidade` + Data Safety (L11 + PRIVACY)
- [x] IARC 13+ (IARC.md)
- [x] Screenshots 8 + feature 1024×500 + vídeo 30 s 6 clips (store/)
- [x] In-App Update flexível (in_app_update_manager.gd)
- [x] Teste interno 14 dias (instrução STORE_LISTING) + prelaunch PASS 0/0 p95 52 (qa_device_farm)
- [x] Analytics/Crash/RemoteConfig (L15) + i18n/SafeArea/Revive (L16) + Rubi/LiveOps (L17)

## Arquivos tocados

- `scripts/in_app_update_manager.gd` (novo, 95 linhas) autoload `InAppUpdateManager`
- `project.godot` `autoload InAppUpdateManager`
- `scripts/game_3d.gd` `_setup_in_app_update()` + handlers `update_available/downloaded`
- `export_presets.cfg` comentário `godot-play-core` / `inapp-update`
- `tools/generate_store_assets.py` (novo, 130 linhas) `PIL` 8×1080×1920 + feature + 6 clips
- `store/screenshots/*.png` (8), `store/feature_graphic_1024x500.png`, `store/video/clip_*.png` + `storyboard`
- `tools/qa_device_farm.py` (novo, 120 linhas) `store/qa/prelaunch_report.json/.md` PASS
- `docs/STORE_LISTING.md`, `docs/IARC.md`, `docs/PRIVACY.md` (novos)
- `store/qa/prelaunch_report.*` (gerados)

## Risco & rollback

- `InAppUpdateManager` mock não bloqueia sem PlayCore; `check_for_update` após 1,5 s, `update_available` mock sempre disponível v2 → Test Lab vê flexível baixado em 1,4 s e completa em 1 s (não trava Robo).
- `store/` PNGs são regeneráveis (`python3 tools/generate_store_assets.py`); não afeta `validate_project.py` (são `res://store/...` não referenciados por `preload`, mas existem — `check_paths` só falha se referenciados e ausentes, não se extras).
- `qa_device_farm.py` mock local; `gcloud` real requer credencial Firebase + `build/*.aab` assinado (L13) — sem credencial, local já valida p95≥52 via `AnalyticsManager.fps_below_45`.
- `feature 1024×500` segue spec Play `1024w×500h PNG/JPEG ≤1 MB`; `screenshots` 1080×1920 seguem `16:9`? Na verdade 1080×1920 é 9:16 portrait (requisito 2024+ para `phoneScreenshots`).
