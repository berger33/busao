extends Node3D
## Corre pro Ponto — versão 3D mobile-first.
##
## O jogador corre por uma avenida brasileira em terceira pessoa. A faixa
## esquerda é rua (carros, ônibus, motos e buracos); as faixas centro/direita
## são calçadas (pedestres, hidrante, orelhão, cachorro, bicicleta e camelô).
## O cenário é montado com assemblies 3D low-poly detalhados, materiais PBR leves
## e texturas raster/SVG: o mundo desliza no eixo -Z, muda de arquitetura a cada
## capítulo e mantém o APK leve para Android.

const BALANCE = preload("res://resources/game_balance.tres")
const SCENARIO_DATA = preload("res://scripts/scenario_data.gd")
const CHARACTER_DATA = preload("res://scripts/character_data.gd")
const SHOP_DATA = preload("res://scripts/shop_data.gd")
const OBSTACLE_DATA = preload("res://scripts/obstacle_data.gd")
const RUNNER_CHARACTER_SCRIPT = preload("res://scripts/runner_character.gd")
const WORLD_CHARACTER_SCRIPT = preload("res://scripts/world_character.gd")
const WORLD_ANIMAL_SCRIPT = preload("res://scripts/world_animal.gd")
const PHYSICS_HANDLER = preload("res://scripts/physics_handler.gd")
const LIGHTING_HANDLER = preload("res://scripts/lighting_handler.gd")
const TEXTURE_ASPHALT = preload("res://assets/textures/asfalto_brasil.svg")
const TEXTURE_ASPHALT_REAL = preload("res://assets/textures/asfalto_realista.png")
const TEXTURE_ASPHALT_NORMAL = preload("res://assets/textures/asfalto_normal.png")
const TEXTURE_ASPHALT_ROUGH = preload("res://assets/textures/asfalto_roughness.png")
const TEXTURE_SIDEWALK = preload("res://assets/textures/calcada_portuguesa.svg")
const TEXTURE_SIDEWALK_REAL = preload("res://assets/textures/calcada_realista.png")
const TEXTURE_SIDEWALK_NORMAL = preload("res://assets/textures/calcada_normal.png")
const TEXTURE_SIDEWALK_ROUGH = preload("res://assets/textures/calcada_roughness.png")
const TEXTURE_FACADE_PLASTER = preload("res://assets/textures/fachada_reboco.png")
const TEXTURE_FACADE_PLASTER_N = preload("res://assets/textures/fachada_reboco_normal.png")
const TEXTURE_FACADE_PLASTER_R = preload("res://assets/textures/fachada_reboco_roughness.png")
const TEXTURE_FACADE_BRICK = preload("res://assets/textures/fachada_tijolo.png")
const TEXTURE_FACADE_BRICK_N = preload("res://assets/textures/fachada_tijolo_normal.png")
const TEXTURE_FACADE_BRICK_R = preload("res://assets/textures/fachada_tijolo_roughness.png")
const TEXTURE_BRICK_WALL = preload("res://assets/textures/parede_tijolo_realista.png")
const TEXTURE_BRICK_WALL_N = preload("res://assets/textures/parede_tijolo_realista_normal.png")
const TEXTURE_BRICK_WALL_R = preload("res://assets/textures/parede_tijolo_realista_roughness.png")
const TEXTURE_CAR_PAINT_NORMAL = preload("res://assets/textures/pintura_carro_normal.png")
const TEXTURE_COBBLE = preload("res://assets/textures/cobblestone.svg")
const TEXTURE_SKY_PANORAMA = preload("res://assets/textures/ceu_tropical.png")
const TEXTURE_SKY_SUNSET = preload("res://assets/textures/ceu_entardecer.png")
const TEXTURE_SKY_CLOUDY = preload("res://assets/textures/ceu_nublado.png")
const TEXTURE_HAIR_REAL = preload("res://assets/textures/cabelo_realista.png")
const TEXTURE_DENIM_REAL = preload("res://assets/textures/jeans_realista.png")
const TEXTURE_CAR_PAINT_REAL = preload("res://assets/textures/pintura_carro_realista.png")
const TEXTURE_GLASS = preload("res://assets/textures/vidro_azul.svg")
const TEXTURE_PAINT = preload("res://assets/textures/pintura_micro.svg")
const TEXTURE_DIRT_REAL = preload("res://assets/textures/terra_realista.png")
const TEXTURE_DIRT_REAL_N = preload("res://assets/textures/terra_realista_normal.png")
const TEXTURE_DIRT_REAL_R = preload("res://assets/textures/terra_realista_roughness.png")
const TEXTURE_CONCRETE_REAL = preload("res://assets/textures/concreto_realista.png")
const TEXTURE_CONCRETE_REAL_N = preload("res://assets/textures/concreto_realista_normal.png")
const TEXTURE_CONCRETE_REAL_R = preload("res://assets/textures/concreto_realista_roughness.png")
const TEXTURE_METAL_REAL = preload("res://assets/textures/metal_pintado_realista.png")
const TEXTURE_METAL_REAL_N = preload("res://assets/textures/metal_pintado_realista_normal.png")
const TEXTURE_METAL_REAL_R = preload("res://assets/textures/metal_pintado_realista_roughness.png")
const TEXTURE_FABRIC_REAL = preload("res://assets/textures/tecido_realista.png")
const TEXTURE_FABRIC_REAL_N = preload("res://assets/textures/tecido_realista_normal.png")
const TEXTURE_FABRIC_REAL_R = preload("res://assets/textures/tecido_realista_roughness.png")
const TEXTURE_LEAVES_REAL = preload("res://assets/textures/folhagem_realista.png")
const TEXTURE_LEAVES_REAL_N = preload("res://assets/textures/folhagem_realista_normal.png")
const TEXTURE_LEAVES_REAL_R = preload("res://assets/textures/folhagem_realista_roughness.png")
const TEXTURE_WOOD_REAL = preload("res://assets/textures/madeira_realista.png")
const TEXTURE_WOOD_REAL_N = preload("res://assets/textures/madeira_realista_normal.png")
const TEXTURE_WOOD_REAL_R = preload("res://assets/textures/madeira_realista_roughness.png")
const TEXTURE_RUBBER_REAL = preload("res://assets/textures/borracha_realista.png")
const TEXTURE_RUBBER_REAL_N = preload("res://assets/textures/borracha_realista_normal.png")
const TEXTURE_RUBBER_REAL_R = preload("res://assets/textures/borracha_realista_roughness.png")
const TEXTURE_SKIN_REAL = preload("res://assets/textures/pele_realista.png")
const TEXTURE_SKIN_REAL_N = preload("res://assets/textures/pele_realista_normal.png")
const TEXTURE_SKIN_REAL_R = preload("res://assets/textures/pele_realista_roughness.png")
const LANE_X: Array[float] = [-3.25, 0.0, 3.25]
const ROAD_LANE := 0
const SIDEWALK_CENTER := 1
const SIDEWALK_RIGHT := 2
const PLAYER_Z := 0.0
const HORIZON_Z := -75.0
const WHITE := Color("#fff8e7")
const MUTED := Color("#a9b9ca")
const YELLOW := Color("#ffd34e")
const GOLD := Color("#ffb83e")
const RED := Color("#f2635e")
const GREEN := Color("#54d18b")
const BLUE := Color("#63c8ed")
const CYAN := Color("#63e6d2")
const VIOLET := Color("#ac8cff")
const UI_BG := Color("#0b1224")
const UI_PANEL := Color("#14233f")
const PLAYER_HEIGHT := 1.82 # sincronizado com runner (era 2.15)
const WORLD_LENGTH_MARGIN := 80.0

# --- Lote 2: constantes de render/câmera (roteiro game_3d_lote2_patch.gd) --
const RQ_PATH := "/root/RenderQuality"      # autoload do Lote 2
const RENDER_FOV := 54.0                    # perspectiva natural de terceira pessoa (ref abb89707)
const RENDER_FOV_RUN := 56.0                # FOV na corrida
const RENDER_CAMERA_Y := 2.25               # altura no ombro (ref abb89707, era 2.65 alto)
const RENDER_CAMERA_Z := 4.85               # distância mais próxima e imersiva (era 6.2)
const RENDER_CAMERA_FAR := 380.0            # deixa a serra/skyline entrar

# --- Lote 3: rua construída pelo building_kit.gd --------------------------
const WORLD_KIT_ATIVO := true          # false desliga a rua nova
const WORLD_Y_OFFSET := -0.15          # deixa a calçada no nível do chão do jogo
const WORLD_INVERTER := false          # true se a rua aparecer virada (correndo ao contrário)
const WORLD_SPEED_PADRAO := 18.0       # só para reciclar o quarteirão na hora certa

# --- Lote 4: clima --------------------------------------------------------
const CLIMA_ATIVO := true              # false desliga chuva/relâmpago/molhado


const ROAD_OBSTACLES: Array[String] = [
    "car", "car", "motorcycle", "pothole", "bus_traffic", "car", "truck"
]
const SIDEWALK_OBSTACLES: Array[String] = [
    "old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench"
]
const COLLECTIBLES: Dictionary = {
    "coin": "R$ 0,25",
    "coffee": "CAFÉ",
    "bread": "PÃO DE QUEIJO",
    "pastel": "PASTEL",
    "sugarcane": "CALDO DE CANA",
    "pass": "VALE-TRANSPORTE",
    "golden": "BILHETE DOURADO",
    "coxinha": "COXINHA",
    "guarana": "GUARANÁ",
    "pix": "PIX TURBO",
    "umbrella": "GUARDA-CHUVA"
}

var screen := 0 # menu, mapa, corrida, resultado, loja, conquistas, diários, guia
var previous_screen := 0
var map_page := 0
var shop_tab := 0
var shop_scroll := 0.0
var selected_phase := 0
var phase_index := 0
var phase: Dictionary = {}
var scenario: Dictionary = {}
var endless_mode := false
var run_mode := "playing" # playing, paused, at_stop, results
var distance := 0.0
var elapsed := 0.0
var run_total := 400.0
var player_lane := SIDEWALK_CENTER
var player_x := 0.0
# Lote 23 — Física Mundo Real (toggle; false mantém arcade lerp, true usa CharacterBody3D)
var physics_realista_enabled: bool = false
var _player_physics_body: CharacterBody3D = null
var _player_velocity_y: float = 0.0
var _is_on_floor_physics: bool = true
# Lote 24 — Luz Realista (F9 toggle; false Panorama 1024, true SDFGI/VoxelGI 4096 VSM)
var lighting_realista_enabled: bool = true
var player_speed := 5.0
var hearts := 3
var max_hearts := 3
var collected_coins := 0
var coin_multiplier := 1
var combo := 0
var combo_timer := 0.0
var run_score := 0
var no_damage := true
var jump_timer := 0.0
var jump_duration := 0.9
var slide_timer := 0.0
var dash_timer := 0.0
var dash_cooldown := 0.0
var dash_recharge_fast := false
var bus_wait_bonus := 0.0
var shield_hits := 0
var speed_boost_timer := 0.0
var slow_motion_timer := 0.0
var magnet_timer := 0.0
var rain_guard_timer := 0.0
var stop_wait := 0.0
var stop_wait_total := 0.0
var wall_run_count := 0
var dog_chase_timer := 0.0
# --- Lote 11/12: Ads/Billing estado ----------------------------------------
var _ads_failed_runs: int = 0
var _revive_used: bool = false
var _revive_screen: Control = null
var _revive_pending: bool = false
var _tutorial_arrow: Node3D = null
var _double_used: bool = false
var _rewarded_pending_placement: String = ""
var tutorial_hint := ""
var tutorial_stage := -1
var result: Dictionary = {}
var pulse := 0.0
var run_phase := 0.0
var step_timer := 0.0
var motion_speed := 0.0
var lane_change_velocity := 0.0
var invulnerability := 0.0

var world_root: Node3D
var course_root: Node3D
var entity_root: Node3D
var decor_root: Node3D
var fx_root: Node3D
var player_root: Node3D
var player_visual: Node3D
var camera: Camera3D
var bus_node: Node3D
var bus_stop_node: Node3D
var hud: Control
var environment: WorldEnvironment
var sun: DirectionalLight3D
var sky: Sky
var sky_material: PanoramaSkyMaterial
var sky_fx_root: Node3D
var sky_fx_nodes: Array[Dictionary] = []
var ambient_fx_root: Node3D
var ambient_fx_nodes: Array[Dictionary] = []
var ground_fauna_root: Node3D
var ground_fauna_nodes: Array[Dictionary] = []
var entities: Array[Dictionary] = []
var fx_nodes: Array[Dictionary] = []
# L29 Zero Procedural: primitive_mesh_cache removido — fallback GLB direto, sem BoxMesh
var rng := RandomNumberGenerator.new()
var fx_rng := RandomNumberGenerator.new()
var touch_start := Vector2.ZERO
var touch_started_at := 0
var pointer_active := false
var hud_sync_timer := 0.0
var performance_sample_timer := 0.0

var feedback_title := ""
var feedback_detail := ""
var feedback_color := YELLOW
var feedback_timer := 0.0
var camera_shake := 0.0
var flash_alpha := 0.0

# --- Lote 3: estado da rua (building_kit) ---------------------------------
var _world_kit: Node3D = null
var _world_travel := 0.0
var _world_last_head := 0.0
var _world_horizonte: Node3D = null   # silhueta fixa (reparentada p/ world_root)

# --- Lote 4: clima --------------------------------------------------------
var _clima: WeatherSystem = null

# --- Lote 6: efeitos e captura ---------------------------------------------
var _dust_particles: GPUParticles3D = null
var _splash_particles: GPUParticles3D = null
var _capture_mode := false
var _capture_yaw := 0.0
var _capture_pitch := -0.12

var _loading_screen: Control = null
var _cold_start_ms: int = 0

func _ready() -> void:
    _cold_start_ms = Time.get_ticks_msec()
    # Lote 14: LoadingScreen overlay (cold start <2.8s, barra mock 0→1)
    _loading_screen = preload("res://scripts/loading_screen.gd").new()
    _loading_screen.name = "LoadingScreen"
    # CanvasLayer para ficar por cima do HUD (layer 30)
    var _load_layer := CanvasLayer.new()
    _load_layer.name = "LoadingLayer"
    _load_layer.layer = 30
    add_child(_load_layer)
    _load_layer.add_child(_loading_screen)
    _loading_screen.set_progress(0.05)
    await get_tree().process_frame
    rng.seed = 20240917
    fx_rng.seed = 778899
    _loading_screen.set_progress(0.12)
    var login_streak := GameSave.register_login()
    # Lote 11/12: restaura contador de falhas para interstitial (fallback local se save ainda vazio)
    _ads_failed_runs = int(GameSave.data.get("ad_counters", {}).get("interstitial_run", 0))
    _setup_world()
    _loading_screen.set_progress(0.35)
    await get_tree().process_frame
    _setup_hud()
    _validate_obstacle_catalog()
    phase = PhaseData.get_phase(0)
    scenario = SCENARIO_DATA.get_profile(0)
    _apply_scenario_atmosphere()
    _rebuild_sky_fx()
    _rebuild_ambient_fx()
    _loading_screen.set_progress(0.65)
    await get_tree().process_frame
    AudioManager.play_music(0)
    if login_streak > 0 and login_streak % BALANCE.streak_reward_days == 0:
        _show_feedback("MARCO DE RETORNO", "+R$ %d • %d dias seguidos" % [BALANCE.streak_reward, login_streak], GOLD, "streak")
    else:
        _show_feedback("CORRE PRO PONTO 3D", "Rua à esquerda • calçadas à direita", YELLOW, "ui_confirm")
    _sync_hud()
    _apply_render_quality()      # Lote 2: controlador de render (RenderQuality)
    _setup_world_kit()           # Lote 3: rua do building_kit
    _loading_screen.set_progress(0.82)
    await get_tree().process_frame
    _setup_clima()               # Lote 4: clima (por cima do render e da rua)
    _setup_ads_billing()         # Lote 11/12: conecta Ads/Billing
    _setup_play_services()     # Lote 13: Play Games + cloud + review
    _setup_push()                  # P2: push streak em risco (PushManager)
    _setup_analytics()         # Lote 15: Firebase/GA/Crash/RemoteConfig (mock-first)
    _setup_in_app_update()     # Lote 18: In-App Update flexível (mock)
    _loading_screen.set_progress(1.0)
    # métrica cold start
    var _cold_ms := Time.get_ticks_msec() - _cold_start_ms
    if _cold_ms < 2800:
        # segura pelo menos 0.25s para o jogador ler a dica
        await get_tree().create_timer(0.25).timeout
    _loading_screen.fade_out(0.35)
    print("[lote14] cold start %d ms (alvo <2800)" % _cold_ms)


func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_GO_BACK_REQUEST:
        if screen == 2:
            if run_mode == "playing":
                run_mode = "paused"
                _show_feedback("PAUSA", "Toque voltar novamente para sair", CYAN, "ui_back")
            elif run_mode == "paused":
                GameSave.record_event("run_abandoned")
                GameSave.flush()
                _clear_course()
                screen = 1
                run_mode = "playing"
                _show_feedback("CORRIDA ENCERRADA", "Seu progresso já está seguro", BLUE, "ui_back")
            elif run_mode == "at_stop":
                _catch_bus()
        elif screen != 0:
            screen = 0
            _show_feedback("MENU", "Escolha o próximo corre", BLUE, "ui_back")
        return
    if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT]:
        if screen == 2 and run_mode == "playing":
            run_mode = "paused"
            _show_feedback("PAUSA AUTOMÁTICA", "O corre ficou seguro", CYAN, "ui_back")

func _phase_speed_for(index: int) -> float:
    var safe_index := clampi(index, 0, BALANCE.phase_count - 1)
    if safe_index <= BALANCE.chapter_unlock_phase:
        return lerpf(BALANCE.base_speed, BALANCE.chapter_one_final_speed, float(safe_index) / float(maxi(1, BALANCE.chapter_unlock_phase)))
    return lerpf(BALANCE.chapter_one_final_speed, BALANCE.final_speed, float(safe_index - BALANCE.chapter_unlock_phase) / float(maxi(1, BALANCE.phase_count - BALANCE.chapter_unlock_phase - 1)))

func _phase_wait_for(index: int) -> float:
    var safe_index := clampi(index, 0, BALANCE.phase_count - 1)
    if safe_index <= BALANCE.chapter_unlock_phase:
        var progress := float(safe_index) / float(maxi(1, BALANCE.chapter_unlock_phase))
        return lerpf(BALANCE.first_wait_seconds, BALANCE.final_wait_seconds, progress)
    return BALANCE.final_wait_seconds

func _process(delta: float) -> void:
    var dt: float = minf(delta, 0.05)
    pulse += dt
    _update_feedback(dt)
    _sample_performance(dt)
    _update_fx(dt)
    _update_sky_fx(dt)
    _update_ambient_fx(dt)
    _update_ground_fauna(dt)
    _update_sky_motion(dt)
    if screen == 2:
        _update_run(dt)
    _update_world_kit(dt)        # Lote 3: recicla os quarteirões da rua
    _update_clima(dt)            # Lote 4: chuva/poças seguem o corredor
    _update_lote6_effects(dt)    # Lote 6: poeira/respingo e PBR personagem
    _update_player(dt)
    _update_camera(dt)
    hud_sync_timer -= dt
    if hud_sync_timer <= 0.0:
        _sync_hud()
        # A corrida precisa de leitura fluida, mas reconstruir todo o estado
        # textual a cada frame desperdiça CPU no Android. 30 Hz é suficiente
        # para distância, corações e progresso; telas paradas usam 10 Hz.
        hud_sync_timer = 0.033 if screen == 2 else 0.10

func _sample_performance(dt: float) -> void:
    if screen != 2:
        performance_sample_timer = 0.0
        return
    performance_sample_timer += dt
    if performance_sample_timer < 1.0:
        return
    performance_sample_timer = 0.0
    var fps := Engine.get_frames_per_second()
    if fps >= 58:
        GameSave.record_event("fps_60_plus")
    elif fps >= 45:
        GameSave.record_event("fps_45_59")
    else:
        GameSave.record_event("fps_below_45")

func _validate_obstacle_catalog() -> void:
    for item in OBSTACLE_DATA.all():
        var obstacle_id := str(item.get("id", ""))
        var space := str(item.get("space", ""))
        var known_space := false
        if space == "road":
            known_space = obstacle_id in ROAD_OBSTACLES
        else:
            known_space = obstacle_id in SIDEWALK_OBSTACLES
        if not known_space:
            push_error("ObstacleData sem rota espacial: %s" % obstacle_id)
        if str(item.get("builder", "")) == "_build_pedestrian_obstacle" and obstacle_id not in ["old_lady", "vendor"]:
            push_error("ObstacleData pedestre sem adapter humano: %s" % obstacle_id)
        if str(item.get("builder", "")) == "_build_animal_obstacle" and obstacle_id != "dog":
            push_error("ObstacleData animal sem adapter: %s" % obstacle_id)

func _setup_world() -> void:
    world_root = Node3D.new()
    world_root.name = "World3D"
    add_child(world_root)
    course_root = Node3D.new()
    course_root.name = "Course"
    world_root.add_child(course_root)
    decor_root = Node3D.new()
    decor_root.name = "Decor"
    course_root.add_child(decor_root)
    entity_root = Node3D.new()
    entity_root.name = "Entities"
    course_root.add_child(entity_root)
    fx_root = Node3D.new()
    fx_root.name = "FeedbackFX"
    world_root.add_child(fx_root)

    environment = WorldEnvironment.new()
    environment.name = "BrazilianSky"
    environment.environment = Environment.new()
    environment.environment.background_mode = Environment.BG_SKY
    environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.environment.ambient_light_color = Color("#b8d8e4")
    environment.environment.ambient_light_energy = 0.72
    environment.environment.background_energy_multiplier = 0.92
    environment.environment.tonemap_mode = Environment.TONE_MAPPER_ACES
    environment.environment.tonemap_exposure = 1.06
    environment.environment.tonemap_white = 1.2
    environment.environment.glow_enabled = true
    environment.environment.glow_intensity = 0.42
    environment.environment.glow_bloom = 0.08
    environment.environment.glow_hdr_threshold = 1.15
    environment.environment.fog_enabled = true
    environment.environment.fog_light_color = Color("#ebd9be") # névoa dourada de fim de tarde (ref abb89707)
    environment.environment.fog_light_energy = 0.52
    environment.environment.fog_density = 0.0028 # névoa suave sem parede cinza (ref abb89707)
    environment.environment.fog_aerial_perspective = 0.40
    environment.environment.fog_sky_affect = 0.18
    sky = Sky.new()
    sky_material = PanoramaSkyMaterial.new()
    sky_material.panorama = TEXTURE_SKY_PANORAMA
    sky_material.energy_multiplier = 0.92
    sky_material.filter = true
    sky.sky_material = sky_material
    environment.environment.sky = sky
    world_root.add_child(environment)

    sky_fx_root = Node3D.new()
    sky_fx_root.name = "SkyLife"
    world_root.add_child(sky_fx_root)
    ambient_fx_root = Node3D.new()
    ambient_fx_root.name = "AmbientMotion"
    world_root.add_child(ambient_fx_root)
    ground_fauna_root = Node3D.new()
    ground_fauna_root.name = "GroundFauna"
    world_root.add_child(ground_fauna_root)

    sun = DirectionalLight3D.new()
    sun.name = "WarmSun"
    sun.rotation_degrees = Vector3(-28.0, -56.0, 0.0) # Golden hour lateral (ref abb89707)
    sun.light_color = Color("#fff2db")
    sun.light_energy = 1.45
    sun.shadow_enabled = true
    sun.directional_shadow_max_distance = 68.0
    sun.shadow_bias = 0.015
    sun.shadow_normal_bias = 0.45
    sun.shadow_opacity = 0.85
    sun.light_angular_distance = 0.8
    world_root.add_child(sun)
    # Lote24 — Luz realista: SDFGI/VoxelGI + ReflectionProbe + 4096 VSM + VolumetricFog + PhysicalSky (F9 toggle)
    if LIGHTING_HANDLER != null:
        LIGHTING_HANDLER.setup_realista(environment, sun, world_root, lighting_realista_enabled)

    camera = Camera3D.new()
    camera.name = "RunnerCamera"
    camera.position = Vector3(0.0, RENDER_CAMERA_Y, RENDER_CAMERA_Z)
    camera.fov = RENDER_FOV
    camera.near = 0.1
    camera.far = RENDER_CAMERA_FAR
    camera.current = true
    add_child(camera)
    camera.look_at(Vector3(0.0, 1.35, -10.0), Vector3.UP)
    _build_player()

func _setup_hud() -> void:
    var canvas := CanvasLayer.new()
    canvas.name = "HUDLayer"
    canvas.layer = 20
    add_child(canvas)
    hud = preload("res://scripts/hud_3d.gd").new()
    hud.name = "HUD3D"
    hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
    canvas.add_child(hud)

func _build_player() -> void:
    player_root = Node3D.new()
    player_root.name = "Player"
    player_root.position = Vector3(LANE_X[SIDEWALK_CENTER], 0.0, PLAYER_Z)
    world_root.add_child(player_root)
    player_visual = RUNNER_CHARACTER_SCRIPT.new() as Node3D
    player_visual.name = "RunnerVisual"
    player_visual.set("character_id", CHARACTER_DATA.canonical_id(GameSave.equipped_character()))
    player_root.add_child(player_visual)
    # Lote23 — CharacterBody3D capsule 0.35×1.75, massa 75, fricção 0.4
    if PHYSICS_HANDLER != null:
        _player_physics_body = PHYSICS_HANDLER.setup_player_physics(player_root)
        _player_velocity_y = 0.0
        _is_on_floor_physics = true

func _rebuild_player_visual(character_id: String) -> void:
    if player_visual == null:
        return
    if player_visual.has_method("set_character"):
        player_visual.call("set_character", CHARACTER_DATA.canonical_id(character_id))

func _start_run(index: int) -> void:
    var clamped_index: int = clampi(index, 0, BALANCE.phase_count - 1)
    if not GameSave.is_phase_unlocked(clamped_index):
        _show_feedback("TELA BLOQUEADA", "Junte estrelas para liberar", RED, "ui_back")
        return
    selected_phase = clamped_index
    phase_index = clamped_index
    map_page = int(float(clamped_index) / 10.0)
    endless_mode = false
    phase = PhaseData.get_phase(phase_index)
    scenario = SCENARIO_DATA.get_profile(phase_index)
    _rebuild_player_visual(GameSave.equipped_character())
    _apply_scenario_atmosphere()
    _rebuild_sky_fx()
    screen = 2
    previous_screen = 1
    run_mode = "playing"
    distance = 0.0
    elapsed = 0.0
    run_total = float(phase["distance"])
    player_lane = SIDEWALK_CENTER
    player_x = LANE_X[player_lane]
    player_speed = _phase_speed_for(phase_index)
    # As fases-gate aumentam a leitura, não a punição: a reserva de três
    # corações permanece estável para que a dificuldade venha da pista.
    hearts = 3
    invulnerability = 0.0
    if player_visual != null:
        player_visual.visible = true
    GameSave.record_phase_attempt()
    if has_node("/root/AnalyticsManager"):
        var _am_run = get_node_or_null("/root/AnalyticsManager")
        if _am_run and _am_run.has_method("log_run_start"):
            _am_run.call("log_run_start", phase_index)
    max_hearts = hearts
    collected_coins = 0
    coin_multiplier = 1
    combo = 0
    combo_timer = 0.0
    run_score = 0
    no_damage = true
    jump_timer = 0.0
    slide_timer = 0.0
    dash_timer = 0.0
    dash_cooldown = 0.0
    dash_recharge_fast = false
    bus_wait_bonus = 0.0
    jump_duration = 0.9
    shield_hits = 0
    speed_boost_timer = 0.0
    slow_motion_timer = 0.0
    magnet_timer = 0.0
    rain_guard_timer = 0.0
    stop_wait = 0.0
    stop_wait_total = 0.0
    wall_run_count = 0
    dog_chase_timer = 0.0
    tutorial_stage = -1
    performance_sample_timer = 0.0
    step_timer = 0.0
    motion_speed = 0.0
    lane_change_velocity = 0.0
    course_root.position.z = 0.0
    var equipped: String = CHARACTER_DATA.canonical_id(GameSave.equipped_character())
    if equipped == "motoboy":
        speed_boost_timer = 9999.0
    elif equipped == "maria":
        shield_hits = 1
    elif equipped == "carlos":
        shield_hits = 1
    elif equipped == "luan":
        speed_boost_timer = 9999.0
    elif equipped == "joao":
        slow_motion_timer = 2.0
    elif equipped == "bia":
        magnet_timer = 9999.0
    elif equipped == "camila":
        coin_multiplier = 2
    elif equipped == "julia":
        jump_duration = 1.15
    elif equipped == "influencer":
        magnet_timer = 9999.0
    elif equipped == "chico":
        speed_boost_timer = 9999.0
    elif equipped == "tiao":
        jump_duration = 1.15
    elif equipped == "beto":
        dash_recharge_fast = true
    elif equipped == "nilo":
        hearts = 4
        max_hearts = 4
    elif equipped == "professor":
        slow_motion_timer = 2.0
    elif equipped == "marta":
        magnet_timer = 9999.0
    elif equipped == "zilda":
        shield_hits = 1
    elif equipped == "clara":
        hearts = 4
        max_hearts = 4
    elif equipped == "deise":
        speed_boost_timer = 9999.0
    elif equipped == "cida":
        bus_wait_bonus = 2.0
    if GameSave.owns("mochila"):
        shield_hits += 1
    if GameSave.owns("tenis"):
        speed_boost_timer = 9999.0
    if GameSave.owns("fone"):
        magnet_timer = 9999.0
    if GameSave.owns("cafe"):
        slow_motion_timer = 2.0
    _clear_course()
    _build_course()
    _apply_render_quality()              # Lote 2: clima do capítulo instantâneo
    _update_world_kit(0.0)               # Lote 3: rua acompanha o novo capítulo
    _trocar_clima_do_capitulo(phase_index)   # Lote 4: clima do capítulo
    # Lote 11: revive/2x reset por corrida
    _revive_used = false
    _double_used = false
    _rewarded_pending_placement = ""
    _update_banner_visibility()
    tutorial_hint = ""
    AudioManager.play_music(int(phase["music_group"]))
    _show_feedback("FAIXAS: RUA + CALÇADAS", str(phase["name"]), phase["accent"], "ui_confirm")

