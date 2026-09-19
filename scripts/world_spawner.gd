extends RefCounted
class_name WorldSpawner
## WorldSpawner — P2 refactor
## Extrai a lógica de spawn do game_3d.gd para isolar curso e tráfego.
## Mantém constantes de validação espelhadas para audit (LANE_X etc).

const LANE_X: Array[float] = [-3.25, 0.0, 3.25]
const ROAD_LANE := 0
const SIDEWALK_CENTER := 1
const SIDEWALK_RIGHT := 2
const ROAD_OBSTACLES: Array[String] = ["car", "car", "motorcycle", "pothole", "bus_traffic", "car", "truck"]
const SIDEWALK_OBSTACLES: Array[String] = ["old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench"]
const COLLECTIBLES: Dictionary = {"coin": "R$ 0,25", "coffee": "CAFÉ", "bread": "PÃO DE QUEIJO", "pastel": "PASTEL", "sugarcane": "CALDO DE CANA", "pass": "VALE-TRANSPORTE", "golden": "BILHETE DOURADO", "coxinha": "COXINHA", "guarana": "GUARANÁ", "pix": "PIX TURBO", "umbrella": "GUARDA-CHUVA"}

# Chamado por game_3d._build_course antes do spawn para limpar decals; o spawn
# de tráfego e coletáveis continua em game_3d (delegação progressiva).
static func road_interval_for(obstacle_count: int) -> float:
    return clampf(26.0 - float(obstacle_count), 6.0, 24.0)

static func sidewalk_interval_for(road_interval: float) -> float:
    return maxf(15.0, road_interval * 2.1)

static func traffic_speed_for(kind: String, seed_index: int) -> float:
    var base: float = {"car": 2.3, "bus_traffic": 1.35, "motorcycle": 3.8, "truck": 1.05}.get(kind, 0.0)
    return base + float(seed_index % 3) * 0.42

static func bonus_kind_for_phase(phase_index: int, distance: float) -> String:
    var options: Array[String] = ["coffee", "bread", "pastel", "sugarcane", "pass"]
    if phase_index >= 19:
        options.append("golden")
    if phase_index >= 20:
        options.append("coxinha")
        options.append("guarana")
        options.append("pix")
        options.append("umbrella")
    return options[(phase_index + int(distance)) % options.size()]

static func forced_gags_for(phase_index: int) -> Array[String]:
    match phase_index:
        1: return ["bread", "hydrant"]
        3: return ["vendor", "pothole"]
        5: return ["vendor", "bicycle"]
        6: return ["bus_traffic", "dog"]
        7: return ["cone", "pothole"]
        8: return ["pothole", "car", "pothole"]
        9: return ["motorcycle", "old_lady"]
        10: return ["dog", "dog", "old_lady"]
        13: return ["dog", "bicycle"]
        14: return ["hydrant", "pothole"]
        17: return ["truck", "cone"]
        18: return ["dog", "motorcycle", "truck"]
        19: return ["truck", "bus_traffic", "dog", "payphone", "motorcycle"]
        _: pass
    if phase_index >= 20:
        return [["bus_traffic", "pix", "motorcycle", "hydrant", "dog"],["car", "umbrella", "dog", "payphone", "bus_traffic"],["motorcycle", "bicycle", "pothole", "vendor", "dog"],["truck", "car", "dog", "umbrella", "motorcycle"],["bus_traffic", "pothole", "vendor", "truck", "dog"],["car", "payphone", "motorcycle", "hydrant", "truck"]][mini(5, int(float(phase_index - 20) / 5.0))]
    return ["car", "cone"]

# Decals de rua (P2): manchas de asfalto e bueiros como discos sobre a pista do BuildingKit.
# Chamado após _setup_world_kit com o total do capítulo. Usa o decor_root do jogo
# para que os discos rolem com o curso (course_root.position.z = distance).
static func spawn_street_decals(game: Node3D, total_length: float) -> void:
    if game == null:
        return
    var decor: Node3D = game.get("decor_root")
    if decor == null:
        return
    # Y ligeiramente acima do topo da pista do kit (kit topo ~ WORLD_Y_OFFSET). Evita z-fighting.
    var y_patch: float = float(game.get("WORLD_Y_OFFSET")) + 0.06 if game.get("WORLD_Y_OFFSET") != null else -0.09
    var y_manhole: float = y_patch + 0.015
    var world_len: float = total_length + 80.0
    # Material factories delegadas ao game (_material) para manter paleta PBR
    var total: int = int(world_len / 14.0)
    for i in total:
        var z: float = -float(i) * 14.0 - 6.0
        if z < -total_length - 12.0 or z > 6.0:
            continue
        if i % 3 == 0:
            if game.has_method("_build_asphalt_patch"):
                game.call("_build_asphalt_patch", Vector3(LANE_X[ROAD_LANE], y_patch, z), 0.72 + float(i % 2) * 0.24)
        if i % 7 == 2:
            if game.has_method("_build_manhole"):
                game.call("_build_manhole", Vector3(LANE_X[ROAD_LANE], y_manhole, z - 3.2))
