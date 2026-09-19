extends Node3D
## Animal 3D de mundo com o mesmo contrato de poses do corredor humano:
## idle, run, jump, crouch parado e crouch em movimento. O cachorro caramelo
## mantém a anatomia original; as aves urbanas (pombo, passarinho, gaivota e
## urubu) e os bichos do interior (capivara, cavalo, boi, macaco e caranguejo)
## compartilham o mesmo contrato para que TODAS as posições existam em cada
## espécie criada.

const TEXTURE_FUR = preload("res://assets/textures/pelo_realista.png")
const TEXTURE_FUR_N = preload("res://assets/textures/pelo_realista_normal.png")
const TEXTURE_FUR_R = preload("res://assets/textures/pelo_realista_roughness.png")
const TEXTURE_RUBBER = preload("res://assets/textures/borracha_realista.png")
const TEXTURE_RUBBER_N = preload("res://assets/textures/borracha_realista_normal.png")
const TEXTURE_RUBBER_R = preload("res://assets/textures/borracha_realista_roughness.png")
const TEXTURE_METAL = preload("res://assets/textures/metal_pintado_realista.png")
const TEXTURE_METAL_N = preload("res://assets/textures/metal_pintado_realista_normal.png")
const TEXTURE_METAL_R = preload("res://assets/textures/metal_pintado_realista_roughness.png")
const TEXTURE_FEATHER = preload("res://assets/textures/pena_realista.png")
const TEXTURE_FEATHER_N = preload("res://assets/textures/pena_realista_normal.png")
const TEXTURE_FEATHER_R = preload("res://assets/textures/pena_realista_roughness.png")

const BIRD_PROFILES: Dictionary = {
    "pombo": {"body": Color("#8d95a5"), "wing": Color("#6f7889"), "beak": Color("#454b5e"), "size": 0.9, "span": 0.42, "flap": 7.6, "legs": Color("#c56b4a")},
    "passaro": {"body": Color("#7c6a4b"), "wing": Color("#5d4f39"), "beak": Color("#3a352d"), "size": 0.62, "span": 0.34, "flap": 10.5, "legs": Color("#8a6a4a")},
    "gaivota": {"body": Color("#f2efe2"), "wing": Color("#d9d4c4"), "beak": Color("#e8a13c"), "size": 1.0, "span": 0.60, "flap": 5.4, "legs": Color("#e8a13c")},
    "urubu": {"body": Color("#36322f"), "wing": Color("#211e1c"), "beak": Color("#9aa0a8"), "size": 1.15, "span": 0.76, "flap": 3.6, "legs": Color("#6b6f75")},
}

# Quadrúpedes de interior: capivara se deita (lie), cavalo e boi pastam
# (crouch = cabeça no chão). O ciclo de pernas é o mesmo do caramelo.
const QUADRUPED_PROFILES: Dictionary = {
    "capivara": {"cycle": 8.5, "bob": 0.022, "lie": true, "crouch_head": 0.10},
    "cavalo": {"cycle": 7.5, "bob": 0.035, "lie": false, "crouch_head": -0.95},
    "boi": {"cycle": 6.0, "bob": 0.030, "lie": false, "crouch_head": -0.75},
}

# Tamanhos-alvo (m) de cada modelo GLB drop-in: [comprimento, altura]. O
# comprimento vira o eixo X no jogo (apois a rotação de 90°) e a altura o Y;
# o `_fit_glb` escala pelo bbox real do GLB para caber nesses valores.
# Espécie sem entrada aqui (ou sem .glb na pasta) usa o modelo procedural.
const GLB_SIZES: Dictionary = {
    "pombo": [0.26, 0.21],
    "passaro": [0.18, 0.11],
    "gaivota": [0.80, 0.46],
    "urubu": [1.30, 0.80],
    "caramelo": [0.95, 0.72],
    "capivara": [1.35, 0.62],
    "cavalo": [1.90, 1.45],
    "boi": [2.00, 1.50],
    "macaco": [0.85, 0.95],
    "caranguejo": [0.60, 0.30],
}

var species: String = "caramelo"
var fur_color := Color("#b8794d")
var body_root: Node3D
var tail: Node3D
var head: Node3D
var legs: Array[Node3D] = []
var leg_is_front: Array[bool] = []
var wings: Array[Node3D] = []
var arms: Array[Node3D] = []
var claws: Array[Node3D] = []
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

# ---- GLB drop-in: animacao do modelo externo por pose ----
var glb_player: AnimationPlayer
var glb_clip_pose := {} # pose ("run"/"crouch"/"idle") -> nome do clip
var glb_pose_atual := ""

# ---- blob shadow (P2) ----------------------------------------------------
var blob_shadow: MeshInstance3D
var blob_mat: StandardMaterial3D

func configure(next_species: String = "caramelo") -> void:
    species = next_species

func _ready() -> void:
    rng.seed = hash(species) + get_instance_id()
    # Qualquer especie com <especie>.glb em assets/characters/animais/ usa o
    # modelo drop-in (escala por GLB_SIZES); sem o arquivo, entra o
    # builder procedural da especie.
    if _build_animal_glb(species):
        _ensure_blob_shadow(_blob_size_for_species(species))
        return
    if species == "caramelo":
        _build_caramelo()
    elif BIRD_PROFILES.has(species):
        _build_bird()
    elif species == "capivara":
        _build_capivara()
    elif species == "cavalo":
        _build_cavalo()
    elif species == "boi":
        _build_boi()
    elif species == "macaco":
        _build_macaco()
    elif species == "caranguejo":
        _build_caranguejo()
    else:
        _build_bird()
    _ensure_blob_shadow(_blob_size_for_species(species))

