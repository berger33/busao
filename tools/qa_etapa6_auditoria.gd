extends SceneTree
## ETAPA 6 — Teste de aceitação headless dos gaps fechados na auditoria do
## blueprint (antes da produção das 50 fases).
## Rodar: godot --headless --path . -s res://tools/qa_etapa6_auditoria.gd
## Cenários:
##   A. derrota por atraso informa segundos faltando (blueprint §5)
##   B. estrelas por objetivo: melhor realização por tentativa (blueprint §9)
##   C. migração de save v3 -> v4 preserva progresso e deriva objetivos
##   D. caminho real do jogo grava objetivos nas tentativas (fase piloto)
##   E. visualização de colisor em modo de teste (blueprint §4)
##   F. piloto intacto: validador verde e 21 entidades autorais
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null
var _save: Node = null


func _initialize() -> void:
    print("== ETAPA 6 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _save = _game.get_node("/root/GameSave")
    _unlock_up_to_phase_3()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA6_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA6_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_3() -> void:
    _save.call("record_phase", 0, 3, 10.0)
    _save.call("record_phase", 1, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


## O save persiste entre execuções do QA: zera os objetivos do cenário para
## a verificação ser idempotente.
func _reset_goals(index: int) -> void:
    _save.data["phase_goals"][index] = {"prazo": false, "sem_dano": false, "moedas": false}
    _save.data["phase_stars"][index] = 0


# A. Derrota por atraso: diretor calcula metros E segundos faltando.
func _scenario_a() -> void:
    var diretor: RefCounted = _game.run_director
    diretor.setup(400.0, 5.0, 10.0, 0.0)
    diretor.begin_countdown()
    diretor.update(3.0, 0.0)      # termina a contagem (2,4 s)
    var eventos: Array = diretor.update(11.0, 100.0)
    print("atraso: faltavam %.0f m, %.1f s" % [diretor.shortfall_m, diretor.shortfall_s])
    _check(eventos.has("deadline") and absf(diretor.shortfall_m - 300.0) < 0.01
            and absf(diretor.shortfall_s - 60.0) < 0.01,
            "A. atraso informa 300 m e 60 s faltando (400 m a 5 m/s, prazo 10 s)")


# B. Estrelas por objetivo: união das melhores tentativas.
func _scenario_b() -> void:
    _reset_goals(5)
    var r1: Dictionary = _save.call("record_phase", 5, 2, 30.0,
            {"prazo": true, "sem_dano": false, "moedas": true})
    var r2: Dictionary = _save.call("record_phase", 5, 2, 32.0,
            {"prazo": true, "sem_dano": true, "moedas": false})
    print("tentativa1 -> %d estrelas, tentativa2 -> %d estrelas" % [
            int(r1.get("stars_total", 0)), int(r2.get("stars_total", 0))])
    _check(int(r1.get("stars_total", 0)) == 2 and int(r2.get("stars_total", 0)) == 3,
            "B. sem dano numa tentativa + moedas em outra = 3 estrelas")


# C. Migração v3 -> v4: progresso preservado, prazo derivado das estrelas.
func _scenario_c() -> void:
    _save.data["phase_stars"][7] = 2
    _save.data.erase("phase_goals")
    _save.call("_migrate_data", 3)
    var goals: Array = _save.data.get("phase_goals", [])
    var goal7: Dictionary = goals[7] if goals.size() > 7 else {}
    print("migracao: %d goals, fase7=%s, schema=%d" % [goals.size(), str(goal7),
            int(_save.data.get("schema_version", 0))])
    _check(goals.size() == 50 and bool(goal7.get("prazo", false))
            and not bool(goal7.get("sem_dano", false))
            and int(_save.data.get("schema_version", 0)) == 4,
            "C. save v3 migra para v4 sem perder estrelas")


# D. Caminho real: duas tentativas no piloto somam objetivos.
func _scenario_d() -> void:
    _reset_goals(2)
    _start_phase(2)
    _game.no_damage = false
    _game.collected_coins = 99
    _game._finish_run(true)
    var estrelas_d1: int = _save.call("phase_stars", 2)
    _start_phase(2)
    _game.no_damage = true
    _game.collected_coins = 0
    _game._finish_run(true)
    var estrelas_d2: int = _save.call("phase_stars", 2)
    print("piloto: tentativa com moedas -> %d; depois sem dano -> %d" % [
            estrelas_d1, estrelas_d2])
    _check(estrelas_d1 == 2 and estrelas_d2 == 3,
            "D. piloto: moedas e corrida limpa em tentativas distintas = 3 estrelas")


# E. Modo de teste: colliders visíveis só quando o flag está ligado.
func _scenario_e() -> void:
    _game.debug_hitboxes = true
    _start_phase(0)
    var com_debug := 0
    for e in _game.entities:
        if e["node"].find_children("DebugHitbox", "MeshInstance3D", true, false).size() > 0:
            com_debug += 1
    _game.debug_hitboxes = false
    _start_phase(0)
    var sem_debug := 0
    for e in _game.entities:
        if e["node"].find_children("DebugHitbox", "MeshInstance3D", true, false).size() > 0:
            sem_debug += 1
    print("hitboxes: %d com flag ligado, %d desligado" % [com_debug, sem_debug])
    _check(com_debug > 5 and sem_debug == 0,
            "E. colisor visível apenas no modo de teste")


# F. Piloto intacto após as mudanças.
func _scenario_f() -> void:
    var resultado: Dictionary = PatternValidator.validate(LevelData.PILOT)
    _start_phase(2)
    _check(bool(resultado.get("valid", false)) and _game.entities.size() == 21,
            "F. piloto segue válido e com 21 entidades autorais")
