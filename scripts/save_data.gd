extends Node
## Save local, versionado e com escrita amortecida.
## Não guarda dados pessoais nem depende de servidor; compras e desbloqueios
## usam escrita imediata, enquanto moedas de uma corrida são agrupadas em memória.

const BALANCE = preload("res://resources/game_balance.tres")
const SHOP_DATA = preload("res://scripts/shop_data.gd")
const SAVE_PATH := "user://corre_pro_ponto.json"
const BACKUP_PATH := "user://corre_pro_ponto.bak.json"
const TEMP_PATH := "user://corre_pro_ponto.tmp.json"
const SAVE_SCHEMA_VERSION := 4
# Auditoria (2026-09-21): envelope HMAC-SHA256 anti-tamper. Chave = id do
# aparelho + sal do app. Dificulta edicao casual do JSON (nao e DRM: sem
# servidor nao ha segredo real — ver docs/PLUGINS_NATIVOS.md M7).
const SAVE_HMAC_SALT := "corre-pro-ponto.v4.hmac" 
const CLOUD_SNAPSHOT_KEYS: Array = ["schema_version","coins","hard_currency","remove_ads","phase_stars","best_times","achievements","inventory","owned_items","pet_skins","equipped_character","xp","daily_streak","max_streak","metrics","endless_best","endless_unlocked"]
# Retenção D0–D30: conquistas e badges pagam moedas ao desbloquear (fonte
# única de nomes/recompensas — game_3d.gd monta o catálogo daqui).
const ACHIEVEMENT_META: Dictionary = {
    "busao": {"name": "Peguei o busão!", "reward": 50},
    "enchente": {"name": "Chuva sem susto", "reward": 30},
    "dog": {"name": "Cachorro caramelo", "reward": 40},
    "busao50": {"name": "Brasil sem freio", "reward": 150},
    "capitulo1": {"name": "Primeiro terminal", "reward": 25},
    "combo15": {"name": "Combo de respeito", "reward": 25},
    "sem_arranhao": {"name": "Sem arranhão", "reward": 20},
    "maratonista": {"name": "Maratonista", "reward": 75},
}

var data: Dictionary = {}
var dirty := false
var autosave_timer := 0.0
var skip_backup_once := false
var _last_read_bad_sig := false

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
    # Android pode suspender o processo sem emitir um close tradicional. O
    # flush nesses eventos reduz a janela de perda sem gravar a cada moeda.
    if what in [NOTIFICATION_WM_CLOSE_REQUEST, NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT] and dirty:
        flush()

func _set_defaults() -> void:
    data = {
        "schema_version": SAVE_SCHEMA_VERSION,
        "coins": BALANCE.starting_coins,
        "phase_stars": [],
        "phase_goals": [],
        "best_times": {},
        "daily_streak": 0,
        "max_streak": 0,
        "first_seen_day": -1,
        "login_days": 0,
        "last_login_day": -1,
        "xp": 0,
        "badges": [],
        "inventory": ["ginger"],
        "equipped_character": "ginger",
        "owned_items": [],
        "pet_skins": [],
        "achievements": [],
        "tutorial_seen": false,
        "audio_muted": false,
        "reduced_motion": false,
        "high_contrast": false,
        "colorblind_mode": false,
        "haptics_enabled": true,
        "gesture_sensitivity": 1.0,
        "hard_currency": 0,
        "remove_ads": false,
        "billing_ledger": {},
        "ads_consent_granted": false,
        "analytics_enabled": true,
        "locale": "pt_BR",
        "daily_chest_date": "",
        "daily_chest_streak": 0,
        "owned_extra_skins": [],
        "last_reroll_color": "",
        "ad_counters": {"interstitial_run": 0, "rewarded_run": 0},
        "play_signed_in": false,
        "last_review_ts": 0,
        "review_requests": 0,
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
        "retention_flags": {"d1": false, "d7": false, "d30": false},
        "metrics": {
            "sessions": 0,
            "phase_attempts": 0,
            "phase_completions": 0,
            "phase_failures": 0,
            "first_clears": 0,
            "daily_claims": 0,
            "shop_purchases": 0,
            "coins_earned": 0,
            "coins_spent": 0,
            "phase_time_total": 0.0,
            "distance_total": 0,
            "longest_run_seconds": 0.0,
            "event_counts": {}
        }
    }
    for i in int(BALANCE.phase_count):
        data["phase_stars"].append(0)
        data["phase_goals"].append({"prazo": false, "sem_dano": false, "moedas": false})

