extends Node
## AdsManager — Lote 11 (Ads MVP)
## Wrapper AdMob com fallback mock para editor/teste.
## Contrato: banner no menu/mapa/loja, interstitial pós-derrota (cooldown 90 s, 1 a cada 2), rewarded revive 1× e 2× moedas.
## Sem SDK nativo o manager simula carregamento e recompensa com timers (editor não quebra).

signal banner_loaded
signal banner_failed(reason: String)
signal interstitial_loaded
signal interstitial_failed(reason: String)
signal interstitial_closed
signal rewarded_loaded
signal rewarded_failed(reason: String)
signal rewarded_completed(placement: String)
signal consent_updated(granted: bool)

const PLACEMENT_BANNER_MENU := "banner_menu"
const PLACEMENT_INTERSTITIAL_RESULT := "interstitial_result"
const PLACEMENT_REWARDED_REVIVE := "rewarded_revive"
const PLACEMENT_REWARDED_DOUBLE := "rewarded_double"

# Mock delays (s) — simulam rede em editor
const MOCK_LOAD_BANNER := 0.8
const MOCK_LOAD_INTERSTITIAL := 1.2
const MOCK_LOAD_REWARDED := 1.0
const MOCK_SHOW_REWARDED := 2.2  # tempo de vídeo simulado

var _consent_granted := false
var _consent_required := false
var _initialized := false
var _banner_ready := false
var _banner_visible := false
var _interstitial_ready := false
var _interstitial_cooldown := 0.0
var _rewarded_ready := false
var _mock_interstitial_timer := 0.0
var _mock_rewarded_timer := 0.0
var _mock_banner_timer := 0.0
var _native_available := false
var _remove_ads_cache := false

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native_available = _detect_native_ads()
    _consent_granted = bool(GameSave.data.get("ads_consent_granted", false)) if GameSave else false
    _remove_ads_cache = bool(GameSave.data.get("remove_ads", false)) if GameSave else false
    print("[ads] manager pronto | nativo=%s consent=%s remove_ads=%s" % [str(_native_available), str(_consent_granted), str(_remove_ads_cache)])
    # Auto-init no próximo frame para garantir GameSave já carregado; mock não quebra editor
    call_deferred("initialize")

func _detect_native_ads() -> bool:
    # Detecta plugin AdMob (ex.: MobileAds, AdMob). Retorna false no editor sem plugin.
    if Engine.has_singleton("MobileAds") or Engine.has_singleton("AdMob"):
        return true
    # Verifica autoload alternativo (ex.: GodotAdMob)
    if ClassDB.class_exists("MobileAds"):
        return true
    return false

func initialize() -> void:
    if _initialized:
        return
    _initialized = true
    # Em produção real aqui chamaria MobileAds.initialize()
    if _native_available:
        print("[ads] inicializando SDK nativo…")
        # Exemplo: MobileAds.initialize()
        # Conecta sinais nativos quando disponíveis
        _try_connect_native_signals()
    else:
        print("[ads] SDK nativo ausente — modo mock (editor)")
    # Inicia timers mock
    _mock_banner_timer = MOCK_LOAD_BANNER
    _mock_interstitial_timer = MOCK_LOAD_INTERSTITIAL
    _mock_rewarded_timer = MOCK_LOAD_REWARDED
    request_consent_if_required()

func request_consent_if_required() -> void:
    # Lote 11: UMP simplificado — em produção usa ConsentInformation.requestConsentInfoUpdate()
    # Aqui apenas respeita flag persistida; se nunca perguntado, assume consent implícito (mock).
    if GameSave and not GameSave.data.has("ads_consent_granted"):
        # Mock: supõe consentido após 0.5 s para não bloquear teste interno
        _consent_granted = true
        GameSave.data["ads_consent_granted"] = true
        GameSave.flush()
        consent_updated.emit(true)
        print("[ads] consent mock concedido (interno)")
    elif _consent_granted:
        consent_updated.emit(true)

func is_consent_granted() -> bool:
    return _consent_granted

func has_remove_ads() -> bool:
    if GameSave:
        return bool(GameSave.data.get("remove_ads", false))
    return _remove_ads_cache

func set_remove_ads(enabled: bool) -> void:
    _remove_ads_cache = enabled
    if GameSave:
        GameSave.data["remove_ads"] = enabled
        GameSave.flush()
    if enabled:
        hide_banner()

# ---- Banner ----
func show_banner() -> void:
    if has_remove_ads():
        print("[ads] banner suprimido (remove_ads)")
        return
    if _banner_visible:
        return
    _banner_visible = true
    if _native_available:
        # MobileAds.show_banner(...)
        print("[ads] banner show (nativo)")
    else:
        # Mock: dispara loaded após timer
        if _banner_ready:
            banner_loaded.emit()
        print("[ads] banner show (mock) placement=%s" % PLACEMENT_BANNER_MENU)

