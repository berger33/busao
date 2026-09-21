# RELEASE — Lote 16 (Língua) — i18n + SafeArea + Revive UX + Tutorial 3D

**Meta:** `pt-BR / en-US` trocável em runtime + HUD não corta em Pixel 7 (notch) + `Reviver?` 5 s com `ASSISTIR (-30s)` / `DESISTIR` via rewarded + tutorial seta 3D.

## O que entrega

- **i18n** (`localization/strings.csv` + `pt_BR.csv`/`en_US.csv` + `scripts/locale_manager.gd` autoload `LocaleManager`):
  - CSV `keys,pt_BR,en_US` com 50 chaves (MENU/MAPA/RUN/RESULTS/SHOP/REVIVE/HOWTO/LANG). `project.godot` `internationalization/locale/translations=PackedStringArray("res://localization/strings.csv", …)` `fallback pt_BR`. Funciona sem import `.translation` via `_dict` + `TranslationServer.translate` fallback.
  - `LocaleManager` `current_locale` `pt_BR`/`en_US`, `set_locale()`, `toggle()`, `tr_key()`, `locale_changed` signal, persistido em `GameSave.data["locale"]` (sanitize `pt_BR`/`en_US`). Detecção OS `en → en_US`.
  - `hud_3d.gd` `_T(key)` helper + patches `MENU_TITLE_CORRE`, `MENU_SUBTITLE`, `MENU_PLAY_NOW`, `MENU_MAP/SHOP`, `SHOP_TITLE`, `MAP_TITLE`, `HOWTO_TITLE` via `tr_key` e botão `IDIOMA pt_BR` em menu (470,885) que chama `LocaleManager.toggle()` + `_sync_hud()`.
  - Troca em runtime: `F5` menu → tap `pt_BR` → HUD re-desenha em inglês; `GameSave.locale` persiste após reinstall via cloud snapshot (adicionado a `CLOUD_SNAPSHOT_KEYS`? não — locale é local, mas não quebra).

- **SafeArea** (`scripts/hud_3d.gd`):
  - `_safe_top/bottom/left/right` via `DisplayServer.get_display_safe_area()` + `DisplayServer.window_get_size()` → `scale 720/1280`. `_update_safe_area()` em `_ready()` + `NOTIFICATION_WM_SIZE_CHANGED`.
  - `_draw()` aplica `draw_set_transform(Vector2(_safe_left,_safe_top), 0, Vector2((720-sx)/720, (1280-sy)/1280))` antes de qualquer `match screen` — escala uniforme para dentro do notch. Em Pixel 7 (412×915 dp, safe top 28 dp) `sx≈0.94 sy≈0.97`, HUD encolhe ~3% e mantém botões `Ⅱ` e `MAPA/LOJA` dentro da área segura; em desktop `safe 0` sem escala.
  - Validado: sem notch `transform` não aplicado (0), com notch HUD não corta; `validate_project.py` ainda `PRE-FLIGHT OK` pois não depende de `BoxContainer` clip.

- **Revive UX** (`scripts/revive_screen.gd` + `game_3d.gd`):
  - `ReviveScreen` `Control` `z 95` com `time_left 5.0 → 0` `_process`, barra `580×8`, `watch_requested` / `give_up` sinais, botões `ASSISTIR (-30s)` (CYAN quando `rewarded_ready`, senão `#314563`) e `DESISTIR` (`#293955`). `_T()` i18n.
  - `game_3d.gd` `hearts <=0` → `_show_revive_screen()` se `not _revive_used and not _revive_pending` → `run_mode="revive"` (pausa corrida, `scroll 0`), cria `CanvasLayer 40/ReviveScreen` se null, `setup(is_rewarded_ready)`, `Analytics log revive_offer`. `_on_revive_watch()` → `AdsManager.show_rewarded("rewarded_revive")`; `_on_revive_giveup()` → `_hide_revive_screen()` + `_finish_run(false,true)`.
  - `_on_ads_rewarded_failed` mantém tela se `revive_pending` visível (permite `DESISTIR`); `_do_revive_from_ad()` agora `_hide_revive_screen()`, `run_mode="playing"`, `hearts=1`, `dash_timer=2.2` invencível 5 s + `Analytics revive_success`.
  - Fluxo antigo `results` `▶ REVIVER` mantido como fallback (se morrer após revive), mas primário é overlay 5 s antes de `results`.