func _process(delta: float) -> void:
    motion_time += delta
    # glb_player (AnimationPlayer do drop-in) avanca sozinho no loop da cena.
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
    _sincronizar_clip_glb()
    if species == "caramelo":
        _animate_caramelo()
    elif BIRD_PROFILES.has(species):
        _animate_bird()
    elif QUADRUPED_PROFILES.has(species):
        _animate_quadruped()
    elif species == "macaco":
        _animate_macaco()
    elif species == "caranguejo":
        _animate_caranguejo()
    _update_blob_shadow()

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
                    _enter_pose("crouch") # no chão: bicando, pastando ou deitada
                    behavior_timer = rng.randf_range(1.2, 2.2)
            "crouch":
                if rng.randf() < 0.3:
                    crouch_moving = true # sai de fininho, agachada em movimento
                    _enter_pose("crouch")
                    behavior_timer = rng.randf_range(0.8, 1.4)
                else:
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
                tail.rotation.z = -0.50 + sin(motion_time * (9.0 if crouch_moving else 6.0)) * 0.30
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
                if crouch_moving:
                    # rasteira agachada: ciclo curto com o corpo baixo
                    leg.rotation.z = sin(motion_time * 9.5 + float(index) * PI) * 0.13
                else:
                    # reverência: dianteiras dobradas, traseiras quase plantadas
                    leg.rotation.z = -0.45 if front else -0.05
            _:
                leg.rotation.x = 0.0
                leg.rotation.z = sin(motion_time * (10.0 if running else 2.8) + float(index) * PI) * (0.20 if running else 0.03)
    if body_root:
        match pose_state:
            "jump":
                body_root.position.y = 0.055
                body_root.rotation.z = 0.12 # focinho para cima
            "crouch":
                body_root.position.y = -0.055 if crouch_moving else -0.085
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
            # pombo ANDANDO: passos alternados das pernas + o balanco de
            # cabeca para frente tipico da especie; asas sempre coladas
            left.rotation.z = 0.12
            right.rotation.z = -0.12
            left.rotation.y = 0.0
            right.rotation.y = 0.0
            body_root.position.y = absf(sin(motion_time * 9.0)) * 0.012
            body_root.rotation.x = 0.34
            if head:
                head.rotation.x = 0.10
                head.position.z = 0.155 + maxf(0.0, sin(motion_time * 9.0)) * 0.055
            for index in legs.size():
                legs[index].rotation.x = sin(motion_time * 9.0 + float(index) * PI) * 0.62
            if tail:
                tail.rotation.x = 0.30 + sin(motion_time * 4.5) * 0.05
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
            if crouch_moving:
                # correção de rota agachada: corpo baixo, asas meio abertas
                left.rotation.z = 0.24
                right.rotation.z = -0.24
                left.rotation.y = -0.20
                right.rotation.y = 0.20
                body_root.position.y = -0.035
                body_root.rotation.x = 0.10
                if head:
                    head.rotation.x = 0.10
                for index in legs.size():
                    legs[index].rotation.x = sin(motion_time * 13.0 + float(index) * PI) * 0.22
            else:
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

func _animate_quadruped() -> void:
    var profile: Dictionary = QUADRUPED_PROFILES.get(species, QUADRUPED_PROFILES["capivara"])
    var cycle: float = float(profile.get("cycle", 8.0))
    var bob: float = float(profile.get("bob", 0.025))
    var lie: bool = bool(profile.get("lie", false))
    var graze_angle: float = float(profile.get("crouch_head", 0.0))
    if body_root:
        match pose_state:
            "jump":
                body_root.position.y = 0.10
                body_root.rotation.z = 0.10
            "crouch":
                body_root.position.y = -0.10 if (lie and not crouch_moving) else (-0.05 if crouch_moving else 0.0)
                body_root.rotation.z = 0.0
            _:
                body_root.position.y = sin(motion_time * (cycle if running else 2.0)) * (bob if running else 0.006)
                body_root.rotation.z = 0.0
    if head:
        match pose_state:
            "jump":
                head.rotation.z = 0.18
            "crouch":
                # capivara deitada mantém a cabeça no nível do chão;
                # cavalo e boi abaixam pescoço e cabeça para pastar.
                head.rotation.z = graze_angle * (0.7 if crouch_moving else 1.0)
            _:
                head.rotation.z = sin(motion_time * (cycle * 0.5 if running else 1.6)) * (0.08 if running else 0.045)
    if tail:
        match pose_state:
            "jump":
                tail.rotation.y = 0.0
            "crouch":
                tail.rotation.y = sin(motion_time * 2.2) * 0.18
            _:
                tail.rotation.y = sin(motion_time * (6.0 if running else 2.4)) * (0.38 if running else 0.22)
    for index in legs.size():
        var leg := legs[index]
        var front: bool = leg_is_front[index] if index < leg_is_front.size() else true
        match pose_state:
            "jump":
                leg.rotation.x = 0.0
                leg.rotation.z = -0.26 if front else -0.52
            "crouch":
                leg.rotation.x = 0.0
                if crouch_moving:
                    leg.rotation.z = sin(motion_time * cycle * (1.15 if lie else 0.6) + float(index) * PI) * 0.12
                elif lie:
                    # deitada: patas dobradas junto ao corpo
                    leg.rotation.z = -0.40 if front else -0.04
                else:
                    leg.rotation.z = 0.0
            _:
                leg.rotation.x = 0.0
                leg.rotation.z = sin(motion_time * (cycle if running else 2.2) + float(index) * PI) * (0.20 if running else 0.03)

