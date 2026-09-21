extends Node
## BillingManager — Lote 12 (Billing MVP) + hardening Auditoria (2026-09-21).
## Wrapper Play Billing 6 com fallback mock (editor/teste).
## Catalogo e autoritativo aqui; HUD so exibe.
##
## Garantias desta versao:
## - ledger idempotente grant->ack->consume persistido no save: crash no meio
##   da compra nao duplica moedas nem deixa consumable sem consumir (o Google
##   reembolsa consumable nao consumido em ~3 dias);
## - reconcile_pending() no boot retoma o que ficou pelo caminho;
## - mock passa pelo MESMO caminho do nativo (grant/ack/consume);
## - rebalance S 300 / M 1000 / L 2200 (S cruza Maria 180); starter one-time.

signal products_loaded(products: Array[Dictionary])
signal purchase_success(product_id: String)
signal purchase_failed(product_id: String, reason: String)
signal purchase_pending(product_id: String)
signal owned_restored(product_ids: Array[String])

const PRODUCT_REMOVE_ADS := "remove_ads"
const PRODUCT_COIN_PACK_S := "coin_pack_s"     # 300
const PRODUCT_COIN_PACK_M := "coin_pack_m"     # 1000
const PRODUCT_COIN_PACK_L := "coin_pack_l"     # 2200
const PRODUCT_STARTER_PACK := "starter_pack"   # motoboy + 300 (one-time)

# Catalogo autoritativo — preco exibido na HUD, valor canonico no manager.
const BILLING_CATALOG: Array[Dictionary] = [
    {
        "id": PRODUCT_COIN_PACK_S,
        "title": "Pacote 300 moedas",
        "subtitle": "300 R$ para skins e turbos",
        "price_label": "R$ 4,90",
        "price_brl": 4.90,
        "coins": 300,
        "hard": 0,
        "type": "consumable"
    },
    {
        "id": PRODUCT_COIN_PACK_M,
        "title": "Pacote 1000 moedas",
        "subtitle": "+10% bônus • 1000 R$",
        "price_label": "R$ 14,90",
        "price_brl": 14.90,
        "coins": 1000,
        "hard": 0,
        "type": "consumable"
    },
    {
        "id": PRODUCT_COIN_PACK_L,
        "title": "Pacote 2200 moedas",
        "subtitle": "+20% bônus • 2200 R$",
        "price_label": "R$ 29,90",
        "price_brl": 29.90,
        "coins": 2200,
        "hard": 0,
        "type": "consumable"
    },
    {
        "id": PRODUCT_REMOVE_ADS,
        "title": "Remover anúncios",
        "subtitle": "sem interstitial/banner • rewarded continua",
        "price_label": "R$ 9,90",
        "price_brl": 9.90,
        "coins": 0,
        "hard": 0,
        "type": "non_consumable"
    },
    {
        "id": PRODUCT_STARTER_PACK,
        "title": "Pack Motoboy",
        "subtitle": "Rafa Motoboy + 300 R$ • compra única",
        "price_label": "R$ 3,90",
        "price_brl": 3.90,
        "coins": 300,
        "hard": 0,
        "character": "motoboy",
        "type": "one_time"
    },
]

var _initialized := false
var _native_available := false
var _native_billing = null
var _products_cache: Array[Dictionary] = []
var _purchases_pending: Dictionary = {} # product_id -> purchase_token

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native_available = _detect_native_billing()
    print("[billing] manager pronto | nativo=%s catalog=%d" % [str(_native_available), BILLING_CATALOG.size()])
    call_deferred("initialize")

func _detect_native_billing() -> bool:
    for singleton in ["GodotGooglePlayBilling", "PlayBilling"]:
        if Engine.has_singleton(singleton):
            _native_billing = Engine.get_singleton(singleton)
            return true
    if ClassDB.class_exists("GodotGooglePlayBilling"):
        return true
    return false

func initialize() -> void:
    if _initialized:
        return
    _initialized = true
    _products_cache = BILLING_CATALOG.duplicate(true)
    if _native_available:
        print("[billing] inicializando SDK nativo…")
        _try_connect_native_signals()
        if _native_billing != null and _native_billing.has_method("start_connection"):
            _native_billing.call("start_connection")
    else:
        print("[billing] SDK nativo ausente — modo mock (editor)")
        get_tree().create_timer(0.6).timeout.connect(func(): products_loaded.emit(_products_cache))
    call_deferred("reconcile_pending")

func get_products() -> Array[Dictionary]:
    if _products_cache.is_empty():
        return BILLING_CATALOG.duplicate(true)
    return _products_cache.duplicate(true)

