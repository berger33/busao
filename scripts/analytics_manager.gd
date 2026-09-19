extends Node
## AnalyticsManager — Lote 15 (Espelho)
## Mock-first: Firebase Analytics + Crashlytics + GameAnalytics mirror.
## Contrato: log_event(name, params), set_user_properties, report_crash(reason),
##           is_enabled(), mirror_metrics(). Só envia se consent concedido (UMP/Data Safety).
## Nativo (Android): delega para singletons FirebaseAnalytics / Crashlytics / GameAnalytics quando disponíveis.
## Mock editor: escreve user://analytics_mock.jsonl e espelha GameSave.metrics.event_counts para dashboard local.

signal analytics_ready
signal event_logged(name: String)

const MOCK_LOG_PATH := "user://analytics_mock.jsonl"
const MOCK_CRASH_PATH := "user://crash_mock.log"
const ENABLED_KEY := "analytics_enabled"

var _native_firebase := false
var _native_ga := false
var _native_crash := false
var _enabled := false
var _consent_granted := false
var _queue: Array[Dictionary] = []
var _session_id: String = ""
var _fps_below_45_count: int = 0
var _fps_sample_frames: int = 0

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _session_id = "%d-%d" % [Time.get_unix_time_from_system(), randi() % 10000]
    _native_firebase = _detect_firebase()
    _native_ga = _detect_ga()
    _native_crash = _detect_crash()
    _consent_granted = _read_consent()
    _enabled = _consent_granted
    print("[analytics] pronto | firebase=%s ga=%s crash=%s consent=%s session=%s" % [str(_native_firebase), str(_native_ga), str(_native_crash), str(_consent_granted), _session_id])
    # Autoregistra session_start já espelhado em GameSave.register_login(); aqui só garante espelho
    call_deferred("_flush_queue")
    # Escuta mudança de consent do AdsManager
    if Engine.has_singleton("AdsManager") or get_node_or_null("/root/AdsManager"):
        var am = get_node_or_null("/root/AdsManager")
        if am and am.has_signal("consent_updated"):
            am.consent_updated.connect(func(granted: bool): _on_consent_updated(granted))

func _read_consent() -> bool:
    if GameSave:
        return bool(GameSave.data.get("ads_consent_granted", false)) and bool(GameSave.data.get(ENABLED_KEY, true))
    return false

func _detect_firebase() -> bool:
    if Engine.has_singleton("FirebaseAnalytics") or Engine.has_singleton("Firebase"):
        return true
    if ClassDB.class_exists("FirebaseAnalytics"):
        return true
    # GodotFireBase plugin id: firebase-analytics
    if Engine.has_singleton("GodotFirebaseAnalytics"):
        return true
    return false

func _detect_ga() -> bool:
    if Engine.has_singleton("GameAnalytics") or ClassDB.class_exists("GameAnalytics"):
        return true
    return false

func _detect_crash() -> bool:
    if Engine.has_singleton("FirebaseCrashlytics") or Engine.has_singleton("Crashlytics"):
        return true
    if ClassDB.class_exists("FirebaseCrashlytics"):
        return true
    if Engine.has_singleton("GodotCrashlytics"):
        return true
    return false

func is_enabled() -> bool:
    return _enabled and _consent_granted

func set_enabled(enabled: bool) -> void:
    _enabled = enabled
    if GameSave:
        GameSave.data[ENABLED_KEY] = enabled
        GameSave.flush()
    print("[analytics] enabled=%s" % str(enabled))

func _on_consent_updated(granted: bool) -> void:
    _consent_granted = granted
    _enabled = granted
    if granted:
        print("[analytics] consent concedido — ativando espelho")
        _flush_queue()
    else:
        print("[analytics] consent revogado — pausando envios")

# ---- Evento principal: espelha save_data + envia nativo/mock ----
func log_event(name: String, params: Dictionary = {}) -> void:
    var safe := name.strip_edges().to_lower().replace(" ", "_")
    if safe == "" or safe.length() > 40:
        return
    # Gate LGPD: sem consent, apenas enfileira (max 50) e não persiste fora
    if not is_enabled():
        if _queue.size() < 50:
            _queue.append({"name": safe, "params": params, "ts": int(Time.get_unix_time_from_system()), "session": _session_id})
        return
    _send_event(safe, params)

func _send_event(name: String, params: Dictionary) -> void:
    # 1 - Espelha em GameSave.metrics.event_counts (fonte canônica do dashboard local)
    if GameSave and GameSave.has_method("record_event"):
        GameSave.call("record_event", name, 1)
    # 2 - Mock file (jsonl) — dashboard local + teste de 5 min
    _write_mock(name, params)
    # 3 - Nativo quando disponível
    if _native_firebase:
        # FirebaseAnalytics.logEvent(name, params)
        print("[analytics] firebase log %s %s" % [name, str(params)])
    if _native_ga:
        # GameAnalytics.addDesignEvent(name, params)
        print("[analytics] GA mirror %s" % name)
    event_logged.emit(name)
    # Retenção: session_start já conta para D1/D7 em save_data.retention_flags
    if name == "run_start":
        if GameSave:
            GameSave.data["metrics"]["sessions"] = int(GameSave.data["metrics"].get("sessions", 0))

