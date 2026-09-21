extends SceneTree
## ETAPA 9 — Teste de aceitação headless do lote 3 das 50 fases:
## fases 11–15 autorais + andaime/poça/floreira/ciclista/moto (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa9_lote3.gd
## Cenários:
##   S. dados das cinco fases conforme a tabela do plano + matriz das famílias
##   T. validador aprova as quinze fases do bairro (base e impulso 1,22x)
##   U. montagem exata: só as entidades dos dados, nada procedural
##   V. comportamentos: andaime, poça, ciclista, moto e rumo da travessia
##   W. ordem de aprendizagem + famílias novas seguras fora do nível
##   X. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 9 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_15()
    _scenario_s()
    _scenario_t()
    _scenario_u()
    _scenario_v()
    _scenario_w()
    _scenario_x()
    if _failures.is_empty():
        print("ETAPA9_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA9_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_15() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(14):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# S. Dados das cinco fases + matriz das famílias novas.
func _scenario_s() -> void:
    var esperado := [
        [10, "bairro_11", 392.0, 14, 6.6, 72.0],
        [11, "bairro_12", 392.0, 14, 6.6, 72.0],
        [12, "bairro_13", 420.0, 15, 6.8, 72.0],
        [13, "bairro_14", 420.0, 15, 6.8, 73.0],
        [14, "bairro_15", 448.0, 16, 7.0, 73.0],
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
        ["scaffold", ObstacleRules.Classe.SLIDE_UNDER, 1.3],
        ["puddle", ObstacleRules.Classe.SOFT, 1.2],
        ["planter", ObstacleRules.Classe.FULL, 1.3],
        ["cyclist", ObstacleRules.Classe.FULL, 1.1],
        ["moto_cross", ObstacleRules.Classe.VEHICLE, 1.0],
    ]
    for linha in matriz:
        var kind := str(linha[0])
        if ObstacleRules.classe_for(kind) != int(linha[1]) \
                or absf(ObstacleRules.hit_width(kind) - float(linha[2])) > 0.001 \
                or ObstacleData.entry(kind).is_empty():
            ok = false
            print("  família %s fora da matriz" % kind)
    var gates := {"scaffold": 10, "puddle": 11, "planter": 12, "cyclist": 12, "moto_cross": 13}
    for kind in gates.keys():
        if not (str(kind) in _game.SIDEWALK_OBSTACLES_GATED) \
                or int(_game.GATED_INTRO_PHASE.get(str(kind), -1)) != int(gates[kind]):
            ok = false
            print("  gate de %s incorreto" % str(kind))
    _check(ok, "S. fases 11–15: dados do plano, matriz das 5 famílias e gates")


# T. Validador aprova as quinze fases do bairro na base e no impulso.
func _scenario_t() -> void:
    var ok := true
    for index in range(15):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "T. validador aprova as 15 fases do bairro (base e impulso)")


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


# U. Montagem exata: nada de procedural nas fases autorais.
func _scenario_u() -> void:
    var ok := true
    for index in [10, 11, 12, 13, 14]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "U. fases 11–15 montadas só com os dados do nível")


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


