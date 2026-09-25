extends SceneTree
## ETAPA 16 — Teste de aceitação headless do lote 10 das 50 fases:
## fases 46–50 autorais no caminho do terminal final, sem família nova
## (PLANO_50_FASES).
## Rodar: godot --headless --path . -s res://tools/qa_etapa16_lote10.gd
## Cenários:
##   L10-A. dados das cinco fases + gates intactos + cenário do terminal
##   L10-B. validador aprova as 50 fases do bairro (base e impulso 1,22x)
##   L10-C. montagem exata: só as entidades dos dados, nada procedural
##   L10-D. comportamentos: placas, conexão, ônibus, revisão e chamada
##   L10-E. ordem de aprendizagem: lote de reuso, sem estreia
##   L10-F. determinismo: percursos autorais independem de semente
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 16 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    if _game._clima == null:
        # ETAPA 14 — o _ready só monta o clima depois de awaits longos.
        _game._setup_clima()
    _unlock_all_phases()
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    if _failures.is_empty():
        print("ETAPA16_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA16_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_all_phases() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(50):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


# L10-A. Dados das cinco fases + gates intactos + cenário do terminal.
func _scenario_a() -> void:
    var esperado := [
        [45, "bairro_46", 532.0, 19, 8.5, 72.0],
        [46, "bairro_47", 560.0, 20, 8.6, 74.0],
        [47, "bairro_48", 588.0, 21, 8.7, 76.0],
        [48, "bairro_49", 588.0, 21, 8.8, 74.0],
        [49, "bairro_50", 616.0, 22, 9.0, 75.0],
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
    for index in [45, 46, 47, 48, 49]:
        var scenery: Dictionary = LevelData.for_phase(index).get("scenery", {})
        var predios: Dictionary = scenery.get("predios", {})
        var pesos: Dictionary = predios.get("tipo_pesos", {})
        var pisos: Array = predios.get("pisos", [])
        var props: Dictionary = scenery.get("props", {})
        var multidao: Dictionary = scenery.get("multidao", {})
        var placas: Dictionary = scenery.get("placas", {})
        var tem_paleta: bool = scenery.has("paleta") \
                and str(scenery.get("paleta", {}).get("nome", "")) == "dia"
        if int(pesos.get("tijolo", -1)) != 2 or int(pesos.get("reboco", -1)) != 2 \
                or int(pesos.get("loja", -1)) != 4 or int(pesos.get("obra", -1)) != 0 \
                or pisos.size() != 2 or int(pisos[0]) != 2 or int(pisos[1]) != 4 \
                or str(props.get("arvore", {}).get("glb", "")) != "arvore" \
                or absf(float(props.get("arvore", {}).get("espacamento_m", 0.0)) - 24.0) > 0.01 \
                or absf(float(props.get("banco", {}).get("espacamento_m", 0.0)) - 18.0) > 0.01 \
                or absf(float(props.get("lixeira", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or absf(float(props.get("poste", {}).get("espacamento_m", 0.0)) - 12.0) > 0.01 \
                or str(scenery.get("clima", "")) != "limpo" \
                or int(multidao.get("quantidade", -1)) != 14 \
                or absf(float(multidao.get("x_min_m", 0.0)) - 6.5) > 0.01 \
                or absf(float(multidao.get("x_max_m", 0.0)) - 7.4) > 0.01 \
                or absf(float(placas.get("passo_m", 0.0)) - 56.0) > 0.01 \
                or absf(float(placas.get("x_m", 0.0)) - 5.8) > 0.01 \
                or absf(float(placas.get("margem_cruzamento_m", 0.0)) - 6.0) > 0.01 \
                or str(scenery.get("marco", "")) != "terminal" \
                or tem_paleta != (index == 47):
            ok = false
            print("  fase %d sem cenário do caminho do terminal" % [index + 1])
    var centro_45: Dictionary = LevelData.for_phase(44).get("scenery", {})
    if int(centro_45.get("multidao", {}).get("quantidade", -1)) != 12 \
            or not centro_45.has("outdoors") or centro_45.has("placas") \
            or centro_45.has("marco"):
        ok = false
        print("  fase 45 deveria seguir no centro, sem placas nem marco")
    _check(ok, "L10-A. fases 46–50: dados do plano, gates intactos e cenário")


# L10-B. Validador aprova as 50 fases do bairro na base e no impulso.
func _scenario_b() -> void:
    var ok := true
    for index in range(50):
        var resultado: Dictionary = PatternValidator.validate(LevelData.for_phase(index))
        if not bool(resultado.get("valid", false)) or resultado.get("route", []).is_empty():
            ok = false
            print("  fase %d reprovada: %s (fator %s)" % [index + 1,
                    str(resultado.get("reason")), str(resultado.get("speed_factor", "?"))])
    _check(ok, "L10-B. validador aprova as 50 fases do bairro (base e impulso)")


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


# L10-C. Montagem exata: nada de procedural nas fases autorais.
func _scenario_c() -> void:
    var ok := true
    for index in [45, 46, 47, 48, 49]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var esperado_total: int = level["patterns"].size() + level["coins"].size()
        if _game.entities.size() != esperado_total or _assinatura_entidades() != _assinatura_esperada(index):
            ok = false
            print("  fase %d: %d entidades (esperado %d)" % [
                    index + 1, _game.entities.size(), esperado_total])
    _check(ok, "L10-C. fases 46–50 montadas só com os dados do nível")


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
    # ETAPA 16 — epsilon dentro da janela: at_m - lead_m em ponto
    # flutuante pode sair um ULP acima do literal (128-70,1 > 57,9) e o
    # cruzamento nunca armaria (t_start fica -1 e o nó não anda).
    var d0: float = start_d + 0.01
    _game.distance = d0
    _game.elapsed = d0 / speed
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


func _slots_placas_esperados(level: Dictionary) -> Array:
    # Espelha _spawn_placas a partir dos dados (passo, desloc, margem).
    var cfg: Dictionary = level.get("scenery", {}).get("placas", {})
    var passo := float(cfg.get("passo_m", 56.0))
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


func _assinatura_multidao() -> String:
    var partes: Array = []
    for item in _game.crowd_nodes:
        var node: Node3D = item["node"]
        partes.append("%d|%d" % [int(roundf(node.position.x * 100.0)),
                int(roundf(node.position.z * 100.0))])
    partes.sort()
    return ";".join(partes)


func _assinatura_placas() -> String:
    var partes: Array = []
    for no in _decor_por_marca("placa"):
        var pos: Vector3 = (no as Node3D).position
        partes.append("%d|%d" % [int(roundf(pos.x * 100.0)), int(roundf(pos.z * 100.0))])
    partes.sort()
    return ";".join(partes)


# L10-D. Placas, conexão, ônibus, revisão, chamada e caminho do terminal.
func _scenario_d() -> void:
    var ok := true
    # D1 — fase 46: três pedestres (SOFT) em D, E e C; D livre no clímax.
    _start_phase(45)
    var ped_a: Dictionary = _find_entity("crosser", 100.0)
    var ped_b: Dictionary = _find_entity("crosser", 212.0)
    var ped_c: Dictionary = _find_entity("crosser", 296.0)
    if ped_a.is_empty() or ped_b.is_empty() or ped_c.is_empty():
        ok = false
        print("  pedestres da fase 46 não montados")
    else:
        _emulate_approach(ped_a, 46.7, 100.0, 8.5)
        var ped_a_x: float = (ped_a["node"] as Node3D).position.x
        _emulate_approach(ped_b, 158.7, 212.0, 8.5)
        var ped_b_x: float = (ped_b["node"] as Node3D).position.x
        _emulate_approach(ped_c, 264.0, 296.0, 8.5)
        var ped_c_x: float = (ped_c["node"] as Node3D).position.x
        print("  pedestres em x=%.2f/%.2f/%.2f na passagem" % [ped_a_x, ped_b_x, ped_c_x])
        if absf(ped_a_x - 3.25) > 0.05 or absf(ped_b_x + 3.25) > 0.05 or absf(ped_c_x) > 0.05:
            ok = false
            print("  pedestres deveriam bloquear D, E e C nas passagens")
        _set_player(2, 3.25)
        _game._resolve_entity(ped_a)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
        _set_player(0, -3.25)
        _game._resolve_entity(ped_a)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pelo grupo 1")
        _set_player(1, 0.0)
        _game._resolve_entity(ped_c)
        if _game.hearts != 3 or _game.invulnerability <= 0.0:
            ok = false
            print("  esbarrar no pedestre deveria tropeçar sem dano")
        _set_player(2, 3.25)
        _game._resolve_entity(ped_c)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  D deveria passar limpo pelo grupo 3")
    # D2 — fase 47: carrinhos (FULL) em E e D; clímax com barreira em E.
    _start_phase(46)
    var cart_a: Dictionary = _find_entity("cart", 128.0)
    var cart_b: Dictionary = _find_entity("cart", 296.0)
    var barreira: Dictionary = _find_entity("barrier", 380.0)
    var caixa_cli: Dictionary = _find_entity("crate", 408.0)
    if cart_a.is_empty() or cart_b.is_empty() or barreira.is_empty() or caixa_cli.is_empty():
        ok = false
        print("  conexão da fase 47 não montada")
    else:
        _emulate_approach(cart_a, 57.9, 128.0, 8.6)
        var cart_a_x: float = (cart_a["node"] as Node3D).position.x
        _emulate_approach(cart_b, 225.9, 296.0, 8.6)
        var cart_b_x: float = (cart_b["node"] as Node3D).position.x
        print("  carrinhos em x=%.2f/%.2f na passagem" % [cart_a_x, cart_b_x])
        if absf(cart_a_x + 3.25) > 0.05 or absf(cart_b_x - 3.25) > 0.05:
            ok = false
            print("  carrinhos deveriam bloquear E e D nas passagens")
        _set_player(0, -3.25)
        _game._resolve_entity(cart_a)
        if _game.hearts != 2:
            ok = false
            print("  carrinho em E deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(1, 0.0)
        _game._resolve_entity(cart_a)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  C deveria passar limpo pelo carrinho")
        if int(barreira["lane"]) != 0 or int(caixa_cli["lane"]) != 1:
            ok = false
            print("  clímax deveria ter barreira em E com caixa em C")
        _set_player(0, -3.25)
        _game.slide_timer = 0.5
        _game._resolve_entity(barreira)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  deslizar sob a barreira deveria ser desvio limpo")
        _set_player(0, -3.25)
        _game._resolve_entity(barreira)
        if _game.hearts != 2:
            ok = false
            print("  correr na barreira deveria causar dano (corações=%d)" % _game.hearts)
    # D3 — fase 48: dois ônibus (VEHICLE) com o nariz em C e zonas.
    _start_phase(47)
    var bus_a: Dictionary = _find_entity("bus_cross", 184.0)
    var bus_b: Dictionary = _find_entity("bus_cross", 352.0)
    if bus_a.is_empty() or bus_b.is_empty():
        ok = false
        print("  ônibus da fase 48 não montados")
    else:
        _emulate_approach(bus_a, 149.2, 184.0, 8.7)
        var bus_a_x: float = (bus_a["node"] as Node3D).position.x
        _emulate_approach(bus_b, 317.2, 352.0, 8.7)
        var bus_b_x: float = (bus_b["node"] as Node3D).position.x
        print("  ônibus em x=%.2f/%.2f na passagem" % [bus_a_x, bus_b_x])
        if absf(bus_a_x) > 0.05 or absf(bus_b_x) > 0.05:
            ok = false
            print("  ônibus deveriam bloquear C nas passagens")
        var rumo_a: float = (bus_a["node"] as Node3D).rotation.y
        var rumo_b: float = (bus_b["node"] as Node3D).rotation.y
        if absf(rumo_a + PI / 2.0) > 0.01 or absf(rumo_b + PI / 2.0) > 0.01:
            ok = false
            print("  ônibus deveriam cruzar para +X (nariz no rumo)")
        _set_player(1, 0.0)
        _game.jump_timer = 0.5
        _game._resolve_entity(bus_a)
        if _game.hearts != 2:
            ok = false
            print("  pular no ônibus deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(2, 3.25)
        _game._resolve_entity(bus_b)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  D deveria passar limpo pelo segundo ônibus")
        var zonas: Array = _zonas_sinalizadas()
        var em_184 := 0
        var em_352 := 0
        for z in zonas:
            var zz: float = (z as Node3D).position.z
            if absf(zz + 184.0) < 2.0:
                em_184 += 1
            if absf(zz + 352.0) < 2.0:
                em_352 += 1
        print("  zonas na fase 48: %d (%d em 184, %d em 352)" % [zonas.size(), em_184, em_352])
        if zonas.size() != 2 or em_184 != 1 or em_352 != 1:
            ok = false
            print("  fase 48 deveria ter só as zonas dos ônibus em 184 e 352")
    # D4 — fase 49: revisão de doze famílias; moto (VEHICLE) em D.
    _start_phase(48)
    var familias := {}
    for p in LevelData.for_phase(48).get("patterns", []):
        familias[str(p["kind"])] = true
    var doze := ["cone", "crosser", "bench", "cyclist", "crate", "cart",
            "scaffold", "pothole", "barrier", "van", "hydrant", "moto_cross"]
    var revisao_ok: bool = familias.size() == 12
    for kind in doze:
        revisao_ok = revisao_ok and familias.has(kind)
    print("  revisão com %d famílias" % familias.size())
    if not revisao_ok:
        ok = false
        print("  fase 49 deveria revisar as doze famílias em blocos")
    var rev_ped: Dictionary = _find_entity("crosser", 100.0)
    var rev_cic: Dictionary = _find_entity("cyclist", 156.0)
    var rev_cart: Dictionary = _find_entity("cart", 212.0)
    var rev_moto: Dictionary = _find_entity("moto_cross", 380.0)
    if rev_ped.is_empty() or rev_cic.is_empty() or rev_cart.is_empty() or rev_moto.is_empty():
        ok = false
        print("  travessias da fase 49 não montadas")
    else:
        _emulate_approach(rev_ped, 44.8, 100.0, 8.8)
        var rev_ped_x: float = (rev_ped["node"] as Node3D).position.x
        _emulate_approach(rev_cic, 132.1, 156.0, 8.8)
        var rev_cic_x: float = (rev_cic["node"] as Node3D).position.x
        _emulate_approach(rev_cart, 140.3, 212.0, 8.8)
        var rev_cart_x: float = (rev_cart["node"] as Node3D).position.x
        _emulate_approach(rev_moto, 364.1, 380.0, 8.8)
        var rev_moto_x: float = (rev_moto["node"] as Node3D).position.x
        print("  revisão em x=%.2f/%.2f/%.2f/%.2f" % [rev_ped_x, rev_cic_x, rev_cart_x, rev_moto_x])
        if absf(rev_ped_x - 3.25) > 0.05 or absf(rev_cic_x + 3.25) > 0.05 \
                or absf(rev_cart_x - 3.25) > 0.05 or absf(rev_moto_x - 3.23) > 0.05:
            ok = false
            print("  revisão deveria bloquear D, E, D e D nas passagens")
        _set_player(2, 3.25)
        _game.jump_timer = 0.5
        _game._resolve_entity(rev_moto)
        if _game.hearts != 2:
            ok = false
            print("  pular na moto deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(rev_moto)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pela moto")
    # D5 — fase 50: três atos, três respiros, embarque dourado e terminal.
    _start_phase(49)
    var resp_a: Dictionary = _find_entity("cone", 240.0)
    var resp_b: Dictionary = _find_entity("bench", 408.0)
    var resp_c: Dictionary = _find_entity("cone", 548.0)
    var fim_bus: Dictionary = _find_entity("bus_cross", 464.0)
    var fim_moto: Dictionary = _find_entity("moto_cross", 520.0)
    if resp_a.is_empty() or resp_b.is_empty() or resp_c.is_empty() \
            or fim_bus.is_empty() or fim_moto.is_empty():
        ok = false
        print("  atos da fase 50 não montados")
    else:
        if int(resp_a["lane"]) != 1 or int(resp_b["lane"]) != 1 or int(resp_c["lane"]) != 1:
            ok = false
            print("  respiros deveriam ocupar C (240, 408 e 548)")
        _emulate_approach(fim_bus, 428.0, 464.0, 9.0)
        var fim_bus_x: float = (fim_bus["node"] as Node3D).position.x
        _emulate_approach(fim_moto, 503.7, 520.0, 9.0)
        var fim_moto_x: float = (fim_moto["node"] as Node3D).position.x
        print("  ato final em x=%.2f/%.2f na passagem" % [fim_bus_x, fim_moto_x])
        if absf(fim_bus_x) > 0.05 or absf(fim_moto_x - 3.25) > 0.05:
            ok = false
            print("  ato final deveria bloquear C e D nas passagens")
        _set_player(2, 3.25)
        _game._resolve_entity(fim_moto)
        if _game.hearts != 2:
            ok = false
            print("  moto em D deveria causar dano (corações=%d)" % _game.hearts)
        _set_player(0, -3.25)
        _game._resolve_entity(fim_moto)
        if _game.hearts != 3 or _game.invulnerability > 0.0:
            ok = false
            print("  E deveria passar limpo pela moto final")
    var dourados := 0
    for at in [560.0, 568.0, 576.0]:
        var g: Dictionary = _find_entity("golden", at)
        if not g.is_empty() and int(g["lane"]) == 1 and bool(g["collectible"]):
            dourados += 1
    print("  bilhetes dourados em C: %d/3" % dourados)
    if dourados != 3:
        ok = false
        print("  embarque deveria ter três dourados em C (560, 568, 576)")
    else:
        _set_player(1, 0.0)
        _game._resolve_entity(_find_entity("golden", 560.0))
        if _game.hearts != 3:
            ok = false
            print("  coletar o dourado não deveria causar dano")
    var marcos: Array = _decor_por_marca("terminal")
    if marcos.size() != 1:
        ok = false
        print("  fase 50 deveria ter um terminal no ponto (%d)" % marcos.size())
    else:
        var mpos: Vector3 = (marcos[0] as Node3D).position
        var mrumo: float = (marcos[0] as Node3D).rotation.y
        print("  terminal em %s rumo=%.2f" % [str(mpos), mrumo])
        if absf(mpos.x + 6.0) > 0.05 or absf(mpos.z + 630.0) > 0.05 or absf(mrumo - PI) > 0.01:
            ok = false
            print("  terminal deveria receber no ponto, de frente para quem chega")
    # D6 — placas, multidão, marcos, tempo seco e tarde dourada fixa.
    var contagem := {45: 18, 46: 20, 47: 20, 48: 20, 49: 22}
    for index in [45, 46, 47, 48, 49]:
        _start_phase(index)
        var level: Dictionary = LevelData.for_phase(index)
        var conta: Array = _slots_placas_esperados(level)
        var placas: Array = _decor_por_marca("placa")
        print("  fase %d: %d placas (%d slots x 2)" % [index + 1, placas.size(), conta[0].size()])
        if placas.size() != int(contagem[index]) or placas.size() != conta[0].size() * 2:
            ok = false
            print("  fase %d deveria ter %d placas" % [index + 1, int(contagem[index])])
        for no in placas:
            var pos: Vector3 = (no as Node3D).position
            if absf(absf(pos.x) - 5.8) > 0.05 or absf(pos.y) > 0.01:
                ok = false
                print("  placa fora do alinhamento: %s" % str(pos))
            for at in conta[1]:
                if absf(-pos.z - float(at)) < 6.0:
                    ok = false
                    print("  placa sobre a travessia %s: %s" % [str(at), str(pos)])
        var marco: Array = _decor_por_marca("terminal")
        if marco.size() != 1:
            ok = false
            print("  fase %d deveria ter o terminal no ponto" % [index + 1])
    _start_phase(49)
    var sig_placas: String = _assinatura_placas()
    _start_phase(49)
    if sig_placas != _assinatura_placas() or sig_placas.is_empty():
        ok = false
        print("  placas deveriam repetir o desenho na fase")
    _start_phase(44)
    if not _decor_por_marca("placa").is_empty() or not _decor_por_marca("terminal").is_empty():
        ok = false
        print("  fase 45 não deveria ter placas nem terminal")
    _start_phase(45)
    var figuras: Array = _game.crowd_nodes
    print("  fase 46: %d figuras na multidão" % figuras.size())
    if figuras.size() != 14:
        ok = false
        print("  fase 46 deveria ter 14 figuras na multidão")
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
    _start_phase(45)
    var sig_mult: String = _assinatura_multidao()
    _start_phase(45)
    if sig_mult != _assinatura_multidao() or sig_mult.is_empty():
        ok = false
        print("  multidão deveria repetir o desenho na fase")
    for index in [45, 46, 47, 48, 49]:
        _start_phase(index)
        var estado: String = str(_game._clima._estado)
        var chovendo: bool = bool(_game._clima._chuva.emitting)
        print("  fase %d: %s chuva=%s" % [index + 1, estado, str(chovendo)])
        if estado != "limpo" or chovendo:
            ok = false
            print("  fase %d deveria ter tempo seco" % [index + 1])
    _start_phase(47)
    var sol_48: Color = _game._render_profile_world().get("sun_color", Color(0, 0, 0))
    print("  fase 48 sol=(%.2f, %.2f, %.2f)" % [sol_48.r, sol_48.g, sol_48.b])
    if absf(sol_48.r - 1.0) > 0.01 or absf(sol_48.g - 0.93) > 0.01 or absf(sol_48.b - 0.80) > 0.01:
        ok = false
        print("  fase 48 deveria fixar a paleta de dia no grande evento")
    _check(ok, "L10-D. placas, conexão, ônibus, revisão, chamada e terminal")


# L10-E. Ordem de aprendizagem: lote de reuso, sem estreia.
func _scenario_e() -> void:
    var base: Array = []
    for index in range(45):
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                base.append(str(p["kind"]))
    var ok := true
    for index in [45, 46, 47, 48, 49]:
        for p in LevelData.for_phase(index)["patterns"]:
            if not base.has(str(p["kind"])):
                ok = false
                print("  fase %d usa %s fora da ordem" % [index + 1, str(p["kind"])])
    var estreia := {}
    for index in range(50):
        for p in LevelData.for_phase(index)["patterns"]:
            var kind := str(p["kind"])
            if not estreia.has(kind):
                estreia[kind] = index
    for kind in estreia.keys():
        if int(estreia[kind]) >= 45:
            ok = false
            print("  %s estreia na fase %d (lote de reuso)" % [str(kind), int(estreia[kind]) + 1])
    _check(ok, "L10-E. fases 46–50 só reusam famílias apresentadas")


# L10-F. Determinismo: percursos autorais independem de semente.
func _scenario_f() -> void:
    var ok := true
    for index in [45, 46, 47, 48, 49]:
        _game.rng.seed = 20240917
        _start_phase(index)
        var sig1: String = _assinatura_entidades()
        _game.rng.seed = 777
        _start_phase(index)
        if sig1 != _assinatura_entidades() or sig1.is_empty():
            ok = false
            print("  fase %d variou com a semente" % [index + 1])
    _check(ok, "L10-F. percursos autorais independem de semente")