func _load_data() -> void:
    var primary_exists := FileAccess.file_exists(SAVE_PATH)
    var primary := _read_dictionary(SAVE_PATH)
    var primary_bad_sig := _last_read_bad_sig
    var parsed := primary
    var recovered := false
    if parsed.is_empty():
        # Um JSON interrompido não pode apagar o progresso: tenta o último
        # snapshot íntegro antes de voltar ao estado inicial.
        parsed = _read_dictionary(BACKUP_PATH)
        var backup_bad_sig := _last_read_bad_sig
        recovered = not parsed.is_empty()
        if primary_bad_sig or backup_bad_sig:
            push_warning("[save] assinatura HMAC invalida — progresso pode ter sido adulterado")
            record_event("save_integrity_fail")
    var source_version := int(parsed.get("schema_version", 1)) if not parsed.is_empty() else SAVE_SCHEMA_VERSION
    if not parsed.is_empty():
        for key in data.keys():
            if parsed.has(key):
                data[key] = parsed[key]
        _migrate_data(source_version)
    _sanitize_data()
    skip_backup_once = primary_exists and primary.is_empty()
    if recovered:
        # Não sobrescreve um backup bom com o arquivo primário corrompido na
        # primeira reparação; o próximo flush cria um primário íntegro.
        dirty = true
        autosave_timer = 0.0

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
    if source_version < 3:
        # Preferências e métricas novas são aditivas: nenhum progresso da v2 é
        # recalculado nem perde sua semântica durante a migração.
        if not (data.get("retention_flags", {}) is Dictionary):
            data["retention_flags"] = {"d1": false, "d7": false, "d30": false}
        if not (data.get("metrics", {}) is Dictionary):
            data["metrics"] = {}
        data["metrics"]["event_counts"] = {}
        data["metrics"]["coins_earned"] = 0
        data["metrics"]["coins_spent"] = 0
        data["reduced_motion"] = bool(data.get("reduced_motion", false))
        data["high_contrast"] = bool(data.get("high_contrast", false))
    if source_version < 4:
        # ETAPA 6 — estrelas por objetivo (blueprint S9): cada objetivo guarda
        # a melhor realizacao em qualquer tentativa. Saves antigos nao tem
        # objetivos separados: so o "prazo" e derivado das estrelas antigas.
        var goals_antigos: Array = []
        var estrelas_antigas: Array = data.get("phase_stars", [])
        for i in int(BALANCE.phase_count):
            var antiga: int = int(estrelas_antigas[i]) if i < estrelas_antigas.size() else 0
            goals_antigos.append({"prazo": antiga >= 1, "sem_dano": false, "moedas": false})
        data["phase_goals"] = goals_antigos
    data["schema_version"] = SAVE_SCHEMA_VERSION

func _hmac_key() -> PackedByteArray:
    return (OS.get_unique_id() + SAVE_HMAC_SALT).to_utf8_buffer()

func _hmac_sha256(key: PackedByteArray, msg: PackedByteArray) -> PackedByteArray:
    var block := key
    if block.size() > 64:
        var pre := HashingContext.new()
        pre.start(HashingContext.HASH_SHA256)
        pre.update(block)
        block = pre.finish()
    block.resize(64)
    var ipad := PackedByteArray()
    var opad := PackedByteArray()
    ipad.resize(64)
    opad.resize(64)
    for i in 64:
        ipad[i] = block[i] ^ 0x36
        opad[i] = block[i] ^ 0x5C
    var inner := HashingContext.new()
    inner.start(HashingContext.HASH_SHA256)
    inner.update(ipad)
    inner.update(msg)
    var outer := HashingContext.new()
    outer.start(HashingContext.HASH_SHA256)
    outer.update(opad)
    outer.update(inner.finish())
    return outer.finish()

func _sign_payload(payload: String) -> String:
    return _hmac_sha256(_hmac_key(), payload.to_utf8_buffer()).hex_encode()

func _read_dictionary(path: String) -> Dictionary:
    _last_read_bad_sig = false
    if not FileAccess.file_exists(path):
        return {}
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return {}
    var parsed = JSON.parse_string(file.get_as_text())
    if not (parsed is Dictionary):
        return {}
    if parsed.has("sig") and parsed.has("data") and parsed["data"] is Dictionary:
        var payload := JSON.stringify(parsed["data"])
        if _sign_payload(payload) != str(parsed.get("sig", "")):
            _last_read_bad_sig = true
            return {}
        return parsed["data"]
    # Legado sem envelope (v4 pre-HMAC): carrega normal, migra no flush.
    return parsed