func _write_mock(name: String, params: Dictionary) -> void:
    var line := JSON.stringify({"ts": int(Time.get_unix_time_from_system()), "session": _session_id, "name": name, "params": params})
    var f := FileAccess.open(MOCK_LOG_PATH, FileAccess.READ_WRITE)
    var existing := ""
    if FileAccess.file_exists(MOCK_LOG_PATH):
        var r := FileAccess.open(MOCK_LOG_PATH, FileAccess.READ)
        if r:
            existing = r.get_as_text()
            r.close()
    var w := FileAccess.open(MOCK_LOG_PATH, FileAccess.WRITE)
    if w:
        w.store_string(existing + ("" if existing.is_empty() else "\n") + line)
        w.close()

func _flush_queue() -> void:
    if not is_enabled() or _queue.is_empty():
        return
    for e in _queue:
        _send_event(e["name"], e.get("params", {}))
    _queue.clear()
    analytics_ready.emit()

# ---- Dashboard local (espelho do que Firebase mostraria) ----
func get_dashboard() -> Dictionary:
    var ev: Dictionary = {}
    var total_sessions: int = 0
    var retention: Dictionary = {}
    if GameSave:
        ev = (GameSave.data.get("metrics", {}).get("event_counts", {}) as Dictionary).duplicate(true)
        total_sessions = int(GameSave.data.get("metrics", {}).get("sessions", 0))
        retention = GameSave.retention_flags() if GameSave.has_method("retention_flags") else {}
    var crash_count: int = 0
    if FileAccess.file_exists(MOCK_CRASH_PATH):
        var t := FileAccess.get_file_as_string(MOCK_CRASH_PATH)
        crash_count = t.split("\n", false).size()
    return {
        "session_id": _session_id,
        "enabled": is_enabled(),
        "native_firebase": _native_firebase,
        "native_ga": _native_ga,
        "event_counts": ev,
        "sessions": total_sessions,
        "retention": retention,
        "fps_below_45": _fps_below_45_count,
        "fps_samples": _fps_sample_frames,
        "crashes": crash_count,
        "queue": _queue.size(),
    }

# ---- Crashlytics ----
func report_crash(reason: String, stack: String = "") -> void:
    var msg := "[%s] %s %s" % [Time.get_datetime_string_from_system(false, true), reason, stack]
    # Mock file
    var existing := ""
    if FileAccess.file_exists(MOCK_CRASH_PATH):
        existing = FileAccess.get_file_as_string(MOCK_CRASH_PATH)
    var w := FileAccess.open(MOCK_CRASH_PATH, FileAccess.WRITE)
    if w:
        w.store_string(existing + ("" if existing.is_empty() else "\n") + msg)
        w.close()
    if _native_crash:
        print("[crash] nativo report %s" % reason)
        # FirebaseCrashlytics.recordException(reason)
    else:
        print("[crash] mock gravado %s" % reason)
    # Também loga como evento para aparecer no dashboard em 5 min
    log_event("crash_report", {"reason": reason.left(40)})

func force_crash_test() -> void:
    # Teste que aparece em 5 min no mock e em Crashlytics nativo (se plugin)
    report_crash("force_crash_test", "scripts/analytics_manager.gd:force_crash_test")
    # Loga também um evento não fatal para o teste do critério "crash forçado aparece em 5 min"
    log_event("crash_forced", {"where": "manual_test"})
    print("[crash] force_crash_test — verifique user://crash_mock.log e MOCK_LOG_PATH em até 5 min")

# ---- Frame pacing (fps_below_45 por modelo) ----
func _process(delta: float) -> void:
    # Amostra a cada frame; contador por sessão para dashboard
    _fps_sample_frames += 1
    var fps := Engine.get_frames_per_second()
    if fps > 0 and fps < 45 and _fps_sample_frames % 6 == 0:
        # Throttle: 1 amostra a cada 6 frames evita flood
        _fps_below_45_count += 1
        if is_enabled() and _fps_below_45_count % 60 == 0:
            log_event("fps_below_45", {"fps": int(fps), "count": _fps_below_45_count})

# ---- Helper para game_3d: log seguro de hit/car ----
func log_hit(kind: String) -> void:
    log_event("hit_" + kind, {"kind": kind})

func log_ad_rewarded(placement: String) -> void:
    log_event("ad_rewarded", {"placement": placement})

func log_run_start(phase: int) -> void:
    log_event("run_start", {"phase": phase})

func log_run_finish(success: bool, stars: int) -> void:
    log_event("run_finish" if success else "run_fail", {"stars": stars})