func _animate_macaco() -> void:
    if body_root:
        match pose_state:
            "jump":
                body_root.position.y = 0.10
                body_root.rotation.z = -0.12
            "crouch":
                body_root.position.y = -0.16 if not crouch_moving else -0.12
                body_root.rotation.z = -0.05
            _:
                body_root.position.y = sin(motion_time * (11.0 if running else 2.4)) * (0.02 if running else 0.007)
                body_root.rotation.z = -0.18 if running else 0.0
    if head:
        match pose_state:
            "jump":
                head.rotation.z = -0.15
            "crouch":
                head.rotation.z = 0.22 # espiando com curiosidade
            _:
                head.rotation.z = sin(motion_time * 2.1) * 0.14
    if tail:
        match pose_state:
            "jump":
                tail.rotation.z = 0.15 # cauda esticada no salto
            "crouch":
                tail.rotation.z = 1.15 # cauda enroscada
            _:
                tail.rotation.z = 0.72 + sin(motion_time * (5.0 if running else 2.0)) * 0.20
    for index in arms.size():
        var arm := arms[index]
        match pose_state:
            "jump":
                arm.rotation.z = 1.90 # braços para cima na direção do salto
            "crouch":
                arm.rotation.z = sin(motion_time * 10.0 + float(index) * PI) * 0.22 if crouch_moving else 0.30
            _:
                arm.rotation.z = sin(motion_time * (11.0 if running else 2.6) + float(index) * PI) * (0.55 if running else 0.08)
    for index in legs.size():
        var leg := legs[index]
        match pose_state:
            "jump":
                leg.rotation.z = -0.45
            "crouch":
                leg.rotation.z = sin(motion_time * 10.0 + float(index) * PI) * 0.16 if crouch_moving else -0.30
            _:
                leg.rotation.z = sin(motion_time * (11.0 if running else 2.6) + float(index) * PI) * (0.45 if running else 0.05)

func _animate_caranguejo() -> void:
    if body_root:
        match pose_state:
            "jump":
                body_root.position.y = 0.07
                body_root.rotation.z = 0.0
            "crouch":
                body_root.position.y = -0.055 if not crouch_moving else -0.035
                body_root.rotation.z = 0.0
            _:
                body_root.position.y = sin(motion_time * (15.0 if running else 2.8)) * (0.008 if running else 0.004)
                body_root.rotation.z = sin(motion_time * 15.0) * 0.03 if running else 0.0
    for index in claws.size():
        var claw := claws[index]
        var side: float = -1.0 if index == 0 else 1.0
        match pose_state:
            "jump":
                claw.rotation.z = side * 1.15 # pinças erguidas
            "crouch":
                claw.rotation.z = side * -0.28 if not crouch_moving else side * -0.18
            _:
                if index == 0:
                    claw.rotation.z = -0.20 + sin(motion_time * 3.2) * 0.26 # pinça saudação
                else:
                    claw.rotation.z = 0.12 + sin(motion_time * 2.4) * 0.10
    for index in legs.size():
        var leg := legs[index]
        var side: float = -1.0 if index < 3 else 1.0
        match pose_state:
            "jump":
                leg.rotation.y = 0.0
                leg.rotation.z = side * 0.45 # patas recolhidas
            "crouch":
                leg.rotation.z = side * (1.0 if not crouch_moving else 0.8)
                leg.rotation.y = sin(motion_time * 13.0 + float(index) * PI) * 0.10 if crouch_moving else 0.0
            _:
                leg.rotation.z = side * 0.85
                leg.rotation.y = sin(motion_time * (16.0 if running else 2.2) + float(index) * PI) * (0.24 if running else 0.05)

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

    _ellipsoid(body_root, Vector3(0.0, 0.56, 0.0), Vector3(0.74, 0.35, 0.44), fur, "DogBody")
    _ellipsoid(body_root, Vector3(-0.05, 0.74, 0.0), Vector3(0.46, 0.14, 0.30), _material(Color("#8a5a30"), TEXTURE_FUR, 0.86), "DogSela")
    _ellipsoid(body_root, Vector3(0.40, 0.70, 0.0), Vector3(0.22, 0.26, 0.22), fur, "DogNeck")
    _ellipsoid(body_root, Vector3(0.53, 0.90, 0.0), Vector3(0.28, 0.26, 0.24), face, "DogHead")
    _ellipsoid(body_root, Vector3(0.80, 0.80, 0.0), Vector3(0.21, 0.105, 0.10), face, "DogMuzzle")
    _ellipsoid(body_root, Vector3(0.98, 0.82, 0.0), Vector3(0.05, 0.045, 0.045), dark, "DogNose")
    for side in [-1.0, 1.0]:
        _ellipsoid(body_root, Vector3(0.58, 0.98, side * 0.14), Vector3(0.04, 0.05, 0.04), eye, "DogEye")
        var ear := _ellipsoid(body_root, Vector3(0.40, 1.12, side * 0.15), Vector3(0.06, 0.24, 0.09), fur, "DogEar")
        ear.rotation.z = side * 0.30
        _ellipsoid(body_root, Vector3(0.40, 1.10, side * 0.155), Vector3(0.03, 0.16, 0.035), inner_ear, "DogEarInner")
    _torus(body_root, 0.20, 0.025, Vector3(0.40, 0.78, 0.0), collar, "DogCollar")
    _sphere(body_root, 0.065, Vector3(0.40, 0.62, -0.22), metal, "DogTag")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.052, 0.50, Vector3(front * 0.40, 0.30, side * 0.15), fur, "DogLeg")
            legs.append(leg)
            leg_is_front.append(front > 0.0)
            _ellipsoid(body_root, Vector3(front * 0.40, 0.045, side * 0.15), Vector3(0.075, 0.045, 0.09), dark, "DogPaw")
    tail = _capsule(body_root, 0.05, 0.44, Vector3(-0.68, 0.86, 0.0), fur, "DogTailBase")
    tail.rotation.z = -1.05
    var tail_tip := _ellipsoid(body_root, Vector3(-0.80, 1.16, 0.0), Vector3(0.075, 0.10, 0.075), fur, "DogTailTip")
    tail_tip.rotation.z = -0.5