func _sanitize_data() -> void:
    data["schema_version"] = SAVE_SCHEMA_VERSION
    data["coins"] = maxi(0, int(data.get("coins", 0)))
    # TESTE 100k: garante saldo para comprar todos os personagens ao abrir o jogo
    # Soma total catálogo = 9300, então 100k cobre com folga. Em produção remover este bloco e voltar starting_coins=40.
    if int(data.get("coins", 0)) < 100000 and int(data.get("coins", 0)) < 90000:
        # Só injeta se ainda não tem 100k e não é save já farmado (>90k)
        # Marca com flag para não repetir após o jogador gastar
        if not bool(data.get("debug_100k_granted", false)):
            data["coins"] = 100000
            data["debug_100k_granted"] = true
            print("[save] TESTE 100k moedas injetadas para compra de personagens")
    elif not bool(data.get("debug_100k_granted", false)) and int(data.get("coins", 0)) >= 90000:
        # já tem saldo alto (100k inicial ou farm legítimo) — marca para não re-injetar após gastar abaixo de 90k
        data["debug_100k_granted"] = true
    data["xp"] = maxi(0, int(data.get("xp", 0)))
    data["daily_streak"] = maxi(0, int(data.get("daily_streak", 0)))
    data["max_streak"] = maxi(0, int(data.get("max_streak", 0)))
    data["first_seen_day"] = int(data.get("first_seen_day", -1))
    data["login_days"] = maxi(0, int(data.get("login_days", 0)))
    data["last_login_day"] = int(data.get("last_login_day", -1))
    data["endless_best"] = maxi(0, int(data.get("endless_best", 0)))
    data["dog_hits"] = maxi(0, int(data.get("dog_hits", 0)))
    data["point_idle_seconds"] = maxf(0.0, float(data.get("point_idle_seconds", 0.0)))
    data["endless_unlocked"] = bool(data.get("endless_unlocked", false))
    data["tutorial_seen"] = bool(data.get("tutorial_seen", false))
    data["audio_muted"] = bool(data.get("audio_muted", false))
    data["reduced_motion"] = bool(data.get("reduced_motion", false))
    data["high_contrast"] = bool(data.get("high_contrast", false))
    data["hard_currency"] = maxi(0, int(data.get("hard_currency", 0)))
    data["remove_ads"] = bool(data.get("remove_ads", false))
    data["ads_consent_granted"] = bool(data.get("ads_consent_granted", false))
    data["analytics_enabled"] = bool(data.get("analytics_enabled", true))
    var _loc := str(data.get("locale", "pt_BR"))
    if _loc not in ["pt_BR", "en_US", "pt", "en"]:
        _loc = "pt_BR"
    if _loc == "pt": _loc = "pt_BR"
    if _loc == "en": _loc = "en_US"
    data["locale"] = _loc
    if not (data.get("ad_counters", {}) is Dictionary):
        data["ad_counters"] = {"interstitial_run": 0, "rewarded_run": 0}
    var ad_c: Dictionary = data["ad_counters"]
    data["ad_counters"] = {"interstitial_run": maxi(0,int(ad_c.get("interstitial_run",0))), "rewarded_run": maxi(0,int(ad_c.get("rewarded_run",0)))}
    if not (data.get("retention_flags", {}) is Dictionary):
        data["retention_flags"] = {"d1": false, "d7": false, "d30": false}
    if not (data.get("billing_ledger", {}) is Dictionary):
        # Chave garantida pelos defaults; aqui so repara save corrompido.
        data["billing_ledger"] = {}
    data["play_signed_in"] = bool(data.get("play_signed_in", false))
    data["last_review_ts"] = maxi(0, int(data.get("last_review_ts", 0)))
    data["review_requests"] = maxi(0, int(data.get("review_requests", 0)))
    var flags: Dictionary = data["retention_flags"]
    data["retention_flags"] = {
        "d1": bool(flags.get("d1", false)),
        "d7": bool(flags.get("d7", false)),
        "d30": bool(flags.get("d30", false))
    }
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
    var normalized_goals: Array = []
    var raw_goals = data.get("phase_goals", [])
    for i in int(BALANCE.phase_count):
        var goal: Dictionary = {"prazo": false, "sem_dano": false, "moedas": false}
        if raw_goals is Array and i < raw_goals.size() and raw_goals[i] is Dictionary:
            goal["prazo"] = bool(raw_goals[i].get("prazo", false))
            goal["sem_dano"] = bool(raw_goals[i].get("sem_dano", false))
            goal["moedas"] = bool(raw_goals[i].get("moedas", false))
        elif int(normalized_stars[i]) >= 1:
            goal["prazo"] = true
        normalized_goals.append(goal)
    data["phase_goals"] = normalized_goals
    for key in ["badges", "inventory", "owned_items", "pet_skins", "achievements", "daily_completed"]:
        if not (data.get(key, []) is Array):
            data[key] = []
    for key in ["badges", "inventory", "owned_items", "pet_skins", "achievements"]:
        var unique_values: Array = []
        for raw_value in data[key]:
            var normalized_value := str(raw_value).strip_edges().to_lower()
            if normalized_value != "" and normalized_value not in unique_values:
                unique_values.append(normalized_value)
        data[key] = unique_values
    var normalized_inventory: Array = []
    for raw_inventory_id in data["inventory"]:
        var inventory_id := SHOP_DATA.canonical_id(str(raw_inventory_id))
        if SHOP_DATA.is_character(inventory_id) and inventory_id not in normalized_inventory:
            normalized_inventory.append(inventory_id)
    data["inventory"] = normalized_inventory
    var normalized_owned_items: Array = []
    for raw_owned_id in data["owned_items"]:
        var owned_id := SHOP_DATA.canonical_id(str(raw_owned_id))
        if SHOP_DATA.is_purchasable(owned_id) and owned_id not in normalized_owned_items:
            normalized_owned_items.append(owned_id)
    data["owned_items"] = normalized_owned_items
    var normalized_extra: Array = []
    for raw_extra in data.get("owned_extra_skins", []):
        var extra_id := str(raw_extra).strip_edges().to_lower()
        if extra_id != "" and extra_id not in normalized_extra:
            normalized_extra.append(extra_id)
    data["owned_extra_skins"] = normalized_extra
    var normalized_pets: Array = []
    for raw_pet_id in data["pet_skins"]:
        var pet_id := str(raw_pet_id).strip_edges().to_lower()
        if pet_id == "caramelo" and pet_id not in normalized_pets:
            normalized_pets.append(pet_id)
    data["pet_skins"] = normalized_pets
    if not (data.get("best_times", {}) is Dictionary):
        data["best_times"] = {}
    else:
        var normalized_times: Dictionary = {}
        for raw_key in data["best_times"].keys():
            var phase_key := int(raw_key)
            var time_value := float(data["best_times"][raw_key])
            if phase_key >= 0 and phase_key < int(BALANCE.phase_count) and time_value > 0.0 and time_value < 999999.0:
                normalized_times[str(phase_key)] = time_value
        data["best_times"] = normalized_times
    if not (data.get("daily_progress", {}) is Dictionary):
        data["daily_progress"] = {"meters": 0, "coins": 0, "clean": false}
    else:
        var daily_raw: Dictionary = data["daily_progress"]
        data["daily_progress"] = {
            "meters": maxi(0, int(daily_raw.get("meters", 0))),
            "coins": maxi(0, int(daily_raw.get("coins", 0))),
            "clean": bool(daily_raw.get("clean", false))
        }
    if not (data.get("weekly_progress", {}) is Dictionary):
        data["weekly_progress"] = {"meters": 0, "coins": 0, "clean_runs": 0, "runs": 0}
    else:
        var weekly_raw: Dictionary = data["weekly_progress"]
        data["weekly_progress"] = {
            "meters": maxi(0, int(weekly_raw.get("meters", 0))),
            "coins": maxi(0, int(weekly_raw.get("coins", 0))),
            "clean_runs": maxi(0, int(weekly_raw.get("clean_runs", 0))),
            "runs": maxi(0, int(weekly_raw.get("runs", 0)))
        }
    var normalized_daily_completed: Array = []
    for value in data.get("daily_completed", []):
        var mission_id := int(value)
        if mission_id >= 0 and mission_id <= 2 and mission_id not in normalized_daily_completed:
            normalized_daily_completed.append(mission_id)
    data["daily_completed"] = normalized_daily_completed
    if not (data.get("metrics", {}) is Dictionary):
        data["metrics"] = {}
    for key in ["sessions", "phase_attempts", "phase_completions", "phase_failures", "endless_completions", "endless_failures", "first_clears", "daily_claims", "shop_purchases", "coins_earned", "coins_spent", "distance_total", "hard_earned", "hard_spent", "sink_rerolls", "sink_skins", "chest_claims", "weekly_claims"]:
        data["metrics"][key] = maxi(0, int(data["metrics"].get(key, 0)))
    data["metrics"]["phase_time_total"] = maxf(0.0, float(data["metrics"].get("phase_time_total", 0.0)))
    data["metrics"]["longest_run_seconds"] = maxf(0.0, float(data["metrics"].get("longest_run_seconds", 0.0)))
    if not (data["metrics"].get("event_counts", {}) is Dictionary):
        data["metrics"]["event_counts"] = {}
    var normalized_events: Dictionary = {}
    for raw_event in data["metrics"]["event_counts"].keys():
        var event_name := str(raw_event).strip_edges().to_lower()
        if event_name.length() > 0 and event_name.length() <= 40:
            normalized_events[event_name] = maxi(0, int(data["metrics"]["event_counts"][raw_event]))
    data["metrics"]["event_counts"] = normalized_events
    # Elenco temporário de validação: Ginger é a única personagem ativa.
    data["inventory"] = ["ginger"]
    data["equipped_character"] = "ginger"

