extends Node
## BillingManager — Lote 12 (Billing MVP)
## Wrapper Play Billing 6 com fallback mock (editor/teste).
## Catálogo é autoritativo aqui; HUD só exibe. Validação local; validação servidor fica para Lote 17.

signal products_loaded(products: Array[Dictionary])
signal purchase_success(product_id: String)
signal purchase_failed(product_id: String, reason: String)
signal purchase_pending(product_id: String)
signal owned_restored(product_ids: Array[String])

const PRODUCT_REMOVE_ADS := "remove_ads"
const PRODUCT_COIN_PACK_S := "coin_pack_s"     # 120
const PRODUCT_COIN_PACK_M := "coin_pack_m"     # 550
const PRODUCT_COIN_PACK_L := "coin_pack_l"     # 1400
const PRODUCT_STARTER_PACK := "starter_pack"   # motoboy + 120

# Catálogo autoritativo — preço exibido na HUD, valor canônico no manager.
const BILLING_CATALOG: Array[Dictionary] = [
	{
		"id": PRODUCT_COIN_PACK_S,
		"title": "Pacote 120 moedas",
		"subtitle": "120 R$ para skins e turbos",
		"price_label": "R$ 4,90",
		"price_brl": 4.90,
		"coins": 120,
		"hard": 0,
		"type": "consumable"
	},
	{
		"id": PRODUCT_COIN_PACK_M,
		"title": "Pacote 550 moedas",
		"subtitle": "+10% bônus • 550 R$",
		"price_label": "R$ 14,90",
		"price_brl": 14.90,
		"coins": 550,
		"hard": 0,
		"type": "consumable"
	},
	{
		"id": PRODUCT_COIN_PACK_L,
		"title": "Pacote 1400 moedas",
		"subtitle": "+20% bônus • 1400 R$",
		"price_label": "R$ 29,90",
		"price_brl": 29.90,
		"coins": 1400,
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
		"subtitle": "Rafa Motoboy + 120 R$",
		"price_label": "R$ 3,90",
		"price_brl": 3.90,
		"coins": 120,
		"hard": 0,
		"character": "motoboy",
		"type": "consumable"
	},
]

var _initialized := false
var _native_available := false
var _products_cache: Array[Dictionary] = []
var _purchases_pending: Dictionary = {} # product_id -> bool
var _mock_delay := 0.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_native_available = _detect_native_billing()
	print("[billing] manager pronto | nativo=%s catalog=%d" % [str(_native_available), BILLING_CATALOG.size()])
	call_deferred("initialize")

func _detect_native_billing() -> bool:
	if Engine.has_singleton("GodotGooglePlayBilling"):
		return true
	if ClassDB.class_exists("GodotGooglePlayBilling"):
		return true
	# Outro nome comum
	if Engine.has_singleton("PlayBilling"):
		return true
	return false

func initialize() -> void:
	if _initialized:
		return
	_initialized = true
	_products_cache = BILLING_CATALOG.duplicate(true)
	if _native_available:
		print("[billing] inicializando SDK nativo…")
		# Exemplo: billing = Engine.get_singleton("GodotGooglePlayBilling")
		# billing.startConnection(...)
		_try_connect_native_signals()
		# billing.querySkuDetails(...)
	else:
		print("[billing] SDK nativo ausente — modo mock (editor)")
		# Mock: supõe produtos carregados após 0.6 s
		get_tree().create_timer(0.6).timeout.connect(func(): products_loaded.emit(_products_cache))

func get_products() -> Array[Dictionary]:
	if _products_cache.is_empty():
		return BILLING_CATALOG.duplicate(true)
	return _products_cache.duplicate(true)

func price_label_for(product_id: String) -> String:
	for p in BILLING_CATALOG:
		if str(p.get("id","")) == product_id:
			return str(p.get("price_label",""))
	return "—"