## Modelo GLB drop-in (assets/characters/animais/<species>.glb): escala por
## GLB_SIZES, assenta no chao e toca a animacao de comportamento em loop.
## Retorna true se o modelo foi usado (builders proceduais sao pulados).
func _build_animal_glb(p_species: String) -> bool:
    if not GLB_SIZES.has(p_species):
        return false
    var caminho := "res://assets/characters/animais/%s.glb" % p_species
    if not ResourceLoader.exists(caminho):
        return false
    var empacotado: PackedScene = load(caminho) as PackedScene
    if empacotado == null:
        return false
    var modelo := empacotado.instantiate()
    if modelo == null:
        return false
    var tamanhos: Array = GLB_SIZES[p_species]
    var comp := float(tamanhos[0])
    var alt := float(tamanhos[1])
    modelo.rotation.y = PI / 2.0   # GLBs chegam olhando +Z; convensao da entidade e +X
    add_child(modelo)
    _fit_glb(modelo, comp, alt)
    _animar_glb(modelo)
    return true

## Escala pelo bbox real do modelo (espaco local, pre-rotacao) e assenta o
## fundo no chao local, com o centro X/Z do modelo sobre a origem da entidade.
func _fit_glb(modelo: Node3D, comp_alvo: float, alt_alvo: float) -> void:
    var aabb := AABB()
    var primeiro := true
    var pilha: Array[Node] = [modelo]
    while not pilha.is_empty():
        var no: Node = pilha.pop_back()
        if no is MeshInstance3D:
            var mi := no as MeshInstance3D
            var local := mi.transform * mi.get_aabb()
            if primeiro:
                aabb = local
                primeiro = false
            else:
                aabb = aabb.merge(local)
        for filho in no.get_children():
            pilha.append(filho)
    if primeiro or not aabb.has_volume():
        return
    var fator := minf(comp_alvo / maxf(aabb.size.z, 0.001), alt_alvo / maxf(aabb.size.y, 0.001))
    modelo.scale = Vector3.ONE * fator
    # O aabb esta no espaco local do modelo (que chega girado 90° em Y); o
    # deslocamento de assentamento precisa ser rotacionado pelo proprio modelo
    # para cair no espaco do pai, senao o animal aparece deslocado do spawn.
    var assento_local := Vector3(aabb.get_center().x, aabb.position.y, aabb.get_center().z)
    modelo.position -= (modelo.basis * assento_local) * fator

## Escolhe o clip conforme o comportamento e toca em loop:
## - no voo (behavior_mode == "flight"): clip "fly"/"voo" (bater de asas),
##   se existir — o pombo (lote 1) nao tem, entao cai no walk como antes;
## - no chao: clip da pose atual (walk/trot para run, graze/lie para crouch,
##   idle/stand para idle), com fallback em cascata — e o _process troca de
##   clip quando a pose muda (_sincronizar_clip_glb).
func _animar_glb(modelo: Node3D) -> void:
    glb_player = _achar_player(modelo)
    if glb_player == null or glb_player.get_animation_list().is_empty():
        return
    _mapear_clips_pose()
    var escolhido := ""
    if behavior_mode == "flight":
        # No voo, prefere o clip de bater de asas ("fly"/"voo").
        for nome in glb_player.get_animation_list():
            var baixo := nome.to_lower()
            if baixo.contains("fly") or baixo.contains("voo"):
                escolhido = nome
                break
    if escolhido == "":
        # No chao, ou sem clip de voo (ex.: pombo no aereo): clip da pose.
        escolhido = _clip_para_pose(pose_state)
    var anim := glb_player.get_animation(escolhido)
    if anim != null:
        anim.loop_mode = Animation.LOOP_LINEAR
    glb_pose_atual = pose_state
    glb_player.play(escolhido)

