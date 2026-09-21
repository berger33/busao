extends SceneTree
## ETAPA 8 — Teste de aceitação headless do lote 2 das 50 fases:
## fases 6–10 autorais + famílias dinâmicas (PLANO_50_FASES §"Comércio e praça").
## Rodar: godot --headless --path . -s res://tools/qa_etapa8_lote2.gd
## Cenários:
##   M. dados das cinco fases conforme a tabela do plano + matriz das famílias
##   N. validador aprova as dez fases do bairro (base e impulso 1,22x)
##   O. montagem exata: só as entidades dos dados, nada procedural
##   P. travessias laterais: espera, cruzamento no relógio da simulação e colisão real
##   Q. ordem de aprendizagem: cada fase usa só famílias já apresentadas
##   R. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 8 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_10()
    _scenario_m()
    _scenario_n()
    _scenario_o()
    _scenario_p()
    _scenario_q()
    _scenario_r()
    if _failures.is_empty():
        print("ETAPA8_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA8_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_10() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(9):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# M. Dados das cinco fases + matriz das famílias novas.
func _scenario_m() -> void:
    var esperado := [
        [5, "bairro_06", 364.0, 13, 6.2, 71.0],
        [6, "bairro_07", 364.0, 13, 6.3, 70.0],
        [7, "bairro_08", 392.0, 14, 6.4, 73.0],
        [8, "bairro_09", 392.0, 14, 6.5, 72.0],
        [9, "bairro_10", 420.0, 15, 6.5, 75.0],
    ]
    var ok := true
    for linha in esperado:
        var level: Dictionary = LevelData.for_phase(int(linha[0]))
        if level.is_empty() or str(level["id"]) != str(linha[1]) \
                or absf(float(level["distance_m"]) - float(linha[2])) > 0.01 \
                or int(level["chunks"]) != int(linha[3]) \
                or absf(float(level["base_speed_mps"]) - float(linha[4])) > 0.01 \
                or absf(float(level["deadline_seconds"]) - float(linha[5])) > 0.01 \
                or absf(float(level["chunks"]) * 28.0 - float(level["distance_m"])) > 0.01 \
                or absf(_game._phase_speed_for(int(linha[0])) - float(linha[4])) > 0.01 \
                or absf(_game._phase_deadline_for(int(linha[0])) - float(linha[5])) > 0.01:
            ok = false
            print("  fase %s diverge: %s" % [str(linha[0]), str(level)])
    var matriz := [
        ["trash", ObstacleRules.Classe.FULL, 0.8],
        ["crosser", ObstacleRules.Classe.SOFT, 0.9],
        ["cart", ObstacleRules.Classe.FULL, 1.3],
        ["van", ObstacleRules.Classe.VEHICLE, 1.3],
    ]
    for linha in matriz:
        var kind := str(linha[0])
        if ObstacleRules.classe_for(kind) != int(linha[1]) \
                or absf(ObstacleRules.hit_width(kind) - float(linha[2])) > 0.001 \
                or ObstacleData.entry(kind).is_empty():
            ok = false
            print("  família %s fora da matriz" % kind)
    var gates := {"trash": 5, "crosser": 6, "cart": 7, "van": 8}
    for kind in gates.keys():
        if not (str(kind) in _game.SIDEWALK_OBSTACLES_GATED) \
                or int(_game.GATED_INTRO_PHASE.get(str(kind), -1)) != int(gates[kind]):
            ok = false
            print("  gate de %s incorreto" % str(kind))
    _check(ok, "M. fases 6–10: dados do plano, matriz das 4 famílias e gates de introdução")


# N. Validador aprova as dez fases do bairro na base e no impulso.
func _scenario_n() -> void:
    var ok := true
    for index in range(10):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "N. validador aprova as 10 fases do bairro (base e impulso)")


func _assinatura_entidades() -> String:
    var partes: Array = []
    for e in _game.entities:
        partes.append("%s|%d|%d|%s" % [str(e["kind"]), int(e["lane"]),
                int(roundf(float(e["distance"]) * 10.0)),
                "c" if bool(e["collectible"]) else "o"])
    partes.sort()
    return ";".join(partes)


func _assinatura_esperada(index: int) -> String:
    var level: Dictionary = LevelData.for_phase(index)
    var partes: Array = []
    for p in level.get("patterns", []):
        partes.append("%s|%d|%d|o" % [str(p["kind"]), int(p["lane"]), int(roundf(float(p["at_m"]) * 10.0))])
    for c in level.get("coins", []):
        partes.append("%s|%d|%d|c" % [str(c["kind"]), int(c["lane"]), int(roundf(float(c["at_m"]) * 10.0))])
    partes.sort()
    return ";".join(partes)


# O. Montagem exata: nada de procedural nas fases autorais.
func _scenario_o() -> void:
    var ok := true
    for index in [5, 6, 7, 8, 9]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "O. fases 6–10 montadas só com os dados do nível")


