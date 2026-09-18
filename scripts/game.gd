extends Node2D
## Corre pro Ponto — implementação 2D legada (não é a cena de entrada).
## `scenes/main.tscn` usa `game_3d.gd`; este arquivo fica apenas como referência
## histórica para não criar uma segunda fonte de verdade de produto.
## Um runner mobile-first desenhado inteiramente com CanvasItem: sem dependências,
## sem internet e com o mesmo código funcionando no editor e no Android.

const VIEW := Vector2(720.0, 1280.0)
const BALANCE = preload("res://resources/game_balance.tres")
const HORIZON_Y := 382.0
const GROUND_Y := 1075.0
const VISIBLE_Z := 78.0
const LANE_NAMES := ["ESQUERDA", "CENTRO", "DIREITA"]
const UI_BG := Color("#0b1224")
const UI_PANEL := Color("#14233f")
const UI_PANEL_2 := Color("#203a60")
const UI_INK := Color("#07101f")
const WHITE := Color("#fff8e7")
const MUTED := Color("#a9b9ca")
const YELLOW := Color("#ffd34e")
const GOLD := Color("#ffb83e")
const CORAL := Color("#ff6b62")
const RED := Color("#f2635e")
const GREEN := Color("#54d18b")
const BLUE := Color("#63c8ed")
const VIOLET := Color("#ac8cff")
const CYAN := Color("#63e6d2")
const SHADOW := Color(0.01, 0.025, 0.07, 0.48)

const OBSTACLE_NAMES := {
    "trash": "LIXEIRA", "bench": "BANCO", "puddle": "POÇA", "dog": "CARAMELO",
    "cyclist": "CICLISTA", "cone": "OBRA", "sign": "PLACA", "phone": "CELULAR",
    "motoboy": "MOTOBOY", "vendor": "CAMELÔ", "pigeon": "POMBO", "bus": "ÔNIBUS",
    "capybara": "CAPIVARA", "horse": "CAVALO", "truck": "CAMINHÃO", "fridge": "GELADEIRA",
    "scooter": "PATINETE", "drone": "DRONE", "turnstile": "CATRACA", "traffic": "SEMÁFORO",
    "cart": "CARRINHO", "luggage": "MALA", "wall": "PAREDE", "ramp": "RAMPA"
}
const COLLECTIBLE_NAMES := {
    "coin": "R$ 0,25", "coffee": "CAFÉ", "bread": "PÃO DE QUEIJO", "pastel": "PASTEL",
    "sugarcane": "CALDO DE CANA", "mint": "BALA DE HORTELÃ", "pass": "VALE-TRANSPORTE", "golden": "BILHETE DOURADO",
    "coxinha": "COXINHA", "guarana": "GUARANÁ", "pix": "PIX TURBO", "umbrella": "GUARDA-CHUVA", "clover": "TREVO DO ZÉ"
}

var screen: int = 0 # 0 menu, 1 mapa, 2 corrida, 3 resultado, 4 loja, 5 conquistas, 6 diários, 7 como jogar
var previous_screen: int = 0
var phase_index := 0
var phase: Dictionary = {}
var selected_phase := 0
var endless_mode := false
var run_mode := "playing" # playing, paused, at_stop
var elapsed := 0.0
var distance := 0.0
var run_total := 400.0
var player_lane := 1
var hearts := 3
var max_hearts := 3
var collected_coins := 0
var coin_multiplier := 1
var combo := 0
var combo_timer := 0.0
var run_score := 0
var run_coins_value := 0
var rain_guard_timer := 0.0
var no_damage := true
var jump_timer := 0.0
var jump_duration := 0.85
var jump_boost_timer := 0.0
var slide_timer := 0.0
var dash_timer := 0.0
var dash_cooldown := 0.0
var step_timer := 0.0
var invulnerability := 0.0
var slow_motion_timer := 0.0
var speed_boost_timer := 0.0
var magnet_timer := 0.0
var shield_hits := 0
var super_jump := false
var wall_run_timer := 0.0
var wall_run_count := 0
var dog_chase_timer := 0.0
var dog_hits := 0
var passed_obstacles := 0
var stop_wait := 0.0
var stop_wait_total := 0.0
var point_idle_seconds := 0.0
var run_start_time := 0.0
var entities: Array = []
var particles: Array = []
var confetti: Array = []
var rng := RandomNumberGenerator.new()
var fx_rng := RandomNumberGenerator.new()
var toast := ""
var toast_timer := 0.0
var result: Dictionary = {}
var daily_claimed: Array = []
var last_daily_key := ""
var touch_start := Vector2.ZERO
var touch_started_at := 0
var pointer_active := false
var map_scroll := 0.0
var map_page := 0
var shop_tab := 0
var pulse := 0.0
var tutorial_hint := ""

# Feedback de sensação: cada gesto deixa uma resposta visual, sonora e tátil
# (sem depender de partículas caras ou de um plugin externo).
var screen_flash_color := Color.WHITE
var screen_flash_alpha := 0.0
var camera_shake := 0.0
var feedback_title := ""
var feedback_detail := ""
var feedback_color := YELLOW
var feedback_timer := 0.0
var feedback_max_time := 1.0
var floating_feedback: Array = []
var impact_rings: Array = []
var transition_alpha := 0.0

func _ready() -> void:
    rng.seed = 20240917
    fx_rng.seed = 778899
    var streak := GameSave.register_login()
    phase = PhaseData.get_phase(0)
    AudioManager.play_music(0)
    if streak > 1:
        _feedback("SEQUÊNCIA x%d" % streak, "Você voltou para o ponto", GOLD, "streak", Vector2(360, 300), 0.24, 0.05)
    queue_redraw()

func _process(delta: float) -> void:
    var dt := minf(delta, 0.05)
    pulse += dt
    if toast_timer > 0.0:
        toast_timer -= dt
    if screen == 2:
        _update_run(dt)
    _update_particles(dt)
    _update_feedback(dt)
    transition_alpha = maxf(0.0, transition_alpha - dt * 3.2)
    queue_redraw()

func _input(event: InputEvent) -> void:
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
        return

func _handle_key(event: InputEventKey) -> void:
    if event.keycode == KEY_ESCAPE:
        if screen == 2:
            if run_mode == "paused":
                run_mode = "playing"
                _ui_feedback(Vector2(360, 640), "VAMOS!", "O próximo obstáculo é seu", GREEN)
            elif run_mode == "playing":
                run_mode = "paused"
                _ui_feedback(Vector2(360, 640), "PAUSA", "Respira e lê a pista", YELLOW)
            else:
                screen = previous_screen if previous_screen != 2 else 0
                _ui_feedback(Vector2(360, 640), "DE VOLTA", "O busão sempre volta", BLUE, "ui_back")
        elif screen != 0:
            screen = 0
            _ui_feedback(Vector2(360, 640), "MENU", "Escolha o próximo corre", BLUE, "ui_back")
        queue_redraw()
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
            if result.get("success", false):
                screen = 1
            else:
                _start_run(phase_index)
        elif screen == 7:
            screen = previous_screen

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
    _handle_tap(pos)

func _handle_tap(pos: Vector2) -> void:
    if screen == 0:
        if Rect2(70, 564, 580, 104).has_point(pos):
            _start_run(0)
        elif Rect2(70, 700, 275, 82).has_point(pos):
            _ui_feedback(pos, "MAPA ABERTO", "Escolha seu próximo corre", BLUE)
            screen = 1
        elif Rect2(375, 700, 275, 82).has_point(pos):
            _ui_feedback(pos, "LOJA DO PONTO", "Seu estilo, suas regras", CORAL)
            screen = 4
        elif Rect2(70, 808, 275, 82).has_point(pos):
            _ui_feedback(pos, "CONQUISTAS", "Cada corre deixa uma história", VIOLET)
            screen = 5
        elif Rect2(375, 808, 275, 82).has_point(pos):
            _ui_feedback(pos, "DESAFIOS", "Recompensas esperando", GREEN)
            screen = 6
        elif Rect2(70, 930, 580, 80).has_point(pos):
            _ui_feedback(pos, "GUIA RÁPIDO", "Aprenda. Corra. Pegue o busão.", YELLOW)
            screen = 7
            previous_screen = 0
    elif screen == 1:
        if Rect2(26, 40, 120, 60).has_point(pos) or Rect2(25, 1080, 155, 72).has_point(pos):
            _ui_feedback(pos, "DE VOLTA AO MENU", "O ponto continua te esperando", BLUE, "ui_back")
            screen = 0
        elif Rect2(190, 1080, 155, 72).has_point(pos):
            map_page = maxi(0, map_page - 1)
            _ui_feedback(pos, "CAPÍTULO ANTERIOR", "Revisitando seus melhores corres", BLUE, "whoosh")
        elif Rect2(355, 1080, 155, 72).has_point(pos):
            map_page = mini(4, map_page + 1)
            _ui_feedback(pos, "NOVO CAPÍTULO", "Mais caos, mais recompensas", GOLD, "whoosh")
        elif GameSave.data.get("endless_unlocked", false) and Rect2(520, 1080, 175, 72).has_point(pos):
            _ui_feedback(pos, "ENDLESS", "Bata seu recorde local", VIOLET, "ui_confirm")
            _start_endless()
        else:
            var hit := _phase_at_position(pos)
            if hit >= 0:
                if GameSave.is_phase_unlocked(hit):
                    _start_run(hit)
                else:
                    _feedback("TELA BLOQUEADA", "Junte mais estrelas para abrir", CORAL, "ui_back", pos, 0.0, 0.08)
                    _show_toast("Junte estrelas para abrir essa corrida!")
    elif screen == 2:
        if Rect2(620, 36, 72, 58).has_point(pos):
            run_mode = "playing" if run_mode == "paused" else "paused"
            _ui_feedback(pos, "PAUSA" if run_mode == "paused" else "VAMOS!", "Controle seu ritmo", YELLOW if run_mode == "paused" else GREEN)
        elif run_mode == "paused" and Rect2(80, 590, 560, 90).has_point(pos):
            run_mode = "playing"
            _ui_feedback(pos, "VAMOS!", "O próximo obstáculo é seu", GREEN)
        elif run_mode == "at_stop" and Rect2(70, 800, 580, 110).has_point(pos):
            _catch_bus()
    elif screen == 3:
        if Rect2(55, 880, 290, 88).has_point(pos):
            _ui_feedback(pos, "MAPA", "Escolha o próximo capítulo", BLUE, "ui_back")
            screen = 1
        elif Rect2(375, 880, 290, 88).has_point(pos):
            if result.get("success", false):
                _ui_feedback(pos, "DE NOVO!", "Mais uma chance de bater o recorde", GOLD)
                if result.get("endless", false):
                    _start_endless()
                else:
                    _start_run(phase_index)
            elif result.get("game_over", false):
                _revive_run()
            else:
                _start_run(phase_index)
        elif Rect2(55, 1000, 610, 72).has_point(pos):
            _ui_feedback(pos, "NOVO CORRE", "A prática deixa você imparável", BLUE)
            if result.get("success", false):
                screen = 0
            else:
                _start_run(phase_index)
        elif Rect2(55, 1090, 610, 72).has_point(pos):
            _ui_feedback(pos, "ATÉ A PRÓXIMA", "O busão sempre volta", BLUE, "ui_back")
            screen = 0
    elif screen == 4:
        if Rect2(25, 38, 120, 62).has_point(pos) or Rect2(45, 1135, 630, 70).has_point(pos):
            _ui_feedback(pos, "DE VOLTA", "Seu estilo ficou salvo", BLUE, "ui_back")
            screen = 0
        elif Rect2(30, 150, 660, 80).has_point(pos):
            shop_tab = 0 if pos.x < 360 else 1
            _ui_feedback(pos, "CATÁLOGO ATUALIZADO", "Toque para equipar", CORAL)
        else:
            _shop_tap(pos)
    elif screen == 5 or screen == 6 or screen == 7:
        if Rect2(25, 38, 120, 62).has_point(pos) or Rect2(45, 1110, 630, 70).has_point(pos):
            _ui_feedback(pos, "DE VOLTA", "Seu progresso está seguro", BLUE, "ui_back")
            screen = previous_screen if previous_screen not in [5, 6, 7] else 0
        elif screen == 6:
            var daily_index := _daily_at_position(pos)
            if daily_index >= 0:
                _claim_daily(daily_index)

func _phase_at_position(pos: Vector2) -> int:
    var origin_y := 160.0 - map_scroll
    var first_phase := map_page * 10
    for local_index in 10:
        var col := local_index % 2
        var row := int(float(local_index) / 2.0)
        var rect := Rect2(25.0 + col * 340.0, origin_y + row * 170.0, 330.0, 140.0)
        if rect.has_point(pos):
            return first_phase + local_index
    return -1

func _daily_at_position(pos: Vector2) -> int:
    for i in 3:
        if Rect2(35, 200 + i * 190, 650, 145).has_point(pos):
            return i
    return -1

func _start_run(index: int) -> void:
    index = clampi(index, 0, 49)
    map_page = int(float(index) / 10.0)
    endless_mode = false
    if not GameSave.is_phase_unlocked(index):
        _show_toast("Essa tela ainda está fechada. Mais estrelas!")
        return
    phase_index = index
    selected_phase = index
    phase = PhaseData.get_phase(index)
    screen = 2
    previous_screen = 1
    run_mode = "playing"
    elapsed = 0.0
    distance = 0.0
    run_total = float(phase["distance"])
    player_lane = 1
    max_hearts = 3
    hearts = max_hearts
    collected_coins = 0
    run_coins_value = 0
    coin_multiplier = 1
    combo = 0
    combo_timer = 0.0
    run_score = 0
    rain_guard_timer = 0.0
    no_damage = true
    jump_timer = 0.0
    slide_timer = 0.0
    dash_timer = 0.0
    dash_cooldown = 0.0
    step_timer = 0.0
    invulnerability = 0.0
    slow_motion_timer = 0.0
    speed_boost_timer = 0.0
    magnet_timer = 0.0
    shield_hits = 0
    var equipped := str({"chefe": "carlos", "caramelo": "julia"}.get(GameSave.equipped_character(), GameSave.equipped_character()))
    if equipped == "motoboy":
        speed_boost_timer = 9999.0
    elif equipped == "maria":
        shield_hits = 1
    elif equipped == "carlos":
        shield_hits = 1
    elif equipped == "influencer":
        magnet_timer = 9999.0
    if GameSave.owns("mochila"):
        shield_hits += 1
    if GameSave.owns("tenis"):
        speed_boost_timer = 9999.0
    if GameSave.owns("fone"):
        magnet_timer = 9999.0
    if GameSave.owns("cafe"):
        slow_motion_timer = 2.0
    super_jump = false
    wall_run_timer = 0.0
    wall_run_count = 0
    dog_chase_timer = 0.0
    dog_hits = 0
    passed_obstacles = 0
    stop_wait = 0.0
    stop_wait_total = 0.0
    point_idle_seconds = float(GameSave.data.get("point_idle_seconds", 0.0))
    run_start_time = Time.get_ticks_msec() / 1000.0
    tutorial_hint = ""
    particles.clear()
    confetti.clear()
    _build_course()
    AudioManager.play_music(int(phase["music_group"]))
    if phase_index == 0 and not GameSave.data.get("tutorial_seen", false):
        tutorial_hint = "DESLIZE para mudar de pista • TOQUE para dar DASH"
        GameSave.data["tutorial_seen"] = true
        GameSave.save()
    _show_toast(str(phase["special"]))
    _feedback("FASE %02d" % (phase_index + 1), str(phase["name"]), phase["accent"], "ui_confirm", Vector2(360, 560), 0.2, 0.05)

