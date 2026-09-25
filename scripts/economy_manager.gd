extends Node
## EconomyManager — Lote 17 (Sinfonia)
## 2ª moeda Rubi + daily_chest + weekly_event + sinks + shop rotation (determinístico, sem paywall F1-F5).
## Mock-first: sem servidor, determinístico via seed diária/semanal; auditável por tools/audit_balance.py.

signal chest_claimed(reward: Dictionary)
signal chest_claim_failed(reason: String)
@warning_ignore("unused_signal")
signal weekly_event_changed(event: Dictionary)
signal sink_purchased(kind: String)

const RUBI_STARTING := 0
const DAILY_CHEST_COOLDOWN_DAYS := 1
const REROLL_COST_COINS := 40
# Retenção D0–D30: era 80 (27–80 dias de baú por skin — inalcançável);
# 15 ≈ 1–2 semanas de baú + níveis, preço de cosmético premium justo.
const SKIN_EXTRA_COST_RUBI := 15

# Eventos semanais (LiveOps) — rodízio determinístico por weekly_key % 3
const WEEKLY_EVENTS: Array[Dictionary] = [
    {"id": "semana_motoboy", "title": "Semana do Motoboy", "desc": "motos +30% • bonus +5 R$ por moto desviada", "moto_rate_bonus": 0.30, "accent": Color("#f2635e")},
    {"id": "semana_onibus", "title": "Semana do Busão", "desc": "ônibus +20% • recompensa +8 R$ no ponto", "bus_rate_bonus": 0.20, "accent": Color("#63c8ed")},
    {"id": "semana_normal", "title": "Semana Normal", "desc": "fluxo equilibrado • sem bônus", "accent": Color("#54d18b")},
]

var _last_weekly_key: String = ""

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    # Garante campos de LiveOps no save (migração L17)
    _ensure_save_fields()
    # Conecta locale? não precisa
    print("[economy] pronto Rubi=%d chest=%s weekly=%s" % [get_rubi(), str(get_daily_chest_status()), str(get_weekly_event())])

func _ensure_save_fields() -> void:
    if not GameSave:
        return
    var d: Dictionary = GameSave.data
    if not d.has("daily_chest_date"):
        d["daily_chest_date"] = ""
    if not d.has("daily_chest_streak"):
        d["daily_chest_streak"] = 0
    if not d.has("weekly_event_seen"):
        d["weekly_event_seen"] = {}
    # metrics hard
    if not d.has("metrics"):
        d["metrics"] = {}
    var m: Dictionary = d["metrics"]
    for k in ["hard_earned", "hard_spent", "sink_rerolls", "sink_skins", "chest_claims", "weekly_claims"]:
        if not m.has(k):
            m[k] = 0
    # owned_extra_skins
    if not d.has("owned_extra_skins"):
        d["owned_extra_skins"] = []

# ---- Rubi ----
func get_rubi() -> int:
    return int(GameSave.data.get("hard_currency", 0)) if GameSave else 0

func can_spend_rubi(amount: int) -> bool:
    return amount >= 0 and get_rubi() >= amount

func add_rubi(amount: int, reason: String = "") -> void:
    if amount <= 0:
        return
    if GameSave and GameSave.has_method("add_hard_currency"):
        GameSave.call("add_hard_currency", amount)
    else:
        GameSave.data["hard_currency"] = get_rubi() + amount
        GameSave.flush()
    GameSave.data["metrics"]["hard_earned"] = int(GameSave.data["metrics"].get("hard_earned", 0)) + amount
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "hard_earned", {"amount": amount, "reason": reason})
    print("[economy] +%d Rubi (%s) saldo=%d" % [amount, reason, get_rubi()])

func spend_rubi(amount: int, reason: String = "") -> bool:
    if not can_spend_rubi(amount):
        return false
    GameSave.data["hard_currency"] = get_rubi() - amount
    GameSave.data["metrics"]["hard_spent"] = int(GameSave.data["metrics"].get("hard_spent", 0)) + amount
    GameSave.flush()
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "hard_spent", {"amount": amount, "reason": reason})
    print("[economy] -%d Rubi (%s) saldo=%d" % [amount, reason, get_rubi()])
    return true

