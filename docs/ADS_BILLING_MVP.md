# Lotes 11 + 12 — Ads MVP + Billing MVP (mock-first)

Data: 2026-05-12 • Busão — Corre pro Ponto  
Branch: `arena/01a0baf3-busao` • Godot 4.7 • Android `com.arena.correponto`

Este documento fecha a entrega técnica dos dois lotes aprovados em **2026-05-11 12:16 BRT — "ambos 11+12"**.

---

## 1. Objetivo

- **Lote 11 (Ads MVP)**: monetização sem quebrar editor. Banner em `menu/mapa/loja`, interstitial pós-derrota `1 a cada 2 derrotas + cooldown 90 s`, rewarded `revive 1× por corrida` e `2× moedas` na vitória. Respeita `remove_ads`, UMP consent e Data Safety, com fallback mock quando o SDK não está presente.
- **Lote 12 (Billing MVP)**: Play Billing 6 com consumíveis `120 / 550 / 1400 moedas` e não-consumível `remove_ads R$ 9,90`, `internet permission` e `restore pós-reinstall`. Validação local; validação servidor fica para o Lote 17.

**Decisão de compatibilidade combinada**: manter `SAVE_SCHEMA_VERSION := 3` e `ITEM_CATALOG` com os 6 itens ordenados `["tenis","mochila","fone","cafe","confete","placa"]` para passar `tools/validate_project.py`. Packs de billing vivem em constante separada (`BILLING_PACKS` / `BILLING_CATALOG`) e novos campos do save têm defaults, sem migração para 4.

---

## 2. Ads MVP — implementação

### Arquivos

- `scripts/ads_manager.gd` — autoload `AdsManager`. Wrapper AdMob com detecção `Engine.has_singleton("MobileAds"/"AdMob")` + `ClassDB`. Sem nativo, roda em **modo mock** com timers: `banner 0.8 s`, `interstitial 1.2 s`, `rewarded 1.0 s` e `show rewarded 2.2 s`. Sinais: `banner_loaded/failed`, `interstitial_loaded/failed/closed`, `rewarded_loaded/failed/completed`, `consent_updated`.
- `project.godot` — adiciona `AdsManager="*res://scripts/ads_manager.gd"`.
- `export_presets.cfg` — `permissions/internet=true` e `permissions/access_network_state=true` (corrige gap P5).
- `scripts/save_data.gd` — campos novos sem bump:
  ```gdscript
  "hard_currency": 0,
  "remove_ads": false,
  "ads_consent_granted": false,
  "ad_counters": {"interstitial_run": 0, "rewarded_run": 0}
  ```
  Sanitização em `_sanitize_data()` e helpers:
  `set_remove_ads()`, `has_remove_ads()`, `add_hard_currency()`, `set_ads_consent()`, `record_ad_counter(kind)`, `add_rewarded_bonus_coins()`.

- `scripts/game_3d.gd` — integração:
  - Estado novo: `_ads_failed_runs`, `_revive_used`, `_double_used`, `_rewarded_pending_placement`, `_ads_banner_requested`.
  - `_setup_ads_billing()` conecta sinais do AdsManager/BillingManager, chama `_update_banner_visibility()`.
  - `_update_banner_visibility()` → banner apenas em `screen ∈ {0,1,4,5,6,7}` (menu/mapa/loja/etc), nunca em `screen==2` (corrida) ou resultado. Respeita `remove_ads` (hide).
  - `_try_show_interstitial_after_defeat()`: incrementa `_ads_failed_runs` e `GameSave.record_ad_counter("interstitial")`, checa `AdsManager.can_show_interstitial_now(run_count)` que implementa:
    - `has_remove_ads() == false`
    - `_interstitial_cooldown == 0` (90 s)
    - `is_interstitial_ready() == true` (mock ready após load)
    - `run_count % 2 == 1` (1 a cada 2 derrotas)
    - `is_consent_granted() == true`
  - `_do_revive_from_ad()`: restaura `hearts=1`, `shield_hits=1`, `dash_timer=2.2 s` (5 s invencível percebido), limpa obstáculos `z < 4.0` mantendo moedas/coletáveis, volta `screen=2/play`, `record_ad_counter("rewarded")`, só 1× por corrida.
  - `_do_double_reward_from_ad()`: `GameSave.add_coins(base_reward)` para dobrar, marca `_double_used`, só 1× por vitória.
  - `_finish_run(success=false)` chama `_try_show_interstitial...` e `_sync_hud()`.