func hide_banner() -> void:
    if not _banner_visible:
        return
    _banner_visible = false
    if _native_available:
        print("[ads] banner hide (nativo)")
    else:
        print("[ads] banner hide (mock)")

func is_banner_visible() -> bool:
    return _banner_visible and not has_remove_ads()

# ---- Interstitial ----
func is_interstitial_ready() -> bool:
    if has_remove_ads():
        return false
    if _native_available:
        # return MobileAds.is_interstitial_ready()
        return _interstitial_ready
    return _interstitial_ready

func show_interstitial(placement: String = PLACEMENT_INTERSTITIAL_RESULT) -> bool:
    if has_remove_ads():
        print("[ads] interstitial bloqueado remove_ads")
        return false
    if not is_interstitial_ready():
        print("[ads] interstitial não pronto (%s)" % placement)
        interstitial_failed.emit("not_ready")
        return false
    if Engine.get_frames_per_second() < 15:
        print("[ads] interstitial adiado: FPS baixo")
        return false
    _interstitial_ready = false
    var _rc_cd := 90.0
    if has_node("/root/RemoteConfig"):
        var _rc = get_node_or_null("/root/RemoteConfig")
        if _rc and _rc.has_method("ad_interstitial_cooldown"):
            _rc_cd = _rc.call("ad_interstitial_cooldown")
    _interstitial_cooldown = _rc_cd
    if _native_available:
        print("[ads] interstitial show nativo %s" % placement)
        # MobileAds.show_interstitial()
    else:
        print("[ads] interstitial show mock %s" % placement)
        # Mock: fecha após 0.6 s
        get_tree().create_timer(0.6).timeout.connect(func(): _on_mock_interstitial_closed())
    if GameSave:
        GameSave.record_event("ad_interstitial_show")
        GameSave.data["metrics"]["event_counts"]["ad_interstitial_show"] = int(GameSave.data["metrics"]["event_counts"].get("ad_interstitial_show", 0)) + 1
    return true

func _on_mock_interstitial_closed() -> void:
    interstitial_closed.emit()
    # Recarrega
    _mock_interstitial_timer = MOCK_LOAD_INTERSTITIAL

# ---- Rewarded ----
func is_rewarded_ready() -> bool:
    if _native_available:
        return _rewarded_ready
    return _rewarded_ready

func show_rewarded(placement: String) -> bool:
    if not is_rewarded_ready():
        print("[ads] rewarded não pronto (%s)" % placement)
        rewarded_failed.emit("not_ready")
        return false
    _rewarded_ready = false
    if _native_available:
        print("[ads] rewarded show nativo %s" % placement)
        # MobileAds.show_rewarded()
    else:
        print("[ads] rewarded show mock %s (%.1fs)" % [placement, MOCK_SHOW_REWARDED])
        get_tree().create_timer(MOCK_SHOW_REWARDED).timeout.connect(func(): _on_mock_rewarded_completed(placement))
    if GameSave:
        GameSave.record_event("ad_rewarded_show")
    return true

func _on_mock_rewarded_completed(placement: String) -> void:
    rewarded_completed.emit(placement)
    # Recarrega
    _mock_rewarded_timer = MOCK_LOAD_REWARDED
    if GameSave:
        GameSave.record_event("ad_rewarded_complete")
        GameSave.data["metrics"]["event_counts"]["ad_rewarded_complete"] = int(GameSave.data["metrics"]["event_counts"].get("ad_rewarded_complete", 0)) + 1

func _try_connect_native_signals() -> void:
    # Quando plugin nativo existir, conecta sinais reais aqui.
    # Ex.: MobileAds.interstitial_closed.connect(_on_native_interstitial_closed)
    pass

func _process(delta: float) -> void:
    if not _initialized:
        return
    _interstitial_cooldown = maxf(0.0, _interstitial_cooldown - delta)
    # Mock loaders
    if not _banner_ready:
        _mock_banner_timer -= delta
        if _mock_banner_timer <= 0.0:
            _banner_ready = true
            banner_loaded.emit()
            if _banner_visible and not has_remove_ads():
                print("[ads] banner mock loaded")
    if not _interstitial_ready and _mock_interstitial_timer > 0.0:
        _mock_interstitial_timer -= delta
        if _mock_interstitial_timer <= 0.0:
            _interstitial_ready = true
            interstitial_loaded.emit()
            print("[ads] interstitial mock ready")
    if not _rewarded_ready and _mock_rewarded_timer > 0.0:
        _mock_rewarded_timer -= delta
        if _mock_rewarded_timer <= 0.0:
            _rewarded_ready = true
            rewarded_loaded.emit()
            print("[ads] rewarded mock ready")

func can_show_interstitial_now(run_count: int) -> bool:
    if has_remove_ads():
        return false
    if _interstitial_cooldown > 0.0:
        return false
    if not is_interstitial_ready():
        return false
    # 1 a cada 2 derrotas (run_count % 2 == 1)
    if run_count % 2 != 1:
        return false
    return _consent_granted