func price_label_for(product_id: String) -> String:
    for p in BILLING_CATALOG:
        if str(p.get("id", "")) == product_id:
            return str(p.get("price_label", ""))
    return "—"

func is_owned(product_id: String) -> bool:
    if GameSave == null:
        return false
    if product_id == PRODUCT_REMOVE_ADS:
        return bool(GameSave.data.get("remove_ads", false))
    if product_id == PRODUCT_STARTER_PACK:
        return _ledger_has_consumed(PRODUCT_STARTER_PACK)
    return false

# ------------------------------------------------------------------
# Ledger idempotente (grant->ack->consume), persistido no save.
# ------------------------------------------------------------------

func _ledger() -> Dictionary:
    if GameSave == null:
        return {}
    if not (GameSave.data.get("billing_ledger", {}) is Dictionary):
        GameSave.data["billing_ledger"] = {}
    return GameSave.data["billing_ledger"]

func _ledger_save() -> void:
    if GameSave:
        GameSave.flush()

func _ledger_has_consumed(product_id: String) -> bool:
    for token in _ledger().keys():
        var entry: Dictionary = _ledger()[token]
        if str(entry.get("product_id", "")) == product_id and str(entry.get("state", "")) in ["acknowledged", "consumed"]:
            return true
    return false

func _ledger_put(token: String, product_id: String, state: String) -> void:
    var ledger := _ledger()
    ledger[token] = {"product_id": product_id, "state": state, "ts": int(Time.get_unix_time_from_system())}
    _ledger_save()

func _ledger_state(token: String) -> String:
    return str(_ledger().get(token, {}).get("state", ""))

func reconcile_pending() -> void:
    # Retoma compras interrompidas por crash: grant sem ack/consume e
    # pendencias de sessao anterior (mock nunca completa apos restart).
    var ledger := _ledger()
    if ledger.is_empty():
        return
    print("[billing] reconcile: %d entradas" % ledger.size())
    for token in ledger.keys():
        var entry: Dictionary = ledger[token]
        var pid := str(entry.get("product_id", ""))
        var state := str(entry.get("state", ""))
        if state == "pending":
            _ledger_put(token, pid, "expired")
            print("[billing] reconcile expirou %s" % pid)
        elif state == "granted":
            acknowledge_purchase(pid, token)
            consume_if_needed(pid, token)
        elif state == "acknowledged" and _is_consumable(pid):
            consume_if_needed(pid, token)

func _is_consumable(product_id: String) -> bool:
    return str(_find_product(product_id).get("type", "")) == "consumable"

# ------------------------------------------------------------------
# Compra
# ------------------------------------------------------------------

func purchase(product_id: String) -> bool:
    if not _initialized:
        initialize()
    var product := _find_product(product_id)
    if product.is_empty():
        purchase_failed.emit(product_id, "unknown_product")
        return false
    if product_id == PRODUCT_REMOVE_ADS and is_owned(product_id):
        purchase_failed.emit(product_id, "already_owned")
        return false
    if product_id == PRODUCT_STARTER_PACK and is_owned(product_id):
        purchase_failed.emit(product_id, "already_owned")
        return false
    if _purchases_pending.has(product_id):
        purchase_pending.emit(product_id)
        return false
    var token := "mock_%s_%d" % [product_id, Time.get_ticks_msec()]
    _purchases_pending[product_id] = token
    _ledger_put(token, product_id, "pending")
    if _native_billing != null and _native_billing.has_method("purchase"):
        print("[billing] purchase nativo %s" % product_id)
        _native_billing.call("purchase", product_id)
        # O callback chega por `purchases_updated` -> _on_native_purchases().
    else:
        if _native_available:
            print("[billing] nativo sem purchase() — caindo para mock")
        print("[billing] purchase mock %s (1.2s)" % product_id)
        get_tree().create_timer(1.2).timeout.connect(func(): _mock_complete_purchase(product_id, token, true))
    if GameSave:
        GameSave.record_event("billing_purchase_attempt")
    return true

func restore_purchases() -> void:
    if _native_billing != null and _native_billing.has_method("query_purchases"):
        print("[billing] restore nativo")
        _native_billing.call("query_purchases")
        return
    # Mock/ledger: remove_ads do save + one-times ja consumidos no ledger.
    var restored: Array[String] = []
    if GameSave and bool(GameSave.data.get("remove_ads", false)):
        restored.append(PRODUCT_REMOVE_ADS)
    if _ledger_has_consumed(PRODUCT_STARTER_PACK):
        restored.append(PRODUCT_STARTER_PACK)
    print("[billing] restore mock/ledger: %s" % str(restored))
    owned_restored.emit(restored)

func _find_product(product_id: String) -> Dictionary:
    for p in BILLING_CATALOG:
        if str(p.get("id", "")) == product_id:
            return p
    return {}