func _start_endless() -> void:
    if not GameSave.data.get("endless_unlocked", false):
        _show_toast("Termine a Maratona final para abrir o Endless.")
        return
    _start_run(BALANCE.endless_unlock_phase)
    endless_mode = true
    run_total = 1000.0
    phase["name"] = "ENDLESS"
    phase["location"] = "ranking local"
    phase["special"] = "Dificuldade sobe sem parar. Quanto você aguenta?"
    phase["distance"] = run_total
    phase["wait"] = 0.0
    _build_course()
    _show_toast("ENDLESS: bateu 1000 m, Zé!")
    _feedback("ENDLESS ATIVADO", "Quanto tempo você aguenta?", VIOLET, "streak", Vector2(360, 560), 0.3, 0.08)

func _build_course() -> void:
    entities.clear()
    var total := float(phase["distance"])
    var obstacle_rate := int(phase["obstacles"])
    var spacing := 100.0 / maxf(2.0, float(obstacle_rate))
    var pool: Array = _hazard_pool()
    var d := 25.0
    var n := 0
    while d < total - 12.0:
        var kind: String = str(pool[n % pool.size()])
        var lane := (n * 5 + phase_index * 2) % 3
        if kind == "wall":
            lane = 0 if n % 2 == 0 else 2
        entities.append({"kind": kind, "lane": lane, "z": d, "passed": false, "resolved": false})
        if n % 4 == 1 and phase_index >= 5:
            var second_lane := (lane + 1 + (n % 2)) % 3
            entities.append({"kind": "coin", "lane": second_lane, "z": d + 3.2, "passed": false, "resolved": false})
        d += spacing + rng.randf_range(-1.6, 1.8)
        n += 1
    # Rampas e paredes são distribuídas de forma previsível para permitir treino.
    var ramps: int = int(phase["ramps"])
    for r in ramps:
        var ramp_z := 42.0 + float(r + 1) * (total - 74.0) / float(ramps + 1)
        entities.append({"kind": "ramp", "lane": (r + phase_index) % 3, "z": ramp_z, "passed": false, "resolved": false})
        for c in 4:
            entities.append({"kind": "coin", "lane": (r + c + phase_index) % 3, "z": ramp_z + 2.5 + c * 2.1, "passed": false, "resolved": false})
    var walls: int = int(phase["wall_runs"])
    for w in walls:
        var wall_z := 52.0 + float(w + 1) * (total - 92.0) / float(walls + 1)
        entities.append({"kind": "wall", "lane": 0 if w % 2 == 0 else 2, "z": wall_z, "passed": false, "resolved": false})
    # Cada tela tem sua gag principal garantida, inclusive se o sorteio mudar.
    var forced: Array = []
    match phase_index:
        1: forced = ["bread", "trash"]
        3: forced = ["vendor", "puddle"]
        5: forced = ["vendor", "pigeon"]
        6: forced = ["bus", "pigeon"]
        7: forced = ["cone", "ramp"]
        8: forced = ["puddle", "fridge", "puddle"]
        9: forced = ["motoboy", "cyclist"]
        10: forced = ["dog", "dog", "capybara"]
        11: forced = ["coin", "sugarcane"]
        12: forced = ["vendor", "pigeon"]
        13: forced = ["capybara", "horse"]
        14: forced = ["wall", "ramp"]
        15: forced = ["bus", "phone", "phone"]
        16: forced = ["phone", "pigeon"]
        17: forced = ["truck", "cone"]
        18: forced = ["dog", "motoboy", "truck"]
        19: forced = ["truck", "bus", "dog", "fridge", "motoboy"]
        _: forced = ["trash", "phone"]
    if phase_index >= 20:
        var expansion_sets: Array = [
            ["drone", "pix", "scooter", "traffic", "luggage"],
            ["cart", "umbrella", "dog", "turnstile", "drone"],
            ["scooter", "cart", "traffic", "luggage", "dog"],
            ["drone", "truck", "capybara", "umbrella", "scooter"],
            ["turnstile", "traffic", "luggage", "truck", "dog"],
            ["drone", "cart", "traffic", "umbrella", "truck"]
        ]
        forced = expansion_sets[mini(5, int(float(phase_index - 20) / 5.0))]
    for j in forced.size():
        var forced_z := 68.0 + j * maxf(15.0, (total - 105.0) / maxf(1.0, float(forced.size())))
        entities.append({"kind": str(forced[j]), "lane": (j + phase_index) % 3, "z": forced_z, "passed": false, "resolved": false})
    # Fileiras de moedas criam a leitura de risco versus recompensa.
    var coin_z := 18.0
    var coin_row := 0
    while coin_z < total - 8.0:
        entities.append({"kind": "coin", "lane": coin_row % 3, "z": coin_z, "passed": false, "resolved": false})
        if coin_row % 5 == 0 and phase_index >= 2:
            entities.append({"kind": _bonus_kind_for_phase(), "lane": (coin_row + 1) % 3, "z": coin_z + 5.0, "passed": false, "resolved": false})
        coin_z += 15.0 + rng.randf_range(-1.0, 2.0)
        coin_row += 1
    entities.append({"kind": "bus", "lane": 1, "z": total - 28.0, "passed": false, "resolved": false})

func _hazard_pool() -> Array:
    var base: Array = ["trash", "bench", "puddle", "cyclist", "phone", "sign"]
    if phase_index >= 3: base.append("vendor")
    if phase_index >= 5: base.append("pigeon")
    if phase_index >= 7: base.append("cone")
    if phase_index >= 8: base.append("fridge")
    if phase_index >= 9: base.append("motoboy")
    if phase_index >= 10: base.append("dog")
    if phase_index >= 12: base.append("capybara")
    if phase_index >= 13: base.append("horse")
    if phase_index >= 15: base.append("bus")
    if phase_index >= 17: base.append("truck")
    if phase_index >= 20: base.append("scooter")
    if phase_index >= 21: base.append("drone")
    if phase_index >= 23: base.append("traffic")
    if phase_index >= 25: base.append("cart")
    if phase_index >= 27: base.append("turnstile")
    if phase_index >= 29: base.append("luggage")
    return base

func _bonus_kind_for_phase() -> String:
    var options := ["coffee", "bread", "pastel", "sugarcane", "mint", "pass"]
    if phase_index >= 19:
        options.append("golden")
    if phase_index >= 20:
        options.append("coxinha")
        options.append("guarana")
        options.append("pix")
        options.append("umbrella")
        options.append("clover")
    return str(options[(phase_index + int(distance)) % options.size()])

func _update_run(dt: float) -> void:
    if run_mode == "paused":
        return
    if run_mode == "at_stop":
        stop_wait -= dt
        point_idle_seconds += dt
        if point_idle_seconds >= 30.0 and not GameSave.has_achievement("idle"):
            GameSave.award_achievement("idle")
            _show_toast("Só mais um pouquinho: 30s no ponto!")
        if stop_wait <= 0.0:
            _finish_run(false)
        return
    elapsed += dt
    step_timer -= dt
    if step_timer <= 0.0:
        AudioManager.play_sfx("step")
        step_timer = maxf(0.16, 0.34 - float(phase["speed"]) * 0.01)
    if jump_timer > 0.0:
        jump_timer = maxf(0.0, jump_timer - dt)
        if jump_timer <= 0.0:
            super_jump = false
    if slide_timer > 0.0:
        slide_timer = maxf(0.0, slide_timer - dt)
    if dash_timer > 0.0:
        dash_timer = maxf(0.0, dash_timer - dt)
    dash_cooldown = maxf(0.0, dash_cooldown - dt)
    invulnerability = maxf(0.0, invulnerability - dt)
    slow_motion_timer = maxf(0.0, slow_motion_timer - dt)
    speed_boost_timer = maxf(0.0, speed_boost_timer - dt)
    magnet_timer = maxf(0.0, magnet_timer - dt)
    wall_run_timer = maxf(0.0, wall_run_timer - dt)
    dog_chase_timer = maxf(0.0, dog_chase_timer - dt)
    rain_guard_timer = maxf(0.0, rain_guard_timer - dt)
    combo_timer = maxf(0.0, combo_timer - dt)
    if combo_timer <= 0.0:
        combo = 0
    var speed := float(phase["speed"])
    if slow_motion_timer > 0.0: speed *= 0.55
    if speed_boost_timer > 0.0: speed *= 1.22
    if dash_timer > 0.0: speed *= 2.0
    if wall_run_timer > 0.0: speed *= 1.33
    distance += speed * dt
    for entity in entities:
        if entity["passed"]:
            continue
        entity["z"] = float(entity["z"]) - speed * dt
        var z: float = float(entity["z"])
        if z < 11.0 and str(entity["kind"]) in COLLECTIBLE_NAMES and magnet_timer > 0.0:
            if absf(int(entity["lane"]) - player_lane) <= 1:
                entity["lane"] = player_lane
        if z <= 0.6:
            entity["passed"] = true
            _resolve_entity(entity)
    if distance >= run_total:
        distance = run_total
        if endless_mode:
            _finish_run(true)
            return
        run_mode = "at_stop"
        stop_wait_total = float(phase["wait"])
        stop_wait = stop_wait_total
        _feedback("PONTO!", "SEGURA O BUSÃO!", YELLOW, "horn", Vector2(505, 375), 0.32, 0.08)
        _show_toast("O ponto! SEGURA O BUSÃO!")
        _spawn_particles(Vector2(575, 340), YELLOW, 28)
    if dog_chase_timer > 0.0 and int(elapsed * 4.0) % 13 == 0 and invulnerability <= 0.0 and int(elapsed * 4.0) != int((elapsed - dt) * 4.0):
        # O cachorro acompanha o corredor, mas deixa uma janela de reação.
        if rng.randf() < 0.15:
            _hit_player("dog")
    if wall_run_timer > 0.0 and int(elapsed * 6.0) % 2 == 0:
        _spawn_particles(Vector2(_lane_x(player_lane), GROUND_Y - 80), BLUE, 1)
    if hearts <= 0:
        _finish_run(false, true)

func _resolve_entity(entity: Dictionary) -> void:
    var kind := str(entity["kind"])
    var lane := int(entity["lane"])
    if kind in COLLECTIBLE_NAMES:
        if lane == player_lane or magnet_timer > 0.0:
            _collect(kind)
        return
    passed_obstacles += 1
    if kind == "dog":
        dog_chase_timer = 10.0
        var dog_position := Vector2(_lane_x(player_lane), GROUND_Y - 100)
        _feedback("CARAMELO!", "10 segundos na sua cola", CORAL, "bark", dog_position, 0.28, 0.07)
        _show_toast("CARAMELO NA SUA COLA! CORRE 10s!")
        if lane != player_lane:
            return
    if lane != player_lane and kind != "wall":
        return
    if kind == "wall":
        if player_lane == lane and jump_timer > 0.0:
            wall_run_timer = 2.6
            wall_run_count += 1
            var wall_position := Vector2(_lane_x(player_lane), GROUND_Y - 130)
            _feedback("WALL-RUN!", "Jeitinho brasileiro desbloqueado", CYAN, "wall", wall_position, 0.3, 0.06)
            _floating_feedback("+ESTILO", wall_position + Vector2(0, -130), CYAN, 15)
            _show_toast("WALL-RUN! Mais rápido, Zé!")
        elif player_lane == lane:
            _feedback("PAREDE!", "Pule para correr por cima", BLUE, "ui_back", Vector2(_lane_x(player_lane), GROUND_Y - 120), 0.0, 0.02)
            _show_toast("SWIPE ↑ na parede para correr por cima!")
        return
    if kind == "ramp":
        if player_lane == lane and jump_timer > 0.0:
            jump_timer = 1.25
            jump_duration = 1.25
            super_jump = true
            var ramp_position := Vector2(_lane_x(player_lane), GROUND_Y - 150)
            _feedback("SUPER PULO!", "Atalho aéreo perfeito", GOLD, "reward", ramp_position, 0.34, 0.07)
            _floating_feedback("+ATALHO", ramp_position + Vector2(0, -100), GOLD, 16)
            _show_toast("SUPER PULO! Atalho aéreo!")
        return
    if lane == player_lane:
        var safe := false
        if kind in ["trash", "bench", "cone", "pigeon", "fridge", "scooter", "cart", "luggage"]:
            safe = jump_timer > 0.0 or dash_timer > 0.0
        elif kind in ["puddle"]:
            safe = jump_timer > 0.0 or slide_timer > 0.0 or dash_timer > 0.0 or rain_guard_timer > 0.0
        elif kind == "sign" or kind == "turnstile":
            safe = slide_timer > 0.0 or jump_timer > 0.0
        elif kind == "drone":
            safe = slide_timer > 0.0 or dash_timer > 0.0
        elif kind == "traffic":
            safe = jump_timer > 0.0 or dash_timer > 0.0
        elif kind == "ramp":
            safe = true
        elif kind == "capybara":
            safe = dash_timer > 0.0
        elif kind == "horse":
            safe = jump_timer > 0.0 or dash_timer > 0.0
        elif kind == "truck":
            safe = dash_timer > 0.0 or jump_timer > 0.0
        elif kind == "bus":
            safe = jump_timer > 0.0 or dash_timer > 0.0
        if safe:
            var dodge_position := Vector2(_lane_x(player_lane), GROUND_Y - 100)
            var reaction := _funny_reaction(kind)
            _feedback("DESVIO LIMPO", reaction, YELLOW, "reward", dodge_position, 0.14, 0.025)
            _floating_feedback("+HABILIDADE", dodge_position + Vector2(0, -115), YELLOW, 14)
            _show_toast(reaction)
        else:
            _hit_player(kind)

func _funny_reaction(kind: String) -> String:
    var reactions := {
        "trash": "O gato: MIAU! Desvio bonito.",
        "bench": "O véio: ÔÔÔ! Quase acordou!",
        "puddle": "Molhou só o tênis!",
        "fridge": "Molhou só o tênis!",
        "cone": "TRRRRRR... obra vencida!",
        "pigeon": "POMBO NA CARA!",
        "scooter": "Patinete voador? Quem deixou?",
        "drone": "Entrega expressa desviada!",
        "turnstile": "Catraca liberada no jeitinho!",
        "traffic": "Sinal amarelo: acelera!",
        "cart": "Carrinho sem dono!",
        "luggage": "Mala despachada!",
        "horse": "Êta, interior!",
        "truck": "Timing de cinema!",
        "bus": "Pulo por cima do busão!"
    }
    return str(reactions.get(kind, "Boa, Zé!"))

func _hit_player(kind: String) -> void:
    if invulnerability > 0.0 or dash_timer > 0.0:
        return
    if shield_hits > 0:
        shield_hits -= 1
        invulnerability = 0.8
        var shield_position := Vector2(_lane_x(player_lane), GROUND_Y - 120)
        _feedback("ESCUDO!", "O impacto foi absorvido", CYAN, "hit", shield_position, 0.3, 0.05)
        _floating_feedback("BLOQUEADO", shield_position + Vector2(0, -105), CYAN, 16)
        _show_toast("O pastel segurou o impacto! MASSA GROSSA!")
        return
    hearts -= 1
    no_damage = false
    invulnerability = 1.1
    var hit_position := Vector2(_lane_x(player_lane), GROUND_Y - 120)
    var hearts_label := "1 coração" if hearts == 1 else ("%d corações" % hearts)
    _feedback("AI!", hearts_label + " restante", RED, "impact_heavy", hit_position, 0.62, 0.16)
    _floating_feedback("-1 CORAÇÃO", hit_position + Vector2(0, -120), RED, 17)
    if kind == "dog":
        dog_hits += 1
        GameSave.data["dog_hits"] = int(GameSave.data.get("dog_hits", 0)) + 1
        if int(GameSave.data["dog_hits"]) >= 10:
            GameSave.award_achievement("dog")
        GameSave.save()
        _show_toast("O caramelo te pegou! Levanta, Zé!")
    elif kind == "motoboy":
        AudioManager.play_sfx("shout")
        _show_toast("SAI DA RUA! — motoboy, provavelmente")
    elif kind == "truck":
        _show_toast("CAMINHÃO DESGOVERNADO! Timing exato, lembra?")
    else:
        _show_toast("Ai! Ainda tem coração. Foco no ponto!")

