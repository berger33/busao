extends Node
## Save simples, local e sem permissões de internet. O JSON fica em user://.

const SAVE_PATH := "user://corre_pro_ponto.json"
const PHASE_COUNT := 50
var data: Dictionary = {}

func _ready() -> void:
    _set_defaults()
    _load_data()

func _set_defaults() -> void:
    data = {
        "coins": 40,
        "phase_stars": [],
        "best_times": {},
        "daily_streak": 0,
        "last_login_day": -1,
        "xp": 0,
        "badges": [],
        "inventory": ["ze"],
        "equipped_character": "ze",
        "owned_items": [],
        "achievements": [],
        "tutorial_seen": false,
        "daily_date": "",
        "daily_completed": [],
        "daily_progress": {"meters": 0, "coins": 0, "clean": false},
        "dog_hits": 0,
        "point_idle_seconds": 0.0,
        "endless_unlocked": false,
        "endless_best": 0
    }
    for i in PHASE_COUNT:
        data["phase_stars"].append(0)

func _load_data() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        return
    var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
    if file == null:
        return
    var parsed = JSON.parse_string(file.get_as_text())
    if parsed is Dictionary:
        for key in data.keys():
            if parsed.has(key):
                data[key] = parsed[key]
        var equipped: String = str(data.get("equipped_character", "ze"))
        var character_aliases: Dictionary = {"chefe": "carlos", "caramelo": "julia", "nina": "influencer"}
        if character_aliases.has(equipped):
            data["equipped_character"] = character_aliases[equipped]
        var owned: Array = data.get("owned_items", [])
        for legacy_id in character_aliases.keys():
            if legacy_id in owned and character_aliases[legacy_id] not in owned:
                owned.append(character_aliases[legacy_id])
        data["owned_items"] = owned
        if data["phase_stars"].size() < PHASE_COUNT:
            while data["phase_stars"].size() < PHASE_COUNT:
                data["phase_stars"].append(0)

func save() -> void:
    var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(data))

func coins() -> int:
    return int(data.get("coins", 0))

func add_coins(amount: int) -> void:
    data["coins"] = coins() + maxi(0, amount)
    save()

func can_spend(amount: int) -> bool:
    return coins() >= amount

func spend(amount: int) -> bool:
    if not can_spend(amount):
        return false
    data["coins"] = coins() - amount
    save()
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
    if index >= PHASE_COUNT:
        return false
    if index == 19:
        return total_stars() >= 45 and phase_stars(18) >= 1
    if index == 49:
        return total_stars() >= 120 and phase_stars(48) >= 1
    return phase_stars(index - 1) >= 1

func record_phase(index: int, stars: int, time_seconds: float) -> void:
    if index < 0 or index >= PHASE_COUNT:
        return
    data["phase_stars"][index] = maxi(phase_stars(index), clampi(stars, 0, 3))
    var key := str(index)
    var previous := float(data["best_times"].get(key, 99999.0))
    if time_seconds < previous:
        data["best_times"][key] = snappedf(time_seconds, 0.01)
    save()

func best_time(index: int) -> float:
    return float(data["best_times"].get(str(index), 0.0))

func owns(item: String) -> bool:
    return item in data["owned_items"] or item in data["inventory"]

func unlock(item: String, price: int) -> bool:
    if owns(item):
        return true
    if not spend(price):
        return false
    data["owned_items"].append(item)
    save()
    return true

func equip_character(character: String) -> void:
    if owns(character):
        data["equipped_character"] = character
        save()

func equipped_character() -> String:
    return str(data.get("equipped_character", "ze"))

func has_achievement(id: String) -> bool:
    return id in data["achievements"]

func award_achievement(id: String) -> bool:
    if has_achievement(id):
        return false
    data["achievements"].append(id)
    save()
    return true

func get_daily_completed() -> Array:
    return data.get("daily_completed", [])

func set_daily_completed(values: Array, date_key: String) -> void:
    data["daily_date"] = date_key
    data["daily_completed"] = values
    save()

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

func record_daily_progress(
    date_key: String, meters: int, coins_collected: int, clean: bool
) -> void:
    var progress := daily_progress(date_key)
    progress["meters"] = int(progress["meters"]) + maxi(0, meters)
    progress["coins"] = int(progress["coins"]) + maxi(0, coins_collected)
    progress["clean"] = bool(progress["clean"]) or clean
    data["daily_date"] = date_key
    data["daily_progress"] = progress
    save()

func register_login() -> int:
    var today := int(Time.get_unix_time_from_system() / 86400.0)
    var last := int(data.get("last_login_day", -1))
    if today == last:
        return int(data.get("daily_streak", 0))
    if today == last + 1:
        data["daily_streak"] = int(data.get("daily_streak", 0)) + 1
    else:
        data["daily_streak"] = 1
    data["last_login_day"] = today
    if int(data["daily_streak"]) % 7 == 0:
        data["coins"] = coins() + 100
    save()
    return int(data["daily_streak"])

func add_xp(amount: int) -> void:
    data["xp"] = int(data.get("xp", 0)) + maxi(0, amount)
    save()

func xp() -> int:
    return int(data.get("xp", 0))

func badge_count() -> int:
    return data.get("badges", []).size()

func award_badge(id: String) -> bool:
    if id in data.get("badges", []):
        return false
    data["badges"].append(id)
    save()
    return true
