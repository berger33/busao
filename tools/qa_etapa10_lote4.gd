extends SceneTree
## ETAPA 10 — Teste de aceitação headless do lote 4 das 50 fases:
## fases 16–20 autorais + cachorro/caixa/caminhão/ônibus (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa10_lote4.gd
## Cenários:
##   L4-A. dados das cinco fases conforme a tabela do plano + matriz e gates
##   L4-B. validador aprova as vinte fases do bairro (base e impulso 1,22x)
##   L4-C. montagem exata: só as entidades dos dados, nada procedural
##   L4-D. comportamentos: cachorro, caixa, caminhão, ônibus, rumos e zonas
##   L4-E. ordem de aprendizagem + famílias novas seguras fora do nível
##   L4-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 10 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_20()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA10_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA10_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_20() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(19):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L4-A. Dados das cinco fases + matriz das famílias novas + gates + cenário.
func _scenario_a() -> void:
    var esperado := [
        [15, "bairro_16", 420.0, 15, 7.0, 71.0],
        [16, "bairro_17", 448.0, 16, 7.2, 73.0],
        [17, "bairro_18", 448.0, 16, 7.2, 73.0],
        [18, "bairro_19", 476.0, 17, 7.4, 74.0],
        [19, "bairro_20", 504.0, 18, 7.5, 76.0],
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
        ["dog_cross", ObstacleRules.Classe.SOFT, 0.9],
        ["crate", ObstacleRules.Classe.LOW, 1.0],
        ["truck_cross", ObstacleRules.Classe.VEHICLE, 1.4],
        ["bus_cross", ObstacleRules.Classe.VEHICLE, 1.4],
    ]
    for linha in matriz:
        var kind := str(linha[0])
        if ObstacleRules.classe_for(kind) != int(linha[1]) \
                or absf(ObstacleRules.hit_width(kind) - float(linha[2])) > 0.001 \
                or ObstacleData.entry(kind).is_empty():
            ok = false
            print("  família %s fora da matriz" % kind)
    var gates := {"dog_cross": 15, "crate": 16, "truck_cross": 17, "bus_cross": 17}
    for kind in gates.keys():
        if not (str(kind) in _game.SIDEWALK_OBSTACLES_GATED) \
                or int(_game.GATED_INTRO_PHASE.get(str(kind), -1)) != int(gates[kind]):
            ok = false
            print("  gate de %s incorreto" % str(kind))
    for index in [15, 16, 17, 18, 19]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        if str(scenery.get("props", {}).get("arvore", {}).get("glb", "")) != "palmeira":
            ok = false
            print("  fase %d sem palmeira no cenário" % [index + 1])
    var scenery_15: Dictionary = LevelData.for_phase(14).get("scenery", {})
    if not scenery_15.get("props", {}).is_empty():
        ok = false
        print("  fase 15 não deveria ter props de cenário")
    _check(ok, "L4-A. fases 16–20: dados do plano, matriz, gates e palmeiras")


# L4-B. Validador aprova as vinte fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(20):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L4-B. validador aprova as 20 fases do bairro (base e impulso)")


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


# L4-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [15, 16, 17, 18, 19]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L4-C. fases 16–20 montadas só com os dados do nível")


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


func _nomes_descendentes(no: Node) -> String:
    var resultado := ""
    for filho in no.get_children():
        resultado += "|" + filho.name
        resultado += _nomes_descendentes(filho)
    return resultado


func _arvores_do_kit(nome_procurado: String) -> int:
    var achadas := 0
    var kit: Node3D = _game._world_kit
    if kit == null:
        return 0
    for no in kit.find_children("*", "Node3D", true, false):
        if no.has_meta("superficie") and str(no.get_meta("superficie")) == "arvore":
            if (no.name + _nomes_descendentes(no)).find(nome_procurado) >= 0:
                achadas += 1
    return achadas


func _zonas_sinalizadas() -> Array:
    # Sem frames entre as fases, os nós liberados seguem na árvore e os novos
    # ganham nomes opacos (@Node3D@N); a zona é achada pela base zebrada
    # (nome exato dentro do pai novo) e a identidade vem da posição.
    var zonas: Array = []
    for base in _game.entity_root.find_children("CrossZoneBase", "MeshInstance3D", true, false):
        var zona := (base as Node).get_parent() as Node3D
        if zona != null and is_instance_valid(zona) and not zona.is_queued_for_deletion():
            zonas.append(zona)
    return zonas