## Mapeia clip por categoria de nome para cada pose do contrato.
func _mapear_clips_pose() -> void:
    for nome in glb_player.get_animation_list():
        var baixo := nome.to_lower()
        if baixo.contains("walk") or baixo.contains("trot") or baixo.contains("run"):
            glb_clip_pose["run"] = nome
        elif baixo.contains("graze") or baixo.contains("lie") or baixo.contains("deita") or baixo.contains("pasto"):
            glb_clip_pose["crouch"] = nome
        elif baixo.contains("idle") or baixo.contains("stand"):
            glb_clip_pose["idle"] = nome

## Clip para um estado de pose: a propria pose, senao run, senao idle,
## senao o primeiro disponivel.
func _clip_para_pose(pose: String) -> String:
    if glb_clip_pose.has(pose):
        return glb_clip_pose[pose]
    if glb_clip_pose.has("run"):
        return glb_clip_pose["run"]
    if glb_clip_pose.has("idle"):
        return glb_clip_pose["idle"]
    return glb_player.get_animation_list()[0]

## Troca o clip do GLB quando a pose muda. So em modo chao: no voo a ave
## fica trancada no clip de asas (o planeio alterna run/idle de pose, o que
## aqui nao deve trocar a animacao).
func _sincronizar_clip_glb() -> void:
    if glb_player == null or behavior_mode == "flight":
        return
    var pose := "run" if pose_state == "jump" else pose_state
    if pose == glb_pose_atual:
        return
    glb_pose_atual = pose
    var clip := _clip_para_pose(pose)
    if glb_player.current_animation == clip:
        return
    var anim := glb_player.get_animation(clip)
    if anim != null:
        anim.loop_mode = Animation.LOOP_LINEAR
    glb_player.play(clip)

func _achar_player(no: Node) -> AnimationPlayer:
    if no is AnimationPlayer:
        return no as AnimationPlayer
    for filho in no.get_children():
        var achado := _achar_player(filho)
        if achado != null:
            return achado
    return null

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

    # Pombo em postura de andar: corpo inclinado para frente, asas FOLDADAS
    # contra o corpo (nunca abertas no chao), pernas visiveis dando os passos.
    body_root.rotation.x = 0.34
    _ellipsoid(body_root, Vector3(0.0, 0.0, 0.02), Vector3(0.135, 0.135, 0.26), feather, "BirdBody")
    _ellipsoid(body_root, Vector3(0.0, 0.05, 0.12), Vector3(0.095, 0.10, 0.10), feather, "BirdBreast")

    head = Node3D.new()
    head.name = "BirdHeadPivot"
    head.position = Vector3(0.0, 0.155, 0.155)
    body_root.add_child(head)
    _ellipsoid(head, Vector3.ZERO, Vector3(0.075, 0.085, 0.085), feather, "BirdHead")
    _ellipsoid(head, Vector3(0.0, -0.045, 0.035), Vector3(0.05, 0.06, 0.06), feather, "BirdPescoco")
    _box(head, Vector3(0.035, 0.028, 0.09), Vector3(0.0, -0.012, 0.095), beak_mat, "BirdBico")
    _ellipsoid(head, Vector3(0.0, 0.02, 0.028), Vector3(0.012, 0.014, 0.012), Color("#c9d4e0"), feather, "BirdCeroma")
    for side in [-1.0, 1.0]:
        _ellipsoid(head, Vector3(side * 0.045, 0.02, 0.03), Vector3(0.014, 0.014, 0.014), eye, "BirdEye")

    # asas dobradas contra o corpo (forma de gota apontando para tras)
    for side in [-1.0, 1.0]:
        var asa := _ellipsoid(body_root, Vector3(side * 0.105, 0.035, -0.06),
                Vector3(0.045, 0.075, span * 0.42), wing_mat, "BirdAsa")
        asa.rotation.z = side * 0.22
        wings.append(asa)

    tail = Node3D.new()
    tail.name = "BirdTailPivot"
    tail.position = Vector3(0.0, 0.035, -0.20)
    tail.rotation.x = 0.30
    body_root.add_child(tail)
    _box(tail, Vector3(0.09, 0.016, 0.17), Vector3(0.0, 0.0, -0.075), wing_mat, "BirdCauda")

    for side in [-1.0, 1.0]:
        var leg := _capsule(body_root, 0.012, 0.17, Vector3(side * 0.045, -0.02, 0.01), leg_mat, "BirdPerna")
        legs.append(leg)
        leg_is_front.append(false)
        _box(body_root, Vector3(0.045, 0.014, 0.075), Vector3(side * 0.045, -0.105, 0.045), leg_mat, "BirdPe")