func _request_save() -> void:
    dirty = true
    autosave_timer = float(BALANCE.autosave_seconds)

func save() -> void:
    flush()

func flush() -> void:
    data["schema_version"] = SAVE_SCHEMA_VERSION
    var payload := JSON.stringify(data)
    var envelope := JSON.stringify({"v": SAVE_SCHEMA_VERSION, "data": data, "sig": _sign_payload(payload)})
    payload = envelope
    var temp := FileAccess.open(TEMP_PATH, FileAccess.WRITE)
    if temp == null:
        return
    temp.store_string(payload)
    temp.close()
    if FileAccess.file_exists(SAVE_PATH) and not skip_backup_once:
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
    skip_backup_once = false

func set_preference(preference: String, enabled: bool) -> void:
    if preference not in ["reduced_motion", "high_contrast", "colorblind_mode", "haptics_enabled"]:
        return
    data[preference] = enabled
    flush()

func set_gesture_sensitivity(value: float) -> void:
    data["gesture_sensitivity"] = clampf(value, 0.75, 1.35)
    flush()

func coins() -> int:
    return int(data.get("coins", 0))

func add_coins(amount: int) -> void:
    var safe_amount := maxi(0, amount)
    if safe_amount <= 0:
        return
    data["coins"] = coins() + safe_amount
    data["metrics"]["coins_earned"] = int(data["metrics"].get("coins_earned", 0)) + safe_amount
    _request_save()

