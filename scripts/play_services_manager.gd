extends Node
## PlayServicesManager — Lote 13 (Release + Cloud + In-App Review)
## Mock-first: no editor sem plugin, simula Play Games sign-in, cloud snapshot e review com timers e user://.
## Nativo (Android): delega para singletons Godot Play Games / InAppReview quando disponíveis.
## Contrato: sign_in(), is_signed_in(), cloud_save(), cloud_load(), request_review_after_run(), unlock_achievement(), submit_leaderboard()

signal signed_in
signal signed_out
@warning_ignore("unused_signal")
signal sign_in_failed(reason: String)
signal cloud_saved
signal cloud_save_failed(reason: String)
signal cloud_loaded(snapshot: Dictionary)
signal cloud_load_failed(reason: String)
signal review_requested
signal review_failed(reason: String)
signal achievement_unlocked(id: String)

const CLOUD_MOCK_PATH := "user://cloud_snapshot.mock.json"
const LEADERBOARD_ENDLESS := "CgkEndlessDistance"
const LEADERBOARD_STARS := "CgkTotalStars"
# Achievements mapeando IDs locais do GameSave para Play Games
const ACHIEVEMENT_MAP := {
    "busao": "CgkAchievementBusao",
    "enchente": "CgkAchievementEnchente",
    "dog": "CgkAchievementDog",
    "busao50": "CgkAchievementBusao50",
    "combo15": "CgkAchievementCombo15",
    "sem_arranhao": "CgkAchievementSemArranhao",
    "capitulo1": "CgkAchievementCapitulo1",
    "maratonista": "CgkAchievementMaratonista",
}

var _signed_in := false
var _native_games := false
var _native_review := false
var _cloud_pending_save := false
var _review_cooldown := 0.0
var _mock_sign_timer := 0.0
var _mock_cloud_timer := 0.0
var _mock_review_timer := 0.0
var _first_clears_for_review := 0

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native_games = _detect_native_games()
    _native_review = _detect_native_review()
    print("[play] manager pronto | games_nativo=%s review_nativo=%s" % [str(_native_games), str(_native_review)])
    # Tenta sign-in automático após GameSave carregar (mock ok)
    call_deferred("_auto_sign_in")
    # Verifica cloud existente para restaurar pós-reinstall (mock)
    call_deferred("_try_auto_cloud_load")

func _process(delta: float) -> void:
    if _review_cooldown > 0.0:
        _review_cooldown = maxf(0.0, _review_cooldown - delta)
    # Timers mock
    if _mock_sign_timer > 0.0:
        _mock_sign_timer -= delta
        if _mock_sign_timer <= 0.0:
            _mock_sign_timer = 0.0
            _signed_in = true
            if GameSave:
                GameSave.data["play_signed_in"] = true
                # não flush imediato para não spammar disco no boot
            signed_in.emit()
            print("[play] sign-in mock OK")
    if _mock_cloud_timer > 0.0:
        _mock_cloud_timer -= delta
        if _mock_cloud_timer <= 0.0:
            _mock_cloud_timer = 0.0
            _finish_mock_cloud_save()

func _detect_native_games() -> bool:
    if Engine.has_singleton("GodotPlayGameServices") or Engine.has_singleton("PlayGameServices"):
        return true
    if ClassDB.class_exists("GodotPlayGameServices"):
        return true
    if Engine.has_singleton("PlayGames"):
        return true
    return false

func _detect_native_review() -> bool:
    if Engine.has_singleton("GodotInAppReview") or Engine.has_singleton("InAppReview"):
        return true
    if ClassDB.class_exists("GodotInAppReview"):
        return true
    return false

func _auto_sign_in() -> void:
    # Só assina se nunca falhou e internet mock ok
    if GameSave and bool(GameSave.data.get("play_signed_in", false)):
        _signed_in = true
        signed_in.emit()
        return
    sign_in()

func sign_in() -> void:
    if _signed_in:
        signed_in.emit()
        return
    if _native_games:
        print("[play] sign_in nativo…")
        # Exemplo nativo:
        # PlayGameServices.signIn()
        # conectar sinais: _on_sign_in_success, _on_sign_in_failed
        # Mock fallback se não conectar em 2s
        _mock_sign_timer = 1.1
    else:
        print("[play] sign_in mock…")
        _mock_sign_timer = 0.9

func sign_out() -> void:
    _signed_in = false
    if GameSave:
        GameSave.data["play_signed_in"] = false
        GameSave.flush()
    signed_out.emit()
    print("[play] sign_out")

func _on_sign_in_failed(reason: String = "error") -> void:
    _signed_in = false
    sign_in_failed.emit(reason)
    print("[play] sign-in falhou: %s" % reason)

func is_signed_in() -> bool:
    return _signed_in

# --- Cloud Save (Snapshots) ---
func cloud_save() -> void:
    if not is_signed_in():
        # Tenta sign-in e agenda save
        _cloud_pending_save = true
        sign_in()
        print("[play] cloud_save adiado — aguardando sign-in")
        return
    if _native_games:
        print("[play] cloud_save nativo…")
        # Nativo: PlayGameServices.snapshotSave("corre_pro_ponto", payload, description)
        # Aqui usamos mock + fallback file
        _mock_cloud_timer = 0.7
        _write_mock_cloud()
    else:
        print("[play] cloud_save mock…")
        _mock_cloud_timer = 0.6
        _write_mock_cloud()

