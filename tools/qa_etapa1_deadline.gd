extends SceneTree
## ETAPA 1 — Teste de aceitação headless da regra do prazo (RunDirector).
## Rodar: godot --headless --path . -s tools/qa_etapa1_deadline.gd
## Cenários:
##   A. chegada adiantada            -> sucesso
##   B. chegada no limite do prazo   -> sucesso (chegada avaliada antes da expiração)
##   C. chegada 1 s atrasada         -> derrota "atraso"
##   D. prazo expira no meio do caminho -> derrota "atraso" com distância restante
##   E. fôlego zerado                -> derrota "folego"
##   F. pausa suspende o relógio     -> time_used inalterado
##   G. impacto acrescenta +2 s      -> penalty_total
##   H. prazo autoral nas 50 + tabela de margens íntegra + clamp na final
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 1 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    await _scenario_a()
    await _scenario_b()
    await _scenario_c()
    await _scenario_d()
    await _scenario_e()
    await _scenario_f()
    await _scenario_g()
    _scenario_h()
    if _failures.is_empty():
        print("ETAPA1_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA1_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    # Contagem de largada pulada para determinismo dos cenários.
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


func _sleep(seconds: float) -> void:
    var t0: int = Time.get_ticks_msec()
    while (Time.get_ticks_msec() - t0) < int(seconds * 1000.0):
        await process_frame


func _wait_for_run_mode(mode: String, timeout_s: float) -> String:
    var t0: int = Time.get_ticks_msec()
    while str(_game.run_mode) != mode and (Time.get_ticks_msec() - t0) < int(timeout_s * 1000.0):
        await process_frame
    return str(_game.run_mode)


# A. Perto do ponto com folga no relógio: cruza, embarca, vence.
func _scenario_a() -> void:
    _start_phase(0)
    _game.distance = _game.run_total - 2.0
    var mode: String = await _wait_for_run_mode("results", 10.0)
    var d = _game.run_director
    _check(mode == "results" and d.finished and d.success
            and bool(_game.result.get("success", false)),
            "A. chegada adiantada -> sucesso")


# B. No limite: tempo quase esgotado, zona de embarque a 1 mm.
# A chegada é avaliada antes da expiração no mesmo frame -> sucesso.
func _scenario_b() -> void:
    _start_phase(0)
    _game.run_director.time_used = _game.run_director.deadline - 0.05
    _game.distance = _game.run_total - 0.001
    var mode: String = await _wait_for_run_mode("results", 10.0)
    var d = _game.run_director
    _check(mode == "results" and d.finished and d.success
            and bool(_game.result.get("success", false)),
            "B. chegada no limite do prazo -> sucesso")


# C. Tarde demais: cruza 1 s depois do prazo -> derrota "atraso".
func _scenario_c() -> void:
    _start_phase(0)
    _game.run_director.time_used = _game.run_director.deadline + 1.0
    _game.distance = _game.run_total - 0.001
    var mode: String = await _wait_for_run_mode("results", 10.0)
    var d = _game.run_director
    _check(mode == "results" and d.finished and not d.success
            and d.fail_reason == "atraso"
            and not bool(_game.result.get("success", false))
            and str(_game.result.get("fail_reason", "")) == "atraso",
            "C. chegada atrasada -> derrota 'atraso'")


# D. O relógio zera longe do ponto: o ônibus parte, distância restante informada.
func _scenario_d() -> void:
    _start_phase(0)
    _game.run_director.time_used = _game.run_director.deadline - 0.3
    _game.distance = 10.0
    var mode: String = await _wait_for_run_mode("results", 10.0)
    var d = _game.run_director
    _check(mode == "results" and d.finished and not d.success
            and d.fail_reason == "atraso" and d.shortfall_m > 50.0,
            "D. prazo expira no meio do caminho -> 'atraso' com distância restante")


# E. Sem fôlego e sem reviver: derrota com causa "folego".
func _scenario_e() -> void:
    _start_phase(0)
    _game.hearts = 1
    _game._revive_used = true
    _game._hit_player("cone")
    var mode: String = await _wait_for_run_mode("results", 10.0)
    var d = _game.run_director
    _check(mode == "results" and d.finished and not d.success
            and d.fail_reason == "folego"
            and str(_game.result.get("fail_reason", "")) == "folego",
            "E. fôlego zerado -> derrota 'folego'")


# F. Pausado, o relógio do prazo não anda.
func _scenario_f() -> void:
    _start_phase(0)
    await _sleep(0.25)
    var t0: float = _game.run_director.time_used
    _check(t0 > 0.0, "F1. relógio anda durante a corrida")
    _game.run_mode = "paused"
    await _sleep(0.6)
    var t1: float = _game.run_director.time_used
    _check(absf(t1 - t0) < 0.0001, "F2. pausa suspende o relógio do prazo")
    _game.run_mode = "playing"


# G. Impacto válido: -1 coração e +2 s no tempo consumido.
func _scenario_g() -> void:
    _start_phase(0)
    _game.hearts = 3
    _game._hit_player("cone")
    var d = _game.run_director
    _check(absf(d.penalty_total - 2.0) < 0.001
            and absf(d.time_used - 2.0) < 0.001
            and int(_game.hearts) == 2,
            "G. impacto acrescenta +2 s ao tempo consumido")


# H. Prazo autoral nas 50 + tabela de margens íntegra + clamp na final.
func _scenario_h() -> void:
    # ETAPA 16 — as 50 fases são autorais: o prazo vem dos dados do nível
    # (blueprint §8) em todas; a tabela de margens segue íntegra para o
    # modo procedural e o índice 50 fixa na final.
    var ok := true
    for i in range(50):
        var prazo: float = _game._phase_deadline_for(i)
        var dado: float = float(LevelData.for_phase(i).get("deadline_seconds", -1.0))
        if absf(prazo - dado) > 0.001:
            ok = false
            print("  fase %d: prazo %.2f diverge do dado %.2f" % [i + 1, prazo, dado])
    var margens: Array = _game.DEADLINE_MARGINS
    if margens.size() != 50:
        ok = false
        print("  tabela de margens com %d entradas (esperado 50)" % margens.size())
    for i in range(50):
        var margem: float = _game._deadline_margin_for(i)
        if absf(margem - float(margens[i])) > 0.001 or margem <= 0.0:
            ok = false
            print("  margem %d fora da tabela: %s" % [i, str(margem)])
    var fixo: float = _game._phase_deadline_for(50)
    var final: float = _game._phase_deadline_for(49)
    var pressa_fixa: float = _game._phase_speed_for(50)
    print("prazo índice 50 = %s s (final = %s, velocidade = %s)" % [str(fixo), str(final), str(pressa_fixa)])
    if absf(fixo - final) > 0.001 or absf(pressa_fixa - 9.0) > 0.001:
        ok = false
        print("  índice 50 deveria fixar na final")
    _check(ok, "H. prazo autoral nas 50, margens íntegras e clamp na final")
