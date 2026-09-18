extends Node3D
## Animal 3D de mundo com o mesmo contrato de poses do corredor humano:
## idle, run, jump e crouch (agachado parado ou em movimento). O cachorro
## caramelo mantém a anatomia original; as aves urbanas (pombo, passarinho,
## gaivota e urubu) ganham corpo articulado com asas, cabeça, cauda e patas
## para que TODAS as posições existam em cada espécie.

const TEXTURE_FUR = preload("res://assets/textures/pele_suave.svg")
const TEXTURE_RUBBER = preload("res://assets/textures/borracha.svg")
const TEXTURE_METAL = preload("res://assets/textures/metal_pintado.svg")
const TEXTURE_FEATHER = preload("res://assets/textures/tecido_urbano.svg")

const BIRD_PROFILES: Dictionary = {
    "pombo": {"body": Color("#8d95a5"), "wing": Color("#6f7889"), "beak": Color("#454b5e"), "size": 0.9, "span": 0.42, "flap": 7.6, "legs": Color("#c56b4a")},
    "passaro": {"body": Color("#7c6a4b"), "wing": Color("#5d4f39"), "beak": Color("#3a352d"), "size": 0.62, "span": 0.34, "flap": 10.5, "legs": Color("#8a6a4a")},
    "gaivota": {"body": Color("#f2efe2"), "wing": Color("#d9d4c4"), "beak": Color("#e8a13c"), "size": 1.0, "span": 0.60, "flap": 5.4, "legs": Color("#e8a13c")},
    "urubu": {"body": Color("#36322f"), "wing": Color("#211e1c"), "beak": Color("#9aa0a8"), "size": 1.15, "span": 0.76, "flap": 3.6, "legs": Color("#6b6f75")},
}

var species: String = "caramelo"
var fur_color := Color("#b8794d")
var body_root: Node3D
var tail: Node3D
var head: Node3D
var legs: Array[Node3D] = []
var leg_is_front: Array[bool] = []
var wings: Array[Node3D] = []
var motion_time := 0.0
var running := false

# ---- contrato de poses (espelha o runner_character.gd) ----
var pose_state := "idle" # idle | run | jump | crouch
var pose_hold := 0.0
var return_state := "idle"
var crouch_moving := false

# ---- comportamentos autônomos ----
var dog_chasing := false
var chase_hop_timer := 0.0
var behavior_mode := "" # "" | flight | ground
var behavior_timer := 0.0
var rng := RandomNumberGenerator.new()

func configure(next_species: String = "caramelo") -> void:
    species = next_species

func _ready() -> void:
    rng.seed = hash(species) + get_instance_id()
    if species == "caramelo":
        _build_caramelo()
    elif BIRD_PROFILES.has(species):
        _build_bird()
    else:
        _build_bird()

func _process(delta: float) -> void:
    motion_time += delta
    if pose_hold > 0.0:
        pose_hold -= delta
        if pose_hold <= 0.0:
            _enter_pose(return_state)
    if dog_chasing and pose_state == "run":
        chase_hop_timer -= delta
        if chase_hop_timer <= 0.0:
            _enter_pose("jump", 0.42, "run")
            chase_hop_timer = 1.25 + float(get_instance_id() % 5) * 0.12
    if behavior_mode != "" and pose_hold <= 0.0:
        behavior_timer -= delta
        if behavior_timer <= 0.0:
            _step_behavior()
    if species == "caramelo":
        _animate_caramelo()
    else:
        _animate_bird()

## Mesmo contrato do corredor: pulo vence, depois agachamento (parado ou
## em movimento), depois corrida e por fim parado.
func set_motion(is_running: bool, is_crouching: bool, jump_height: float) -> void:
    if jump_height > 0.05:
        _enter_pose("jump", 0.45, "run" if is_running and not is_crouching else "idle")
    elif is_crouching:
        crouch_moving = is_running
        _enter_pose("crouch")
    elif is_running:
        _enter_pose("run")
    else:
        _enter_pose("idle")

func set_pose(next_state: String, hold := 0.0, return_to := "") -> void:
    _enter_pose(next_state, hold, return_to)

## Compatibilidade com a perseguição do caramelo: agora dispara a sequência
## completa — reverência (play bow) antes de correr, com saltinhos de empolgação.
func set_running(value: bool) -> void:
    if value:
        dog_chasing = true
        crouch_moving = false
        chase_hop_timer = 1.3
        _enter_pose("crouch", 0.6, "run")
    else:
        dog_chasing = false
        _enter_pose("idle")