# ---- Daily Chest (soft + Rubi, 1/dia, sem aleatoriedade paga) ----
func get_daily_chest_status(date_key: String = "") -> Dictionary:
    var key: String = date_key if date_key != "" else Time.get_date_string_from_system()
    var claimed: bool = str(GameSave.data.get("daily_chest_date", "")) == key
    # Recompensa determinística por dia: 5/10/15 soft + 1/2/3 Rubi via hash do dia
    var day_num: int = 0
    # Usa Time.get_unix_time_from_datetime_dict para derivar day number
    var dict := Time.get_datetime_dict_from_system(false)
    dict["hour"] = 0; dict["minute"] = 0; dict["second"] = 0
    day_num = int(Time.get_unix_time_from_datetime_dict(dict) / 86400.0)
    var soft: int = 5 + (day_num % 3) * 5  # 5,10,15
    var hard: int = 1 + (day_num % 3)      # 1,2,3
    # Bonus semanal: se evento motoboy, +2 Rubi no chest
    var weekly := get_weekly_event()
    if weekly.get("id", "") == "semana_motoboy":
        hard += 1
    return {"date": key, "claimed": claimed, "soft": soft, "hard": hard, "streak": int(GameSave.data.get("daily_chest_streak", 0))}

func can_claim_daily_chest(date_key: String = "") -> bool:
    var st := get_daily_chest_status(date_key)
    return not bool(st.get("claimed", false))

func claim_daily_chest(date_key: String = "") -> Dictionary:
    var key: String = date_key if date_key != "" else Time.get_date_string_from_system()
    if not can_claim_daily_chest(key):
        chest_claim_failed.emit("already_claimed")
        return {}
    var st := get_daily_chest_status(key)
    var soft: int = int(st.get("soft", 0))
    var hard: int = int(st.get("hard", 0))
    # Credit
    GameSave.add_coins(soft)
    add_rubi(hard, "daily_chest")
    GameSave.data["daily_chest_date"] = key
    GameSave.data["daily_chest_streak"] = int(GameSave.data.get("daily_chest_streak", 0)) + 1
    GameSave.data["metrics"]["chest_claims"] = int(GameSave.data["metrics"].get("chest_claims", 0)) + 1
    GameSave.flush()
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "daily_chest", {"soft": soft, "hard": hard})
    var reward := {"soft": soft, "hard": hard, "date": key}
    chest_claimed.emit(reward)
    print("[economy] daily_chest %s +%d soft +%d Rubi" % [key, soft, hard])
    return reward

# ---- Weekly Event ----
func get_weekly_event(weekly_key: String = "") -> Dictionary:
    var key: String = weekly_key if weekly_key != "" else GameSave.weekly_key() if GameSave and GameSave.has_method("weekly_key") else "0"
    var idx: int = int(key) % WEEKLY_EVENTS.size() if key.is_valid_int() else hash(key) % WEEKLY_EVENTS.size()
    idx = abs(idx) % WEEKLY_EVENTS.size()
    var ev: Dictionary = WEEKLY_EVENTS[idx].duplicate(true)
    ev["weekly_key"] = key
    if _last_weekly_key != key:
        _last_weekly_key = key
        weekly_event_changed.emit(ev)
    return ev

func is_weekly_event_active(event_id: String) -> bool:
    return str(get_weekly_event().get("id", "")) == event_id

func get_weekly_bonus_coins() -> int:
    var ev := get_weekly_event()
    if ev.get("id", "") == "semana_onibus":
        return 8
    if ev.get("id", "") == "semana_motoboy":
        return 5
    return 0

func get_moto_rate_multiplier() -> float:
    var ev := get_weekly_event()
    return 1.0 + float(ev.get("moto_rate_bonus", 0.0))