func _find_entity(kind: String, at_m: float) -> Dictionary:
    for e in _game.entities:
        if str(e["kind"]) == kind and absf(float(e["distance"]) - at_m) < 0.01:
            return e
    return {}


func _emulate_approach(entity: Dictionary, start_d: float, at_m: float, speed: float) -> void:
    var node: Node3D = entity["node"]
    _game.distance = start_d
    _game.elapsed = start_d / speed
    _game._update_crossing(entity, node)
    _game.distance = at_m
    _game.elapsed = at_m / speed
    _game._update_crossing(entity, node)


func _set_player(lane: int, x: float) -> void:
    _game.player_lane = lane
    _game.player_x = x
    _game.jump_timer = 0.0
    _game.slide_timer = 0.0
    _game.invulnerability = 0.0
    _game.hearts = 3


# P. Travessias laterais: espera, cruzamento e colisão pela posição real.
func _scenario_p() -> void:
    var ok := true
    # P1 — matemática pura da travessia (pedestre da fase 7, 72 m).
    var c: Dictionary = {"from_x": 4.9, "to_x": -3.25, "start_d": 32.0,
            "cross_mps": 1.3, "t_start": -1.0}
    if absf(_game._crossing_x(c, 10.0, 1.0) - 4.9) > 0.001:
        ok = false
        print("  antes do gatilho o pedestre não espera no ponto de partida")
    c["t_start"] = 32.0 / 6.3
    if absf(_game._crossing_x(c, 72.0, 72.0 / 6.3) + 3.25) > 0.01:
        ok = false
        print("  pedestre não completa a travessia na chegada (base 6,3 m/s)")
    # P2 — pedestre real: esbarrão (SOFT) no corredor bloqueado, limpo no livre.
    _start_phase(6)
    var ped: Dictionary = _find_entity("crosser", 72.0)
    if ped.is_empty():
        ok = false
        print("  pedestre da fase 7 não montado")
    else:
        _emulate_approach(ped, 32.0, 72.0, 6.3)
        var ped_x: float = (ped["node"] as Node3D).position.x
        print("  pedestre em x=%.2f na passagem" % ped_x)
        _set_player(0, -3.25)
        _game._resolve_entity(ped)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrão no pedestre deveria tropeçar sem dano")
        _set_player(1, 0.0)
        _game._resolve_entity(ped)
        if _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo pedestre")
    # P3 — carrinho real (FULL): dano no corredor bloqueado, limpo no livre.
    _start_phase(7)
    var cart: Dictionary = _find_entity("cart", 100.0)
    if cart.is_empty():
        ok = false
        print("  carrinho da fase 8 não montado")
    else:
        _emulate_approach(cart, 48.0, 100.0, 6.4)
        var cart_x: float = (cart["node"] as Node3D).position.x
        print("  carrinho em x=%.2f na passagem" % cart_x)
        _set_player(0, -3.25)
        _game._resolve_entity(cart)
        if _game.hearts != 2:
            ok = false
            print("  carrinho no corredor deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cart)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo carrinho")
    _check(ok, "P. travessias: espera, cruzamento no relógio e colisão real (SOFT/FULL)")


# Q. Ordem de aprendizagem (introduções do blueprint §6).
func _scenario_q() -> void:
    var base := ["cone", "hydrant", "payphone", "trash"]
    var familias := {
        5: base,
        6: base + ["bench", "crosser"],
        7: base + ["bench", "crosser", "cart"],
        8: base + ["bench", "crosser", "cart", "van", "barrier"],
        9: base + ["bench", "crosser", "cart", "van", "barrier"],
    }
    var ok := true
    for index in [5, 6, 7, 8, 9]:
        var permitidas: Array = familias[index]
        for p in LevelData.for_phase(index)["patterns"]:
            if not permitidas.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    # Nenhuma família nova aparece antes da sua fase de introdução.
    var intros := {"trash": 5, "crosser": 6, "cart": 7, "van": 8}
    for index in range(10):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if intros.has(kind) and index < int(intros[kind]):
                ok = false
                print("  %s aparece na fase %d antes da introdução" % [kind, index + 1])
    # Fase 10 é revisão: nada estreado nela.
    var novas_na_10 := false
    for p in LevelData.for_phase(9)["patterns"]:
        var kind := str(p["kind"])
        if intros.has(kind) and int(intros[kind]) == 9:
            novas_na_10 = true
    _check(ok and not novas_na_10,
            "Q. ordem de aprendizagem: introduções 6→9 e fase 10 como revisão")


# R. Determinismo: percursos autorais independem de semente.
func _scenario_r() -> void:
    var ok := true
    for index in [5, 6, 7, 8, 9]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "R. percursos autorais independem de semente")