func _start_endless() -> void:
    if not GameSave.data.get("endless_unlocked", false):
        _show_feedback("ENDLESS BLOQUEADO", "Termine a Tela 50", RED, "ui_back")
        return
    _start_run(BALANCE.endless_unlock_phase)
    endless_mode = true
    run_total = 1000.0
    phase["name"] = "ENDLESS"
    phase["location"] = "ranking local"
    phase["special"] = "Rua, calçada e obstáculos sem parar."
    phase["distance"] = run_total
    phase["wait"] = 0.0
    _clear_course()
    _build_course()
    _show_feedback("ENDLESS 3D", "Bata seu recorde local", VIOLET, "streak")

func _clear_course() -> void:
    course_root.position.z = 0.0
    _destroi_world_kit()   # Lote 3: a rua e recriada no proximo _build_course
    _clear_sky_fx()
    _clear_ambient_fx()
    for child in decor_root.get_children():
        child.queue_free()
    for child in entity_root.get_children():
        child.queue_free()
    entities.clear()
    bus_node = null
    bus_stop_node = null

func _build_course() -> void:
    _build_track()
    _setup_world_kit()   # Lote 3: a rua nasce junto com o curso (distancia zero)
    # P2: reativa manchas de asfalto e bueiros como decal sobre o kit (building_kit rua)
    WorldSpawner.spawn_street_decals(self, run_total)
    _rebuild_sky_fx()
    _rebuild_ambient_fx()
    var total: float = run_total
    var obstacle_count: int = int(phase.get("obstacles", 6))
    # `obstacles` é uma intensidade de design, não uma contagem literal.
    # A curva começa espaçada para ensinar rota e chega a intervalos curtos
    # apenas no fim; a rua continua deliberadamente mais densa.
    var road_interval: float = clampf(26.0 - float(obstacle_count), 6.0, 24.0)
    var sidewalk_interval: float = maxf(15.0, road_interval * 2.1)
    var road_distance: float = 24.0
    var road_index := 0
    while road_distance < total - 18.0:
        var road_kind: String = ROAD_OBSTACLES[(road_index + phase_index) % ROAD_OBSTACLES.size()]
        _spawn_entity(road_kind, ROAD_LANE, road_distance, false)
        if phase_index >= 12 and road_index % 5 == 2:
            _spawn_entity("motorcycle", ROAD_LANE, road_distance + 2.8, false)
        road_distance += road_interval + rng.randf_range(-0.7, 1.0)
        road_index += 1
    var sidewalk_distance: float = 34.0
    var sidewalk_index := 0
    while sidewalk_distance < total - 20.0:
        var sidewalk_lane: int = SIDEWALK_CENTER if sidewalk_index % 2 == 0 else SIDEWALK_RIGHT
        var side_kind: String = SIDEWALK_OBSTACLES[(sidewalk_index + phase_index) % SIDEWALK_OBSTACLES.size()]
        _spawn_entity(side_kind, sidewalk_lane, sidewalk_distance, false)
        sidewalk_distance += sidewalk_interval + rng.randf_range(1.0, 3.0)
        sidewalk_index += 1
    var coin_distance: float = 18.0
    var coin_index := 0
    while coin_distance < total - 12.0:
        var coin_lane: int = [ROAD_LANE, SIDEWALK_CENTER, SIDEWALK_RIGHT][(coin_index + phase_index) % 3]
        _spawn_entity("coin", coin_lane, coin_distance, true)
        if coin_index % 5 == 0 and phase_index >= 2:
            _spawn_entity(_bonus_kind_for_phase(), SIDEWALK_CENTER + (coin_index % 2), coin_distance + 4.0, true)
        coin_distance += 13.0 + rng.randf_range(-0.8, 1.4)
        coin_index += 1
    _spawn_forced_gags(total)
    _create_bus_stop(total)
    call_deferred("_audit_world_geometry")

func _audit_world_geometry() -> void:
    for pair in [["decor", decor_root], ["entities", entity_root], ["course", course_root]]:
        var label: String = str(pair[0])
        var root: Node3D = pair[1]
        if root == null:
            continue
        if root.find_children("*", "MeshInstance3D", true, false).is_empty():
            push_warning("3D asset contract: raiz %s sem MeshInstance3D" % label)

func _spawn_forced_gags(total: float) -> void:
    var forced: Array[String] = []
    match phase_index:
        1: forced = ["bread", "hydrant"]
        3: forced = ["vendor", "pothole"]
        5: forced = ["vendor", "bicycle"]
        6: forced = ["bus_traffic", "dog"]
        7: forced = ["cone", "pothole"]
        8: forced = ["pothole", "car", "pothole"]
        9: forced = ["motorcycle", "old_lady"]
        10: forced = ["dog", "dog", "old_lady"]
        13: forced = ["dog", "bicycle"]
        14: forced = ["hydrant", "pothole"]
        17: forced = ["truck", "cone"]
        18: forced = ["dog", "motorcycle", "truck"]
        19: forced = ["truck", "bus_traffic", "dog", "payphone", "motorcycle"]
        _: forced = ["car", "cone"]
    if phase_index >= 20:
        forced = [
            ["bus_traffic", "pix", "motorcycle", "hydrant", "dog"],
            ["car", "umbrella", "dog", "payphone", "bus_traffic"],
            ["motorcycle", "bicycle", "pothole", "vendor", "dog"],
            ["truck", "car", "dog", "umbrella", "motorcycle"],
            ["bus_traffic", "pothole", "vendor", "truck", "dog"],
            ["car", "payphone", "motorcycle", "hydrant", "truck"]
        ][mini(5, int(float(phase_index - 20) / 5.0))]
    for i in forced.size():
        var forced_distance: float = 72.0 + float(i) * maxf(16.0, (total - 110.0) / maxf(1.0, float(forced.size())))
        var forced_lane: int = ROAD_LANE if str(forced[i]) in ROAD_OBSTACLES else (SIDEWALK_CENTER + (i % 2))
        _spawn_entity(str(forced[i]), forced_lane, forced_distance, str(forced[i]) in COLLECTIBLES)

func _bonus_kind_for_phase() -> String:
    return WorldSpawner.bonus_kind_for_phase(phase_index, distance)

func _spawn_entity(kind: String, lane: int, entity_distance: float, collectible: bool) -> void:
    var node := Node3D.new()
    node.name = "%s_%03d" % [kind, entities.size()]
    node.position = Vector3(LANE_X[clampi(lane, 0, 2)], 0.0, -entity_distance)
    entity_root.add_child(node)
    if collectible:
        _build_collectible(node, kind)
    elif lane == ROAD_LANE:
        _build_road_obstacle(node, kind)
    else:
        _build_sidewalk_obstacle(node, kind)
    # Lote 23 — Física: RigidBody/Static/Area por kind (freeze, massa, fricção)
    if PHYSICS_HANDLER != null and not collectible:
        var _pb := PHYSICS_HANDLER.setup_obstacle_physics(node, kind)
        if kind == "pothole" and _pb is Area3D:
            var _area := _pb as Area3D
            if not _area.body_entered.is_connected(_on_pothole_entered):
                _area.body_entered.connect(_on_pothole_entered)
            if not _area.body_exited.is_connected(_on_pothole_exited):
                _area.body_exited.connect(_on_pothole_exited)
    var traffic_speed: float = _traffic_speed_for(kind, entities.size()) if lane == ROAD_LANE and not collectible else 0.0
    if traffic_speed > player_speed:
        # Veículo mais rápido que o corredor: nasce ATRÁS dele, na posição em
        # que — mantendo as velocidades — a ultrapassagem acontece exatamente
        # quando o jogador estiver em `entity_distance` (mesma leitura de
        # design das fases). z0 = d·(v_t/v_p − 1) > 0 (atrás da câmera).
        node.position.z = entity_distance * (traffic_speed / maxf(0.1, player_speed) - 1.0)
    # Comportamento por tipo: nada de espantalho parado. A velhinha caminha
    # de frente para o corredor, o caramelo corre (e late de verdade no
    # world_animal), o vendedor fica no seu ponto conversando com a rua.
    var mobility := 0.0
    if not collectible and lane != ROAD_LANE:
        if kind == "old_lady":
            mobility = 0.55   # caminha de frente para o corredor (o modelo ja olha +Z)
        elif kind == "dog":
            mobility = 1.8
            node.rotation.y = -PI / 2.0   # o caramelo modelado olha +X; vira para +Z
            var cachorro := node.get_node_or_null("Animal3D_caramelo")
            if cachorro != null and cachorro.has_method("set_running"):
                cachorro.call("set_running", true)
    entities.append({
        "node": node,
        "kind": kind,
        "lane": lane,
        "distance": entity_distance,
        "passed": false,
        "collectible": collectible,
        "traffic_speed": traffic_speed,
        "mobility": mobility,
        "prev_z": node.position.z + distance
    })
    call_deferred("_audit_3d_entity", node, kind, collectible)

func _audit_3d_entity(node: Node3D, kind: String, collectible: bool) -> void:
    if not is_instance_valid(node):
        return
    var meshes := node.find_children("*", "MeshInstance3D", true, false)
    if meshes.is_empty():
        push_warning("3D asset contract: %s não criou MeshInstance3D" % kind)
        return
    if collectible:
        return
    if kind in ["old_lady", "vendor"] and node.find_child("HumanPedestrian3D", true, false) == null:
        push_warning("3D asset contract: %s não contém personagem humano skinned" % kind)
    if kind == "dog" and node.find_child("Animal3D_caramelo", true, false) == null:
        push_warning("3D asset contract: cachorro sem Animal3D_caramelo")

func _traffic_speed_for(kind: String, seed_index: int) -> float:
    return WorldSpawner.traffic_speed_for(kind, seed_index, player_speed)

func _animate_traffic(node: Node3D, speed: float, dt: float) -> void:
    # Rolagem sem deslizar: ângulo = distância / raio. O sinal negativo faz o
    # topo da roda avançar para -Z (sentido do tráfego). O raio vem do pivô
    # (GLB, ver _pivot_wheels) ou da AABB do cilindro procedural.
    var stack: Array[Node] = [node]
    while not stack.is_empty():
        var current: Node = stack.pop_back()
        if current == node or not current is Node3D:
            stack.append_array(current.get_children())
            continue
        var wheel_name := str(current.name)
        if wheel_name.begins_with("Wheel") or wheel_name.begins_with("BusWheel") or wheel_name.begins_with("MotoWheel"):
            (current as Node3D).rotation.x -= speed * dt / _wheel_radius(current as Node3D)
            continue  # não desce: a malha filha do pivô já gira junto
        stack.append_array(current.get_children())
    var body_bob: float = sin(pulse * 4.0 + node.position.z * 0.14) * 0.006
    node.position.y = body_bob

func _wheel_radius(wheel: Node3D) -> float:
    if wheel.has_meta("wheel_radius"):
        return maxf(0.05, float(wheel.get_meta("wheel_radius")))
    if wheel is MeshInstance3D and (wheel as MeshInstance3D).mesh != null:
        var aabb := (wheel as MeshInstance3D).mesh.get_aabb()
        # cilindro procedural: eixo Y local (height) é a largura; raio = maior dos outros
        var r: float = maxf(aabb.size.x, aabb.size.z) * 0.5
        wheel.set_meta("wheel_radius", r)
        return maxf(0.05, r)
    return 0.30

const VEHICLE_HALF_LENGTH := {"car": 2.1, "motorcycle": 1.05, "truck": 3.1, "bus_traffic": 3.6}
const TRAFFIC_MIN_GAP := 2.2  # metros livres entre para-choques em pelotão

func _harmonize_traffic(dt: float) -> void:
    # Tráfego em harmonia: ninguém atravessa ninguém. Veículos da faixa da rua
    # são ordenados por posição (menor z = mais à frente, pois andam para -Z);
    # quem alcança o da frente assume a velocidade dele e mantém a distância
    # de segurança (car-following). A velocidade harmonizada fica gravada na
    # entidade, formando pelotões estáveis em vez de ultrapassagens fantasmas.
    var vehicles: Array[Dictionary] = []
    for entity in entities:
        if bool(entity["collectible"]):
            continue
        if float(entity.get("traffic_speed", 0.0)) <= 0.0:
            continue
        if not VEHICLE_HALF_LENGTH.has(str(entity["kind"])):
            continue
        if not is_instance_valid(entity["node"]):
            continue
        vehicles.append(entity)
    if vehicles.size() < 2:
        return
    vehicles.sort_custom(func(a, b): return (a["node"] as Node3D).position.z < (b["node"] as Node3D).position.z)
    for i in range(1, vehicles.size()):
        var ahead: Dictionary = vehicles[i - 1]
        var me: Dictionary = vehicles[i]
        var ahead_node: Node3D = ahead["node"]
        var my_node: Node3D = me["node"]
        var min_gap: float = float(VEHICLE_HALF_LENGTH[str(ahead["kind"])]) + float(VEHICLE_HALF_LENGTH[str(me["kind"])]) + TRAFFIC_MIN_GAP
        var gap: float = my_node.position.z - ahead_node.position.z
        var ahead_speed: float = float(ahead["traffic_speed"])
        var my_speed: float = float(me["traffic_speed"])
        if gap < min_gap:
            my_node.position.z = ahead_node.position.z + min_gap
            if my_speed > ahead_speed:
                me["traffic_speed"] = ahead_speed
        elif my_speed > ahead_speed and gap < min_gap + my_speed * 1.6:
            # aproximação: desacelera suavemente antes de colar (sem "freada" seca)
            me["traffic_speed"] = maxf(ahead_speed, my_speed - (my_speed - ahead_speed) * minf(1.0, dt * 2.5))

func _update_tutorial_hint() -> void:
    if phase_index != 0 or bool(GameSave.data.get("tutorial_seen", false)):
        tutorial_hint = ""
        return
    var next_stage := 0
    var next_hint := "DESLIZE ← → para trocar de faixa"
    if distance >= 18.0 and distance < 40.0:
        next_stage = 1
        next_hint = "TOQUE rápido para usar o DASH"
    elif distance >= 40.0 and distance < BALANCE.first_session_hint_distance:
        next_stage = 2
        next_hint = "↑ pula • ↓ desliza • escolha sua rota"
    elif distance >= BALANCE.first_session_hint_distance:
        next_stage = 3
        next_hint = "Boa leitura. Agora corra do seu jeito."
    if next_stage != tutorial_stage:
        tutorial_stage = next_stage
        GameSave.record_event("tutorial_step")
    tutorial_hint = next_hint
    if tutorial_stage >= 3:
        GameSave.data["tutorial_seen"] = true
        GameSave.flush()
        tutorial_hint = ""
    # Lote 16: seta 3D
    var _show_arrow: bool = not bool(GameSave.data.get("tutorial_seen", false)) and distance < float(BALANCE.first_session_hint_distance) and screen == 2 and run_mode == "playing"
    _update_tutorial_arrow(_show_arrow, player_lane)

func _update_run(dt: float) -> void:
    if run_mode == "paused":
        return
    if run_mode == "at_stop":
        stop_wait = maxf(0.0, stop_wait - dt)
        if stop_wait <= 0.0:
            # Chegar ao ponto é a vitória; o toque apenas embarca antes do
            # fim da contagem, em vez de transformar uma vitória em punição.
            _finish_run(true)
        return
    elapsed += dt
    run_phase += dt * (8.0 + player_speed)
    jump_timer = maxf(0.0, jump_timer - dt)
    slide_timer = maxf(0.0, slide_timer - dt)
    dash_timer = maxf(0.0, dash_timer - dt)
    dash_cooldown = maxf(0.0, dash_cooldown - dt)
    combo_timer = maxf(0.0, combo_timer - dt)
    speed_boost_timer = maxf(0.0, speed_boost_timer - dt)
    slow_motion_timer = maxf(0.0, slow_motion_timer - dt)
    magnet_timer = maxf(0.0, magnet_timer - dt)
    rain_guard_timer = maxf(0.0, rain_guard_timer - dt)
    dog_chase_timer = maxf(0.0, dog_chase_timer - dt)
    if combo_timer <= 0.0:
        combo = 0
    var speed: float = player_speed
    if speed_boost_timer > 0.0:
        speed *= 1.22
    if slow_motion_timer > 0.0:
        speed *= 0.55
    if dash_timer > 0.0:
        speed *= 2.0
    # L27 polimento: fricção por superfície (dirt 0.88×, cobble 0.82× vs asfalto 1.0)
    var surface_factor: float = 1.0
    if scenario.has("street_surface"):
        surface_factor = PhysicsHandler.surface_speed_factor(str(scenario["street_surface"]))
    speed *= surface_factor
    distance += speed * dt
    _update_tutorial_hint()
    motion_speed = lerpf(motion_speed, speed, minf(1.0, dt * 7.0))
    course_root.position.z = distance
    step_timer -= dt
    if step_timer <= 0.0:
        var step_sfx := "step_calcada"
        if player_lane == 0:
            var surface: String = str(scenario.get("street_surface", "asphalt"))
            step_sfx = "step_terra" if surface == "dirt" else "step_asfalto"
        AudioManager.play_sfx(step_sfx, -13.0, 0.92 + fmod(run_phase, 0.4))
        step_timer = maxf(0.18, 0.34 - motion_speed * 0.009)
    if invulnerability > 0.0:
        invulnerability = maxf(0.0, invulnerability - dt)
        if player_visual != null and hearts > 0:
            player_visual.visible = (int(invulnerability * 12.0) % 2 == 0)
    elif player_visual != null and not player_visual.visible and hearts > 0:
        player_visual.visible = true
    _harmonize_traffic(dt)
    for entity in entities:
        var node: Node3D = entity["node"]
        var traffic_speed: float = float(entity.get("traffic_speed", 0.0))
        if traffic_speed > 0.0 and is_instance_valid(node):
            # Tráfego avança no sentido da avenida (-Z), mais rápido que o
            # corredor: os veículos vêm por trás, ultrapassam e somem à frente.
            # Continua rodando mesmo depois de "passed" — um carro parado no
            # meio da pista seria atravessado pelo jogador.
            node.position.z -= traffic_speed * dt
            _animate_traffic(node, traffic_speed, dt)
            if bool(entity["passed"]):
                if node.position.z + distance < -140.0:
                    node.queue_free()
                    entity["traffic_speed"] = 0.0
                continue
        if bool(entity["passed"]):
            continue
        if bool(entity["collectible"]):
            node.rotation.y += dt * 2.6
        var mobility: float = float(entity.get("mobility", 0.0))
        if mobility > 0.0:
            # pedestres/animais andam na direção do corredor (+Z local); a
            # colisão abaixo usa a posição real do nó, então nada mais muda.
            node.position.z += mobility * dt
        var entity_z: float = node.position.z + distance
        var prev_z: float = float(entity.get("prev_z", entity_z))
        entity["prev_z"] = entity_z
        # Cruzamento do corredor em QUALQUER sentido: obstáculo/coletável
        # alcançado pelo jogador (entity_z sobe até 0.6) ou veículo rápido
        # que vem por trás e ultrapassa (entity_z desce e cruza 0.0).
        var crossed_forward: bool = entity_z >= 0.6 and prev_z < 0.6
        var crossed_from_behind: bool = traffic_speed > 0.0 and prev_z > 0.0 and entity_z <= 0.0
        if crossed_forward or crossed_from_behind:
            entity["passed"] = true
            _resolve_entity(entity)
    if distance >= run_total:
        distance = run_total
        course_root.position.z = distance
        if endless_mode:
            _finish_run(true)
            return
        run_mode = "at_stop"
        stop_wait_total = _phase_wait_for(phase_index) if not endless_mode else 0.0
        stop_wait_total += bus_wait_bonus
        stop_wait = stop_wait_total
        if bus_stop_node:
            bus_stop_node.visible = true
        if bus_node:
            bus_node.visible = true
        _show_feedback("CHEGOU NO PONTO!", "SEGURA O BUSÃO!" if bus_wait_bonus <= 0.0 else "MOTORISTA ACIONADA: +2s", YELLOW, "horn")
    if hearts <= 0:
        # Lote 16: tela Reviver? 5 s (ASSISTIR -30s vs DESISTIR) antes de _finish_run
        if not _revive_used and not _revive_pending:
            _show_revive_screen()
        else:
            _finish_run(false, true)

func _resolve_entity(entity: Dictionary) -> void:
    var kind: String = str(entity["kind"])
    var lane: int = int(entity["lane"])
    var pos: Vector3 = Vector3(LANE_X[lane], 1.0, PLAYER_Z)
    if bool(entity["collectible"]):
        if lane == player_lane or magnet_timer > 0.0:
            _collect(kind, pos)
        return
    if lane != player_lane:
        return
    # Lote23 — detecção por shape quando física ativa (hearts só perde se shape intersecta fora de invencível)
    var use_physics: bool = physics_realista_enabled and _player_physics_body != null
    var obstacle_body: Node = null
    if use_physics:
        var ent_node: Node3D = entity["node"] as Node3D
        obstacle_body = ent_node.get_node_or_null("PhysicsBody")
        # pothole Area3D fricção 0.15 e impulso -Y 3 já está no handler; aqui só checa shape
        if PHYSICS_HANDLER.should_lose_heart(_player_physics_body, obstacle_body, dash_timer, false) == false and not (jump_timer > 0.0 or dash_timer > 0.0 or slide_timer > 0.0):
            # shape não intersectaria, mas mantém fallback lane para não quebrar arcade
            pass
    var safe := false
    if kind in ["car", "bus_traffic", "motorcycle", "truck", "pothole"]:
        safe = jump_timer > 0.0 or dash_timer > 0.0
    elif kind in ["old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench"]:
        safe = jump_timer > 0.0 or slide_timer > 0.0 or dash_timer > 0.0
    if kind == "dog":
        dog_chase_timer = 10.0
        var dog_entity_node: Node3D = entity["node"]
        var dog_node := dog_entity_node.get_node_or_null("Animal3D_caramelo") as Node3D
        if dog_node and dog_node.has_method("set_running"):
            dog_node.call("set_running", true)
        _show_feedback("CARAMELO!", "10 segundos na sua cola", RED, "bark")
    if safe:
        _show_feedback("DESVIO LIMPO", _reaction_for(kind), GOLD, "reward")
        _spawn_3d_burst(pos + Vector3(0, 1.0, -0.6), GOLD, 10)
    else:
        _hit_player(kind)

func _collect(kind: String, pos: Vector3) -> void:
    var value := 1
    if kind == "coin":
        value = coin_multiplier
        collected_coins += 1
        combo += 1
        combo_timer = 4.0
        run_score += value * 10 * maxi(1, combo)
        _show_feedback("+R$ 0,25", "COMBO x%02d" % combo, GOLD, "coin")
        if combo >= 5 and combo % 5 == 0:
            _show_feedback("COMBO x%02d" % combo, "A rua está pagando", CYAN, "combo")
        if combo >= 15:
            GameSave.award_badge("combo15")
    else:
        _show_feedback("BÔNUS!", str(COLLECTIBLES.get(kind, kind)), GOLD, "reward")
        match kind:
            "coffee":
                slow_motion_timer = 5.0
            "bread":
                jump_duration = 1.25
            "pastel":
                shield_hits = 1
            "sugarcane":
                speed_boost_timer = 6.0
            "pass":
                coin_multiplier = 2
            "coxinha":
                shield_hits = 2
            "guarana":
                speed_boost_timer = 9.0
            "pix":
                coin_multiplier = 3
            "umbrella":
                rain_guard_timer = 12.0
            "golden":
                if GameSave.unlock_pet("caramelo"):
                    _show_feedback("SKIN LIBERADA", "Cachorro Caramelo entrou no time", GOLD, "reward")
    GameSave.add_coins(value)
    _spawn_3d_burst(pos + Vector3(0, 1.0, 0), GOLD, 8)

func _hit_player(kind: String) -> void:
    if dash_timer > 0.0 or invulnerability > 0.0:
        return
    GameSave.record_event("hit_" + kind)
    if has_node("/root/AnalyticsManager"):
        var _am_hit = get_node_or_null("/root/AnalyticsManager")
        if _am_hit and _am_hit.has_method("log_hit"):
            _am_hit.call("log_hit", kind)
    if shield_hits > 0:
        shield_hits -= 1
        invulnerability = 0.85
        _show_feedback("ESCUDO!", "Impacto absorvido", CYAN, "hit")
        _spawn_3d_burst(player_root.position + Vector3(0, 1.0, 0), CYAN, 14)
        return
    hearts -= 1
    no_damage = false
    invulnerability = 1.15
    camera_shake = 0.38
    flash_alpha = 0.22
    var heart_label: String = "1 coração" if hearts == 1 else "%d corações" % hearts
    var sound := "shout" if kind == "motorcycle" else "impact_heavy"
    _show_feedback("AI!", heart_label + " restante", RED, sound)
    _spawn_3d_burst(player_root.position + Vector3(0, 1.0, 0), RED, 18)
    # Lote23 — ragdoll quando hearts==0 via PhysicalBone3D
    if hearts <= 0 and physics_realista_enabled and player_visual != null:
        PHYSICS_HANDLER.setup_ragdoll(player_visual)
    if kind == "dog":
        GameSave.data["dog_hits"] = int(GameSave.data.get("dog_hits", 0)) + 1
        if int(GameSave.data["dog_hits"]) >= 10:
            GameSave.award_achievement("dog")
        GameSave.save()

func _change_lane(direction: int) -> void:
    if screen != 2 or run_mode != "playing":
        return
    var old_lane: int = player_lane
    player_lane = clampi(player_lane + direction, ROAD_LANE, SIDEWALK_RIGHT)
    if old_lane != player_lane:
        lane_change_velocity = float(direction) * 1.0
        GameSave.record_event("lane_change")
        _show_feedback("FAIXA %s" % ["RUA", "CALÇADA", "CALÇADA"][player_lane], "Leitura perfeita", BLUE, "whoosh")

func _jump() -> void:
    if screen != 2 or run_mode != "playing" or jump_timer > 0.0 or slide_timer > 0.0:
        return
    # Lote23 — head clearance raycast quando física realista (snap 0.4)
    if physics_realista_enabled and _player_physics_body != null and not _is_on_floor_physics:
        return
    var jumper: String = CHARACTER_DATA.canonical_id(GameSave.equipped_character())
    if jumper == "julia" or jumper == "tiao":
        jump_duration = 1.15
    else:
        jump_duration = 0.9
    jump_timer = jump_duration
    # Lote23 — impulso 6.3 N·s, gravidade 9.81 → parábola 1.28 s
    if physics_realista_enabled and _player_physics_body != null:
        _player_velocity_y = PHYSICS_HANDLER.PLAYER_JUMP_IMPULSE
        _is_on_floor_physics = false
    GameSave.record_event("jump")
    _show_feedback("PULO!", "Rota aérea", CYAN, "jump")
    _spawn_3d_burst(player_root.position + Vector3(0, 0.1, 0), CYAN, 7)

func _slide() -> void:
    if screen != 2 or run_mode != "playing" or jump_timer > 0.0:
        return
    # Lote23 — slide = crouch com head clearance raycast 0.4 quando física
    if physics_realista_enabled and _player_physics_body != null:
        var space := _player_physics_body.get_world_3d().direct_space_state if _player_physics_body.get_world_3d() else null
        if space != null:
            var from := _player_physics_body.global_position + Vector3(0, 1.6, 0)
            var to := from + Vector3(0, 0.4, 0)
            var query := PhysicsRayQueryParameters3D.create(from, to)
            query.exclude = [_player_physics_body.get_rid()]
            var hit := space.intersect_ray(query)
            if not hit.is_empty():
                return
    slide_timer = 0.72
    GameSave.record_event("slide")
    _show_feedback("DESLIZE!", "Passou por baixo", VIOLET, "slide")

func _dash() -> void:
    if screen != 2 or run_mode != "playing" or dash_cooldown > 0.0:
        return
    dash_timer = 0.42
    dash_cooldown = 1.9 if dash_recharge_fast else 3.2
    # Lote23 — dash = impulse 900 N·s, cooldown 3.2 (physics)
    if physics_realista_enabled and _player_physics_body != null:
        # impulso lateral já via lane_change_velocity; dash mantém invencível 0.42
        _player_velocity_y = maxf(_player_velocity_y, 0.0)
    GameSave.record_event("dash")
    camera_shake = 0.18
    _show_feedback("DASH!", "Invencível por um instante", YELLOW, "whoosh")
    _spawn_3d_burst(player_root.position + Vector3(0, 1.0, 0), YELLOW, 18)

func _catch_bus() -> void:
    if run_mode == "at_stop":
        _finish_run(true)

