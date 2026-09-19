extends Node
## RemoteConfigManager — Lote 15 (Espelho)
## Mock-first: Firebase Remote Config com defaults locais e fetch mock 1.1 s.
## Contrato: fetch(), get_float(key), get_int(key), get_bool(key), get_string(key), is_ready().
## Nativo: FirebaseRemoteConfig.fetchAndActivate() quando singleton disponível.

signal config_ready
signal config_fetch_failed(reason: String)

const DEFAULTS := {
    "ad_interstitial_cooldown": 90.0,
    "rewarded_coins_multiplier": 2.0,
    "price_motoboy": 260,
    "price_tenis": 200,
    "ad_freq": 2,
    "ad_rewarded_double_enabled": true,
    "weekly_distance_target": 2500,
    "starter_pack_enabled": true,
}

const MOCK_FETCH_DELAY := 1.1
const CACHE_PATH := "user://remote_config.mock.json"

var _config: Dictionary = {}
var _native := false
var _ready_flag := false
var _fetching := false
var _mock_timer: float = 0.0

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native = _detect_native()
    _config = DEFAULTS.duplicate(true)
    # Carrega cache mock se existir (sobrevive a reinstall mock, mas não a wipe)
    if FileAccess.file_exists(CACHE_PATH):
        var txt := FileAccess.get_file_as_string(CACHE_PATH)
        var parsed = JSON.parse_string(txt)
        if parsed is Dictionary:
            for k in parsed.keys():
                if _config.has(k):
                    _config[k] = parsed[k]
            print("[remote] cache carregado %s" % str(_config))
    print("[remote] pronto | nativo=%s defaults=%s" % [str(_native), str(DEFAULTS)])
    # Fetch automático 0.5s após boot (não bloqueia first frame)
    call_deferred("_auto_fetch")

func _detect_native() -> bool:
    if Engine.has_singleton("FirebaseRemoteConfig") or Engine.has_singleton("RemoteConfig"):
        return true
    if ClassDB.class_exists("FirebaseRemoteConfig"):
        return true
    if Engine.has_singleton("GodotFirebaseRemoteConfig"):
        return true
    return false

func _auto_fetch() -> void:
    await get_tree().create_timer(0.5).timeout
    fetch()

func fetch() -> void:
    if _fetching:
        return
    _fetching = true
    if _native:
        print("[remote] fetch nativo…")
        # Exemplo: FirebaseRemoteConfig.fetchAndActivate()
        # conecta _on_fetch_success / _on_fetch_failed
        _mock_timer = MOCK_FETCH_DELAY
    else:
        print("[remote] fetch mock…")
        _mock_timer = MOCK_FETCH_DELAY

func _process(delta: float) -> void:
    if _mock_timer > 0.0:
        _mock_timer -= delta
        if _mock_timer <= 0.0:
            _mock_timer = 0.0
            _finish_mock_fetch()

func _finish_mock_fetch() -> void:
    _fetching = false
    # Mock: sem servidor, apenas confirma defaults (em prod viriam do console)
    # Simula variação A/B 5% para teste: price_motoboy 260→180 em 1 de 20 fetches
    if randi() % 20 == 0 and _config["price_motoboy"] == 260:
        _config["price_motoboy"] = 180
        print("[remote] A/B mock: price_motoboy 260→180")
    # Persiste cache
    var w := FileAccess.open(CACHE_PATH, FileAccess.WRITE)
    if w:
        w.store_string(JSON.stringify(_config))
        w.close()
    _ready_flag = true
    config_ready.emit()
    print("[remote] config_ready %s" % str(_config))

func is_ready() -> bool:
    return _ready_flag

func get_float(key: String) -> float:
    return float(_config.get(key, DEFAULTS.get(key, 0.0)))

func get_int(key: String) -> int:
    return int(_config.get(key, DEFAULTS.get(key, 0)))

func get_bool(key: String) -> bool:
    return bool(_config.get(key, DEFAULTS.get(key, false)))

func get_string(key: String) -> String:
    return str(_config.get(key, DEFAULTS.get(key, "")))

func get_config() -> Dictionary:
    return _config.duplicate(true)

# Helpers específicos do roadmap
func ad_interstitial_cooldown() -> float:
    return get_float("ad_interstitial_cooldown")

func rewarded_multiplier() -> float:
    return get_float("rewarded_coins_multiplier")

func price_for_item(item_id: String) -> int:
    var k := "price_" + item_id
    if _config.has(k):
        return get_int(k)
    return -1