func _build_capivara() -> void:
    body_root = Node3D.new()
    body_root.name = "Capivara3D"
    add_child(body_root)
    var fur := _material(Color("#8a6444"), TEXTURE_FUR, 0.85)
    var belly := _material(Color("#a3835f"), TEXTURE_FUR, 0.88)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.6)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.2)
    _ellipsoid(body_root, Vector3(0.0, 0.46, 0.0), Vector3(0.80, 0.42, 0.52), fur, "CapivaraBody")
    _ellipsoid(body_root, Vector3(0.06, 0.28, 0.0), Vector3(0.62, 0.22, 0.40), belly, "CapivaraBelly")
    head = Node3D.new()
    head.name = "CapivaraHeadPivot"
    head.position = Vector3(0.74, 0.60, 0.0)
    body_root.add_child(head)
    _ellipsoid(head, Vector3.ZERO, Vector3(0.30, 0.25, 0.27), fur, "CapivaraHead")
    _ellipsoid(head, Vector3(0.22, -0.04, 0.0), Vector3(0.17, 0.13, 0.15), belly, "CapivaraMuzzle")
    _ellipsoid(head, Vector3(0.36, 0.00, 0.0), Vector3(0.05, 0.04, 0.05), dark, "CapivaraNose")
    for side in [-1.0, 1.0]:
        var ear := _ellipsoid(head, Vector3(0.06, 0.20, side * 0.18), Vector3(0.055, 0.06, 0.04), fur, "CapivaraEar")
        ear.rotation.z = 0.1
        _ellipsoid(head, Vector3(0.17, 0.06, side * 0.22), Vector3(0.035, 0.035, 0.035), eye, "CapivaraEye")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.062, 0.30, Vector3(front * 0.36, 0.17, side * 0.20), fur, "CapivaraLeg")
            legs.append(leg)
            leg_is_front.append(front > 0.0)
            _ellipsoid(body_root, Vector3(front * 0.36, 0.045, side * 0.22), Vector3(0.10, 0.05, 0.12), dark, "CapivaraPaw")
    tail = _ellipsoid(body_root, Vector3(-0.80, 0.50, 0.0), Vector3(0.06, 0.05, 0.06), fur, "CapivaraTail")

func _build_cavalo() -> void:
    body_root = Node3D.new()
    body_root.name = "Cavalo3D"
    add_child(body_root)
    var fur := _material(Color("#7a4e33"), TEXTURE_FUR, 0.84)
    var mane := _material(Color("#2e211a"), TEXTURE_FUR, 0.78)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.5)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.2)
    _ellipsoid(body_root, Vector3(0.0, 1.06, 0.0), Vector3(0.74, 0.44, 0.46), fur, "CavaloBody")
    _ellipsoid(body_root, Vector3(-0.42, 1.10, 0.0), Vector3(0.30, 0.36, 0.42), fur, "CavaloHindquarter")
    head = Node3D.new()
    head.name = "CavaloHeadPivot"
    head.position = Vector3(0.58, 1.34, 0.0)
    body_root.add_child(head)
    var neck := _ellipsoid(head, Vector3(-0.04, 0.16, 0.0), Vector3(0.15, 0.34, 0.17), fur, "CavaloNeck")
    neck.rotation.z = -0.35
    _ellipsoid(head, Vector3(0.24, 0.44, 0.0), Vector3(0.22, 0.16, 0.15), fur, "CavaloHead")
    _ellipsoid(head, Vector3(0.42, 0.38, 0.0), Vector3(0.13, 0.10, 0.11), fur, "CavaloMuzzle")
    var mane_mesh := _box(head, Vector3(0.05, 0.55, 0.06), Vector3(-0.12, 0.22, 0.0), mane, "HorseMane")
    mane_mesh.rotation.z = -0.30
    for side in [-1.0, 1.0]:
        var ear := _ellipsoid(head, Vector3(0.18, 0.58, side * 0.07), Vector3(0.035, 0.10, 0.03), mane, "CavaloEar")
        ear.rotation.z = 0.12
        _ellipsoid(head, Vector3(0.26, 0.50, side * 0.13), Vector3(0.03, 0.03, 0.03), eye, "CavaloEye")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.052, 0.82, Vector3(front * 0.40, 0.41, side * 0.19), fur, "CavaloLeg")
            legs.append(leg)
            leg_is_front.append(front > 0.0)
            _cylinder(body_root, 0.065, 0.055, 0.14, Vector3(front * 0.40, 0.06, side * 0.19), dark, "CavaloHoof")
    tail = Node3D.new()
    tail.name = "CavaloTailPivot"
    tail.position = Vector3(-0.70, 1.28, 0.0)
    body_root.add_child(tail)
    _capsule(tail, 0.045, 0.50, Vector3(0.02, -0.24, 0.0), mane, "CavaloTail")
    _ellipsoid(tail, Vector3(0.03, -0.50, 0.0), Vector3(0.07, 0.10, 0.07), mane, "CavaloTailTuft")