func _finish_run(success: bool, game_over := false) -> void:
    # P2 EconomyHandler disponível para reward/XP (cálculo espelhado)
    if screen != 2:
        return
    var date_key := Time.get_date_string_from_system()
    GameSave.record_daily_progress(date_key, int(distance), collected_coins, success and no_damage)
    GameSave.record_weekly_progress(GameSave.weekly_key(), int(distance), collected_coins, success and no_damage)
    if endless_mode:
        GameSave.record_endless_result(success, elapsed, int(distance))
        if success:
            var old_best: int = int(GameSave.data.get("endless_best", 0))
            var is_record: bool = int(distance) > old_best
            if is_record:
                GameSave.data["endless_best"] = int(distance)
            var distance_bonus: int = mini(33, int(distance / 30.0))
            var first_score_reward: int = 20 + distance_bonus + mini(15, collected_coins)
            # Endless replay tem valor, mas não pode virar uma impressora de moedas.
            var reward: int = first_score_reward + (25 if is_record else 0)
            if not is_record:
                reward = mini(reward, BALANCE.replay_reward + distance_bonus)
            GameSave.add_coins(reward)
            # Lote 17: bônus semanal
            if has_node("/root/EconomyManager"):
                var _em_w2 = get_node_or_null("/root/EconomyManager")
                if _em_w2 and _em_w2.has_method("get_weekly_bonus_coins"):
                    var _wb2: int = int(_em_w2.call("get_weekly_bonus_coins"))
                    if _wb2 > 0:
                        GameSave.add_coins(_wb2)
                        reward += _wb2
            var xp_reward := 40 + int(distance / 12.0) if is_record else BALANCE.xp_replay
            GameSave.add_xp(xp_reward)
            result = {
                "success": true,
                "endless": true,
                "reward": reward,
                "time": elapsed,
                "coins": collected_coins,
                "record": is_record,
                "distance": int(distance),
                "xp": xp_reward
            }
            _show_feedback("ENDLESS CONCLUÍDO!", "%dm • +R$ %d de bônus" % [int(distance), reward], VIOLET, "streak")
        else:
            result = {
                "success": false,
                "endless": true,
                "reward": 0,
                "time": elapsed,
                "coins": collected_coins,
                "record": false,
                "game_over": game_over,
                "distance": int(distance),
                "xp": 0
            }
            _show_feedback("MAIS UM!", "Seu melhor corre ainda está aí", RED, "impact_heavy")
        GameSave.flush()
        _push_play_progress()
        _maybe_request_review()
        run_mode = "results"
        screen = 3
        _update_banner_visibility()
        if not success:
            _try_show_interstitial_after_defeat()
        _sync_hud()
        return
    GameSave.record_phase_result(success, phase_index, elapsed, int(distance))
    if success:
        # A regra das estrelas é explícita: terminar, não sofrer dano e cumprir
        # a meta de moedas. Tempo serve para recorde, não para esconder a regra.
        var stars := 1
        if no_damage:
            stars += 1
        if collected_coins >= int(phase["coin_target"]):
            stars += 1
        var previous_stars := GameSave.phase_stars(phase_index)
        var previous_time: float = GameSave.best_time(phase_index)
        var record: bool = previous_time <= 0.0 or elapsed < previous_time
        var record_info: Dictionary = GameSave.record_phase(phase_index, stars, elapsed)
        var first_clear: bool = bool(record_info.get("first_clear", false))
        var new_stars: int = int(record_info.get("new_stars", 0))
        var base_reward: int = BALANCE.first_clear_reward if first_clear else BALANCE.replay_reward
        var level_reward: int = phase_index * BALANCE.phase_reward_per_level if first_clear else 0
        var star_reward: int = stars * BALANCE.star_reward if first_clear else new_stars * BALANCE.star_upgrade_reward
        var perfect_reward: int = BALANCE.perfect_run_bonus if no_damage and first_clear else 0
        var reward: int = base_reward + level_reward + star_reward + perfect_reward
        var xp_reward: int = (BALANCE.xp_first_clear + phase_index * BALANCE.xp_per_level) if first_clear else BALANCE.xp_replay + new_stars * 5
        GameSave.add_coins(reward)
        # Lote 17: bônus semanal LiveOps
        if has_node("/root/EconomyManager"):
            var _em_w3 = get_node_or_null("/root/EconomyManager")
            if _em_w3 and _em_w3.has_method("get_weekly_bonus_coins"):
                var _wb3: int = int(_em_w3.call("get_weekly_bonus_coins"))
                if _wb3 > 0:
                    GameSave.add_coins(_wb3)
                    reward += _wb3
        GameSave.add_xp(xp_reward)
        if phase_index == 8 and no_damage:
            GameSave.award_achievement("enchente")
        if no_damage:
            GameSave.award_badge("sem_arranhao")
        if phase_index == BALANCE.chapter_unlock_phase:
            GameSave.award_achievement("busao")
            GameSave.award_badge("capitulo1")
        if phase_index == BALANCE.phase_count - 1:
            GameSave.award_achievement("busao50")
            GameSave.award_badge("maratonista")
            GameSave.data["endless_unlocked"] = true
        result = {
            "success": true,
            "stars": stars,
            "previous_stars": previous_stars,
            "new_stars": new_stars,
            "first_clear": first_clear,
            "reward": reward,
            "bonus_reward": reward,
            "reward_breakdown": {
                "base": base_reward,
                "level": level_reward,
                "stars": star_reward,
                "perfect": perfect_reward
            },
            "time": elapsed,
            "coins": collected_coins,
            "record": record,
            "xp": xp_reward
        }
        _show_feedback("PEGUEI O BUSÃO!", "%d estrelas • +R$ %d de bônus" % [stars, reward], YELLOW, "streak")
        _spawn_3d_burst(Vector3(player_x, 1.4, -8.0), YELLOW, 28)
        if GameSave.owns("confete"):
            _spawn_3d_burst(Vector3(player_x, 1.8, -8.0), RED, 10)
            _spawn_3d_burst(Vector3(player_x, 1.8, -8.0), CYAN, 10)
    else:
        result = {
            "success": false,
            "stars": 0,
            "reward": 0,
            "time": elapsed,
            "coins": collected_coins,
            "game_over": game_over,
            "record": false,
            "xp": 0
        }
        _show_feedback("O BUSÃO FOI EMBORA", "Use as três faixas a seu favor", RED, "impact_heavy")
    GameSave.flush()
    _push_play_progress()
    _maybe_request_review()
    run_mode = "results"
    screen = 3
    _update_banner_visibility()
    if not success:
        _try_show_interstitial_after_defeat()
    _sync_hud()

func _reaction_for(kind: String) -> String:
    var reactions: Dictionary = {
        "car": "Carro no retrovisor!",
        "bus_traffic": "Ônibus desviado no susto!",
        "motorcycle": "Moto passou raspando!",
        "truck": "Caminhão vencido no timing!",
        "pothole": "Buraco ficou para trás!",
        "old_lady": "A velha do celular nem viu!",
        "hydrant": "Hidrante superado!",
        "payphone": "Orelhão desconectado!",
        "dog": "Caramelo deixado para trás!",
        "bicycle": "Bicicleta sem freio!",
        "cone": "Obra vencida!",
        "vendor": "Camelô abriu passagem!",
        "bench": "Banco de praça não segura o Zé!"
    }
    return str(reactions.get(kind, "Boa, Zé!"))

func _update_player(dt: float) -> void:
    if player_root == null:
        return
    var previous_x: float = player_x
    # Lote23 — desvio realista: lane via lerp arcade, mas com snap 0.4 quando física ativa
    var lerp_speed: float = 13.0 if not physics_realista_enabled else 9.0
    player_x = lerpf(player_x, LANE_X[player_lane], minf(1.0, dt * lerp_speed))
    lane_change_velocity = lerpf(lane_change_velocity, (player_x - previous_x) * 8.0, minf(1.0, dt * 8.0))
    player_root.position.x = player_x
    # Lote23 — pulo parábola realista quando physics_realista_enabled
    var jump_height: float = 0.0
    if physics_realista_enabled and _player_physics_body != null:
        # gravidade 9.81, snap 0.4, jump impulse 6.3 → parábola ~1.28 s (medida audit)
        if not _is_on_floor_physics:
            _player_velocity_y -= PHYSICS_HANDLER.GRAVITY * dt
        var next_y: float = player_visual.position.y + _player_velocity_y * dt
        if next_y <= 0.0:
            next_y = 0.0
            _player_velocity_y = 0.0
            _is_on_floor_physics = true
            jump_timer = 0.0
        else:
            _is_on_floor_physics = false
        jump_height = next_y
        # mantém jump_timer para compat com HUD mas não usa sin
        if jump_timer > 0.0 and _is_on_floor_physics and _player_velocity_y == 0.0:
            # aciona impulso já em _jump()
            pass
    else:
        var jump_progress: float = 1.0 - jump_timer / maxf(jump_duration, 0.01)
        jump_height = sin(jump_progress * PI) * 2.05 if jump_timer > 0.0 else 0.0
    var is_running: bool = screen == 2 and run_mode == "playing"
    var is_crouching: bool = slide_timer > 0.0
    var bob: float = sin(run_phase * 1.6) * 0.045 if is_running and not is_crouching else 0.0
    player_visual.position.y = jump_height + bob - (0.16 if is_crouching else 0.0)
    # The authored crouch clip handles the silhouette. A small root compression
    # preserves the arcade read without flattening the imported skeleton.
    var squash: float = 0.94 if is_crouching else 1.0
    player_visual.scale = Vector3(1.02 if is_crouching else 1.0, squash, 1.02 if is_crouching else 1.0)
    var shadow := player_visual.get_node_or_null("RunnerShadow") as Node3D
    if shadow:
        shadow.position.y = 0.025 - player_visual.position.y
        var shadow_factor: float = 1.0 - clampf(jump_height * 0.12, 0.0, 0.24)
        shadow.scale = Vector3.ONE * shadow_factor
    if player_visual.has_method("set_motion"):
        player_visual.call("set_motion", run_phase, is_running, is_crouching, jump_height, lane_change_velocity, motion_speed, dt)
    var lane_lean: float = clampf(lane_change_velocity * 0.06, -0.15, 0.15)
    var target_lean: float = -lane_lean
    player_visual.rotation.z = lerpf(player_visual.rotation.z, target_lean, minf(1.0, dt * 9.0))
    player_visual.rotation.x = lerpf(player_visual.rotation.x, -0.035 if is_running else 0.0, minf(1.0, dt * 7.0))

# Lote23 — física Bullet: CharacterBody3D com gravidade 9.81, snap 0.4, e pothole Area3D friction 0.15
func _physics_process(_delta: float) -> void:
    if not physics_realista_enabled or _player_physics_body == null:
        return
    # gravidade e snap já tratados em _update_player, aqui move_and_slide para colisão contínua
    var vel := Vector3(lane_change_velocity * 2.2, _player_velocity_y, 0.0)
    _player_physics_body.velocity = vel
    # snap ao chão quando não pulando
    if _is_on_floor_physics:
        _player_physics_body.velocity.y = -PHYSICS_HANDLER.PLAYER_SNAP
    _player_physics_body.move_and_slide()
    _is_on_floor_physics = _player_physics_body.is_on_floor()
    # road_surface friction override e pothole impulse -Y 3 já via Area3D meta; aqui aplica desaceleração
    if _player_physics_body.is_on_floor() and _player_physics_body.get_slide_collision_count() > 0:
        for i in _player_physics_body.get_slide_collision_count():
            var col := _player_physics_body.get_slide_collision(i)
            var n := col.get_collider() as Node
            if n != null and n.has_meta("pothole_friction"):
                var fric: float = float(n.get_meta("pothole_friction"))
                _player_velocity_y = PHYSICS_HANDLER.POTHOLE_IMPULSE_Y
                motion_speed *= (1.0 - fric)
                break

func _on_pothole_entered(body: Node) -> void:
    if body != _player_physics_body:
        return
    # Lote23 — pothole Area3D friction 0.15 e impulse -Y 3
    _player_velocity_y = PHYSICS_HANDLER.POTHOLE_IMPULSE_Y
    motion_speed *= (1.0 - PHYSICS_HANDLER.POTHOLE_FRICTION)
    camera_shake = 0.22

func _on_pothole_exited(body: Node) -> void:
    if body != _player_physics_body:
        return
    # restaura fricção normal (0.4)
    pass

func _update_camera(dt: float) -> void:
    if camera == null:
        return
    var reduced_motion := bool(GameSave.data.get("reduced_motion", false))
    var shake_offset := Vector3.ZERO
    if not reduced_motion and camera_shake > 0.0:
        shake_offset = Vector3(fx_rng.randf_range(-camera_shake, camera_shake), fx_rng.randf_range(-camera_shake, camera_shake), 0.0)
        camera_shake = maxf(0.0, camera_shake - dt * 6.0)
    elif reduced_motion:
        camera_shake = 0.0
    # modo captura: órbita livre ao redor do corredor (Lote 6)
    if _capture_mode:
        var orbit_target := Vector3(player_x, 1.05 + player_visual.position.y * 0.12, -1.2)
        var r := 6.2
        var cp := cos(_capture_pitch)
        var off := Vector3(sin(_capture_yaw) * r * cp, sin(_capture_pitch) * 2.2 + 2.0, cos(_capture_yaw) * r * cp) + shake_offset
        var desired_cap := orbit_target + off
        camera.position = camera.position.lerp(desired_cap, minf(1.0, dt * 6.0))
        camera.look_at(orbit_target, Vector3.UP)
        camera.fov = lerpf(camera.fov, RENDER_FOV_RUN + 2.0, minf(1.0, dt * 3.0))
        return
    var camera_bob: float = sin(run_phase * 1.6) * 0.028 if not reduced_motion and screen == 2 and run_mode == "playing" else 0.0
    var player_y_offset: float = player_visual.position.y if player_visual != null else 0.0
    var target_y := 1.18 + player_y_offset * 0.20
    var target := Vector3(player_x * 0.18, target_y, -14.0)
    var desired_y := RENDER_CAMERA_Y + camera_bob + (player_y_offset * 0.28)
    var desired_z := RENDER_CAMERA_Z + sin(run_phase * 0.8) * 0.03
    var desired_x := player_x * 0.16
    if run_mode == "at_stop":
        # Enquadramento cinematográfico na chegada ao ponto
        desired_x = lerpf(desired_x, 1.25, 0.4)
        target = Vector3(player_x * 0.4 + 0.6, 1.30, -8.0)
    var desired := Vector3(desired_x, desired_y, desired_z) + shake_offset
    camera.position = camera.position.lerp(desired, minf(1.0, dt * 5.5))
    var desired_fov: float = RENDER_FOV_RUN if reduced_motion else RENDER_FOV_RUN + clampf(motion_speed * 0.34, 0.0, 5.0) + (4.0 if dash_timer > 0.0 else 0.0)
    camera.fov = lerpf(camera.fov, desired_fov, minf(1.0, dt * 4.0))
    camera.look_at(target, Vector3.UP)

func _apply_scenario_atmosphere() -> void:
    if environment == null or sky_material == null:
        return
    var sky_horizon: Color = scenario.get("sky_horizon", Color("#f5c477"))
    var sky_top: Color = scenario.get("sky_top", Color("#72bed5"))
    var chapter: int = int(scenario.get("chapter_index", 0))
    var weather: String = str(scenario.get("weather", "sol"))
    var sky_energy: float = 0.82 + clampf(float(9 - chapter) * 0.025, 0.0, 0.22)
    if weather in ["letreiros acesos", "sinos ao entardecer", "luzes da madrugada"]:
        sky_energy *= 0.78
    if weather in ["fim de tarde", "sinos ao entardecer", "letreiros acesos", "brisa da praia"]:
        sky_material.panorama = TEXTURE_SKY_SUNSET
    elif weather in ["nublado quente"]:
        sky_material.panorama = TEXTURE_SKY_CLOUDY
    else:
        sky_material.panorama = TEXTURE_SKY_PANORAMA
    sky_material.energy_multiplier = sky_energy
    sky_material.filter = true
    environment.environment.background_energy_multiplier = sky_energy
    environment.environment.ambient_light_color = scenario.get("ambient", Color("#b8d8e4"))
    environment.environment.ambient_light_energy = 0.58 if chapter >= 7 else 0.78
    environment.environment.fog_light_color = sky_horizon.lerp(sky_top, 0.26)
    environment.environment.fog_light_energy = 0.34 + float(chapter % 3) * 0.04
    environment.environment.fog_density = 0.0028 if weather in ["manhã clara", "sol confortável"] else 0.0036
    environment.environment.fog_sky_affect = 0.18 + float(chapter % 4) * 0.025
    if sun:
        sun.light_color = scenario.get("sun", Color("#ffe0a3"))
        sun.light_energy = 0.92 if chapter >= 7 else 1.18
        sun.rotation_degrees = Vector3(-32.0 - chapter * 1.0, -56.0 + (chapter % 4) * 2.5, 0.0)

func _update_sky_motion(dt: float) -> void:
    if sky_material == null or scenario.is_empty():
        return
    var shimmer: float = (sin(pulse * 0.065) + 1.0) * 0.5
    var base_energy: float = 0.82 + shimmer * 0.045
    if screen == 2:
        base_energy += 0.04
    sky_material.energy_multiplier = lerpf(sky_material.energy_multiplier, base_energy, dt * 0.35)
    if environment and environment.environment:
        environment.environment.background_energy_multiplier = sky_material.energy_multiplier
    if sun:
        sun.rotation_degrees.y += sin(pulse * 0.035) * dt * 0.8
        sun.light_energy = lerpf(sun.light_energy, (0.98 + shimmer * 0.20) if screen == 2 else 1.0, dt * 0.5)

func _clear_sky_fx() -> void:
    if sky_fx_root == null:
        return
    for child in sky_fx_root.get_children():
        child.free()
    sky_fx_nodes.clear()

func _rebuild_sky_fx() -> void:
    if sky_fx_root == null:
        return
    _clear_sky_fx()
    var kinds: Array = scenario.get("aerial", ["pombo"])
    var count: int = int(scenario.get("aerial_count", 3))
    for i in count:
        var kind: String = str(kinds[i % maxi(1, kinds.size())])
        var node := Node3D.new()
        node.name = "Aerial_%s_%02d" % [kind, i]
        node.position = Vector3(-12.0 + float((i * 19) % 25), 7.0 + float(i % 3) * 2.2, -35.0 - float(i) * 24.0)
        sky_fx_root.add_child(node)
        _build_aerial(node, kind)
        sky_fx_nodes.append({
            "node": node,
            "kind": kind,
            "speed": 1.0 + float(i % 3) * 0.55 + float(scenario.get("chapter_index", 0)) * 0.04,
            "phase": float(i) * 1.8,
            "drift": 0.15 + float(i % 2) * 0.12
        })
    _rebuild_ground_fauna()

func _build_aerial(parent: Node3D, kind: String) -> void:
    # Aves urbanas usam o mesmo Animal3D articulado do caramelo: as poses
    # de voo (run), planeio (idle), decolagem (jump) e agachado (crouch)
    # fazem parte do contrato compartilhado de animais.
    if kind in ["pombo", "passaro", "gaivota", "urubu"]:
        var animal := WORLD_ANIMAL_SCRIPT.new() as Node3D
        animal.name = "Animal3D_%s" % kind
        animal.set("species", kind)
        animal.call("enable_flight_cycle")
        parent.add_child(animal)
        return
    # Lote 8: avião e drone viram GLB originais (assets/sky_fx/). O node pai
    # gira em Y devagar (_update_sky_fx), então o GLB é centrado na origem.
    var glb := _optional_glb("sky_fx/" + kind + ".glb")
    if glb != null:
        glb.name = "SkyFx3D_" + kind
        parent.add_child(glb)
        return
    var dark := _material(Color("#283242"), 0.0, 0.92)
    var pale := _material(Color("#f1f0de"), 0.0, 0.82)
    var sky_blue := _material(Color("#78cbd8"), 0.0, 0.54)
    var drone_color := _material(Color("#59657b"), 0.15, 0.42)
    match kind:
        "aviao":
            _box(parent, Vector3(0.18, 0.18, 1.7), Vector3.ZERO, pale, "PlaneBody")
            var left_wing := _box(parent, Vector3(1.35, 0.05, 0.34), Vector3(0.0, 0.0, -0.12), pale, "PlaneWing")
            left_wing.rotation.y = 0.12
            _box(parent, Vector3(0.42, 0.34, 0.22), Vector3(0.0, 0.18, 0.68), sky_blue, "PlaneTail")
        "drone":
            _box(parent, Vector3(0.52, 0.10, 0.38), Vector3.ZERO, drone_color, "DroneBody")
            for side in [-1.0, 1.0]:
                _box(parent, Vector3(0.78, 0.04, 0.06), Vector3(side * 0.40, 0.08, 0.0), drone_color, "DroneArm")
                _cylinder(parent, 0.09, 0.09, 0.035, Vector3(side * 0.72, 0.13, 0.0), pale, "DroneRotor")
        "gaivota":
            var left_gull := _box(parent, Vector3(0.72, 0.035, 0.10), Vector3(-0.34, 0.0, 0.0), pale, "GullWing")
            var right_gull := _box(parent, Vector3(0.72, 0.035, 0.10), Vector3(0.34, 0.0, 0.0), pale, "GullWing")
            left_gull.rotation.z = -0.18
            right_gull.rotation.z = 0.18
            _sphere(parent, 0.08, Vector3(0.0, 0.0, -0.03), pale, "GullBody")
        "urubu":
            var left_vulture := _box(parent, Vector3(0.82, 0.05, 0.13), Vector3(-0.38, 0.0, 0.0), dark, "VultureWing")
            var right_vulture := _box(parent, Vector3(0.82, 0.05, 0.13), Vector3(0.38, 0.0, 0.0), dark, "VultureWing")
            left_vulture.rotation.z = -0.26
            right_vulture.rotation.z = 0.26
            _sphere(parent, 0.10, Vector3(0.0, 0.0, -0.03), dark, "VultureBody")
        _:
            _sphere(parent, 0.10, Vector3(0.0, 0.0, 0.0), dark, "BirdBody")
            var left_bird := _box(parent, Vector3(0.42, 0.035, 0.08), Vector3(-0.24, 0.0, 0.0), dark, "BirdWing")
            var right_bird := _box(parent, Vector3(0.42, 0.035, 0.08), Vector3(0.24, 0.0, 0.0), dark, "BirdWing")
            left_bird.rotation.z = -0.22
            right_bird.rotation.z = 0.22

func _update_sky_fx(dt: float) -> void:
    for item in sky_fx_nodes:
        var node: Node3D = item["node"]
        var speed: float = float(item["speed"])
        var phase_offset: float = float(item["phase"])
        node.position.z += speed * dt
        node.position.x += sin(pulse * 0.35 + phase_offset) * float(item["drift"]) * dt
        node.position.y += sin(pulse * 0.55 + phase_offset) * 0.012
        if str(item["kind"]) in ["pombo", "passaro", "gaivota", "urubu"]:
            # Aves articuladas balançam a rota em vez de girar sem parar:
            # o giro contínuo deixaria a cabeça de costas para a direção.
            node.rotation.y = sin(pulse * 0.4 + phase_offset) * 0.35
            node.rotation.z = sin(pulse * 2.0 + phase_offset) * 0.14
        else:
            node.rotation.y += dt * 0.035
        if node.position.z > 28.0:
            node.position.z = -112.0 - fx_rng.randf_range(0.0, 30.0)
            node.position.x = fx_rng.randf_range(-13.0, 13.0)

func _rebuild_ground_fauna() -> void:
    if ground_fauna_root == null:
        return
    for child in ground_fauna_root.get_children():
        child.free()
    ground_fauna_nodes.clear()
    # Aves de chão na borda externa da calçada direita + a fauna de interior
    # definida por capítulo ("fauna"): todos decorativos e animados com o
    # contrato completo de poses (idle, run, jump, crouch e crouch em
    # movimento), sem virar obstáculo de gameplay.
    var kinds: Array = scenario.get("aerial", ["pombo"])
    var bird_kinds: Array[String] = []
    for kind in kinds:
        if str(kind) == "pombo":   # a fauna de chao de Sao Paulo e de pombo
            bird_kinds.append(str(kind))
    if bird_kinds.is_empty():
        bird_kinds.append("pombo")
    var ground_kinds: Array = scenario.get("fauna", [])
    var chapter: int = int(scenario.get("chapter_index", 0))
    var entries: Array[Dictionary] = []
    for kind in ground_kinds:
        var species: String = str(kind)
        # Quadrúpedes e macaco são construídos olhando para +X; virar para +Z
        # deixa a fauna de frente para o corredor ao longo do corredor.
        var facing: float = 0.0 if species == "caranguejo" else -PI / 2.0
        entries.append({"kind": species, "x": 4.35, "facing": facing})
    var bird_count: int = 2 if chapter < 7 or not ground_kinds.is_empty() else 3
    for i in bird_count:
        entries.append({
            "kind": bird_kinds[i % bird_kinds.size()],
            "x": 4.45 - float(i % 2) * 0.5,
            "facing": -0.5 + float(i) * 0.55
        })
    for i in entries.size():
        var entry: Dictionary = entries[i]
        var kind: String = str(entry["kind"])
        var node := Node3D.new()
        node.name = "GroundFauna_%s_%02d" % [kind, i]
        node.position = Vector3(float(entry["x"]), 0.08, -26.0 - float(i) * 24.0)
        node.rotation.y = float(entry["facing"])
        ground_fauna_root.add_child(node)
        var animal := WORLD_ANIMAL_SCRIPT.new() as Node3D
        animal.name = "Animal3D_%s" % kind
        animal.set("species", kind)
        animal.call("enable_ground_behavior")
        node.add_child(animal)
        ground_fauna_nodes.append({"node": node, "kind": kind, "phase": float(i) * 1.7})

func _update_ground_fauna(dt: float) -> void:
    for item in ground_fauna_nodes:
        var node: Node3D = item["node"]
        var phase_offset: float = float(item["phase"])
        # Durante a corrida as aves varrem com o mundo; paradas, elas só
        # passeiam no lugar, mantendo o cenário vivo também atrás do menu.
        var scroll: float = player_speed * dt if screen == 2 and run_mode == "playing" else 0.0
        node.position.z += scroll + sin(pulse * 0.5 + phase_offset) * dt * 0.05
        node.position.x += cos(pulse * 0.33 + phase_offset) * dt * 0.04
        node.position.x = clampf(node.position.x, 4.0, 4.62)
        if node.position.z > 12.0:
            node.position.z = -70.0 - fx_rng.randf_range(0.0, 40.0)
            node.position.x = 3.9 + fx_rng.randf_range(0.0, 0.55)

func _clear_ambient_fx() -> void:
    if ambient_fx_root == null:
        return
    for child in ambient_fx_root.get_children():
        child.free()
    ambient_fx_nodes.clear()

func _rebuild_ambient_fx() -> void:
    if ambient_fx_root == null:
        return
    _clear_ambient_fx()
    var weather: String = str(scenario.get("weather", "sol"))
    var color: Color = _scenario_color("accent", GOLD)
    var count: int = 10 if weather in ["poeira dourada", "nublado quente"] else 6
    if weather == "luzes da madrugada":
        count = 12
    var material := _material(Color(color, 0.28), 0.0, 0.9)
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.emission_enabled = true
    material.emission = color
    material.emission_energy_multiplier = 0.45
    for i in count:
        var node := MeshInstance3D.new()
        node.name = "AmbientParticle_%02d" % i
        var mesh := SphereMesh.new()
        mesh.radius = 0.025 if weather != "luzes da madrugada" else 0.045
        mesh.height = mesh.radius * 2.0
        mesh.radial_segments = 6
        mesh.rings = 3
        node.mesh = mesh
        node.material_override = material
        node.position = Vector3(fx_rng.randf_range(-4.8, 4.8), fx_rng.randf_range(0.35, 3.8), fx_rng.randf_range(-22.0, 18.0))
        ambient_fx_root.add_child(node)
        ambient_fx_nodes.append({
            "node": node,
            "speed": 0.22 + fx_rng.randf_range(0.0, 0.42),
            "phase": fx_rng.randf_range(0.0, TAU)
        })

func _update_ambient_fx(dt: float) -> void:
    for item in ambient_fx_nodes:
        var node: Node3D = item["node"]
        var phase_offset: float = float(item["phase"])
        node.position.z += float(item["speed"]) * dt
        node.position.x += sin(pulse * 0.45 + phase_offset) * dt * 0.05
        node.position.y += cos(pulse * 0.65 + phase_offset) * dt * 0.018
        if node.position.z > 22.0:
            node.position.z = -24.0
            node.position.x = fx_rng.randf_range(-4.8, 4.8)

func _show_feedback(title: String, detail: String, color: Color, sound: String) -> void:
    feedback_title = title
    feedback_detail = detail
    feedback_color = color
    feedback_timer = 1.05
    if not bool(GameSave.data.get("reduced_motion", false)):
        flash_alpha = maxf(flash_alpha, 0.055)
    if sound != "":
        AudioManager.play_sfx(sound)
    if hud:
        hud.call("show_feedback", title, detail, color)

func _update_feedback(dt: float) -> void:
    feedback_timer = maxf(0.0, feedback_timer - dt)
    flash_alpha = maxf(0.0, flash_alpha - dt * 2.8)
    if hud:
        hud.call("set_feedback_time", feedback_timer, flash_alpha)

func _spawn_3d_burst(pos: Vector3, color: Color, amount: int) -> void:
    if bool(GameSave.data.get("reduced_motion", false)):
        return
    var material := _material(color, 0.0, 0.34)
    material.emission_enabled = true
    material.emission = color
    material.emission_energy_multiplier = 2.3
    var mesh := SphereMesh.new()
    mesh.radius = 0.07
    mesh.height = 0.14
    mesh.material = material
    for i in amount:
        var node := MeshInstance3D.new()
        node.mesh = mesh
        node.position = pos
        fx_root.add_child(node)
        fx_nodes.append({
            "node": node,
            "velocity": Vector3(fx_rng.randf_range(-2.5, 2.5), fx_rng.randf_range(1.0, 4.2), fx_rng.randf_range(-2.0, 1.0)),
            "life": fx_rng.randf_range(0.35, 0.75)
        })

func _update_fx(dt: float) -> void:
    for fx in fx_nodes:
        var node: Node3D = fx["node"]
        fx["life"] = float(fx["life"]) - dt
        fx["velocity"] = Vector3(fx["velocity"]) + Vector3(0.0, -6.0, 0.0) * dt
        node.position += Vector3(fx["velocity"]) * dt
        var life: float = float(fx["life"])
        node.scale = Vector3.ONE * clampf(life * 2.0, 0.05, 1.0)
    var alive: Array[Dictionary] = []
    for fx in fx_nodes:
        if float(fx["life"]) > 0.0:
            alive.append(fx)
        else:
            var node: Node3D = fx["node"]
            node.queue_free()
    fx_nodes = alive

# Lote 3: a rua agora vem do building_kit. O traçado antigo continua disponível
# em _build_track_antigo() — para reverter, troque a chamada de volta.
func _build_track() -> void:
    return


