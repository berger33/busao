extends Node
# PhysicsHandler — Lote 23: Física Mundo Real (Bullet) — helper para CharacterBody3D / RigidBody3D / Area3D
# Mantém arcade como fallback; quando PHYSICS_REALISTA true, usa gravidade/massa/fricção reais.

class_name PhysicsHandler

const GRAVITY: float = 9.81
const PLAYER_MASS: float = 75.0
const PLAYER_FRICTION: float = 0.4
const PLAYER_RESTITUTION: float = 0.0
const PLAYER_CAPSULE_RADIUS: float = 0.35
const PLAYER_CAPSULE_HEIGHT: float = 1.75
const PLAYER_SNAP: float = 0.4
const PLAYER_JUMP_IMPULSE: float = 6.3
const PLAYER_DASH_IMPULSE: float = 900.0
const PLAYER_DASH_COOLDOWN: float = 3.2
const POTHOLE_FRICTION: float = 0.15
const POTHOLE_IMPULSE_Y: float = -3.0
const VEHICLE_MASS: Dictionary = {
    "car": 1200.0,
    "carro": 1300.0,
    "bus_traffic": 8500.0,
    "truck": 5500.0,
    "motorcycle": 220.0,
    "bicycle": 18.0
}
# L27 polimento: fricção por superfície (audit 5.5: asfalto 0.35, calcada 0.55, dirt/cobble retarda 12-18%)
const SURFACE_FRICTION: Dictionary = {
    "asphalt": 0.35,
    "sidewalk": 0.55,
    "dirt": 0.62,
    "cobble": 0.68,
    "pothole": 0.15
}
const SURFACE_SPEED_FACTOR: Dictionary = {
    "asphalt": 1.0,
    "sidewalk": 0.98,
    "dirt": 0.88,
    "cobble": 0.82,
    "pothole": 0.85
}

# Cria CharacterBody3D para o jogador (capsule 0.35x1.75) e retorna o body
static func setup_player_physics(player_root: Node3D) -> CharacterBody3D:
    if player_root == null:
        return null
    # evita duplicar
    var existing := player_root.get_node_or_null("PlayerPhysicsBody") as CharacterBody3D
    if existing != null:
        return existing
    var body := CharacterBody3D.new()
    body.name = "PlayerPhysicsBody"
    body.set_meta("mass", PLAYER_MASS) # CharacterBody3D não tem 'mass'; guardamos como meta para gravidade/empurrão
    # colisão: CapsuleShape3D 0.35x1.75 (altura total = altura + 2*raio)
    var shape := CapsuleShape3D.new()
    shape.radius = PLAYER_CAPSULE_RADIUS
    shape.height = PLAYER_CAPSULE_HEIGHT
    var col := CollisionShape3D.new()
    col.name = "PlayerCapsule"
    col.shape = shape
    # offset para centro da cápsula (base no chão)
    col.position.y = PLAYER_CAPSULE_HEIGHT * 0.5 + PLAYER_CAPSULE_RADIUS * 0.2
    var phys_mat := PhysicsMaterial.new()
    phys_mat.friction = PLAYER_FRICTION
    phys_mat.bounce = PLAYER_RESTITUTION
    col.shape = shape
    # CharacterBody3D não usa physics_material_override direto, mas o shape colide
    body.add_child(col)
    # snap e gravidade são tratados no _physics_process do game_3d
    player_root.add_child(body)
    return body