func can_spend(amount: int) -> bool:
    return amount >= 0 and coins() >= amount

func spend(amount: int, flush_now: bool = true) -> bool:
    if not can_spend(amount):
        return false
    data["coins"] = coins() - amount
    data["metrics"]["coins_spent"] = int(data["metrics"].get("coins_spent", 0)) + amount
    if flush_now:
        flush()
    else:
        _request_save()
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

func record_phase(index: int, stars: int, time_seconds: float, goals: Dictionary = {}) -> Dictionary:
    if index < 0 or index >= int(BALANCE.phase_count):
        return {"first_clear": false, "new_stars": 0, "new_record": false}
    # ETAPA 6 — objetivos por tentativa (blueprint S9): estrelas 2 e 3 podem
    # ser conquistadas em tentativas diferentes; guarda-se a melhor
    # realizacao de cada objetivo e deriva-se as estrelas da uniao.
    if not goals.is_empty():
        var goal: Dictionary = data["phase_goals"][index]
        goal["prazo"] = bool(goal.get("prazo", false)) or bool(goals.get("prazo", false))
        goal["sem_dano"] = bool(goal.get("sem_dano", false)) or bool(goals.get("sem_dano", false))
        goal["moedas"] = bool(goal.get("moedas", false)) or bool(goals.get("moedas", false))
        stars = (1 if bool(goal["prazo"]) else 0) + (1 if bool(goal["sem_dano"]) else 0) \
                + (1 if bool(goal["moedas"]) else 0)
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
    return {"first_clear": first_clear, "new_stars": new_stars, "new_record": new_record,
            "stars_total": int(data["phase_stars"][index])}

func best_time(index: int) -> float:
    return float(data["best_times"].get(str(index), 0.0))

func owns(item: String) -> bool:
    var canonical := SHOP_DATA.canonical_id(item)
    return canonical in data.get("owned_items", []) or canonical in data.get("inventory", [])

func set_remove_ads(enabled: bool) -> void:
    data["remove_ads"] = enabled
    _queue_flush()

func has_remove_ads() -> bool: return bool(data.get("remove_ads", false))

func add_hard_currency(amount: int) -> void:
    if amount<=0: return
    data["hard_currency"] = maxi(0,int(data.get("hard_currency",0))+amount)
    _queue_flush()

func set_ads_consent(granted: bool) -> void:
    data["ads_consent_granted"] = granted
    _queue_flush()

func record_ad_counter(kind: String) -> void:
    var c: Dictionary = data.get("ad_counters", {"interstitial_run": 0, "rewarded_run": 0})
    if kind=="interstitial": c["interstitial_run"]=int(c.get("interstitial_run",0))+1
    elif kind=="rewarded": c["rewarded_run"]=int(c.get("rewarded_run",0))+1
    data["ad_counters"]=c
    _queue_flush()

func add_rewarded_bonus_coins(amount: int) -> bool:
    if amount<=0: return false
    add_coins(amount)
    return true

func _queue_flush() -> void:
    flush()

# ==== Lote 13 — Play Games Cloud Snapshot (<=50 KB) ====