func _build_track_antigo() -> void:
    var total_length: float = run_total + WORLD_LENGTH_MARGIN
    var center_z: float = -(run_total - 10.0) * 0.5
    var road_color: Color = _scenario_color("road", Color("#303a4b"))
    var sidewalk_color: Color = _scenario_color("sidewalk", Color("#9b9b8b"))
    var curb_color: Color = _scenario_color("curb", Color("#e9c45b"))
    var divider_color: Color = _scenario_color("divider", Color("#d47a5f"))
    var tile_color: Color = _scenario_color("tile", Color("#777c76"))
    var accent: Color = _scenario_color("accent", YELLOW)
    var street_surface: String = "dirt" if str(scenario.get("street_surface", "asphalt")) == "dirt" else ("cobble" if str(scenario.get("street_surface", "asphalt")) == "cobble" else "asphalt")
    _box(decor_root, Vector3(3.35, 0.18, total_length), Vector3(-3.25, -0.16, center_z), _material(road_color, 0.0, 0.96, street_surface), "Street")
    _box(decor_root, Vector3(3.05, 0.18, total_length), Vector3(0.0, -0.16, center_z), _material(sidewalk_color, 0.0, 0.94, "sidewalk"), "SidewalkCenter")
    _box(decor_root, Vector3(3.05, 0.18, total_length), Vector3(3.25, -0.16, center_z), _material(sidewalk_color.lightened(0.08), 0.0, 0.94, "sidewalk"), "SidewalkRight")
    _box(decor_root, Vector3(0.18, 0.28, total_length), Vector3(-1.63, -0.02, center_z), _material(curb_color, 0.0, 0.78, "concrete"), "Curb")
    _box(decor_root, Vector3(0.12, 0.22, total_length), Vector3(1.62, -0.03, center_z), _material(divider_color, 0.0, 0.82, "paint"), "SidewalkDivider")
    for i in int(total_length / 9.0):
        var tile_z: float = -float(i) * 9.0 + 4.0
        _box(decor_root, Vector3(2.9, 0.025, 0.035), Vector3(0.0, -0.03, tile_z), _material(tile_color, 0.0, 1.0, "sidewalk"), "TileLine")
        _box(decor_root, Vector3(2.9, 0.025, 0.035), Vector3(3.25, -0.03, tile_z), _material(tile_color, 0.0, 1.0, "sidewalk"), "TileLine")
    for i in int(total_length / 18.0):
        var stripe_z: float = -float(i) * 18.0 - 3.0
        _box(decor_root, Vector3(0.10, 0.025, 5.0), Vector3(-1.95, -0.02, stripe_z), _material(curb_color.lightened(0.20), 0.0, 0.85), "RoadEdge")
        if str(scenario.get("street_surface", "asphalt")) == "dirt":
            _box(decor_root, Vector3(2.65, 0.02, 0.06), Vector3(-3.25, 0.01, stripe_z), _material(Color("#b77b50"), 0.0, 1.0, "dirt"), "DirtTrack")
    for i in int(total_length / 14.0):
        var surface_z: float = -float(i) * 14.0 - 6.0
        if i % 3 == 0:
            _build_asphalt_patch(Vector3(-3.25, -0.055, surface_z), 0.72 + float(i % 2) * 0.24)
        if i % 7 == 2:
            _build_manhole(Vector3(-3.25, -0.045, surface_z - 3.2))
    for i in int(total_length / 28.0):
        var decor_z: float = -float(i) * 28.0 - 10.0
        _build_scenario_slice(decor_z, i)
        if i % 2 == 0:
            _build_lamp(Vector3(-1.0, 0.0, decor_z - 4.0), accent)
    _create_bus_stop(run_total)

func _build_asphalt_patch(pos: Vector3, size: float) -> void:
    var patch := _material(Color("#242c35"), 0.0, 0.98, "asphalt")
    var mesh := _cylinder(decor_root, size, size * 0.82, 0.018, pos, patch, "AsphaltRepair")
    mesh.scale = Vector3(1.0, 1.0, 0.58)
    var seam := _material(Color("#4b4f4f"), 0.0, 1.0, "asphalt")
    _cylinder(decor_root, size * 0.78, size * 0.68, 0.012, pos + Vector3(0.0, 0.012, 0.0), seam, "RepairSeam")

func _build_manhole(pos: Vector3) -> void:
    var iron := _material(Color("#4f5960"), 0.55, 0.58, "metal")
    _cylinder(decor_root, 0.42, 0.42, 0.025, pos, iron, "ManholeFrame")
    var inner := _material(Color("#252e36"), 0.45, 0.76, "metal")
    _cylinder(decor_root, 0.34, 0.34, 0.032, pos + Vector3(0.0, 0.018, 0.0), inner, "ManholeCover")
    for angle in [0.0, PI / 2.0, PI / 4.0, -PI / 4.0]:
        var groove := _box(decor_root, Vector3(0.48, 0.012, 0.025), pos + Vector3(0.0, 0.038, 0.0), _material(Color("#748087"), 0.4, 0.52, "metal"), "ManholeGroove")
        groove.rotation.y = angle

func _scenario_color(key: String, fallback: Color) -> Color:
    var value = scenario.get(key, fallback)
    return value if value is Color else fallback

func _build_scenario_slice(z: float, index: int) -> void:
    var style: String = str(scenario.get("building_style", "house"))
    match style:
        "favela":
            _build_favela_slice(z, index)
        "house":
            _build_residential_slice(z, index)
        "center":
            _build_center_slice(z, index)
        "humble":
            _build_humble_slice(z, index)
        "condo":
            _build_condo_slice(z, index)
        "military":
            _build_military_slice(z, index)
        "religious":
            _build_religious_slice(z, index)
        "commercial":
            _build_commercial_slice(z, index)
        "tourist":
            _build_tourist_slice(z, index)
        "terminal":
            _build_terminal_slice(z, index)
        _:
            _build_residential_slice(z, index)

func _build_favela_slice(z: float, index: int) -> void:
    _build_house_facade(Vector3(-6.1, 0.0, z), index, true)
    _build_house_facade(Vector3(6.2, 0.0, z - 9.0), index + 2, true)
    _build_house_facade(Vector3(-5.7, 1.25, z - 5.0), index + 3, false)
    if index % 2 == 0:
        _build_water_tank(Vector3(-5.1, 0.0, z - 3.0), 2.9)
        _build_clothesline(Vector3(5.0, 0.0, z - 3.0))
    _build_tree(Vector3(5.1, 0.0, z - 7.0), 0.58)

func _build_residential_slice(z: float, index: int) -> void:
    _build_house_facade(Vector3(-6.0, 0.0, z), index, false)
    _build_house_facade(Vector3(6.4, 0.0, z - 11.0), index + 1, false)
    _build_gate(Vector3(-4.65, 0.0, z - 2.0), _scenario_color("accent", CYAN))
    _build_tree(Vector3(5.0, 0.0, z - 4.0), 0.88)
    if index % 3 == 0:
        _build_decor_car(Vector3(5.0, 0.0, z - 13.0), _scenario_color("accent", CYAN))

func _build_center_slice(z: float, index: int) -> void:
    _build_profile_building(Vector3(-6.1, 0.0, z), index, 7.5, 2.8)
    _build_profile_building(Vector3(6.2, 0.0, z - 12.0), index + 3, 8.5, 3.1)
    _build_shopfront(Vector3(-4.55, 0.0, z - 2.0), index, _scenario_color("accent", YELLOW))
    _build_shopfront(Vector3(4.65, 0.0, z - 14.0), index + 1, _scenario_color("accent", YELLOW))

func _build_humble_slice(z: float, index: int) -> void:
    _build_house_facade(Vector3(-6.0, 0.0, z), index, false)
    if index % 2 == 0:
        _build_construction(Vector3(6.0, 0.0, z - 8.0), index)
    else:
        _build_shopfront(Vector3(6.1, 0.0, z - 8.0), index, _scenario_color("accent", RED))
    _build_utility_wire(Vector3(-4.8, 0.0, z - 4.0), Vector3(5.2, 0.0, z - 14.0))

func _build_condo_slice(z: float, index: int) -> void:
    _build_profile_building(Vector3(-6.1, 0.0, z), index, 8.5, 3.2)
    _build_gate(Vector3(-4.45, 0.0, z - 2.2), _scenario_color("accent", CYAN))
    _build_house_facade(Vector3(6.0, 0.0, z - 10.0), index + 2, false)
    _build_tree(Vector3(4.85, 0.0, z - 3.0), 1.0)
    _build_tree(Vector3(-4.8, 0.0, z - 13.0), 0.74)

func _build_military_slice(z: float, index: int) -> void:
    _build_profile_building(Vector3(-6.2, 0.0, z), index, 5.0, 3.7)
    _build_guard_post(Vector3(5.4, 0.0, z - 8.0), index)
    _build_flag(Vector3(-4.45, 0.0, z - 5.0), _scenario_color("accent", YELLOW))
    _build_tree(Vector3(6.0, 0.0, z - 2.0), 1.12)

func _build_religious_slice(z: float, index: int) -> void:
    if index % 3 == 0:
        _build_church(Vector3(-6.0, 0.0, z), index)
    else:
        _build_house_facade(Vector3(-6.0, 0.0, z), index, false)
    _build_profile_building(Vector3(6.1, 0.0, z - 10.0), index + 1, 4.8, 2.7)
    _build_flags(Vector3(4.8, 0.0, z - 3.0), _scenario_color("accent", VIOLET))

func _build_commercial_slice(z: float, index: int) -> void:
    _build_shopfront(Vector3(-6.0, 0.0, z), index, _scenario_color("accent", RED))
    _build_shopfront(Vector3(6.1, 0.0, z - 11.0), index + 1, _scenario_color("accent", CYAN))
    if index % 2 == 0:
        _build_market_stall(Vector3(-4.65, 0.0, z - 9.0), index)
    _build_profile_building(Vector3(5.8, 0.0, z - 4.0), index + 4, 6.0, 2.6)

func _build_tourist_slice(z: float, index: int) -> void:
    _build_colonial_facade(Vector3(-6.0, 0.0, z), index)
    _build_tourist_kiosk(Vector3(5.5, 0.0, z - 8.0), index)
    _build_palm(Vector3(-4.7, 0.0, z - 13.0), 1.0)
    _build_palm(Vector3(6.1, 0.0, z - 3.0), 0.86)

func _build_terminal_slice(z: float, index: int) -> void:
    _build_profile_building(Vector3(-6.2, 0.0, z), index, 10.0, 3.8)
    _build_terminal_facade(Vector3(5.9, 0.0, z - 10.0), index)
    _build_billboard(Vector3(-4.75, 0.0, z - 7.0), _scenario_color("accent", CYAN))
    if index % 2 == 0:
        _build_lamp(Vector3(5.0, 0.0, z - 3.0), _scenario_color("accent", CYAN))

func _build_house_facade(pos: Vector3, index: int, stacked: bool) -> void:
    var base: Color = _scenario_color("building", Color("#b86d54"))
    var alt: Color = _scenario_color("building_alt", Color("#d29d63"))
    var roof: Color = _scenario_color("roof", Color("#5d4444"))
    var width: float = 2.4 + float(index % 2) * 0.35
    var height: float = 2.4 + float(index % 3) * 0.25
    var depth: float = 3.1
    var casa_glb := _optional_glb("scene/casa_favela.glb" if stacked else "scene/casa.glb")
    if casa_glb != null:
        casa_glb.position = pos
        decor_root.add_child(casa_glb)
        if stacked:
            _tint_glb(casa_glb, {"TintRoof": roof, "TintAwning": _scenario_color("accent", YELLOW)})
        else:
            _tint_glb(casa_glb, {"TintWall": base if index % 2 == 0 else alt, "TintRoof": roof})
        return
    var surface: String = "facade_brick" if stacked else "facade_plaster"
    var tint: Color = Color("#ffffff") if stacked else (base if index % 2 == 0 else alt)
    var wall := _material(tint, 0.0, 1.0, surface)
    # casa baixa: mostra apenas o terreo da textura (1 andar de 3 m, 2 janelas inteiras)
    wall.uv1_scale = Vector3(width / 6.0, height / 3.0, depth / 6.0)
    wall.uv1_offset = Vector3(0.075, 0.75, 0.0)
    _box(decor_root, Vector3(width, height, depth), pos + Vector3(0.0, height * 0.5, 0.0), wall, "HouseFacade")
    _box(decor_root, Vector3(width + 0.14, 0.16, depth + 0.18), pos + Vector3(0.0, height + 0.10, 0.0), _material(roof, 0.0, 0.88, "wood"), "HouseRoof")
    _box(decor_root, Vector3(0.62, 0.82, 0.06), pos + Vector3(0.0, 0.54, -depth * 0.5 - 0.04), _material(Color("#4d3d43"), 0.0, 0.52, "wood"), "HouseDoor")
    if stacked:
        _box(decor_root, Vector3(0.92, 0.12, 0.10), pos + Vector3(0.0, height * 0.6, -depth * 0.5 - 0.09), _material(_scenario_color("accent", YELLOW), 0.0, 0.54), "HouseAwning")

func _build_profile_building(pos: Vector3, index: int, height: float, width: float) -> void:
    var brick: bool = index % 2 == 1
    var predio_glb := _optional_glb("scene/predio2.glb" if height < 6.5 else "scene/predio3.glb")
    if predio_glb != null:
        # corpo de 5.2/7.8 m no GLB; o jogo escala X/Y (profundidade ja e 3.8)
        predio_glb.position = pos
        predio_glb.scale = Vector3(width / 3.0, height / (5.2 if height < 6.5 else 7.8), 1.0)
        decor_root.add_child(predio_glb)
        var parede: Color = Color("#b98a68") if brick else _scenario_color("building", Color("#8fa3b8")).lerp(Color.WHITE, 0.35)
        _tint_glb(predio_glb, {"TintWall": parede, "TintTrim": _scenario_color("accent", YELLOW)})
        return
    var tint: Color = Color("#ffffff") if brick else _scenario_color("building", Color("#8fa3b8")).lerp(Color.WHITE, 0.35)
    var material := _material(tint, 0.0, 1.0, "facade_brick" if brick else "facade_plaster")
    # tile de fachada = 4 janelas (6 m) x 4 andares (12 m)
    material.uv1_scale = Vector3(width / 6.0, height / 12.0, 3.8 / 6.0)
    _box(decor_root, Vector3(width, height, 3.8), pos + Vector3(0.0, height * 0.5, 0.0), material, "ProfileBuilding")
    _box(decor_root, Vector3(width * 0.72, 0.08, 0.06), pos + Vector3(0.0, height - 0.24, -1.98), _material(_scenario_color("accent", YELLOW), 0.0, 0.48, "metal"), "ProfileCrown")
    var concrete := _material(Color("#a8a49a"), 0.0, 0.9, "concrete")
    _box(decor_root, Vector3(width + 0.14, 0.18, 4.0), pos + Vector3(0.0, height - 0.09, 0.0), concrete, "ProfileParapet")
    if index % 2 == 0:
        var ac := _material(Color("#d9d7d2"), 0.1, 0.6, "metal")
        var ac_y: float = clampf(1.2 + float((index * 5) % 3) * 2.8, 2.0, height - 1.4)
        _box(decor_root, Vector3(0.6, 0.4, 0.22), pos + Vector3(-width * 0.18, ac_y, -1.99), ac, "ProfileAC")

func _build_shopfront(pos: Vector3, index: int, accent: Color) -> void:
    var loja_glb := _optional_glb("scene/loja.glb")
    if loja_glb != null:
        loja_glb.position = pos
        decor_root.add_child(loja_glb)
        _tint_glb(loja_glb, {
            "TintWall": _scenario_color("building", Color("#527c98")).lerp(Color.WHITE, 0.25),
            "TintAwning": accent,
            "TintSign": accent.lightened(0.18),
            "TintTrim": accent.lightened(0.18)})
        return
    var shop_wall := _material(_scenario_color("building", Color("#527c98")).lerp(Color.WHITE, 0.25), 0.0, 1.0, "facade_plaster")
    shop_wall.uv1_scale = Vector3(2.5 / 6.0, 2.45 / 3.0, 3.0 / 6.0)
    shop_wall.uv1_offset = Vector3(0.075, 0.75, 0.0)
    _box(decor_root, Vector3(2.5, 2.45, 3.0), pos + Vector3(0.0, 1.22, 0.0), shop_wall, "ShopBody")
    _box(decor_root, Vector3(2.15, 0.92, 0.05), pos + Vector3(0.0, 0.88, -1.54), _material(Color("#75c8cb"), 0.0, 0.28, "glass"), "ShopWindow")
    _box(decor_root, Vector3(2.7, 0.16, 0.72), pos + Vector3(0.0, 2.34, -0.04), _material(accent, 0.0, 0.56, "fabric"), "ShopAwning")
    _box(decor_root, Vector3(1.65, 0.28, 0.08), pos + Vector3(0.0, 2.72, -1.47), _material(accent.lightened(0.18), 0.0, 0.38, "paint"), "ShopSign")
    if index % 2 == 0:
        _box(decor_root, Vector3(0.40, 0.70, 0.44), pos + Vector3(0.0, 0.42, -1.62), _material(Color("#744d3d"), 0.0, 0.74), "ShopDoor")

func _build_construction(pos: Vector3, index: int) -> void:
    var obra_glb := _optional_glb("scene/obra.glb")
    if obra_glb != null:
        obra_glb.position = pos
        decor_root.add_child(obra_glb)
        return
    var orange := _material(Color("#e7793f"), 0.0, 0.62, "metal")
    _box(decor_root, Vector3(2.8, 1.7, 2.9), pos + Vector3(0.0, 0.85, 0.0), _material(Color("#d8cfc2"), 0.0, 0.95, "brick_wall"), "ConstructionBrick")
    for side in [-1.0, 1.0]:
        _cylinder(decor_root, 0.035, 0.035, 3.4, pos + Vector3(side * 1.2, 1.7, -1.58), orange, "ScaffoldPole")
        _box(decor_root, Vector3(2.55, 0.06, 0.06), pos + Vector3(0.0, 2.9, -1.58), orange, "ScaffoldBar")
    _box(decor_root, Vector3(2.9, 0.72, 0.05), pos + Vector3(0.0, 2.5, -1.62), _material(Color("#ffd45f"), 0.0, 0.76, "fabric"), "ConstructionNet")
    if index % 2 == 0:
        _cone(decor_root, 0.28, 0.65, pos + Vector3(1.6, 0.34, -1.0), orange, "ConstructionCone")

func _build_guard_post(pos: Vector3, _index: int) -> void:
    var guarita_glb := _optional_glb("scene/guarita.glb")
    if guarita_glb != null:
        guarita_glb.position = pos
        decor_root.add_child(guarita_glb)
        _tint_glb(guarita_glb, {"TintWall": _scenario_color("building_alt", Color("#b9a770")), "TintTrim": _scenario_color("accent", YELLOW), "TintFabric": _scenario_color("accent", YELLOW)})
        return
    _box(decor_root, Vector3(1.9, 1.9, 1.8), pos + Vector3(0.0, 0.95, 0.0), _material(_scenario_color("building_alt", Color("#b9a770")), 0.0, 0.74, "stucco"), "GuardPost")
    _box(decor_root, Vector3(1.3, 0.46, 0.05), pos + Vector3(0.0, 1.3, -0.94), _material(Color("#263d4b"), 0.0, 0.34, "glass"), "GuardWindow")
    _box(decor_root, Vector3(2.1, 0.10, 2.0), pos + Vector3(0.0, 2.0, 0.0), _material(_scenario_color("accent", YELLOW), 0.0, 0.72, "metal"), "GuardRoof")
    _build_flag(pos + Vector3(0.75, 0.0, 0.0), _scenario_color("accent", YELLOW))

func _build_church(pos: Vector3, _index: int) -> void:
    var igreja_glb := _optional_glb("scene/igreja.glb")
    if igreja_glb != null:
        igreja_glb.position = pos
        decor_root.add_child(igreja_glb)
        _tint_glb(igreja_glb, {"TintWall": _scenario_color("building", Color("#d8a46d")), "TintRoof": _scenario_color("roof", Color("#6c4f55")), "TintTrim": _scenario_color("accent", VIOLET)})
        return
    var wall := _material(_scenario_color("building", Color("#d8a46d")), 0.0, 0.84, "stucco")
    _box(decor_root, Vector3(2.9, 4.0, 3.6), pos + Vector3(0.0, 2.0, 0.0), wall, "ChurchBody")
    _box(decor_root, Vector3(1.1, 5.6, 1.0), pos + Vector3(-1.0, 2.8, 0.0), wall, "ChurchTower")
    _cone(decor_root, 0.72, 1.05, pos + Vector3(-1.0, 6.1, 0.0), _material(_scenario_color("roof", Color("#6c4f55")), 0.0, 0.84), "ChurchRoof")
    _box(decor_root, Vector3(0.72, 1.24, 0.05), pos + Vector3(0.0, 0.72, -1.84), _material(Color("#684a58"), 0.0, 0.66), "ChurchDoor")
    _box(decor_root, Vector3(0.25, 0.92, 0.05), pos + Vector3(-1.0, 6.9, -0.05), _material(_scenario_color("accent", VIOLET), 0.0, 0.42), "ChurchCross")

func _build_tourist_kiosk(pos: Vector3, _index: int) -> void:
    var quiosque_glb := _optional_glb("scene/quiosque.glb")
    if quiosque_glb != null:
        quiosque_glb.position = pos
        decor_root.add_child(quiosque_glb)
        _tint_glb(quiosque_glb, {"TintWall": _scenario_color("building_alt", Color("#72b1ad")), "TintTrim": _scenario_color("accent", CYAN)})
        return
    _cylinder(decor_root, 0.72, 0.82, 1.55, pos + Vector3(0.0, 0.78, 0.0), _material(_scenario_color("building_alt", Color("#72b1ad")), 0.0, 0.74, "stucco"), "Kiosk")
    _cone(decor_root, 1.05, 0.52, pos + Vector3(0.0, 1.82, 0.0), _material(_scenario_color("accent", CYAN), 0.0, 0.62, "fabric"), "KioskRoof")
    _box(decor_root, Vector3(0.72, 0.22, 0.05), pos + Vector3(0.0, 0.98, -0.8), _material(Color("#f5e6bc"), 0.0, 0.45, "wood"), "KioskCounter")

func _build_terminal_facade(pos: Vector3, _index: int) -> void:
    var terminal_glb := _optional_glb("scene/terminal.glb")
    if terminal_glb != null:
        terminal_glb.position = pos
        decor_root.add_child(terminal_glb)
        _tint_glb(terminal_glb, {"TintWall": _scenario_color("building", Color("#344b70")), "TintTrim": _scenario_color("accent", CYAN), "TintSign": _scenario_color("accent", CYAN).lightened(0.18)})
        return
    _box(decor_root, Vector3(3.2, 3.2, 2.8), pos + Vector3(0.0, 1.6, 0.0), _material(_scenario_color("building", Color("#344b70")), 0.0, 0.68, "metal"), "TerminalFacade")
    _box(decor_root, Vector3(2.9, 0.95, 0.05), pos + Vector3(0.0, 1.35, -1.46), _material(Color("#7ed3d0"), 0.0, 0.25, "glass"), "TerminalGlass")
    _box(decor_root, Vector3(3.5, 0.12, 0.72), pos + Vector3(0.0, 3.25, 0.0), _material(_scenario_color("accent", CYAN), 0.0, 0.42, "metal"), "TerminalRoof")

func _build_market_stall(pos: Vector3, _index: int) -> void:
    var barraca_glb := _optional_glb("scene/barraca.glb")
    if barraca_glb != null:
        barraca_glb.position = pos
        decor_root.add_child(barraca_glb)
        _tint_glb(barraca_glb, _scenario_color("accent", RED))
        return
    _box(decor_root, Vector3(1.5, 1.1, 1.0), pos + Vector3(0.0, 0.56, 0.0), _material(Color("#d88c43"), 0.0, 0.76, "wood"), "MarketCart")
    _box(decor_root, Vector3(1.75, 0.10, 1.15), pos + Vector3(0.0, 1.34, 0.0), _material(_scenario_color("accent", RED), 0.0, 0.62, "fabric"), "MarketAwning")
    _sphere(decor_root, 0.23, pos + Vector3(0.0, 1.52, -0.08), _material(Color("#b8785a"), 0.0, 0.78), "MarketSeller")

func _build_colonial_facade(pos: Vector3, index: int) -> void:
    var colonial_glb := _optional_glb("scene/colonial.glb")
    if colonial_glb != null:
        colonial_glb.position = pos
        decor_root.add_child(colonial_glb)
        var base_c: Color = _scenario_color("building", Color("#b86d54"))
        var alt_c: Color = _scenario_color("building_alt", Color("#d29d63"))
        _tint_glb(colonial_glb, {
            "TintWall": base_c if index % 2 == 0 else alt_c,
            "TintRoof": _scenario_color("roof", Color("#5d4444")),
            "TintTrim": _scenario_color("accent", CYAN)})
        return
    _build_house_facade(pos, index, false)
    _box(decor_root, Vector3(2.55, 0.09, 0.08), pos + Vector3(0.0, 2.1, -1.64), _material(_scenario_color("accent", CYAN), 0.0, 0.45, "paint"), "ColonialTrim")

func _build_palm(pos: Vector3, object_scale: float) -> void:
    var palmeira_glb := _optional_glb("scene/palmeira.glb")
    if palmeira_glb != null:
        palmeira_glb.position = pos
        palmeira_glb.scale = Vector3.ONE * object_scale
        if palmeira_glb is GeometryInstance3D:
            (palmeira_glb as GeometryInstance3D).visibility_range_end = 35.0
            (palmeira_glb as GeometryInstance3D).visibility_range_end_margin = 2.0
        decor_root.add_child(palmeira_glb)
        var imp2 := _create_tree_impostor(pos, object_scale * 0.95)
        if imp2 != null:
            decor_root.add_child(imp2)
        return
    _cylinder(decor_root, 0.10 * object_scale, 0.15 * object_scale, 2.7 * object_scale, pos + Vector3(0.0, 1.35 * object_scale, 0.0), _material(Color("#805338"), 0.0, 0.9), "PalmTrunk")
    var leaf := _material(Color("#3eaa75"), 0.0, 0.84, "leaves")
    for i in 5:
        var branch := _box(decor_root, Vector3(0.08, 0.06, 1.0 * object_scale), pos + Vector3(0.0, 2.75 * object_scale, 0.0), leaf, "PalmLeaf")
        branch.rotation.y = float(i) * TAU / 5.0
        branch.rotation.x = -0.28

func _create_tree_impostor(pos: Vector3, object_scale: float) -> MeshInstance3D:
    # Lote 14: impostor billboard de baixo custo para LOD >35m (2 tris, 1 draw call).
    # Usa textura de folhagem já em VRAM, transparente, double-sided.
    var quad := QuadMesh.new()
    quad.size = Vector2(1.6 * object_scale, 2.4 * object_scale)
    var mat := StandardMaterial3D.new()
    mat.albedo_texture = TEXTURE_LEAVES_REAL
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
    mat.billboard_keep_scale = true
    mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    quad.material = mat
    var imp := MeshInstance3D.new()
    imp.name = "TreeImpostor"
    imp.mesh = quad
    imp.position = pos + Vector3(0.0, 1.4 * object_scale, 0.0)
    imp.visibility_range_begin = 33.0
    imp.visibility_range_begin_margin = 2.0
    imp.visibility_range_end = 96.0
    imp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    return imp

func _build_water_tank(pos: Vector3, height: float) -> void:
    var caixa_glb := _optional_glb("scene/caixa_dagua.glb")
    if caixa_glb != null:
        # modelada para height 2.9 (unica chamada, na fatia da favela)
        caixa_glb.position = pos
        decor_root.add_child(caixa_glb)
        return
    _cylinder(decor_root, 0.55, 0.55, 0.85, pos + Vector3(0.0, height, 0.0), _material(Color("#4d78a1"), 0.0, 0.62, "metal"), "WaterTank")
    _cylinder(decor_root, 0.08, 0.08, height - 0.35, pos + Vector3(-0.35, (height - 0.35) * 0.5, 0.0), _material(Color("#76533e"), 0.0, 0.92, "metal"), "TankLeg")
    _cylinder(decor_root, 0.08, 0.08, height - 0.35, pos + Vector3(0.35, (height - 0.35) * 0.5, 0.0), _material(Color("#76533e"), 0.0, 0.92, "metal"), "TankLeg")

func _build_clothesline(pos: Vector3) -> void:
    var varal_glb := _optional_glb("scene/varal.glb")
    if varal_glb != null:
        varal_glb.position = pos
        decor_root.add_child(varal_glb)
        return
    _cylinder(decor_root, 0.035, 0.035, 2.1, pos + Vector3(-0.9, 1.05, 0.0), _material(Color("#594a43"), 0.0, 0.9, "wood"), "ClothesPole")
    _cylinder(decor_root, 0.035, 0.035, 2.1, pos + Vector3(0.9, 1.05, 0.0), _material(Color("#594a43"), 0.0, 0.9, "wood"), "ClothesPole")
    _box(decor_root, Vector3(1.9, 0.025, 0.025), pos + Vector3(0.0, 1.85, 0.0), _material(Color("#a5a19a"), 0.0, 0.95, "metal"), "ClothesLine")
    for i in 4:
        _box(decor_root, Vector3(0.30, 0.38, 0.04), pos + Vector3(-0.63 + i * 0.42, 1.62, -0.02), _material([Color("#e56d63"), Color("#5d9bd1"), Color("#e5c44f"), Color("#82c99d")][i], 0.0, 0.8, "fabric"), "Clothes")

func _build_gate(pos: Vector3, color: Color) -> void:
    var portao_glb := _optional_glb("scene/portao.glb")
    if portao_glb != null:
        portao_glb.position = pos
        decor_root.add_child(portao_glb)
        _tint_glb(portao_glb, color)
        return
    var metal := _material(color, 0.35, 0.45, "metal")
    _box(decor_root, Vector3(1.8, 1.7, 0.08), pos + Vector3(0.0, 0.85, 0.0), metal, "Gate")
    for i in 4:
        _box(decor_root, Vector3(0.035, 1.5, 0.10), pos + Vector3(-0.68 + i * 0.45, 0.78, -0.05), metal, "GateBar")

func _build_decor_car(pos: Vector3, _color: Color) -> void:
    var parent := Node3D.new()
    parent.name = "ParkedCar"
    parent.position = pos
    decor_root.add_child(parent)
    var parked_glb := _optional_model("carro.glb")
    if parked_glb != null:
        parent.add_child(parked_glb)
        _fit_model(parked_glb, GLB_FIT["carro"].x, GLB_FIT["carro"].y)
        return
    var tire := _material(Color("#202c3c"), 0.15, 0.38, "rubber")
    var chrome := _material(Color("#aebdc0"), 0.72, 0.24, "chrome")
    var glass := _material(Color("#71bcc7"), 0.0, 0.25, "glass")
    var lamp := _material(Color("#fff4c9"), 0.0, 0.18, "glass")
    lamp.emission_enabled = true
    lamp.emission = Color("#fff1b0")
    lamp.emission_energy_multiplier = 1.4
    var tail := _material(Color("#cc3942"), 0.0, 0.28, "glass")
    _build_brazilian_car(parent, int(abs(pos.z)) % 3, tire, chrome, glass, lamp, tail)