func _collect(kind: String) -> void:
    var value := 1
    var reward_position := Vector2(_lane_x(player_lane), GROUND_Y - 155)
    if kind == "coin":
        value = coin_multiplier
        collected_coins += 1
        run_coins_value += value
        combo += 1
        combo_timer = 4.0
        run_score += value * 10 * maxi(1, combo)
        var pitch := 0.94 + minf(0.18, float(combo) * 0.012)
        _micro_feedback("+R$ %0.2f" % (0.25 * value), reward_position, GOLD, "coin", pitch)
        if combo >= 5 and combo % 5 == 0:
            var combo_color := GOLD if combo < 15 else CYAN
            _feedback("COMBO x%02d" % combo, "A sequência está valendo mais", combo_color, "combo", reward_position, 0.28, 0.06)
        _show_toast("R$ 0,25 × %d  •  COMBO %02d" % [coin_multiplier, combo])
        if combo >= 15:
            if GameSave.award_badge("combo15"):
                _feedback("BADGE DESBLOQUEADO", "Combo de respeito", CYAN, "streak", reward_position, 0.3, 0.08)
    else:
        var bonus_title := str(COLLECTIBLE_NAMES.get(kind, "BÔNUS"))
        _feedback("BÔNUS!", bonus_title, GOLD, "reward", reward_position, 0.2, 0.05)
        match kind:
            "coffee":
                slow_motion_timer = 5.0
                _show_toast("Ai que delícia, cara! Câmera lenta.")
            "bread":
                jump_boost_timer = 7.0
                _show_toast("Pão de queijo: energia mineira!")
            "pastel":
                shield_hits = 1
                _show_toast("Massa grossa: escudo de 1 hit!")
            "sugarcane":
                speed_boost_timer = 6.0
                _show_toast("Caldo de cana turbo!")
            "mint":
                magnet_timer = 8.0
                _show_toast("Bala de hortelã: ímã de moedas!")
            "pass":
                coin_multiplier = 2
                _show_toast("Vale-transporte: moedas em dobro!")
            "coxinha":
                shield_hits = 2
                _show_toast("Coxinha de rodoviária: duas mordidas de escudo!")
            "guarana":
                speed_boost_timer = 9.0
                _show_toast("Guaraná gelado: modo foguete!")
            "pix":
                coin_multiplier = 3
                _show_toast("PIX TURBO: aceita em qualquer pista!")
            "umbrella":
                rain_guard_timer = 12.0
                _show_toast("Guarda-chuva aberto: respingo zero!")
            "clover":
                coin_multiplier = 4
                shield_hits = maxi(shield_hits, 1)
                _show_toast("Trevo do Zé: hoje vai dar bom!")
            "golden":
                if GameSave.unlock_pet("caramelo"):
                    _feedback("SKIN LIBERADA", "Cachorro Caramelo entrou no time", GOLD, "streak", reward_position, 0.35, 0.1)
                _show_toast("Bilhete dourado! Skin Caramelo liberada!")
        _floating_feedback("+EFEITO", reward_position + Vector2(0, -105), GOLD, 14)
    GameSave.add_coins(value)

func _change_lane(direction: int) -> void:
    if screen != 2 or run_mode != "playing":
        return
    var old := player_lane
    player_lane = clampi(player_lane + direction, 0, 2)
    if old != player_lane:
        var lane_position := Vector2(_lane_x(player_lane), GROUND_Y - 30)
        _feedback("PISTA %s" % LANE_NAMES[player_lane], "Boa leitura!", BLUE, "whoosh", lane_position, 0.16, 0.02)
        _floating_feedback("+FLUIDEZ", lane_position + Vector2(0, -100), BLUE, 14)

func _jump() -> void:
    if screen != 2 or run_mode != "playing" or jump_timer > 0.0 or slide_timer > 0.0:
        return
    jump_duration = 0.95 if jump_boost_timer <= 0.0 else 1.25
    jump_timer = jump_duration
    super_jump = false
    var jump_position := Vector2(_lane_x(player_lane), GROUND_Y - 40)
    _feedback("PULO!", "Rota aérea", CYAN, "jump", jump_position, 0.1, 0.02)
    _floating_feedback("+ALTURA", jump_position + Vector2(0, -125), CYAN, 14)

func _slide() -> void:
    if screen != 2 or run_mode != "playing" or jump_timer > 0.0:
        return
    slide_timer = 0.72
    var slide_position := Vector2(_lane_x(player_lane), GROUND_Y - 35)
    _feedback("DESLIZE!", "Passou por baixo", VIOLET, "slide", slide_position, 0.08, 0.02)
    _floating_feedback("+PRECISÃO", slide_position + Vector2(0, -90), VIOLET, 14)

func _dash() -> void:
    if screen != 2 or run_mode != "playing" or dash_cooldown > 0.0:
        return
    dash_timer = 0.42
    dash_cooldown = 3.2
    invulnerability = maxf(invulnerability, 0.5)
    var dash_position := Vector2(_lane_x(player_lane), GROUND_Y - 90)
    _feedback("DASH!", "Invencível por um instante", YELLOW, "whoosh", dash_position, 0.42, 0.06)
    _floating_feedback("+MOMENTO", dash_position + Vector2(0, -115), YELLOW, 15)
    _show_toast("DASH! Sai da frente!")

func _catch_bus() -> void:
    if run_mode != "at_stop":
        return
    _finish_run(true)

func _revive_run() -> void:
    if result.get("success", false):
        return
    screen = 2
    run_mode = "playing"
    hearts = 1
    max_hearts = maxi(max_hearts, 1)
    invulnerability = 3.0
    result.clear()
    _show_toast("REVIVE offline: uma nova tentativa, sem anúncio e sem custo.")

func _finish_run(success: bool, game_over := false) -> void:
    if screen != 2:
        return
    GameSave.data["point_idle_seconds"] = point_idle_seconds
    GameSave.save()
    GameSave.record_daily_progress(Time.get_date_string_from_system(), int(distance), collected_coins, success and no_damage)
    if endless_mode:
        if success:
            var old_best := int(GameSave.data.get("endless_best", 0))
            var is_record := int(distance) > old_best
            if is_record:
                GameSave.data["endless_best"] = int(distance)
                GameSave.save()
            var endless_reward := 40 + int(distance / 10.0) + collected_coins + combo * 2
            GameSave.add_coins(endless_reward)
            GameSave.add_xp(100 + int(distance / 5.0))
            result = {"success": true, "endless": true, "stars": 0, "reward": endless_reward, "time": elapsed, "coins": collected_coins, "score": run_score, "game_over": false, "record": is_record, "distance": int(distance)}
            _feedback("ENDLESS CONCLUÍDO!", "%dm • +R$ %d" % [int(distance), endless_reward], VIOLET, "streak", Vector2(360, 350), 0.5, 0.1)
        else:
            result = {"success": false, "endless": true, "stars": 0, "reward": 0, "time": elapsed, "coins": collected_coins, "score": run_score, "game_over": game_over, "record": false, "distance": int(distance)}
            _feedback("MAIS UM!", "Seu melhor corre ainda está aí", RED, "impact_heavy", Vector2(360, 450), 0.35, 0.08)
        run_mode = "results"
        screen = 3
        return
    if success:
        var stars := 1
        if no_damage:
            stars = 2
        var record := GameSave.best_time(phase_index)
        var was_record := record <= 0.0 or elapsed < record
        if collected_coins >= int(phase["coin_target"]) and (was_record or elapsed < 100.0):
            stars = 3
        var reward := 20 + phase_index * 3 + stars * 5 + collected_coins + combo
        GameSave.record_phase(phase_index, stars, elapsed)
        GameSave.add_coins(reward)
        GameSave.add_xp(25 + phase_index * 4 + int(run_score / 100.0))
        if phase_index == 19:
            GameSave.award_achievement("busao")
            GameSave.award_badge("capitulo1")
        if phase_index == 49:
            GameSave.award_achievement("busao50")
            GameSave.award_badge("maratonista")
            GameSave.data["endless_unlocked"] = true
            GameSave.save()
        if no_damage and stars >= 2:
            GameSave.award_badge("sem_arranhao")
        if phase_index == 8 and no_damage:
            GameSave.award_achievement("enchente")
        if wall_run_count >= 3:
            GameSave.award_achievement("wallrun")
        result = {"success": true, "stars": stars, "reward": reward, "time": elapsed, "coins": collected_coins, "score": run_score, "combo": combo, "game_over": false, "record": was_record}
        _feedback("PEGUEI O BUSÃO!", "%d estrelas • +R$ %d" % [stars, reward], YELLOW, "streak", Vector2(360, 350), 0.45, 0.1)
        _floating_feedback("+%d XP" % (25 + phase_index * 4 + int(run_score / 100.0)), Vector2(360, 470), GREEN, 20)
        _spawn_particles(Vector2(360, 350), YELLOW, 42)
    else:
        result = {"success": false, "stars": 0, "reward": 0, "time": elapsed, "coins": collected_coins, "score": run_score, "game_over": game_over, "record": false}
        _feedback("QUASE!", "Use a pista, o pulo e o dash", RED, "impact_heavy", Vector2(360, 450), 0.35, 0.08)
    run_mode = "results"
    screen = 3

func _show_toast(message: String) -> void:
    toast = message
    toast_timer = 2.8

func _update_particles(dt: float) -> void:
    for p in particles:
        p["life"] = float(p["life"]) - dt
        p["pos"] = Vector2(p["pos"]) + Vector2(p["velocity"]) * dt
        p["velocity"] = Vector2(p["velocity"]) + Vector2(0, 180) * dt
    particles = particles.filter(func(p): return float(p["life"]) > 0.0)
    for c in confetti:
        c["life"] = float(c["life"]) - dt
        c["pos"] = Vector2(c["pos"]) + Vector2(c["velocity"]) * dt
    confetti = confetti.filter(func(c): return float(c["life"]) > 0.0)

func _update_feedback(dt: float) -> void:
    screen_flash_alpha = maxf(0.0, screen_flash_alpha - dt * 4.8)
    camera_shake = maxf(0.0, camera_shake - dt * 8.0)
    feedback_timer = maxf(0.0, feedback_timer - dt)
    for item in floating_feedback:
        item["life"] = float(item["life"]) - dt
        item["pos"] = Vector2(item["pos"]) + Vector2(item["drift"]) * dt
    floating_feedback = floating_feedback.filter(func(item): return float(item["life"]) > 0.0)
    for ring in impact_rings:
        ring["life"] = float(ring["life"]) - dt
        ring["radius"] = float(ring["radius"]) + float(ring["growth"]) * dt
    impact_rings = impact_rings.filter(func(ring): return float(ring["life"]) > 0.0)

func _feedback(
    title: String,
    detail: String,
    color: Color,
    sound: String = "",
    panel_position: Vector2 = Vector2(-1, -1),
    intensity: float = 0.0,
    flash: float = 0.0
) -> void:
    var origin := panel_position if panel_position.x >= 0.0 else Vector2(360, 540)
    feedback_title = title
    feedback_detail = detail
    feedback_color = color
    feedback_max_time = 0.92 if intensity < 0.5 else 1.25
    feedback_timer = feedback_max_time
    screen_flash_color = color
    screen_flash_alpha = maxf(screen_flash_alpha, flash)
    camera_shake = maxf(camera_shake, intensity)
    impact_rings.append({
        "pos": origin,
        "radius": 20.0,
        "growth": 150.0 + intensity * 70.0,
        "life": 0.48,
        "color": color
    })
    _spawn_particles(origin, color, 7 + int(intensity * 10.0))
    if sound != "":
        AudioManager.play_sfx(sound)

func _ui_feedback(pos: Vector2, title: String, detail: String, color: Color, sound := "ui_confirm") -> void:
    _feedback(title, detail, color, sound, pos, 0.0, 0.035)
    transition_alpha = 0.18

func _micro_feedback(text: String, pos: Vector2, color: Color, sound: String, pitch := 1.0) -> void:
    _floating_feedback(text, pos + Vector2(0, -22), color, 15)
    impact_rings.append({"pos": pos, "radius": 12.0, "growth": 92.0, "life": 0.32, "color": color})
    _spawn_particles(pos, color, 4)
    AudioManager.play_sfx(sound, -2.0, pitch)

func _floating_feedback(text: String, pos: Vector2, color: Color, size := 18) -> void:
    floating_feedback.append({
        "text": text,
        "pos": pos,
        "drift": Vector2(fx_rng.randf_range(-8.0, 8.0), -48.0),
        "life": 1.0,
        "max_life": 1.0,
        "color": color,
        "size": size
    })

func _draw_feedback_overlay() -> void:
    for ring in impact_rings:
        var alpha := clampf(float(ring["life"]) / 0.48, 0.0, 1.0)
        draw_arc(Vector2(ring["pos"]), float(ring["radius"]), 0.0, TAU, 24, Color(ring["color"], alpha * 0.72), 3.0)
    for item in floating_feedback:
        var alpha := clampf(float(item["life"]) / float(item["max_life"]), 0.0, 1.0)
        _text_center(Vector2(item["pos"]), str(item["text"]), int(item["size"]), Color(item["color"], alpha))
    if feedback_timer > 0.0:
        var progress := clampf(feedback_timer / feedback_max_time, 0.0, 1.0)
        var alpha := minf(1.0, (1.0 - progress) * 8.0) if progress < 0.88 else 1.0
        var width := minf(620.0, 130.0 + float(feedback_title.length() + feedback_detail.length()) * 4.1)
        var y := 142.0 if screen == 2 else 122.0
        var rect := Rect2((720.0 - width) / 2.0, y, width, 68.0)
        _panel(Rect2(rect.position + Vector2(0, 4), rect.size), Color(feedback_color, 0.18 * alpha), 18)
        draw_rect(Rect2(rect.position + Vector2(0, rect.size.y - 3), Vector2(rect.size.x * progress, 3)), Color(feedback_color, 0.9 * alpha))
        _text_center(Vector2(360, y + 28), feedback_title, 20, Color(WHITE, alpha))
        _text_center(Vector2(360, y + 52), feedback_detail, 13, Color(feedback_color.lightened(0.22), alpha))
    if screen_flash_alpha > 0.0:
        draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(screen_flash_color, screen_flash_alpha))

func _spawn_particles(pos: Vector2, color: Color, amount: int) -> void:
    for i in amount:
        particles.append({"pos": pos, "velocity": Vector2(fx_rng.randf_range(-90, 90), fx_rng.randf_range(-170, -30)), "life": fx_rng.randf_range(0.35, 0.8), "color": color})

func _spawn_confetti(amount: int) -> void:
    var colors := [Color("#f54291"), Color("#55d7c0"), Color("#ffd34e"), Color("#6da8ff"), Color("#ff754f")]
    for i in amount:
        confetti.append({"pos": Vector2(fx_rng.randf_range(20, 700), fx_rng.randf_range(-80, 220)), "velocity": Vector2(fx_rng.randf_range(-35, 35), fx_rng.randf_range(60, 180)), "life": fx_rng.randf_range(2.0, 4.5), "color": colors[i % colors.size()]})

