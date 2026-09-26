extends SceneTree
## ETAPA 11 — Teste de aceitação headless do lote 5 das 50 fases:
## fases 21–25 autorais no centro histórico, sem família nova
## (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa11_lote5.gd
## Cenários:
##   L5-A. dados das cinco fases + gates intactos + cenários do centro
##   L5-B. validador aprova as 25 fases do bairro (base e impulso 1,22x)
##   L5-C. montagem exata: só as entidades dos dados, nada procedural
##   L5-D. comportamentos: pedestres, obra, igreja e vitrines
##   L5-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L5-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 11 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_26()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA11_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA11_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_26() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(25):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L5-A. Dados das cinco fases + gates intactos + cenários do centro.
func _scenario_a() -> void:
    var esperado := [
        [20, "bairro_21", 448.0, 16, 7.4, 72.0],
        [21, "bairro_22", 476.0, 17, 7.5, 74.0],
        [22, "bairro_23", 476.0, 17, 7.6, 73.0],
        [23, "bairro_24", 504.0, 18, 7.6, 76.0],
        [24, "bairro_25", 504.0, 18, 7.7, 74.0],
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
    for index in [20, 21, 22, 23]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var pesos: Dictionary = scenery.get("predios", {}).get("tipo_pesos", {})
        if int(pesos.get("loja", -1)) != 5 or int(pesos.get("reboco", -1)) != 4 \
                or int(pesos.get("tijolo", -1)) != 1 or int(pesos.get("obra", -1)) != 0 \
                or scenery.has("marco"):
            ok = false
            print("  fase %d sem rua de comércio antigo" % [index + 1])
    var largo: Dictionary = LevelData.for_phase(24).get("scenery", {})
    if int(largo.get("predios", {}).get("tipo_pesos", {}).get("loja", -1)) != 5 \
            or str(largo.get("marco", "")) != "igreja":
        ok = false
        print("  fase 25 sem largo da igreja")
    for index in [20, 21, 22, 23, 24]:
        var props: Dictionary = LevelData.for_phase(index).get("scenery", {}).get("props", {})
        if str(props.get("arvore", {}).get("glb", "")) != "ipe_amarelo" \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 10.0) > 0.01 \
                or absf(float(props.get("poste", {}).get("espacamento_m", 0.0)) - 10.0) > 0.01:
            ok = false
            print("  fase %d sem mobiliário da praça" % [index + 1])
    var scenery_20: Dictionary = LevelData.for_phase(19).get("scenery", {})
    if scenery_20.has("predios") or scenery_20.has("marco"):
        ok = false
        print("  fase 20 não deveria ter prédios nem marco")
    _check(ok, "L5-A. fases 21–25: dados do plano, gates intactos e cenários")


# L5-B. Validador aprova as 25 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(25):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L5-B. validador aprova as 25 fases do bairro (base e impulso)")


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


# L5-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [20, 21, 22, 23, 24]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L5-C. fases 21–25 montadas só com os dados do nível")


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


func _subindo_liberado(no: Node) -> bool:
    # queue_free marca só o nó direto; filho de pai liberado só sai no
    # próximo frame — subir até a raiz para saber se a peça vale.
    var n: Node = no
    while n != null:
        if n.is_queued_for_deletion():
            return true
        n = n.get_parent()
    return false


func _malhas_decor(nome_procurado: String) -> Array:
    # Peças do GLB (nome exato no pai novo) fora da fila de liberação.
    var achadas: Array = []
    for mi in _game.decor_root.find_children("*", "MeshInstance3D", true, false):
        if str(mi.name).find(nome_procurado) >= 0 \
                and is_instance_valid(mi) and not _subindo_liberado(mi):
            achadas.append(mi)
    return achadas


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