# L4-D. Cachorro, caixa, caminhão, ônibus, rumos, zonas e palmeiras.
func _scenario_d() -> void:
    var ok := true
    # D1 — cachorro (SOFT): esbarra sem dano e SEM perseguição.
    _start_phase(15)
    var dog: Dictionary = _find_entity("dog_cross", 72.0)
    if dog.is_empty():
        ok = false
        print("  cachorro da fase 16 não montado")
    else:
        _emulate_approach(dog, 49.2, 72.0, 7.0)
        var dog_x: float = (dog["node"] as Node3D).position.x
        print("  cachorro em x=%.2f na passagem (mobilidade=%.1f)" % [dog_x, float(dog.get("mobility", -1.0))])
        if absf(dog_x + 3.25) > 0.05 or absf(float(dog.get("mobility", -1.0))) > 0.001:
            ok = false
            print("  cachorro deveria bloquear E parado na borda, sem mobilidade")
        _set_player(0, -3.25)
        _game._resolve_entity(dog)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no cachorro deveria tropeçar sem dano")
        if _game.dog_chase_timer > 0.0:
            ok = false
            print("  cachorro da fase 16 não deveria perseguir")
    # D2 — caixa (LOW): pular resolve; parado sofre dano.
    _start_phase(16)
    var box: Dictionary = _find_entity("crate", 72.0)
    if box.is_empty():
        ok = false
        print("  caixa da fase 17 não montada")
    else:
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(box)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a caixa deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game._resolve_entity(box)
        if _game.hearts != 2:
            ok = false
            print("  bater na caixa deveria causar dano (corações=%d)" % _game.hearts)
    # D3 — caminhão (VEHICLE): nem o pulo resolve; livre passa limpo.
    _start_phase(17)
    var truck: Dictionary = _find_entity("truck_cross", 72.0)
    if truck.is_empty():
        ok = false
        print("  caminhão da fase 18 não montado")
    else:
        _emulate_approach(truck, 54.9, 72.0, 7.2)
        var truck_x: float = (truck["node"] as Node3D).position.x
        print("  caminhão em x=%.2f na passagem" % truck_x)
        if absf(truck_x + 3.25) > 0.05:
            ok = false
            print("  nariz do caminhão deveria bloquear E na passagem")
        _set_player(0, -3.25)
        _game.jump_timer = 0.5
        _game._resolve_entity(truck)
        if _game.hearts != 2:
            ok = false
            print("  pular no caminhão deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(truck)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo caminhão")
    # D4 — ônibus (VEHICLE): nem o pulo resolve; livre passa limpo.
    var bus: Dictionary = _find_entity("bus_cross", 128.0)
    if bus.is_empty():
        ok = false
        print("  ônibus da fase 18 não montado")
    else:
        _emulate_approach(bus, 99.2, 128.0, 7.2)
        var bus_x: float = (bus["node"] as Node3D).position.x
        print("  ônibus em x=%.2f na passagem" % bus_x)
        if absf(bus_x) > 0.05:
            ok = false
            print("  nariz do ônibus deveria bloquear C na passagem")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(bus)
        if _game.hearts != 2:
            ok = false
            print("  pular no ônibus deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(bus)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo ônibus")
    # D5 — área sinalizada: faixa no chão sob cada cruzamento pesado.
    var zonas_18 := _zonas_sinalizadas()
    var ats_18: Array = []
    for z in zonas_18:
        ats_18.append(-(z as Node3D).position.z)
    ats_18.sort()
    print("  zonas fase 18 em: %s" % str(ats_18))
    if ats_18 != [72.0, 128.0, 184.0, 296.0, 312.0]:
        ok = false
        print("  fase 18 deveria ter 5 zonas sinalizadas (uma por pesado)")
    else:
        for z in zonas_18:
            if (z as Node3D).get_child_count() != 6:
                ok = false
                print("  zona em %.0f m incompleta" % (-(z as Node3D).position.z))
    _start_phase(19)
    var zonas_20 := _zonas_sinalizadas()
    if zonas_20.size() != 1 or absf((zonas_20[0] as Node3D).position.z + 352.0) > 0.01:
        ok = false
        print("  fase 20 deveria ter só a zona do caminhão (352 m)")
    _start_phase(15)
    if not _zonas_sinalizadas().is_empty():
        ok = false
        print("  fase 16 não deveria ter zona sinalizada")
    # D6 — rumos: pesados encaram +X (-90°); cachorro encara o rumo (0/180°).
    _start_phase(17)
    var truck_r: Dictionary = _find_entity("truck_cross", 72.0)
    var bus_r: Dictionary = _find_entity("bus_cross", 128.0)
    var rot_truck: float = (truck_r["node"] as Node3D).rotation.y if not truck_r.is_empty() else 999.0
    var rot_bus: float = (bus_r["node"] as Node3D).rotation.y if not bus_r.is_empty() else 999.0
    _start_phase(15)
    var dog_ida: Dictionary = _find_entity("dog_cross", 72.0)
    var dog_volta: Dictionary = _find_entity("dog_cross", 156.0)
    var dog_trio: Dictionary = _find_entity("dog_cross", 296.0)
    var rot_dog_ida: float = (dog_ida["node"] as Node3D).rotation.y if not dog_ida.is_empty() else 999.0
    var rot_dog_volta: float = (dog_volta["node"] as Node3D).rotation.y if not dog_volta.is_empty() else 999.0
    var rot_dog_trio: float = (dog_trio["node"] as Node3D).rotation.y if not dog_trio.is_empty() else 999.0
    print("  rumos: caminhão=%.2f ônibus=%.2f cachorro=%.2f/%.2f/%.2f" % [rot_truck, rot_bus, rot_dog_ida, rot_dog_volta, rot_dog_trio])
    if absf(rot_truck + PI / 2.0) > 0.01 or absf(rot_bus + PI / 2.0) > 0.01 \
            or absf(rot_dog_ida - PI) > 0.01 or absf(rot_dog_volta) > 0.01 \
            or absf(rot_dog_trio - PI) > 0.01:
        ok = false
        print("  modelos deveriam encarar o rumo da travessia")
    # D7 — nariz na origem: a ponta colide, a carroceria vai a reboque.
    _start_phase(17)
    var truck_n: Dictionary = _find_entity("truck_cross", 72.0)
    var bus_n: Dictionary = _find_entity("bus_cross", 128.0)
    if truck_n.is_empty() or bus_n.is_empty():
        ok = false
        print("  pesados da fase 18 não montados para o nariz")
    else:
        var farol := (truck_n["node"] as Node3D).find_child("TruckHeadlight", true, false) as Node3D
        var bau := (truck_n["node"] as Node3D).find_child("TruckCargo", true, false) as Node3D
        var parabrisa := (bus_n["node"] as Node3D).find_child("BusWindshield", true, false) as Node3D
        var corpo := (bus_n["node"] as Node3D).find_child("BusBody", true, false) as Node3D
        if farol == null or bau == null or parabrisa == null or corpo == null:
            ok = false
            print("  peças do nariz/carroceria não encontradas")
        else:
            print("  nariz: farol z=%.2f baú z=%.2f parabrisa z=%.2f corpo z=%.2f" % [
                    farol.position.z, bau.position.z, parabrisa.position.z, corpo.position.z])
            if absf(farol.position.z) > 0.05 or bau.position.z < 3.0 \
                    or absf(parabrisa.position.z - 0.02) > 0.05 or corpo.position.z < 3.0:
                ok = false
                print("  nariz deveria estar na origem, com a carroceria atrás")
    # D8 — palmeiras: contrato do asset + avenida com palmeiras, fase 15 sem.
    var palmeira: PackedScene = load("res://assets/scene/palmeira.glb")
    if palmeira == null:
        ok = false
        print("  palmeira.glb não importa como cena")
    else:
        var modelo: Node3D = palmeira.instantiate()
        var tem_malha := not modelo.find_children("*", "MeshInstance3D", true, false).is_empty()
        var caixa := AABB()
        var primeira := true
        for mi in modelo.find_children("*", "MeshInstance3D", true, false):
            var recorte: AABB = (mi as MeshInstance3D).get_aabb()
            recorte.position += (mi as Node3D).position
            if primeira:
                caixa = recorte
                primeira = false
            else:
                caixa = caixa.merge(recorte)
        print("  palmeira.glb AABB: y %.2f..%.2f" % [caixa.position.y, caixa.end.y])
        if not tem_malha or absf(caixa.position.y) > 0.5 or caixa.end.y < 2.0:
            ok = false
            print("  palmeira.glb fora do contrato (origem no chão, árvore > 2 m)")
        modelo.free()
    _start_phase(15)
    var palmeiras_16: int = _arvores_do_kit("palmeira")
    print("  palmeiras no cenário da fase 16: %d" % palmeiras_16)
    if palmeiras_16 < 2:
        ok = false
        print("  fase 16 deveria ter palmeiras no cenário")
    _start_phase(14)
    var palmeiras_15: int = _arvores_do_kit("palmeira")
    var comuns_15: int = _arvores_do_kit("arvore")
    print("  fase 15: %d árvores comuns, %d palmeiras" % [comuns_15, palmeiras_15])
    if comuns_15 < 2 or palmeiras_15 != 0:
        ok = false
        print("  fase 15 deveria seguir com a árvore comum")
    _check(ok, "L4-D. cachorro, caixa, caminhão, ônibus, rumos, zonas e palmeiras")


