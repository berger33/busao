extends Node
## Save local, versionado e com escrita amortecida.
## Não guarda dados pessoais nem depende de servidor; compras e desbloqueios
## usam escrita imediata, enquanto moedas de uma corrida são agrupadas em memória.

const BALANCE = preload("res://resources/game_balance.tres")
const SAVE_PATH := "user://corre_pro_ponto.json"
const BACKUP_PATH := "user://corre_pro_ponto.bak.json"
const TEMP_PATH := "user://corre_pro_ponto.tmp.json"
const SAVE_SCHEMA_VERSION := 2

var data: Dictionary = {}
var dirty := false
var autosave_timer := 0.0

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _set_defaults()
    _load_data()

func _process(delta: float) -> void:
    if not dirty:
        return
    autosave_timer -= delta
    if autosave_timer <= 0.0:
        flush()

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST and dirty:
        flush()

func _set_defaults() -> void:
    data = {
        "schema_version": SAVE_SCHEMA_VERSION,
        "coins": BALANCE.starting_coins,
        "phase_stars": [],
        "best_times": {},
        "daily_streak": 0,
        "max_streak": 0,
        "first_seen_day": -1,
        "login_days": 0,
        "last_login_day": -1,
        "xp": 0,
        "badges": [],
        "inventory": ["ze"],
        "equipped_character": "ze",
        "owned_items": [],
        "pet_skins": [],
        "achievements": [],
        "tutorial_seen": false,
        "audio_muted": false,
        "daily_date": "",
        "daily_completed": [],
        "daily_progress": {"meters": 0, "coins": 0, "clean": false},
        "weekly_key": "",
        "weekly_progress": {"meters": 0, "coins": 0, "clean_runs": 0, "runs": 0},
        "weekly_claimed": false,
        "dog_hits": 0,
        "point_idle_seconds": 0.0,
        "endless_unlocked": false,
        "endless_best": 0,
        "metrics": {
            "sessions": 0,
            "phase_attempts": 0,
            "phase_completions": 0,
            "phase_failures": 0,
            "first_clears": 0,
            "daily_claims": 0,
            "shop_purchases": 0,
            "phase_time_total": 0.0,
            "distance_total": 0,
            "longest_run_seconds": 0.0
        }
    }
    for i in int(BALANCE.phase_count):
        data["phase_stars"].append(0)

func _load_data() -> void:
    var parsed := _read_dictionary(SAVE_PATH)
    if parsed.is_empty():
        # Um JSON interrompido não pode apagar o progresso: tenta o último
        # snapshot íntegro antes de voltar ao estado inicial.
        parsed = _read_dictionary(BACKUP_PATH)
    var source_version := int(parsed.get("schema_version", 1)) if not parsed.is_empty() else SAVE_SCHEMA_VERSION
    if not parsed.is_empty():
        for key in data.keys():
            if parsed.has(key):
                data[key] = parsed[key]
        _migrate_data(source_version)
    _sanitize_data()

func _migrate_data(source_version: int) -> void:
    if source_version < 2:
        # A versão 1 já usava os mesmos campos principais; a migração adiciona
        # apenas o envelope de métricas, pet skins, semana e campos de login.
        if not (data.get("metrics", {}) is Dictionary):
            data["metrics"] = {}
        if not (data.get("pet_skins", []) is Array):
            data["pet_skins"] = []
        if not (data.get("weekly_progress", {}) is Dictionary):
            data["weekly_progress"] = {"meters": 0, "coins": 0, "clean_runs": 0, "runs": 0}
        data["schema_version"] = SAVE_SCHEMA_VERSION

