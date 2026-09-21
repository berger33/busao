class_name ObstacleData
extends RefCounted
## Contrato de assets 3D do mundo: nenhum obstáculo jogável é 2D ou vazio.
## Os assemblies de veículos/props continuam leves, enquanto pessoas e animais
## usam adaptadores 3D próprios e meshes nomeados para inspeção.

const CATALOG: Array[Dictionary] = [
    {"id": "car", "space": "road", "kind": "vehicle", "builder": "_build_road_obstacle", "asset": "brazilian_car_assembly"},
    {"id": "bus_traffic", "space": "road", "kind": "vehicle", "builder": "_build_road_obstacle", "asset": "bus_assembly"},
    {"id": "motorcycle", "space": "road", "kind": "vehicle", "builder": "_build_road_obstacle", "asset": "motorcycle_assembly"},
    {"id": "pothole", "space": "road", "kind": "surface_hazard", "builder": "_build_road_obstacle", "asset": "pothole_mesh"},
    {"id": "truck", "space": "road", "kind": "vehicle", "builder": "_build_road_obstacle", "asset": "truck_assembly"},
    {"id": "old_lady", "space": "sidewalk", "kind": "pedestrian", "builder": "_build_pedestrian_obstacle", "asset": "quaternius_skinned_female"},
    {"id": "hydrant", "space": "sidewalk", "kind": "street_prop", "builder": "_build_sidewalk_obstacle", "asset": "hydrant_assembly"},
    {"id": "payphone", "space": "sidewalk", "kind": "street_prop", "builder": "_build_sidewalk_obstacle", "asset": "payphone_assembly"},
    {"id": "dog", "space": "sidewalk", "kind": "animal", "builder": "_build_animal_obstacle", "asset": "caramelo_animal_3d"},
    {"id": "bicycle", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "bicycle_assembly"},
    {"id": "cone", "space": "sidewalk", "kind": "construction_prop", "builder": "_build_sidewalk_obstacle", "asset": "traffic_cone_assembly"},
    {"id": "barrier", "space": "sidewalk", "kind": "construction_prop", "builder": "_build_sidewalk_obstacle", "asset": "barrier_assembly"},
    {"id": "vendor", "space": "sidewalk", "kind": "pedestrian", "builder": "_build_pedestrian_obstacle", "asset": "quaternius_skinned_human_rotating"},
    {"id": "bench", "space": "sidewalk", "kind": "street_prop", "builder": "_build_sidewalk_obstacle", "asset": "bench_assembly"},
    {"id": "trash", "space": "sidewalk", "kind": "street_prop", "builder": "_build_sidewalk_obstacle", "asset": "trash_assembly"},
    {"id": "crosser", "space": "sidewalk", "kind": "pedestrian", "builder": "_build_sidewalk_obstacle", "asset": "crosser_assembly"},
    {"id": "cart", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "cart_assembly"},
    {"id": "van", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "van_assembly"},
    {"id": "scaffold", "space": "sidewalk", "kind": "construction_prop", "builder": "_build_sidewalk_obstacle", "asset": "scaffold_assembly"},
    {"id": "puddle", "space": "sidewalk", "kind": "surface_hazard", "builder": "_build_sidewalk_obstacle", "asset": "puddle_mesh"},
    {"id": "planter", "space": "sidewalk", "kind": "street_prop", "builder": "_build_sidewalk_obstacle", "asset": "planter_assembly"},
    {"id": "cyclist", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "cyclist_assembly"},
    {"id": "moto_cross", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "moto_cross_assembly"},
    {"id": "dog_cross", "space": "sidewalk", "kind": "animal", "builder": "_build_sidewalk_obstacle", "asset": "caramelo_crossing"},
    {"id": "crate", "space": "sidewalk", "kind": "construction_prop", "builder": "_build_sidewalk_obstacle", "asset": "crate_assembly"},
    {"id": "truck_cross", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "truck_cross_assembly"},
    {"id": "bus_cross", "space": "sidewalk", "kind": "vehicle_prop", "builder": "_build_sidewalk_obstacle", "asset": "bus_cross_assembly"},
]

const COLLECTIBLE_IDS: Array[String] = [
    "coin", "coffee", "bread", "pastel", "sugarcane", "pass", "golden",
    "coxinha", "guarana", "pix", "umbrella",
]

const SCENERY_IDS: Array[String] = [
    "house", "building", "shopfront", "construction", "guard_post", "church",
    "tourist_kiosk", "terminal", "market_stall", "colonial_facade", "tree", "palm",
    "water_tank", "clothesline", "gate", "billboard", "lamp", "bus_stop",
]

static func all() -> Array[Dictionary]:
    var output: Array[Dictionary] = []
    for item in CATALOG:
        output.append(item.duplicate(true))
    return output

static func road_ids() -> Array[String]:
    var output: Array[String] = []
    for item in CATALOG:
        if str(item.get("space", "")) == "road":
            output.append(str(item.get("id", "")))
    return output

static func sidewalk_ids() -> Array[String]:
    var output: Array[String] = []
    for item in CATALOG:
        if str(item.get("space", "")) == "sidewalk":
            output.append(str(item.get("id", "")))
    return output

static func entry(id: String) -> Dictionary:
    for item in CATALOG:
        if str(item.get("id", "")) == id:
            return item.duplicate(true)
    return {}