func _build_boi() -> void:
    body_root = Node3D.new()
    body_root.name = "Boi3D"
    add_child(body_root)
    var fur := _material(Color("#d8c9a8"), TEXTURE_FUR, 0.86)
    var patch := _material(Color("#7a5a42"), TEXTURE_FUR, 0.86)
    var muzzle := _material(Color("#d9a79a"), TEXTURE_FUR, 0.8)
    var horn := _material(Color("#e8e0c8"), TEXTURE_RUBBER, 0.45)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.5)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.2)
    _ellipsoid(body_root, Vector3(0.0, 0.98, 0.0), Vector3(0.88, 0.50, 0.56), fur, "BoiBody")
    _ellipsoid(body_root, Vector3(-0.20, 1.14, 0.22), Vector3(0.34, 0.26, 0.16), patch, "BoiPatch")
    _ellipsoid(body_root, Vector3(0.30, 0.86, -0.30), Vector3(0.28, 0.20, 0.14), patch, "BoiPatch")
    head = Node3D.new()
    head.name = "BoiHeadPivot"
    head.position = Vector3(0.74, 1.06, 0.0)
    body_root.add_child(head)
    _ellipsoid(head, Vector3.ZERO, Vector3(0.28, 0.24, 0.24), fur, "BoiHead")
    _ellipsoid(head, Vector3(0.24, -0.08, 0.0), Vector3(0.20, 0.14, 0.18), muzzle, "BoiMuzzle")
    for side in [-1.0, 1.0]:
        var horn_mesh := _cylinder(head, 0.030, 0.014, 0.18, Vector3(0.06, 0.20, side * 0.16), horn, "OxHorn")
        horn_mesh.rotation.z = 0.35
        horn_mesh.rotation.x = side * 0.45
        var ear := _ellipsoid(head, Vector3(0.02, 0.12, side * 0.26), Vector3(0.10, 0.05, 0.06), fur, "BoiEar")
        ear.rotation.x = side * 0.5
        _ellipsoid(head, Vector3(0.18, 0.06, side * 0.19), Vector3(0.035, 0.035, 0.035), eye, "BoiEye")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.07, 0.64, Vector3(front * 0.38, 0.32, side * 0.20), fur, "BoiLeg")
            legs.append(leg)
            leg_is_front.append(front > 0.0)
            _cylinder(body_root, 0.075, 0.065, 0.14, Vector3(front * 0.38, 0.06, side * 0.20), dark, "BoiHoof")
    tail = Node3D.new()
    tail.name = "BoiTailPivot"
    tail.position = Vector3(-0.84, 1.18, 0.0)
    body_root.add_child(tail)
    _capsule(tail, 0.035, 0.55, Vector3(0.0, -0.26, 0.0), fur, "BoiTail")
    _ellipsoid(tail, Vector3(0.0, -0.55, 0.0), Vector3(0.06, 0.09, 0.06), patch, "BoiTailTuft")

func _build_macaco() -> void:
    body_root = Node3D.new()
    body_root.name = "Macaco3D"
    add_child(body_root)
    var fur := _material(Color("#6e5236"), TEXTURE_FUR, 0.85)
    var face := _material(Color("#c99b78"), TEXTURE_FUR, 0.8)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.5)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.2)
    var torso := _ellipsoid(body_root, Vector3(0.0, 0.52, 0.0), Vector3(0.26, 0.34, 0.24), fur, "MacacoTorso")
    torso.rotation.z = -0.25
    head = Node3D.new()
    head.name = "MacacoHeadPivot"
    head.position = Vector3(0.16, 0.86, 0.0)
    body_root.add_child(head)
    _ellipsoid(head, Vector3.ZERO, Vector3(0.17, 0.17, 0.17), fur, "MacacoHead")
    _ellipsoid(head, Vector3(0.12, -0.01, 0.0), Vector3(0.11, 0.12, 0.13), face, "MacacoFace")
    for side in [-1.0, 1.0]:
        _ellipsoid(head, Vector3(0.02, 0.02, side * 0.17), Vector3(0.055, 0.055, 0.02), fur, "MacacoEar")
        _ellipsoid(head, Vector3(0.20, 0.04, side * 0.06), Vector3(0.025, 0.025, 0.025), eye, "MacacoEye")
        # braços com pivô de ombro
        var shoulder := Node3D.new()
        shoulder.name = "MonkeyShoulderL" if side < 0.0 else "MonkeyShoulderR"
        shoulder.position = Vector3(0.08, 0.68, side * 0.20)
        body_root.add_child(shoulder)
        _capsule(shoulder, 0.045, 0.50, Vector3(0.04, -0.22, 0.0), fur, "MonkeyArm")
        _ellipsoid(shoulder, Vector3(0.06, -0.46, 0.0), Vector3(0.05, 0.05, 0.05), face, "MonkeyHand")
        arms.append(shoulder)
    for side in [-1.0, 1.0]:
        var leg := _capsule(body_root, 0.05, 0.42, Vector3(-0.08, 0.22, side * 0.12), fur, "MonkeyLeg")
        legs.append(leg)
        leg_is_front.append(false)
        _ellipsoid(body_root, Vector3(-0.08, 0.03, side * 0.14), Vector3(0.07, 0.04, 0.09), dark, "MonkeyFoot")
    tail = Node3D.new()
    tail.name = "MonkeyTailPivot"
    tail.position = Vector3(-0.24, 0.62, 0.0)
    body_root.add_child(tail)
    var tail_mesh := _capsule(tail, 0.028, 0.62, Vector3(-0.26, 0.10, 0.0), fur, "MonkeyTail")
    tail_mesh.rotation.z = 0.72

