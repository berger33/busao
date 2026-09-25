extends SceneTree
## ETAPA 13 — Teste de aceitação headless do lote 7 das 50 fases:
## fases 31–35 autorais no Parque e orla, sem família nova (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa13_lote7.gd
## Cenários:
##   L7-A. dados das cinco fases + gates intactos + cenário do parque
##   L7-B. validador aprova as 35 fases do bairro (base e impulso 1,22x)
##   L7-C. montagem exata: só as entidades dos dados, nada procedural
##   L7-D. comportamentos: caramelo, ciclistas, calçadão, orla e palmeiras
##   L7-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L7-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 13 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_36()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA13_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA13_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_36() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(35):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L7-A. Dados das cinco fases + gates intactos + cenário do parque.
func _scenario_a() -> void:
    var esperado := [
        [30, "bairro_31", 476.0, 17, 7.8, 73.0],
        [31, "bairro_32", 504.0, 18, 8.0, 73.0],
        [32, "bairro_33", 504.0, 18, 8.0, 73.0],
        [33, "bairro_34", 532.0, 19, 8.1, 75.0],
        [34, "bairro_35", 560.0, 20, 8.2, 77.0],
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
    for index in [30, 31, 32, 33, 34]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var predios: Dictionary = scenery.get("predios", {})
        var pesos: Dictionary = predios.get("tipo_pesos", {})
        var pisos: Array = predios.get("pisos", [])
        var quiosques: Dictionary = scenery.get("quiosques", {})
        var paleta: Dictionary = scenery.get("paleta", {})
        var props: Dictionary = scenery.get("props", {})
        if int(pesos.get("tijolo", -1)) != 2 or int(pesos.get("reboco", -1)) != 4 \
                or int(pesos.get("loja", -1)) != 2 or int(pesos.get("obra", -1)) != 0 \
                or pisos.size() != 2 or int(pisos[0]) != 1 or int(pisos[1]) != 2 \
                or absf(float(quiosques.get("passo_m", 0.0)) - 112.0) > 0.01 \
                or absf(float(quiosques.get("x_m", 0.0)) - 6.4) > 0.01 \
                or absf(float(quiosques.get("margem_cruzamento_m", 0.0)) - 6.0) > 0.01 \
                or str(paleta.get("nome", "")) != "orla" \
                or absf(float(paleta.get("nevoa_densidade", 0.0)) - 0.35) > 0.001 \
                or absf(float(paleta.get("exposicao", 0.0)) - 0.55) > 0.001 \
                or str(props.get("arvore", {}).get("glb", "")) != "palmeira" \
                or absf(float(props.get("arvore", {}).get("espacamento_m", 0.0)) - 8.0) > 0.01 \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or absf(float(props.get("lixeira", {}).get("espacamento_m", 0.0)) - 18.0) > 0.01:
            ok = false
            print("  fase %d sem cenário do parque" % [index + 1])
    for index in [30, 31, 32, 33]:
        if LevelData.for_phase(index).get("scenery", {}).has("marco"):
            ok = false
            print("  fase %d não deveria ter marco" % [index + 1])
    if str(LevelData.for_phase(34).get("scenery", {}).get("marco", "")) != "guarita":
        ok = false
        print("  fase 35 sem marco da guarita")
    var feira: Dictionary = LevelData.for_phase(29).get("scenery", {})
    if feira.has("quiosques") or feira.has("paleta") or feira.has("marco") \
            or not feira.has("feira"):
        ok = false
        print("  fase 30 deveria seguir na feira, sem quiosques nem paleta")
    _check(ok, "L7-A. fases 31–35: dados do plano, gates intactos e cenário")


# L7-B. Validador aprova as 35 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(35):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L7-B. validador aprova as 35 fases do bairro (base e impulso)")


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


# L7-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [30, 31, 32, 33, 34]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L7-C. fases 31–35 montadas só com os dados do nível")


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
            # ETAPA 13 — comparação sem maiúsculas: os repetidos viram
            # @Node3D@N e os filhos do GLB mantêm maiúsculas (Palmeira).
            if (no.name + _nomes_descendentes(no)).to_lower().find(nome_procurado) >= 0:
                achadas += 1
    return achadas


func _subindo_liberado(no: Node) -> bool:
    # queue_free marca só o nó direto; filho de pai liberado só sai no
    # próximo frame — subir até a raiz para saber se a peça vale.
    var n: Node = no
    while n != null:
        if n.is_queued_for_deletion():
            return true
        n = n.get_parent()
    return false


func _superficies_do_kit(superficie: String) -> int:
    var achadas := 0
    var kit: Node3D = _game._world_kit
    if kit == null:
        return 0
    for no in kit.find_children("*", "Node3D", true, false):
        if no.has_meta("superficie") and str(no.get_meta("superficie")) == superficie \
                and not _subindo_liberado(no):
            achadas += 1
    return achadas


func _decor_por_marca(marca: String) -> Array:
    # Uma marca decor_kind por peça (GLB ou reserva), fora da fila de
    # liberação — nome não serve (@Node3D@N nos repetidos).
    var achadas: Array = []
    for no in _game.decor_root.find_children("*", "Node3D", true, false):
        if no.has_meta("decor_kind") and str(no.get_meta("decor_kind")) == marca \
                and is_instance_valid(no) and not _subindo_liberado(no):
            achadas.append(no)
    return achadas


func _slots_quiosques_esperados(level: Dictionary) -> Array:
    # Espelha _spawn_quiosques a partir dos dados (passo, desloc, margem).
    var cfg: Dictionary = level.get("scenery", {}).get("quiosques", {})
    var passo := float(cfg.get("passo_m", 112.0))
    var desloc := float(cfg.get("desloc_m", passo * 0.5))
    var margem := float(cfg.get("margem_cruzamento_m", 6.0))
    var total := float(level.get("distance_m", 0.0))
    var cruzamentos: Array = []
    for p in level.get("patterns", []):
        if p.has("cross_mps"):
            cruzamentos.append(float(p.get("at_m", 0.0)))
    var slots: Array = []
    var z := desloc
    while z < total - 10.0:
        var livre := true
        for at in cruzamentos:
            if absf(z - at) < margem:
                livre = false
        if livre:
            slots.append(z)
        z += passo
    return [slots, cruzamentos]


func _contrato_glb(caminho: String, etiqueta: String) -> bool:
    var cena: PackedScene = load(caminho)
    if cena == null:
        print("  %s não importa como cena" % etiqueta)
        return false
    var modelo: Node3D = cena.instantiate()
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
    print("  %s AABB: y %.2f..%.2f" % [etiqueta, caixa.position.y, caixa.end.y])
    modelo.free()
    if not tem_malha or absf(caixa.position.y) > 0.5 or caixa.end.y < 1.5:
        print("  %s fora do contrato (origem no chão, peça > 1,5 m)" % etiqueta)
        return false
    return true


# L7-D. Caramelo, ciclistas, calçadão, orla e palmeiras.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 32: cachorro e pedestre em eventos separados (SOFT).
    _start_phase(31)
    var dog: Dictionary = _find_entity("dog_cross", 100.0)
    var ped: Dictionary = _find_entity("crosser", 156.0)
    if dog.is_empty() or ped.is_empty():
        ok = false
        print("  passeio da fase 32 não montado")
    else:
        _emulate_approach(dog, 73.9, 100.0, 8.0)
        var dog_x: float = (dog["node"] as Node3D).position.x
        _emulate_approach(ped, 105.8, 156.0, 8.0)
        var ped_x: float = (ped["node"] as Node3D).position.x
        print("  passeio em x=%.2f/%.2f na passagem" % [dog_x, ped_x])
        if absf(dog_x + 3.26) > 0.05 or absf(ped_x - 3.26) > 0.05 \
                or absf(float(dog.get("mobility", -1.0))) > 0.001:
            ok = false
            print("  cachorro e pedestre deveriam bloquear E e D, sem mobilidade")
        _set_player(0, -3.25)
        _game._resolve_entity(dog)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no cachorro deveria tropeçar sem dano")
        _set_player(1, 0.0)
        _game._resolve_entity(dog)
        _set_player(1, 0.0)
        _game._resolve_entity(ped)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  C deveria passar limpo pelo passeio")
        _set_player(2, 3.25)
        _game._resolve_entity(ped)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
    # D2 — fase 33: dois ciclistas em momentos diferentes (FULL).
    _start_phase(32)
    var cic_a: Dictionary = _find_entity("cyclist", 128.0)
    var cic_b: Dictionary = _find_entity("cyclist", 240.0)
    if cic_a.is_empty() or cic_b.is_empty():
        ok = false
        print("  ciclistas da fase 33 não montados")
    else:
        _emulate_approach(cic_a, 106.3, 128.0, 8.0)
        var cic_a_x: float = (cic_a["node"] as Node3D).position.x
        _emulate_approach(cic_b, 218.3, 240.0, 8.0)
        var cic_b_x: float = (cic_b["node"] as Node3D).position.x
        print("  ciclistas em x=%.2f/%.2f na passagem" % [cic_a_x, cic_b_x])
        if absf(cic_a_x + 3.24) > 0.05 or absf(cic_b_x - 3.24) > 0.05:
            ok = false
            print("  ciclistas deveriam bloquear E e D nas passagens")
        _set_player(0, -3.25)
        _game._resolve_entity(cic_a)
        if _game.hearts != 2:
            ok = false
            print("  ciclista em E deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cic_a)
        _set_player(1, 0.0)
        _game._resolve_entity(cic_b)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  C deveria passar limpo pelos ciclistas")
        _set_player(2, 3.25)
        _game._resolve_entity(cic_b)
        if _game.hearts != 2:
            ok = false
            print("  ciclista em D deveria causar dano (corações=%d)" % _game.hearts)
    # D3 — fase 34: vala (pulo) e barra (deslize) no calçadão.
    _start_phase(33)
    var vala: Dictionary = _find_entity("pothole", 156.0)
    var barra: Dictionary = _find_entity("barrier", 240.0)
    if vala.is_empty() or barra.is_empty():
        ok = false
        print("  manutenção da fase 34 não montada")
    else:
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(vala)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a vala deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game._resolve_entity(vala)
        if _game.hearts != 2:
            ok = false
            print("  cair na vala deveria causar dano (corações=%d)" % _game.hearts)
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
    # D4 — quiosques: contrato dos assets + fileiras fora das travessias.
    if not _contrato_glb("res://assets/scene/quiosque.glb", "quiosque.glb"):
        ok = false
    if not _contrato_glb("res://assets/scene/guarita.glb", "guarita.glb"):
        ok = false
    var contagem := {30: 8, 31: 8, 32: 8, 33: 10, 34: 10}
    for index in [30, 31, 32, 33, 34]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var conta: Array = _slots_quiosques_esperados(level)
        var quiosques: Array = _decor_por_marca("quiosque")
        print("  fase %d: %d quiosques (%d slots x 2)" % [index + 1, quiosques.size(), conta[0].size()])
        if quiosques.size() != int(contagem[index]) or quiosques.size() != conta[0].size() * 2:
            ok = false
            print("  fase %d deveria ter %d quiosques" % [index + 1, int(contagem[index])])
        for no in quiosques:
            var pos: Vector3 = (no as Node3D).position
            if absf(absf(pos.x) - 6.4) > 0.05 or absf(pos.x) < 4.6:
                ok = false
                print("  quiosque fora do alinhamento: %s" % str(pos))
            for at in conta[1]:
                if absf(-pos.z - float(at)) < 6.0:
                    ok = false
                    print("  quiosque sobre a travessia %s: %s" % [str(at), str(pos)])
    _start_phase(29)
    if not _decor_por_marca("quiosque").is_empty():
        ok = false
        print("  fase 30 não deveria ter quiosques")
    # D5 — fase 35: a guarita marca o ponto; paleta orla aplicada no jogo.
    _start_phase(34)
    var guaritas_35: Array = _decor_por_marca("guarita")
    var perfil_orla: Dictionary = _game._render_profile()
    print("  fase 35: %d guarita(s), nevoa=%.2f exposicao=%.2f" % [guaritas_35.size(),
            float(perfil_orla.get("fog_density", -1.0)), float(perfil_orla.get("exposure", -1.0))])
    if guaritas_35.size() != 1:
        ok = false
        print("  fase 35 deveria ter a guarita ao lado do ponto")
    else:
        var gpos: Vector3 = (guaritas_35[0] as Node3D).position
        if absf(gpos.x + 6.0) > 0.5 or absf(gpos.z + 574.0) > 1.0:
            ok = false
            print("  guarita fora do ponto: %s" % str(gpos))
    if absf(float(perfil_orla.get("fog_density", 0.0)) - 0.35) > 0.001 \
            or absf(float(perfil_orla.get("exposure", 0.0)) - 0.55) > 0.001 \
            or absf(float(perfil_orla.get("ambient_energy", 0.0)) - 0.66) > 0.001:
        ok = false
        print("  fase 35 deveria aplicar a paleta orla (luz aberta)")
    _start_phase(33)
    if not _decor_por_marca("guarita").is_empty():
        ok = false
        print("  fase 34 não deveria ter guarita")
    _start_phase(29)
    var perfil_30: Dictionary = _game._render_profile()
    if absf(float(perfil_30.get("fog_density", 0.0)) - 0.58) > 0.001 \
            or absf(float(perfil_30.get("exposure", 0.0)) - 0.48) > 0.001:
        ok = false
        print("  fase 30 deveria manter o rodízio global (tarde_dourada)")
    # D6 — palmeiras na orla; feira e avenida intactas.
    _start_phase(30)
    var total_31: int = _superficies_do_kit("arvore")
    var palmeiras_31: int = _arvores_do_kit("palmeira")
    var ipes_31: int = _arvores_do_kit("ipe_amarelo")
    print("  fase 31: %d árvores, %d palmeiras, %d ipês" % [total_31, palmeiras_31, ipes_31])
    if total_31 < 2 or palmeiras_31 < 2 or ipes_31 != 0:
        ok = false
        print("  fase 31 deveria ter palmeiras na alameda, sem ipês")
    _start_phase(29)
    var comuns_30: int = _arvores_do_kit("arvore")
    if comuns_30 < 2 or _arvores_do_kit("palmeira") != 0:
        ok = false
        print("  fase 30 deveria seguir com a árvore comum")
    _check(ok, "L7-D. caramelo, ciclistas, calçadão, orla e palmeiras")


# L7-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(30):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [30, 31, 32, 33, 34]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(35):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 30:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L7-E. fases 31–35 só reusam famílias apresentadas")


# L7-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [30, 31, 32, 33, 34]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L7-F. percursos autorais independem de semente")
