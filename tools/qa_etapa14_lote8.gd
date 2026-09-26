extends SceneTree
## ETAPA 14 — Teste de aceitação headless do lote 8 das 50 fases:
## fases 36–40 autorais Depois da chuva, sem família nova (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa14_lote8.gd
## Cenários:
##   L8-A. dados das cinco fases + gates intactos + cenário de chuva
##   L8-B. validador aprova as 40 fases do bairro (base e impulso 1,22x)
##   L8-C. montagem exata: só as entidades dos dados, nada procedural
##   L8-D. comportamentos: poças, piso seco, obra, entrega e clima
##   L8-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L8-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 14 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    if _game._clima == null:
        # O _ready só chega ao clima depois de awaits longos (serviços);
        # o QA monta o sistema na hora para testar o estado por fase
        # (_ready não retoma sem novos frames: sem duplicar o nó).
        _game._setup_clima()
    _unlock_up_to_phase_41()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA14_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA14_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_41() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(40):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L8-A. Dados das cinco fases + gates intactos + cenário de chuva.
func _scenario_a() -> void:
    var esperado := [
        [35, "bairro_36", 476.0, 17, 7.8, 74.0],
        [36, "bairro_37", 504.0, 18, 8.0, 74.0],
        [37, "bairro_38", 532.0, 19, 8.1, 76.0],
        [38, "bairro_39", 532.0, 19, 8.2, 74.0],
        [39, "bairro_40", 560.0, 20, 8.3, 76.0],
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
    var intros: Dictionary = _game.GATED_INTRO_PHASE
    var max_intro := 0
    for kind in intros.keys():
        max_intro = maxi(max_intro, int(intros[kind]))
    if max_intro != 17 or int(intros.get("dog_cross", -1)) != 15 \
            or int(intros.get("crate", -1)) != 16 \
            or int(intros.get("truck_cross", -1)) != 17 \
            or int(intros.get("bus_cross", -1)) != 17:
        ok = false
        print("  gates alterados no lote sem família nova")
    for index in [35, 36, 37, 38, 39]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var pesos: Dictionary = scenery.get("predios", {}).get("tipo_pesos", {})
        var props: Dictionary = scenery.get("props", {})
        if int(pesos.get("tijolo", -1)) != 3 or int(pesos.get("reboco", -1)) != 4 \
                or int(pesos.get("loja", -1)) != 2 or int(pesos.get("obra", -1)) != 1 \
                or str(props.get("arvore", {}).get("glb", "")) != "arvore" \
                or absf(float(props.get("arvore", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 14.0) > 0.01 \
                or absf(float(props.get("lixeira", {}).get("espacamento_m", 0.0)) - 18.0) > 0.01 \
                or scenery.has("marco") or scenery.has("quiosques") or scenery.has("feira"):
            ok = false
            print("  fase %d sem cenário da rua molhada" % [index + 1])
    for index in [35, 36, 37, 38]:
        if str(LevelData.for_phase(index).get("scenery", {}).get("clima", "")) != "chuva":
            ok = false
            print("  fase %d sem chuva fixa" % [index + 1])
    if str(LevelData.for_phase(39).get("scenery", {}).get("clima", "")) != "limpo":
        ok = false
        print("  fase 40 sem sol de volta")
    var dia_36: Dictionary = LevelData.for_phase(35).get("scenery", {}).get("paleta", {})
    var sol_40: Dictionary = LevelData.for_phase(39).get("scenery", {}).get("paleta", {})
    if str(dia_36.get("nome", "")) != "chuva_dia" or str(sol_40.get("nome", "")) != "sol" \
            or absf(float(dia_36.get("nevoa_densidade", 0.0)) - 0.5) > 0.001 \
            or absf(float(sol_40.get("nevoa_densidade", 0.0)) - 0.5) > 0.001:
        ok = false
        print("  fases 36 e 40 sem paleta de dia (rodízio daria noite)")
    for index in [36, 37, 38]:
        if LevelData.for_phase(index).get("scenery", {}).has("paleta"):
            ok = false
            print("  fase %d deveria usar o rodízio de luz" % [index + 1])
    var orla: Dictionary = LevelData.for_phase(34).get("scenery", {})
    if orla.has("clima") or not orla.has("quiosques") \
            or str(orla.get("marco", "")) != "guarita":
        ok = false
        print("  fase 35 deveria seguir na orla, sem clima fixo")
    _check(ok, "L8-A. fases 36–40: dados do plano, gates intactos e cenário")


# L8-B. Validador aprova as 40 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(40):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L8-B. validador aprova as 40 fases do bairro (base e impulso)")


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


# L8-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [35, 36, 37, 38, 39]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L8-C. fases 36–40 montadas só com os dados do nível")


func _find_entity(kind: String, at_m: float) -> Dictionary:
    for e in _game.entities:
        if str(e["kind"]) == kind and absf(float(e["distance"]) - at_m) < 0.01:
            return e
    return {}


func _count_entities(kind: String, lane: int, at_m: float) -> int:
    var n := 0
    for e in _game.entities:
        if str(e["kind"]) == kind and int(e["lane"]) == lane \
                and absf(float(e["distance"]) - at_m) < 0.01:
            n += 1
    return n


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
            # ETAPA 13 — comparação sem maiúsculas: os repetidos viram
            # @Node3D@N e os filhos do GLB mantêm maiúsculas.
            if (no.name + _nomes_descendentes(no)).to_lower().find(nome_procurado) >= 0:
                achadas += 1
    return achadas


func _superficies_do_kit(superficie: String) -> int:
    var achadas := 0
    var kit: Node3D = _game._world_kit
    if kit == null:
        return 0
    for no in kit.find_children("*", "Node3D", true, false):
        var n: Node = no
        var liberado := false
        while n != null:
            if n.is_queued_for_deletion():
                liberado = true
            n = n.get_parent()
        if no.has_meta("superficie") and str(no.get_meta("superficie")) == superficie \
                and not liberado:
            achadas += 1
    return achadas


# L8-D. Poças, piso seco, obra, entrega e clima.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 36: poça (SOFT) — pular resolve, pisar molha o pé.
    _start_phase(35)
    var poca: Dictionary = _find_entity("puddle", 184.0)
    if poca.is_empty():
        ok = false
        print("  poça da fase 36 não montada")
    else:
        _set_player(0, -3.25)
        _game._resolve_entity(poca)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pela poça de C")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(poca)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a poça deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game.slow_motion_timer = 0.0
        _game._resolve_entity(poca)
        if _game.hearts != 3 or _game.invulnerability <= 0.0 \
                or _game.slow_motion_timer <= 0.0:
            ok = false
            print("  pisar na poça deveria molhar o pé sem dano (lentidão)")
    # D2 — fase 37: moedas sobre a poça (recompensa) e laterais secas.
    _start_phase(36)
    if _find_entity("puddle", 128.0).is_empty() \
            or _count_entities("coin", 1, 120.0) != 1 \
            or _count_entities("coin", 1, 128.0) != 1 \
            or _count_entities("coin", 1, 136.0) != 1:
        ok = false
        print("  rota de recompensa da fase 37 não montada")
    else:
        var seca := true
        for e in _game.entities:
            if not bool(e["collectible"]) and absf(float(e["distance"]) - 128.0) < 0.01 \
                    and int(e["lane"]) != 1:
                seca = false
        if not seca:
            ok = false
            print("  E e D deveriam seguir secos na estação 128")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(_find_entity("puddle", 128.0))
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a poça premiada deveria ser desvio limpo")
    # D3 — fase 39: buraco (pulo), barra (deslize) e poças fora da aterrissagem.
    _start_phase(38)
    var buraco: Dictionary = _find_entity("pothole", 156.0)
    var barra: Dictionary = _find_entity("barrier", 268.0)
    if buraco.is_empty() or barra.is_empty():
        ok = false
        print("  obra da fase 39 não montada")
    else:
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(buraco)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular o buraco deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game._resolve_entity(buraco)
        if _game.hearts != 2:
            ok = false
            print("  cair no buraco deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game.slide_timer = 0.5
        _game._resolve_entity(barra)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  deslizar sob a barra deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(barra)
        if _game.hearts != 2:
            ok = false
            print("  pular na barra deveria causar dano (corações=%d)" % _game.hearts)
        var pocos_livres := true
        var level_39: Dictionary = LevelData.for_phase(38)
        for p in level_39.get("patterns", []):
            if str(p.get("kind", "")) != "pothole":
                continue
            for q in level_39.get("patterns", []):
                if str(q.get("kind", "")) != "puddle" \
                        or int(q.get("lane", -1)) != int(p.get("lane", -2)):
                    continue
                var apos: float = float(q.get("at_m", 0.0)) - float(p.get("at_m", 0.0))
                if apos > 0.0 and apos < 28.0:
                    pocos_livres = false
        if not pocos_livres:
            ok = false
            print("  poça dentro da aterrissagem obrigatória na fase 39")
    # D4 — fase 38: carrinho (FULL) e pedestre (SOFT) debaixo d'água.
    _start_phase(37)
    var cart: Dictionary = _find_entity("cart", 100.0)
    var ped: Dictionary = _find_entity("crosser", 268.0)
    if cart.is_empty() or ped.is_empty():
        ok = false
        print("  entrega da fase 38 não montada")
    else:
        _emulate_approach(cart, 34.0, 100.0, 8.1)
        var cart_x: float = (cart["node"] as Node3D).position.x
        _emulate_approach(ped, 237.5, 268.0, 8.1)
        var ped_x: float = (ped["node"] as Node3D).position.x
        print("  entrega em x=%.2f/%.2f na passagem" % [cart_x, ped_x])
        if absf(cart_x + 3.25) > 0.05 or absf(ped_x) > 0.1:
            ok = false
            print("  carrinho e pedestre deveriam bloquear E e C nas passagens")
        _set_player(0, -3.25)
        _game._resolve_entity(cart)
        if _game.hearts != 2:
            ok = false
            print("  carrinho em E deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cart)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  C deveria passar limpo pelo carrinho")
        _set_player(1, 0.0)
        _game._resolve_entity(ped)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  pedestre no centro deveria tropeçar sem dano")
        _set_player(0, -3.25)
        _game._resolve_entity(ped)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pelo pedestre")
    # D5 — clima: garoa nas fases 36–39, sol na 40, rodízio intacto.
    if _game._clima == null or _game._clima._chuva == null:
        ok = false
        print("  sistema de clima não montado")
    else:
        # _alvo_molhado interpola por frames (transição do motor); sem
        # frames no QA, o observável síncrono é estado + chuva emitindo.
        for index in [35, 36, 37, 38]:
            _start_phase(index)
            var estado: String = str(_game._clima._estado)
            var chovendo: bool = bool(_game._clima._chuva.emitting)
            var gotas: int = int(_game._clima._chuva.amount)
            print("  fase %d: %s chuva=%s(%d)" % [index + 1, estado, str(chovendo), gotas])
            if estado != "chuva" or not chovendo or gotas != 700:
                ok = false
                print("  fase %d deveria ter garoa leve (700 gotas)" % [index + 1])
        _start_phase(39)
        var sol_estado: String = str(_game._clima._estado)
        var sol_chove: bool = bool(_game._clima._chuva.emitting)
        print("  fase 40: %s chuva=%s" % [sol_estado, str(sol_chove)])
        if sol_estado != "limpo" or sol_chove:
            ok = false
            print("  fase 40 deveria ter o sol de volta, sem chuva")
        _start_phase(35)
        var perfil_36: Dictionary = _game._render_profile()
        _start_phase(39)
        var perfil_40: Dictionary = _game._render_profile()
        _start_phase(38)
        var perfil_39: Dictionary = _game._render_profile()
        _start_phase(33)
        var ciclo_34: String = str(_game._clima._estado)
        print("  luz: f36 nevoa=%.2f sol=%.2f | f40 nevoa=%.2f sol=%.2f | f39 nevoa=%.2f | f34=%s" % [
                float(perfil_36.get("fog_density", -1.0)), float(perfil_36.get("sun_energy", -1.0)),
                float(perfil_40.get("fog_density", -1.0)), float(perfil_40.get("sun_energy", -1.0)),
                float(perfil_39.get("fog_density", -1.0)), ciclo_34])
        if absf(float(perfil_36.get("fog_density", 0.0)) - 0.5) > 0.001 \
                or absf(float(perfil_36.get("sun_energy", 0.0)) - 1.1) > 0.001 \
                or absf(float(perfil_40.get("fog_density", 0.0)) - 0.5) > 0.001 \
                or absf(float(perfil_40.get("sun_energy", 0.0)) - 1.1) > 0.001:
            ok = false
            print("  fases 36 e 40 deveriam ter luz de dia (não noite urbana)")
        if absf(float(perfil_39.get("fog_density", 0.0)) - 0.66) > 0.001 \
                or ciclo_34 != "nublado":
            ok = false
            print("  rodízio global deveria seguir onde não há override")
    # D6 — árvore comum na rua molhada; orla intacta.
    _start_phase(35)
    var total_36: int = _superficies_do_kit("arvore")
    var comuns_36: int = _arvores_do_kit("arvore")
    var palmeiras_36: int = _arvores_do_kit("palmeira")
    print("  fase 36: %d árvores, %d comuns, %d palmeiras" % [total_36, comuns_36, palmeiras_36])
    if total_36 < 2 or comuns_36 < 2 or palmeiras_36 != 0:
        ok = false
        print("  fase 36 deveria ter só a árvore comum")
    _start_phase(34)
    if _arvores_do_kit("palmeira") < 2:
        ok = false
        print("  fase 35 deveria seguir com palmeiras")
    _check(ok, "L8-D. poças, piso seco, obra, entrega e clima")


# L8-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(35):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [35, 36, 37, 38, 39]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(40):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 35:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L8-E. fases 36–40 só reusam famílias apresentadas")


# L8-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [35, 36, 37, 38, 39]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L8-F. percursos autorais independem de semente")
