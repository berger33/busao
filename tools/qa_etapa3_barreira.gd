extends SceneTree
## ETAPA 3 — Teste de aceitação headless da barreira suspensa (SLIDE_UNDER).
## Rodar: godot --headless --path . -s res://tools/qa_etapa3_barreira.gd
## Cenários:
##   K. deslizar sob a barreira      -> desvio limpo
##   L. pular na barreira            -> dano (pulo não passa por cima)
##   M. correr sem ação na barreira  -> dano
##   N. fase de introdução: fases 1-2 sem barreira; fase 3 com barreira
##   O. determinismo do percurso: mesma fase, mesma sequência de obstáculos
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 3 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_3()
    _scenario_k()
    _scenario_l()
    _scenario_m()
    _scenario_n()
    _scenario_o()
    if _failures.is_empty():
        print("ETAPA3_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA3_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_3() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    save.call("record_phase", 0, 3, 10.0)
    save.call("record_phase", 1, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"
    _game.hearts = 3
    _game.invulnerability = 0.0
    _game.player_lane = 1
    _game.player_x = _game.LANE_X[1]


func _spawn_test_barrier(lane: int) -> Dictionary:
    var e: Dictionary = {
        "kind": "barrier",
        "lane": lane,
        "collectible": false,
        "passed": false,
        "node": _game.player_root,
    }
    _game.entities.append(e)
    return e


# K. Deslizar sob a barreira: desvio limpo, sem dano.
func _scenario_k() -> void:
    _start_phase(0)
    _game.slide_timer = 0.4
    var e: Dictionary = _spawn_test_barrier(1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 3, "K. deslizar sob a barreira -> desvio limpo")


# L. Pular na barreira: o pulo não passa por cima -> dano.
func _scenario_l() -> void:
    _start_phase(0)
    _game.jump_timer = 0.4
    var e: Dictionary = _spawn_test_barrier(1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 2, "L. pular na barreira -> dano")


# M. Correr sem ação na barreira -> dano.
func _scenario_m() -> void:
    _start_phase(0)
    var e: Dictionary = _spawn_test_barrier(1)
    _game._resolve_entity(e)
    _check(int(_game.hearts) == 2, "M. correr sem ação na barreira -> dano")


func _count_barriers(index: int) -> int:
    _start_phase(index)
    var n := 0
    for e in _game.entities:
        if str(e["kind"]) == "barrier":
            n += 1
    return n


# N. Fase de introdução (blueprint §6): fases 1-2 sem barreira; fase 3 com.
func _scenario_n() -> void:
    var fase1: int = _count_barriers(0)
    var fase2: int = _count_barriers(1)
    var fase3: int = _count_barriers(2)
    print("barreiras: fase1=%d fase2=%d fase3=%d" % [fase1, fase2, fase3])
    _check(fase1 == 0 and fase2 == 0 and fase3 >= 1,
            "N. barreira entra só na fase 3 (introdução)")


func _course_signature(index: int) -> String:
    # Mesma semente + mesma fase => mesmo percurso (reproducibilidade).
    _game.rng.seed = 20240917
    _start_phase(index)
    var sig := ""
    for e in _game.entities:
        if bool(e["collectible"]):
            continue
        sig += "%s:%d:%d;" % [str(e["kind"]), int(e["lane"]), int(float(e["distance"]) * 10.0)]
    return sig


# O. Determinismo do percurso: mesma fase gera a mesma sequência.
func _scenario_o() -> void:
    var sig1: String = _course_signature(2)
    var sig2: String = _course_signature(2)
    _check(sig1 == sig2 and sig1.length() > 0,
            "O. percurso determinístico (mesma fase, mesma sequência)")
