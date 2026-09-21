class_name PatternValidator
extends RefCounted
## ETAPA 4 — validador de caminho (blueprint §7).
##
## Para cada nível, calcula se existe pelo menos uma sequência legal de
## ações do começo ao fim, considerando o estado do jogador: corredor,
## posição lateral durante a troca, ação em andamento (pulo/deslize) e o
## tempo que cada ação ocupa. Não basta um corredor vazio por fotografia:
## é preciso chegar até ele no tempo disponível.
##
## Modelo: trocar de corredor ocupa SWITCH_S por corredor e precisa começar
## livre, antes da estação; a transição completa-se na estação. Com
## corredores a 3,25 m e larguras de colisão <= 1,4 m, o meio do caminho
## entre corredores é geometricamente seguro, então estações consecutivas
## só precisam respeitar o tempo da troca. Pulo/deslize ocupam a faixa até
## o fim da duração e podem cobrir estações seguintes dentro da mesma ação.
##
## Uso: PatternValidator.validate(level) -> {valid, reason, route}
## validate() roda na velocidade base e com impulso máximo (1,22x), como
## pede o blueprint ("revalidar na velocidade máxima").

const OBSTACLE_RULES = preload("res://scripts/obstacle_rules.gd")

const SWITCH_S := 0.25          # transição de corredor (blueprint §4)
const JUMP_S := 0.9             # duração do pulo
const SLIDE_S := 0.72           # duração do deslize
const BOOST_FACTOR := 1.22      # impulso máximo (velocidade de revalidação)
const STATION_TOLERANCE_M := 2.0


static func validate(level: Dictionary) -> Dictionary:
    var base_speed: float = float(level.get("base_speed_mps", 6.0))
    for factor in [1.0, BOOST_FACTOR]:
        var result: Dictionary = _validate_at_speed(level, base_speed * factor)
        if not bool(result.get("valid", false)):
            result["speed_factor"] = factor
            return result
    var full: Dictionary = _validate_at_speed(level, base_speed)
    full["speed_factor"] = 1.0
    return full


static func _validate_at_speed(level: Dictionary, speed: float) -> Dictionary:
    var stations: Array = _stations_from(level)
    if stations.is_empty():
        return {"valid": true, "reason": "sem obstáculos", "route": []}
    var route: Array = []
    if _search(stations, 0, 1, -1.0, "", -1.0, speed, route):
        return {"valid": true, "reason": "rota legal encontrada", "route": route}
    return {"valid": false, "reason": "nenhuma sequência legal de ações", "route": []}


## Agrupa padrões por estação (obstáculos a menos de STATION_TOLERANCE_M
## chegam juntos e precisam ser resolvidos de uma vez).
static func _stations_from(level: Dictionary) -> Array:
    var obstacles: Array = []
    for p in level.get("patterns", []):
        obstacles.append({
            "kind": str(p.get("kind", "")),
            "lane": int(p.get("lane", 1)),
            "at_m": float(p.get("at_m", 0.0)),
            "classe": OBSTACLE_RULES.classe_for(str(p.get("kind", ""))),
        })
    obstacles.sort_custom(func(a, b): return float(a["at_m"]) < float(b["at_m"]))
    var stations: Array = []
    for o in obstacles:
        if stations.is_empty() or float(o["at_m"]) - float(stations.back()["at_m"]) > STATION_TOLERANCE_M:
            stations.append({"at_m": float(o["at_m"]), "obstacles": [o]})
        else:
            stations.back()["obstacles"].append(o)
    return stations


## Ação única que cobre todos os obstáculos da lista na mesma faixa:
## "jump", "slide", "free" (não precisa de ação) ou "none" (impossível).
static func _action_for(obstacles: Array) -> String:
    var needs_jump := false
    var needs_slide := false
    for o in obstacles:
        var classe: int = int(o["classe"])
        if OBSTACLE_RULES.jump_clears(classe):
            needs_jump = true
        elif OBSTACLE_RULES.slide_clears(classe):
            needs_slide = true
        else:
            return "none"  # FULL/VEHICLE: nenhuma ação resolve nesta faixa
    if needs_jump and needs_slide:
        return "none"  # duas ações incompatíveis na mesma faixa e estação
    if needs_jump:
        return "jump"
    if needs_slide:
        return "slide"
    return "free"


static func _search(stations: Array, i: int, lane: int, busy_until: float,
        last_action: String, last_action_end: float, speed: float,
        route: Array) -> bool:
    if i >= stations.size():
        return true
    var station: Dictionary = stations[i]
    var at_m: float = float(station["at_m"])
    for target_lane in range(3):
        var steps: int = absi(target_lane - lane)
        # A troca começa livre, antes da estação, e termina nela.
        var change_start: float = at_m - speed * SWITCH_S * float(steps)
        if steps > 0 and busy_until > change_start:
            continue
        var in_lane: Array = []
        for o in station["obstacles"]:
            if int(o["lane"]) == target_lane:
                in_lane.append(o)
        var decision_action := ""
        var next_busy: float = busy_until if steps == 0 else at_m
        var next_action: String = last_action
        var next_action_end: float = last_action_end
        if in_lane.is_empty():
            decision_action = "pass"
        elif _covered_by_last(in_lane, last_action, last_action_end, at_m):
            # Ainda no ar/deslize da ação anterior: atravessa sem agir.
            decision_action = "carry"
        else:
            var action: String = _action_for(in_lane)
            if action == "none" or next_busy > at_m:
                continue
            var duration: float = JUMP_S if action == "jump" else SLIDE_S
            decision_action = action
            next_busy = at_m + speed * duration
            next_action = action
            next_action_end = next_busy
        route.append({"at_m": at_m, "lane": target_lane, "action": decision_action})
        if _search(stations, i + 1, target_lane, next_busy, next_action, next_action_end, speed, route):
            return true
        route.pop_back()
    return false


## Os obstáculos ficam cobertos pela ação anterior ainda ativa em at_m?
static func _covered_by_last(obstacles: Array, last_action: String, last_action_end: float, at_m: float) -> bool:
    if last_action_end <= at_m:
        return false
    for o in obstacles:
        var classe: int = int(o["classe"])
        if last_action == "jump" and OBSTACLE_RULES.jump_clears(classe):
            continue
        if last_action == "slide" and OBSTACLE_RULES.slide_clears(classe):
            continue
        return false
    return true