# ---- Shop rotation (determinístico semanal) ----
func get_featured_item(weekly_key: String = "") -> Dictionary:
    # Escolhe um dos 6 itens como destaque com 15% desconto na semana
    var key: String = weekly_key if weekly_key != "" else GameSave.weekly_key() if GameSave and GameSave.has_method("weekly_key") else "0"
    var items: Array = []
    if GameSave:
        # Use shop_data catalog
        var SHOP_DATA = preload("res://scripts/shop_data.gd")
        items = SHOP_DATA.item_catalog()
    if items.is_empty():
        return {}
    var idx: int = int(key) % items.size() if key.is_valid_int() else hash(key) % items.size()
    idx = abs(idx) % items.size()
    var feat: Dictionary = items[idx].duplicate(true)
    feat["discount"] = 0.15
    feat["featured"] = true
    feat["discounted_price"] = maxi(1, int(round(int(feat.get("price", 0)) * 0.85)))
    feat["weekly_key"] = key
    return feat

func get_featured_price(item_id: String) -> int:
    var feat := get_featured_item()
    if str(feat.get("id", "")) == item_id:
        return int(feat.get("discounted_price", feat.get("price", 0)))
    var SHOP_DATA = preload("res://scripts/shop_data.gd")
    return SHOP_DATA.price_for(item_id)

# ---- Sinks ----
func reroll_moto_color() -> bool:
    if not GameSave.can_spend(REROLL_COST_COINS):
        chest_claim_failed.emit("no_coins")
        return false
    if not GameSave.spend(REROLL_COST_COINS, true):
        return false
    GameSave.data["metrics"]["sink_rerolls"] = int(GameSave.data["metrics"].get("sink_rerolls", 0)) + 1
    GameSave.flush()
    # Gera cor aleatória determinística via rng
    var colors: Array[String] = ["#f2635e", "#63c8ed", "#54d18b", "#ffd34e", "#ac8cff"]
    var pick: String = colors[randi() % colors.size()]
    # Persiste último reroll
    GameSave.data["last_reroll_color"] = pick
    sink_purchased.emit("reroll")
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "sink_reroll", {"cost": REROLL_COST_COINS, "color": pick})
    print("[economy] reroll moto %s -%d coins" % [pick, REROLL_COST_COINS])
    return true

func buy_extra_skin(skin_id: String) -> bool:
    var canon := str(skin_id).strip_edges().to_lower()
    if canon == "":
        return false
    if canon in (GameSave.data.get("owned_extra_skins", []) as Array):
        return true # já tem
    if not can_spend_rubi(SKIN_EXTRA_COST_RUBI):
        chest_claim_failed.emit("no_rubi")
        return false
    if not spend_rubi(SKIN_EXTRA_COST_RUBI, "skin:" + canon):
        return false
    (GameSave.data["owned_extra_skins"] as Array).append(canon)
    GameSave.data["metrics"]["sink_skins"] = int(GameSave.data["metrics"].get("sink_skins", 0)) + 1
    GameSave.flush()
    sink_purchased.emit("skin")
    print("[economy] skin extra %s -%d Rubi" % [canon, SKIN_EXTRA_COST_RUBI])
    return true

func owns_extra_skin(skin_id: String) -> bool:
    return str(skin_id).strip_edges().to_lower() in (GameSave.data.get("owned_extra_skins", []) as Array)

# ---- Audit helper (para tools/audit_balance.py L17) ----
func get_audit_ratios() -> Dictionary:
    var m: Dictionary = GameSave.data.get("metrics", {})
    var coins_spent: int = int(m.get("coins_spent", 0))
    var coins_earned: int = int(m.get("coins_earned", 0))
    var hard_spent: int = int(m.get("hard_spent", 0))
    var hard_earned: int = int(m.get("hard_earned", 0))
    var sink_rerolls: int = int(m.get("sink_rerolls", 0))
    var sink_skins: int = int(m.get("sink_skins", 0))
    # Simulação estática: sem sinks, coins_spent seria ~75% de earned; com sinks L17, sobe +30%
    var soft_ratio: float = float(coins_spent) / max(1, coins_earned) if coins_earned > 0 else 0.0
    var hard_ratio: float = float(hard_spent) / max(1, hard_earned) if hard_earned > 0 else 0.0
    return {
        "soft_sink_ratio": soft_ratio,
        "hard_sink_ratio": hard_ratio,
        "hard_source": hard_earned,
        "hard_sink": hard_spent,
        "soft_source": coins_earned,
        "soft_sink": coins_spent,
        "rerolls": sink_rerolls,
        "skins": sink_skins,
    }