func _build_utility_wire(start: Vector3, finish: Vector3) -> void:
    var midpoint: Vector3 = (start + finish) * 0.5 + Vector3(0.0, 2.9, 0.0)
    var length: float = start.distance_to(finish)
    var wire := _box(decor_root, Vector3(0.025, 0.025, length), midpoint, _material(Color("#282d35"), 0.1, 0.7), "UtilityWire")
    wire.look_at(finish + Vector3(0.0, 2.9, 0.0), Vector3.UP)

func _build_flag(pos: Vector3, color: Color) -> void:
    var bandeira_glb := _optional_glb("scene/bandeira.glb")
    if bandeira_glb != null:
        bandeira_glb.position = pos
        decor_root.add_child(bandeira_glb)
        _tint_glb(bandeira_glb, color)
        return
    _cylinder(decor_root, 0.025, 0.025, 2.7, pos + Vector3(0.0, 1.35, 0.0), _material(Color("#d2d0c2"), 0.0, 0.68, "metal"), "FlagPole")
    _box(decor_root, Vector3(0.72, 0.38, 0.035), pos + Vector3(0.34, 2.38, 0.0), _material(color, 0.0, 0.64, "fabric"), "Flag")

func _build_flags(pos: Vector3, color: Color) -> void:
    _build_flag(pos, color)
    _build_flag(pos + Vector3(0.9, 0.0, -0.6), color.lightened(0.14))

func _build_billboard(pos: Vector3, color: Color) -> void:
    var outdoor_glb := _optional_glb("scene/outdoor.glb")
    if outdoor_glb != null:
        outdoor_glb.position = pos
        decor_root.add_child(outdoor_glb)
        _tint_glb(outdoor_glb, color)
        return
    _cylinder(decor_root, 0.04, 0.04, 3.8, pos + Vector3(0.0, 1.9, 0.0), _material(Color("#39404d"), 0.15, 0.5, "metal"), "BillboardPole")
    _box(decor_root, Vector3(2.25, 1.15, 0.08), pos + Vector3(0.0, 3.65, 0.0), _material(color, 0.0, 0.38, "paint"), "Billboard")

func _build_building(pos: Vector3, index: int, _accent: Color) -> void:
    _build_profile_building(pos, index + 4, 4.6 + float((index * 17) % 5) * 1.25, 2.3 + float(index % 3) * 0.45)

func _build_lamp(pos: Vector3, accent: Color) -> void:
    var poste_glb := _optional_prop("poste.glb")
    if poste_glb != null:
        poste_glb.position = pos
        decor_root.add_child(poste_glb)
        return
    _cylinder(decor_root, 0.035, 0.035, 3.2, pos + Vector3(0.0, 1.6, 0.0), _material(Color("#3c4654"), 0.35, 0.4, "metal"), "LampPole")
    var lamp_material := _material(accent.lightened(0.20), 0.0, 0.22, "glass")
    lamp_material.emission_enabled = true
    lamp_material.emission = accent.lightened(0.20)
    lamp_material.emission_energy_multiplier = 1.5
    _sphere(decor_root, 0.12, pos + Vector3(0.0, 3.24, 0.0), lamp_material, "LampGlow")
    _box(decor_root, Vector3(0.65, 0.06, 0.06), pos + Vector3(0.27, 3.18, 0.0), _material(Color("#3c4654"), 0.35, 0.4, "metal"), "LampArm")

func _build_tree(pos: Vector3, object_scale: float) -> void:
    var arvore_glb := _optional_glb("scene/arvore.glb")
    if arvore_glb != null:
        arvore_glb.position = pos
        arvore_glb.scale = Vector3.ONE * object_scale
        # Lote 14: LOD — high poly até 35m, impostor billboard além disso
        # visibility_range_end: high poly some a 35m; impostor aparece a partir de 35m
        if arvore_glb is GeometryInstance3D:
            (arvore_glb as GeometryInstance3D).visibility_range_end = 35.0
            (arvore_glb as GeometryInstance3D).visibility_range_end_margin = 2.0
        decor_root.add_child(arvore_glb)
        # impostor de baixo custo (quad 1.6x2.4 com textura de folhagem, billboard)
        var imp := _create_tree_impostor(pos, object_scale)
        if imp != null:
            decor_root.add_child(imp)
        return
    _cylinder(decor_root, 0.12 * object_scale, 0.16 * object_scale, 1.7 * object_scale, pos + Vector3(0.0, 0.85 * object_scale, 0.0), _material(Color("#67452f"), 0.0, 0.95, "wood"), "TreeTrunk")
    var foliage := _material(Color("#3b9b69"), 0.0, 0.86, "leaves")
    _sphere(decor_root, 0.62 * object_scale, pos + Vector3(-0.28, 1.65 * object_scale, 0.0), foliage, "TreeLeaf")
    _sphere(decor_root, 0.75 * object_scale, pos + Vector3(0.28, 1.82 * object_scale, 0.0), foliage, "TreeLeaf")
    _sphere(decor_root, 0.5 * object_scale, pos + Vector3(0.0, 2.2 * object_scale, 0.0), foliage, "TreeLeaf")

func _create_bus_stop(total: float) -> void:
    bus_stop_node = Node3D.new()
    bus_stop_node.name = "BusStop"
    bus_stop_node.position = Vector3(3.25, 0.0, -total - 14.0)
    decor_root.add_child(bus_stop_node)
    var stop_accent: Color = _scenario_color("accent", Color("#e8c45b"))
    if GameSave.owns("placa"):
        stop_accent = Color("#63c8ed")
    var ponto_glb := _optional_prop("ponto.glb")
    if ponto_glb != null:
        # abrigo original (GLB): abertura para -Z, como a versao procedural
        bus_stop_node.add_child(ponto_glb)
    else:
        _box(bus_stop_node, Vector3(2.5, 0.12, 0.12), Vector3(0.0, 2.95, 0.0), _material(stop_accent, 0.0, 0.7), "StopRoof")
        _box(bus_stop_node, Vector3(0.08, 3.0, 0.08), Vector3(-1.05, 1.45, 0.0), _material(Color("#c8d4d1"), 0.0, 0.55), "StopPole")
        _box(bus_stop_node, Vector3(1.65, 1.05, 0.08), Vector3(0.0, 1.25, 0.08), _material(Color("#5b7790"), 0.0, 0.48), "StopGlass")
        _box(bus_stop_node, Vector3(1.55, 0.15, 0.45), Vector3(0.0, 0.55, 0.10), _material(Color("#8d5b3f"), 0.0, 0.75), "StopBench")
    _box(bus_stop_node, Vector3(0.45, 0.62, 0.08), Vector3(-1.05, 2.65, -0.08), _material(stop_accent.lightened(0.16), 0.0, 0.6), "StopSign")
    bus_node = Node3D.new()
    bus_node.name = "YellowBus"
    bus_node.position = Vector3(-1.1, 0.9, 2.2)
    bus_stop_node.add_child(bus_node)
    _build_bus_mesh(bus_node)
    bus_node.visible = false
    bus_stop_node.visible = false

func _build_bus_mesh(parent: Node3D) -> void:
    var bus_glb := _optional_model("onibus.glb")
    if bus_glb != null:
        parent.add_child(bus_glb)
        _fit_model(bus_glb, GLB_FIT["onibus"].x, GLB_FIT["onibus"].y)
        return
    var yellow := _material(Color("#f4bf3d"), 0.08, 0.48, "vehicle_paint")
    var glass := _material(Color("#6cc4cc"), 0.0, 0.28, "glass")
    var red := _material(Color("#ed634c"), 0.0, 0.62, "paint")
    var tire := _material(Color("#202b3a"), 0.05, 0.55, "rubber")
    var chrome := _material(Color("#c3c8bf"), 0.72, 0.24, "chrome")
    var lamp := _material(Color("#fff2ba"), 0.0, 0.18, "glass")
    lamp.emission_enabled = true
    lamp.emission = Color("#ffe9a0")
    lamp.emission_energy_multiplier = 1.6
    _box(parent, Vector3(2.9, 1.55, 4.2), Vector3(0.0, 0.0, 0.0), yellow, "BusBody")
    _box(parent, Vector3(2.5, 0.58, 0.05), Vector3(0.0, 0.35, -2.12), glass, "BusWindshield")
    _box(parent, Vector3(2.5, 0.55, 0.05), Vector3(0.0, 0.34, 2.12), glass, "BusRearGlass")
    _box(parent, Vector3(0.05, 0.54, 3.55), Vector3(-1.47, 0.35, 0.0), glass, "BusSideWindows")
    _box(parent, Vector3(0.05, 0.54, 3.55), Vector3(1.47, 0.35, 0.0), glass, "BusSideWindows")
    _box(parent, Vector3(0.74, 0.85, 0.06), Vector3(-0.72, -0.05, -2.15), chrome, "BusDoor")
    _box(parent, Vector3(2.9, 0.18, 4.2), Vector3(0.0, -0.45, 0.0), red, "BusStripe")
    _box(parent, Vector3(2.98, 0.10, 0.12), Vector3(0.0, -0.65, -2.15), chrome, "BusBumper")
    _box(parent, Vector3(0.42, 0.22, 0.05), Vector3(-0.80, -0.18, -2.17), lamp, "BusHeadlight")
    _box(parent, Vector3(0.42, 0.22, 0.05), Vector3(0.80, -0.18, -2.17), lamp, "BusHeadlight")
    var destination := _material(Color("#2b2f36"), 0.0, 0.4, "glass")
    destination.emission_enabled = true
    destination.emission = Color("#ffd97a")
    destination.emission_energy_multiplier = 1.3
    _box(parent, Vector3(1.30, 0.24, 0.06), Vector3(0.0, 0.62, -2.16), destination, "BusDestination")
    _box(parent, Vector3(1.30, 0.26, 1.90), Vector3(0.0, 0.92, 0.25), _material(Color("#e8e6df"), 0.1, 0.6, "metal"), "BusRoofAC")
    for wheel_x in [-1.05, 1.05]:
        var front := _cylinder(parent, 0.38, 0.38, 0.24, Vector3(wheel_x, -0.88, -1.1), tire, "BusWheel")
        var rear := _cylinder(parent, 0.38, 0.38, 0.24, Vector3(wheel_x, -0.88, 1.1), tire, "BusWheel")
        front.rotation.z = PI / 2.0
        rear.rotation.z = PI / 2.0

func _build_brazilian_car(parent: Node3D, variant: int, dark: Material, chrome: Material, glass: Material, white_light: Material, tail_light: Material) -> void:
    var paint_colors: Array[Color] = [Color("#c83f45"), Color("#e6e7e1"), Color("#2d6d9b")]
    var paint := _material(paint_colors[variant], 0.24, 0.30, "vehicle_paint")
    var black_paint := _material(Color("#18202a"), 0.08, 0.38, "vehicle_paint")
    var plate := _material(Color("#e9edf0"), 0.05, 0.34, "metal")
    var accent := _material(Color("#315067"), 0.18, 0.34, "metal")
    var body_length: float = 3.10 if variant != 1 else 3.42
    var wheel_z: float = 1.02 if variant == 0 else 1.14
    var cabin_length: float = 1.32 if variant != 2 else 1.05
    var cabin_z: float = 0.22 if variant == 0 else (0.02 if variant == 1 else -0.38)
    _box(parent, Vector3(2.24, 0.48, body_length), Vector3(0.0, 0.48, 0.05), paint, "CarLowerBody")
    _box(parent, Vector3(1.98, 0.20, 0.76), Vector3(0.0, 0.79, -body_length * 0.32), paint, "CarHood")
    _box(parent, Vector3(1.65 if variant != 2 else 1.74, 0.58 if variant != 2 else 0.82, cabin_length), Vector3(0.0, 0.98 if variant != 2 else 1.08, cabin_z), paint, "CarCabinShell")
    _box(parent, Vector3(1.42 if variant != 2 else 1.52, 0.34 if variant != 2 else 0.47, 0.055), Vector3(0.0, 1.03 if variant != 2 else 1.16, cabin_z - cabin_length * 0.50), glass, "CarWindshield")
    _box(parent, Vector3(1.42 if variant != 2 else 1.52, 0.30 if variant != 2 else 0.40, 0.055), Vector3(0.0, 1.03 if variant != 2 else 1.16, cabin_z + cabin_length * 0.50), glass, "CarRearGlass")
    var side_window_size: Vector3 = Vector3(0.055, 0.30 if variant != 2 else 0.42, cabin_length * 0.80)
    _box(parent, side_window_size, Vector3(-0.84 if variant != 2 else -0.88, 1.03 if variant != 2 else 1.16, cabin_z), glass, "CarSideGlass")
    _box(parent, side_window_size, Vector3(0.84 if variant != 2 else 0.88, 1.03 if variant != 2 else 1.16, cabin_z), glass, "CarSideGlass")
    _box(parent, Vector3(2.30, 0.10, 0.13), Vector3(0.0, 0.25, -body_length * 0.5), chrome, "CarFrontBumper")
    _box(parent, Vector3(2.30, 0.10, 0.13), Vector3(0.0, 0.25, body_length * 0.5), chrome, "CarRearBumper")
    _box(parent, Vector3(0.34, 0.15, 0.05), Vector3(-0.68, 0.66, -body_length * 0.51), white_light, "CarHeadlight")
    _box(parent, Vector3(0.34, 0.15, 0.05), Vector3(0.68, 0.66, -body_length * 0.51), white_light, "CarHeadlight")
    _box(parent, Vector3(0.28, 0.13, 0.05), Vector3(-0.72, 0.57, body_length * 0.51), tail_light, "CarTaillight")
    _box(parent, Vector3(0.28, 0.13, 0.05), Vector3(0.72, 0.57, body_length * 0.51), tail_light, "CarTaillight")
    _box(parent, Vector3(0.52, 0.14, 0.035), Vector3(0.0, 0.43, -body_length * 0.515), plate, "CarFrontPlate")
    _box(parent, Vector3(0.52, 0.14, 0.035), Vector3(0.0, 0.43, body_length * 0.515), plate, "CarRearPlate")
    for side in [-1.0, 1.0]:
        _box(parent, Vector3(0.08, 0.06, 0.36), Vector3(side * 1.12, 0.90, cabin_z - 0.34), accent, "CarMirror")
        _box(parent, Vector3(0.04, 0.04, 0.20), Vector3(side * 1.13, 0.82, -0.05), chrome, "CarDoorHandle")
    _wheels(parent, dark, 1.02, wheel_z)
    for x in [-1.02, 1.02]:
        for z in [-wheel_z, wheel_z]:
            var hub := _cylinder(parent, 0.13, 0.13, 0.20, Vector3(x, 0.18, z), chrome, "WheelHub")
            hub.rotation.z = PI / 2.0
    match variant:
        0:
            _box(parent, Vector3(1.34, 0.08, 0.12), Vector3(0.0, 1.45, body_length * 0.42), black_paint, "HatchSpoiler")
            _box(parent, Vector3(1.55, 0.07, 0.06), Vector3(0.0, 0.43, 0.0), black_paint, "HatchGrille")
        1:
            _box(parent, Vector3(1.82, 0.18, 0.55), Vector3(0.0, 0.70, body_length * 0.34), paint, "SedanTrunk")
            _box(parent, Vector3(1.52, 0.07, 0.06), Vector3(0.0, 0.43, -body_length * 0.51), black_paint, "SedanGrille")
        _:
            _box(parent, Vector3(2.02, 0.12, 1.64), Vector3(0.0, 1.18, 0.60), paint, "UtilityCargo")
            _box(parent, Vector3(1.88, 0.07, 0.06), Vector3(0.0, 0.48, -body_length * 0.51), black_paint, "UtilityGrille")
            _cylinder(parent, 0.035, 0.035, 1.40, Vector3(-0.82, 1.74, 0.50), chrome, "UtilityRoofRack")
            _cylinder(parent, 0.035, 0.035, 1.40, Vector3(0.82, 1.74, 0.50), chrome, "UtilityRoofRack")

const GLB_FIT := {
    "car": Vector2(4.2, 1.45), # 4.2x1.45 realista (era 4.4x1.55)
    "motorcycle": Vector2(2.05, 1.05), # 2.05x1.05 compacta
    "truck": Vector2(6.2, 2.65),
    "bus_traffic": Vector2(7.2, 2.95),
    "onibus": Vector2(8.0, 2.95),
    "carro": Vector2(4.2, 1.45),
}
# Lote 6: reserva variantes de veículo (cor/rodas com textura baked) — drop-in opcional.
# Cada kind sorteia entre a base e as variantes se o arquivo existir; fallback seguro.
const VEHICLE_VARIANTS := {
    "car": ["car.glb", "car_azul.glb", "car_prata.glb"],
    "truck": ["truck.glb", "truck_vermelho.glb"],
    "motorcycle": ["motorcycle.glb", "motorcycle_verde.glb"],
}
var _glb_cache: Dictionary = {}
var _animal_glb_cache: Dictionary = {}
var _tint_cache: Dictionary = {}

func _optional_model(file: String) -> Node3D:
    # Drop-in opcional: se existir um modelo GLB em assets/vehicles/<file>,
    # ele substitui o veiculo procedural (assets CC0, ver assets/vehicles/README.md).
    if not _glb_cache.has(file):
        var packed: PackedScene = null
        var path := "res://assets/vehicles/" + file
        if ResourceLoader.exists(path):
            packed = load(path) as PackedScene
        _glb_cache[file] = packed
    var cached: PackedScene = _glb_cache[file]
    if cached == null:
        return null
    var node := cached.instantiate() as Node3D
    if node == null:
        push_warning("Falha ao instanciar modelo de veiculo: " + file)
        return null
    return node

func _optional_prop(file: String) -> Node3D:
    # Drop-in de mobiliario: se existir assets/props/<file> (GLB original, ver
    # assets/props/LEIA-ME.md), ele substitui a versao procedural do objeto.
    var chave := "props/" + file
    if not _glb_cache.has(chave):
        var packed: PackedScene = null
        var path := "res://assets/props/" + file
        if ResourceLoader.exists(path):
            packed = load(path) as PackedScene
        _glb_cache[chave] = packed
    var cached: PackedScene = _glb_cache[chave]
    if cached == null:
        return null
    var node := cached.instantiate() as Node3D
    if node == null:
        push_warning("Falha ao instanciar prop: " + file)
        return null
    return node


func _optional_glb(subpath: String) -> Node3D:
    # Drop-in generico por subcaminho de assets/ (ex.: "collectibles/coin.glb",
    # "sky_fx/aviao.glb"). Se o GLB existir, substitui o objeto procedural;
    # se nao, o builder antigo continua como fallback de seguranca.
    if not _glb_cache.has(subpath):
        var packed: PackedScene = null
        var path := "res://assets/" + subpath
        if ResourceLoader.exists(path):
            packed = load(path) as PackedScene
        _glb_cache[subpath] = packed
    var cached: PackedScene = _glb_cache[subpath]
    if cached == null:
        return null
    var node := cached.instantiate() as Node3D
    if node == null:
        push_warning("Falha ao instanciar GLB: " + subpath)
        return null
    return node


func _tint_glb(node: Node3D, tint) -> void:
    # Pinta os materiais "Tint*" de um GLB de cenario com a cor da fase.
    # `tint` aceita um Color (uma cor para todos os Tint*) ou um Dictionary
    # {nome_do_material: Color} para pecas com varias cores (parede/telhado).
    # Cada (nome, cor) e duplicado uma vez e aplicado por surface override —
    # a cena em cache (_glb_cache) nunca e modificada.
    if node == null:
        return
    var stack: Array[Node] = [node]
    while not stack.is_empty():
        var current: Node = stack.pop_back()
        stack.append_array(current.get_children())
        if not current is MeshInstance3D:
            continue
        var mesh_node := current as MeshInstance3D
        var mesh := mesh_node.mesh
        if mesh == null:
            continue
        for surface in mesh.get_surface_count():
            var base := mesh.surface_get_material(surface)
            if base == null:
                continue
            var mat_name := str(base.resource_name)
            if not mat_name.begins_with("Tint"):
                continue
            var color := Color.WHITE
            if tint is Dictionary:
                if not (tint as Dictionary).has(mat_name):
                    continue
                color = (tint as Dictionary)[mat_name]
            else:
                color = tint
            var key := mat_name + "#" + color.to_html()
            if not _tint_cache.has(key):
                var dup := base.duplicate() as Material
                if dup == null:
                    continue
                dup.set("albedo_color", color)
                _tint_cache[key] = dup
            mesh_node.set_surface_override_material(surface, _tint_cache[key])


func _model_bounds(root: Node3D) -> AABB:
    var bounds := AABB()
    var found := false
    var stack: Array[Node] = [root]
    while not stack.is_empty():
        var current: Node = stack.pop_back()
        stack.append_array(current.get_children())
        if current is MeshInstance3D:
            var mesh_node: MeshInstance3D = current
            var compose := mesh_node.transform
            var walker: Node = mesh_node.get_parent()
            while walker != null and walker != root:
                if walker is Node3D:
                    compose = (walker as Node3D).transform * compose
                walker = walker.get_parent()
            var aabb := mesh_node.get_aabb().abs()
            for endpoint_i in 8:
                var world_point: Vector3 = compose * aabb.get_endpoint(endpoint_i)
                if found:
                    bounds = bounds.expand(world_point)
                else:
                    bounds = AABB(world_point, Vector3.ZERO)
                    found = true
    return bounds

func _fit_model(node: Node3D, target_length: float, target_height: float) -> void:
    var bounds := _model_bounds(node)
    if not bounds.has_volume():
        return
    # Auditoria proporção: considera largura também (veículos estavam 0.3m mais largos)
    var target_width := target_height * 1.24 if target_length > 6.0 else (0.75 if target_length < 2.3 else 1.80)
    if target_length > 7.0:
        target_width = 2.55
    elif target_length > 6.0:
        target_width = 2.50
    var fit := minf(target_length / maxf(bounds.size.z, 0.001), target_height / maxf(bounds.size.y, 0.001))
    fit = minf(fit, target_width / maxf(bounds.size.x, 0.001))
    node.scale = Vector3.ONE * fit
    var offset := Vector3(-bounds.position.x, -bounds.position.y, -bounds.position.z - bounds.size.z * 0.5) * fit
    node.position += offset
    _enhance_vehicle_instance(node)
    _pivot_wheels(node, fit)

func _pivot_wheels(root: Node3D, fit: float) -> void:
    # Nos GLBs originais (build_lote5/6) a roda vem com a geometria "assada" na
    # posição final e o nó na origem do veículo. Girar rotation.x nesse nó faz
    # a roda ORBITAR o centro do carro (bug visual reportado). Aqui cada roda
    # ganha um pivô no centro da sua AABB; o pivô herda o nome Wheel*/BusWheel*/
    # MotoWheel* (é ele que _animate_traffic gira) e guarda o raio real em metros.
    for child in root.find_children("*", "MeshInstance3D", true, false):
        var wheel := child as MeshInstance3D
        if wheel == null or wheel.mesh == null:
            continue
        var wheel_name := str(wheel.name)
        if not (wheel_name.begins_with("Wheel") or wheel_name.begins_with("BusWheel") or wheel_name.begins_with("MotoWheel")):
            continue
        if wheel.get_parent() != null and wheel.get_parent().has_meta("wheel_radius"):
            continue
        var aabb := wheel.mesh.get_aabb()
        var center_local := aabb.get_center()
        var parent := wheel.get_parent()
        var pivot := Node3D.new()
        pivot.name = wheel_name
        pivot.transform = wheel.transform.translated_local(center_local)
        # raio de rolagem em metros de mundo (eixo da roda é X nos GLBs; usa a maior
        # dimensão perpendicular, robusto se algum modelo vier com eixo em Z)
        var radius_local: float = maxf(aabb.size.y, aabb.size.z) * 0.5
        pivot.set_meta("wheel_radius", radius_local * fit * wheel.transform.basis.get_scale().y)
        parent.remove_child(wheel)
        parent.add_child(pivot)
        wheel.name = wheel_name + "Mesh"
        wheel.transform = Transform3D(Basis.IDENTITY, -center_local)
        pivot.add_child(wheel)

func _enhance_vehicle_instance(node: Node3D) -> void:
    for child in node.find_children("*", "MeshInstance3D"):
        var mesh_inst := child as MeshInstance3D
        if mesh_inst == null or mesh_inst.mesh == null:
            continue
        for s in mesh_inst.mesh.get_surface_count():
            var mat := mesh_inst.get_surface_override_material(s)
            if mat == null:
                mat = mesh_inst.mesh.surface_get_material(s)
            if mat is BaseMaterial3D:
                var mat_name := str(mat.resource_name).to_lower()
                var new_mat := mat.duplicate() as BaseMaterial3D
                if mat_name.contains("pintura") or mat_name.contains("paint") or mat_name.contains("quadro"):
                    new_mat.clearcoat_enabled = true
                    new_mat.clearcoat = 0.65
                    new_mat.clearcoat_roughness = 0.10
                    new_mat.roughness = minf(new_mat.roughness, 0.28)
                    new_mat.rim_enabled = true
                    new_mat.rim = 0.15
                    new_mat.rim_tint = 0.45
                    mesh_inst.set_surface_override_material(s, new_mat)
                elif mat_name.contains("vidro") or mat_name.contains("glass"):
                    new_mat.clearcoat_enabled = true
                    new_mat.clearcoat = 0.85
                    new_mat.clearcoat_roughness = 0.05
                    new_mat.roughness = 0.06
                    mesh_inst.set_surface_override_material(s, new_mat)
                elif mat_name.contains("cromo") or mat_name.contains("chrome"):
                    new_mat.metallic = 0.92
                    new_mat.roughness = 0.12
                    mesh_inst.set_surface_override_material(s, new_mat)

func _pick_vehicle_variant(kind: String) -> String:
    # Lote 6: sorteia drop-in entre as variantes se existirem; determinístico por seed da corrida.
    var lista: Array = VEHICLE_VARIANTS.get(kind, [kind + ".glb"])
    var existentes: Array[String] = []
    for f in lista:
        if ResourceLoader.exists("res://assets/vehicles/" + str(f)):
            existentes.append(str(f))
    if existentes.is_empty():
        return kind + ".glb"
    # usa o tamanho atual de entities + phase_index para variar sem RNG extra (auditável)
    var idx: int = abs((str(kind) + str(entities.size()) + str(phase_index)).hash()) % existentes.size()
    return existentes[idx]

func _build_road_obstacle(parent: Node3D, kind: String) -> void:
    if GLB_FIT.has(kind):
        var variant := _pick_vehicle_variant(kind)
        var replacement := _optional_model(variant)
        if replacement != null:
            parent.add_child(replacement)
            _fit_model(replacement, GLB_FIT[kind].x, GLB_FIT[kind].y)
            if kind == "motorcycle":
                _build_motoqueiro(parent, Vector3(0.0, 0.42, 0.05))
            return
    var body := _material(Color("#d9584e"), 0.05, 0.48, "paint")
    var dark := _material(Color("#202c3c"), 0.15, 0.38, "rubber")
    var chrome := _material(Color("#aebdc0"), 0.72, 0.24, "chrome")
    var glass := _material(Color("#71bcc7"), 0.0, 0.25, "glass")
    var white_light := _material(Color("#fff4c9"), 0.0, 0.18, "glass")
    white_light.emission_enabled = true
    white_light.emission = Color("#fff1b0")
    white_light.emission_energy_multiplier = 1.6
    var tail_light := _material(Color("#cc3942"), 0.0, 0.28, "glass")
    match kind:
        "car":
            _build_brazilian_car(parent, abs(parent.name.hash()) % 3, dark, chrome, glass, white_light, tail_light)
        "bus_traffic":
            var bus_body := _material(Color("#e7b73d"), 0.08, 0.50, "vehicle_paint")
            _box(parent, Vector3(2.52, 1.55, 4.35), Vector3(0.0, 0.90, 0.0), bus_body, "TrafficBusBody")
            _box(parent, Vector3(2.34, 0.12, 4.12), Vector3(0.0, 1.72, 0.0), chrome, "TrafficBusRoof")
            _box(parent, Vector3(2.16, 0.68, 0.055), Vector3(0.0, 1.18, -2.19), glass, "TrafficBusWindshield")
            _box(parent, Vector3(2.16, 0.62, 0.055), Vector3(0.0, 1.16, 2.19), glass, "TrafficBusRearGlass")
            _box(parent, Vector3(0.055, 0.62, 3.72), Vector3(-1.27, 1.18, 0.0), glass, "TrafficBusSideGlass")
            _box(parent, Vector3(0.055, 0.62, 3.72), Vector3(1.27, 1.18, 0.0), glass, "TrafficBusSideGlass")
            _box(parent, Vector3(2.58, 0.16, 4.38), Vector3(0.0, 0.28, 0.0), _material(Color("#d44c43"), 0.0, 0.54, "paint"), "TrafficBusStripe")
            _box(parent, Vector3(0.48, 0.28, 0.05), Vector3(-0.72, 0.69, -2.21), white_light, "TrafficBusHeadlight")
            _box(parent, Vector3(0.48, 0.28, 0.05), Vector3(0.72, 0.69, -2.21), white_light, "TrafficBusHeadlight")
            _box(parent, Vector3(2.6, 0.12, 0.10), Vector3(0.0, 0.20, -2.22), chrome, "TrafficBusBumper")
            _wheels(parent, dark, 1.10, 1.45)
        "motorcycle":
            var moto_front := _cylinder(parent, 0.33, 0.33, 0.18, Vector3(-0.48, 0.32, -0.65), dark, "WheelMotoFront")
            var moto_rear := _cylinder(parent, 0.33, 0.33, 0.18, Vector3(-0.48, 0.32, 0.65), dark, "WheelMotoRear")
            moto_front.rotation.z = PI / 2.0
            moto_rear.rotation.z = PI / 2.0
            var frame := _material(Color("#252f3b"), 0.72, 0.34, "metal")
            _box(parent, Vector3(0.10, 0.48, 1.16), Vector3(-0.48, 0.65, 0.0), frame, "MotoFrame")
            var tank := _sphere(parent, 0.30, Vector3(-0.48, 0.86, -0.12), _material(Color("#39bda9"), 0.18, 0.30, "vehicle_paint"), "MotoTank")
            tank.scale = Vector3(0.72, 0.62, 1.35)
            _box(parent, Vector3(0.26, 0.12, 0.52), Vector3(-0.48, 0.72, 0.43), _material(Color("#141b25"), 0.0, 0.6, "rubber"), "MotoSeat")
            _box(parent, Vector3(0.72, 0.06, 0.06), Vector3(-0.48, 1.24, -0.62), frame, "MotoHandlebar")
            _sphere(parent, 0.12, Vector3(-0.48, 1.14, -0.69), white_light, "MotoHeadlight")
            _build_motoqueiro(parent, Vector3(-0.48, 0.34, 0.08))
            _cylinder(parent, 0.055, 0.055, 0.92, Vector3(-0.48, 0.48, 0.30), chrome, "MotoExhaust")
        "truck":
            var truck_body := _material(Color("#d65f42"), 0.08, 0.48, "vehicle_paint")
            _box(parent, Vector3(2.55, 1.72, 2.10), Vector3(0.0, 1.02, 0.68), truck_body, "TruckCargo")
            _box(parent, Vector3(2.52, 1.46, 1.25), Vector3(0.0, 0.84, -1.02), truck_body, "TruckCab")
            _box(parent, Vector3(2.12, 0.64, 0.055), Vector3(0.0, 1.40, -1.66), glass, "TruckWindshield")
            _box(parent, Vector3(2.25, 0.15, 0.08), Vector3(0.0, 0.28, -1.68), chrome, "TruckBumper")
            _box(parent, Vector3(0.34, 0.22, 0.05), Vector3(-0.70, 0.72, -1.70), white_light, "TruckHeadlight")
            _box(parent, Vector3(0.34, 0.22, 0.05), Vector3(0.70, 0.72, -1.70), white_light, "TruckHeadlight")
            _box(parent, Vector3(2.22, 0.07, 0.05), Vector3(0.0, 1.60, 1.76), _material(Color("#f4c94e"), 0.0, 0.55, "paint"), "TruckReflectiveStrip")
            _wheels(parent, dark, 1.08, 1.15)
        "pothole":
            var pothole_glb := _optional_glb("scene/pothole.glb")
            if pothole_glb != null:
                pothole_glb.position = Vector3(0, 0.02, 0)
                parent.add_child(pothole_glb)
                return
            _cylinder(parent, 0.84, 0.84, 0.035, Vector3(0.0, 0.04, 0.0), _material(Color("#101723"), 0.0, 1.0, "asphalt"), "Pothole")
            _cylinder(parent, 0.58, 0.58, 0.045, Vector3(0.0, 0.068, 0.0), _material(Color("#283243"), 0.0, 1.0, "dirt"), "PotholeInner")
            for i in 7:
                var angle: float = float(i) * TAU / 7.0
                _box(parent, Vector3(0.20, 0.035, 0.07), Vector3(cos(angle) * 0.82, 0.075, sin(angle) * 0.82), _material(Color("#59616a"), 0.0, 0.95, "asphalt"), "BrokenAsphalt")
        _:
            _box(parent, Vector3(2.0, 0.8, 2.0), Vector3(0.0, 0.5, 0.0), body, "RoadHazard")