func _build_caranguejo() -> void:
    body_root = Node3D.new()
    body_root.name = "Caranguejo3D"
    add_child(body_root)
    var shell := _material(Color("#d96a3f"), TEXTURE_RUBBER, 0.55)
    var claw_mat := _material(Color("#e0784a"), TEXTURE_RUBBER, 0.5)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.6)
    _ellipsoid(body_root, Vector3(0.0, 0.16, 0.0), Vector3(0.42, 0.13, 0.30), shell, "CrabShell")
    _ellipsoid(body_root, Vector3(0.0, 0.10, 0.26), Vector3(0.24, 0.07, 0.10), shell, "CrabFace")
    for side in [-1.0, 1.0]:
        _capsule(body_root, 0.012, 0.10, Vector3(side * 0.08, 0.28, 0.28), dark, "CrabEyeStalk")
        _sphere(body_root, 0.028, Vector3(side * 0.08, 0.34, 0.28), dark, "CrabEye")
    for side in [-1.0, 1.0]:
        var claw := Node3D.new()
        claw.name = "CrabClawPivotL" if side < 0.0 else "CrabClawPivotR"
        claw.position = Vector3(side * 0.34, 0.14, 0.20)
        body_root.add_child(claw)
        _capsule(claw, 0.035, 0.22, Vector3(side * 0.09, 0.0, 0.05), claw_mat, "CrabClawArm")
        _box(claw, Vector3(0.09, 0.05, 0.12), Vector3(side * 0.20, 0.0, 0.10), claw_mat, "CrabPincerBase")
        _box(claw, Vector3(0.08, 0.04, 0.09), Vector3(side * 0.24, 0.035, 0.17), claw_mat, "CrabPincerTop")
        _box(claw, Vector3(0.08, 0.04, 0.09), Vector3(side * 0.24, -0.035, 0.17), claw_mat, "CrabPincerBottom")
        claws.append(claw)
    for side in [-1.0, 1.0]:
        for rank in 3:
            var leg := _capsule(body_root, 0.02, 0.24, Vector3(side * (0.34 + float(rank) * 0.03), 0.08, -0.10 + float(rank) * 0.12), claw_mat, "CrabLeg")
            leg.rotation.z = side * 0.85
            legs.append(leg)
            leg_is_front.append(rank == 2)

func _blob_size_for_species(sp: String) -> Vector2:
    match sp:
        \"caramelo\": return Vector2(0.85, 0.55)
        \"capivara\": return Vector2(1.10, 0.72)
        \"cavalo\": return Vector2(1.60, 0.90)
        \"boi\": return Vector2(1.70, 0.95)
        \"macaco\": return Vector2(0.60, 0.60)
        \"caranguejo\": return Vector2(0.62, 0.42)
        \"pombo\": return Vector2(0.42, 0.28)
        \"passaro\": return Vector2(0.28, 0.18)
        \"gaivota\": return Vector2(0.55, 0.36)
        \"urubu\": return Vector2(0.72, 0.46)
        _: return Vector2(0.60, 0.40)

func _ensure_blob_shadow(size: Vector2) -> void:
    if blob_shadow != null:
        return
    blob_shadow = MeshInstance3D.new()
    blob_shadow.name = \"BlobShadow\"
    var mesh := PlaneMesh.new()
    mesh.size = size
    blob_shadow.mesh = mesh
    blob_shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    blob_shadow.position = Vector3(0.0, 0.025, 0.0)
    # Plane em XZ: rotaciona? PlaneMesh por padrão já é XZ? em Godot 4 PlaneMesh é XZ, mas vamos garantir
    blob_shadow.rotation_degrees = Vector3.ZERO
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0, 0, 0, 0.30)
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    mat.no_depth_test = false
    mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
    blob_shadow.material_override = mat
    blob_mat = mat
    add_child(blob_shadow)

func _update_blob_shadow() -> void:
    if blob_shadow == null or blob_mat == null:
        return
    var h: float = 0.0
    if body_root != null:
        h = maxf(0.0, body_root.position.y + 0.10)
    else:
        # GLB: estima pela pose (salto ~0.15–0.25)
        match pose_state:
            \"jump\": h = 0.22
            \"crouch\": h = 0.02 if crouch_moving else 0.0
            _: h = 0.04 if running else 0.01
    # voo: sombra quase some, não some abruptamente
    var flight_factor: float = 1.0
    if behavior_mode == \"flight\":
        h += 0.45
        flight_factor = 0.55
    # altura → escala menor + alpha menor
    var s: float = clampf(1.0 - h * 0.85, 0.42, 1.0) * flight_factor
    blob_shadow.scale = Vector3(s, 1.0, s)
    var a: float = clampf(0.30 - h * 0.55, 0.08, 0.30) * (0.55 if behavior_mode == \"flight\" else 1.0)
    blob_mat.albedo_color.a = a
    # acompanha Y do chão: quando animal sobe, sombra fica no chão
    blob_shadow.position.y = 0.025

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
        material.normal_enabled = true
        material.normal_texture = TEXTURE_FUR_N
        material.normal_scale = 0.7
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_FUR_R
        material.uv1_scale = Vector3(2.0, 2.0, 2.0)
    elif texture == TEXTURE_FEATHER:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_FEATHER_N
        material.normal_scale = 0.6
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_FEATHER_R
        material.uv1_scale = Vector3(2.0, 2.0, 2.0)
    elif texture == TEXTURE_RUBBER:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_RUBBER_N
        material.normal_scale = 0.3
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_RUBBER_R
        material.uv1_scale = Vector3(3.0, 3.0, 3.0)
    elif texture == TEXTURE_METAL:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_METAL_N
        material.normal_scale = 0.4
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_METAL_R
        material.uv1_scale = Vector3(3.0, 3.0, 3.0)
    return material

func _mesh(parent: Node3D, node_name: String, mesh: Mesh, material: Material) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    node.mesh = mesh
    node.material_override = material
    node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
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

func _cylinder(parent: Node3D, top_radius: float, bottom_radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := CylinderMesh.new()
    mesh.top_radius = top_radius
    mesh.bottom_radius = bottom_radius
    mesh.height = height
    mesh.radial_segments = 14
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