func enable_flight_cycle() -> void:
    behavior_mode = "flight"
    _enter_pose("run")
    behavior_timer = 2.2 + float(get_instance_id() % 7) * 0.2

func enable_ground_behavior() -> void:
    behavior_mode = "ground"
    _enter_pose("idle")
    behavior_timer = 1.5 + float(get_instance_id() % 9) * 0.3

func _enter_pose(next_state: String, hold := 0.0, return_to := "") -> void:
    pose_state = next_state
    pose_hold = maxf(0.0, hold)
    return_state = return_to if not return_to.is_empty() else next_state
    crouch_moving = crouch_moving if next_state == "crouch" else false
    running = next_state == "run" or (next_state == "crouch" and crouch_moving)

func _step_behavior() -> void:
    if behavior_mode == "flight":
        if pose_state == "run":
            _enter_pose("idle") # planeio com asas coladas
            behavior_timer = 0.7 + float(get_instance_id() % 3) * 0.15
        else:
            _enter_pose("run")
            behavior_timer = 2.4 + float(get_instance_id() % 7) * 0.25
    elif behavior_mode == "ground":
        match pose_state:
            "idle":
                if rng.randf() < 0.18:
                    _enter_pose("jump", 0.4, "run") # susto: pula e sai correndo
                    behavior_timer = 0.5
                else:
                    _enter_pose("crouch") # bicando o chão
                    behavior_timer = rng.randf_range(1.2, 2.2)
            "crouch":
                _enter_pose("idle")
                behavior_timer = rng.randf_range(2.0, 4.0)
            "jump":
                _enter_pose("run")
                behavior_timer = rng.randf_range(0.9, 1.6)
            _:
                _enter_pose("idle")
                behavior_timer = rng.randf_range(2.0, 4.0)

func _animate_caramelo() -> void:
    if tail:
        match pose_state:
            "jump":
                tail.rotation.z = -1.12 # cauda esticada para trás no salto
            "crouch":
                tail.rotation.z = -0.50 + sin(motion_time * 9.0) * 0.30 # rabo baixo acelerado
            _:
                tail.rotation.z = -0.72 + sin(motion_time * (8.0 if running else 3.8)) * (0.22 if running else 0.13)
    for index in legs.size():
        var leg := legs[index]
        var front: bool = leg_is_front[index] if index < leg_is_front.size() else true
        match pose_state:
            "jump":
                leg.rotation.x = 0.0
                # dianteiras recolhidas sob o corpo, traseiras esticadas para trás
                leg.rotation.z = -0.30 if front else -0.55
            "crouch":
                leg.rotation.x = 0.0
                # reverência: dianteiras dobradas, traseiras quase plantadas
                leg.rotation.z = -0.45 if front else -0.05
            _:
                leg.rotation.z = 0.0
                leg.rotation.x = sin(motion_time * (10.0 if running else 2.8) + float(index) * PI) * (0.18 if running else 0.035)
    if body_root:
        match pose_state:
            "jump":
                body_root.position.y = 0.055
                body_root.rotation.z = 0.12 # focinho para cima
            "crouch":
                body_root.position.y = -0.085
                body_root.rotation.z = -0.10 # frente baixa em reverência
            _:
                body_root.position.y = sin(motion_time * (8.0 if running else 2.0)) * (0.025 if running else 0.008)
                body_root.rotation.z = 0.0