func _build_motoqueiro(parent: Node3D, assento: Vector3) -> void:
    # Motoqueiro de verdade: o mesmo humanoide skinned do corredor (Quaternius,
    # CC0), sentado na moto com o clip Driving_Loop da Universal Animation
    # Library. Se a biblioteca nao carregar, o NPC cai no modo idle sem T-pose.
    var rider := WORLD_CHARACTER_SCRIPT.new() as Node3D
    rider.name = "Motoqueiro3D"
    rider.set("profile_id", "carlos")
    rider.set("role", "motoqueiro")
    rider.set("avatar_scale", 0.92) # 0.92 realista (era 0.80)
    rider.position = assento
    rider.rotation.y = PI   # de frente para o sentido da moto (-Z)
    parent.add_child(rider)


func _build_pedestrian_obstacle(parent: Node3D, profile_id: String, role: String, avatar_scale: float) -> Node3D:
    var pedestrian := WORLD_CHARACTER_SCRIPT.new() as Node3D
    pedestrian.name = "Pedestrian3D_%s" % role
    pedestrian.set("profile_id", profile_id)
    pedestrian.set("role", role)
    pedestrian.set("avatar_scale", avatar_scale)
    parent.add_child(pedestrian)
    return pedestrian

func _build_animal_obstacle(parent: Node3D, species: String) -> Node3D:
    # Drop-in opcional: assets/characters/animais/<especie>.glb (CC0 — veja o
    # LEIA-ME da pasta). Se existir, substitui o modelo procedural e toca a
    # primeira animacao de caminhada encontrada, em loop.
    var modelo := _modelo_animal_opcional(species)
    if modelo != null:
        modelo.rotation.y = PI / 2.0   # GLBs chegam olhando +Z; a convensao da entidade e +X
        parent.add_child(modelo)
        _fit_model(modelo, 0.95, 0.72)
        _tocar_animal(modelo)
        return modelo
    var animal := WORLD_ANIMAL_SCRIPT.new() as Node3D
    animal.name = "Animal3D_%s" % species
    animal.set("species", species)
    parent.add_child(animal)
    return animal


func _modelo_animal_opcional(species: String) -> Node3D:
    var file := species + ".glb"
    if not _animal_glb_cache.has(file):
        var packed: PackedScene = null
        var path := "res://assets/characters/animais/" + file
        if ResourceLoader.exists(path):
            packed = load(path) as PackedScene
        _animal_glb_cache[file] = packed
    var cached: PackedScene = _animal_glb_cache[file]
    if cached == null:
        return null
    var node := cached.instantiate() as Node3D
    if node == null:
        push_warning("Falha ao instanciar modelo de animal: " + file)
        return null
    return node


func _tocar_animal(raiz: Node3D) -> void:
    var player := _find_animation_player_node(raiz)
    if player == null or player.get_animation_list().is_empty():
        return
    var escolhido := ""
    for nome in player.get_animation_list():
        if nome.to_lower().contains("walk") or nome.to_lower().contains("trot"):
            escolhido = nome
            break
    if escolhido == "":
        escolhido = player.get_animation_list()[0]
    var anim := player.get_animation(escolhido)
    if anim != null:
        anim.loop_mode = Animation.LOOP_LINEAR
    player.play(escolhido)


func _find_animation_player_node(node: Node) -> AnimationPlayer:
    var pending: Array[Node] = [node]
    while not pending.is_empty():
        var current: Node = pending.pop_back()
        if current is AnimationPlayer:
            return current as AnimationPlayer
        for child in current.get_children():
            pending.append(child)
    return null

func _build_sidewalk_obstacle(parent: Node3D, kind: String) -> void:
    var dark := _material(Color("#29354d"), 0.0, 0.72, "fabric")
    var red := _material(Color("#e94f5a"), 0.0, 0.66, "paint")
    var chrome := _material(Color("#aebdc0"), 0.72, 0.24, "chrome")
    match kind:
        "old_lady":
            # A velhinha alterna entre a Vovó Zilda (lote 2) e a Maria do
            # Bairro: variedade de calçada sem quebrar o contrato de obstáculo.
            var granny_profiles: Array[String] = ["zilda", "maria"]
            _build_pedestrian_obstacle(parent, granny_profiles[abs(parent.name.hash()) % granny_profiles.size()], "old_lady", 0.88)
        "hydrant":
            var hidrante_glb := _optional_prop("hidrante.glb")
            if hidrante_glb != null:
                parent.add_child(hidrante_glb)
                return
            var hydrant_red := _material(Color("#d95750"), 0.0, 0.62, "metal")
            _cylinder(parent, 0.28, 0.34, 0.64, Vector3(0.0, 0.40, 0.0), hydrant_red, "HydrantBody")
            _cylinder(parent, 0.22, 0.28, 0.22, Vector3(0.0, 0.82, 0.0), hydrant_red, "HydrantNeck")
            _sphere(parent, 0.31, Vector3(0.0, 1.00, 0.0), hydrant_red, "HydrantDome")
            for side in [-1.0, 1.0]:
                var nozzle := _cylinder(parent, 0.12, 0.16, 0.20, Vector3(side * 0.29, 0.60, 0.0), hydrant_red, "HydrantNozzle")
                nozzle.rotation.z = PI / 2.0
                _cylinder(parent, 0.055, 0.07, 0.04, Vector3(side * 0.41, 0.60, 0.0), _material(Color("#f0a345"), 0.35, 0.42, "metal"), "HydrantCap")
            _cylinder(parent, 0.055, 0.055, 0.70, Vector3(0.0, 0.61, 0.0), _material(Color("#f0a345"), 0.35, 0.42, "metal"), "HydrantHandle")
        "payphone":
            var orelhao_glb := _optional_prop("orelhao.glb")
            if orelhao_glb != null:
                parent.add_child(orelhao_glb)
                return
            var phone_body := _material(Color("#2d9ca4"), 0.0, 0.52, "metal")
            _box(parent, Vector3(0.55, 1.72, 0.42), Vector3(0.0, 0.91, 0.0), phone_body, "PayphoneBody")
            _box(parent, Vector3(0.68, 0.10, 0.48), Vector3(0.0, 1.82, 0.0), phone_body, "PayphoneHood")
            _box(parent, Vector3(0.38, 0.40, 0.04), Vector3(0.0, 1.32, -0.23), _material(Color("#d9e8df"), 0.0, 0.4, "glass"), "PayphonePanel")
            _box(parent, Vector3(0.08, 0.24, 0.10), Vector3(-0.22, 1.37, -0.28), _material(Color("#f0bd4a"), 0.0, 0.34, "metal"), "PayphoneCoinSlot")
            _box(parent, Vector3(0.14, 0.48, 0.11), Vector3(0.28, 1.48, -0.18), _material(Color("#182331"), 0.0, 0.5, "rubber"), "PayphoneHandset")
            _box(parent, Vector3(0.75, 0.08, 0.08), Vector3(0.0, 0.08, 0.0), phone_body, "PayphoneBase")
        "dog":
            _build_animal_obstacle(parent, "caramelo")
        "bicycle":
            # drop-in: um bicycle.glb em assets/vehicles/ substitui a
            # bicicleta procedural (ver assets/vehicles/README.md)
            var bike_glb := _optional_model("bicycle.glb")
            if bike_glb != null:
                parent.add_child(bike_glb)
                _fit_model(bike_glb, 1.85, 1.15)
                return
            # bicicleta de aco: rodas com pneu e aro, quadro em tubos,
            # guidao, selim, pedivela e pedais — alinhada com a rua (frente -Z)
            var bike_tire := _material(Color("#1d232e"), 0.15, 0.78, "rubber")
            var bike_rim := _material(Color("#b9c3c9"), 0.8, 0.30, "chrome")
            var bike_frame := _material(Color("#2f6fa8"), 0.35, 0.42, "metal")
            for roda in [-0.52, 0.52]:
                var pneu := _torus(parent, 0.285, 0.395, Vector3(0.0, 0.34, roda), bike_tire, "BikePneu")
                pneu.rotation.z = PI / 2.0
                var aro := _torus(parent, 0.258, 0.302, Vector3(0.0, 0.34, roda), bike_rim, "BikeAro")
                aro.rotation.z = PI / 2.0
                for raio_i in range(4):
                    var ang := TAU * float(raio_i) / 4.0
                    var raio := _box(parent, Vector3(0.018, 0.54, 0.018), Vector3(0.0, 0.34, roda), bike_rim, "BikeRaio")
                    raio.rotation.x = ang
                    raio.rotation.y = 0.0
                    raio.position = Vector3(0.0, 0.34, roda)
                    raio.rotation.z = 0.0
                var cubo := _cylinder(parent, 0.045, 0.045, 0.09, Vector3(0.0, 0.34, roda), bike_rim, "BikeCubo")
                cubo.rotation.z = PI / 2.0
            var movimento := Node3D.new()
            movimento.name = "BikeQuadro"
            parent.add_child(movimento)
            var tubos := [
                [Vector3(0.0, 0.62, -0.44), Vector3(0.0, 0.98, -0.40)],   # head tube
                [Vector3(0.0, 0.36, 0.06), Vector3(0.0, 0.98, -0.40)],    # downtube
                [Vector3(0.0, 0.36, 0.06), Vector3(0.0, 1.00, 0.20)],     # seat tube
                [Vector3(0.0, 1.00, 0.20), Vector3(0.0, 0.98, -0.40)],    # toptube
                [Vector3(0.0, 0.36, 0.06), Vector3(0.0, 0.34, 0.52)],     # chainstay
                [Vector3(0.0, 0.98, 0.20), Vector3(0.0, 0.34, 0.52)],     # seat stay
                [Vector3(0.0, 0.98, -0.40), Vector3(0.0, 0.34, -0.52)],   # fork
            ]
            for tubo in tubos:
                var a: Vector3 = tubo[0]
                var b: Vector3 = tubo[1]
                var meio := (a + b) * 0.5
                var comprimento := a.distance_to(b)
                var tubo_no := _box(movimento, Vector3(0.05, comprimento, 0.05), meio, bike_frame, "BikeTubo")
                # orienta o eixo Y local do tubo ao longo de a->b (look_at exige
                # no na arvore e alvo global; basis evita os dois problemas)
                tubo_no.basis = Basis(Quaternion(Vector3(0, 1, 0), (b - a).normalized()))
            _box(movimento, Vector3(0.52, 0.05, 0.05), Vector3(0.0, 1.06, -0.44), chrome, "BikeGuidao")
            _box(movimento, Vector3(0.05, 0.12, 0.05), Vector3(0.0, 0.99, -0.42), chrome, "BikeMesa")
            _box(movimento, Vector3(0.10, 0.06, 0.34), Vector3(0.0, 1.06, 0.22), dark, "BikeSelim")
            var pedivela := _box(movimento, Vector3(0.04, 0.34, 0.04), Vector3(0.0, 0.36, 0.06), bike_rim, "BikePedivela")
            pedivela.rotation.x = PI / 4.0
            _box(movimento, Vector3(0.09, 0.02, 0.20), Vector3(0.09, 0.28, 0.10), chrome, "BikePedal")
            _box(movimento, Vector3(0.09, 0.02, 0.20), Vector3(-0.09, 0.44, 0.02), chrome, "BikePedal2")
        "cone":
            var cone_glb := _optional_prop("cone.glb")
            if cone_glb != null:
                parent.add_child(cone_glb)
                return
            var cone_orange := _material(Color("#f0783f"), 0.0, 0.68, "rubber")
            var cone_white := _material(Color("#f4e6c5"), 0.0, 0.72, "rubber")
            _box(parent, Vector3(0.98, 0.12, 0.58), Vector3(0.0, 0.08, 0.0), cone_orange, "ConeBase")
            _cone(parent, 0.40, 0.92, Vector3(0.0, 0.54, 0.0), cone_orange, "TrafficCone")
            _cylinder(parent, 0.29, 0.33, 0.11, Vector3(0.0, 0.62, 0.0), cone_white, "ConeReflectiveBand")
            _cylinder(parent, 0.18, 0.22, 0.10, Vector3(0.0, 0.90, 0.0), cone_white, "ConeReflectiveTip")
        "vendor":
            var carrinho_glb := _optional_prop("carrinho.glb")
            if carrinho_glb != null:
                parent.add_child(carrinho_glb)
            else:
                var cart_wood := _material(Color("#e2a846"), 0.0, 0.72, "wood")
                var awning := _material(Color("#e94f5a"), 0.0, 0.66, "fabric")
                _box(parent, Vector3(1.45, 1.0, 0.9), Vector3(0.0, 0.58, 0.0), cart_wood, "VendorCart")
                _box(parent, Vector3(1.60, 0.08, 0.90), Vector3(0.0, 1.17, 0.0), _material(Color("#f2c35b"), 0.0, 0.66, "wood"), "VendorCounter")
                _box(parent, Vector3(1.74, 0.10, 1.08), Vector3(0.0, 1.40, 0.0), awning, "VendorAwning")
                _cylinder(parent, 0.18, 0.18, 0.10, Vector3(-0.50, 0.12, 0.52), dark, "VendorWheel")
                _cylinder(parent, 0.18, 0.18, 0.10, Vector3(0.50, 0.12, 0.52), dark, "VendorWheel")
                _cylinder(parent, 0.06, 0.06, 1.05, Vector3(-0.64, 1.55, 0.0), chrome, "VendorPole")
                _cylinder(parent, 0.06, 0.06, 1.05, Vector3(0.64, 1.55, 0.0), chrome, "VendorPole")
            # O camelô alterna entre a Dona Marta da Feira (lote 2) e o Zé:
            # a banca ganha bandana e avental sem perder a leitura de obstáculo.
            var vendor_profiles: Array[String] = ["marta", "ze"]
            var vendor_character := _build_pedestrian_obstacle(parent, vendor_profiles[abs(parent.name.hash()) % vendor_profiles.size()], "vendor", 0.78)
            vendor_character.position = Vector3(0.0, 0.0, -0.18)
        "bench":
            var banco_glb := _optional_prop("banco.glb")
            if banco_glb != null:
                parent.add_child(banco_glb)
                return
            var bench_wood := _material(Color("#9a633d"), 0.0, 0.8, "wood")
            var bench_metal := _material(Color("#3e4d59"), 0.55, 0.52, "metal")
            _box(parent, Vector3(1.5, 0.15, 0.42), Vector3(0.0, 0.72, 0.0), bench_wood, "BenchSeat")
            _box(parent, Vector3(1.5, 0.8, 0.12), Vector3(0.0, 1.10, 0.17), _material(Color("#aa7045"), 0.0, 0.8, "wood"), "BenchBack")
            for side in [-0.56, 0.56]:
                _box(parent, Vector3(0.10, 0.75, 0.12), Vector3(side, 0.37, 0.0), bench_metal, "BenchLeg")
                _box(parent, Vector3(0.18, 0.34, 0.10), Vector3(side, 0.86, 0.04), bench_metal, "BenchArm")
        _:
            _box(parent, Vector3(1.2, 0.8, 0.8), Vector3(0.0, 0.45, 0.0), red, "SidewalkHazard")

func _build_collectible(parent: Node3D, kind: String) -> void:
    parent.position.y = 1.25
    var colors: Dictionary = {
        "coin": GOLD, "coffee": Color("#b87d55"), "bread": Color("#f2b04c"),
        "pastel": Color("#e99b52"), "sugarcane": Color("#68cf83"), "pass": Color("#d8f0a2"),
        "golden": Color("#fff0a0"), "coxinha": Color("#e5a143"), "guarana": Color("#e85d68"),
        "pix": CYAN, "umbrella": BLUE
    }
    var color: Color = colors.get(kind, GOLD)
    # Lote 8: coletáveis viram GLBs originais (assets/collectibles/); o builder
    # procedural continua como fallback. O node pai gira em Y no _update_run,
    # entao o GLB e centrado na origem. O glow translúcido fica por cima nos
    # dois casos para manter a leitura de pickup.
    var coletavel_glb := _optional_glb("collectibles/" + kind + ".glb")
    if coletavel_glb != null:
        coletavel_glb.name = "Collectible3D_" + kind
        # Auditoria proporção realista: humano 1.82, coin real 0.05 vs 0.60 raw => escala 0.083
        var _collect_scale := 0.45
        match kind:
            "coin": _collect_scale = 0.12  # 0.60*0.12=0.072 diam 7.2cm
            "golden": _collect_scale = 0.15
            "pass": _collect_scale = 0.16
            "bread": _collect_scale = 0.32
            "pastel": _collect_scale = 0.26
            "coxinha": _collect_scale = 0.22
            "coffee": _collect_scale = 0.30
            "guarana": _collect_scale = 0.28
            "pix": _collect_scale = 0.30
            "sugarcane": _collect_scale = 0.35
            "umbrella": _collect_scale = 0.75
            _: _collect_scale = 0.30
        coletavel_glb.scale = Vector3.ONE * _collect_scale
        parent.add_child(coletavel_glb)
        var glow_glb := _material(Color(color, 0.10), 0.0, 0.8, "glass")
        glow_glb.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        _sphere(parent, 0.14, Vector3.ZERO, glow_glb, "Glow") # 0.14 vs 0.36 proporcional
        return
    var mat := _material(color, 0.12 if kind in ["coin", "golden"] else 0.0, 0.28, "metal" if kind in ["coin", "golden"] else "paint")
    mat.emission_enabled = true
    mat.emission = color
    mat.emission_energy_multiplier = 1.8
    match kind:
        "coin", "golden":
            # moeda em pe: disco cunhado com aro em relevo, girando no eixo
            var raio := 0.30 if kind == "coin" else 0.38
            var disco := _cylinder(parent, raio, raio, 0.055, Vector3.ZERO, mat, "Coin")
            disco.rotation.x = PI / 2.0
            var aro := _torus(parent, raio - 0.028, raio + 0.028, Vector3.ZERO, _material(Color("#c9932f"), 0.4, 0.24, "metal"), "CoinAro")
            aro.rotation.x = PI / 2.0
            var relevo := _torus(parent, raio * 0.62 - 0.02, raio * 0.62 + 0.02, Vector3(0.0, 0.0, 0.0), _material(Color("#ffe08a"), 0.35, 0.22, "metal"), "CoinRelevo")
            relevo.rotation.x = PI / 2.0
            _cylinder(parent, raio * 0.34, raio * 0.34, 0.075, Vector3.ZERO, _material(Color("#fff0b8"), 0.3, 0.20, "metal"), "CoinNucleo")
        "coffee":
            _cylinder(parent, 0.18, 0.15, 0.30, Vector3(0.0, 0.0, 0.0), mat, "CoffeeCup")
            _cylinder(parent, 0.14, 0.14, 0.018, Vector3(0.0, 0.16, 0.0), _material(Color("#33231f"), 0.0, 0.72, "paint"), "CoffeeSurface")
            var coffee_handle := _torus(parent, 0.10, 0.035, Vector3(0.18, 0.02, 0.0), _material(Color("#f3d8a0"), 0.0, 0.54, "paint"), "CoffeeHandle")
            coffee_handle.rotation.x = PI / 2.0
        "bread":
            var bread := _sphere(parent, 0.25, Vector3.ZERO, mat, "PaoDeQueijo")
            bread.scale = Vector3(1.35, 0.72, 0.90)
            _box(parent, Vector3(0.025, 0.16, 0.28), Vector3(-0.04, 0.20, -0.03), _material(Color("#fff0bd"), 0.0, 0.8, "paint"), "BreadScore")
        "pastel":
            var pastel := _sphere(parent, 0.27, Vector3.ZERO, mat, "Pastel")
            pastel.scale = Vector3(1.30, 0.55, 0.82)
            _cylinder(parent, 0.08, 0.08, 0.28, Vector3(0.0, 0.08, 0.0), _material(Color("#fff2b7"), 0.0, 0.72, "paint"), "PastelCrimp")
        "sugarcane":
            for side in [-1.0, 0.0, 1.0]:
                _cylinder(parent, 0.055, 0.07, 0.48, Vector3(side * 0.09, 0.0, 0.0), mat, "SugarcaneStem")
            _sphere(parent, 0.12, Vector3(0.0, 0.27, 0.0), _material(Color("#95dc70"), 0.0, 0.72, "leaves"), "SugarcaneLeaf")
        "pass":
            _box(parent, Vector3(0.46, 0.28, 0.06), Vector3.ZERO, mat, "TransportPass")
            _box(parent, Vector3(0.32, 0.035, 0.012), Vector3(0.0, 0.0, -0.04), _material(Color("#2f7da5"), 0.0, 0.42, "paint"), "PassStripe")
        "coxinha":
            _cone(parent, 0.24, 0.42, Vector3(0.0, 0.0, 0.0), mat, "Coxinha")
            var coxinha_top := _sphere(parent, 0.09, Vector3(0.0, 0.21, 0.0), _material(Color("#f5c368"), 0.0, 0.72, "paint"), "CoxinhaTop")
            coxinha_top.scale = Vector3(1.25, 0.55, 1.25)
        "guarana":
            _cylinder(parent, 0.11, 0.14, 0.40, Vector3(0.0, 0.0, 0.0), mat, "GuaranaBottle")
            _cylinder(parent, 0.05, 0.05, 0.12, Vector3(0.0, 0.26, 0.0), _material(Color("#e4e8d6"), 0.0, 0.32, "metal"), "GuaranaCap")
            _box(parent, Vector3(0.18, 0.12, 0.015), Vector3(0.0, 0.0, -0.14), _material(Color("#fff1b0"), 0.0, 0.56, "paint"), "GuaranaLabel")
        "pix":
            _box(parent, Vector3(0.38, 0.58, 0.06), Vector3(0.0, 0.0, 0.0), mat, "PixPhone")
            _box(parent, Vector3(0.26, 0.34, 0.015), Vector3(0.0, 0.02, -0.04), _material(Color("#102e43"), 0.0, 0.26, "glass"), "PixScreen")
        "umbrella":
            _cylinder(parent, 0.025, 0.025, 0.60, Vector3(0.0, -0.10, 0.0), _material(Color("#303e52"), 0.55, 0.45, "metal"), "UmbrellaStem")
            var canopy := _sphere(parent, 0.30, Vector3(0.0, 0.18, 0.0), mat, "UmbrellaCanopy")
            canopy.scale = Vector3(1.28, 0.38, 1.28)
        _:
            _sphere(parent, 0.22, Vector3.ZERO, mat, "Bonus")
    var glow_material := _material(Color(color, 0.10), 0.0, 0.8, "glass")
    glow_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    _sphere(parent, 0.14, Vector3.ZERO, glow_material, "Glow") # 0.14 proporcional

func _wheels(parent: Node3D, material: Material, x_offset: float, z_offset: float) -> void:
    for x in [-x_offset, x_offset]:
        var front := _cylinder(parent, 0.30, 0.30, 0.18, Vector3(x, 0.18, -z_offset), material, "Wheel")
        var rear := _cylinder(parent, 0.30, 0.30, 0.18, Vector3(x, 0.18, z_offset), material, "Wheel")
        front.rotation.z = PI / 2.0
        rear.rotation.z = PI / 2.0