# -----------------------------------------------------------------------------
# Desenho da interface
# -----------------------------------------------------------------------------
func _draw() -> void:
    var shake := Vector2.ZERO
    if camera_shake > 0.0:
        shake = Vector2(fx_rng.randf_range(-camera_shake, camera_shake), fx_rng.randf_range(-camera_shake, camera_shake))
    draw_set_transform(shake, 0.0, Vector2.ONE)
    match screen:
        0: _draw_menu()
        1: _draw_map()
        2: _draw_run()
        3: _draw_results()
        4: _draw_shop()
        5: _draw_achievements()
        6: _draw_daily()
        7: _draw_how_to()
    draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
    _draw_global_particles()
    _draw_feedback_overlay()

func _draw_menu() -> void:
    _draw_gradient(Color("#09152f"), Color("#e05f58"))
    # Camadas de atmosfera e linhas de velocidade dão profundidade à capa.
    for i in 9:
        var line_x := float(18 + i * 91)
        draw_line(Vector2(line_x, 250 + (i % 3) * 22), Vector2(line_x - 86, 520), Color(1, 0.82, 0.42, 0.12), 2.0)
    _draw_city_silhouette(0.50)
    _draw_sun(Vector2(570, 235), 68, Color("#ffd979"))
    draw_circle(Vector2(570, 235), 104 + sin(pulse * 1.4) * 5.0, Color(1.0, 0.72, 0.35, 0.08))
    _ellipse(Vector2(390, 485), 205.0, 20.0, Color(0.02, 0.04, 0.08, 0.34))
    _draw_bus(Vector2(390, 410), 0.92, false)
    _draw_runner(Vector2(148, 425), 0.90, false)
    _panel(Rect2(38, 62, 310, 173), Color(0.04, 0.08, 0.17, 0.64), 26)
    _text(Vector2(60, 126), "CORRE", 62, YELLOW)
    _text(Vector2(60, 188), "PRO PONTO", 52, WHITE)
    _text(Vector2(62, 218), "o runner mais atrasado do Brasil", 17, Color("#ffe4ad"))
    _panel(Rect2(420, 68, 246, 48), Color(0.04, 0.08, 0.17, 0.72), 22)
    _text(Vector2(444, 99), "● AO VIVO", 15, CYAN)
    _text(Vector2(558, 99), "50 FASES", 14, WHITE)
    _panel(Rect2(70, 564, 580, 104), Color("#f1b72f"), 22)
    draw_rect(Rect2(90, 574, 540, 4), Color(1, 1, 1, 0.35))
    _text_center(Vector2(360, 614), "CORRER AGORA", 30, UI_INK)
    _text_center(Vector2(360, 648), "começa na segunda-feira", 17, Color("#553526"))
    _button(Rect2(70, 700, 275, 82), "FASES", Color("#2c9dc1"), 25)
    _button(Rect2(375, 700, 275, 82), "LOJA", Color("#d65b75"), 25)
    _button(Rect2(70, 808, 275, 82), "CONQUISTAS", Color("#805ec7"), 21)
    _button(Rect2(375, 808, 275, 82), "DESAFIOS", Color("#4bad73"), 22)
    _panel(Rect2(70, 930, 580, 80), Color("#172844"), 18)
    draw_circle(Vector2(100, 970), 17, Color("#263f66"))
    _text_center(Vector2(100, 977), "?", 22, CYAN)
    _text(Vector2(132, 965), "COMO JOGAR", 22, WHITE)
    _text(Vector2(132, 992), "swipe ← →  •  swipe ↑ ↓  •  toque = dash", 15, MUTED)
    _panel(Rect2(48, 1055, 624, 105), Color(0.04, 0.08, 0.17, 0.78), 20)
    _text(Vector2(72, 1095), "★ %03d / 150" % GameSave.total_stars(), 24, YELLOW)
    _text(Vector2(425, 1095), "R$ %03d" % GameSave.coins(), 22, Color("#8ee5bb"))
    _text(Vector2(72, 1140), "🔥 %02d dias de sequência" % int(GameSave.data.get("daily_streak", 0)), 17, Color("#ffb86b"))
    _text(Vector2(330, 1140), "6 momentos clipáveis", 15, Color("#f9c8ae"))
    _text(Vector2(72, 1178), "ônibus impossível • humor brasileiro • corre sem parar", 14, Color("#d3e5ef"))

func _draw_map() -> void:
    _draw_ui_background()
    _header("MAPA DE CORRIDAS", "★ %03d / 150" % GameSave.total_stars())
    _text(Vector2(30, 126), "Expansão Brasil sem Freio • capítulo %d / 5" % (map_page + 1), 17, MUTED)
    var origin_y := 160.0 - map_scroll
    var first_phase := map_page * 10
    for local_index in 10:
        var i := first_phase + local_index
        var col := local_index % 2
        var row := int(float(local_index) / 2.0)
        var rect := Rect2(25.0 + col * 340.0, origin_y + row * 170.0, 330.0, 140.0)
        var unlocked := GameSave.is_phase_unlocked(i)
        var p := PhaseData.get_phase(i)
        var card_color := Color("#1d3658") if unlocked else Color("#111d34")
        _panel(rect, card_color, 16)
        if unlocked:
            draw_rect(Rect2(rect.position + Vector2(0, 0), Vector2(5, rect.size.y)), p["accent"])
            if i == selected_phase:
                draw_rect(rect.grow(-2.0), Color(p["accent"], 0.75), false, 2.0)
        _panel(Rect2(rect.position + Vector2(10, 12), Vector2(52, 52)), p["accent"] if unlocked else Color("#303d53"), 13)
        _text_center(rect.position + Vector2(36, 47), "%02d" % (i + 1) if unlocked else "🔒", 20, UI_BG if unlocked else MUTED)
        _text(rect.position + Vector2(76, 34), str(p["name"]), 18, WHITE if unlocked else MUTED)
        _text(rect.position + Vector2(76, 61), str(p["location"]), 13, Color("#90a6bb"))
        var stars := GameSave.phase_stars(i)
        _text(rect.position + Vector2(18, 101), "★".repeat(stars) + "☆".repeat(3 - stars), 18, YELLOW)
        _text(rect.position + Vector2(172, 101), "DIF " + "★".repeat(int(p["difficulty"])), 13, p["accent"])
        _text(rect.position + Vector2(18, 125), "%d m/s  •  %d obstáculos/100m" % [int(p["speed"]), int(p["obstacles"])], 12, MUTED)
    _button(Rect2(25, 1080, 155, 72), "MENU", Color("#293955"), 18)
    _button(Rect2(190, 1080, 155, 72), "‹ ANTERIOR" if map_page > 0 else "•", Color("#293955"), 16)
    _button(Rect2(355, 1080, 155, 72), "PRÓXIMO ›" if map_page < 4 else "•", Color("#293955"), 16)
    if GameSave.data.get("endless_unlocked", false):
        _button(Rect2(520, 1080, 175, 72), "ENDLESS", Color("#9b68d6"), 18)
    else:
        _text_center(Vector2(607, 1125), "★ 120 = TELA 50", 13, MUTED)
    _text_center(Vector2(360, 1205), "Tela 20 exige 45 estrelas • Tela 50 exige 120", 15, Color("#f9c8ae"))

func _draw_results() -> void:
    _draw_gradient(Color("#08132b"), Color("#1c3c5a"))
    for i in 7:
        var ray_angle := -1.25 + float(i) * 0.42
        var ray_end := Vector2(360, 350) + Vector2(cos(ray_angle), sin(ray_angle)) * 420.0
        draw_line(Vector2(360, 350), ray_end, Color(1.0, 0.78, 0.30, 0.055), 10.0)
    var success: bool = result.get("success", false)
    var endless_result: bool = result.get("endless", false)
    if success:
        _spawn_confetti(0 if confetti.size() > 0 else 48)
        _text_center(Vector2(360, 150), "ENDLESS CONCLUÍDO!" if endless_result else "PEGUEI O BUSÃO!", 39, YELLOW)
        _text_center(Vector2(360, 190), (("DISTÂNCIA: %dm" % int(result.get("distance", 0))) if endless_result else ("%02d • %s" % [phase_index + 1, phase["name"]])), 18, WHITE)
        _draw_bus(Vector2(360, 365), 1.12, false)
        if endless_result:
            _text_center(Vector2(360, 510), "%dm" % int(result.get("distance", 0)), 48, Color("#8ee5bb"))
            _text_center(Vector2(360, 548), "RECORDE LOCAL" if result.get("record", false) else "TREINO DE RESISTÊNCIA", 14, VIOLET if result.get("record", false) else MUTED)
        else:
            for star_index in 3:
                var star_center := Vector2(260 + star_index * 100, 505)
                var filled := star_index < int(result["stars"])
                var star_color := YELLOW if filled else Color("#324663")
                if filled:
                    draw_circle(star_center, 37 + sin(pulse * 3.0 + star_index) * 3.0, Color(YELLOW, 0.12))
                _text_center(star_center + Vector2(0, 17), "★", 48, star_color)
        _panel(Rect2(65, 560, 590, 205), Color("#182b48"), 20)
        _text(Vector2(95, 610), "TEMPO", 16, MUTED)
        _text(Vector2(95, 648), "%05.1f s" % float(result["time"]), 31, WHITE)
        _text(Vector2(360, 610), "MOEDAS", 16, MUTED)
        _text(Vector2(360, 648), "+%02d" % int(result["coins"]), 31, Color("#8ee5bb"))
        _text(Vector2(95, 706), "RECOMPENSA", 16, MUTED)
        _text(Vector2(95, 741), "+R$ %d" % int(result["reward"]), 27, YELLOW)
        _text(Vector2(360, 706), "RECORDE LOCAL" if endless_result else "MELHOR TEMPO", 16, MUTED)
        _text(Vector2(360, 741), "NOVO!" if result.get("record", false) else "continua treinando", 22, GREEN if result.get("record", false) else MUTED)
    else:
        _text_center(Vector2(360, 165), "O BUSÃO FOI EMBORA", 35, RED)
        _text_center(Vector2(360, 205), "Zé, você chegou quase lá.", 20, WHITE)
        _draw_bus(Vector2(485, 380), 1.0, true)
        _draw_runner(Vector2(230, 430), 0.86, false)
        _panel(Rect2(65, 560, 590, 170), Color("#2b223a"), 20)
        _text_center(Vector2(360, 610), "DICA DE SOBREVIVÊNCIA", 18, Color("#ffbf8b"))
        _text_center(Vector2(360, 655), "Troque de pista antes do obstáculo", 20, WHITE)
        _text_center(Vector2(360, 688), "e guarde o dash para o caminhão.", 20, MUTED)
    _button(Rect2(55, 880, 290, 88), "MAPA", Color("#2c9dc1"), 24)
    _button(Rect2(375, 880, 290, 88), ("TENTAR DE NOVO" if success else ("REVIVER OFFLINE" if result.get("game_over", false) else "TENTAR DE NOVO")), Color("#e0a83c"), 18)
    _button(Rect2(55, 1000, 610, 72), "MENU PRINCIPAL" if success else "TENTAR DE NOVO", Color("#293955"), 20)
    if not success:
        _button(Rect2(55, 1090, 610, 72), "MENU PRINCIPAL", Color("#293955"), 20)
    _text_center(Vector2(360, 1200), "Dica: 3 estrelas exigem moedas + tempo recorde." if success else "Sem anúncios interrompendo o corre: tente de novo quando quiser.", 14, MUTED)