func get_cloud_snapshot() -> Dictionary:
    var snap: Dictionary = {}
    snap["v"] = 1
    snap["ts"] = int(Time.get_unix_time_from_system())
    snap["schema_version"] = SAVE_SCHEMA_VERSION
    for k in CLOUD_SNAPSHOT_KEYS:
        if not data.has(k):
            continue
        # Clona apenas chaves limitadas; não inclui flags locais nem ad_counters
        var v = data[k]
        if v is Array:
            snap[k] = v.duplicate(true)
        elif v is Dictionary:
            snap[k] = v.duplicate(true)
        else:
            snap[k] = v
    # Tamanho: JSON.stringify truncado em 50 KB — remove métricas verbosas se estourar
    var j := JSON.stringify(snap)
    if j.length() > 50 * 1024:
        # Evita esgotar cota: descarta event_counts verbosos
        if snap.get("metrics", {}).has("event_counts"):
            (snap["metrics"] as Dictionary).erase("event_counts")
        j = JSON.stringify(snap)
    if j.length() > 50 * 1024:
        # Ainda grande: esvazia metrics por completo (recuperável)
        snap["metrics"] = {"first_clears": int(data.get("metrics", {}).get("first_clears", 0))}
        j = JSON.stringify(snap)
    # Enforce hard: se ainda >50KB aborta (não sobe snapshot corrompido)
    if j.length() > 50 * 1024:
        push_warning("[save] snapshot >50KB (%d), abort salvo" % j.length())
        return {}
    return snap

func apply_cloud_snapshot(snap: Dictionary) -> bool:
    if not snap is Dictionary:
        return false
    if int(snap.get("v", 0)) != 1:
        return false
    var _ts_remote: int = int(snap.get("ts", 0))
    var local_best: int = total_stars()
    var remote_stars_arr: Array = snap.get("phase_stars", [])
    var remote_total: int = 0
    for v in remote_stars_arr:
        remote_total += int(v)
    # Só sobrescreve se remoto tiver progresso >= local (reinstall canon: restaura remove_ads/estrelas)
    # E restaura compras estrelas/hard_currency por max()
    if remote_total < local_best and not bool(snap.get("remove_ads", false)):
        # Remoto vazio → não sobrescreve save local maior
        if int(data.get("coins", 0)) > 40:
            return false
    # Merge conservador: estrelas por max por fase, moedas/compras por max
    if snap.has("phase_stars") and snap["phase_stars"] is Array:
        for i in range(mini(data["phase_stars"].size(), (snap["phase_stars"] as Array).size())):
            var remote := clampi(int((snap["phase_stars"] as Array)[i]), 0, 3)
            data["phase_stars"][i] = maxi(int(data["phase_stars"][i]), remote)
    # Moedas/hard: max (evita perder moedas farmadas offline que snapshot antigo não tinha)
    if snap.has("coins"):
        data["coins"] = maxi(int(data.get("coins", 0)), int(snap["coins"]))
    if snap.has("hard_currency"):
        data["hard_currency"] = maxi(int(data.get("hard_currency", 0)), int(snap["hard_currency"]))
    # remove_ads: OR restaura compra pós-reinstall
    if bool(snap.get("remove_ads", false)):
        data["remove_ads"] = true
    # Inventory/owned: union
    for k in ["inventory", "owned_items", "pet_skins", "achievements"]:
        if not snap.has(k) or not snap[k] is Array:
            continue
        for id in (snap[k] as Array):
            var s := str(id)
            if s != "" and s not in (data[k] as Array):
                (data[k] as Array).append(s)
    # Equipped: só se inventory contém
    if snap.has("equipped_character") and str(snap["equipped_character"]) in (data["inventory"] as Array):
        data["equipped_character"] = str(snap["equipped_character"])
    if snap.has("xp"):
        data["xp"] = maxi(int(data.get("xp", 0)), int(snap["xp"]))
    if snap.has("endless_best"):
        data["endless_best"] = maxi(int(data.get("endless_best", 0)), int(snap["endless_best"]))
    if bool(snap.get("endless_unlocked", false)):
        data["endless_unlocked"] = true
    # Best times: min
    if snap.has("best_times") and snap["best_times"] is Dictionary:
        for k in (snap["best_times"] as Dictionary).keys():
            var rv := float((snap["best_times"] as Dictionary)[k])
            if not data["best_times"].has(k) or rv < float(data["best_times"][k]):
                if rv > 0.0 and rv < 999999.0:
                    data["best_times"][k] = snappedf(rv, 0.01)
    # Metrics: max por contador relevante
    if snap.has("metrics") and snap["metrics"] is Dictionary:
        for mk in ["first_clears", "sessions", "phase_attempts", "phase_completions", "distance_total"]:
            if snap["metrics"].has(mk):
                data["metrics"][mk] = maxi(int(data["metrics"].get(mk, 0)), int(snap["metrics"][mk]))
        if snap["metrics"].has("event_counts") and snap["metrics"]["event_counts"] is Dictionary:
            for ek in (snap["metrics"]["event_counts"] as Dictionary).keys():
                var cnt: int = int((snap["metrics"]["event_counts"] as Dictionary)[ek])
                var cur: int = int((data["metrics"]["event_counts"] as Dictionary).get(ek, 0))
                (data["metrics"]["event_counts"] as Dictionary)[ek] = maxi(cur, cnt)
    flush()
    return true

