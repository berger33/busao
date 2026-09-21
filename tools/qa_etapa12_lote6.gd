extends SceneTree
## ETAPA 12 — Teste de aceitação headless do lote 6 das 50 fases:
## fases 26–30 autorais no Mercado, sem família nova (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa12_lote6.gd
## Cenários:
##   L6-A. dados das cinco fases + gates intactos + cenário da feira
##   L6-B. validador aprova as 30 fases do bairro (base e impulso 1,22x)
##   L6-C. montagem exata: só as entidades dos dados, nada procedural
##   L6-D. comportamentos: entregas, esquina, toldos, feira e árvores
##   L6-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L6-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 12 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_31()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA12_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA12_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_31() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(30):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L6-A. Dados das cinco fases + gates intactos + cenário da feira.
func _scenario_a() -> void:
    var esperado := [
        [25, "bairro_26", 476.0, 17, 7.6, 74.0],
        [26, "bairro_27", 504.0, 18, 7.7, 76.0],
        [27, "bairro_28", 504.0, 18, 7.8, 75.0],
        [28, "bairro_29", 532.0, 19, 7.8, 78.0],
        [29, "bairro_30", 532.0, 19, 8.0, 75.0],
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
    for index in [25, 26, 27, 28, 29]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var pesos: Dictionary = scenery.get("predios", {}).get("tipo_pesos", {})
        var feira: Dictionary = scenery.get("feira", {})
        var props: Dictionary = scenery.get("props", {})
        if int(pesos.get("loja", -1)) != 3 or int(pesos.get("reboco", -1)) != 3 \
                or int(pesos.get("tijolo", -1)) != 3 or int(pesos.get("obra", -1)) != 1 \
                or absf(float(feira.get("passo_m", 0.0)) - 56.0) > 0.01 \
                or absf(float(feira.get("x_m", 0.0)) - 6.4) > 0.01 \
                or absf(float(feira.get("margem_cruzamento_m", 0.0)) - 6.0) > 0.01 \
                or str(props.get("arvore", {}).get("glb", "")) != "arvore" \
                or absf(float(props.get("arvore", {}).get("espacamento_m", 0.0)) - 16.0) > 0.01 \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 18.0) > 0.01 \
                or absf(float(props.get("lixeira", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or scenery.has("marco"):
            ok = false
            print("  fase %d sem cenário da feira" % [index + 1])
    var largo: Dictionary = LevelData.for_phase(24).get("scenery", {})
    if largo.has("feira") or str(largo.get("marco", "")) != "igreja" \
            or int(largo.get("predios", {}).get("tipo_pesos", {}).get("loja", -1)) != 5:
        ok = false
        print("  fase 25 deveria seguir no largo da igreja, sem feira")
    _check(ok, "L6-A. fases 26–30: dados do plano, gates intactos e cenário")


# L6-B. Validador aprova as 30 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(30):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L6-B. validador aprova as 30 fases do bairro (base e impulso)")


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


# L6-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [25, 26, 27, 28, 29]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L6-C. fases 26–30 montadas só com os dados do nível")


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


func _barracas_da_feira() -> Array:
    # Uma marca decor_kind=barraca por barraca (GLB ou reserva), fora da
    # fila de liberação — nome não serve (@Node3D@N nos repetidos).
    var achadas: Array = []
    for no in _game.decor_root.find_children("*", "Node3D", true, false):
        if no.has_meta("decor_kind") and str(no.get_meta("decor_kind")) == "barraca" \
                and is_instance_valid(no) and not _subindo_liberado(no):
            achadas.append(no)
    return achadas


func _slots_feira_esperados(level: Dictionary) -> Array:
    # Espelha _spawn_feira a partir dos dados (passo, desloc, margem).
    var feira: Dictionary = level.get("scenery", {}).get("feira", {})
    var passo := float(feira.get("passo_m", 56.0))
    var desloc := float(feira.get("desloc_m", passo * 0.5))
    var margem := float(feira.get("margem_cruzamento_m", 6.0))
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


# L6-D. Entregas, esquina, toldos, feira e árvores.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 27: dois carrinhos a 112 m, sentidos alternados.
    _start_phase(26)
    var cart_a: Dictionary = _find_entity("cart", 140.0)
    var cart_b: Dictionary = _find_entity("cart", 252.0)
    if cart_a.is_empty() or cart_b.is_empty():
        ok = false
        print("  carrinhos da fase 27 não montados")
    else:
        _emulate_approach(cart_a, 79.6, 140.0, 7.7)
        var cart_a_x: float = (cart_a["node"] as Node3D).position.x
        _emulate_approach(cart_b, 191.6, 252.0, 7.7)
        var cart_b_x: float = (cart_b["node"] as Node3D).position.x
        print("  carrinhos em x=%.2f/%.2f na passagem" % [cart_a_x, cart_b_x])
        if absf(cart_a_x + 2.94) > 0.05 or absf(cart_b_x - 2.94) > 0.05:
            ok = false
            print("  carrinhos deveriam bloquear E e D nas passagens")
        _set_player(0, -3.25)
        _game._resolve_entity(cart_a)
        if _game.hearts != 2:
            ok = false
            print("  carrinho em E deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cart_a)
        _set_player(1, 0.0)
        _game._resolve_entity(cart_b)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  C deveria passar limpo pelos carrinhos")
        _set_player(2, 3.25)
        _game._resolve_entity(cart_b)
        if _game.hearts != 2:
            ok = false
            print("  carrinho em D deveria causar dano (corações=%d)" % _game.hearts)
    # D2 — fase 29: a esquina (van + cruzante) e trajetórias separadas.
    _start_phase(28)
    var van_esq: Dictionary = _find_entity("van", 212.0)
    var ped_meio: Dictionary = _find_entity("crosser", 212.0)
    var ped_lado: Dictionary = _find_entity("crosser", 156.0)
    var cart_esq: Dictionary = _find_entity("cart", 100.0)
    if van_esq.is_empty() or ped_meio.is_empty() or ped_lado.is_empty() or cart_esq.is_empty():
        ok = false
        print("  esquina da fase 29 não montada")
    else:
        if int(van_esq["lane"]) != 2:
            ok = false
            print("  van da esquina deveria ocupar D")
        _emulate_approach(ped_meio, 183.0, 212.0, 7.8)
        var ped_meio_x: float = (ped_meio["node"] as Node3D).position.x
        _emulate_approach(ped_lado, 107.1, 156.0, 7.8)
        var ped_lado_x: float = (ped_lado["node"] as Node3D).position.x
        _emulate_approach(cart_esq, 37.7, 100.0, 7.8)
        var cart_esq_x: float = (cart_esq["node"] as Node3D).position.x
        print("  esquina em x=%.2f/%.2f/%.2f" % [ped_meio_x, ped_lado_x, cart_esq_x])
        if absf(ped_meio_x) > 0.1 or absf(ped_lado_x - 3.25) > 0.05 \
                or absf(cart_esq_x + 3.09) > 0.05:
            ok = false
            print("  cruzantes deveriam bloquear C, D e E nas passagens")
        _set_player(1, 0.0)
        _game._resolve_entity(ped_meio)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  pedestre no centro deveria tropeçar sem dano")
        _set_player(0, -3.25)
        _game._resolve_entity(ped_meio)
        _set_player(2, 3.25)
        _game._resolve_entity(ped_meio)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E e D deveriam passar limpos pelo pedestre")
        _set_player(2, 3.25)
        _game._resolve_entity(van_esq)
        if _game.hearts != 2:
            ok = false
            print("  van em D deveria causar dano (corações=%d)" % _game.hearts)
    # D3 — fase 28: toldo (deslize) e caixa (pulo).
    _start_phase(27)
    var toldo: Dictionary = _find_entity("barrier", 128.0)
    var caixa: Dictionary = _find_entity("crate", 184.0)
    if toldo.is_empty() or caixa.is_empty():
        ok = false
        print("  toldos da fase 28 não montados")
    else:
        _set_player(1, 0.0)
        _game.slide_timer = 0.5
        _game._resolve_entity(toldo)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  deslizar sob o toldo deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(toldo)
        if _game.hearts != 2:
            ok = false
            print("  pular no toldo deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(caixa)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a caixa deveria ser desvio limpo")
        _set_player(1, 0.0)
        _game._resolve_entity(caixa)
        if _game.hearts != 2:
            ok = false
            print("  bater na caixa deveria causar dano (corações=%d)" % _game.hearts)
    # D4 — feira: barracas dos dois lados, fora das pistas e das travessias.
    var contagem := {25: 16, 26: 14, 27: 18, 28: 18, 29: 18}
    for index in [25, 26, 27, 28, 29]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var conta: Array = _slots_feira_esperados(level)
        var barracas: Array = _barracas_da_feira()
        print("  fase %d: %d barracas (%d slots x 2)" % [index + 1, barracas.size(), conta[0].size()])
        if barracas.size() != int(contagem[index]) or barracas.size() != conta[0].size() * 2:
            ok = false
            print("  fase %d deveria ter %d barracas" % [index + 1, int(contagem[index])])
        for no in barracas:
            var pos: Vector3 = (no as Node3D).position
            if absf(absf(pos.x) - 6.4) > 0.05 or absf(pos.x) < 4.6:
                ok = false
                print("  barraca fora do alinhamento: %s" % str(pos))
            for at in conta[1]:
                if absf(-pos.z - float(at)) < 6.0:
                    ok = false
                    print("  barraca sobre a travessia %s: %s" % [str(at), str(pos)])
    _start_phase(24)
    if not _barracas_da_feira().is_empty():
        ok = false
        print("  fase 25 não deveria ter barracas")
    # D5 — o kit aplica o cenário da feira; o largo segue intacto.
    _start_phase(25)
    var spec_26: Dictionary = _game._world_kit.spec
    var peso_loja_26: int = int(spec_26.get("predios", {}).get("tipo_pesos", {}).get("loja", -1))
    var peso_obra_26: int = int(spec_26.get("predios", {}).get("tipo_pesos", {}).get("obra", -1))
    print("  feira: loja=%d obra=%d | largo: loja=5" % [peso_loja_26, peso_obra_26])
    if peso_loja_26 != 3 or peso_obra_26 != 1:
        ok = false
        print("  fase 26 deveria renderizar galpões e lojas no fundo")
    _start_phase(24)
    var spec_25: Dictionary = _game._world_kit.spec
    if spec_25.has("feira") \
            or int(spec_25.get("predios", {}).get("tipo_pesos", {}).get("loja", -1)) != 5:
        ok = false
        print("  fase 25 deveria manter o largo da igreja")
    # D6 — árvore comum de volta na feira; largo e avenida intactos.
    _start_phase(25)
    var total_26: int = _superficies_do_kit("arvore")
    var ipes_26: int = _arvores_do_kit("ipe_amarelo")
    var palmeiras_26: int = _arvores_do_kit("palmeira")
    print("  fase 26: %d árvores, %d ipês, %d palmeiras" % [total_26, ipes_26, palmeiras_26])
    if total_26 < 2 or ipes_26 != 0 or palmeiras_26 != 0:
        ok = false
        print("  fase 26 deveria ter só a árvore comum")
    _start_phase(24)
    if _arvores_do_kit("ipe_amarelo") < 2:
        ok = false
        print("  fase 25 deveria seguir com ipês")
    _check(ok, "L6-D. entregas, esquina, toldos, feira e árvores")


# L6-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(25):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [25, 26, 27, 28, 29]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(30):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 25:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L6-E. fases 26–30 só reusam famílias apresentadas")


# L6-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [25, 26, 27, 28, 29]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L6-F. percursos autorais independem de semente")