func is_owned(product_id: String) -> bool:
	if product_id == PRODUCT_REMOVE_ADS:
		return bool(GameSave.data.get("remove_ads", false)) if GameSave else false
	return false

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
	if _purchases_pending.has(product_id):
		purchase_pending.emit(product_id)
		return false
	_purchases_pending[product_id] = true
	if _native_available:
		print("[billing] purchase nativo %s" % product_id)
		# billing.purchase(product_id)
		# Em nativo o callback vem por sinal `purchases_updated`
		# Aqui mockamos queda para mock para não travar teste
		_mock_delay = 1.2
		get_tree().create_timer(_mock_delay).timeout.connect(func(): _mock_complete_purchase(product_id, true))
	else:
		print("[billing] purchase mock %s (%.1fs)" % [product_id, 1.2])
		# Em internal testing o mock sempre sucede (teste `android.test.purchased`)
		get_tree().create_timer(1.2).timeout.connect(func(): _mock_complete_purchase(product_id, true))
	if GameSave:
		GameSave.record_event("billing_purchase_attempt")
	return true

func restore_purchases() -> void:
	if _native_available:
		print("[billing] restore nativo")
		# billing.queryPurchases()
	else:
		# Mock: se o save já tem remove_ads, simula restore bem-sucedido (teste pós-reinstall)
		if GameSave and bool(GameSave.data.get("remove_ads", false)):
			print("[billing] restore mock — remove_ads encontrado no save")
			owned_restored.emit([PRODUCT_REMOVE_ADS])
		else:
			print("[billing] restore mock — nada a restaurar no editor")
			owned_restored.emit([])

func _find_product(product_id: String) -> Dictionary:
	for p in BILLING_CATALOG:
		if str(p.get("id","")) == product_id:
			return p
	return {}

func _mock_complete_purchase(product_id: String, success: bool) -> void:
	_purchases_pending.erase(product_id)
	if not success:
		purchase_failed.emit(product_id, "mock_failed")
		return
	var product := _find_product(product_id)
	if product.is_empty():
		purchase_failed.emit(product_id, "unknown_product")
		return
	# Aplica recompensa autoritativa (mesmo em mock, passa pelo mesmo caminho que o nativo usaria)
	_apply_reward(product)
	purchase_success.emit(product_id)
	if GameSave:
		GameSave.record_event("billing_purchase_success")
		GameSave.data["metrics"]["event_counts"]["billing_purchase_success"] = int(GameSave.data["metrics"]["event_counts"].get("billing_purchase_success", 0)) + 1
	print("[billing] purchase_success %s" % product_id)

func _apply_reward(product: Dictionary) -> void:
	var pid := str(product.get("id",""))
	var coins: int = int(product.get("coins", 0))
	if coins > 0 and GameSave:
		GameSave.add_coins(coins)
		GameSave.flush()
	if pid == PRODUCT_REMOVE_ADS and GameSave:
		GameSave.data["remove_ads"] = true
		GameSave.flush()
		if Engine.has_singleton("AdsManager") or get_node_or_null("/root/AdsManager"):
			var ads = get_node_or_null("/root/AdsManager")
			if ads and ads.has_method("set_remove_ads"):
				ads.set_remove_ads(true)
	if pid == PRODUCT_STARTER_PACK and GameSave:
		var char_id: String = str(product.get("character","motoboy"))
		if not GameSave.owns(char_id):
			# Starter libera personagem sem cobrar R$ soft
			GameSave.data["inventory"].append(char_id)
			GameSave.data["metrics"]["shop_purchases"] = int(GameSave.data["metrics"].get("shop_purchases",0))+1
			GameSave.flush()
		# Equipa automaticamente
		GameSave.equip_character(char_id)

func _try_connect_native_signals() -> void:
	# Quando billing nativo existir, conecta sinais como `connected`, `disconnected`, `purchases_updated`, `querySkuDetails`
	pass

func consume_if_needed(product_id: String) -> void:
	# Consumables precisam ser consumidos após acknowledge para recumpra. Em mock nada a fazer.
	if _native_available:
		# billing.consume(product_id)
		pass