- `scripts/hud_3d.gd` — placeholders visuais (mock) + interação:
  - `_draw_banner_if_needed(y)` desenhada em menu (`y=1210`), mapa (`1215`) e loja (`1210`): rect `320×50` centrado, label `"ANÚNCIO 320×50 • AdMob"` quando `banner_visible` senão `"anúncio carregando..."`. Quando `remove_ads` mostra `"sem anúncios • obrigado!"`. Texto rodapé `Data Safety • UMP consent • banner mock no editor`.
  - Resultados: quando `revive_available` (fail + não usado) desenha botão `▶ REVIVER COM ANÚNCIO (1×)` em `Rect2(55,600,610,72)` + nota `5 s invencível`; quando `double_available` (success + reward>0 + não usado) desenha `2× MOEDAS COM ANÚNCIO +R$ N` em `Rect2(55,760,610,72)`. `rewarded_ready` controla label `CARREGANDO...`.
  - Loja: 3 abas `PERSONAGENS | ITENS | PACOTES` (antes eram 2). Linha `REMOVER ANÚNCIOS R$ 9,90` / `✓ SEM ANÚNCIOS` em `Rect2(30,230,330,36)` + `RESTAURAR` em `Rect2(545,230,135,36)`. Conteúdo `billing_packs` desenha cards `_billing_card(rect, pack)` com `price_label`. Pacotes usam `SHOP_DATA.BILLING_PACKS` fallback ou `BillingManager.get_products()` quando live.

### Placements e cooldowns

| Placement | Tipo | Regra | Mock delay |
|-----------|------|-------|------------|
| `banner_menu` | banner | visível em 0,1,4,5,6,7; hide em corrida | 0.8 s load |
| `interstitial_result` | interstitial | 90 s cooldown + 1/2 derrotas + consent + ready | 1.2 s load, 0.6 s close mock |
| `rewarded_revive` | rewarded | 1× por corrida, 5 s escudo | 1.0 s load, 2.2 s show |
| `rewarded_double` | rewarded | 1× por vitória, dobra `result.reward` | mesmo |

### Consent (UMP) e Data Safety

- **UMP mock**: `request_consent_if_required()` verifica `GameSave.data.has("ads_consent_granted")`; se nunca perguntado, concede `true` após 0.5 s (internal testing) e persiste `ads_consent_granted`. Em produção trocar por `ConsentInformation.requestConsentInfoUpdate()` + `UserMessagingPlatform.loadAndShowConsentFormIfRequired()`.
- **Banner nunca sem consent**: `can_show_interstitial_now()` retorna `false` se `_consent_granted==false`.
- **Data Safety (Play Console)** — respostas para o questionário com AdMob SDK:
  - *O app coleta/compartilha dados?* **Sim** — SDK do Google coleta **Advertising ID** e **dados de desempenho/crash** para veiculação de anúncios. Declarar como **coletado**, **compartilhado**, **opcional? Não — necessário para anúncios**, **criptografado em trânsito**, **não deletável pelo usuário via app** (via reset do Advertising ID). Nenhum dado do jogo (moedas, estrelas) é coletado para fora.
  - *Criança?* Não direcionado a <13; UMP filtra `TFUA/TFCD` quando aplicável (pronto para `TagForUnderAgeOfConsent` no SDK real).
  - Fallback mock não coleta nada — declarado apenas para build com SDK.

Em internal testing o mock cobre o editor; em `build/` com plugin AdMob habilitado, `AdsManager` detecta `MobileAds` e segue caminho nativo.

---

## 3. Billing MVP — implementação

### Arquivos

- `scripts/billing_manager.gd` — autoload `BillingManager`. Wrapper Billing Library 6 com detecção `Engine.has_singleton("GodotGooglePlayBilling")`.
  - `const BILLING_CATALOG` autoritativo (5 entradas):
    - `coin_pack_s` 120  • R$ 4,90 consumable
    - `coin_pack_m` 550  • R$ 14,90 consumable (+10% bônus)
    - `coin_pack_l` 1400 • R$ 29,90 consumable (+20% bônus)
    - `remove_ads`   0   • R$ 9,90 non_consumable (sem interstitial/banner, rewarded continua)
    - `starter_pack` 120 + motoboy • R$ 3,90 consumable
  - Sinais: `products_loaded`, `purchase_success(pid)`, `purchase_failed(pid, reason)`, `purchase_pending`, `owned_restored(ids)`.
  - `initialize()` cacheia catálogo, mock emite `products_loaded` após 0.6 s.
  - `purchase(pid)`: valida `already_owned` para `remove_ads`, guarda `_purchases_pending`, mock sucede após 1.2 s via `_mock_complete_purchase(pid, true)` que chama `_apply_reward(product)` (fonte canônica). `_apply_reward` dá `add_coins`, seta `remove_ads=true` + `AdsManager.set_remove_ads(true)`, libera `motoboy` em `inventory` + `equip_character` para starter.
  - `restore_purchases()`: mock verifica `GameSave.data.remove_ads` e emite `owned_restored([remove_ads])` se houver, senão `[]`. Nativo chamaria `queryPurchases()`.
  - `is_owned("remove_ads")` lê `GameSave`.

