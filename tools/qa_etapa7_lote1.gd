extends SceneTree
## ETAPA 7 — Teste de aceitação headless do lote 1 das 50 fases:
## fases 1, 2, 4 e 5 autorais (PLANO_50_FASES §"Sequência de entrega").
## Rodar: godot --headless --path . -s res://tools/qa_etapa7_lote1.gd
## Cenários:
##   G. dados das quatro fases conforme a tabela do plano
##   H. validador aprova as cinco fases do bairro (base e impulso 1,22x)
##   I. montagem exata: só as entidades dos dados, nada procedural
##   J. ordem de aprendizagem: cada fase usa só as famílias já apresentadas
##   K. visual de calçada nos três corredores (buraco e mobiliário)
##   L. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 7 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_all_first_five()
    _scenario_g()
    _scenario_h()
    _scenario_i()
    _scenario_j()
    _scenario_k()
    _scenario_l()
    if _failures.is_empty():
        print("ETAPA7_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA7_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_all_first_five() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(4):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# G. Dados das quatro fases conforme a tabela do PLANO_50_FASES.
func _scenario_g() -> void:
    var esperado := [
        [0, "bairro_01", 224.0, 8, 5.5, 55.0],
        [1, "bairro_02", 280.0, 10, 5.8, 61.0],
        [3, "bairro_04", 336.0, 12, 6.0, 68.0],
        [4, "bairro_05", 364.0, 13, 6.2, 69.0],
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
    _check(ok, "G. fases 1/2/4/5: distância, módulos, velocidade e prazo do plano")


# H. Validador aprova as cinco fases do bairro na base e no impulso.
func _scenario_h() -> void:
    var ok := true
    for index in [0, 1, 2, 3, 4]:
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s" % [index + 1, str(resultado.get("reason"))])
    _check(ok, "H. validador aprova as 5 fases do bairro (base e impulso)")


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


# I. Montagem exata: nada de procedural nas fases autorais.
func _scenario_i() -> void:
    var ok := true
    for index in [0, 1, 3, 4]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "I. fases 1/2/4/5 montadas só com os dados do nível")


# J. Ordem de aprendizagem (introduções do blueprint §6).
func _scenario_j() -> void:
    var familias := {0: ["cone"], 1: ["cone", "bench"], 3: ["cone", "bench", "barrier", "pothole"],
            4: ["cone", "bench", "barrier", "pothole"]}
    var ok := true
    for index in [0, 1, 3, 4]:
        var permitidas: Array = familias[index]
        for p in LevelData.for_phase(index)["patterns"]:
            if not permitidas.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var barreira_cedo := false
    for index in [0, 1]:
        for p in LevelData.for_phase(index)["patterns"]:
            if str(p["kind"]) == "barrier":
                barreira_cedo = true
    _check(ok and not barreira_cedo,
            "J. ordem de aprendizagem: fase 1 só cone; fase 2 cone+banco; barreira só após a fase 3")


# K. Visual de calçada nos três corredores (buraco e mobiliário).
func _scenario_k() -> void:
    _start_phase(3)
    var buracos_com_visual := 0
    var genericos := 0
    for e in _game.entities:
        if bool(e["collectible"]):
            continue
        var nomes := ""
        var no: Node = e["node"]
        var pilha: Array = [no]
        while not pilha.is_empty():
            var atual: Node = pilha.pop_back()
            nomes += "|" + atual.name
            for filho in atual.get_children():
                pilha.append(filho)
        if str(e["kind"]) == "pothole" and nomes.to_lower().find("pothole") >= 0:
            buracos_com_visual += 1
        if nomes.find("RoadHazard") >= 0 or nomes.find("SidewalkHazard") >= 0:
            genericos += 1
    print("fase 4: %d buracos com visual, %d caixas genéricas" % [buracos_com_visual, genericos])
    _check(buracos_com_visual == 6 and genericos == 0,
            "K. buracos com visual próprio e nenhum obstáculo genérico nos corredores")


# L. Determinismo: percursos autorais independem de semente.
func _scenario_l() -> void:
    var ok := true
    for index in [0, 1, 3, 4]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L. percursos autorais independem de semente")
