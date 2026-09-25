extends RefCounted
class_name EconomyHandler
## EconomyHandler — P2 refactor
## Isola cálculos de recompensa, XP e progressão diária/semanal.
## Mantém BALANCE espelhado e delega persistência ao GameSave.

const BAL_REF := preload("res://resources/game_balance.tres")

static func phase_stars(no_damage: bool, collected: int, coin_target: int) -> int:
    var s := 1
    if no_damage: s += 1
    if collected >= coin_target: s += 1
    return s

static func phase_reward(first_clear: bool, phase_index: int, stars: int, new_stars: int, no_damage: bool) -> Dictionary:
    var balance = BAL_REF
    var base_reward: int = int(balance.first_clear_reward) if first_clear else int(balance.replay_reward)
    var level_reward: int = phase_index * int(balance.phase_reward_per_level) if first_clear else 0
    var star_reward: int = stars * int(balance.star_reward) if first_clear else new_stars * int(balance.star_upgrade_reward)
    var perfect_reward: int = int(balance.perfect_run_bonus) if no_damage and first_clear else 0
    var total: int = base_reward + level_reward + star_reward + perfect_reward
    var xp: int = (int(balance.xp_first_clear) + phase_index * int(balance.xp_per_level)) if first_clear else int(balance.xp_replay) + new_stars * 5
    return {"total": total, "xp": xp, "breakdown": {"base": base_reward, "level": level_reward, "stars": star_reward, "perfect": perfect_reward}}

static func endless_reward(distance: float, collected_coins: int, is_record: bool) -> Dictionary:
    var balance = BAL_REF
    var distance_bonus: int = mini(33, int(distance / 30.0))
    var first_score_reward: int = 20 + distance_bonus + mini(15, collected_coins)
    var reward: int = first_score_reward + (25 if is_record else 0)
    if not is_record:
        reward = mini(reward, int(balance.replay_reward) + distance_bonus)
    var xp: int = 40 + int(distance / 12.0) if is_record else int(balance.xp_replay)
    return {"reward": reward, "xp": xp}

static func apply_weekly_bonus(reward: int) -> int:
    var em = Engine.get_singleton("EconomyManager") if Engine.has_singleton("EconomyManager") else null
    # tenta autoload EconomyManager
    var node = null
    if Engine.has_singleton("EconomyManager"):
        node = Engine.get_singleton("EconomyManager")
    else:
        # fallback via root (Godot autoload fica em /root/EconomyManager)
        var tree := Engine.get_main_loop() as SceneTree
        if tree and tree.root:
            node = tree.root.get_node_or_null("/root/EconomyManager")
    if node and node.has_method("get_weekly_bonus_coins"):
        var extra: int = int(node.call("get_weekly_bonus_coins"))
        if extra > 0:
            return extra
    return 0

static func record_phase_success(game_save: Object, phase_index: int, stars: int, elapsed: float) -> Dictionary:
    if game_save == null or not game_save.has_method("record_phase"):
        return {"first_clear": false, "new_stars": 0}
    return game_save.call("record_phase", phase_index, stars, elapsed)

static func add_coins_and_xp(game_save: Object, coins: int, xp: int) -> void:
    if game_save == null: return
    if coins > 0 and game_save.has_method("add_coins"): game_save.call("add_coins", coins)
    if xp > 0 and game_save.has_method("add_xp"): game_save.call("add_xp", xp)