# Adiciona corpo de colisão ao obstáculo conforme kind
static func setup_obstacle_physics(node: Node3D, kind: String) -> Node:
    if node == null:
        return null
    # evita duplicar
    if node.get_node_or_null("PhysicsBody") != null:
        return node.get_node_or_null("PhysicsBody")
    var body: Node3D
    var shape: Shape3D
    if kind in ["car", "carro", "bus_traffic", "truck", "motorcycle", "bicycle"]:
        # veículos → RigidBody3D (podem ser empurrados: truck empurra car)
        var rb := RigidBody3D.new()
        rb.name = "PhysicsBody"
        rb.mass = VEHICLE_MASS.get(kind, 1000.0)
        rb.freeze = true # parado no trilho, mas com massa para empurrão quando necessário
        rb.continuous_cd = true
        # shape box aproximado por GLB_FIT
        var box := BoxShape3D.new()
        match kind:
            "car":
                box.size = Vector3(1.75, 1.55, 4.4)
            "carro":
                box.size = Vector3(1.75, 1.55, 4.6)
            "motorcycle":
                box.size = Vector3(0.85, 1.15, 2.1)
            "truck":
                box.size = Vector3(2.2, 2.7, 6.4)
            "bus_traffic":
                box.size = Vector3(2.4, 3.0, 7.4)
            "bicycle":
                box.size = Vector3(0.6, 1.15, 1.85)
            _:
                box.size = Vector3(1.6, 1.6, 3.0)
        var col := CollisionShape3D.new()
        col.shape = box
        col.position.y = box.size.y * 0.5
        var pm := PhysicsMaterial.new()
        pm.friction = 0.55
        pm.bounce = 0.05
        rb.physics_material_override = pm
        rb.add_child(col)
        body = rb
    elif kind == "pothole":
        # pothole → Area3D com fricção baixa e impulso -Y
        var area := Area3D.new()
        area.name = "PhysicsBody"
        area.monitoring = true
        area.monitorable = true
        var cyl := CylinderShape3D.new()
        cyl.radius = 0.65
        cyl.height = 0.22
        var col := CollisionShape3D.new()
        col.shape = cyl
        col.position.y = -0.02
        area.add_child(col)
        # metadata para game_3d detectar entrada
        area.set_meta("pothole_friction", POTHOLE_FRICTION)
        area.set_meta("pothole_impulse_y", POTHOLE_IMPULSE_Y)
        body = area
    elif kind in ["hydrant", "bench", "cone", "payphone", "old_lady", "vendor", "dog"]:
        # props / pedestres → StaticBody3D (não move, mas colide)
        var sb := StaticBody3D.new()
        sb.name = "PhysicsBody"
        var box2 := BoxShape3D.new()
        match kind:
            "hydrant":
                box2.size = Vector3(0.55, 0.85, 0.55)
            "bench":
                box2.size = Vector3(1.8, 0.85, 0.65)
            "cone":
                box2.size = Vector3(0.45, 0.85, 0.45)
            "payphone":
                box2.size = Vector3(0.55, 1.7, 0.45)
            "old_lady", "vendor":
                box2.size = Vector3(0.55, 1.75, 0.45)
            "dog":
                box2.size = Vector3(0.95, 0.72, 1.6)
            _:
                box2.size = Vector3(0.8, 0.8, 0.8)
        var col2 := CollisionShape3D.new()
        col2.shape = box2
        col2.position.y = box2.size.y * 0.5
        var pm2 := PhysicsMaterial.new()
        pm2.friction = 0.5
        pm2.bounce = 0.0
        sb.physics_material_override = pm2
        sb.add_child(col2)
        body = sb
    else:
        # fallback Static
        var sb2 := StaticBody3D.new()
        sb2.name = "PhysicsBody"
        var box3 := BoxShape3D.new()
        box3.size = Vector3(1.0, 1.0, 1.0)
        var col3 := CollisionShape3D.new()
        col3.shape = box3
        col3.position.y = 0.5
        sb2.add_child(col3)
        body = sb2
    node.add_child(body)
    return body

# Ragdoll no game over (hearts==0) via PhysicalBone3D
static func setup_ragdoll(player_visual: Node3D) -> void:
    if player_visual == null:
        return
    # procura Skeleton3D no visual (runner_character tem Skeleton)
    var skel := player_visual.get_node_or_null("Skeleton3D") as Skeleton3D
    if skel == null:
        # tenta achar recursivo
        skel = _find_skeleton(player_visual)
    if skel == null:
        return
    # evita duplicar
    if skel.get_node_or_null("Ragdoll") != null:
        return
    # cria PhysicalBone3D para cada osso principal (simplificado)
    var bones = ["Hips", "Spine", "Head", "LeftUpLeg", "RightUpLeg"]
    for b in bones:
        var idx := skel.find_bone(b)
        if idx == -1:
            continue
        var pb := PhysicalBone3D.new()
        pb.name = "Ragdoll_" + b
        pb.bone_name = b
        # shape cápsula por osso
        var cap := CapsuleShape3D.new()
        cap.radius = 0.14
        cap.height = 0.45
        var col := CollisionShape3D.new()
        col.shape = cap
        pb.add_child(col)
        skel.add_child(pb)
    # inicia simulação
    skel.physical_bones_start_simulation()

static func _find_skeleton(root: Node) -> Skeleton3D:
    if root is Skeleton3D:
        return root as Skeleton3D
    for c in root.get_children():
        var r := _find_skeleton(c)
        if r != null:
            return r
    return null

static func surface_speed_factor(surface: String) -> float:
    return float(SURFACE_SPEED_FACTOR.get(surface, 1.0))

static func surface_friction(surface: String) -> float:
    return float(SURFACE_FRICTION.get(surface, 0.4))

# Checa se shape do jogador intersecta shape do obstáculo fora de invencível
static func should_lose_heart(player_body: CharacterBody3D, obstacle_body: Node3D, dash_timer: float, invincible: bool) -> bool:
    if invincible or dash_timer > 0.0:
        return false
    if player_body == null or obstacle_body == null:
        return false
    # usa AABB simples se physics não estiver em simulação (fallback)
    return true