func _mock_complete_purchase(product_id: String, token: String, success: bool) -> void:
    _purchases_pending.erase(product_id)
    if not success:
        _ledger_put(token, product_id, "failed")
        purchase_failed.emit(product_id, "mock_failed")
        return
    _on_purchase_updated(product_id, token)

func _on_purchase_updated(product_id: String, token: String) -> void:
    # Caminho unico (mock e nativo): grant idempotente -> ack -> consume.
    var product := _find_product(product_id)
    if product.is_empty():
        purchase_failed.emit(product_id, "unknown_product")
        return
    var state := _ledger_state(token)
    if state in ["granted", "acknowledged", "consumed"]:
        print("[billing] %s ja entregue (%s) — retomando ack/consume" % [product_id, state])
    else:
        _apply_reward(product)
        _ledger_put(token, product_id, "granted")
        if GameSave:
            GameSave.record_event("billing_purchase_success")
    acknowledge_purchase(product_id, token)
    consume_if_needed(product_id, token)
    purchase_success.emit(product_id)
    print("[billing] purchase_success %s" % product_id)

func acknowledge_purchase(product_id: String, token: String) -> void:
    if _ledger_state(token) in ["acknowledged", "consumed"]:
        return
    if _native_billing != null and _native_billing.has_method("acknowledge"):
        _native_billing.call("acknowledge", token)
    _ledger_put(token, product_id, "acknowledged")

func consume_if_needed(product_id: String, token: String = "") -> void:
    if not _is_consumable(product_id):
        return
    if token != "" and _ledger_state(token) == "consumed":
        return
    if _native_billing != null and _native_billing.has_method("consume"):
        _native_billing.call("consume", token if token != "" else product_id)
    if token != "":
        _ledger_put(token, product_id, "consumed")
    print("[billing] consumed %s" % product_id)

func _apply_reward(product: Dictionary) -> void:
    var pid := str(product.get("id", ""))
    var coins: int = int(product.get("coins", 0))
    if coins > 0 and GameSave:
        GameSave.add_coins(coins)
        GameSave.flush()
    if pid == PRODUCT_REMOVE_ADS and GameSave:
        GameSave.data["remove_ads"] = true
        GameSave.flush()
        var ads := get_node_or_null("/root/AdsManager")
        if ads and ads.has_method("set_remove_ads"):
            ads.set_remove_ads(true)
    if pid == PRODUCT_STARTER_PACK and GameSave:
        var char_id: String = str(product.get("character", "motoboy"))
        if not GameSave.owns(char_id):
            GameSave.data["inventory"].append(char_id)
            GameSave.data["metrics"]["shop_purchases"] = int(GameSave.data["metrics"].get("shop_purchases", 0)) + 1
            GameSave.flush()
        GameSave.equip_character(char_id)

func _try_connect_native_signals() -> void:
    if _native_billing == null:
        return
    # Contrato (docs/PLUGINS_NATIVOS.md): purchases_updated(Array[Dictionary]
    # {product_id, purchase_token, acknowledged}), query_purchases_done(...).
    if _native_billing.has_signal("purchases_updated"):
        var cb := Callable(self, "_on_native_purchases")
        if not _native_billing.is_connected("purchases_updated", cb):
            _native_billing.connect("purchases_updated", cb)
    if _native_billing.has_signal("query_purchases_done"):
        var cb2 := Callable(self, "_on_native_query_done")
        if not _native_billing.is_connected("query_purchases_done", cb2):
            _native_billing.connect("query_purchases_done", cb2)

func _on_native_purchases(purchases: Array) -> void:
    for item in purchases:
        if not (item is Dictionary):
            continue
        var pid := str(item.get("product_id", ""))
        var token := str(item.get("purchase_token", "native_%s" % pid))
        _purchases_pending.erase(pid)
        _on_purchase_updated(pid, token)

func _on_native_query_done(purchases: Array) -> void:
    var restored: Array[String] = []
    for item in purchases:
        if not (item is Dictionary):
            continue
        var pid := str(item.get("product_id", ""))
        var token := str(item.get("purchase_token", "native_%s" % pid))
        if pid == PRODUCT_REMOVE_ADS:
            if GameSave:
                GameSave.data["remove_ads"] = true
                GameSave.flush()
            restored.append(pid)
        elif pid == PRODUCT_STARTER_PACK:
            _ledger_put(token, pid, "acknowledged")
            restored.append(pid)
        elif _is_consumable(pid):
            # Consumable nao consumido (reinstalou antes do consume): entrega
            # agora pelo caminho idempotente e consome em seguida.
            _on_purchase_updated(pid, token)
    owned_restored.emit(restored)
