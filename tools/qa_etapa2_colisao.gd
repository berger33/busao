extends SceneTree
## ETAPA 2 — Teste de aceitação headless das regras de colisão/controle.
## Rodar: godot --headless --path . -s res://tools/qa_etapa2_colisao.gd
## Matriz ação x família (blueprint §4/§6):
##   A. pulo sobre cone          -> desvio limpo
##   B. deslize no banco         -> dano (deslize não resolve)
##   C. pulo no ônibus           -> dano (pulo não atravessa ônibus/caminhão)
##   D. pulo sobre buraco        -> desvio limpo
##   E. obstáculo fora do alcance lateral -> nada acontece
##   F. colisão pela posição real durante a troca de corredor
##   G. esbarrão em pedestre     -> sem dano, com lentidão
##   H. dash não concede imunidade
##   I. buffer de entrada (~120 ms): pulo pedido no ar sai na aterrissagem
##   J. determinismo: mesma entrada, mesma resposta
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 2 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    _scenario_g()
    _scenario_h()
    await _scenario_i()
    _scenario_j()
    if _failures.is_empty():
        print("ETAPA2_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA2_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _start_phase() -> void:
    _game._start_run(0)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"
    _game.hearts = 3
    _game.invulnerability = 0.0
    _game.slow_motion_timer = 0.0
    _game.dash_timer = 0.0
    _game.jump_timer = 0.0
    _game.slide_timer = 0.0
    _game.player_lane = 1
    _game.player_x = _game.LANE_X[1]


func _spawn_test_entity(kind: String, lane: int) -> Dictionary:
    var e: Dictionary = {
        "kind": kind,
        "lane": lane,
        "collectible": false,
        "passed": false,
        "node": _game.player_root,
    }
    _game.entities.append(e)
    return e


# A. Pulo sobre cone: desvio limpo, sem dano.
func _scenario_a() -> void:
    _start_phase()
    _game.jump_timer = 0.4
    var e: Dictionary = _spawn_test_entity("cone", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 3, "A. pulo sobre cone -> desvio limpo")


# B. Deslize no banco: deslize não resolve volume sólido -> dano.
func _scenario_b() -> void:
    _start_phase()
    _game.slide_timer = 0.4
    var e: Dictionary = _spawn_test_entity("bench", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 2, "B. deslize no banco -> dano (deslize não resolve)")


# C. Pulo no ônibus: pulo não atravessa ônibus/caminhão -> dano.
func _scenario_c() -> void:
    _start_phase()
    _game.jump_timer = 0.4
    var e: Dictionary = _spawn_test_entity("bus_traffic", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 2, "C. pulo no ônibus -> dano (pulo não atravessa)")


# D. Pulo sobre buraco: desvio limpo.
func _scenario_d() -> void:
    _start_phase()
    _game.jump_timer = 0.4
    var e: Dictionary = _spawn_test_entity("pothole", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 3, "D. pulo sobre buraco -> desvio limpo")


# E. Obstáculo num corredor distante da posição real -> nada acontece.
func _scenario_e() -> void:
    _start_phase()
    _game.player_lane = 0
    _game.player_x = _game.LANE_X[0]
    var e: Dictionary = _spawn_test_entity("cone", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 3, "E. obstáculo fora do alcance lateral -> nada")


# F. Colisão pela posição real durante a troca de corredor.
func _scenario_f() -> void:
    _start_phase()
    _game.player_lane = 0
    # Perto da borda do corredor vizinho (dentro da largura de colisão).
    _game.player_x = _game.LANE_X[1] - 0.9
    var e1: Dictionary = _spawn_test_entity("hydrant", 1)
    _game._resolve_entity(e1)
    var hit_perto: bool = int(_game.hearts) == 2
    _start_phase()
    _game.player_lane = 0
    # Entre corredores, fora da largura de colisão.
    _game.player_x = _game.LANE_X[1] - 2.0
    var e2: Dictionary = _spawn_test_entity("hydrant", 1)
    _game._resolve_entity(e2)
    var ileso_longe: bool = int(_game.hearts) == 3
    _check(hit_perto and ileso_longe,
            "F. posição real decide a colisão na troca de corredor")


# G. Pedestre: esbarrão sem dano, com lentidão.
func _scenario_g() -> void:
    _start_phase()
    var e: Dictionary = _spawn_test_entity("old_lady", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 3 and float(_game.slow_motion_timer) > 0.0,
            "G. esbarrão em pedestre -> sem dano, com lentidão")


# H. Dash não concede imunidade: cone atravessado no dash -> dano.
func _scenario_h() -> void:
    _start_phase()
    _game.dash_timer = 0.3
    var e: Dictionary = _spawn_test_entity("cone", 1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 2, "H. dash não concede imunidade")


# I. Buffer de entrada: pulo pedido pouco antes de aterrissar sai sozinho.
func _scenario_i() -> void:
    _start_phase()
    _game.jump_timer = 0.04
    _game._jump()  # no ar -> entra no buffer em vez de executar
    var em_buffer: bool = float(_game.jump_timer) <= 0.05
    var t0: int = Time.get_ticks_msec()
    while float(_game.jump_timer) < 0.2 and (Time.get_ticks_msec() - t0) < 3000:
        await process_frame
    _check(em_buffer and float(_game.jump_timer) > 0.2,
            "I. buffer de entrada: pulo pedido no ar sai na aterrissagem")


# J. Determinismo: mesma configuração, mesma resposta (cenário A duas vezes).
func _scenario_j() -> void:
    var resultados: Array = []
    for i in 2:
        _start_phase()
        _game.jump_timer = 0.4
        var e: Dictionary = _spawn_test_entity("cone", 1)
        _game._resolve_entity(e)
        resultados.append(int(_game.hearts))
    _check(resultados == [3, 3], "J. determinismo: mesma entrada, mesma resposta")
