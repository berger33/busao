extends SceneTree
## ETAPA 15 — Teste de aceitação headless do lote 9 das 50 fases:
## fases 41–45 autorais no Centro movimentado, sem família nova
## (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa15_lote9.gd
## Cenários:
##   L9-A. dados das cinco fases + gates intactos + cenário do centro
##   L9-B. validador aprova as 45 fases do bairro (base e impulso 1,22x)
##   L9-C. montagem exata: só as entidades dos dados, nada procedural
##   L9-D. comportamentos: escritório, entregas, sinal, obra e pico
##   L9-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L9-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 15 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    if _game._clima == null:
        # ETAPA 14 — o _ready só monta o clima depois de awaits longos.
        _game._setup_clima()
    _unlock_up_to_phase_46()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA15_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA15_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_46() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(45):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L9-A. Dados das cinco fases + gates intactos + cenário do centro.
func _scenario_a() -> void:
    var esperado := [
        [40, "bairro_41", 504.0, 18, 8.2, 72.0],
        [41, "bairro_42", 532.0, 19, 8.3, 74.0],
        [42, "bairro_43", 560.0, 20, 8.4, 76.0],
        [43, "bairro_44", 560.0, 20, 8.5, 74.0],
        [44, "bairro_45", 588.0, 21, 8.6, 76.0],
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
    for index in [40, 41, 42, 43, 44]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var predios: Dictionary = scenery.get("predios", {})
        var pesos: Dictionary = predios.get("tipo_pesos", {})
        var pisos: Array = predios.get("pisos", [])
        var props: Dictionary = scenery.get("props", {})
        var multidao: Dictionary = scenery.get("multidao", {})
        var outdoors: Dictionary = scenery.get("outdoors", {})
        if int(pesos.get("tijolo", -1)) != 2 or int(pesos.get("reboco", -1)) != 2 \
                or int(pesos.get("loja", -1)) != 5 or int(pesos.get("obra", -1)) != 1 \
                or pisos.size() != 2 or int(pisos[0]) != 3 or int(pisos[1]) != 5 \
                or str(props.get("arvore", {}).get("glb", "")) != "arvore" \
                or absf(float(props.get("arvore", {}).get("espacamento_m", 0.0)) - 24.0) > 0.01 \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 18.0) > 0.01 \
                or absf(float(props.get("lixeira", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or absf(float(props.get("poste", {}).get("espacamento_m", 0.0)) - 14.0) > 0.01 \
                or str(scenery.get("clima", "")) != "limpo" \
                or int(multidao.get("quantidade", -1)) != 12 \
                or absf(float(multidao.get("x_min_m", 0.0)) - 6.5) > 0.01 \
                or absf(float(multidao.get("x_max_m", 0.0)) - 7.4) > 0.01 \
                or absf(float(outdoors.get("passo_m", 0.0)) - 140.0) > 0.01 \
                or absf(float(outdoors.get("x_m", 0.0)) - 7.0) > 0.01 \
                or absf(float(outdoors.get("margem_cruzamento_m", 0.0)) - 6.0) > 0.01 \
                or scenery.has("paleta") or scenery.has("marco"):
            ok = false
            print("  fase %d sem cenário do centro movimentado" % [index + 1])
    var sol: Dictionary = LevelData.for_phase(39).get("scenery", {})
    if sol.has("multidao") or sol.has("outdoors") or not sol.has("paleta"):
        ok = false
        print("  fase 40 deveria seguir ao sol, sem multidão nem outdoors")
    _check(ok, "L9-A. fases 41–45: dados do plano, gates intactos e cenário")


# L9-B. Validador aprova as 45 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(45):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L9-B. validador aprova as 45 fases do bairro (base e impulso)")


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


# L9-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [40, 41, 42, 43, 44]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L9-C. fases 41–45 montadas só com os dados do nível")


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


func _zonas_sinalizadas() -> Array:
    # A zona é achada pela base zebrada e a identidade vem da posição.
    var zonas: Array = []
    for base in _game.entity_root.find_children("CrossZoneBase", "MeshInstance3D", true, false):
        var zona := (base as Node).get_parent() as Node3D
        if zona != null and is_instance_valid(zona) and not _subindo_liberado(zona):
            zonas.append(zona)
    return zonas


func _slots_outdoors_esperados(level: Dictionary) -> Array:
    # Espelha _spawn_outdoors a partir dos dados (passo, desloc, margem).
    var cfg: Dictionary = level.get("scenery", {}).get("outdoors", {})
    var passo := float(cfg.get("passo_m", 140.0))
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


func _assinatura_multidao() -> String:
    var partes: Array = []
    for item in _game.crowd_nodes:
        var node: Node3D = item["node"]
        partes.append("%d|%d" % [int(roundf(node.position.x * 100.0)),
                int(roundf(node.position.z * 100.0))])
    partes.sort()
    return ";".join(partes)


# L9-D. Escritório, entregas, sinal, obra, pico, multidão e outdoors.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 41: dois grupos de pedestres (SOFT), D e E livres.
    _start_phase(40)
    var ped_a: Dictionary = _find_entity("crosser", 100.0)
    var ped_b: Dictionary = _find_entity("crosser", 240.0)
    if ped_a.is_empty() or ped_b.is_empty():
        ok = false
        print("  pedestres da fase 41 não montados")
    else:
        _emulate_approach(ped_a, 48.6, 100.0, 8.2)
        var ped_a_x: float = (ped_a["node"] as Node3D).position.x
        _emulate_approach(ped_b, 188.6, 240.0, 8.2)
        var ped_b_x: float = (ped_b["node"] as Node3D).position.x
        print("  grupos em x=%.2f/%.2f na passagem" % [ped_a_x, ped_b_x])
        if absf(ped_a_x + 3.25) > 0.05 or absf(ped_b_x - 3.25) > 0.05:
            ok = false
            print("  pedestres deveriam bloquear E e D nas passagens")
        _set_player(0, -3.25)
        _game._resolve_entity(ped_a)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
        _set_player(2, 3.25)
        _game._resolve_entity(ped_a)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  D deveria passar limpo pelo grupo 1")
        _set_player(2, 3.25)
        _game._resolve_entity(ped_b)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
        _set_player(0, -3.25)
        _game._resolve_entity(ped_b)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pelo grupo 2")
    # D2 — fase 42: carrinho (FULL), van (VEHICLE) e rota técnica com moedas.
    _start_phase(41)
    var cart: Dictionary = _find_entity("cart", 156.0)
    var van: Dictionary = _find_entity("van", 324.0)
    var caixa: Dictionary = _find_entity("crate", 100.0)
    if cart.is_empty() or van.is_empty() or caixa.is_empty():
        ok = false
        print("  entregas da fase 42 não montadas")
    else:
        _emulate_approach(cart, 88.4, 156.0, 8.3)
        var cart_x: float = (cart["node"] as Node3D).position.x
        print("  carrinho em x=%.2f na passagem" % cart_x)
        if absf(cart_x + 3.24) > 0.05:
            ok = false
            print("  carrinho deveria bloquear E na passagem")
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
        if int(van["lane"]) != 1:
            ok = false
            print("  van do clímax deveria ocupar C")
        _set_player(1, 0.0)
        _game._resolve_entity(van)
        if _game.hearts != 2:
            ok = false
            print("  van em C deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(van)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pela van")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(caixa)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  pular a caixa deveria ser desvio limpo")
        if _count_entities("coin", 1, 92.0) != 1 \
                or _count_entities("coin", 1, 100.0) != 1 \
                or _count_entities("coin", 1, 108.0) != 1:
            ok = false
            print("  rota técnica da fase 42 sem moedas sobre a caixa")
    # D3 — fase 43: moto (VEHICLE), ciclista (FULL) e ônibus com zona.
    _start_phase(42)
    var moto: Dictionary = _find_entity("moto_cross", 128.0)
    var cic: Dictionary = _find_entity("cyclist", 240.0)
    var bus: Dictionary = _find_entity("bus_cross", 352.0)
    if moto.is_empty() or cic.is_empty() or bus.is_empty():
        ok = false
        print("  sinal da fase 43 não montado")
    else:
        _emulate_approach(moto, 112.8, 128.0, 8.4)
        var moto_x: float = (moto["node"] as Node3D).position.x
        _emulate_approach(cic, 217.2, 240.0, 8.4)
        var cic_x: float = (cic["node"] as Node3D).position.x
        _emulate_approach(bus, 318.4, 352.0, 8.4)
        var bus_x: float = (bus["node"] as Node3D).position.x
        print("  sinal em x=%.2f/%.2f/%.2f" % [moto_x, cic_x, bus_x])
        if absf(moto_x + 3.24) > 0.05 or absf(cic_x - 3.24) > 0.05 or absf(bus_x) > 0.05:
            ok = false
            print("  moto, ciclista e ônibus deveriam bloquear E, D e C")
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
            print("  C deveria passar limpo pela moto")
        _set_player(2, 3.25)
        _game._resolve_entity(cic)
        if _game.hearts != 2:
            ok = false
            print("  ciclista em D deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(bus)
        if _game.hearts != 2:
            ok = false
            print("  pular no ônibus deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(2, 3.25)
        _game._resolve_entity(bus)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  D deveria passar limpo pelo ônibus")
        var zonas: Array = _zonas_sinalizadas()
        var no_ponto := 0
        for z in zonas:
            if absf((z as Node3D).position.z + 352.0) < 2.0:
                no_ponto += 1
        print("  zonas na fase 43: %d (%d no ponto do ônibus)" % [zonas.size(), no_ponto])
        if zonas.size() != 1 or no_ponto != 1:
            ok = false
            print("  fase 43 deveria ter só a zona do ônibus em 352")
    # D4 — fase 44: andaime (deslize), buraco (pulo) e hidrante (desvio).
    _start_phase(43)
    var andaime: Dictionary = _find_entity("scaffold", 296.0)
    var buraco: Dictionary = _find_entity("pothole", 212.0)
    var hidrante: Dictionary = _find_entity("hydrant", 128.0)
    if andaime.is_empty() or buraco.is_empty() or hidrante.is_empty():
        ok = false
        print("  reforma da fase 44 não montada")
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
        _game._resolve_entity(hidrante)
        if _game.hearts != 2:
            ok = false
            print("  correr no hidrante deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(hidrante)
        if _game.hearts != 2:
            ok = false
            print("  pular no hidrante deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(hidrante)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pelo hidrante")
    # D5 — multidão anda nas calçadas; outdoors alinhados; rua de lojas.
    if not _contrato_glb("res://assets/scene/outdoor.glb", "outdoor.glb"):
        ok = false
    _start_phase(40)
    var figuras: Array = _game.crowd_nodes
    print("  fase 41: %d figuras na multidão" % figuras.size())
    if figuras.size() != 12:
        ok = false
        print("  fase 41 deveria ter 12 figuras na multidão")
    for item in figuras:
        var fpos: Vector3 = (item["node"] as Node3D).position
        if absf(fpos.x) < 6.3 or absf(fpos.x) > 7.6 or fpos.y < -0.01 or fpos.y > 0.06:
            ok = false
            print("  figura fora da calçada: %s" % str(fpos))
    var antes: Array = []
    for item in figuras:
        antes.append((item["node"] as Node3D).position.z)
    _game._update_multidao(1.0)
    var andou := true
    for i in figuras.size():
        if absf((figuras[i]["node"] as Node3D).position.z - float(antes[i])) < 0.5:
            andou = false
    if not andou:
        ok = false
        print("  multidão deveria andar (Z muda no update)")
    if not figuras.is_empty():
        var prova: Node3D = figuras[0]["node"]
        prova.position.z = 30.0
        _game._update_multidao(0.01)
        var volta_cima: float = prova.position.z
        prova.position.z = -30.0
        _game._update_multidao(0.01)
        if absf(volta_cima + 26.0) > 0.01 or absf(prova.position.z - 24.0) > 0.01:
            ok = false
            print("  multidão deveria reciclar na janela da câmera")
    _start_phase(40)
    var sig_mult: String = _assinatura_multidao()
    _start_phase(40)
    if sig_mult != _assinatura_multidao() or sig_mult.is_empty():
        ok = false
        print("  multidão deveria repetir o desenho na fase")
    _start_phase(39)
    if not _game.crowd_nodes.is_empty():
        ok = false
        print("  fase 40 não deveria ter multidão")
    var contagem := {40: 8, 41: 8, 42: 6, 43: 8, 44: 8}
    for index in [40, 41, 42, 43, 44]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var conta: Array = _slots_outdoors_esperados(level)
        var outdoors: Array = _decor_por_marca("outdoor")
        print("  fase %d: %d outdoors (%d slots x 2)" % [index + 1, outdoors.size(), conta[0].size()])
        if outdoors.size() != int(contagem[index]) or outdoors.size() != conta[0].size() * 2:
            ok = false
            print("  fase %d deveria ter %d outdoors" % [index + 1, int(contagem[index])])
        for no in outdoors:
            var pos: Vector3 = (no as Node3D).position
            if absf(absf(pos.x) - 7.0) > 0.05:
                ok = false
                print("  outdoor fora do alinhamento: %s" % str(pos))
            for at in conta[1]:
                if absf(-pos.z - float(at)) < 6.0:
                    ok = false
                    print("  outdoor sobre a travessia %s: %s" % [str(at), str(pos)])
    _start_phase(39)
    if not _decor_por_marca("outdoor").is_empty():
        ok = false
        print("  fase 40 não deveria ter outdoors")
    _start_phase(40)
    var spec_41: Dictionary = _game._world_kit.spec
    var loja_41: int = int(spec_41.get("predios", {}).get("tipo_pesos", {}).get("loja", -1))
    var toldos_41: int = _superficies_do_kit("toldo")
    print("  centro: loja=%d toldos=%d" % [loja_41, toldos_41])
    if loja_41 != 5 or toldos_41 < 1:
        ok = false
        print("  fase 41 deveria renderizar a rua de lojas")
    # D6 — tempo seco no centro; rodízio intacto onde não há override.
    for index in [40, 41, 42, 43, 44]:
        _start_phase(index)
        var estado: String = str(_game._clima._estado)
        var chovendo: bool = bool(_game._clima._chuva.emitting)
        print("  fase %d: %s chuva=%s" % [index + 1, estado, str(chovendo)])
        if estado != "limpo" or chovendo:
            ok = false
            print("  fase %d deveria ter tempo seco" % [index + 1])
    _start_phase(34)
    if str(_game._clima._estado) != "chuva" or not bool(_game._clima._chuva.emitting):
        ok = false
        print("  fase 35 deveria seguir no rodízio global (chuva)")
    _check(ok, "L9-D. escritório, entregas, sinal, obra, pico e centro")


# L9-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(40):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [40, 41, 42, 43, 44]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(45):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 40:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L9-E. fases 41–45 só reusam famílias apresentadas")


# L9-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [40, 41, 42, 43, 44]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L9-F. percursos autorais independem de semente")