# V. Andaime, poça, ciclista, moto e rumo da travessia.
func _scenario_v() -> void:
    var ok := true
    # V1 — andaime: deslizar resolve, pular não.
    _start_phase(10)
    var scaf: Dictionary = _find_entity("scaffold", 72.0)
    if scaf.is_empty():
        ok = false
        print("  andaime da fase 11 não montado")
    else:
        _set_player(1, 0.0)
        _game.slide_timer = 0.5
        _game._resolve_entity(scaf)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  deslizar sob o andaime deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(scaf)
        if _game.hearts != 2:
            ok = false
            print("  pular no andaime deveria causar dano (corações=%d)" % _game.hearts)
    # V2 — poça: pular resolve, atravessar molha o pé (lentidão, sem dano).
    _start_phase(11)
    var poc: Dictionary = _find_entity("puddle", 72.0)
    if poc.is_empty():
        ok = false
        print("  poça da fase 12 não montada")
    else:
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(poc)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a poça deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game._resolve_entity(poc)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  atravessar a poça deveria molhar o pé sem dano")
    # V3 — ciclista (FULL): dano no corredor bloqueado, limpo no livre.
    _start_phase(12)
    var cyc: Dictionary = _find_entity("cyclist", 100.0)
    if cyc.is_empty():
        ok = false
        print("  ciclista da fase 13 não montado")
    else:
        _emulate_approach(cyc, 81.5, 100.0, 6.8)
        var cyc_x: float = (cyc["node"] as Node3D).position.x
        print("  ciclista em x=%.2f na passagem" % cyc_x)
        _set_player(0, -3.25)
        _game._resolve_entity(cyc)
        if _game.hearts != 2:
            ok = false
            print("  ciclista no corredor deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cyc)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo ciclista")
    # V4 — moto (VEHICLE): nem o pulo resolve; livre passa limpo.
    _start_phase(13)
    var moto: Dictionary = _find_entity("moto_cross", 72.0)
    if moto.is_empty():
        ok = false
        print("  moto da fase 14 não montada")
    else:
        _emulate_approach(moto, 59.7, 72.0, 6.8)
        var moto_x: float = (moto["node"] as Node3D).position.x
        print("  moto em x=%.2f na passagem" % moto_x)
        _set_player(0, -3.25)
        _game.jump_timer = 0.5
        _game._resolve_entity(moto)
        if _game.hearts != 2:
            ok = false
            print("  pular na moto deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(moto)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pela moto")
    # V5 — modelos encaram o rumo (frente -Z: -X gira +90°, +X gira -90°).
    _start_phase(12)
    var cyc_ida: Dictionary = _find_entity("cyclist", 100.0)
    var cyc_volta: Dictionary = _find_entity("cyclist", 184.0)
    var rot_ida: float = (cyc_ida["node"] as Node3D).rotation.y if not cyc_ida.is_empty() else 999.0
    var rot_volta: float = (cyc_volta["node"] as Node3D).rotation.y if not cyc_volta.is_empty() else 999.0
    _start_phase(7)
    var cart: Dictionary = _find_entity("cart", 100.0)
    var rot_cart: float = (cart["node"] as Node3D).rotation.y if not cart.is_empty() else 999.0
    print("  rumos: ciclista=%.2f/%.2f carrinho=%.2f" % [rot_ida, rot_volta, rot_cart])
    if absf(rot_ida - PI / 2.0) > 0.01 or absf(rot_volta + PI / 2.0) > 0.01 \
            or absf(rot_cart - PI / 2.0) > 0.01:
        ok = false
        print("  modelos deveriam encarar o rumo da travessia")
    _check(ok, "V. andaime, poça, ciclista, moto e rumo da travessia")


# W. Ordem de aprendizagem + famílias novas seguras fora do nível.
func _scenario_w() -> void:
    var base := ["cone", "pothole", "scaffold", "bench"]
    var familias := {
        10: base,
        11: base + ["puddle"],
        12: base + ["puddle", "planter", "cyclist"],
        13: base + ["puddle", "planter", "cyclist", "moto_cross", "hydrant"],
        14: base + ["puddle", "planter", "cyclist", "moto_cross", "hydrant"],
    }
    var ok := true
    for index in [10, 11, 12, 13, 14]:
        var permitidas: Array = familias[index]
        for p in LevelData.for_phase(index)["patterns"]:
            if not permitidas.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var intros := {"scaffold": 10, "puddle": 11, "planter": 12, "cyclist": 12, "moto_cross": 13}
    for index in range(15):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if intros.has(kind) and index < int(intros[kind]):
                ok = false
                print("  %s aparece na fase %d antes da introdução" % [kind, index + 1])
    var novas_na_15 := false
    for p in LevelData.for_phase(14)["patterns"]:
        var kind := str(p["kind"])
        if intros.has(kind) and int(intros[kind]) == 14:
            novas_na_15 = true
    # W3 — fora do nível (pool procedural), as novas famílias nascem paradas
    # e resolvem pela regra da classe, sem travar.
    _start_phase(14)
    var estaticos := [
        ["scaffold", "slide"], ["puddle", "wade"], ["planter", "block"],
        ["cyclist", "block"], ["moto_cross", "block"],
    ]
    for linha in estaticos:
        var kind := str(linha[0])
        _game._spawn_entity(kind, 1, 60.0, false, true)
        var e: Dictionary = _find_entity(kind, 60.0)
        if e.is_empty():
            ok = false
            print("  %s estático não montou" % kind)
            continue
        _set_player(1, 0.0)
        if str(linha[1]) == "slide":
            _game.slide_timer = 0.5
        _game._resolve_entity(e)
        var esperado := 3
        if str(linha[1]) == "block":
            esperado = 2
        if _game.hearts != esperado:
            ok = false
            print("  %s estático: corações=%d (esperado %d)" % [kind, _game.hearts, esperado])
    _check(ok and not novas_na_15,
            "W. ordem de aprendizagem, fase 15 como revisão e novas famílias seguras paradas")


# X. Determinismo: percursos autorais independem de semente.
func _scenario_x() -> void:
    var ok := true
    for index in [10, 11, 12, 13, 14]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "X. percursos autorais independem de semente")