func _read_dictionary(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        return {}
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return {}
    var parsed = JSON.parse_string(file.get_as_text())
    return parsed if parsed is Dictionary else {}

func _sanitize_data() -> void:
    data["schema_version"] = SAVE_SCHEMA_VERSION
    data["coins"] = maxi(0, int(data.get("coins", 0)))
    data["xp"] = maxi(0, int(data.get("xp", 0)))
    data["daily_streak"] = maxi(0, int(data.get("daily_streak", 0)))
    data["max_streak"] = maxi(0, int(data.get("max_streak", 0)))
    data["first_seen_day"] = int(data.get("first_seen_day", -1))
    data["login_days"] = maxi(0, int(data.get("login_days", 0)))
    data["last_login_day"] = int(data.get("last_login_day", -1))
    data["endless_best"] = maxi(0, int(data.get("endless_best", 0)))
    data["endless_unlocked"] = bool(data.get("endless_unlocked", false))
    data["tutorial_seen"] = bool(data.get("tutorial_seen", false))
    data["audio_muted"] = bool(data.get("audio_muted", false))
    var normalized_stars: Array = []
    var raw_stars = data.get("phase_stars", [])
    if raw_stars is Array:
        for value in raw_stars:
            normalized_stars.append(clampi(int(value), 0, 3))
    while normalized_stars.size() < int(BALANCE.phase_count):
        normalized_stars.append(0)
    if normalized_stars.size() > int(BALANCE.phase_count):
        normalized_stars.resize(int(BALANCE.phase_count))
    data["phase_stars"] = normalized_stars
    for key in ["badges", "inventory", "owned_items", "pet_skins", "achievements", "daily_completed"]:
        if not (data.get(key, []) is Array):
            data[key] = []
    if not (data.get("best_times", {}) is Dictionary):
        data["best_times"] = {}
    if not (data.get("daily_progress", {}) is Dictionary):
        data["daily_progress"] = {"meters": 0, "coins": 0, "clean": false}
    if not (data.get("weekly_progress", {}) is Dictionary):
        data["weekly_progress"] = {"meters": 0, "coins": 0, "clean_runs": 0, "runs": 0}
    if not (data.get("metrics", {}) is Dictionary):
        data["metrics"] = {}
    for key in ["sessions", "phase_attempts", "phase_completions", "phase_failures", "first_clears", "daily_claims", "shop_purchases", "distance_total"]:
        data["metrics"][key] = maxi(0, int(data["metrics"].get(key, 0)))
    data["metrics"]["phase_time_total"] = maxf(0.0, float(data["metrics"].get("phase_time_total", 0.0)))
    data["metrics"]["longest_run_seconds"] = maxf(0.0, float(data["metrics"].get("longest_run_seconds", 0.0)))
    var equipped := str(data.get("equipped_character", "ze"))
    var aliases: Dictionary = {"chefe": "carlos", "caramelo": "julia", "nina": "influencer"}
    if aliases.has(equipped):
        equipped = str(aliases[equipped])
    data["equipped_character"] = equipped
    if "ze" not in data["inventory"]:
        data["inventory"].append("ze")
    var character_aliases: Dictionary = {"chefe": "carlos", "caramelo": "julia", "nina": "influencer"}
    for legacy_id in character_aliases.keys():
        if legacy_id in data["owned_items"] and character_aliases[legacy_id] not in data["owned_items"]:
            data["owned_items"].append(character_aliases[legacy_id])

func _request_save() -> void:
    dirty = true
    autosave_timer = float(BALANCE.autosave_seconds)

func save() -> void:
    flush()

func flush() -> void:
    data["schema_version"] = SAVE_SCHEMA_VERSION
    var payload := JSON.stringify(data)
    var temp := FileAccess.open(TEMP_PATH, FileAccess.WRITE)
    if temp == null:
        return
    temp.store_string(payload)
    temp.close()
    if FileAccess.file_exists(SAVE_PATH):
        var current_bytes := FileAccess.get_file_as_bytes(SAVE_PATH)
        var backup := FileAccess.open(BACKUP_PATH, FileAccess.WRITE)
        if backup != null:
            backup.store_buffer(current_bytes)
            backup.close()
    var rename_error := DirAccess.rename_absolute(TEMP_PATH, SAVE_PATH)
    if rename_error != OK:
        # Fallback para ambientes Android/editor que não permitem rename.
        var fallback := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
        if fallback == null:
            return
        fallback.store_string(payload)
        fallback.close()
    dirty = false
    autosave_timer = 0.0

func coins() -> int:
    return int(data.get("coins", 0))

func add_coins(amount: int) -> void:
    data["coins"] = coins() + maxi(0, amount)
    _request_save()

func can_spend(amount: int) -> bool:
    return amount >= 0 and coins() >= amount

func spend(amount: int) -> bool:
    if not can_spend(amount):
        return false
    data["coins"] = coins() - amount
    flush()
    return true

func total_stars() -> int:
    var total := 0
    for value in data["phase_stars"]:
        total += int(value)
    return total

func phase_stars(index: int) -> int:
    if index < 0 or index >= data["phase_stars"].size():
        return 0
    return int(data["phase_stars"][index])

func is_phase_unlocked(index: int) -> bool:
    if index <= 0:
        return true
    if index >= int(BALANCE.phase_count):
        return false
    if index == BALANCE.chapter_unlock_phase:
        return total_stars() >= BALANCE.unlock_chapter_stars and phase_stars(BALANCE.chapter_unlock_phase - 1) >= 1
    if index == BALANCE.endless_unlock_phase:
        return total_stars() >= BALANCE.unlock_endless_stars and phase_stars(BALANCE.endless_unlock_phase - 1) >= 1
    return phase_stars(index - 1) >= 1

func record_phase(index: int, stars: int, time_seconds: float) -> Dictionary:
    if index < 0 or index >= int(BALANCE.phase_count):
        return {"first_clear": false, "new_stars": 0, "new_record": false}
    var old_stars := phase_stars(index)
    var clamped_stars := clampi(stars, 0, 3)
    data["phase_stars"][index] = maxi(old_stars, clamped_stars)
    var key := str(index)
    var previous := float(data["best_times"].get(key, 99999.0))
    var new_record := time_seconds < previous
    if new_record:
        data["best_times"][key] = snappedf(time_seconds, 0.01)
    var first_clear := old_stars == 0 and clamped_stars > 0
    var new_stars := maxi(0, int(data["phase_stars"][index]) - old_stars)
    if first_clear:
        data["metrics"]["first_clears"] = int(data["metrics"].get("first_clears", 0)) + 1
    _request_save()
    return {"first_clear": first_clear, "new_stars": new_stars, "new_record": new_record}

func best_time(index: int) -> float:
    return float(data["best_times"].get(str(index), 0.0))

func owns(item: String) -> bool:
    return item in data.get("owned_items", []) or item in data.get("inventory", [])

func unlock(item: String, price: int) -> bool:
    if owns(item):
        return true
    if not spend(price):
        return false
    data["owned_items"].append(item)
    data["metrics"]["shop_purchases"] = int(data["metrics"].get("shop_purchases", 0)) + 1
    flush()
    return true

func unlock_pet(id: String) -> bool:
    if id in data.get("pet_skins", []):
        return false
    data["pet_skins"].append(id)
    _request_save()
    return true

func owns_pet(id: String) -> bool:
    return id in data.get("pet_skins", [])

func equip_character(character: String) -> void:
    var aliases: Dictionary = {"chefe": "carlos", "caramelo": "julia", "nina": "influencer"}
    var canonical := str(aliases.get(character, character))
    if owns(canonical):
        data["equipped_character"] = canonical
        flush()

func equipped_character() -> String:
    return str(data.get("equipped_character", "ze"))

func has_achievement(id: String) -> bool:
    return id in data.get("achievements", [])

func award_achievement(id: String) -> bool:
    if has_achievement(id):
        return false
    data["achievements"].append(id)
    _request_save()
    return true

func get_daily_completed(date_key: String = "") -> Array:
    var wanted_key := date_key if date_key != "" else Time.get_date_string_from_system()
    if str(data.get("daily_date", "")) != wanted_key:
        return []
    return data.get("daily_completed", [])

func set_daily_completed(values: Array, date_key: String) -> void:
    data["daily_date"] = date_key
    data["daily_completed"] = values.duplicate()
    data["metrics"]["daily_claims"] = int(data["metrics"].get("daily_claims", 0)) + 1
    flush()

func daily_progress(date_key: String) -> Dictionary:
    if str(data.get("daily_date", "")) != date_key:
        return {"meters": 0, "coins": 0, "clean": false}
    var raw_progress = data.get("daily_progress", {})
    var progress: Dictionary = raw_progress if raw_progress is Dictionary else {}
    return {
        "meters": int(progress.get("meters", 0)),
        "coins": int(progress.get("coins", 0)),
        "clean": bool(progress.get("clean", false))
    }

func record_daily_progress(date_key: String, meters: int, coins_collected: int, clean: bool) -> void:
    var progress := daily_progress(date_key)
    progress["meters"] = int(progress["meters"]) + maxi(0, meters)
    progress["coins"] = int(progress["coins"]) + maxi(0, coins_collected)
    progress["clean"] = bool(progress["clean"]) or clean
    data["daily_date"] = date_key
    data["daily_progress"] = progress
    _request_save()

func weekly_key() -> String:
    var day_number := _local_day_number()
    return str(int(day_number / 7))

func weekly_progress(key: String) -> Dictionary:
    if str(data.get("weekly_key", "")) != key:
        return {"meters": 0, "coins": 0, "clean_runs": 0, "runs": 0}
    var raw = data.get("weekly_progress", {})
    var progress: Dictionary = raw if raw is Dictionary else {}
    return {
        "meters": int(progress.get("meters", 0)),
        "coins": int(progress.get("coins", 0)),
        "clean_runs": int(progress.get("clean_runs", 0)),
        "runs": int(progress.get("runs", 0))
    }

func record_weekly_progress(key: String, meters: int, coins_collected: int, clean: bool) -> void:
    if str(data.get("weekly_key", "")) != key:
        data["weekly_claimed"] = false
    var progress := weekly_progress(key)
    progress["meters"] = int(progress["meters"]) + maxi(0, meters)
    progress["coins"] = int(progress["coins"]) + maxi(0, coins_collected)
    progress["clean_runs"] = int(progress["clean_runs"]) + (1 if clean else 0)
    progress["runs"] = int(progress["runs"]) + 1
    data["weekly_key"] = key
    data["weekly_progress"] = progress
    _request_save()

func weekly_claimed(key: String) -> bool:
    return str(data.get("weekly_key", "")) == key and bool(data.get("weekly_claimed", false))

func set_weekly_claimed(key: String) -> void:
    data["weekly_key"] = key
    data["weekly_claimed"] = true
    flush()

func register_login() -> int:
    var today := _local_day_number()
    var last := int(data.get("last_login_day", -1))
    if today == last:
        return int(data.get("daily_streak", 0))
    if int(data.get("first_seen_day", -1)) < 0:
        data["first_seen_day"] = today
    data["login_days"] = int(data.get("login_days", 0)) + 1
    if today == last + 1:
        data["daily_streak"] = int(data.get("daily_streak", 0)) + 1
    else:
        data["daily_streak"] = 1
    data["max_streak"] = maxi(int(data.get("max_streak", 0)), int(data["daily_streak"]))
    data["last_login_day"] = today
    if int(data["daily_streak"]) % BALANCE.streak_reward_days == 0:
        data["coins"] = coins() + BALANCE.streak_reward
    data["metrics"]["sessions"] = int(data["metrics"].get("sessions", 0)) + 1
    flush()
    return int(data["daily_streak"])

func record_phase_attempt() -> void:
    data["metrics"]["phase_attempts"] = int(data["metrics"].get("phase_attempts", 0)) + 1
    _request_save()

func record_phase_result(success: bool, phase_index: int = -1, elapsed_seconds: float = 0.0, distance: int = 0) -> void:
    var key := "phase_completions" if success else "phase_failures"
    data["metrics"][key] = int(data["metrics"].get(key, 0)) + 1
    data["metrics"]["phase_time_total"] = float(data["metrics"].get("phase_time_total", 0.0)) + maxf(0.0, elapsed_seconds)
    data["metrics"]["distance_total"] = int(data["metrics"].get("distance_total", 0)) + maxi(0, distance)
    data["metrics"]["longest_run_seconds"] = maxf(float(data["metrics"].get("longest_run_seconds", 0.0)), maxf(0.0, elapsed_seconds))
    if phase_index >= 0:
        data["metrics"]["last_phase"] = phase_index
    _request_save()

func add_xp(amount: int) -> void:
    data["xp"] = int(data.get("xp", 0)) + maxi(0, amount)
    _request_save()

func xp() -> int:
    return int(data.get("xp", 0))

func xp_level() -> int:
    return 1 + int(xp() / maxi(1, BALANCE.xp_level_size))

func xp_into_level() -> int:
    return xp() % maxi(1, BALANCE.xp_level_size)

func xp_to_next_level() -> int:
    return maxi(0, BALANCE.xp_level_size - xp_into_level())

func badge_count() -> int:
    return data.get("badges", []).size()

func award_badge(id: String) -> bool:
    if id in data.get("badges", []):
        return false
    data["badges"].append(id)
    _request_save()
    return true

func _local_day_number() -> int:
    var local_date: Dictionary = Time.get_datetime_dict_from_system(false)
    return int(Time.get_unix_time_from_datetime_dict(local_date, false) / 86400.0)
