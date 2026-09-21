extends SceneTree
## ETAPA 5 — Teste de aceitação headless da frente de conteúdo/arte.
## Rodar: godot --headless --path . -s res://tools/qa_etapa5_arte.gd
## Cenários:
##   V. barreira.glb: contrato de asset (origem no chão, altura ~1,9 m) e
##      drop-in ativo na fase 3 (o GLB substitui o fallback procedural).
##   W. ipe_amarelo.glb: contrato de asset e árvores do piloto usando o ipê
##      (fases sem nível seguem com a árvore comum).
##   X. corredores legíveis: na fase 3 o deck cobre os três corredores
##      (-3,25 / 0 / +3,25); na fase 1 o leiaute padrão permanece.
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 5 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_3()
    _scenario_v()
    _scenario_w()
    _scenario_x()
    if _failures.is_empty():
        print("ETAPA5_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA5_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


func _unlock_up_to_phase_3() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    save.call("record_phase", 0, 3, 10.0)
    save.call("record_phase", 1, 3, 10.0)


func _unlock_up_to_phase_6() -> void:
    var save: Node = _game.get_node("/root/GameSave")
    for i in range(2, 5):
        save.call("record_phase", i, 3, 10.0)


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"


## AABB global da instância (união das MeshInstance3D descendentes).
func _global_aabb(no: Node3D) -> AABB:
    var caixa := AABB()
    var primeira := true
    for mi in no.find_children("*", "MeshInstance3D", true, false):
        var mesh_aabb: AABB = (mi as MeshInstance3D).get_aabb()
        mesh_aabb.position += (mi as Node3D).position
        if primeira:
            caixa = mesh_aabb
            primeira = false
        else:
            caixa = caixa.merge(mesh_aabb)
    return caixa


func _nomes_descendentes(no: Node) -> String:
    var resultado := ""
    for filho in no.get_children():
        resultado += "|" + filho.name
        resultado += _nomes_descendentes(filho)
    return resultado


# V. barreira.glb: contrato de asset + drop-in ativo na fase 3.
func _scenario_v() -> void:
    var prop: Node3D = _game._optional_prop("barreira.glb")
    _check(prop != null and not prop.find_children("*", "MeshInstance3D", true, false).is_empty(),
            "V1. barreira.glb carrega com malha")
    if prop != null:
        var caixa: AABB = _global_aabb(prop)
        print("barreira.glb AABB: y %.2f..%.2f, x %.2f..%.2f" % [
                caixa.position.y, caixa.end.y, caixa.position.x, caixa.end.x])
        _check(absf(caixa.position.y) < 0.02 and caixa.end.y > 1.8 and caixa.end.y < 2.05
                and caixa.position.x < -1.0 and caixa.end.x > 1.0,
                "V2. contrato: origem no chão, ~1,9 m de altura, 2,1+ m de largura")
    _start_phase(2)
    var com_glb := 0
    var com_fallback := 0
    for e in _game.entities:
        if str(e["kind"]) != "barrier":
            continue
        var nomes: String = _nomes_descendentes(e["node"])
        if nomes.to_lower().find("barreira") >= 0:
            com_glb += 1
        if nomes.find("BarrierBar") >= 0:
            com_fallback += 1
    print("barreiras fase3: %d com GLB, %d com fallback procedural" % [com_glb, com_fallback])
    _check(com_glb == 2 and com_fallback == 0,
            "V3. fase 3 usa o barreira.glb (drop-in substitui o procedural)")


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


# W. ipe_amarelo.glb: contrato + árvores do piloto.
func _scenario_w() -> void:
    var cena: PackedScene = load("res://assets/scene/ipe_amarelo.glb")
    _check(cena != null, "W1. ipe_amarelo.glb importa como cena")
    if cena != null:
        var arvore: Node3D = cena.instantiate()
        var caixa: AABB = _global_aabb(arvore)
        print("ipe_amarelo.glb AABB: y %.2f..%.2f" % [caixa.position.y, caixa.end.y])
        _check(absf(caixa.position.y) < 0.02 and caixa.end.y > 3.8 and caixa.end.y < 5.5,
                "W2. contrato: origem no chão, árvore com 3,8–5,5 m")
        arvore.free()
    _start_phase(2)
    var ipes: int = _arvores_do_kit("ipe_amarelo")
    print("ipes no cenario da fase 3: %d" % ipes)
    _check(ipes >= 2, "W3. fase 3 (Rua do Ipê) tem ipe amarelo no cenário")
    _start_phase(0)
    var comuns: int = _arvores_do_kit("arvore")
    var ipes_fase1: int = _arvores_do_kit("ipe_amarelo")
    print("fase 1: %d arvores comuns, %d ipes" % [comuns, ipes_fase1])
    _check(comuns >= 2 and ipes_fase1 == 0,
            "W4. fases sem nível seguem com a árvore comum")


# X. Deck cobre os três corredores na fase 3 (e só lá).
func _deck_cobre(x: float) -> bool:
    var kit: Node3D = _game._world_kit
    if kit == null:
        return false
    for no in kit.find_children("CalcadaDeck", "MeshInstance3D", true, false):
        var mi := no as MeshInstance3D
        if mi.mesh is BoxMesh:
            var tamanho: Vector3 = (mi.mesh as BoxMesh).size
            var x0: float = mi.position.x - tamanho.x * 0.5
            var x1: float = mi.position.x + tamanho.x * 0.5
            if x >= x0 and x <= x1:
                return true
    return false


func _scenario_x() -> void:
    _start_phase(2)
    var cobre_e: bool = _deck_cobre(-3.25)
    var cobre_c: bool = _deck_cobre(0.0)
    var cobre_d: bool = _deck_cobre(3.25)
    print("deck fase3: E=%s C=%s D=%s" % [str(cobre_e), str(cobre_c), str(cobre_d)])
    _check(cobre_e and cobre_c and cobre_d,
            "X1. fase 3: deck cobre os três corredores de corrida")
    # ETAPA 7 — fases 1-5 viraram níveis autorais; o leiaute padrão fica nas
    # fases ainda procedurais (ex.: fase 6, índice 5).
    _unlock_up_to_phase_6()
    _start_phase(5)
    var sem_nivel_e: bool = _deck_cobre(-3.25)
    var sem_nivel_c: bool = _deck_cobre(0.0)
    print("deck fase6: E=%s C=%s (leiaute padrão)" % [str(sem_nivel_e), str(sem_nivel_c)])
    _check(not sem_nivel_e and sem_nivel_c,
            "X2. fases sem nível mantêm o leiaute padrão (rua à esquerda)")