# L5-D. Pedestres, obra, marcos e fatias do centro.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 23: dois pedestres em trajetórias separadas (SOFT).
    _start_phase(22)
    var ped_a: Dictionary = _find_entity("crosser", 128.0)
    var ped_b: Dictionary = _find_entity("crosser", 240.0)
    if ped_a.is_empty() or ped_b.is_empty():
        ok = false
        print("  pedestres da fase 23 não montados")
    else:
        _emulate_approach(ped_a, 80.4, 128.0, 7.6)
        var ped_a_x: float = (ped_a["node"] as Node3D).position.x
        _emulate_approach(ped_b, 192.4, 240.0, 7.6)
        var ped_b_x: float = (ped_b["node"] as Node3D).position.x
        print("  pedestres em x=%.2f/%.2f na passagem" % [ped_a_x, ped_b_x])
        if absf(ped_a_x - 3.25) > 0.05 or absf(ped_b_x + 3.25) > 0.05:
            ok = false
            print("  pedestres deveriam bloquear D e E nas passagens")
        _set_player(2, 3.25)
        _game._resolve_entity(ped_a)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
        _set_player(1, 0.0)
        _game._resolve_entity(ped_b)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  corredor livre deveria passar limpo pelo pedestre")
    # D2 — fase 24: andaime (deslize) e vala curta (pulo).
    _start_phase(23)
    var andaime: Dictionary = _find_entity("scaffold", 72.0)
    var vala: Dictionary = _find_entity("pothole", 128.0)
    if andaime.is_empty() or vala.is_empty():
        ok = false
        print("  obra da fase 24 não montada")
    else:
        _set_player(1, 0.0)
        _game.slide_timer = 0.5
        _game._resolve_entity(andaime)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  deslizar sob o andaime deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(andaime)
        if _game.hearts != 2:
            ok = false
            print("  pular no andaime deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(2, 3.25)
        _game.jump_timer = 0.5
        _game._resolve_entity(vala)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a vala deveria ser desvio limpo")
        _set_player(2, 3.25)
        _game._resolve_entity(vala)
        if _game.hearts != 2:
            ok = false
            print("  cair na vala deveria causar dano (corações=%d)" % _game.hearts)
    # D3 — fase 25: cruzamentos pelo centro (P07/P08), E e D livres.
    _start_phase(24)
    var ped_c: Dictionary = _find_entity("crosser", 100.0)
    var carrinho: Dictionary = _find_entity("cart", 212.0)
    if ped_c.is_empty() or carrinho.is_empty():
        ok = false
        print("  cruzamentos da fase 25 não montados")
    else:
        _emulate_approach(ped_c, 71.0, 100.0, 7.7)
        var ped_c_x: float = (ped_c["node"] as Node3D).position.x
        _emulate_approach(carrinho, 174.3, 212.0, 7.7)
        var carrinho_x: float = (carrinho["node"] as Node3D).position.x
        print("  centro em x=%.2f/%.2f na passagem" % [ped_c_x, carrinho_x])
        if absf(ped_c_x) > 0.05 or absf(carrinho_x) > 0.05:
            ok = false
            print("  cruzamentos deveriam bloquear C nas passagens")
        _set_player(1, 0.0)
        _game._resolve_entity(ped_c)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  pedestre no centro deveria tropeçar sem dano")
        _set_player(0, -3.25)
        _game._resolve_entity(ped_c)
        _set_player(2, 3.25)
        _game._resolve_entity(ped_c)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E e D deveriam passar limpos pelo pedestre")
        _set_player(1, 0.0)
        _game._resolve_entity(carrinho)
        if _game.hearts != 2:
            ok = false
            print("  carrinho no centro deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(carrinho)
        _set_player(2, 3.25)
        _game._resolve_entity(carrinho)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E e D deveriam passar limpos pelo carrinho")
    # D4 — fase 25: a igreja marca o ponto, fora dos corredores.
    var igrejas_25 := _malhas_decor("Igreja")
    var perto_ponto := 0
    for mi in igrejas_25:
        var gp: Vector3 = (mi as Node3D).global_position
        if absf(gp.x + 6.0) < 2.5 and absf(gp.z + 518.0) < 4.0:
            perto_ponto += 1
    print("  peças de igreja na fase 25: %d (%d no ponto)" % [igrejas_25.size(), perto_ponto])
    if perto_ponto < 1:
        ok = false
        print("  fase 25 deveria ter a igreja ao lado do ponto")
    _start_phase(23)
    var igrejas_24 := _malhas_decor("Igreja")
    if not igrejas_24.is_empty():
        ok = false
        print("  fase 24 não deveria ter igreja")
    # D5 — rua de comércio antigo: o kit aplica os pesos do nível e as
    # vitrines com toldo aparecem; a avenida mantém os pesos padrão.
    _start_phase(20)
    var spec_21: Dictionary = _game._world_kit.spec
    var peso_loja_21: int = int(spec_21.get("predios", {}).get("tipo_pesos", {}).get("loja", -1))
    var toldos_21: int = _superficies_do_kit("toldo")
    _start_phase(19)
    var spec_20: Dictionary = _game._world_kit.spec
    var peso_loja_20: int = int(spec_20.get("predios", {}).get("tipo_pesos", {}).get("loja", -1))
    print("  loja: fase21 peso=%d toldos=%d | fase20 peso=%d" % [peso_loja_21, toldos_21, peso_loja_20])
    if peso_loja_21 != 5 or toldos_21 < 1:
        ok = false
        print("  fase 21 deveria renderizar a rua de comércio antigo")
    if peso_loja_20 != 2:
        ok = false
        print("  fase 20 deveria manter os pesos padrão da avenida")
    # D6 — ipês na praça do centro; avenida e piloto intactos.
    _start_phase(20)
    var ipes_21: int = _arvores_do_kit("ipe_amarelo")
    var palmeiras_21: int = _arvores_do_kit("palmeira")
    print("  fase 21: %d ipês, %d palmeiras" % [ipes_21, palmeiras_21])
    if ipes_21 < 2 or palmeiras_21 != 0:
        ok = false
        print("  fase 21 deveria ter ipês na praça, sem palmeiras")
    _start_phase(19)
    var palmeiras_20: int = _arvores_do_kit("palmeira")
    if palmeiras_20 < 2:
        ok = false
        print("  fase 20 deveria seguir com palmeiras")
    _check(ok, "L5-D. pedestres, obra, igreja, vitrines e ipês")


# L5-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(20):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [20, 21, 22, 23, 24]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(25):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 20:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L5-E. fases 21–25 só reusam famílias apresentadas")


# L5-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [20, 21, 22, 23, 24]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L5-F. percursos autorais independem de semente")