func _draw_shop() -> void:
    _draw_ui_background()
    _header("LOJA DO PONTO", "R$ %03d" % GameSave.coins())
    _text(Vector2(30, 126), "Equipe seu corre. Tudo comprado com moeda da passagem.", 16, MUTED)
    _button(Rect2(30, 150, 330, 70), "PERSONAGENS", Color("#2c9dc1" if shop_tab == 0 else "#263958"), 18)
    _button(Rect2(360, 150, 330, 70), "ITENS", Color("#d65b75" if shop_tab == 1 else "#263958"), 20)
    if shop_tab == 0:
        _draw_character_card(Rect2(30, 250, 660, 126), "ze", "Zé Atrasado", "o original", 0, Color("#e9525e"))
        _draw_character_card(Rect2(30, 395, 660, 126), "maria", "Maria do Bairro", "escudo de impacto", 180, Color("#a568d7"))
        _draw_character_card(Rect2(30, 540, 660, 126), "motoboy", "Rafa Motoboy", "velocidade +22%", 260, Color("#4fc2b1"))
        _draw_character_card(Rect2(30, 685, 660, 126), "julia", "Júlia Atleta", "pulo prolongado", 360, Color("#e9d459"))
        _draw_character_card(Rect2(30, 830, 660, 126), "carlos", "Carlos da Obra", "escudo de impacto", 440, Color("#5e7bc4"))
        _draw_character_card(Rect2(30, 975, 660, 126), "influencer", "Nina Creator", "ímã de moedas", 420, Color("#e56b98"))
    else:
        _draw_item_card(Rect2(30, 250, 315, 150), "tenis", "Tênis turbo", "velocidade +", 200, Color("#55d7c0"))
        _draw_item_card(Rect2(375, 250, 315, 150), "mochila", "Mochila", "escudo extra", 180, Color("#f4b84e"))
        _draw_item_card(Rect2(30, 425, 315, 150), "fone", "Fone", "ímã de moedas", 220, Color("#9b77e8"))
        _draw_item_card(Rect2(375, 425, 315, 150), "cafe", "Café térmico", "slow-motion", 150, Color("#c68053"))
        _draw_item_card(Rect2(30, 600, 315, 150), "confete", "Kit confete", "efeito visual", 120, Color("#ef5d9b"))
        _draw_item_card(Rect2(375, 600, 315, 150), "placa", "Placa VIP", "placa decorativa", 300, Color("#6aa9de"))
        _panel(Rect2(30, 800, 660, 250), Color("#1c2d49"), 18)
        _text(Vector2(58, 850), "BILHETE DOURADO", 23, YELLOW)
        _text(Vector2(58, 886), "coletado nas pistas, desbloqueia a skin Caramelo", 16, MUTED)
        _text(Vector2(58, 930), "Dica: procure os bônus depois das rampas.", 18, WHITE)
        _text(Vector2(58, 985), "Seu personagem equipado: " + _character_name(GameSave.equipped_character()), 17, Color("#8ee5bb"))
    _button(Rect2(45, 1135, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_character_card(rect: Rect2, id: String, title: String, subtitle: String, price: int, color: Color) -> void:
    var owned := GameSave.owns(id)
    var equipped := GameSave.equipped_character() == id
    _panel(rect, Color("#223655") if owned else Color("#19273f"), 15)
    _draw_runner(rect.position + Vector2(68, 82), 0.46, false, id)
    _text(rect.position + Vector2(130, 38), title, 22, WHITE)
    _text(rect.position + Vector2(130, 67), subtitle, 15, MUTED)
    var label := "EQUIPADO" if equipped else ("USAR" if owned else "R$ %d" % price)
    _button(Rect2(rect.end.x - 150, rect.position.y + 34, 125, 55), label, color if not equipped else GREEN, 16)

func _draw_item_card(rect: Rect2, id: String, title: String, subtitle: String, price: int, color: Color) -> void:
    var owned := GameSave.owns(id)
    _panel(rect, Color("#223655") if owned else Color("#19273f"), 15)
    _text(rect.position + Vector2(22, 42), title, 21, WHITE)
    _text(rect.position + Vector2(22, 70), subtitle, 15, MUTED)
    _button(Rect2(rect.end.x - 126, rect.position.y + 42, 105, 52), "OK" if owned else "R$ %d" % price, color, 15)

func _shop_tap(pos: Vector2) -> void:
    var chars := [["ze", 0], ["maria", 180], ["motoboy", 260], ["julia", 360], ["carlos", 440], ["influencer", 420]]
    var items := [["tenis", 200], ["mochila", 180], ["fone", 220], ["cafe", 150], ["confete", 120], ["placa", 300]]
    if shop_tab == 0:
        for i in chars.size():
            var rect := Rect2(30, 250 + i * 145, 660, 126)
            if rect.has_point(pos):
                var id: String = chars[i][0]
                var price: int = chars[i][1]
                if GameSave.owns(id):
                    GameSave.equip_character(id)
                    _feedback("EQUIPADO!", _character_name(id), CORAL, "ui_confirm", pos, 0.12, 0.04)
                    _show_toast(_character_name(id) + " equipado!")
                elif GameSave.unlock(id, price):
                    GameSave.equip_character(id)
                    _feedback("DESBLOQUEADO!", _character_name(id), GOLD, "reward", pos, 0.28, 0.07)
                    _show_toast("Desbloqueado: " + _character_name(id))
                else:
                    _feedback("FALTAM MOEDAS", "Continue correndo para comprar", CORAL, "ui_back", pos, 0.0, 0.04)
                    _show_toast("Ainda faltam moedas de passagem.")
                return
    else:
        for i in items.size():
            var col := i % 2
            var row := int(float(i) / 2.0)
            var rect := Rect2(30 + col * 345, 250 + row * 175, 315, 150)
            if rect.has_point(pos):
                var id: String = items[i][0]
                var price: int = items[i][1]
                if GameSave.unlock(id, price):
                    _feedback("ITEM ADQUIRIDO!", id.to_upper() + " entrou no corre", GOLD, "reward", pos, 0.2, 0.05)
                    _show_toast("Item na mochila: " + id)
                else:
                    _feedback("FALTAM MOEDAS", "Junte mais R$ da passagem", CORAL, "ui_back", pos, 0.0, 0.04)
                    _show_toast("Junte mais R$ da passagem.")
                return

func _draw_achievements() -> void:
    _draw_ui_background()
    _header("CONQUISTAS", "%d / 8" % (GameSave.data["achievements"].size() + GameSave.badge_count()))
    _text(Vector2(30, 126), "Histórias que merecem um vídeo curto.", 17, MUTED)
    var ach := [
        ["busao", "Peguei o busão!", "zerar o primeiro arco", Color("#ffd34e")],
        ["enchente", "Sobrevivi à enchente", "Tela 9 sem levar dano", Color("#63c8ed")],
        ["dog", "Cachorro caramelo me pegou", "ser pego pelo dog 10x", Color("#c9824c")],
        ["wallrun", "Jeitinho brasileiro", "3 wall-runs numa fase", Color("#55d7c0")],
        ["idle", "Só mais um pouquinho", "ficar 30s no ponto", Color("#d092e5")],
        ["busao50", "Brasil sem freio", "vencer a Tela 50", Color("#ff7b63")],
        ["combo15", "Combo de respeito", "15 moedas sem quebrar", Color("#71e7c8")],
        ["maratonista", "Maratonista do ponto", "fechar a expansão", Color("#d9a2ff")]
    ]
    for i in ach.size():
        var y := 160.0 + i * 118.0
        var unlocked: bool = GameSave.has_achievement(str(ach[i][0])) or (ach[i][0] in GameSave.data.get("badges", []))
        _panel(Rect2(35, y, 650, 104), Color("#26435a") if unlocked else Color("#19273f"), 17)
        _panel(Rect2(57, y + 17, 58, 58), ach[i][3] if unlocked else Color("#37465a"), 16)
        _text_center(Vector2(86, y + 54), "★" if unlocked else "?", 30, UI_BG if unlocked else MUTED)
        _text(Vector2(140, y + 38), ach[i][1], 19, WHITE if unlocked else MUTED)
        _text(Vector2(140, y + 68), ach[i][2], 14, Color("#9ab1c5"))
        _text(Vector2(565, y + 55), "FEITO" if unlocked else "BLOQUEADO", 12, GREEN if unlocked else MUTED)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_daily() -> void:
    _draw_ui_background()
    _header("DESAFIOS DIÁRIOS", "R$ %03d" % GameSave.coins())
    _text(Vector2(30, 126), "Três missões curtinhas. Volte amanhã para renovar.", 16, MUTED)
    var key := Time.get_date_string_from_system()
    var completed: Array = GameSave.get_daily_completed()
    if GameSave.data.get("daily_date", "") != key:
        completed = []
    var progress := GameSave.daily_progress(key)
    var missions := [
        ["Pé na tábua", "corra 250 metros", 25],
        ["Troco certo", "pegue 10 moedas", 35],
        ["Desvia que eu vou", "termine sem dano", 50]
    ]
    for i in missions.size():
        var y := 200.0 + i * 190.0
        var done := i in completed
        var is_ready := _daily_ready(i, progress)
        _panel(Rect2(35, y, 650, 145), Color("#24445a") if done else Color("#1a2a45"), 17)
        _text(Vector2(65, y + 43), missions[i][0], 25, WHITE)
        _text(Vector2(65, y + 78), missions[i][1], 17, MUTED)
        _text(Vector2(65, y + 116), "FEITO" if done else _daily_status(i, progress), 15, GREEN if done else YELLOW)
        _button(Rect2(505, y + 43, 145, 58), "FEITO" if done else ("RESGATAR" if is_ready else "IR"), GREEN if done else (Color("#5dbd7d") if is_ready else Color("#3d7191")), 15)
    _panel(Rect2(45, 800, 630, 165), Color("#1e2f4d"), 18)
    _text(Vector2(75, 850), "SEQUÊNCIA", 17, MUTED)
    _text(Vector2(75, 895), "🔥 %02d dias  •  XP %04d" % [int(GameSave.data.get("daily_streak", 0)), GameSave.xp()], 25, Color("#ffbd6e"))
    _text(Vector2(75, 930), "7 dias seguidos rendem +R$ 100 automático", 17, Color("#8ee5bb"))
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _daily_ready(index: int, progress: Dictionary) -> bool:
    match index:
        0:
            return int(progress.get("meters", 0)) >= 250
        1:
            return int(progress.get("coins", 0)) >= 10
        2:
            return bool(progress.get("clean", false))
    return false

func _daily_status(index: int, progress: Dictionary) -> String:
    match index:
        0:
            return "%dm / 250m" % mini(int(progress.get("meters", 0)), 250)
        1:
            return "%d / 10 moedas" % mini(int(progress.get("coins", 0)), 10)
        2:
            return "termine uma corrida sem dano" if not bool(progress.get("clean", false)) else "pronto para resgatar"
    return ""

func _claim_daily(index: int) -> void:
    var key := Time.get_date_string_from_system()
    var completed: Array = GameSave.get_daily_completed()
    if GameSave.data.get("daily_date", "") != key:
        completed = []
    if index in completed:
        _ui_feedback(Vector2(360, 650), "JÁ RESGATADO", "Volte amanhã para novos desafios", MUTED, "ui_back")
        return
    var progress := GameSave.daily_progress(key)
    if not _daily_ready(index, progress):
        _feedback("QUASE LÁ!", "Complete a missão antes de resgatar", CORAL, "ui_back", Vector2(360, 650), 0.0, 0.04)
        _show_toast("Complete a missão antes de resgatar.")
        return
    completed.append(index)
    var reward := 25 + index * 10
    GameSave.set_daily_completed(completed, key, reward)
    _feedback("RECOMPENSA!", "+R$ %d • desafio concluído" % reward, GOLD, "reward", Vector2(360, 650), 0.35, 0.08)
    _spawn_confetti(18)
    _show_toast("Desafio completo! Recompensa recebida.")

func _draw_how_to() -> void:
    _draw_ui_background()
    _header("COMO JOGAR", "GUIA RÁPIDO")
    _panel(Rect2(35, 145, 650, 400), Color("#1e3150"), 20)
    _text(Vector2(68, 198), "CONTROLES", 26, YELLOW)
    _text(Vector2(75, 252), "SWIPE ← →", 24, BLUE)
    _text(Vector2(310, 252), "troca de pista", 20, WHITE)
    _text(Vector2(75, 307), "SWIPE ↑", 24, GREEN)
    _text(Vector2(310, 307), "pula obstáculos", 20, WHITE)
    _text(Vector2(75, 362), "SWIPE ↓", 24, Color("#e99be2"))
    _text(Vector2(310, 362), "desliza por baixo", 20, WHITE)
    _text(Vector2(75, 417), "TOQUE", 24, YELLOW)
    _text(Vector2(310, 417), "dash + invencibilidade", 20, WHITE)
    _text(Vector2(75, 472), "TECLADO", 24, Color("#ff9b73"))
    _text(Vector2(310, 472), "A/D • W/S • X", 20, WHITE)
    _panel(Rect2(35, 580, 650, 390), Color("#1a2a45"), 20)
    _text(Vector2(68, 634), "LEMBRETES DO ZÉ", 26, YELLOW)
    _text(Vector2(68, 688), "• Pão de queijo = pulo mais alto", 19, WHITE)
    _text(Vector2(68, 730), "• Pastel = escudo de 1 hit", 19, WHITE)
    _text(Vector2(68, 772), "• Café = tudo em câmera lenta", 19, WHITE)
    _text(Vector2(68, 814), "• Rampas + ↑ = SUPER PULO", 19, WHITE)
    _text(Vector2(68, 856), "• Parede + ↑ = WALL-RUN", 19, WHITE)
    _text(Vector2(68, 898), "• No ponto, toque PEGAR O BUSÃO", 19, WHITE)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

# -----------------------------------------------------------------------------
# Desenho da corrida
# -----------------------------------------------------------------------------
func _draw_run() -> void:
    _draw_world()
    _draw_hud()
    _draw_entities()
    _draw_player(_lane_x(player_lane), _player_y(), 1.0, GameSave.equipped_character())
    if dog_chase_timer > 0.0:
        _draw_dog(Vector2(_lane_x(player_lane) - 52, GROUND_Y - 50), 0.72, true)
        _text(Vector2(30, 340), "AU AU! %0.1fs" % dog_chase_timer, 17, Color("#ffc17a"))
    if run_mode == "paused":
        _draw_overlay_pause()
    elif run_mode == "at_stop":
        _draw_stop_overlay()
    if toast_timer > 0.0:
        _draw_toast()
    _draw_vignette()

func _draw_world() -> void:
    var sky: Color = phase.get("sky", Color("#80d7ee"))
    var horizon: Color = phase.get("horizon", Color("#f3c56a"))
    _draw_gradient(sky, horizon)
    var weather := str(phase.get("weather", "sol"))
    if weather == "poente":
        _draw_sun(Vector2(575, 300), 65, Color("#ffcb77"))
    elif weather == "noite":
        _draw_sun(Vector2(580, 175), 34, Color("#e2e9ff"))
        for i in 16:
            var sx := float((i * 97 + 40) % 700)
            var sy := float(100 + (i * 43) % 215)
            draw_circle(Vector2(sx, sy), 2.0, Color("#ffeaa8"))
    else:
        _draw_sun(Vector2(570, 205), 48, Color("#ffe09a"))
    _draw_background_scene(str(phase.get("theme", "cidade")))
    # Névoa de horizonte e brilho lateral vendem a sensação de câmera, sem
    # sprites pesados: os polígonos ficam baratos no renderer Compatibility.
    draw_rect(Rect2(0, HORIZON_Y - 18, VIEW.x, 52), Color(1, 0.84, 0.58, 0.10))
    draw_circle(Vector2(360, HORIZON_Y + 8), 120 + sin(pulse * 1.2) * 4.0, Color(0.75, 0.92, 0.92, 0.06))
    var road: Color = phase.get("road", Color("#3b4658"))
    draw_colored_polygon(PackedVector2Array([Vector2(276, HORIZON_Y), Vector2(444, HORIZON_Y), Vector2(700, 1120), Vector2(20, 1120)]), road)
    draw_colored_polygon(PackedVector2Array([Vector2(276, HORIZON_Y), Vector2(257, HORIZON_Y), Vector2(0, 1120), Vector2(20, 1120)]), Color("#c2a36f"))
    draw_colored_polygon(PackedVector2Array([Vector2(444, HORIZON_Y), Vector2(463, HORIZON_Y), Vector2(720, 1120), Vector2(700, 1120)]), Color("#c2a36f"))
    # Faixas e linhas convergentes dão sensação de velocidade em 2D.
    for lane in [0, 1]:
        var near_x: float = 302.0 + float(lane) * 116.0
        var far_x: float = 333.0 + float(lane) * 54.0
        draw_dashed_line(Vector2(far_x, HORIZON_Y + 4), Vector2(near_x, 1120), Color("#c9d4d3"), 4.0, 30.0)
    draw_line(Vector2(276, HORIZON_Y), Vector2(20, 1120), Color("#ead59b"), 5.0)
    draw_line(Vector2(444, HORIZON_Y), Vector2(700, 1120), Color("#ead59b"), 5.0)
    # Marcas rápidas em perspectiva fazem o cenário respirar junto com o jogador.
    for mark in 8:
        var mark_z := fmod(float(mark) * 11.0 + distance * 0.52, VISIBLE_Z)
        var mark_depth := 1.0 - mark_z / VISIBLE_Z
        var mark_y := lerpf(HORIZON_Y + 28.0, 1110.0, mark_depth)
        var mark_half := lerpf(3.0, 19.0, mark_depth)
        draw_line(Vector2(360.0 - mark_half, mark_y), Vector2(360.0 + mark_half, mark_y), Color(1, 0.92, 0.65, 0.20 + mark_depth * 0.32), 2.0 + mark_depth * 2.0)
    if dash_timer > 0.0:
        for streak in 11:
            var streak_y := float(190 + (streak * 79 + int(pulse * 260.0)) % 900)
            var streak_x := float((streak * 113) % 720)
            draw_line(Vector2(streak_x, streak_y), Vector2(streak_x - 38, streak_y + 10), Color(1.0, 0.86, 0.38, 0.18), 2.0)
    if weather == "chuva":
        for i in 30:
            var rx := float((i * 71 + int(elapsed * 160)) % 760 - 20)
            var ry := float(370 + (i * 53) % 710)
            draw_line(Vector2(rx, ry), Vector2(rx - 8, ry + 26), Color(0.72, 0.88, 0.97, 0.55), 2.0)
    if weather == "poeira":
        for i in 12:
            var px := float((i * 83 + int(elapsed * 15)) % 700)
            draw_circle(Vector2(px, 830 + (i * 29) % 210), 3.0 + (i % 3), Color(0.86, 0.69, 0.48, 0.35))
    elif weather == "neon":
        for i in 18:
            var glow_x := float((i * 61 + int(elapsed * 45)) % 740)
            draw_circle(Vector2(glow_x, 180 + (i * 37) % 245), 2.0 + (i % 2), Color("#65edcf"))
    elif weather == "confete":
        for i in 16:
            var conf_x := float((i * 47 + int(elapsed * 35)) % 720)
            draw_rect(Rect2(conf_x, 220 + (i * 41) % 230, 5, 12), [Color("#f54291"), Color("#ffd34e"), Color("#55d7c0")][i % 3])
    elif weather == "cinzas":
        for i in 18:
            var ash_x := float((i * 77 + int(elapsed * 12)) % 720)
            draw_circle(Vector2(ash_x, 160 + (i * 43) % 300), 2.5, Color(0.7, 0.7, 0.7, 0.45))

func _draw_background_scene(theme: String) -> void:
    match theme:
        "cidade":
            _draw_city_silhouette(0.72)
            for i in 5:
                _draw_tree(Vector2(55 + i * 145, 365), 0.5 + (i % 2) * 0.1)
        "noite":
            _draw_city_silhouette(0.9)
            for i in 7:
                draw_circle(Vector2(35 + i * 112, 364), 16, Color("#235a62"))
        "chuva":
            _draw_city_silhouette(0.6)
            _text(Vector2(35, 335), "RUA ALAGADA", 15, Color("#b6e0e4"))
            for i in 5:
                _draw_wave(Vector2(40 + i * 150, 360), 0.6)
        "verde":
            for i in 6:
                _draw_tree(Vector2(40 + i * 130, 362), 0.72)
            _text(Vector2(35, 330), "PARQUE / ORLA", 15, Color("#e9f0b3"))
        "carnaval":
            for i in 11:
                var cx := float(20 + i * 70)
                draw_line(Vector2(cx, 215), Vector2(cx, 370), Color("#e34885"), 2)
                draw_circle(Vector2(cx, 215), 9, [Color("#f8d557"), Color("#54d7c0"), Color("#ef6c64")][i % 3])
            _text(Vector2(265, 340), "BLOCO DOS ATRASADOS", 18, Color("#ffe79a"))
        "interior":
            _draw_tree(Vector2(110, 345), 0.9)
            _draw_tree(Vector2(610, 350), 0.8)
            _text(Vector2(42, 331), "BEM-VINDO AO INTERIOR", 14, Color("#fff1bf"))
            draw_line(Vector2(535, 270), Vector2(625, 330), Color("#444654"), 2)
            draw_line(Vector2(580, 300), Vector2(580, 356), Color("#444654"), 2)
        "terminal":
            _draw_terminal()
        "historico":
            _draw_church()
            for i in 3:
                draw_circle(Vector2(85 + i * 230, 346), 18, Color("#ecd5b2"))
                _text(Vector2(70 + i * 230, 368), "foto!", 11, Color("#3d526b"))
        "industria":
            _draw_factory()
        "tecnologia", "futuro":
            _draw_city_silhouette(0.82)
            for i in 8:
                var neon_x := float(15 + i * 96)
                draw_line(Vector2(neon_x, 250 + (i % 3) * 28), Vector2(neon_x + 54, 350), Color("#5debd1"), 3)
                draw_circle(Vector2(neon_x + 54, 350), 5, Color("#ef6cd2"))
            _text(Vector2(230, 338), "BOTECO 2.0", 17, Color("#72f2d3"))
        "festival":
            _draw_city_silhouette(0.55)
            for i in 11:
                var cx := float(20 + i * 70)
                draw_line(Vector2(cx, 210), Vector2(cx, 370), Color("#e34885"), 2)
                draw_circle(Vector2(cx, 210), 10, [Color("#f8d557"), Color("#54d7c0"), Color("#ef6c64")][i % 3])
            _text(Vector2(240, 340), "BRASIL FEST", 18, Color("#ffe79a"))
        "agua":
            _draw_tree(Vector2(80, 360), 0.65)
            _draw_tree(Vector2(630, 360), 0.65)
            for i in 5:
                _draw_wave(Vector2(35 + i * 150, 360), 0.7)
            _text(Vector2(280, 335), "ÁGUA, MAS SEM CALMA", 15, Color("#e9ffff"))
        "sertao":
            _draw_tree(Vector2(100, 355), 0.8)
            _draw_tree(Vector2(620, 355), 0.7)
            draw_rect(Rect2(530, 300, 14, 70), Color("#4f8a4f"))
            draw_circle(Vector2(537, 297), 27, Color("#5a9b51"))
            _text(Vector2(230, 335), "ESTRADA DO FORRÓ", 17, Color("#fff0b0"))
        "apocalipse":
            _draw_factory()
            _draw_city_silhouette(0.5)
            _text(Vector2(250, 340), "CALMA, É SÓ MAIS UMA", 15, Color("#ffcf59"))
        "remix", "final":
            _draw_city_silhouette(0.85)
            _draw_tree(Vector2(80, 350), 0.6)
            _draw_factory()
            _text(Vector2(250, 338), "TUDO AO MESMO TEMPO", 15, Color("#ffe49a"))
        _:
            _draw_city_silhouette(0.7)

func _draw_entities() -> void:
    for entity in entities:
        var z: float = float(entity["z"])
        if z < -3.0 or z > VISIBLE_Z:
            continue
        var depth := 1.0 - clampf(z / VISIBLE_Z, 0.0, 1.0)
        var x := _world_lane_x(int(entity["lane"]), depth)
        var y := lerpf(HORIZON_Y + 22.0, GROUND_Y, depth)
        var depth_scale := 0.28 + depth * 0.95
        var kind := str(entity["kind"])
        if kind in COLLECTIBLE_NAMES:
            draw_circle(Vector2(x, y - 4), 34.0 * depth_scale, Color(1.0, 0.82, 0.28, 0.07 + depth * 0.08))
        else:
            _ellipse(Vector2(x, y + 4), 30.0 * depth_scale, 7.0 * depth_scale, Color(0.02, 0.04, 0.08, 0.20 + depth * 0.16))
        if kind in COLLECTIBLE_NAMES:
            _draw_collectible(kind, Vector2(x, y - 62.0 * depth_scale), depth_scale)
        elif kind == "dog":
            _draw_dog(Vector2(x, y - 40.0 * depth_scale), depth_scale, false)
        elif kind == "wall":
            _draw_wall(Vector2(x, y), depth_scale, int(entity["lane"]) == 0)
        elif kind == "ramp":
            _draw_ramp(Vector2(x, y), depth_scale)
        else:
            _draw_obstacle(kind, Vector2(x, y), depth_scale)

func _draw_hud() -> void:
    draw_rect(Rect2(0, 0, 720, 128), Color(0.025, 0.055, 0.12, 0.94))
    draw_rect(Rect2(0, 124, 720, 4), Color(phase["accent"], 0.55))
    _text(Vector2(24, 36), "%02d  %s" % [phase_index + 1, str(phase["name"]).to_upper()], 18, WHITE)
    _text(Vector2(24, 69), str(phase["location"]), 13, MUTED)
    _panel(Rect2(246, 17, 148, 70), Color("#152b4a"), 17)
    _text(Vector2(264, 43), "%03d m" % int(distance), 22, YELLOW)
    _text(Vector2(264, 70), "R$ %02d" % collected_coins, 15, Color("#8ee5bb"))
    if combo > 1:
        _panel(Rect2(246, 92, 220, 27), Color(1, 0.63, 0.25, 0.14), 10)
        _text(Vector2(258, 112), "COMBO x%02d  •  %04d pts" % [combo, run_score], 12, GOLD)
    var hearts_text := "♥".repeat(hearts) + "♡".repeat(maxi(0, max_hearts - hearts))
    _text(Vector2(474, 42), hearts_text, 24, RED)
    _text(Vector2(474, 70), "%0.1f m/s" % float(phase["speed"]), 13, Color("#d9e3f0"))
    _panel(Rect2(620, 25, 72, 58), Color("#203a60"), 12)
    _text_center(Vector2(656, 61), "Ⅱ" if run_mode == "paused" else "▮▮", 21, WHITE)
    var bar := clampf(distance / run_total, 0.0, 1.0)
    draw_rect(Rect2(22, 116, 676, 6), Color("#0c1a30"))
    draw_rect(Rect2(22, 116, 676 * bar, 6), phase["accent"])
    draw_rect(Rect2(22, 116, minf(676 * bar, 90.0), 6), Color(1, 1, 1, 0.22))
    if jump_timer > 0.0:
        _panel(Rect2(24, 137, 142, 34), Color(0.33, 0.86, 0.82, 0.16), 12)
        _text(Vector2(39, 160), "PULO" if not super_jump else "SUPER PULO", 13, GREEN if not super_jump else YELLOW)
    if slide_timer > 0.0:
        _panel(Rect2(24, 137, 166, 34), Color(0.67, 0.55, 1.0, 0.16), 12)
        _text(Vector2(39, 160), "DESLIZANDO", 13, VIOLET)
    var dash_label := "DASH PRONTO" if dash_cooldown <= 0.0 else "DASH %0.1f" % dash_cooldown
    _panel(Rect2(518, 137, 178, 34), Color(1, 0.72, 0.24, 0.13), 12)
    _text(Vector2(535, 160), dash_label, 13, YELLOW if dash_cooldown <= 0.0 else MUTED)
    _panel(Rect2(20, 1192, 680, 48), Color(0.025, 0.055, 0.12, 0.76), 16)
    _text_center(Vector2(360, 1222), "← → PISTA     ↑ PULO     ↓ DESLIZA     TOQUE DASH", 14, Color(0.87, 0.93, 0.95, 0.82))

func _draw_overlay_pause() -> void:
    draw_rect(Rect2(0, 0, 720, 1280), Color(0.02, 0.04, 0.08, 0.76))
    _panel(Rect2(65, 470, 590, 285), Color("#172541"), 24)
    _text_center(Vector2(360, 545), "PAUSA NO PONTO", 34, YELLOW)
    _text_center(Vector2(360, 590), "Respira. O busão ainda não viu.", 19, MUTED)
    _button(Rect2(80, 635, 560, 82), "CONTINUAR", Color("#54a979"), 24)

func _draw_stop_overlay() -> void:
    draw_rect(Rect2(0, 200, 720, 850), Color(0.03, 0.06, 0.11, 0.50))
    draw_circle(Vector2(505, 375), 165 + sin(pulse * 4.0) * 10.0, Color(1.0, 0.72, 0.24, 0.08))
    _draw_bus(Vector2(505, 375), 0.78, false)
    _draw_bus_stop(Vector2(210, 370), 0.85)
    _panel(Rect2(45, 660, 630, 290), Color("#122945"), 22)
    _text_center(Vector2(360, 715), "CHEGOU NO PONTO!", 31, YELLOW)
    _text_center(Vector2(360, 755), "o ônibus sai em", 18, MUTED)
    _text_center(Vector2(360, 805), "%0.1f s" % stop_wait, 42, RED if stop_wait < 3.0 else WHITE)
    draw_rect(Rect2(105, 820, 510, 5), Color("#2b3c58"))
    draw_rect(Rect2(105, 820, 510 * clampf(stop_wait / maxf(stop_wait_total, 0.01), 0.0, 1.0), 5), YELLOW if stop_wait > 3.0 else RED)
    _button(Rect2(70, 835, 580, 86), "PEGAR O BUSÃO", Color("#f0b83f"), 25)

func _draw_toast() -> void:
    var width := minf(650.0, 92.0 + toast.length() * 7.4)
    var rect := Rect2((720.0 - width) / 2.0, 205 if screen == 2 else 180, width, 58)
    _panel(rect, Color("#132946"), 17)
    draw_rect(Rect2(rect.position, Vector2(6, rect.size.y)), feedback_color)
    _text_center(rect.position + Vector2(width / 2.0 + 4, 36), toast, 16, WHITE)

func _player_y() -> float:
    var air := 0.0
    if jump_timer > 0.0:
        var progress := 1.0 - jump_timer / maxf(jump_duration, 0.01)
        air = sin(progress * PI) * (185.0 if super_jump else (130.0 if jump_boost_timer > 0.0 else 105.0))
    return GROUND_Y - air

func _lane_x(lane: int) -> float:
    return 302.0 + clampi(lane, 0, 2) * 116.0

func _world_lane_x(lane: int, depth: float) -> float:
    var far := 333.0 + clampi(lane, 0, 2) * 27.0
    var near := _lane_x(lane)
    return lerpf(far, near, depth)

# -----------------------------------------------------------------------------
# Ilustrações vetoriais reutilizáveis
# -----------------------------------------------------------------------------
func _draw_vignette() -> void:
    draw_colored_polygon(PackedVector2Array([Vector2(0, 0), Vector2(130, 0), Vector2(84, VIEW.y), Vector2(0, VIEW.y)]), Color(0.01, 0.025, 0.07, 0.14))
    draw_colored_polygon(PackedVector2Array([Vector2(VIEW.x, 0), Vector2(VIEW.x - 130, 0), Vector2(VIEW.x - 84, VIEW.y), Vector2(VIEW.x, VIEW.y)]), Color(0.01, 0.025, 0.07, 0.14))
    draw_rect(Rect2(0, VIEW.y - 62, VIEW.x, 62), Color(0.01, 0.025, 0.07, 0.12))

func _draw_gradient(top: Color, bottom: Color) -> void:
    for i in 16:
        var t := float(i) / 15.0
        draw_rect(Rect2(0, i * 80, 720, 82), top.lerp(bottom, t))

func _draw_ui_background() -> void:
    _draw_gradient(Color("#081329"), Color("#173858"))
    for i in 8:
        draw_circle(Vector2(40 + i * 102, 1060 - (i % 3) * 55), 95, Color(0.09, 0.25, 0.34, 0.18))
    for i in 7:
        var grid_y := 170.0 + i * 150.0
        draw_line(Vector2(0, grid_y), Vector2(720, grid_y - 92), Color(0.45, 0.78, 0.84, 0.045), 1.0)
    draw_circle(Vector2(610, 215), 160 + sin(pulse) * 8.0, Color(0.23, 0.63, 0.78, 0.055))
    draw_rect(Rect2(0, 0, 720, 8), Color(0.39, 0.88, 0.82, 0.52))

func _header(title: String, right: String) -> void:
    draw_rect(Rect2(0, 0, 720, 112), Color(0.025, 0.055, 0.12, 0.94))
    draw_rect(Rect2(0, 108, 720, 4), Color(0.32, 0.82, 0.84, 0.45))
    _panel(Rect2(18, 27, 54, 58), Color("#1c3556"), 18)
    _text_center(Vector2(45, 67), "‹", 39, YELLOW)
    _text(Vector2(92, 48), title, 25, WHITE)
    _text(Vector2(92, 76), "CORRE PRO PONTO", 13, MUTED)
    _panel(Rect2(492, 28, 205, 54), Color("#152a49"), 18)
    _text_center(Vector2(594, 62), right, 17, YELLOW)

func _panel(rect: Rect2, color: Color, radius: float = 12.0) -> void:
    var shadow_rect := Rect2(rect.position + Vector2(0, 6), rect.size)
    draw_style_box(_make_box(SHADOW, radius), shadow_rect)
    draw_style_box(_make_box(color, radius), rect)
    if rect.size.x > radius * 2.0:
        draw_line(rect.position + Vector2(radius, 1), Vector2(rect.end.x - radius, rect.position.y + 1), Color(1, 1, 1, 0.12), 1.0)

func _button(rect: Rect2, label: String, color: Color, size: int = 20) -> void:
    _panel(rect, color, 15)
    draw_rect(Rect2(rect.position + Vector2(3, 3), Vector2(rect.size.x - 6, 4)), Color(1, 1, 1, 0.12))
    draw_line(rect.position + Vector2(14, rect.size.y - 6), rect.end - Vector2(14, 6), Color(0.02, 0.05, 0.1, 0.22), 2)
    _text_center(rect.position + rect.size / 2.0 + Vector2(0, 3), label, size, UI_INK if color != Color("#293955") and color != Color("#263958") else WHITE)

func _make_box(color: Color, radius: float) -> StyleBoxFlat:
    var box := StyleBoxFlat.new()
    box.bg_color = color
    box.corner_radius_top_left = int(radius)
    box.corner_radius_top_right = int(radius)
    box.corner_radius_bottom_left = int(radius)
    box.corner_radius_bottom_right = int(radius)
    box.border_width_left = 1
    box.border_width_top = 1
    box.border_width_right = 1
    box.border_width_bottom = 1
    box.border_color = Color(1, 1, 1, 0.10)
    return box

func _text(pos: Vector2, value: String, size: int, color: Color) -> void:
    draw_string(ThemeDB.fallback_font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _text_center(pos: Vector2, value: String, size: int, color: Color) -> void:
    var width := maxf(100.0, float(value.length() * size) * 0.72)
    draw_string(ThemeDB.fallback_font, Vector2(pos.x - width / 2.0, pos.y), value, HORIZONTAL_ALIGNMENT_CENTER, width, size, color)

func _ellipse(center: Vector2, rx: float, ry: float, color: Color) -> void:
    var points := PackedVector2Array()
    for i in 24:
        var angle := TAU * float(i) / 24.0
        points.append(center + Vector2(cos(angle) * rx, sin(angle) * ry))
    draw_colored_polygon(points, color)

func _draw_sun(pos: Vector2, radius: float, color: Color) -> void:
    draw_circle(pos, radius + 14, Color(color, 0.14))
    draw_circle(pos, radius, color)

func _draw_city_silhouette(alpha: float) -> void:
    var building := Color(0.08, 0.18, 0.28, alpha)
    var x := 0.0
    var i := 0
    while x < 720:
        var w := 48.0 + float((i * 17) % 32)
        var h := 80.0 + float((i * 43) % 130)
        draw_rect(Rect2(x, HORIZON_Y - h, w, h), building)
        for row in 3:
            for col in 2:
                if (row + col + i) % 2 == 0:
                    draw_rect(Rect2(x + 10 + col * 18, HORIZON_Y - h + 18 + row * 26, 8, 10), Color(1.0, 0.83, 0.45, alpha * 0.65))
        x += w + 7
        i += 1

func _draw_tree(pos: Vector2, object_scale: float) -> void:
    draw_rect(Rect2(pos.x - 7 * object_scale, pos.y, 14 * object_scale, 62 * object_scale), Color("#67452f"))
    draw_circle(pos + Vector2(-25, -15) * object_scale, 31 * object_scale, Color("#2e8b5b"))
    draw_circle(pos + Vector2(10, -30) * object_scale, 38 * object_scale, Color("#3ba66a"))
    draw_circle(pos + Vector2(35, -5) * object_scale, 27 * object_scale, Color("#287e58"))

func _draw_wave(pos: Vector2, object_scale: float) -> void:
    for i in 4:
        draw_arc(pos + Vector2(i * 30, 0) * object_scale, 25 * object_scale, 0, PI, 16, Color("#6bbdcc"), 4 * object_scale)

func _draw_terminal() -> void:
    draw_rect(Rect2(35, 255, 650, 130), Color("#26384c"))
    draw_rect(Rect2(48, 275, 620, 10), Color("#e3b548"))
    for i in 5:
        draw_rect(Rect2(70 + i * 125, 295, 75, 70), Color("#81b8bf"))
        draw_line(Vector2(78 + i * 125, 302), Vector2(135 + i * 125, 302), Color("#eaf2de"), 3)
    _text(Vector2(250, 253), "TERMINAL CENTRAL", 17, Color("#fff2bf"))

func _draw_church() -> void:
    draw_colored_polygon(PackedVector2Array([Vector2(235, 370), Vector2(300, 250), Vector2(365, 370)]), Color("#e6c493"))
    draw_rect(Rect2(254, 315, 92, 55), Color("#dcae76"))
    draw_rect(Rect2(280, 335, 38, 35), Color("#5a6c82"))
    draw_rect(Rect2(360, 275, 30, 95), Color("#d8b47e"))
    draw_colored_polygon(PackedVector2Array([Vector2(355, 275), Vector2(375, 235), Vector2(395, 275)]), Color("#d8b47e"))
    _text(Vector2(42, 338), "CENTRO HISTÓRICO", 15, Color("#fff2bf"))

func _draw_factory() -> void:
    draw_rect(Rect2(40, 278, 180, 104), Color("#555e63"))
    draw_rect(Rect2(440, 300, 240, 82), Color("#535d61"))
    for x in [80, 125, 170, 480, 540, 600]:
        draw_rect(Rect2(x, 310, 22, 25), Color("#f0b756"))
    draw_rect(Rect2(165, 190, 28, 100), Color("#4c545a"))
    draw_rect(Rect2(525, 215, 35, 95), Color("#4c545a"))
    _ellipse(Vector2(178, 178), 33, 16, Color(0.7, 0.74, 0.72, 0.22))
    _ellipse(Vector2(543, 202), 40, 18, Color(0.7, 0.74, 0.72, 0.20))

func _draw_obstacle(kind: String, pos: Vector2, object_scale: float) -> void:
    var x := pos.x
    var y := pos.y
    var s := object_scale
    match kind:
        "trash":
            draw_rect(Rect2(x - 25 * s, y - 64 * s, 50 * s, 64 * s), Color("#3b5b63"))
            draw_rect(Rect2(x - 31 * s, y - 72 * s, 62 * s, 11 * s), Color("#243c48"))
            _text_center(Vector2(x, y - 30 * s), "MIAU" if int(elapsed * 3.0) % 4 == 0 else "", int(12 * s + 5), Color("#f4d28c"))
        "bench":
            draw_rect(Rect2(x - 47 * s, y - 42 * s, 94 * s, 13 * s), Color("#9a633d"))
            draw_rect(Rect2(x - 43 * s, y - 68 * s, 86 * s, 18 * s), Color("#aa7045"))
            draw_line(Vector2(x - 30 * s, y - 28 * s), Vector2(x - 40 * s, y + 3 * s), Color("#30353d"), 8 * s)
            draw_line(Vector2(x + 30 * s, y - 28 * s), Vector2(x + 40 * s, y + 3 * s), Color("#30353d"), 8 * s)
            _ellipse(Vector2(x, y - 77 * s), 15 * s, 13 * s, Color("#ca8d67"))
            _text_center(Vector2(x, y - 94 * s), "Zz", int(13 * s + 5), Color("#fff2bd"))
        "puddle":
            _ellipse(Vector2(x, y - 6 * s), 68 * s, 18 * s, Color("#3d9aa8"))
            _ellipse(Vector2(x - 18 * s, y - 12 * s), 24 * s, 6 * s, Color(0.65, 0.92, 0.94, 0.65))
        "fridge":
            draw_rect(Rect2(x - 31 * s, y - 82 * s, 62 * s, 82 * s), Color("#dfe5df"))
            draw_rect(Rect2(x - 28 * s, y - 78 * s, 56 * s, 34 * s), Color("#a9cad0"))
            draw_line(Vector2(x - 25 * s, y - 40 * s), Vector2(x + 25 * s, y - 40 * s), Color("#8ca5a9"), 3 * s)
            draw_circle(Vector2(x + 18 * s, y - 27 * s), 3 * s, Color("#5b6b70"))
            _text_center(Vector2(x, y - 96 * s), "BOIANDO", int(9 * s + 3), WHITE)
        "cyclist":
            draw_circle(Vector2(x - 22 * s, y - 5 * s), 18 * s, Color("#202c3c"), false, 5 * s)
            draw_circle(Vector2(x + 25 * s, y - 5 * s), 18 * s, Color("#202c3c"), false, 5 * s)
            draw_line(Vector2(x - 22 * s, y - 5 * s), Vector2(x + 3 * s, y - 38 * s), Color("#e15c4f"), 5 * s)
            draw_line(Vector2(x + 3 * s, y - 38 * s), Vector2(x + 25 * s, y - 5 * s), Color("#e15c4f"), 5 * s)
            draw_circle(Vector2(x + 3 * s, y - 57 * s), 13 * s, Color("#d8916b"))
            draw_line(Vector2(x - 4 * s, y - 45 * s), Vector2(x - 25 * s, y - 20 * s), Color("#4e8cc6"), 8 * s)
        "cone":
            draw_colored_polygon(PackedVector2Array([Vector2(x, y - 88 * s), Vector2(x - 31 * s, y), Vector2(x + 31 * s, y)]), Color("#f0783f"))
            draw_rect(Rect2(x - 38 * s, y - 9 * s, 76 * s, 10 * s), Color("#e8d4ae"))
            draw_rect(Rect2(x - 24 * s, y - 40 * s, 48 * s, 9 * s), Color("#f5d17b"))
            _text_center(Vector2(x, y - 103 * s), "TRRR", int(10 * s + 3), Color("#fff2af"))
        "sign":
            draw_rect(Rect2(x - 9 * s, y - 82 * s, 18 * s, 82 * s), Color("#858b87"))
            draw_rect(Rect2(x - 58 * s, y - 112 * s, 116 * s, 40 * s), Color("#efc94e"))
            _text_center(Vector2(x, y - 84 * s), "RUA", int(13 * s + 4), Color("#38465c"))
        "phone":
            _ellipse(Vector2(x, y - 30 * s), 27 * s, 38 * s, Color("#e5a17b"))
            draw_rect(Rect2(x - 16 * s, y - 71 * s, 32 * s, 53 * s), Color("#1d344e"))
            draw_rect(Rect2(x - 10 * s, y - 64 * s, 20 * s, 35 * s), Color("#7bd2d0"))
            _text_center(Vector2(x, y - 90 * s), "ZIG", int(10 * s + 3), YELLOW)
        "motoboy":
            draw_circle(Vector2(x, y - 78 * s), 20 * s, Color("#d9916c"))
            _ellipse(Vector2(x, y - 95 * s), 28 * s, 12 * s, Color("#ed4e45"))
            draw_rect(Rect2(x - 25 * s, y - 59 * s, 50 * s, 50 * s), Color("#e84d4b"))
            draw_line(Vector2(x - 20 * s, y - 8 * s), Vector2(x - 35 * s, y + 1 * s), Color("#d9916c"), 8 * s)
            draw_line(Vector2(x + 20 * s, y - 8 * s), Vector2(x + 35 * s, y + 1 * s), Color("#d9916c"), 8 * s)
            _text_center(Vector2(x, y - 120 * s), "SAI!", int(11 * s + 4), Color("#fff2b0"))
        "vendor":
            draw_rect(Rect2(x - 50 * s, y - 68 * s, 100 * s, 60 * s), Color("#e2a846"))
            draw_colored_polygon(PackedVector2Array([Vector2(x - 63 * s, y - 68 * s), Vector2(x, y - 106 * s), Vector2(x + 63 * s, y - 68 * s)]), Color("#e85463"))
            draw_circle(Vector2(x + 4 * s, y - 39 * s), 13 * s, Color("#ce8e6e"))
            _text_center(Vector2(x, y - 82 * s), "OLHA O", int(10 * s + 3), WHITE)
        "pigeon":
            draw_circle(Vector2(x, y - 38 * s), 20 * s, Color("#a4adad"))
            draw_colored_polygon(PackedVector2Array([Vector2(x - 12 * s, y - 40 * s), Vector2(x - 53 * s, y - 69 * s), Vector2(x - 33 * s, y - 22 * s)]), Color("#7d9098"))
            draw_circle(Vector2(x + 7 * s, y - 44 * s), 3 * s, Color("#151c29"))
            _text_center(Vector2(x, y - 88 * s), "POMBO!", int(10 * s + 3), WHITE)
        "scooter":
            draw_circle(Vector2(x - 25 * s, y - 5 * s), 12 * s, Color("#202b3a"))
            draw_circle(Vector2(x + 28 * s, y - 5 * s), 12 * s, Color("#202b3a"))
            draw_line(Vector2(x - 25 * s, y - 10 * s), Vector2(x + 16 * s, y - 45 * s), Color("#f16b4f"), 8 * s)
            draw_line(Vector2(x + 16 * s, y - 45 * s), Vector2(x + 31 * s, y - 70 * s), Color("#f16b4f"), 6 * s)
            draw_circle(Vector2(x - 5 * s, y - 76 * s), 12 * s, Color("#d8916b"))
            _text_center(Vector2(x, y - 101 * s), "VUUUM", int(9 * s + 3), YELLOW)
        "drone":
            draw_line(Vector2(x - 38 * s, y - 56 * s), Vector2(x + 38 * s, y - 56 * s), Color("#aeb9c7"), 7 * s)
            draw_circle(Vector2(x - 43 * s, y - 56 * s), 13 * s, Color("#4e6179"))
            draw_circle(Vector2(x + 43 * s, y - 56 * s), 13 * s, Color("#4e6179"))
            draw_rect(Rect2(x - 23 * s, y - 48 * s, 46 * s, 28 * s), Color("#55d5bf"))
            _text_center(Vector2(x, y - 75 * s), "IFOOD?", int(9 * s + 3), UI_BG)
        "turnstile":
            draw_rect(Rect2(x - 10 * s, y - 105 * s, 20 * s, 105 * s), Color("#718398"))
            draw_circle(Vector2(x, y - 55 * s), 15 * s, Color("#f2c34d"))
            for arm in 3:
                var angle := arm * TAU / 3.0
                draw_line(Vector2(x, y - 55 * s), Vector2(x + cos(angle) * 50 * s, y - 55 * s + sin(angle) * 50 * s), Color("#f2c34d"), 6 * s)
            _text_center(Vector2(x, y - 122 * s), "PI", int(10 * s + 3), Color("#fff0ad"))
        "traffic":
            draw_rect(Rect2(x - 19 * s, y - 115 * s, 38 * s, 100 * s), Color("#303b4b"))
            draw_circle(Vector2(x, y - 95 * s), 10 * s, Color("#ef554f"))
            draw_circle(Vector2(x, y - 65 * s), 10 * s, Color("#f3c84d"))
            draw_circle(Vector2(x, y - 35 * s), 10 * s, Color("#55d98c"))
            _text_center(Vector2(x, y - 132 * s), "CORRE", int(9 * s + 3), WHITE)
        "cart":
            draw_rect(Rect2(x - 47 * s, y - 65 * s, 94 * s, 50 * s), Color("#e15a61"), false, 6 * s)
            draw_line(Vector2(x - 45 * s, y - 65 * s), Vector2(x - 63 * s, y - 97 * s), Color("#c6d1cf"), 6 * s)
            draw_circle(Vector2(x - 25 * s, y + 1 * s), 11 * s, Color("#252d3b"))
            draw_circle(Vector2(x + 30 * s, y + 1 * s), 11 * s, Color("#252d3b"))
            _text_center(Vector2(x, y - 82 * s), "OFERTA", int(9 * s + 3), YELLOW)
        "umbrella":
            draw_arc(Vector2(x, y - 45 * s), 45 * s, PI, TAU, 16, Color("#e85d62"), 8 * s)
            draw_colored_polygon(PackedVector2Array([Vector2(x - 45 * s, y - 45 * s), Vector2(x, y - 72 * s), Vector2(x + 45 * s, y - 45 * s)]), Color("#e85d62"))
            draw_line(Vector2(x, y - 45 * s), Vector2(x + 18 * s, y + 12 * s), Color("#e7d2ac"), 6 * s)
            draw_arc(Vector2(x + 18 * s, y + 12 * s), 10 * s, 0.0, PI, 8, Color("#e7d2ac"), 5 * s)
            _text_center(Vector2(x, y - 83 * s), "CHUVA", int(9 * s + 3), WHITE)
        "luggage":
            draw_rect(Rect2(x - 38 * s, y - 88 * s, 76 * s, 88 * s), Color("#8d6cc1"))
            draw_rect(Rect2(x - 20 * s, y - 105 * s, 40 * s, 20 * s), Color("#59647e"), false, 6 * s)
            draw_circle(Vector2(x - 22 * s, y + 2 * s), 8 * s, Color("#273248"))
            draw_circle(Vector2(x + 22 * s, y + 2 * s), 8 * s, Color("#273248"))
            _text_center(Vector2(x, y - 45 * s), "VIAJA", int(9 * s + 3), WHITE)
        "bus":
            _draw_bus(Vector2(x, y - 85 * s), 0.48 * s, false)
        "capybara":
            _ellipse(Vector2(x, y - 33 * s), 56 * s, 29 * s, Color("#9a6b4b"))
            _ellipse(Vector2(x + 43 * s, y - 62 * s), 25 * s, 20 * s, Color("#a97752"))
            draw_circle(Vector2(x + 51 * s, y - 67 * s), 3 * s, Color("#201d24"))
            _text_center(Vector2(x, y - 91 * s), "calma", int(10 * s + 3), Color("#fff0ba"))
        "horse":
            draw_ellipse_horse(Vector2(x, y), s)
        "truck":
            draw_rect(Rect2(x - 60 * s, y - 92 * s, 120 * s, 92 * s), Color("#d65f42"))
            draw_rect(Rect2(x + 18 * s, y - 62 * s, 42 * s, 45 * s), Color("#80c0c9"))
            draw_circle(Vector2(x - 30 * s, y + 2 * s), 17 * s, Color("#202a38"))
            draw_circle(Vector2(x + 37 * s, y + 2 * s), 17 * s, Color("#202a38"))
            _text_center(Vector2(x, y - 109 * s), "DESGOVERNADO", int(9 * s + 2), Color("#fff0a5"))
        _:
            draw_rect(Rect2(x - 20 * s, y - 40 * s, 40 * s, 40 * s), RED)

func draw_ellipse_horse(pos: Vector2, s: float) -> void:
    _ellipse(pos + Vector2(0, -42 * s), 44 * s, 26 * s, Color("#a9754f"))
    draw_line(pos + Vector2(30, -55) * s, pos + Vector2(50, -94) * s, Color("#a9754f"), 16 * s)
    _ellipse(pos + Vector2(52, -103) * s, 22 * s, 17 * s, Color("#a9754f"))
    draw_circle(pos + Vector2(58, -108) * s, 3 * s, Color("#1b1d27"))
    draw_line(pos + Vector2(-25, -22) * s, pos + Vector2(-31, 1) * s, Color("#714a38"), 8 * s)
    draw_line(pos + Vector2(20, -22) * s, pos + Vector2(27, 1) * s, Color("#714a38"), 8 * s)

func _draw_collectible(kind: String, pos: Vector2, object_scale: float) -> void:
    var color := Color("#ffd34e")
    if kind == "coffee": color = Color("#b87d55")
    elif kind == "bread": color = Color("#f2b04c")
    elif kind == "pastel": color = Color("#e99b52")
    elif kind == "sugarcane": color = Color("#68cf83")
    elif kind == "mint": color = Color("#79dfcb")
    elif kind == "pass": color = Color("#d8f0a2")
    elif kind == "golden": color = Color("#fff0a0")
    elif kind == "coxinha": color = Color("#e5a143")
    elif kind == "guarana": color = Color("#e85d68")
    elif kind == "pix": color = Color("#54dfbf")
    elif kind == "umbrella": color = Color("#72b9f2")
    elif kind == "clover": color = Color("#77d866")
    var bob := sin(pulse * 4.0 + pos.x * 0.01) * 3.0 * object_scale
    var center := pos + Vector2(0, bob)
    var radius := 18.0 * object_scale
    draw_circle(center, radius * 2.0, Color(color, 0.08))
    draw_arc(center, radius * 1.55, pulse * 1.8, pulse * 1.8 + 4.2, 18, Color(color, 0.42), maxf(1.0, 2.0 * object_scale))
    draw_circle(center, radius * 1.12, Color(0.02, 0.06, 0.12, 0.50))
    draw_circle(center, radius, color)
    draw_arc(center, radius * 0.78, PI * 1.05, PI * 1.85, 12, Color(1, 1, 1, 0.62), maxf(1.0, 2.0 * object_scale))
    var bonus_labels := {"coffee": "☕", "bread": "P", "pastel": "★", "sugarcane": "C", "mint": "M", "pass": "VT", "golden": "★", "coxinha": "C", "guarana": "G", "pix": "₱", "umbrella": "U", "clover": "♣"}
    var label: String = "¢" if kind == "coin" else str(bonus_labels.get(kind, "•"))
    _text_center(center + Vector2(0, 6 * object_scale), label, int(14 * object_scale + 4), UI_INK)
    if object_scale > 0.55:
        _text_center(center + Vector2(0, -34 * object_scale), COLLECTIBLE_NAMES.get(kind, kind), int(8 * object_scale + 3), WHITE)

func _draw_wall(pos: Vector2, object_scale: float, left: bool) -> void:
    var direction := -1.0 if left else 1.0
    draw_rect(Rect2(pos.x + direction * 27 * object_scale - 13 * object_scale, pos.y - 135 * object_scale, 26 * object_scale, 135 * object_scale), Color("#8b6b61"))
    draw_rect(Rect2(pos.x + direction * 52 * object_scale - 18 * object_scale, pos.y - 108 * object_scale, 36 * object_scale, 12 * object_scale), Color("#ecb54b"))
    _text_center(pos + Vector2(direction * 45 * object_scale, -153 * object_scale), "↑", int(22 * object_scale + 5), BLUE)

func _draw_ramp(pos: Vector2, object_scale: float) -> void:
    draw_colored_polygon(PackedVector2Array([pos + Vector2(-55, 0) * object_scale, pos + Vector2(53, 0) * object_scale, pos + Vector2(35, -55) * object_scale, pos + Vector2(-18, -18) * object_scale]), Color("#ed9f3c"))
    draw_line(pos + Vector2(-35, -7) * object_scale, pos + Vector2(33, -39) * object_scale, Color("#fff0a4"), 4 * object_scale)
    _text_center(pos + Vector2(0, -68 * object_scale), "↑ SUPER", int(10 * object_scale + 3), YELLOW)

func _draw_dog(pos: Vector2, object_scale: float, chase: bool) -> void:
    _ellipse(pos + Vector2(0, -30) * object_scale, 42 * object_scale, 24 * object_scale, Color("#b8794d"))
    _ellipse(pos + Vector2(34, -56) * object_scale, 23 * object_scale, 22 * object_scale, Color("#c28656"))
    draw_colored_polygon(PackedVector2Array([pos + Vector2(18, -70) * object_scale, pos + Vector2(12, -100) * object_scale, pos + Vector2(30, -78) * object_scale]), Color("#86553f"))
    draw_circle(pos + Vector2(40, -60) * object_scale, 3 * object_scale, Color("#171d28"))
    draw_line(pos + Vector2(-20, -13) * object_scale, pos + Vector2(-27, 10) * object_scale, Color("#774832"), 8 * object_scale)
    draw_line(pos + Vector2(22, -13) * object_scale, pos + Vector2(28, 10) * object_scale, Color("#774832"), 8 * object_scale)
    draw_line(pos + Vector2(-36, -43) * object_scale, pos + Vector2(-65, -60) * object_scale, Color("#c28656"), 7 * object_scale)
    if chase:
        _text_center(pos + Vector2(0, -112) * object_scale, "AU AU!", int(12 * object_scale + 5), Color("#ffeaa4"))

func _draw_player(x: float, y: float, object_scale: float, character: String) -> void:
    _draw_runner(Vector2(x, y), object_scale, false, character)

func _draw_runner(pos: Vector2, object_scale: float, mirrored: bool, character := "ze") -> void:
    var direction := -1.0 if mirrored else 1.0
    var skin := Color("#d8946d")
    var shirt := Color("#e94f5a")
    var pants := Color("#29354d")
    match character:
        "maria": shirt = Color("#a86bd7")
        "motoboy": shirt = Color("#39bda9")
        "julia":
            skin = Color("#ac7049")
            shirt = Color("#c98a4d")
        "carlos":
            shirt = Color("#5272ba")
            pants = Color("#20293b")
        "influencer": shirt = Color("#e45d99")
    var squish := 0.72 if slide_timer > 0.0 else 1.0
    _ellipse(pos + Vector2(0, 5), 46 * object_scale, 12 * object_scale, Color(0.02, 0.04, 0.08, 0.38))
    if dash_timer > 0.0:
        for trail in 3:
            draw_line(pos + Vector2(-58 - trail * 18, -30 + trail * 13) * object_scale, pos + Vector2(-105 - trail * 22, -30 + trail * 13) * object_scale, Color(YELLOW, 0.34 - trail * 0.08), 5 * object_scale)
    draw_line(pos + Vector2(-15 * direction, -4) * object_scale, pos + Vector2(-30 * direction, 36) * object_scale, pants, 14 * object_scale)
    draw_line(pos + Vector2(15 * direction, -4) * object_scale, pos + Vector2(30 * direction, 36) * object_scale, pants, 14 * object_scale)
    draw_line(pos + Vector2(-30 * direction, 35) * object_scale, pos + Vector2(-47 * direction, 35) * object_scale, skin, 9 * object_scale)
    draw_line(pos + Vector2(30 * direction, 35) * object_scale, pos + Vector2(47 * direction, 35) * object_scale, skin, 9 * object_scale)
    var torso := Rect2(pos.x - 28 * object_scale, pos.y - 65 * object_scale, 56 * object_scale, 66 * object_scale * squish)
    draw_rect(torso, shirt)
    draw_rect(torso, Color(0.04, 0.08, 0.14, 0.54), false, maxf(1.0, 2.0 * object_scale))
    draw_rect(Rect2(torso.position + Vector2(7, 7) * object_scale, Vector2(torso.size.x - 14 * object_scale, 5 * object_scale)), Color(1, 1, 1, 0.16))
    draw_line(pos + Vector2(-26 * direction, -48) * object_scale, pos + Vector2(-53 * direction, -24) * object_scale, skin, 11 * object_scale)
    draw_line(pos + Vector2(26 * direction, -48) * object_scale, pos + Vector2(53 * direction, -73) * object_scale, skin, 11 * object_scale)
    draw_circle(pos + Vector2(0, -94 * object_scale * (1.0 if squish > 0.9 else 0.7)), 28 * object_scale, skin)
    draw_arc(pos + Vector2(0, -94 * object_scale * (1.0 if squish > 0.9 else 0.7)), 28 * object_scale, PI, TAU, 12, Color("#3a2831"), 11 * object_scale)
    draw_circle(pos + Vector2(10 * direction, -94 * object_scale), 3 * object_scale, Color("#222533"))
    draw_line(pos + Vector2(8 * direction, -82) * object_scale, pos + Vector2(19 * direction, -79) * object_scale, Color("#5c3038"), 3 * object_scale)
    if character in ["carlos", "chefe"]:
        _text_center(pos + Vector2(0, -138) * object_scale, "CARLOS", int(9 * object_scale + 3), WHITE)
    elif character == "motoboy":
        draw_arc(pos + Vector2(0, -98) * object_scale, 31 * object_scale, PI, TAU, 12, Color("#ed4e45"), 8 * object_scale)
    elif character == "maria":
        draw_circle(pos + Vector2(-31 * direction, -43) * object_scale, 16 * object_scale, Color("#d64c88"))
    elif character == "influencer":
        draw_rect(Rect2(pos.x + 35 * direction * object_scale, pos.y - 78 * object_scale, 22 * object_scale, 35 * object_scale), Color("#1d334f"))

func _draw_bus(pos: Vector2, object_scale: float, leaving: bool) -> void:
    var p := pos
    var s := object_scale
    _ellipse(p + Vector2(0, 58) * s, 139 * s, 18 * s, Color(0.02, 0.04, 0.08, 0.35))
    var body := Rect2(p.x - 125 * s, p.y - 70 * s, 250 * s, 116 * s)
    draw_rect(body, Color("#f4bf3d"), true)
    draw_rect(body, Color("#4e3740"), false, maxf(1.0, 4.0 * s))
    draw_rect(Rect2(p.x - 117 * s, p.y - 62 * s, 234 * s, 10 * s), Color("#ffe98b"), true)
    draw_rect(Rect2(p.x - 105 * s, p.y - 50 * s, 170 * s, 50 * s), Color("#82cfd3"), true)
    draw_rect(Rect2(p.x - 99 * s, p.y - 44 * s, 158 * s, 7 * s), Color(1, 1, 1, 0.32), true)
    for window in 4:
        var window_x := p.x - 91 * s + window * 39 * s
        draw_line(Vector2(window_x, p.y - 47 * s), Vector2(window_x, p.y - 5 * s), Color("#4e8d9b"), 2 * s)
    draw_rect(Rect2(p.x + 68 * s, p.y - 50 * s, 35 * s, 50 * s), Color("#65aeb9"), true)
    draw_rect(Rect2(p.x - 122 * s, p.y + 9 * s, 245 * s, 14 * s), Color("#ed634c"), true)
    draw_rect(Rect2(p.x - 58 * s, p.y + 11 * s, 116 * s, 9 * s), Color("#ff9d50"), true)
    draw_circle(p + Vector2(-78, 53) * s, 25 * s, Color("#202b3a"))
    draw_circle(p + Vector2(82, 53) * s, 25 * s, Color("#202b3a"))
    draw_circle(p + Vector2(-78, 53) * s, 12 * s, Color("#c5d0c8"))
    draw_circle(p + Vector2(82, 53) * s, 12 * s, Color("#c5d0c8"))
    draw_circle(p + Vector2(-78, 53) * s, 5 * s, Color("#6f7c88"))
    draw_circle(p + Vector2(82, 53) * s, 5 * s, Color("#6f7c88"))
    draw_circle(p + Vector2(-113, -3) * s, 6 * s, Color("#fff3a3"))
    var destination := Rect2(p.x - 49 * s, p.y + 27 * s, 98 * s, 20 * s)
    draw_rect(destination, Color("#f7c63f"))
    draw_rect(destination, Color("#6d4930"), false, maxf(1.0, 1.5 * s))
    _text_center(p + Vector2(0, 42) * s, "PONTO", int(11 * s + 5), Color("#51322b"))
    if leaving:
        _text_center(p + Vector2(0, -95) * s, "TCHAU!", int(18 * s + 7), RED)

func _draw_bus_stop(pos: Vector2, object_scale: float) -> void:
    var p := pos
    var s := object_scale
    draw_line(p + Vector2(0, -150) * s, p + Vector2(0, 30) * s, Color("#d9dde1"), 8 * s)
    draw_rect(Rect2(p.x - 47 * s, p.y - 160 * s, 94 * s, 60 * s), Color("#eec442"))
    _text_center(p + Vector2(0, -121) * s, "P", int(28 * s + 8), Color("#253650"))
    draw_line(p + Vector2(-65, 25) * s, p + Vector2(65, 25) * s, Color("#b7c8c7"), 6 * s)
    _text_center(p + Vector2(0, -180) * s, "PONTO", int(12 * s + 4), WHITE)

func _draw_global_particles() -> void:
    for p in particles:
        var life: float = float(p["life"])
        var pos := Vector2(p["pos"])
        var alpha := minf(1.0, life * 2.0)
        var particle_color: Color = p["color"]
        draw_circle(pos, 7.0 + life * 7.0, Color(particle_color, alpha * 0.10))
        draw_circle(pos, 2.0 + life * 3.0, Color(particle_color, alpha))
        draw_line(pos, pos - Vector2(p["velocity"]) * 0.045, Color(particle_color, alpha * 0.35), 1.5)
    for c in confetti:
        var confetti_pos := Vector2(c["pos"])
        var confetti_alpha := minf(1.0, float(c["life"]))
        draw_rect(Rect2(confetti_pos, Vector2(7, 13)), Color(c["color"], confetti_alpha))
        draw_line(confetti_pos, confetti_pos + Vector2(7, 0), Color(1, 1, 1, confetti_alpha * 0.35), 1.0)

func _character_name(id: String) -> String:
    return {"ze": "Zé Atrasado", "maria": "Maria do Bairro", "motoboy": "Rafa Motoboy", "julia": "Júlia Atleta", "caramelo": "Júlia Atleta", "carlos": "Carlos da Obra", "chefe": "Carlos da Obra", "influencer": "Nina Creator"}.get(id, id)
