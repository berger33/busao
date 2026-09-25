# Plugins nativos — contratos de wiring + checklist

Todos os managers funcionam em **mock** (editor/teste) e ligam o caminho
**nativo** automaticamente quando o singleton/método existe. Este doc define
o contrato exato que cada plugin precisa expor — instale, confira os nomes e
rode o checklist. Nada aqui quebra o mock se o plugin estiver ausente.

## 1. Google Play Billing — `GodotGooglePlayBilling` (ou `PlayBilling`)

Singleton: `Engine.has_singleton("GodotGooglePlayBilling")`.

| Membro | Tipo | Uso pelo `billing_manager.gd` |
|---|---|---|
| `start_connection()` | método | `initialize()` |
| `purchase(product_id: String)` | método | `purchase()` |
| `acknowledge(purchase_token: String)` | método | `acknowledge_purchase()` |
| `consume(purchase_token: String)` | método | `consume_if_needed()` (só consumables) |
| `query_purchases()` | método | `restore_purchases()` |
| `purchases_updated(Array[Dictionary])` | sinal | `{product_id, purchase_token, acknowledged}` → `_on_native_purchases()` |
| `query_purchases_done(Array[Dictionary])` | sinal | mesmo formato → `_on_native_query_done()` |

Regras: grant→ack→consume idempotente via `billing_ledger` no save;
`reconcile_pending()` no boot retoma crash. **Nunca** entregue consumable
sem `consume()` (Google reembolsa em ~3 dias).

Checklist:
- [ ] `android.test.purchased` credita moedas e persiste após reinstall
- [ ] matar o app no meio da compra → reconcile entrega 1× (sem duplicar)
- [ ] `remove_ads` esconde banner/interstitial, mantém rewarded
- [ ] `starter_pack` compra única (2ª tentativa → `already_owned`)

## 2. AdMob — `MobileAds` (ou `AdMob`)

| Membro | Tipo | Uso pelo `ads_manager.gd` |
|---|---|---|
| `set_request_configuration(Dictionary)` | método | `{max_ad_content_rating: "PG", tag_for_child_directed_treatment: false, tag_for_under_age_of_consent: true, tag_for_npa: bool}` |
| `initialize()` | método | futuro (hoje só flags; mock cobre o resto) |
| `show_banner/show_interstitial/show_rewarded` | métodos | futuros — hoje o manager só registra; ligue aqui |

Checklist:
- [ ] banner some com `remove_ads`; rewarded continua
- [ ] interstitial 1 a cada 2 derrotas, cooldown 90 s, nunca sem decisão de consent
- [ ] NPA serve criativo não-personalizado com `_npa_mode=true`

## 3. UMP — `UserMessagingPlatform` (ou `UMP`)

| Membro | Tipo | Uso pelo `ads_manager.gd` |
|---|---|---|
| `request_consent_info_update()` | método | `request_consent_if_required()` |
| `consent_info_updated(granted: bool)` | sinal | → `grant_consent_via_ump()` |

Sem plugin: resolve como **NPA** (nunca autoconcede). Personalizado exige
opt-in gravado em `ads_consent_granted`.

## 4. Play Games / Review / Update — `PlayServicesManager`

Ver `scripts/play_services_manager.gd` + `in_app_update_manager.gd`.
Contratos: sign-in, snapshots <50 KB (`CLOUD_SNAPSHOT_KEYS` no save),
`request_review_after_run(first_clears)` (10 clears + 2º dia), update flexível.

## 5. Firebase (Analytics/Crashlytics/RemoteConfig) — futuro

`analytics_manager.gd` e `remote_config_manager.gd` são mock-first com
`log_event()`/`price_for_item()`; ligue aos singletons GodotFirebase quando
publicar. Respeite `analytics_enabled` + consentimento (sem consent, nada sai
do aparelho — ver `PRIVACY.md`).

## 6. HMAC do save (M7) — nota de honestidade

O envelope HMAC-SHA256 (`save_data.gd`) usa chave = `OS.get_unique_id()` +
sal do app: trava edição casual, **não** é DRM (qualquer segredo no cliente
é extraível). Validação servidor-side de receipts/inventário continua no
backlog (Lote 17 do plano) para quando houver backend.