func _animate_bird() -> void:
    if body_root == null or wings.size() < 2:
        return
    var profile: Dictionary = BIRD_PROFILES.get(species, BIRD_PROFILES["pombo"])
    var flap_speed: float = float(profile.get("flap", 7.0))
    var left: Node3D = wings[0]
    var right: Node3D = wings[1]
    match pose_state:
        "run":
            # voo: bate asas com o corpo nivelado e patas recolhidas
            var flap: float = sin(motion_time * flap_speed) * 0.58
            left.rotation.z = -flap
            right.rotation.z = flap
            left.rotation.y = 0.0
            right.rotation.y = 0.0
            body_root.position.y = sin(motion_time * flap_speed) * 0.012
            body_root.rotation.x = -0.05
            if head:
                head.rotation.x = 0.0
            for leg in legs:
                leg.rotation.x = 1.05
            if tail:
                tail.rotation.x = 0.0
        "idle":
            # pousado: asas coladas ao corpo, cabeça balançando, cauda viva
            left.rotation.z = 0.10
            right.rotation.z = -0.10
            left.rotation.y = -0.55
            right.rotation.y = 0.55
            body_root.position.y = 0.0
            body_root.rotation.x = 0.06
            if head:
                head.rotation.x = -0.06 + sin(motion_time * 2.4) * 0.16
            for leg in legs:
                leg.rotation.x = 0.0
            if tail:
                tail.rotation.x = -0.06 + sin(motion_time * 3.1) * 0.05
        "jump":
            # decolagem: asas erguidas, corpo empinado, patas esticadas
            left.rotation.z = -0.95
            right.rotation.z = 0.95
            left.rotation.y = 0.0
            right.rotation.y = 0.0
            body_root.position.y = 0.05
            body_root.rotation.x = -0.20
            if head:
                head.rotation.x = 0.0
            for leg in legs:
                leg.rotation.x = 0.55
            if tail:
                tail.rotation.x = 0.10
        "crouch":
            # agachado/bicando: corpo baixo, cabeça no chão, cauda erguida
            left.rotation.z = 0.06
            right.rotation.z = -0.06
            left.rotation.y = -0.12
            right.rotation.y = 0.12
            body_root.position.y = -0.045
            body_root.rotation.x = 0.10
            if head:
                head.rotation.x = 0.55
            for leg in legs:
                leg.rotation.x = -0.15
            if tail:
                tail.rotation.x = -0.22

func _build_caramelo() -> void:
    body_root = Node3D.new()
    body_root.name = "CarameloDog3D"
    add_child(body_root)
    var fur := _material(fur_color, TEXTURE_FUR, 0.82)
    var face := _material(Color("#c28656"), TEXTURE_FUR, 0.84)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.72)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.22)
    var inner_ear := _material(Color("#75412f"), TEXTURE_FUR, 0.88)
    var collar := _material(Color("#2e75a6"), TEXTURE_FUR, 0.46)
    var metal := _material(Color("#f0bd4a"), TEXTURE_METAL, 0.20, 0.82)

    _ellipsoid(body_root, Vector3(0.0, 0.56, 0.0), Vector3(0.72, 0.43, 0.50), fur, "DogBody")
    _ellipsoid(body_root, Vector3(0.40, 0.72, 0.0), Vector3(0.28, 0.30, 0.30), fur, "DogNeck")
    _ellipsoid(body_root, Vector3(0.53, 0.91, -0.04), Vector3(0.34, 0.31, 0.31), face, "DogHead")
    _ellipsoid(body_root, Vector3(0.77, 0.83, -0.20), Vector3(0.17, 0.14, 0.14), face, "DogMuzzle")
    _ellipsoid(body_root, Vector3(0.88, 0.84, -0.28), Vector3(0.07, 0.06, 0.05), dark, "DogNose")
    for side in [-1.0, 1.0]:
        _ellipsoid(body_root, Vector3(0.61, 0.99, side * 0.20), Vector3(0.055, 0.06, 0.055), eye, "DogEye")
        var ear := _ellipsoid(body_root, Vector3(0.43, 1.10, side * 0.19), Vector3(0.13, 0.22, 0.10), fur, "DogEar")
        ear.rotation.z = side * 0.18
        _ellipsoid(body_root, Vector3(0.43, 1.10, side * 0.205), Vector3(0.075, 0.14, 0.035), inner_ear, "DogEarInner")
    _torus(body_root, 0.20, 0.025, Vector3(0.40, 0.78, 0.0), collar, "DogCollar")
    _sphere(body_root, 0.065, Vector3(0.40, 0.62, -0.22), metal, "DogTag")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.075, 0.42, Vector3(front * 0.40, 0.27, side * 0.19), fur, "DogLeg")
            legs.append(leg)
            leg_is_front.append(front > 0.0)
            _ellipsoid(body_root, Vector3(front * 0.40, 0.06, side * 0.20), Vector3(0.10, 0.055, 0.12), dark, "DogPaw")
    tail = _capsule(body_root, 0.065, 0.46, Vector3(-0.67, 0.83, 0.13), fur, "DogTailBase")
    tail.rotation.z = -0.72
    var tail_tip := _ellipsoid(body_root, Vector3(-0.86, 1.00, 0.13), Vector3(0.10, 0.12, 0.10), fur, "DogTailTip")
    tail_tip.rotation.z = -0.36