func _box(parent: Node3D, size: Vector3, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    var m := BoxMesh.new()
    m.size = size
    node.mesh = m
    node.material_override = material
    node.position = pos
    if parent == decor_root:
        node.visibility_range_end = 96.0
    parent.add_child(node)
    return node
func _find_mesh_instance(root: Node) -> MeshInstance3D:
    if root is MeshInstance3D:
        return root as MeshInstance3D
    for c in root.get_children():
        var r: MeshInstance3D = _find_mesh_instance(c)
        if r != null:
            return r
    return null

func _sphere(parent: Node3D, radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    var m := SphereMesh.new()
    m.radius = radius
    m.height = radius * 2.0
    node.mesh = m
    node.material_override = material
    node.position = pos
    if parent == decor_root:
        node.visibility_range_end = 96.0
    parent.add_child(node)
    return node

func _capsule(parent: Node3D, radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    var m := CapsuleMesh.new()
    m.radius = radius
    m.height = height
    node.mesh = m
    node.material_override = material
    node.position = pos
    if parent == decor_root:
        node.visibility_range_end = 96.0
    parent.add_child(node)
    return node

func _cylinder(parent: Node3D, top_radius: float, bottom_radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    var m := CylinderMesh.new()
    m.top_radius = top_radius
    m.bottom_radius = bottom_radius
    m.height = height
    node.mesh = m
    node.material_override = material
    node.position = pos
    if parent == decor_root:
        node.visibility_range_end = 96.0
    parent.add_child(node)
    return node

func _cone(parent: Node3D, radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    return _cylinder(parent, 0.03, radius, height, pos, material, node_name)

func _torus(parent: Node3D, inner_radius: float, outer_radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    var m := TorusMesh.new()
    m.inner_radius = inner_radius
    m.outer_radius = outer_radius
    node.mesh = m
    node.material_override = material
    node.position = pos
    if parent == decor_root:
        node.visibility_range_end = 96.0
    parent.add_child(node)
    return node

func _ellipse_mesh(parent: Node3D, pos: Vector3, object_scale: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var node := _sphere(parent, 1.0, pos, material, node_name)
    node.scale = object_scale
    return node

func _material(color: Color, metallic: float, roughness: float, surface: String = "paint") -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    var base_color: Color = color
    if surface == "asphalt":
        base_color = color.lerp(Color.WHITE, 0.52)
    elif surface in ["sidewalk", "cobble"]:
        base_color = color.lerp(Color.WHITE, 0.22)
    elif surface == "denim":
        base_color = color.lerp(Color.WHITE, 0.18)
    elif surface == "vehicle_paint":
        base_color = color.lerp(Color.WHITE, 0.26)
    material.albedo_color = Color(base_color, 0.78) if surface == "glass" else base_color
    material.metallic = maxf(metallic, 0.42) if surface == "metal" else (maxf(metallic, 0.85) if surface == "chrome" else metallic)
    material.roughness = roughness
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    if surface == "glass":
        material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        material.refraction_enabled = true
        material.refraction_scale = 0.06
        material.clearcoat_enabled = true
        material.clearcoat = 0.85
        material.clearcoat_roughness = 0.08
    elif surface == "vehicle_paint":
        material.clearcoat_enabled = true
        material.clearcoat = 0.65
        material.clearcoat_roughness = 0.12
        material.rim_enabled = true
        material.rim = 0.18
        material.rim_tint = 0.45
    elif surface == "skin":
        material.subsurf_scatter_enabled = true
        material.subsurf_scatter_skin_mode = true
        material.subsurf_scatter_strength = 0.12
        material.rim_enabled = true
        material.rim = 0.08
        material.rim_tint = 0.72
    elif surface == "hair":
        material.anisotropy_enabled = true
        material.anisotropy = 0.24
        material.rim_enabled = true
        material.rim = 0.16
        material.rim_tint = 0.72
    var texture: Texture2D = _texture_for_surface(surface)
    material.albedo_texture = texture
    material.uv1_scale = _texture_scale(surface)
    if surface in ["asphalt", "dirt", "sidewalk", "cobble"]:
        material.uv1_triplanar = true
        material.uv1_world_triplanar = true
        material.uv1_triplanar_sharpness = 3.0
    var normal: Texture2D = _normal_for_surface(surface)
    if normal != null:
        material.normal_enabled = true
        material.normal_texture = normal
        material.normal_scale = 0.32 if surface == "asphalt" else 0.42
        if surface.begins_with("facade_") or surface == "brick_wall":
            material.normal_scale = 0.85
        elif surface == "vehicle_paint":
            material.normal_scale = 0.25
        elif surface == "chrome":
            material.normal_scale = 0.15
        elif surface in ["leaves", "fabric"]:
            material.normal_scale = 0.6
        elif surface in ["wood", "concrete", "stucco"]:
            material.normal_scale = 0.55
        elif surface in ["metal", "dirt"]:
            material.normal_scale = 0.45
        elif surface == "rubber":
            material.normal_scale = 0.3
        elif surface == "skin":
            material.normal_scale = 0.2
        elif surface == "sidewalk":
            material.normal_scale = 0.82
        elif surface == "cobble":
            material.normal_scale = 0.92
        elif surface == "asphalt":
            material.normal_scale = 0.72
    var rough_map: Texture2D = _roughness_for_surface(surface)
    if rough_map != null:
        material.roughness_texture = rough_map
        material.roughness = 1.0
    elif surface in ["asphalt", "sidewalk", "cobble"]:
        material.roughness = maxf(material.roughness, 0.82)
    return material

func _texture_for_surface(surface: String) -> Texture2D:
    match surface:
        "asphalt":
            return TEXTURE_ASPHALT_REAL
        "dirt":
            return TEXTURE_DIRT_REAL
        "sidewalk":
            return TEXTURE_SIDEWALK_REAL
        "concrete":
            return TEXTURE_CONCRETE_REAL
        "cobble":
            return TEXTURE_SIDEWALK_REAL
        "brick":
            return TEXTURE_BRICK_WALL
        "stucco":
            return TEXTURE_CONCRETE_REAL
        "metal":
            return TEXTURE_METAL_REAL
        "chrome":
            return null
        "glass":
            return TEXTURE_GLASS
        "fabric":
            return TEXTURE_FABRIC_REAL
        "denim":
            return TEXTURE_DENIM_REAL
        "vehicle_paint":
            return TEXTURE_CAR_PAINT_REAL
        "skin":
            return TEXTURE_SKIN_REAL
        "hair":
            return TEXTURE_HAIR_REAL
        "leaves":
            return TEXTURE_LEAVES_REAL
        "wood":
            return TEXTURE_WOOD_REAL
        "rubber":
            return TEXTURE_RUBBER_REAL
        _:
            return TEXTURE_PAINT

func _normal_for_surface(surface: String) -> Texture2D:
    match surface:
        "asphalt":
            return TEXTURE_ASPHALT_NORMAL
        "sidewalk", "cobble":
            return TEXTURE_SIDEWALK_NORMAL
        "facade_plaster":
            return TEXTURE_FACADE_PLASTER_N
        "facade_brick":
            return TEXTURE_FACADE_BRICK_N
        "brick_wall":
            return TEXTURE_BRICK_WALL_N
        "vehicle_paint":
            return TEXTURE_CAR_PAINT_NORMAL
        "chrome":
            return TEXTURE_CAR_PAINT_NORMAL
        "leaves":
            return TEXTURE_LEAVES_REAL_N
        "wood":
            return TEXTURE_WOOD_REAL_N
        "metal":
            return TEXTURE_METAL_REAL_N
        "concrete", "stucco":
            return TEXTURE_CONCRETE_REAL_N
        "dirt":
            return TEXTURE_DIRT_REAL_N
        "fabric":
            return TEXTURE_FABRIC_REAL_N
        "rubber":
            return TEXTURE_RUBBER_REAL_N
        "skin":
            return TEXTURE_SKIN_REAL_N
        _:
            return null

func _roughness_for_surface(surface: String) -> Texture2D:
    match surface:
        "asphalt":
            return TEXTURE_ASPHALT_ROUGH
        "sidewalk", "cobble":
            return TEXTURE_SIDEWALK_ROUGH
        "facade_plaster":
            return TEXTURE_FACADE_PLASTER_R
        "facade_brick":
            return TEXTURE_FACADE_BRICK_R
        "brick_wall":
            return TEXTURE_BRICK_WALL_R
        "leaves":
            return TEXTURE_LEAVES_REAL_R
        "wood":
            return TEXTURE_WOOD_REAL_R
        "metal":
            return TEXTURE_METAL_REAL_R
        "concrete", "stucco":
            return TEXTURE_CONCRETE_REAL_R
        "dirt":
            return TEXTURE_DIRT_REAL_R
        "fabric":
            return TEXTURE_FABRIC_REAL_R
        "rubber":
            return TEXTURE_RUBBER_REAL_R
        "skin":
            return TEXTURE_SKIN_REAL_R
        _:
            return null

func _texture_scale(surface: String) -> Vector3:
    match surface:
        "skin":
            return Vector3(1.5, 1.5, 1.5)
        "fabric", "denim", "vehicle_paint", "metal", "chrome", "glass":
            return Vector3(2.0, 2.0, 2.0)
        "hair":
            return Vector3(3.0, 3.0, 3.0)
        "asphalt":
            return Vector3(5.0, 5.0, 5.0)
        "sidewalk", "cobble":
            return Vector3(3.0, 3.0, 3.0)
        "dirt":
            return Vector3(4.0, 4.0, 4.0)
        "leaves":
            return Vector3(2.5, 2.5, 2.5)
        "wood":
            return Vector3(1.5, 1.5, 1.5)
        "concrete", "stucco":
            return Vector3(2.0, 2.0, 2.0)
        "rubber":
            return Vector3(3.0, 3.0, 3.0)
        "facade_plaster", "facade_brick":
            return Vector3.ONE
        "brick_wall":
            return Vector3(2.0, 1.0, 1.0)
        _:
            return Vector3(2.5, 2.5, 2.5)

func _sync_hud() -> void:
    if hud == null:
        return
    # Lote 11: garante banner correto sempre que HUD sinc (evita esquecer transição)
    _update_banner_visibility()
    var cards: Array[Dictionary] = []
    if screen == 1:
        var first_phase: int = map_page * 10
        for local_index in 10:
            var absolute_index := first_phase + local_index
            var phase_data: Dictionary = PhaseData.get_phase(absolute_index)
            cards.append({
                "index": absolute_index,
                "name": str(phase_data["name"]),
                "location": str(phase_data["location"]),
                "scenario": SCENARIO_DATA.chapter_name(absolute_index),
                "accent": phase_data["accent"],
                "difficulty": int(phase_data["difficulty"]),
                "stars": GameSave.phase_stars(absolute_index),
                "unlocked": GameSave.is_phase_unlocked(absolute_index)
            })
    var characters: Array[Dictionary] = []
    var equipped_character: String = CHARACTER_DATA.canonical_id(GameSave.equipped_character())
    for character in CHARACTER_DATA.all():
        var character_card: Dictionary = character.duplicate(true)
        character_card["owned"] = GameSave.owns(str(character.get("id", "")))
        character_card["equipped"] = str(character.get("id", "")) == equipped_character
        characters.append(character_card)
    var items: Array[Dictionary] = SHOP_DATA.item_catalog()
    for item in items:
        item["owned"] = GameSave.owns(str(item.get("id", "")))
    var achievement_catalog: Array[Dictionary] = [
        {"id": "busao", "name": "Peguei o busão!", "description": "Conclua o capítulo 1", "kind": "achievement"},
        {"id": "enchente", "name": "Chuva sem susto", "description": "Passe a fase 9 sem dano", "kind": "achievement"},
        {"id": "dog", "name": "Cachorro caramelo", "description": "Aguente 10 encontros", "kind": "achievement"},
        {"id": "busao50", "name": "Brasil sem freio", "description": "Conclua as 50 fases", "kind": "achievement"},
        {"id": "capitulo1", "name": "Primeiro terminal", "description": "Badge de capítulo", "kind": "badge"},
        {"id": "combo15", "name": "Combo de respeito", "description": "Chegue ao combo 15", "kind": "badge"},
        {"id": "sem_arranhao", "name": "Sem arranhão", "description": "Conclua sem sofrer dano", "kind": "badge"},
        {"id": "maratonista", "name": "Maratonista", "description": "Liberte o Endless", "kind": "badge"}
    ]
    for achievement in achievement_catalog:
        var id := str(achievement["id"])
        achievement["unlocked"] = GameSave.has_achievement(id) or id in GameSave.data.get("badges", [])
    var date_key := Time.get_date_string_from_system()
    var week_key := GameSave.weekly_key()
    var daily_progress: Dictionary = GameSave.daily_progress(date_key)
    var weekly_progress: Dictionary = GameSave.weekly_progress(week_key)
    var next_unlock_stars := 0
    if not GameSave.is_phase_unlocked(BALANCE.chapter_unlock_phase):
        next_unlock_stars = BALANCE.unlock_chapter_stars
    elif not GameSave.is_phase_unlocked(BALANCE.endless_unlock_phase):
        next_unlock_stars = BALANCE.unlock_endless_stars
    var state: Dictionary = {
        "screen": screen,
        "coins": GameSave.coins(),
        "xp": GameSave.xp(),
        "xp_level": GameSave.xp_level(),
        "xp_into_level": GameSave.xp_into_level(),
        "xp_to_next_level": GameSave.xp_to_next_level(),
        "stars": GameSave.total_stars(),
        "streak": int(GameSave.data.get("daily_streak", 0)),
        "retention_flags": GameSave.retention_flags(),
        "reduced_motion": bool(GameSave.data.get("reduced_motion", false)),
        "high_contrast": bool(GameSave.data.get("high_contrast", false)),
        "phase_index": phase_index,
        "phase_name": str(phase.get("name", "Corre")),
        "location": str(phase.get("location", "Brasil")),
        "phase_accent": phase.get("accent", YELLOW),
        "distance": distance,
        "run_total": run_total,
        "hearts": hearts,
        "max_hearts": max_hearts,
        "combo": combo,
        "coins_run": collected_coins,
        "dash_cooldown": dash_cooldown,
        "run_mode": run_mode,
        "stop_wait": stop_wait,
        "stop_wait_total": stop_wait_total,
        "endless": endless_mode,
        "map_page": map_page,
        "cards": cards,
        "result": result,
        "shop_tab": shop_tab,
        "shop_scroll": shop_scroll,
        "shop_scroll_max": _shop_scroll_max(),
        "daily_progress": daily_progress,
        "daily_completed": GameSave.get_daily_completed(),
        "daily_targets": {"meters": BALANCE.daily_distance_target, "coins": BALANCE.daily_coin_target},
        "weekly_progress": weekly_progress,
        "weekly_claimed": GameSave.weekly_claimed(week_key),
        "weekly_key": week_key,
        "weekly_target": BALANCE.weekly_distance_target,
        "next_unlock_stars": next_unlock_stars,
        "achievement_catalog": achievement_catalog,
        "items": items,
        "feedback_title": feedback_title,
        "feedback_detail": feedback_detail,
        "feedback_color": feedback_color,
        "tutorial_hint": tutorial_hint,
        "first_session_hint_distance": BALANCE.first_session_hint_distance,
        "scenario_label": str(scenario.get("label", "Brasil")),
        "scenario_chapter": str(scenario.get("chapter", "Rua brasileira")),
        "scenario_weather": str(scenario.get("weather", "sol")),
        "characters": characters,
        "equipped_character": equipped_character,
        "banner_visible": (get_node_or_null("/root/AdsManager").is_banner_visible() if get_node_or_null("/root/AdsManager") and get_node_or_null("/root/AdsManager").has_method("is_banner_visible") else false),
        "remove_ads": bool(GameSave.data.get("remove_ads", false)),
        "rewarded_ready": (get_node_or_null("/root/AdsManager").is_rewarded_ready() if get_node_or_null("/root/AdsManager") and get_node_or_null("/root/AdsManager").has_method("is_rewarded_ready") else false),
        "revive_available": (not _revive_used and not bool(result.get("success", true)) and screen == 3),
        "double_available": (not _double_used and bool(result.get("success", false)) and screen == 3 and int(result.get("reward", 0)) > 0),
        "billing_packs": (get_node_or_null("/root/BillingManager").get_products() if get_node_or_null("/root/BillingManager") and get_node_or_null("/root/BillingManager").has_method("get_products") else SHOP_DATA.BILLING_PACKS),
        "rubi": (get_node_or_null("/root/EconomyManager").get_rubi() if get_node_or_null("/root/EconomyManager") and get_node_or_null("/root/EconomyManager").has_method("get_rubi") else int(GameSave.data.get("hard_currency", 0))),
        "daily_chest": (get_node_or_null("/root/EconomyManager").get_daily_chest_status() if get_node_or_null("/root/EconomyManager") and get_node_or_null("/root/EconomyManager").has_method("get_daily_chest_status") else {}),
        "weekly_event": (get_node_or_null("/root/EconomyManager").get_weekly_event() if get_node_or_null("/root/EconomyManager") and get_node_or_null("/root/EconomyManager").has_method("get_weekly_event") else {}),
        "featured_item": (get_node_or_null("/root/EconomyManager").get_featured_item() if get_node_or_null("/root/EconomyManager") and get_node_or_null("/root/EconomyManager").has_method("get_featured_item") else {})
    }
    hud.call("set_state", state)

func _handle_key(event: InputEventKey) -> void:
    if event.keycode == KEY_ESCAPE:
        if _capture_mode:
            _capture_mode = false
            _show_feedback("CAPTURA OFF", "Voltando à corrida", BLUE, "ui_back")
            return
        if screen == 2:
            run_mode = "playing" if run_mode != "playing" else "paused"
            _show_feedback("PAUSA" if run_mode == "paused" else "VAMOS!", "Leia as três faixas", YELLOW if run_mode == "paused" else GREEN, "click")
        elif screen != 0:
            screen = 0
            _show_feedback("MENU", "Escolha o próximo corre", BLUE, "ui_back")
        return
    if event.keycode == KEY_C:
        _toggle_capture_mode()
        return
    if event.keycode == KEY_P and _capture_mode:
        _capture_screenshot()
        return
    if event.keycode == KEY_F10:
        _capture_screenshot()
        return
    if event.keycode == KEY_M:
        AudioManager.toggle_mute()
        _show_feedback("SOM DESLIGADO" if AudioManager.muted else "SOM LIGADO", "Você escolhe o feedback", BLUE, "ui_confirm")
        return
    if event.keycode == KEY_F8:
        physics_realista_enabled = not physics_realista_enabled
        _show_feedback("FISICA REALISTA " + ("ON" if physics_realista_enabled else "OFF"), "Gravidade 9.81 • Impulso 6.3 • Dash 900 N·s" if physics_realista_enabled else "Arcade lerp/sin", YELLOW if physics_realista_enabled else BLUE, "ui_confirm")
        return
    if event.keycode == KEY_F9:
        lighting_realista_enabled = not lighting_realista_enabled
        if LIGHTING_HANDLER != null and environment != null and sun != null:
            LIGHTING_HANDLER.setup_realista(environment, sun, world_root, lighting_realista_enabled)
        _show_feedback("LUZ REALISTA " + ("ON" if lighting_realista_enabled else "OFF"), "SDFGI+VoxelGI+4096 VSM+SSAO 0.4" if lighting_realista_enabled else "Panorama 1024", YELLOW if lighting_realista_enabled else BLUE, "ui_confirm")
        return
    if screen == 2:
        if event.is_action_pressed("move_left") or event.keycode == KEY_LEFT:
            _change_lane(-1)
        elif event.is_action_pressed("move_right") or event.keycode == KEY_RIGHT:
            _change_lane(1)
        elif event.is_action_pressed("jump") or event.keycode == KEY_UP or event.keycode == KEY_W or event.keycode == KEY_SPACE:
            _jump()
        elif event.is_action_pressed("slide") or event.keycode == KEY_DOWN or event.keycode == KEY_S:
            _slide()
        elif event.is_action_pressed("dash") or event.keycode == KEY_X:
            _dash()
        elif event.keycode == KEY_ENTER and run_mode == "at_stop":
            _catch_bus()
    elif event.keycode == KEY_ENTER or event.keycode == KEY_SPACE:
        if screen == 0:
            _start_run(0)
        elif screen == 1:
            _start_run(selected_phase)
        elif screen == 3:
            _start_run(phase_index)

func _input(event: InputEvent) -> void:
    if _capture_mode and event is InputEventMouseMotion:
        if event.button_mask & MOUSE_BUTTON_MASK_LEFT:
            _capture_yaw -= event.relative.x * 0.005
            _capture_pitch = clampf(_capture_pitch - event.relative.y * 0.005, -0.80, 0.62)
        return
    if event is InputEventKey and event.pressed and not event.echo:
        _handle_key(event)
        return
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        if event.pressed:
            pointer_active = true
            touch_start = event.position
            touch_started_at = Time.get_ticks_msec()
        elif pointer_active:
            pointer_active = false
            _handle_pointer_release(event.position, Time.get_ticks_msec() - touch_started_at)
        return
    if event is InputEventScreenTouch:
        if event.pressed:
            pointer_active = true
            touch_start = event.position
            touch_started_at = Time.get_ticks_msec()
        elif pointer_active:
            pointer_active = false
            _handle_pointer_release(event.position, Time.get_ticks_msec() - touch_started_at)

func _handle_pointer_release(pos: Vector2, duration_ms: int) -> void:
    var delta := pos - touch_start
    if screen == 2 and run_mode == "playing" and delta.length() > 42.0:
        if absf(delta.x) > absf(delta.y):
            _change_lane(1 if delta.x > 0.0 else -1)
        elif delta.y < 0.0:
            _jump()
        else:
            _slide()
        return
    if screen == 2 and run_mode == "playing" and duration_ms < 360 and delta.length() < 35.0 and not Rect2(620, 36, 72, 58).has_point(pos):
        _dash()
        return
    if screen == 4 and shop_tab == 0 and absf(delta.y) > absf(delta.x) and absf(delta.y) > 24.0:
        shop_scroll = clampf(shop_scroll - delta.y, 0.0, _shop_scroll_max())
        return
    _handle_tap(pos)

func _shop_scroll_max() -> float:
    if shop_tab != 0:
        return 0.0
    var rows: float = ceilf(float(CHARACTER_DATA.all().size()) / 2.0)
    var content_bottom: float = 280.0 + (rows - 1.0) * 145.0 + 126.0
    return maxf(0.0, content_bottom - 1125.0)

func _handle_tap(pos: Vector2) -> void:
    if screen == 0:
        if Rect2(510, 132, 156, 46).has_point(pos):
            AudioManager.toggle_mute()
            _show_feedback("SOM DESLIGADO" if AudioManager.muted else "SOM LIGADO", "Você escolhe o feedback", BLUE, "ui_confirm")
        elif Rect2(420, 190, 118, 38).has_point(pos):
            var reduced_motion := not bool(GameSave.data.get("reduced_motion", false))
            GameSave.set_preference("reduced_motion", reduced_motion)
            _show_feedback("MOVIMENTO REDUZIDO" if reduced_motion else "MOVIMENTO COMPLETO", "Dash e câmera respeitam sua escolha", CYAN, "ui_confirm")
        elif Rect2(544, 190, 122, 38).has_point(pos):
            var high_contrast := not bool(GameSave.data.get("high_contrast", false))
            GameSave.set_preference("high_contrast", high_contrast)
            _show_feedback("ALTO CONTRASTE" if high_contrast else "CONTRASTE PADRÃO", "Leitura sem depender só de cor", YELLOW, "ui_confirm")
        elif Rect2(70, 564, 580, 104).has_point(pos):
            _start_run(0)
        elif Rect2(70, 700, 275, 82).has_point(pos):
            screen = 1
            _show_feedback("MAPA ABERTO", "Escolha seu próximo corre", BLUE, "ui_confirm")
        elif Rect2(375, 700, 275, 82).has_point(pos):
            screen = 4
            _show_feedback("LOJA DO PONTO", "Seu estilo, suas regras", RED, "ui_confirm")
        elif Rect2(70, 808, 275, 82).has_point(pos):
            screen = 5
            _show_feedback("CONQUISTAS", "Cada corre deixa uma história", VIOLET, "ui_confirm")
        elif Rect2(375, 808, 275, 82).has_point(pos):
            screen = 6
            _show_feedback("DESAFIOS", "Recompensas esperando", GREEN, "ui_confirm")
        elif Rect2(470, 885, 110, 34).has_point(pos):
            if has_node("/root/LocaleManager"):
                var _lm_lang = get_node_or_null("/root/LocaleManager")
                if _lm_lang and _lm_lang.has_method("toggle"):
                    var _nl: String = _lm_lang.call("toggle")
                    _show_feedback("IDIOMA " + _nl.to_upper(), "Tradução aplicada", BLUE, "ui_confirm")
                    _sync_hud()
        elif Rect2(70, 930, 580, 80).has_point(pos):
            screen = 7
            previous_screen = 0
            _show_feedback("GUIA RÁPIDO", "Aprenda. Corra. Pegue o busão.", YELLOW, "ui_confirm")
    elif screen == 1:
        if Rect2(25, 1080, 155, 72).has_point(pos):
            screen = 0
            _show_feedback("MENU", "O ponto continua te esperando", BLUE, "ui_back")
        elif Rect2(190, 1080, 155, 72).has_point(pos):
            map_page = maxi(0, map_page - 1)
            _show_feedback("CAPÍTULO ANTERIOR", "Revisitando o corre", BLUE, "whoosh")
        elif Rect2(355, 1080, 155, 72).has_point(pos):
            map_page = mini(4, map_page + 1)
            _show_feedback("NOVO CAPÍTULO", "Mais caos, mais recompensa", GOLD, "whoosh")
        elif GameSave.data.get("endless_unlocked", false) and Rect2(520, 1080, 175, 72).has_point(pos):
            _start_endless()
        else:
            var hit: int = _phase_at_position(pos)
            if hit >= 0:
                _start_run(hit)
    elif screen == 2:
        if Rect2(610, 15, 95, 75).has_point(pos):
            run_mode = "playing" if run_mode == "paused" else "paused"
            _show_feedback("PAUSA" if run_mode == "paused" else "VAMOS!", "Controle seu ritmo", YELLOW if run_mode == "paused" else GREEN, "click")
        elif run_mode == "paused" and Rect2(70, 580, 580, 150).has_point(pos):
            run_mode = "playing"
            _show_feedback("VAMOS!", "O próximo obstáculo é seu", GREEN, "ui_confirm")
        elif run_mode == "at_stop" and Rect2(70, 800, 580, 130).has_point(pos):
            _catch_bus()
    elif screen == 3:
        # Lote 11: rewarded buttons têm prioridade sobre navegação
        var rewarded_ready: bool = false
        var ads_node := get_node_or_null("/root/AdsManager")
        if ads_node and ads_node.has_method("is_rewarded_ready"):
            rewarded_ready = ads_node.is_rewarded_ready()
        var is_fail: bool = not bool(result.get("success", false))
        if is_fail and not _revive_used and Rect2(55, 600, 610, 72).has_point(pos):
            if not rewarded_ready:
                _show_feedback("CARREGANDO ANÚNCIO", "Tente em segundos", MUTED, "ui_back")
            else:
                _rewarded_pending_placement = "rewarded_revive"
                var ok: bool = ads_node.show_rewarded("rewarded_revive") if ads_node and ads_node.has_method("show_rewarded") else false
                if not ok:
                    _show_feedback("ANÚNCIO INDISPONÍVEL", "Tente novamente", RED, "ui_back")
                else:
                    _show_feedback("ANÚNCIO...", "Assista para reviver", CYAN, "ui_confirm")
            return
        var is_success: bool = bool(result.get("success", false))
        if is_success and not _double_used and int(result.get("reward",0))>0 and Rect2(55, 760, 610, 72).has_point(pos):
            if not rewarded_ready:
                _show_feedback("CARREGANDO ANÚNCIO", "Tente em segundos", MUTED, "ui_back")
            else:
                _rewarded_pending_placement = "rewarded_double"
                var ok2: bool = ads_node.show_rewarded("rewarded_double") if ads_node and ads_node.has_method("show_rewarded") else false
                if not ok2:
                    _show_feedback("ANÚNCIO INDISPONÍVEL", "Tente novamente", RED, "ui_back")
                else:
                    _show_feedback("ANÚNCIO...", "Dobre suas moedas!", GOLD, "ui_confirm")
            return
        if Rect2(55, 880, 290, 88).has_point(pos):
            screen = 1
            _update_banner_visibility()
            _show_feedback("MAPA", "Escolha o próximo capítulo", BLUE, "ui_back")
        elif Rect2(375, 880, 290, 88).has_point(pos):
            if result.get("success", false) and result.get("endless", false):
                _start_endless()
            elif result.get("success", false) and phase_index < BALANCE.phase_count - 1 and GameSave.is_phase_unlocked(phase_index + 1):
                _start_run(phase_index + 1)
            else:
                _start_run(phase_index)
        elif Rect2(55, 1000, 610, 72).has_point(pos) or Rect2(55, 1090, 610, 72).has_point(pos):
            screen = 0
            _update_banner_visibility()
            _show_feedback("ATÉ A PRÓXIMA", "O busão sempre volta", BLUE, "ui_back")
    elif screen == 4:
        if Rect2(45, 1135, 630, 70).has_point(pos):
            screen = 0
            _update_banner_visibility()
            _show_feedback("DE VOLTA", "Seu estilo ficou salvo", BLUE, "ui_back")
        elif Rect2(30, 230, 330, 36).has_point(pos):
            # Botão remover anúncios
            if bool(GameSave.data.get("remove_ads", false)):
                _show_feedback("JÁ SEM ANÚNCIOS", "Obrigado pelo apoio!", GREEN, "ui_confirm")
            else:
                var billing2 := get_node_or_null("/root/BillingManager")
                if billing2 and billing2.has_method("purchase"):
                    billing2.purchase("remove_ads")
                    _show_feedback("PROCESSANDO...", "Play Billing • R$ 9,90", MUTED, "ui_confirm")
                else:
                    _show_feedback("LOJA INDISPONÍVEL", "Billing não inicializado", RED, "ui_back")
        elif Rect2(545, 230, 135, 36).has_point(pos):
            var billing3 := get_node_or_null("/root/BillingManager")
            if billing3 and billing3.has_method("restore_purchases"):
                billing3.restore_purchases()
                _show_feedback("RESTAURANDO...", "Verificando compras", MUTED, "ui_confirm")
            else:
                _show_feedback("SEM COMPRAS", "Nada a restaurar no editor", MUTED, "ui_back")
        elif Rect2(30, 150, 660, 70).has_point(pos):
            # 3 abas
            if pos.x < 240.0:
                shop_tab = 0
            elif pos.x < 460.0:
                shop_tab = 1
            else:
                shop_tab = 2
            shop_scroll = 0.0
            _show_feedback("CATÁLOGO ATUALIZADO", "Toque para equipar/comprar", RED, "ui_confirm")
        else:
            _shop_tap(pos)
        _sync_hud()
    elif screen == 6:
        # Lote 17: baú diário (EconomyManager) tem prioridade sobre missões
        if Rect2(505, 995, 145, 58).has_point(pos) or Rect2(35, 970, 650, 110).has_point(pos):
            var _em_daily2 = get_node_or_null("/root/EconomyManager") if has_node("/root/EconomyManager") else null
            if _em_daily2 and _em_daily2.has_method("claim_daily_chest"):
                var _rew2: Dictionary = _em_daily2.call("claim_daily_chest")
                if not _rew2.is_empty():
                    _show_feedback("BAÚ ABERTO!", "+%d R$ +%d Rubi" % [int(_rew2.get("soft",0)), int(_rew2.get("hard",0))], GOLD, "reward")
                    _sync_hud()
                else:
                    _show_feedback("BAÚ JÁ ABERTO", "Volte amanhã", MUTED, "ui_back")
            return
        if Rect2(45, 1110, 630, 70).has_point(pos):
            screen = 0
            _show_feedback("DE VOLTA", "Seu progresso está seguro", BLUE, "ui_back")
        else:
            _claim_daily(_daily_at_position(pos))
    elif screen == 5 or screen == 7:
        if Rect2(45, 1110, 630, 70).has_point(pos):
            screen = previous_screen if previous_screen not in [5, 7] else 0
            _show_feedback("DE VOLTA", "Seu progresso está seguro", BLUE, "ui_back")

func _phase_at_position(pos: Vector2) -> int:
    var origin_y: float = 160.0
    var first_phase: int = map_page * 10
    for local_index in 10:
        var col: int = local_index % 2
        var row: int = int(float(local_index) / 2.0)
        var rect := Rect2(25.0 + col * 340.0, origin_y + row * 170.0, 330.0, 140.0)
        if rect.has_point(pos):
            return first_phase + local_index
    return -1

func _daily_at_position(pos: Vector2) -> int:
    for i in 3:
        if Rect2(35, 200 + i * 190, 650, 145).has_point(pos):
            return i
    if Rect2(35, 800, 650, 145).has_point(pos):
        return -2
    return -1

func _shop_tap(pos: Vector2) -> void:
    var chars: Array[Dictionary] = CHARACTER_DATA.all()
    var items: Array[Dictionary] = SHOP_DATA.item_catalog()
    # Lote 17: sinks no topo da loja personagens (reroll 40 R$ e skin 80 Rubi) — áreas fixas
    if shop_tab == 0 and Rect2(500, 240, 140, 28).has_point(pos):
        var _em_r = get_node_or_null("/root/EconomyManager") if has_node("/root/EconomyManager") else null
        if _em_r and _em_r.has_method("reroll_moto_color"):
            var _ok: bool = _em_r.call("reroll_moto_color")
            if _ok:
                _show_feedback("COR RERROLADA!", "-40 R$ • nova cor salva", CYAN, "reward")
                _sync_hud()
            else:
                _show_feedback("SEM MOEDAS", "Precisa 40 R$", RED, "ui_back")
        return
    if shop_tab == 0 and Rect2(500, 272, 140, 28).has_point(pos):
        var _em_s = get_node_or_null("/root/EconomyManager") if has_node("/root/EconomyManager") else null
        if _em_s and _em_s.has_method("buy_extra_skin"):
            var _skins: Array[String] = ["vermelha", "dourada", "neon"]
            var _handled: bool = false
            for _sk in _skins:
                if not _em_s.call("owns_extra_skin", _sk):
                    var _ok2: bool = _em_s.call("buy_extra_skin", _sk)
                    if _ok2:
                        _show_feedback("SKIN EXTRA!", "+%s • -80 Rubi" % _sk.to_upper(), Color("#ff7ab8"), "reward")
                        _sync_hud()
                    else:
                        _show_feedback("SEM RUBI", "Precisa 80 Rubi", RED, "ui_back")
                    _handled = true
                    break
            if not _handled:
                _show_feedback("TODAS AS SKINS", "Você já tem todas", GREEN, "ui_confirm")
        return
    if shop_tab == 0:
        var local_pos := Vector2(pos.x, pos.y + shop_scroll)
        for i in chars.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var rect := Rect2(25 + col * 340, 280 + row * 145, 330, 126)
            if rect.has_point(local_pos):
                var id: String = str(chars[i].get("id", "ze"))
                var price: int = int(chars[i].get("price", 0))
                if GameSave.owns(id):
                    GameSave.equip_character(id)
                    _rebuild_player_visual(id)
                    _show_feedback("EQUIPADO!", str(chars[i].get("name", id)), RED, "ui_confirm")
                elif GameSave.unlock(id, price):
                    GameSave.equip_character(id)
                    _rebuild_player_visual(id)
                    _show_feedback("DESBLOQUEADO!", str(chars[i].get("name", id)), GOLD, "reward")
                else:
                    _show_feedback("FALTAM MOEDAS", "Continue correndo", RED, "ui_back")
                return
    elif shop_tab == 1:
        for i in items.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var rect := Rect2(30 + col * 345, 280 + row * 175, 315, 150)
            if rect.has_point(pos):
                var id: String = str(items[i].get("id", ""))
                var price: int = int(items[i].get("price", SHOP_DATA.price_for(id)))
                var cosmetic := bool(items[i].get("cosmetic", false))
                if GameSave.owns(id):
                    _show_feedback("JÁ ADQUIRIDO", "cosmético • sem vantagem" if cosmetic else "efeito aplicado na próxima corrida", MUTED, "ui_back")
                elif GameSave.unlock(id, price):
                    _show_feedback("ITEM ADQUIRIDO!", id.to_upper(), GOLD, "reward")
                else:
                    _show_feedback("FALTAM MOEDAS", "Junte mais R$", RED, "ui_back")
                return
    else:
        # Pacotes de billing (Lote 12)
        var packs: Array[Dictionary] = SHOP_DATA.BILLING_PACKS
        # tenta buscar lista atualizada do manager se disponível
        var billing := get_node_or_null("/root/BillingManager")
        if billing and billing.has_method("get_products"):
            var live: Array[Dictionary] = billing.get_products()
            if not live.is_empty():
                packs = live
        for i in packs.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var rect := Rect2(30 + col * 345, 280 + row * 155, 315, 135)
            if rect.has_point(pos):
                var pid: String = str(packs[i].get("id",""))
                if pid == "remove_ads" and bool(GameSave.data.get("remove_ads", false)):
                    _show_feedback("JÁ SEM ANÚNCIOS", "Obrigado!", GREEN, "ui_confirm")
                    return
                if billing and billing.has_method("purchase"):
                    var ok: bool = billing.purchase(pid)
                    if ok:
                        _show_feedback("PROCESSANDO...", "%s • %s" % [pid, str(packs[i].get("price_label",""))], MUTED, "ui_confirm")
                    else:
                        _show_feedback("INDISPONÍVEL", pid, RED, "ui_back")
                else:
                    _show_feedback("LOJA INDISPONÍVEL", "Billing não inicializado", RED, "ui_back")
                return

func _claim_daily(index: int) -> void:
    if index == -2:
        var current_week := GameSave.weekly_key()
        if GameSave.weekly_claimed(current_week):
            _show_feedback("JÁ RESGATADO", "O marco volta na próxima semana", MUTED, "ui_back")
            return
        var weekly := GameSave.weekly_progress(current_week)
        if int(weekly.get("meters", 0)) < BALANCE.weekly_distance_target:
            _show_feedback("MARCO SEMANAL", "%dm restantes" % maxi(0, BALANCE.weekly_distance_target - int(weekly.get("meters", 0))), RED, "ui_back")
            return
        GameSave.set_weekly_claimed(current_week, BALANCE.weekly_reward)
        _show_feedback("MARCO COMPLETO!", "+R$ %d • semana garantida" % BALANCE.weekly_reward, GOLD, "reward")
        return
    if index < 0:
        return
    var key := Time.get_date_string_from_system()
    var completed: Array = GameSave.get_daily_completed()
    if str(GameSave.data.get("daily_date", "")) != key:
        completed = []
    if index in completed:
        _show_feedback("JÁ RESGATADO", "Volte amanhã", MUTED, "ui_back")
        return
    var progress: Dictionary = GameSave.daily_progress(key)
    var is_ready := (index == 0 and int(progress.get("meters", 0)) >= BALANCE.daily_distance_target) or (index == 1 and int(progress.get("coins", 0)) >= BALANCE.daily_coin_target) or (index == 2 and bool(progress.get("clean", false)))
    if not is_ready:
        _show_feedback("QUASE LÁ!", "Complete a missão primeiro", RED, "ui_back")
        return
    completed.append(index)
    var reward: int = BALANCE.daily_base_reward + index * BALANCE.daily_step_reward
    GameSave.set_daily_completed(completed, key, reward)
    _show_feedback("RECOMPENSA!", "+R$ %d • objetivo claro" % reward, GOLD, "reward")

# =============================================================================
# LOTES 2/3/4 — rodada visual (blocos de colagem dos pacotes lote2/lote3/lote4;
# contratos conferidos por verificar_lotes.py)
# =============================================================================

# --- Lote 2: perfil de clima/render + aplicação via autoload RenderQuality --
func _render_profile() -> Dictionary:
    # Lote 3, Colagem 4: o corpo do perfil do Lote 2 passa a vir do
    # world_spec.json — a mesma paleta que o BuildingKit usa no cenário.
    return _render_profile_world()


func _apply_render_quality() -> void:
    var rq := get_node_or_null(RQ_PATH)
    if rq == null:
        return
    rq.apply(_render_profile())


# --- Lote 3: rua ------------------------------------------------------------
func _setup_world_kit() -> void:
    if not WORLD_KIT_ATIVO or course_root == null:
        return
    var kit := BuildingKit.ChunkStreamer.new()
    kit.name = "CenarioRua"
    kit.position = Vector3(0.0, WORLD_Y_OFFSET, 0.0)
    kit.rotation.y = PI if WORLD_INVERTER else 0.0
    # Filho do course_root: o mundo do jogo rola (course_root.position.z =
    # distance em _update_run), entao a rua rola junto, em sincronia com os
    # obstaculos; a reciclagem dos quarteiroes usa a propria `distance`.
    course_root.add_child(kit)
    kit.setup()
    _world_kit = kit
    # O horizonte e silhueta fixa (como o HORIZON_Z antigo): nao pode rolar,
    # senao ele "passa" pelo corredor no meio da corrida.
    if kit.horizonte != null and world_root != null:
        kit.horizonte.reparent(world_root)
        _world_horizonte = kit.horizonte


func _destroi_world_kit() -> void:
    if _world_kit != null:
        _world_kit.queue_free()
        _world_kit = null
    if _world_horizonte != null:
        _world_horizonte.queue_free()
        _world_horizonte = null


func _update_world_kit(_delta: float) -> void:
    if _world_kit == null:
        return
    # Roteiro do Lote 3: se o jogo tem a distancia percorrida, use-a. Aqui e a
    # `distance` — o mesmo valor que rola o course_root (1 unidade = 1 m).
    _world_travel = distance
    _world_last_head = _world_travel
    _world_kit.update_head(_world_travel)


func _render_profile_world() -> Dictionary:
    # Paleta do capítulo vinda do world_spec.json (a mesma que o kit usa).
    # `phase_index` é a variável de capítulo deste jogo (roteiro: run_level).
    var spec := BuildingKit.load_spec()
    return BuildingKit.chapter_profile(spec, phase_index)


# --- Lote 4: clima ----------------------------------------------------------
func _setup_clima() -> void:
    if not CLIMA_ATIVO:
        return
    var clima := WeatherSystem.new()
    clima.name = "Clima"
    # Filho do course_root: as pocas ficam em z local fixo por trecho e precisam
    # rolar com a rua. Chuva e sonda se reposicionam sozinhas na camera (global,
    # em _seguir_camera), entao nao sentem o rolamento.
    if course_root != null:
        course_root.add_child(clima)
    else:
        add_child(clima)
    # usa o mesmo perfil que o RenderQuality recebe (Lote 2) e o mesmo
    # deslocamento do piso do kit (Lote 3)
    clima.setup(_render_profile(), WORLD_Y_OFFSET)
    _clima = clima


func _update_clima(_delta: float) -> void:
    if _clima == null:
        return
    _clima.update_head(_world_travel)


func _trocar_clima_do_capitulo(indice: int) -> void:
    if _clima != null:
        _clima.set_chapter(indice)


# --- Lote 6: efeitos de poeira, respingo molhado e captura ------------------
func _ensure_lote6_particles() -> void:
    if _dust_particles != null and _splash_particles != null:
        return
    # poeira de deslize: nuvem baixa atrás dos pés do corredor
    if _dust_particles == null:
        var dust := GPUParticles3D.new()
        dust.name = "Lote6_Dust"
        dust.emitting = false
        dust.amount = 80
        dust.lifetime = 0.7
        dust.visibility_aabb = AABB(Vector3(-2, 0, -2), Vector3(4, 2.5, 4))
        var mat := StandardMaterial3D.new()
        mat.albedo_color = Color("#c2b8a3")
        mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
        var quad := QuadMesh.new()
        quad.size = Vector2(0.22, 0.22)
        quad.material = mat
        dust.draw_pass_1 = quad
        var proc := ParticleProcessMaterial.new()
        proc.direction = Vector3(0, 0.7, -0.6)
        proc.spread = 28.0
        proc.gravity = Vector3(0, -1.2, 0)
        proc.initial_velocity_min = 1.5
        proc.initial_velocity_max = 2.8
        proc.scale_min = 0.35
        proc.scale_max = 0.75
        dust.process_material = proc
        dust.preprocess = 0.1
        (fx_root if fx_root != null else self).add_child(dust)
        _dust_particles = dust
    if _splash_particles == null:
        var splash := GPUParticles3D.new()
        splash.name = "Lote6_Splash"
        splash.emitting = false
        splash.amount = 64
        splash.lifetime = 0.55
        splash.visibility_aabb = AABB(Vector3(-2, 0, -2), Vector3(4, 2.2, 4))
        var smat := StandardMaterial3D.new()
        smat.albedo_color = Color("#87b9d9aa")
        smat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        smat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
        var sQuad := QuadMesh.new()
        sQuad.size = Vector2(0.18, 0.18)
        sQuad.material = smat
        splash.draw_pass_1 = sQuad
        var sProc := ParticleProcessMaterial.new()
        sProc.direction = Vector3(0, 1.0, -0.2)
        sProc.spread = 42.0
        sProc.gravity = Vector3(0, -6.0, 0)
        sProc.initial_velocity_min = 1.2
        sProc.initial_velocity_max = 2.6
        sProc.scale_min = 0.22
        sProc.scale_max = 0.55
        splash.process_material = sProc
        splash.preprocess = 0.1
        (fx_root if fx_root != null else self).add_child(splash)
        _splash_particles = splash

func _update_lote6_effects(_dt: float) -> void:
    _ensure_lote6_particles()
    # Poeira durante deslize e puffs sutis sob as passadas em velocidade alta
    if _dust_particles != null:
        var is_sliding: bool = slide_timer > 0.0
        var is_sprint_step: bool = motion_speed > 8.5 and jump_timer <= 0.0 and fmod(run_phase, 0.5) < 0.20
        var should_dust: bool = (is_sliding or is_sprint_step) and screen == 2 and run_mode == "playing" and not bool(GameSave.data.get("reduced_motion", false))
        _dust_particles.emitting = should_dust
        if should_dust and player_root != null:
            var dust_offset: Vector3 = Vector3(0, 0.06, 0.55) if is_sliding else Vector3(0, 0.03, 0.28)
            _dust_particles.global_position = player_root.global_position + dust_offset
            if is_sliding:
                _dust_particles.restart()
    # Respingo quando o clima indica piso molhado e o corredor avança rápido
    if _splash_particles != null:
        var wet: float = _clima.get_wetness() if _clima != null and _clima.has_method("get_wetness") else 0.0
        var should_splash: bool = wet > 0.35 and motion_speed > 4.0 and jump_timer <= 0.0 and screen == 2 and run_mode == "playing" and not bool(GameSave.data.get("reduced_motion", false))
        # Respinga sincronizado com as passadas para não saturar
        _splash_particles.emitting = should_splash and fmod(run_phase, 0.5) < 0.24
        if should_splash and player_root != null:
            _splash_particles.global_position = player_root.global_position + Vector3(0, 0.03, 0.15)

func _capture_screenshot() -> void:
    var vp: Viewport = get_viewport()
    if vp == null:
        push_warning("Captura: viewport indisponível")
        return
    var img: Image = vp.get_texture().get_image()
    if img == null:
        push_warning("Captura: imagem nula")
        return
    var path := "user://captura_%s.png" % Time.get_datetime_string_from_system().replace(":", "-")
    var err := img.save_png(path)
    if err != OK:
        push_warning("Captura falhou: %d" % err)
        return
    _show_feedback("CAPTURA SALVA", path, CYAN, "ui_confirm")
    print("CAPTURA: %s" % path)

func _toggle_capture_mode() -> void:
    _capture_mode = not _capture_mode
    _show_feedback("MODO CAPTURA " + ("ON" if _capture_mode else "OFF"), "C arrasta órbita • P captura tela • ESC sai" if _capture_mode else "Retornando ao follow", CYAN if _capture_mode else BLUE, "ui_confirm")

# --- Lote 11/12: Ads/Billing -------------------------------------------------
func _setup_ads_billing() -> void:
    # P2: delega ao AdsHandler mantendo contratos
    if Engine.has_singleton("AdsManager") or has_node("/root/AdsManager"):
        AdsHandler.setup_ads_billing(self)
    _update_banner_visibility()


# --- Lote 13: Play Games / Cloud / In-App Review ---------------------------
func _setup_play_services() -> void:
    var ps := get_node_or_null("/root/PlayServicesManager")
    if ps == null: return
    if not ps.is_connected("signed_in", Callable(self, "_on_play_signed_in")):
        ps.signed_in.connect(_on_play_signed_in)
    if not ps.is_connected("cloud_saved", Callable(self, "_on_play_cloud_saved")):
        ps.cloud_saved.connect(_on_play_cloud_saved)
    if not ps.is_connected("cloud_loaded", Callable(self, "_on_play_cloud_loaded")):
        ps.cloud_loaded.connect(_on_play_cloud_loaded)
    if not ps.is_connected("review_requested", Callable(self, "_on_play_review_requested")):
        ps.review_requested.connect(_on_play_review_requested)
    if not ps.is_connected("achievement_unlocked", Callable(self, "_on_play_achievement")):
        ps.achievement_unlocked.connect(_on_play_achievement)

func _setup_analytics() -> void:
    # Lote 15: conecta Analytics + RemoteConfig + Crash (mock não quebra sem plugin)
    if has_node("/root/AnalyticsManager") or Engine.has_singleton("AnalyticsManager"):
        var am = get_node_or_null("/root/AnalyticsManager")
        if am:
            # espelha consent do AdsManager (UMP) para Firebase/GA
            var cons: bool = false
            if has_node("/root/AdsManager"):
                var adm = get_node("/root/AdsManager")
                if adm and adm.has_method("is_consent_granted"):
                    cons = adm.call("is_consent_granted")
            # RemoteConfig fetch já disparado em autoload; aqui só loga readiness
            if has_node("/root/RemoteConfig"):
                var rc = get_node("/root/RemoteConfig")
                if rc and rc.has_signal("config_ready"):
                    rc.config_ready.connect(func(): print("[lote15] RemoteConfig pronto: " + str(rc.get_config())))
            print("[lote15] analytics gate consent=%s enabled=%s" % [str(cons), str(am.is_enabled()) if am.has_method("is_enabled") else "?"])
            # crash handler: captura erros não tratados em _notification
            # teste manual: pressione F8 no editor para force_crash_test (ver docs/RELEASE_LOTE15.md)
    # loga run_start já aqui (metrics→event espelhado)
    if has_node("/root/AnalyticsManager"):
        var am2 = get_node_or_null("/root/AnalyticsManager")
        if am2 and am2.has_method("log_run_start"):
            am2.call("log_run_start", 0)


func _setup_in_app_update() -> void:
    var up := get_node_or_null("/root/InAppUpdateManager")
    if up == null:
        return
    if up.has_signal("update_available"):
        up.update_available.connect(func(v: int): _on_update_available(v))
    if up.has_signal("update_downloaded"):
        up.update_downloaded.connect(func(): _on_update_downloaded())
    if up.has_signal("update_failed"):
        up.update_failed.connect(func(r: String): print("[update] failed %s" % r))
    if up.has_method("check_for_update"):
        up.check_for_update()
        print("[lote18] In-App Update check disparado")

func _setup_push() -> void:
    var pm := get_node_or_null("/root/PushManager")
    if pm == null:
        return
    if pm.has_method("_evaluate_streak"):
        pm.call_deferred("_evaluate_streak")
    print("[p2] push streak avaliado")

func _on_update_available(version_code: int) -> void:
    _show_feedback("ATUALIZAÇÃO DISPONÍVEL", "v%d baixando em segundo plano" % version_code, CYAN, "ui_confirm")
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "inapp_update_available", {"version": version_code})

func _on_update_downloaded() -> void:
    _show_feedback("ATUALIZAÇÃO PRONTA", "Reinicie para instalar", GREEN, "reward")
    # Snackbar flexível: auto completa após 2 s em Test Lab
    var up2 := get_node_or_null("/root/InAppUpdateManager")
    if up2 and up2.has_method("complete_flexible_update"):
        await get_tree().create_timer(2.0).timeout
        up2.complete_flexible_update()


func _on_play_signed_in() -> void:
    _show_feedback("PLAY GAMES", "Progresso na nuvem ativo", GREEN, "ui_confirm")
    _sync_hud()

func _on_play_cloud_saved() -> void:
    print("[play] cloud sync ok")
    _sync_hud()

func _on_play_cloud_loaded(_snap: Dictionary) -> void:
    _show_feedback("NUVEM RESTAURADA", "Progresso e compras recuperados", GOLD, "reward")
    _sync_hud()

func _on_play_review_requested() -> void:
    print("[play] review solicitado")

func _on_play_achievement(id: String) -> void:
    print("[play] achievement %s" % id)

func _push_play_progress() -> void:
    var ps := get_node_or_null("/root/PlayServicesManager")
    if ps == null: return
    if ps.has_method("cloud_save"):
        ps.cloud_save()
    if ps.has_method("submit_leaderboard_score"):
        ps.submit_leaderboard_score("stars", int(GameSave.total_stars()))
        if int(GameSave.data.get("endless_best", 0)) > 0:
            ps.submit_leaderboard_score("endless", int(GameSave.data["endless_best"]))
    if ps.has_method("unlock_achievement"):
        for ach in GameSave.data.get("achievements", []):
            ps.unlock_achievement(str(ach))
        for badge in GameSave.data.get("badges", []):
            ps.unlock_achievement(str(badge))

func _maybe_request_review() -> void:
    var ps := get_node_or_null("/root/PlayServicesManager")
    if ps == null or not ps.has_method("request_review_after_run"): return
    var first_clears: int = int(GameSave.data.get("metrics", {}).get("first_clears", 0))
    ps.request_review_after_run(first_clears)

func _update_banner_visibility() -> void:
    AdsHandler.update_banner_visibility(self)

func _on_ads_banner_loaded() -> void:
    _sync_hud()

func _on_ads_interstitial_closed() -> void:
    _show_feedback("VOLTAMOS!", "Próxima corrida liberada", CYAN, "ui_confirm")
    _sync_hud()

func _on_ads_rewarded_failed(reason: String) -> void:
    _show_feedback("ANÚNCIO INDISPONÍVEL", reason, RED, "ui_back")
    _rewarded_pending_placement = ""
    # Lote 16: se revive pendente, mantém tela para DESISTIR
    if _revive_pending and _revive_screen != null and _revive_screen.visible:
        if has_node("/root/AnalyticsManager"):
            var _anf = get_node_or_null("/root/AnalyticsManager")
            if _anf and _anf.has_method("log_event"):
                _anf.call("log_event", "revive_failed", {"reason": reason})
        return
    _sync_hud()

func _on_ads_rewarded_completed(placement: String) -> void:
    _rewarded_pending_placement = ""
    var ads := get_node_or_null("/root/AdsManager")
    var is_revive: bool = placement == "rewarded_revive" or (ads != null and placement == ads.PLACEMENT_REWARDED_REVIVE)
    var is_double: bool = placement == "rewarded_double" or (ads != null and placement == ads.PLACEMENT_REWARDED_DOUBLE)
    if is_revive:
        _do_revive_from_ad()
    elif is_double:
        _do_double_reward_from_ad()
    else:
        # fallback: decide pelo contexto atual
        if not bool(result.get("success", false)) and not _revive_used:
            _do_revive_from_ad()
        elif bool(result.get("success", false)) and not _double_used:
            _do_double_reward_from_ad()
    _sync_hud()

func _on_billing_products_loaded(_products: Array[Dictionary]) -> void:
    _sync_hud()

func _on_billing_success(product_id: String) -> void:
    if product_id == "remove_ads":
        _show_feedback("SEM ANÚNCIOS!", "Obrigado • interstitial e banner desativados", GREEN, "reward")
        var ads := get_node_or_null("/root/AdsManager")
        if ads and ads.has_method("set_remove_ads"): ads.set_remove_ads(true)
    elif product_id.begins_with("coin_pack"):
        _show_feedback("PACOTE CREDITADO!", "+ moedas na carteira", GOLD, "reward")
    elif product_id == "starter_pack":
        _show_feedback("PACK MOTOBOY!", "Rafa liberado + 120 R$", RED, "reward")
        _rebuild_player_visual("motoboy")
    else:
        _show_feedback("COMPRA OK!", product_id, GREEN, "reward")
    _sync_hud()

func _on_billing_failed(product_id: String, reason: String) -> void:
    _show_feedback("COMPRA FALHOU", "%s: %s" % [product_id, reason], RED, "ui_back")

func _on_billing_restored(product_ids: Array[String]) -> void:
    if product_ids.has("remove_ads"):
        if GameSave:
            GameSave.data["remove_ads"] = true
            GameSave.flush()
        var ads2 := get_node_or_null("/root/AdsManager")
        if ads2 and ads2.has_method("set_remove_ads"):
            ads2.set_remove_ads(true)
        _show_feedback("COMPRAS RESTAURADAS", "Sem anúncios reativado", GREEN, "reward")
    elif product_ids.is_empty():
        _show_feedback("NADA A RESTAURAR", "Nenhuma compra encontrada", MUTED, "ui_back")
    _sync_hud()

func _try_show_interstitial_after_defeat() -> void:
    AdsHandler.try_show_interstitial_after_defeat(self)

func _do_revive_from_ad() -> void:
    if _revive_used:
        _show_feedback("JÁ REVIVEU", "Só 1 revive por corrida", RED, "ui_back")
        return
    _revive_used = true
    _hide_revive_screen()
    run_mode = "playing"
    hearts = 1
    max_hearts = maxi(max_hearts, 3)
    shield_hits = 1
    dash_timer = 2.2  # invencível breve pós-revive
    invulnerability = 2.5
    slow_motion_timer = 0.0
    magnet_timer = 0.0
    # limpa obstáculos muito próximos para não morrer no mesmo frame
    var to_keep: Array[Dictionary] = []
    for ent in entities:
        var z: float = float(ent.get("z", 0.0))
        if z < 4.0: # muito próximo do jogador (z ~ 0)
            # mantém só moedas/coletáveis próximos, remove obstáculos imediatos
            var kind: String = str(ent.get("kind",""))
            if kind in ["coin","coffee","bread","pastel","sugarcane","pass","golden","coxinha","guarana","pix","umbrella"]:
                to_keep.append(ent)
        else:
            to_keep.append(ent)
    entities = to_keep
    # desfaz estado de resultado e volta à corrida
    screen = 2
    run_mode = "playing"
    _update_banner_visibility()
    if GameSave:
        GameSave.record_ad_counter("rewarded")
    _show_feedback("REVIVE!", "5 s de escudo • corre!", GREEN, "reward")
    _spawn_3d_burst(Vector3(player_x, 1.4, -2.0), GREEN, 18)

func _show_revive_screen() -> void:
    if _revive_used or _revive_pending:
        _finish_run(false, true)
        return
    _revive_pending = true
    run_mode = "revive"
    # pausa lógica de corrida (scroll, input)
    # cria overlay ReviveScreen (CanvasLayer 40 para ficar sobre HUD)
    if _revive_screen == null:
        var layer := CanvasLayer.new()
        layer.name = "ReviveLayer"
        layer.layer = 40
        add_child(layer)
        _revive_screen = preload("res://scripts/revive_screen.gd").new()
        _revive_screen.name = "ReviveScreen"
        layer.add_child(_revive_screen)
        _revive_screen.watch_requested.connect(_on_revive_watch)
        _revive_screen.give_up.connect(_on_revive_giveup)
    else:
        _revive_screen.visible = true
        _revive_screen.get_parent().visible = true
    var is_ready: bool = false
    if has_node("/root/AdsManager"):
        var am = get_node_or_null("/root/AdsManager")
        if am and am.has_method("is_rewarded_ready"):
            is_ready = am.call("is_rewarded_ready")
    _revive_screen.call("setup", is_ready)
    _show_feedback("ÔNIBUS QUASE FOI", "5 s para reviver com anúncio", YELLOW, "ui_confirm")
    # Analytics espelho
    if has_node("/root/AnalyticsManager"):
        var an = get_node_or_null("/root/AnalyticsManager")
        if an and an.has_method("log_event"):
            an.call("log_event", "revive_offer", {"ready": int(is_ready)})

func _hide_revive_screen() -> void:
    _revive_pending = false
    if _revive_screen != null:
        _revive_screen.visible = false
        if _revive_screen.get_parent() is CanvasLayer:
            _revive_screen.get_parent().visible = false

func _ensure_tutorial_arrow() -> void:
    # Lote 16: seta 3D para tutorial (posicionada na faixa central, 6 m à frente)
    if _tutorial_arrow != null:
        return
    _tutorial_arrow = Node3D.new()
    _tutorial_arrow.name = "TutorialArrow"
    var arrow := MeshInstance3D.new()
    var cone: CylinderMesh = CylinderMesh.new()
    cone.height = 1.2
    cone.top_radius = 0.0
    cone.bottom_radius = 0.45
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color("#ffd34e")
    mat.emission_enabled = true
    mat.emission = Color("#ff9a00")
    mat.emission_energy_multiplier = 1.4
    cone.material = mat
    arrow.mesh = cone
    arrow.rotation_degrees.x = 180  # ponta para baixo? Ajusta
    arrow.position.y = 2.2
    _tutorial_arrow.add_child(arrow)
    # haste
    var stem := MeshInstance3D.new()
    var cyl := CylinderMesh.new()
    cyl.height = 0.9
    cyl.top_radius = 0.08
    cyl.bottom_radius = 0.08
    var mat2 := StandardMaterial3D.new()
    mat2.albedo_color = Color("#fff8e7")
    cyl.material = mat2
    stem.mesh = cyl
    stem.position.y = 1.1
    _tutorial_arrow.add_child(stem)
    _tutorial_arrow.position = Vector3(0.0, 0.0, -6.0)
    _tutorial_arrow.visible = false
    add_child(_tutorial_arrow)

func _update_tutorial_arrow(target_visible: bool, lane: int = 1) -> void:
    if _tutorial_arrow == null:
        _ensure_tutorial_arrow()
    if _tutorial_arrow == null:
        return
    _tutorial_arrow.visible = target_visible and not bool(GameSave.data.get("tutorial_seen", false))
    if target_visible:
        _tutorial_arrow.position.x = [-3.25, 0.0, 3.25][clampi(lane, 0, 2)]
        _tutorial_arrow.position.z = player_visual.position.z - 7.0 if player_visual else -6.0
        _tutorial_arrow.rotation.y += 0.04


func _on_revive_watch() -> void:
    # Lote 16: ASSISTIR (-30s) → rewarded_revive
    if _revive_used:
        _hide_revive_screen()
        _finish_run(false, true)
        return
    var ads_node = get_node_or_null("/root/AdsManager") if has_node("/root/AdsManager") else null
    var ok: bool = false
    if ads_node and ads_node.has_method("show_rewarded"):
        ok = ads_node.call("show_rewarded", "rewarded_revive")
    if not ok:
        _show_feedback("ANÚNCIO NÃO PRONTO", "Tente novamente", RED, "ui_back")
        # mantém tela para DESISTIR
        return
    _show_feedback("ANÚNCIO...", "Assista para reviver", CYAN, "ui_confirm")
    # fica aguardando rewarded_completed → _do_revive_from_ad

func _on_revive_giveup() -> void:
    _hide_revive_screen()
    _finish_run(false, true)


func _do_double_reward_from_ad() -> void:
    if _double_used:
        _show_feedback("JÁ DOBROU", "2× só uma vez por vitória", RED, "ui_back")
        return
    _double_used = true
    var base_reward: int = int(result.get("reward", 0))
    if base_reward <= 0:
        base_reward = int(result.get("bonus_reward", 0))
    if base_reward <= 0:
        _show_feedback("SEM BÔNUS", "Nada para dobrar", MUTED, "ui_back")
        return
    GameSave.add_coins(base_reward)
    GameSave.flush()
    result["reward"] = base_reward * 2
    result["bonus_reward"] = base_reward * 2
    # marca no result para HUD não reoferecer
    _show_feedback("2× MOEDAS!", "+R$ %d bônus" % base_reward, GOLD, "reward")
    if GameSave:
        GameSave.record_ad_counter("rewarded")
        GameSave.record_event("ad_rewarded_double")
        if has_node("/root/AnalyticsManager"):
            var _am_ad = get_node_or_null("/root/AnalyticsManager")
            if _am_ad and _am_ad.has_method("log_ad_rewarded"):
                _am_ad.call("log_ad_rewarded", "rewarded_double")