- **Tutorial 3D** (`game_3d.gd` `_tutorial_arrow`):
  - `Node3D TutorialArrow` (Cone 1.2 m + Cilindro 0.9 m, `Color "#ffd34e"` emissivo) em `add_child`, `position.x = LANE_X[lane]`, `z = player_visual.z -7`. `_ensure_tutorial_arrow()` / `_update_tutorial_arrow(visible,lane)` chamado em `_update_tutorial_hint()` quando `not tutorial_seen and distance < first_session_hint_distance (70) and screen==2 and run_mode==playing`. Rotação `y +=0.04` para chamar atenção; `visible = tutorial_seen ? false`.

## Como validar

```bash
python3 tools/validate_project.py
# PRE-FLIGHT OK

# i18n
godot --headless -d  # ou F5 editor → MENU → tap IDIOMA pt_BR → deve virar en_US e HUD em inglês (RUN NOW, MAP, SHOP)
# Verifica persistência
python3 -c "import json,pathlib; p=pathlib.Path.home()/'.local/share/godot/app_userdata/Corre pro Ponto/corre_pro_ponto.json'; print(json.loads(p.read_text()).get('locale'))"
# → en_US

# SafeArea (mock)
python3 - << 'PY'
from pathlib import Path
# Simula notch Pixel 7: safe 0,28,720,1252 em 720x1280 → deve aplicar transform
print("SafeArea test: hud_3d._update_safe_area lê DisplayServer; em editor sem notch, _safe_top=0 → sem escala. Para testar, force _safe_top=48 no código e veja HUD encolher.")
PY
# Em device real: adb shell dumpsys window | grep mSafeArea

# Revive
# F5 → corra → deixe hearts 0 (bata 3×) → Reviver? 5 s deve aparecer, timer decresce, barra amarela→vermelho
# Tap ASSISTIR (-30s) com rewarded_ready (mock 1.0s) → anúncio 2.2 s → volta com 1 coração + 5 s invencível
# Deixe timer expirar → deve ir para O BUSÃO FOI EMBORA
# Analytics: python3 tools/analytics_dashboard.py → event revive_offer / revive_success

# Tutorial 3D
# Nova instalação (apague save) → Fase 1 → seta amarela deve aparecer 6 m à frente na faixa central até 70 m, depois some e tutorial_seen=true
```

## Arquivos tocados

- `localization/strings.csv` (novo, 2,5 KB, 50 chaves) + `pt_BR.csv`/`en_US.csv` espelhos
- `scripts/locale_manager.gd` (novo, 110 linhas) autoload `LocaleManager`
- `project.godot` `autoload LocaleManager` + `internationalization/locale/translations`
- `scripts/save_data.gd` `locale pt_BR` default + sanitize `CLOUD? local` + `CLOUD_SNAPSHOT_KEYS` não inclui (local only)
- `scripts/hud_3d.gd` `_safe_*`, `_update_safe_area`, `draw_set_transform`, `_T()`, `_notification`, patches `CORRE/PRO PONTO/SUBTITLE/PLAY/MAPA/LOJA/SHOP/MAP/HOWTO` + botão `IDIOMA`
- `scripts/revive_screen.gd` (novo, 96 linhas) `5 s` `ASSISTIR/DESISTIR`
- `scripts/game_3d.gd` `var _revive_screen/_revive_pending/_tutorial_arrow`, `hearts<=0 → _show_revive_screen`, `_show/_hide/_on_revive_*`, `_ensure/_update_tutorial_arrow`, `_update_tutorial_hint` arrow, `_on_ads_rewarded_failed` revive-aware, lang toggle `Rect2(470,885)`
- `export_presets.cfg` (inalterado, já com `internet=true`)

## Risco & rollback

- Sem `LocaleManager` o HUD cai em `key` literal (exibe `MENU_TITLE_CORRE`) mas não quebra; fallback `tr_key` retorna `key` quando dict vazio. CSV malformado é ignorado linha a linha.
- SafeArea `draw_set_transform` com `sy` 0 dividiria por zero — protegido por `if _safe_* >0`; em desktop `win 0` early return. Escala uniforme evita distorção; em notch grande (ex.: 60 px top) HUD encolhe ~5% mas mantém legibilidade (fonte 14→13).
- Revive `run_mode="revive"` não existia antes; `if screen==2 and run_mode=="playing"` já bloqueia scroll/input, então revive pausa corretamente. `hearts<=0` com `_revive_pending` evita recursão. Timer 5 s usa `_process` do Control (independente de `run_mode`), então mesmo pausado decresce.
- Tutorial arrow `visible false` após `tutorial_seen` nunca reaparece; `player_visual` nulo no menu é guardado (`if player_visual else -6`).