func _write_mock_cloud() -> void:
    if not GameSave:
        cloud_save_failed.emit("no_save")
        return
    var snap := GameSave.get_cloud_snapshot() if GameSave.has_method("get_cloud_snapshot") else {}
    if snap.is_empty():
        snap = {"data": GameSave.data.duplicate(true), "ts": int(Time.get_unix_time_from_system())}
    var json := JSON.stringify(snap)
    var f := FileAccess.open(CLOUD_MOCK_PATH, FileAccess.WRITE)
    if f == null:
        cloud_save_failed.emit("write_failed")
        return
    f.store_string(json)
    f.close()
    print("[play] cloud snapshot mock gravado %d bytes ts=%s" % [json.length(), str(snap.get("ts", 0))])

func _finish_mock_cloud_save() -> void:
    if _cloud_pending_save:
        _cloud_pending_save = false
    cloud_saved.emit()
    print("[play] cloud_saved")

func _try_auto_cloud_load() -> void:
    if not FileAccess.file_exists(CLOUD_MOCK_PATH):
        return
    # Só restaura se save local está vazio (pós-reinstall) — não sobrescreve progresso local maior
    var local_stars := 0
    if GameSave:
        local_stars = int(GameSave.data.get("coins", 0)) + int(GameSave.total_stars()) if GameSave.has_method("total_stars") else 0
    if local_stars > 40: # já tem progresso (starting 40), não restaura automaticamente
        return
    cloud_load()

func cloud_load() -> void:
    if not FileAccess.file_exists(CLOUD_MOCK_PATH):
        cloud_load_failed.emit("no_snapshot")
        return
    var txt := FileAccess.get_file_as_string(CLOUD_MOCK_PATH)
    if txt.is_empty():
        cloud_load_failed.emit("empty")
        return
    var snap = JSON.parse_string(txt)
    if not snap is Dictionary:
        cloud_load_failed.emit("parse")
        return
    if GameSave and GameSave.has_method("apply_cloud_snapshot"):
        var ok: bool = GameSave.call("apply_cloud_snapshot", snap)
        if ok:
            cloud_loaded.emit(snap)
            print("[play] cloud_load aplicado ts=%s" % str(snap.get("ts", 0)))
        else:
            cloud_load_failed.emit("apply_rejected")
    else:
        cloud_loaded.emit(snap as Dictionary)

# --- Achievements / Leaderboard ---
func unlock_achievement(local_id: String) -> void:
    var play_id: String = ACHIEVEMENT_MAP.get(local_id, "")
    if play_id == "":
        return
    if _native_games:
        print("[play] unlock nativo %s (%s)" % [local_id, play_id])
        # PlayGameServices.unlockAchievement(play_id)
    else:
        print("[play] unlock mock %s" % local_id)
    achievement_unlocked.emit(local_id)

func submit_leaderboard_score(kind: String, score: int) -> void:
    var lb_id := LEADERBOARD_ENDLESS if kind == "endless" else LEADERBOARD_STARS
    if _native_games:
        print("[play] leaderboard nativo %s %d" % [lb_id, score])
        # PlayGameServices.submitScore(lb_id, score)
    else:
        print("[play] leaderboard mock %s %d" % [lb_id, score])

# --- In-App Review ---
func can_request_review() -> bool:
    if _review_cooldown > 0.0:
        return false
    # Rate limit: 1 vez por 3 dias em mock (via GameSave)
    if GameSave:
        var last: int = int(GameSave.data.get("last_review_ts", 0))
        var now: int = int(Time.get_unix_time_from_system())
        if last > 0 and now - last < 3 * 86400:
            return false
    return true

func request_review() -> void:
    if not can_request_review():
        review_failed.emit("cooldown")
        return
    if _native_review:
        print("[play] review nativo…")
        # GodotInAppReview.requestReview() — callback onReviewCompleted
        _mock_review_timer = 1.5
        review_requested.emit()
        _on_review_completed()
    else:
        print("[play] review mock… codificado como feedback suave")
        _mock_review_timer = 0.8
        review_requested.emit()
        _on_review_completed()

func _on_review_completed() -> void:
    _review_cooldown = 90.0
    if GameSave:
        GameSave.data["last_review_ts"] = int(Time.get_unix_time_from_system())
        GameSave.data["review_requests"] = int(GameSave.data.get("review_requests", 0)) + 1
        GameSave.flush()
    print("[play] review fluxo concluído (mock)")

func request_review_after_run(first_clears: int) -> void:
    # Chamado de game_3d.gd após _finish_run; só pede após 3 first_clears e se pode
    _first_clears_for_review = first_clears
    if first_clears >= 3 and can_request_review():
        # Atraso 1.2 s para não roubar foco do resultado
        await get_tree().create_timer(1.2).timeout
        request_review()
        print("[play] review agendado após %d first_clears" % first_clears)
