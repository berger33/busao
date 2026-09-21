extends Node
## PushManager — P2 (polimento)
## Streak em risco: agenda notificação local mock para 20h do dia seguinte se streak >0 e não logou hoje.
## Mock-first: sem plugin, escreve user://push_mock.json e printa; nativo usa GodotNotifications / OneSignal quando disponível.

signal push_scheduled(title: String, body: String)
signal push_cancelled

const MOCK_PATH := "user://push_mock.json"
const STREAK_HOUR := 20

var _native := false
var _scheduled: Dictionary = {}

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native = _detect_native()
    print("[push] pronto nativo=%s" % str(_native))
    # Avalia streak ao iniciar
    call_deferred("_evaluate_streak")

func _detect_native() -> bool:
    if Engine.has_singleton("GodotNotifications") or Engine.has_singleton("OneSignal") or Engine.has_singleton("Notifications"):
        return true
    if ClassDB.class_exists("GodotNotifications"):
        return true
    return false

func _evaluate_streak() -> void:
    if not GameSave:
        return
    var streak: int = int(GameSave.data.get("daily_streak", 0))
    var last: int = int(GameSave.data.get("last_login_day", -1))
    var today: int = _today_number()
    if streak <= 0:
        cancel_streak_push()
        return
    if last == today:
        # já logou hoje, agenda para amanhã 20h se quebrar sequência
        schedule_streak_push(streak, today + 1)
    elif last == today - 1:
        # em risco: não logou hoje, mas ainda dentro da janela
        schedule_streak_push(streak, today)
    else:
        cancel_streak_push()

func _today_number() -> int:
    if GameSave and GameSave.has_method("_local_day_number"):
        return GameSave.call("_local_day_number")
    var d := Time.get_datetime_dict_from_system(false)
    d["hour"] = 0; d["minute"] = 0; d["second"] = 0
    return int(Time.get_unix_time_from_datetime_dict(d) / 86400.0)

func schedule_streak_push(streak: int, target_day: int) -> void:
    var title := "🔥 Streak em risco!"
    var body := "Seu ônibus sai em %d dias seguidos — corra hoje para não perder!" % streak
    if streak >= 7:
        body = "Maratona %d dias! Não perca seu bônus de R$ %d hoje às 20h." % [streak, 100]
    _scheduled = {"title": title, "body": body, "day": target_day, "hour": STREAK_HOUR, "streak": streak}
    # Mock persist
    var f := FileAccess.open(MOCK_PATH, FileAccess.WRITE)
    if f:
        f.store_string(JSON.stringify(_scheduled))
        f.close()
    if _native:
        print("[push] nativo schedule %s %s" % [title, body])
        # OneSignal.postNotification(...) / GodotNotifications.create(...)
    else:
        print("[push] mock agendado streak=%d dia=%d %s" % [streak, target_day, body])
    push_scheduled.emit(title, body)

func cancel_streak_push() -> void:
    if _scheduled.is_empty():
        return
    _scheduled.clear()
    if FileAccess.file_exists(MOCK_PATH):
        DirAccess.remove_absolute(MOCK_PATH)
    if _native:
        print("[push] nativo cancel")
    else:
        print("[push] mock cancelado")
    push_cancelled.emit()

func get_scheduled() -> Dictionary:
    if _scheduled.is_empty() and FileAccess.file_exists(MOCK_PATH):
        var txt := FileAccess.get_file_as_string(MOCK_PATH)
        var d = JSON.parse_string(txt)
        if d is Dictionary:
            _scheduled = d
    return _scheduled.duplicate(true)

func is_streak_push_scheduled() -> bool:
    return not get_scheduled().is_empty()