# L4-E. Ordem de aprendizagem + famílias novas seguras fora do nível.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(15):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var intros := {"dog_cross": 15, "crate": 16, "truck_cross": 17, "bus_cross": 17}
    var ok := true
    for index in [15, 16, 17, 18, 19]:
        var permitidas: Array = base.duplicate()
        for kind in intros.keys():
            if index >= int(intros[kind]):
                permitidas.append(str(kind))
        for p in LevelData.for_phase(index)["patterns"]:
            if not permitidas.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    for index in range(20):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if intros.has(kind) and index < int(intros[kind]):
                ok = false
                print("  %s aparece na fase %d antes da introdução" % [kind, index + 1])
    var estreia := {}
    for index in range(20):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) == 18 or int(estreia[kind]) == 19:
            ok = false
            print("  %s estreia na fase %d (revisão não introduz família)" % [str(kind), int(estreia[kind]) + 1])
    # E4 — fora do nível (pool procedural), as novas famílias nascem paradas
    # e resolvem pela regra da classe, sem travar.
    _start_phase(19)
    _game._spawn_entity("dog_cross", 1, 60.0, false, true)
    var dog_parado: Dictionary = _find_entity("dog_cross", 60.0)
    if dog_parado.is_empty():
        ok = false
        print("  cachorro parado não montou")
    else:
        _set_player(1, 0.0)
        _game._resolve_entity(dog_parado)
        if _game.hearts != 3 or _game.invulnerability <= 0.0 or _game.dog_chase_timer > 0.0:
            ok = false
            print("  cachorro parado deveria tropeçar sem dano nem perseguição")
    _game._spawn_entity("crate", 1, 60.0, false, true)
    var caixa_parada: Dictionary = _find_entity("crate", 60.0)
    if caixa_parada.is_empty():
        ok = false
        print("  caixa parada não montou")
    else:
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(caixa_parada)
        if _game.hearts != 3:
            ok = false
            print("  pular a caixa parada deveria ser limpo")
    for pesado in ["truck_cross", "bus_cross"]:
        _game._spawn_entity(pesado, 1, 60.0, false, true)
        var parado: Dictionary = _find_entity(pesado, 60.0)
        if parado.is_empty():
            ok = false
            print("  %s parado não montou" % pesado)
            continue
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(parado)
        if _game.hearts != 2:
            ok = false
            print("  pular no %s parado deveria causar dano" % pesado)
        var rot_parado: float = (parado["node"] as Node3D).rotation.y
        if absf(rot_parado - PI) > 0.01:
            ok = false
            print("  %s parado deveria encarar quem chega (180°)" % pesado)
    _check(ok, "L4-E. ordem de aprendizagem, revisão sem estreia e novas famílias seguras paradas")


# L4-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [15, 16, 17, 18, 19]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L4-F. percursos autorais independem de semente")