func _build_bird() -> void:
    var profile: Dictionary = BIRD_PROFILES.get(species, BIRD_PROFILES["pombo"])
    var size: float = float(profile.get("size", 0.9))
    var span: float = float(profile.get("span", 0.42))
    body_root = Node3D.new()
    body_root.name = "Bird3D"
    add_child(body_root)
    body_root.scale = Vector3.ONE * size
    var feather := _material(profile.get("body", Color.GRAY), TEXTURE_FEATHER, 0.86)
    var wing_mat := _material(profile.get("wing", Color.DIM_GRAY), TEXTURE_FEATHER, 0.88)
    var beak_mat := _material(profile.get("beak", Color.BLACK), TEXTURE_RUBBER, 0.42)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.2)
    var leg_mat := _material(profile.get("legs", Color.BROWN), TEXTURE_RUBBER, 0.55)

    # Corpo orientado para +Z, a mesma direção das rotas aéreas do cenário.
    _ellipsoid(body_root, Vector3(0.0, 0.0, 0.02), Vector3(0.17, 0.15, 0.30), feather, "BirdBody")
    _ellipsoid(body_root, Vector3(0.0, 0.10, 0.05), Vector3(0.12, 0.11, 0.13), feather, "BirdBreast")

    head = Node3D.new()
    head.name = "BirdHeadPivot"
    head.position = Vector3(0.0, 0.15, 0.22)
    body_root.add_child(head)
    _ellipsoid(head, Vector3.ZERO, Vector3(0.10, 0.10, 0.10), feather, "BirdHead")
    _box(head, Vector3(0.045, 0.035, 0.11), Vector3(0.0, -0.01, 0.10), beak_mat, "BirdBeak")
    for side in [-1.0, 1.0]:
        _ellipsoid(head, Vector3(side * 0.055, 0.025, 0.04), Vector3(0.02, 0.02, 0.02), eye, "BirdEye")

    for side in [-1.0, 1.0]:
        var shoulder := Node3D.new()
        shoulder.name = "BirdShoulderL" if side < 0.0 else "BirdShoulderR"
        shoulder.position = Vector3(side * 0.11, 0.04, 0.0)
        body_root.add_child(shoulder)
        _box(shoulder, Vector3(span, 0.03, span * 0.46), Vector3(side * span * 0.5, 0.0, 0.0), wing_mat, "BirdWingL" if side < 0.0 else "BirdWingR")
        wings.append(shoulder)

    tail = Node3D.new()
    tail.name = "BirdTailPivot"
    tail.position = Vector3(0.0, 0.03, -0.24)
    body_root.add_child(tail)
    _box(tail, Vector3(0.15, 0.02, 0.24), Vector3(0.0, 0.0, -0.12), wing_mat, "BirdTail")

    for side in [-1.0, 1.0]:
        var leg := _capsule(body_root, 0.016, 0.14, Vector3(side * 0.05, -0.09, 0.0), leg_mat, "BirdLeg")
        legs.append(leg)
        leg_is_front.append(false)

func _material(color: Color, texture: Texture2D, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.albedo_texture = texture
    material.roughness = roughness
    material.metallic = metallic
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    if texture == TEXTURE_FUR:
        material.subsurf_scatter_enabled = true
        material.subsurf_scatter_skin_mode = true
        material.subsurf_scatter_strength = 0.06
    return material

func _mesh(parent: Node3D, node_name: String, mesh: Mesh, material: Material) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    node.mesh = mesh
    node.material_override = material
    node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
    node.receive_shadow = true
    parent.add_child(node)
    return node

func _ellipsoid(parent: Node3D, pos: Vector3, scale_value: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := SphereMesh.new()
    mesh.radius = 1.0
    mesh.height = 2.0
    mesh.radial_segments = 24
    mesh.rings = 14
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    node.scale = scale_value
    return node

func _sphere(parent: Node3D, radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    return _ellipsoid(parent, pos, Vector3.ONE * radius, material, node_name)

func _capsule(parent: Node3D, radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := CapsuleMesh.new()
    mesh.radius = radius
    mesh.height = height
    mesh.radial_segments = 16
    mesh.rings = 8
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    return node

func _box(parent: Node3D, size: Vector3, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := BoxMesh.new()
    mesh.size = size
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    return node

func _torus(parent: Node3D, inner_radius: float, outer_radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := TorusMesh.new()
    mesh.inner_radius = inner_radius
    mesh.outer_radius = outer_radius
    mesh.rings = 24
    mesh.ring_segments = 10
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    return node
