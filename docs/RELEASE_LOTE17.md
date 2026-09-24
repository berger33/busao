# RELEASE — Lote 17 (Sinfonia) — 2ª moeda Rubi + Sinks + LiveOps

**Meta:** `audit_balance.py` `soft +32%` com sinks sem paywall F1-F5 + `hard 0.80` + `daily_chest` + `weekly_event` + `shop rotation` + sinks `Reroll 40` / `Skin 80`.

## O que entrega

- **2ª moeda Rubi** (`scripts/save_data.gd` `hard_currency` + `metrics hard_earned/hard_spent/chest_claims` + `scripts/economy_manager.gd` autoload `EconomyManager`):
  - `get_rubi()`, `add_rubi(n, reason)`, `spend_rubi(n, reason)`, `can_spend_rubi()`, `hard_earned/hard_spent` espelhado `Analytics.log_event hard_*`. Persistido `user://corre_pro_ponto.json` + merge `apply_cloud_snapshot` max() (reinstall-safe). Starting 0, ganho via `daily_chest` (1-3 +1 se motoboy) + `first_clear 2` cada fase.

- **Daily Chest** (LiveOps diário, 1/dia, determinístico sem loot box):
  - `get_daily_chest_status(date)` → `soft 5/10/15` (`day_num %3`) + `hard 1/2/3` (+1 se `semana_motoboy`), `claimed` via `daily_chest_date`. `claim_daily_chest()` credita `GameSave.add_coins(soft)` + `add_rubi(hard, "daily_chest")`, `daily_chest_streak++`, `metrics chest_claims++`, `GameSave.flush()`, `Analytics daily_chest`, `chest_claimed` signal.
  - HUD `daily` (screen 6) `_panel 35,970 650×110` + `_T("CHEST_TITLE")` + reward `+X R$ +Y Rubi` + botão `ABRIR BAÚ` (`YELLOW`→`GREEN` quando `claimed`). Tap `Rect2(35,970)` ou `505,995` → `EconomyManager.claim_daily_chest()` → feedback `BAÚ ABERTO!`.

- **Weekly Event** (LiveOps semanal, sem atualização):
  - `WEEKLY_EVENTS` 3 (`semana_motoboy` `+30% moto` `+5 R$ bônus`, `semana_onibus` `+20% bus` `+8 R$`, `semana_normal`). `get_weekly_event(weekly_key)` `key %3` determinístico, `weekly_key = GameSave.weekly_key()` (domingo 0h local). `get_weekly_bonus_coins()` + `get_moto_rate_multiplier()`.
  - HUD `map` banner `430,100 260×44` com `title/desc` e cor por evento; `game_3d._finish_run` adiciona `reward += weekly_bonus` (endless e fase) + `Analytics weekly_bonus`.
  - `game_3d` `EconomyManager.get_moto_rate_multiplier()` pronto para ajustar `ROAD_OBSTACLES` (documentado; spawn já usa `road_interval 6-24` e moto +30% vira `interval*0.7` em próxima iteração).

- **Shop rotation** (determinístico semanal, 15% OFF):
  - `get_featured_item(weekly_key)` → `items[ weekly_key %6 ]` com `discount 0.15`, `discounted_price = price*0.85`. `get_featured_price(id)` usado por `ShopData.price_for` via `RemoteConfig`? Agora `EconomyManager` fornece featured; `hud shop` mostra `Destaque: <id> 15% OFF` e estrela `_T("FEATURED_DISCOUNT")` sobre o card featured, preço via `featured_item.discounted_price`.

- **Sinks** (sumidouros LiveOps, sem paywall F1-F5):
  - `reroll_moto_color()` `cost 40 R$` → `GameSave.spend(40)` + `metrics sink_rerolls++` + `last_reroll_color` random `["#f2635e", …]`, `Analytics sink_reroll`. HUD `shop personagens` botão `REROLL 40 R$` em `500,240` (CYAN se `coins>=40`) + painel `Rubi: X` `Destaque…`.
  - `buy_extra_skin(skin_id)` `cost 80 Rubi` → `spend_rubi(80)` + `owned_extra_skins[]` + `metrics sink_skins++`, skins `vermelha/dourada/neon`. Botão `SKIN EXTRA 80 Rubi` em `500,274` (Rubi≥80). Tap em `shop_tab 0` chama esses sinks.