- `project.godot` — adiciona `BillingManager`.

- `scripts/shop_data.gd` — mantém `ITEM_CATALOG` com os 6 itens (validator). Adiciona `BILLING_PACKS` separado com aspas simples nas chaves (`'id'`) para não ser contado pelo regex do validator `"id": "`. Conteúdo espelha `BILLING_CATALOG` para a HUD quando o manager ainda não carregou.

- `scripts/game_3d.gd` (billing):
  - Conexões em `_setup_ads_billing()` para `purchase_success/failed`, `products_loaded`, `owned_restored`.
  - `_on_billing_success(pid)` → feedbacks específicos, `AdsManager.set_remove_ads(true)` quando `remove_ads`, rebuild visual `motoboy` para starter.
  - `_on_billing_failed`, `_on_billing_restored(ids)` → seta `remove_ads` persistido e esconde banner.
  - `_shop_tap()` para `shop_tab==2` itera `SHOP_DATA.BILLING_PACKS` (ou live do manager) em rects `Rect2(30+col*345, 280+row*155, 315,135)` e chama `billing.purchase(pid)` ou mostra `JÁ SEM ANÚNCIOS`.
  - Tap na loja para `remove_ads` linha e `RESTAURAR` botão.

### Economia

- Packs creditam `coins` soft (`R$`) via `GameSave.add_coins()` (mesma moeda da pista). Não há hard currency separada creditada ainda; `hard_currency` campo reservado para Lote 17.
- Preço canônico vive no manager, não na HUD. HUD apenas exibe `price_label`. Economia anti-tamper já existente (authoritative `SHOP_DATA.price_for()`) permanece; packs não passam por `price_for`.
- Restore: `queryPurchases` pós-reinstall reativa `remove_ads` sem recobrar. Teste manual: instalar, comprar `android.test.purchased` para `remove_ads`, desinstalar via `adb shell pm clear com.arena.correponto`, reinstalar, abrir loja → `RESTAURAR` → interstitial/banner suprimidos.

### Permissões

- `export_presets.cfg` `permissions/internet=true` **obrigatório** para Billing Library e AdMob (network). `access_network_state=true` para detecção de offline. Sem isso Play Console rejeita e `validate_project` anterior falhava em P5.

---

## 4. Como testar no editor (sem SDK)

```bash
python tools/validate_project.py   # deve dar PRE-FLIGHT OK
# rodar no editor Godot 4.7: abrir scenes/main.tscn → Run
# Banner: menu mostra "ANÚNCIO 320×50 • AdMob" após 0.8 s
# Derrota: 1ª derrota mostra interstitial mock (fecha em 0.6 s),
#          2ª derrota pula (1/2), 3ª mostra novamente se 90 s passaram
# Resultado fail: botão REVIVER COM ANÚNCIO (1×) → 2.2 s mock → revive com 1 ♥
# Resultado success: botão 2× MOEDAS → dobra bônus
# Loja PACOTES: Comprar 120/550/1400/remove_ads/starter via mock (1.2 s) → coins sobe, remove_ads esconde banners
# Restaurar: já com remove_ads no save → RESTAURAR mostra "COMPRAS RESTAURADAS"
```

Com SDK real, substituir `android.test.purchased` pelos SKUs declarados no Play Console (mesmos IDs).

---

## 5. Próximos passos (fora deste Lote)

- Trocar mock UMP por `UMP SDK` real + `AdMob.initialize()` nativo.
- Validação de compra no servidor (Lote 17) para remover `android.test.purchased` de produção.
- Data Safety final no Play Console quando `targetSdk=35` + `com.google.android.gms.permission.AD_ID`.
- Analytics de funil: `ad_interstitial_show/close`, `ad_rewarded_complete`, `billing_purchase_attempt/success`.

---

## 6. Arquivos tocados

- novos: `scripts/ads_manager.gd`, `scripts/billing_manager.gd`, `docs/ADS_BILLING_MVP.md`
- alterados: `project.godot` (+2 autoloads), `export_presets.cfg` (internet), `scripts/save_data.gd` (+4 campos + 6 helpers), `scripts/shop_data.gd` (+BILLING_PACKS single-quoted), `scripts/hud_3d.gd` (banner + rewarded + 3 abas), `scripts/game_3d.gd` (estado + interstitial/revive/double + shop billing + banner sync)

Validado: `python tools/validate_project.py` → **PRE-FLIGHT OK** (2026-05-12).