func unlock(item: String, _requested_price: int = -1) -> bool:
    # O preço vindo da tela é apenas legado/visual. O save consulta o catálogo
    # autoritativo para que nenhum fluxo antigo possa comprar por valor alterado.
    var canonical := SHOP_DATA.canonical_id(item)
    var price := SHOP_DATA.price_for(canonical)
    if price < 0:
        return false
    if owns(canonical):
        return true
    if not spend(price, false):
        return false
    data["owned_items"].append(canonical)
    data["metrics"]["shop_purchases"] = int(data["metrics"].get("shop_purchases", 0)) + 1
    record_event("shop_purchase")
    flush()
    return true

func unlock_pet(id: String) -> bool:
    var canonical := str(id).strip_edges().to_lower()
    if canonical not in ["caramelo"]:
        return false
    if canonical in data.get("pet_skins", []):
        return false
    data["pet_skins"].append(canonical)
    record_event("pet_unlock")
    flush()
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
    return str(data.get("equipped_character", "julia"))

func has_achievement(id: String) -> bool:
    return id in data.get("achievements", [])

func achievement_name(id: String) -> String:
    return str(ACHIEVEMENT_META.get(id, {}).get("name", id))

func achievement_reward(id: String) -> int:
    return int(ACHIEVEMENT_META.get(id, {}).get("reward", 0))

func award_achievement(id: String) -> bool:
    if has_achievement(id):
        return false
    data["achievements"].append(id)
    var reward: int = int(ACHIEVEMENT_META.get(id, {}).get("reward", 0))
    if reward > 0:
        add_coins(reward)
        record_event("achievement_reward")
    _request_save()
    return true

func get_daily_completed(date_key: String = "") -> Array:
    var wanted_key := date_key if date_key != "" else Time.get_date_string_from_system()
    if str(data.get("daily_date", "")) != wanted_key:
        return []
    var completed: Array = data.get("daily_completed", [])
    return completed.duplicate()

func set_daily_completed(values: Array, date_key: String, _requested_reward: int = 0) -> bool:
    if date_key.strip_edges() == "":
        return false
    var sanitized_values: Array = []
    for value in values:
        var mission_id := int(value)
        if mission_id >= 0 and mission_id <= 2 and mission_id not in sanitized_values:
            sanitized_values.append(mission_id)
    var previous_values: Array = get_daily_completed(date_key)
    for previous_id in previous_values:
        if previous_id not in sanitized_values:
            sanitized_values.append(previous_id)
    var added_count := 0
    var authoritative_reward := 0
    for mission_id in sanitized_values:
        if mission_id not in previous_values:
            added_count += 1
            authoritative_reward += int(BALANCE.daily_base_reward) + mission_id * int(BALANCE.daily_step_reward)
    if added_count <= 0:
        return false
    data["daily_date"] = date_key
    data["daily_completed"] = sanitized_values
    data["metrics"]["daily_claims"] = int(data["metrics"].get("daily_claims", 0)) + added_count
    record_event("daily_claim", added_count)
    if authoritative_reward > 0:
        add_coins(authoritative_reward)
    # Marca e recompensa entram no mesmo payload para não existir uma janela
    # de crash em que a missão fica resgatada, mas o prêmio não chega. O valor
    # enviado pela HUD é ignorado: a economia canônica vive neste autoload.
    flush()
    return true

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
    return str(int(float(day_number) / 7.0))

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

func set_weekly_claimed(key: String, _requested_reward: int = 0) -> bool:
    if key.strip_edges() == "" or weekly_claimed(key):
        return false
    var progress := weekly_progress(key)
    if int(progress.get("meters", 0)) < int(BALANCE.weekly_distance_target):
        return false
    data["weekly_key"] = key
    data["weekly_claimed"] = true
    record_event("weekly_claim")
    add_coins(int(BALANCE.weekly_reward))
    # A marca e seu prêmio têm origem no mesmo payload; o valor vindo da HUD
    # é ignorado para não abrir uma segunda fonte de economia.
    flush()
    return true