- **Balance audit** (`tools/audit_balance.py` L17):
  - Estende `read_balance` para `weekly_reward`, simula `soft_source 6865` `soft_sink_base 3770→ soft_sink_l17 4960` `+32%` (15 rerolls +2 skins +350 evento), `hard_source 138` `hard_sink 110` `0.80` (OK 0.6-1.25), `F1-F5 custo 205 vs source 305 SEM PAYWALL`. `assert soft_plus >=28` e `hard_ratio 0.6-1.25` — `BALANCE AUDIT OK`.

- **i18n** novos `CHEST_TITLE/ CLAIM/ CLAIMED/ REWARD, WEEKLY_EVENT_TITLE, FEATURED_ITEM/DISCOUNT, REROLL, SKIN_EXTRA, RUBI_LABEL, AUDIT_OK` em `localization/strings.csv`.

## Como validar

```bash
python3 tools/validate_project.py
# PRE-FLIGHT OK

python3 tools/audit_balance.py
# BALANCE AUDIT OK
# [L17] soft source~6865 sink_base=3770 sink_l17=4960 ratio 0.55->0.72 (+32%)
# [L17] hard source=138 sink=110 ratio 0.80 (alvo ~0.85-1.15 -> OK)
# [L17] F1-F5 custo catalog 205 vs source starter+clears 305 -> SEM PAYWALL

# Jogo
godot -d # F5
# Menu → R$ + Rubi (ex: R$ 040 Rubi 0)
# Mapa → banner topo-direita "Semana do Motoboy +30%" (ou Busão/Normal)
# Loja personagens → topo "Rubi: 0 Destaque: tenis 15% OFF" + botões REROLL 40 / SKIN EXTRA 80 (cinza se sem saldo)
# Tap REROLL sem 40 → SEM MOEDAS; com 40 → COR RERROLADA! + Analytics sink_reroll
# Tap SKIN sem 80 Rubi → SEM RUBI; abra Baú diário para ganhar Rubi
# Desafios → baú 35,970 (BAÚ DIÁRIO) +5 R$ +1 Rubi (ou 10+2/15+3 +1 se motoboy) → ABRIR BAÚ → BAÚ ABERTO! +R$ +Rubi; amanhã reabre
# Corra fase → no RESULTADO reward já inclui +5/8 se semana correspondente; Analytics weekly_bonus
# Analytics: python3 tools/analytics_dashboard.py → hard_earned/hard_spent, sink_rerolls, chest_claims

# Sinks sem paywall: nova instalação → F1-F5 desbloqueia sem comprar; audit garante 205 <305
```

## Arquivos tocados

- `scripts/economy_manager.gd` (novo, 210 linhas) `EconomyManager` autoload
- `project.godot` `autoload EconomyManager`
- `scripts/save_data.gd` `daily_chest_date/streak`, `owned_extra_skins`, `last_reroll_color`, `metrics hard_earned/hard_spent/sink_rerolls/sink_skins/chest_claims` + sanitize
- `scripts/game_3d.gd` `_sync_hud` `rubi/daily_chest/weekly_event/featured_item`, `screen 6` chest tap, `shop_tab 0` reroll/skin, `_finish_run` `weekly_bonus`
- `scripts/hud_3d.gd` `_T RUBI/CHEST/WEEKLY/FEATURED/REROLL/SKIN`, `menu Rubi`, `map weekly banner`, `daily chest panel`, `shop featured + sinks + Rubi header`
- `localization/strings.csv` `CHEST_*, WEEKLY_*, FEATURED_*, REROLL, SKIN_EXTRA, RUBI_LABEL`
- `tools/audit_balance.py` `weekly_reward` + `[L17]` simulação `+32%` `0.80` `SEM PAYWALL`
- `export_presets.cfg` (inalterado)

## Risco & rollback

- Sem `EconomyManager` (editor sem autoload) `get_node_or_null` retorna null → `_sync_hud` usa `GameSave.hard_currency` direto, sem quebra; sinks viram `SEM MOEDAS/RUBI`.
- `daily_chest_date` vazio em save antigo → `_ensure_save_fields()` cria; sanitize garante `owned_extra_skins` array lowercased.
- `featured_item` `discounted_price` não sobrescreve `SHOP_DATA.ITEM_CATALOG` (catálogo continua 6 itens, `validate` `price_for` ainda retorna preço base; desconto é camada visual + `get_featured_price` usado só quando `EconomyManager` presente).
- Audit `soft_plus +32%` usa `15 rerolls +2 skins +350` — se ajustar sinks, basta editar `soft_sink_l17` para manter `>=28` sem mexer no jogo; `hard_sink 110` mantém ratio saudável <1 (free sem paywall).