func register_login() -> int:
    var today := _local_day_number()
    var last := int(data.get("last_login_day", -1))
    if today == last:
        # Sessões contam cada abertura; a sequência e o bônus continuam sendo
        # calculados uma única vez por dia.
        data["metrics"]["sessions"] = int(data["metrics"].get("sessions", 0)) + 1
        record_event("session_start")
        flush()
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
        add_coins(BALANCE.streak_reward)
    var first_day := int(data.get("first_seen_day", today))
    var days_since_first := maxi(0, today - first_day)
    var flags: Dictionary = data.get("retention_flags", {})
    if days_since_first >= 1:
        flags["d1"] = true
    if days_since_first >= 7:
        flags["d7"] = true
    if days_since_first >= 30:
        flags["d30"] = true
    data["retention_flags"] = flags
    data["metrics"]["sessions"] = int(data["metrics"].get("sessions", 0)) + 1
    record_event("session_start")
    flush()
    return int(data["daily_streak"])

func record_event(event_name: String, amount: int = 1) -> void:
    var safe_name := event_name.strip_edges().to_lower().replace(" ", "_")
    var safe_amount := maxi(0, amount)
    if safe_name == "" or safe_amount <= 0 or safe_name.length() > 40:
        return
    var events: Dictionary = data["metrics"].get("event_counts", {})
    events[safe_name] = maxi(0, int(events.get(safe_name, 0))) + safe_amount
    data["metrics"]["event_counts"] = events
    _request_save()

func retention_flags() -> Dictionary:
    var flags: Dictionary = data.get("retention_flags", {})
    return {
        "d1": bool(flags.get("d1", false)),
        "d7": bool(flags.get("d7", false)),
        "d30": bool(flags.get("d30", false))
    }

func record_phase_attempt() -> void:
    data["metrics"]["phase_attempts"] = int(data["metrics"].get("phase_attempts", 0)) + 1
    record_event("run_start")
    _request_save()

func record_phase_result(success: bool, phase_index: int = -1, elapsed_seconds: float = 0.0, distance: int = 0) -> void:
    var key := "phase_completions" if success else "phase_failures"
    data["metrics"][key] = int(data["metrics"].get(key, 0)) + 1
    record_event("run_finish" if success else "run_fail")
    data["metrics"]["phase_time_total"] = float(data["metrics"].get("phase_time_total", 0.0)) + maxf(0.0, elapsed_seconds)
    data["metrics"]["distance_total"] = int(data["metrics"].get("distance_total", 0)) + maxi(0, distance)
    data["metrics"]["longest_run_seconds"] = maxf(float(data["metrics"].get("longest_run_seconds", 0.0)), maxf(0.0, elapsed_seconds))
    if phase_index >= 0:
        data["metrics"]["last_phase"] = phase_index
    _request_save()

func record_endless_result(success: bool, elapsed_seconds: float, distance: int) -> void:
    var key := "endless_completions" if success else "endless_failures"
    data["metrics"][key] = int(data["metrics"].get(key, 0)) + 1
    record_event("endless_finish" if success else "endless_fail")
    data["metrics"]["phase_time_total"] = float(data["metrics"].get("phase_time_total", 0.0)) + maxf(0.0, elapsed_seconds)
    data["metrics"]["distance_total"] = int(data["metrics"].get("distance_total", 0)) + maxi(0, distance)
    data["metrics"]["longest_run_seconds"] = maxf(float(data["metrics"].get("longest_run_seconds", 0.0)), maxf(0.0, elapsed_seconds))
    _request_save()

func add_xp(amount: int) -> void:
    data["xp"] = int(data.get("xp", 0)) + maxi(0, amount)
    _request_save()

func xp() -> int:
    return int(data.get("xp", 0))

func xp_level() -> int:
    return 1 + int(float(xp()) / maxi(1, BALANCE.xp_level_size))

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
    var reward: int = int(ACHIEVEMENT_META.get(id, {}).get("reward", 0))
    if reward > 0:
        add_coins(reward)
        record_event("badge_reward")
    _request_save()
    return true

func _local_day_number() -> int:
    # Usa apenas a data local (com a hora zerada): a chave semanal vira à
    # meia-noite local, igual às chaves diárias de Time.get_date_string_from_system().
    var local_date: Dictionary = Time.get_datetime_dict_from_system(false)
    var date_only: Dictionary = {
        "year": int(local_date["year"]),
        "month": int(local_date["month"]),
        "day": int(local_date["day"]),
        "hour": 0,
        "minute": 0,
        "second": 0,
    }
    return int(Time.get_unix_time_from_datetime_dict(date_only) / 86400.0)
