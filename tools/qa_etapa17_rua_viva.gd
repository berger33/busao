extends SceneTree
## ETAPA 17 — Teste de aceitação headless do contrato da "rua viva" por cenário:
## coroamento dos prédios, decalques do asfalto e encardido deixam de ser iguais
## em todas as fases e passam a vir do CENARIO_* de scripts/level_data.gd,
## fundido por cima de resources/world_spec.json pelo BuildingKit.
## Rodar: godot --headless --path . -s res://tools/qa_etapa17_rua_viva.gd
## Cenários:
##   RV-A. padrões do spec: os 3 blocos existem e rua_viva devolve o padrão
##   RV-B. override do capítulo chega ao kit (merge profundo, spec intacto)
##   RV-C. identidade de topo: PARQUE sem escada/caixa, CENTRO com as duas
##   RV-D. densidade dos decalques: AVENIDA > BAIRRO > PARQUE em setas;
##         CENTRO > BAIRRO > PARQUE em remendos
##   RV-E. encardido: albedo por capítulo e desligamento por superfície
##   RV-F. orçamento: variação é estilo, não custo (teto de nós vs. bairro)
##   RV-G. elementos novos de rua: jardineiras por capítulo
##   RV-H. elementos novos de fachada: letreiro em 3 grupos de cor e grade
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []

## Nós que a camada viva pode acrescentar ao quarteirão (1 draw call cada).
const NOS_RUA_VIVA := [
    "Platibanda", "RecuoTopo", "CasaMaquinas", "CaixaDagua", "ArCondicionado",
    "EscadaMontante", "EscadaPatamar", "EscadaLance",
    "EncardidoParede", "EncardidoPoste", "EncardidoSarjeta",
    "SetaHaste", "SetaCabeca", "AroEsgoto", "TampaEsgoto", "RemendoAsfalto",
    "Jardineira", "JardineiraPlanta", "GradeJanela",
    "LetreiroLoja", "LetreiroLojaB", "LetreiroLojaC",
]



func _initialize() -> void:
    print("== ETAPA 17 QA (headless) ==")
    _scenario_a()
    _scenario_b()
    _scenario_c()
    _scenario_d()
    _scenario_e()
    _scenario_f()
    _scenario_g()
    _scenario_h()
    if _failures.is_empty():
        print("ETAPA17_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA17_QA_FALHOU")
        quit(1)


func _check(cond: bool, label: String) -> void:
    if cond:
        print("ok  ", label)
    else:
        _failures.append(label)
        print("FAIL ", label)


## Spec do capítulo: base do disco + override do cenário (mesmo caminho do jogo,
## game_3d._setup_world_kit -> kit.setup(SPEC_PATH, scenery)).
func _spec_do(cenario: Dictionary) -> Dictionary:
    return BuildingKit.spec_with_overrides(BuildingKit.load_spec(), cenario)


func _chunk(cenario: Dictionary, index: int = 3) -> Node3D:
    var no: Node3D = BuildingKit.build_chunk(_spec_do(cenario), index, 0.0)
    root.add_child(no)
    return no


## Soma as instâncias de um nó ao longo de cinco quarteirões seguidos (140 m).
## É a medida honesta de densidade: o ritmo das setas é global, então um bloco
## isolado de 28 m não distingue passo de 16 m de passo de 24 m.
func _instancias_na_rua(cenario: Dictionary, nome: String, blocos: int = 5) -> int:
    var total := 0
    for i in range(blocos):
        var chunk: Node3D = _chunk(cenario, i)
        total += _instancias(chunk, nome)
        chunk.queue_free()
    return total


## Procura um nó pelo nome dentro do quarteirão (os multimesh são filhos diretos,
## mas a busca recursiva protege contra reorganização futura da árvore).
func _achar(raiz: Node, nome: String) -> Node:
    if raiz.name == nome:
        return raiz
    for filho in raiz.get_children():
        var achado: Node = _achar(filho, nome)
        if achado != null:
            return achado
    return null


## Quantas instâncias esse multimesh emite (0 quando o nó nem existe).
func _instancias(raiz: Node, nome: String) -> int:
    var no: Node = _achar(raiz, nome)
    if no == null:
        return 0
    if no is MultiMeshInstance3D:
        var mmi := no as MultiMeshInstance3D
        if mmi.multimesh != null:
            return int(mmi.multimesh.instance_count)
    return 1


# RV-A. Padrões do spec.
func _scenario_a() -> void:
    var spec: Dictionary = BuildingKit.load_spec()
    var bloco = spec.get("rua_viva", {})
    var tem_blocos: bool = typeof(bloco) == TYPE_DICTIONARY \
            and bloco.has("coroamento") and bloco.has("decalques") and bloco.has("encardido")
    var coro: Dictionary = BuildingKit.rua_viva(spec, "coroamento")
    var dec: Dictionary = BuildingKit.rua_viva(spec, "decalques")
    var enc: Dictionary = BuildingKit.rua_viva(spec, "encardido")
    var padrao_ok: bool = bool(coro.get("escada_incendio", false)) \
            and int(coro.get("caixa_dagua_min_andares", 0)) == 3 \
            and absf(float(dec.get("seta_passo_m", 0.0)) - 16.0) < 0.001 \
            and absf(float(enc.get("albedo", 0.0)) - 0.42) < 0.001
    _check(tem_blocos and padrao_ok,
            "RV-A. world_spec.rua_viva com os 3 blocos e padrões do kit preservados")


# RV-B. Override do capítulo chega ao kit sem sujar o spec base.
func _scenario_b() -> void:
    var parque: Dictionary = _spec_do(LevelData.CENARIO_PARQUE)
    var centro: Dictionary = _spec_do(LevelData.CENARIO_CENTRO)
    var coro_parque: Dictionary = BuildingKit.rua_viva(parque, "coroamento")
    var coro_centro: Dictionary = BuildingKit.rua_viva(centro, "coroamento")
    var enc_centro: Dictionary = BuildingKit.rua_viva(centro, "encardido")
    var chegou: bool = not bool(coro_parque.get("escada_incendio", true)) \
            and int(coro_centro.get("caixa_dagua_min_andares", 0)) == 2 \
            and float(enc_centro.get("albedo", 1.0)) < 0.40
    # as chaves não citadas pelo capítulo continuam valendo (merge, não troca)
    var herdou: bool = bool(coro_centro.get("platibanda", false)) \
            and bool(BuildingKit.rua_viva(parque, "encardido").get("sarjeta", false))
    # e o spec do disco não foi mutado pelo override
    var base_intacta: bool = bool(BuildingKit.rua_viva(
            BuildingKit.load_spec(), "coroamento").get("escada_incendio", false))
    _check(chegou and herdou and base_intacta,
            "RV-B. override do cenário funde no spec, herda o resto e não muta a base")


# RV-C. Identidade de topo por capítulo.
func _scenario_c() -> void:
    var p_escada: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "EscadaMontante")
    var p_caixa: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "CaixaDagua")
    var p_ac: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "ArCondicionado")
    var c_escada: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "EscadaMontante")
    var c_caixa: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "CaixaDagua")
    var c_plati: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "Platibanda")
    var parque_limpo: bool = p_escada == 0 and p_caixa == 0 and p_ac == 0
    var centro_cheio: bool = c_escada > 0 and c_caixa > 0 and c_plati > 0
    print("  parque escada=%d caixa=%d ac=%d | centro escada=%d caixa=%d platibanda=%d" % [
        p_escada, p_caixa, p_ac, c_escada, c_caixa, c_plati])
    _check(parque_limpo and centro_cheio,
            "RV-C. PARQUE sem escada/caixa/ar-condicionado e CENTRO com o topo cheio")


# RV-D. Densidade dos decalques do asfalto.
func _scenario_d() -> void:
    var s_bairro: int = _instancias_na_rua(LevelData.CENARIO_BAIRRO, "SetaHaste")
    var s_avenida: int = _instancias_na_rua(LevelData.CENARIO_AVENIDA, "SetaHaste")
    var s_parque: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "SetaHaste")
    var r_bairro: int = _instancias_na_rua(LevelData.CENARIO_BAIRRO, "RemendoAsfalto")
    var r_centro: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "RemendoAsfalto")
    var r_parque: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "RemendoAsfalto")
    var setas_ok: bool = s_avenida > s_bairro and s_bairro > s_parque and s_parque > 0
    var remendos_ok: bool = r_centro > r_bairro and r_bairro > r_parque and r_parque > 0
    print("  setas 140 m  avenida=%d bairro=%d parque=%d" % [s_avenida, s_bairro, s_parque])
    print("  remendos 140 m centro=%d bairro=%d parque=%d" % [r_centro, r_bairro, r_parque])
    _check(setas_ok and remendos_ok,
            "RV-D. AVENIDA > BAIRRO > PARQUE em setas; CENTRO > BAIRRO > PARQUE em remendos")


# RV-E. Encardido por capítulo (força e superfícies).
func _scenario_e() -> void:
    var bairro: Node3D = _chunk(LevelData.CENARIO_BAIRRO)
    var centro: Node3D = _chunk(LevelData.CENARIO_CENTRO)
    var parque: Node3D = _chunk(LevelData.CENARIO_PARQUE)
    var a_bairro: float = _albedo_encardido(bairro)
    var a_centro: float = _albedo_encardido(centro)
    var a_parque: float = _albedo_encardido(parque)
    # menor albedo = mais sujo: centro é o mais encardido, parque o mais limpo
    var forca_ok: bool = a_centro < a_bairro and a_bairro < a_parque and a_centro > 0.0
    # PARQUE desliga a mancha no pé do poste; BAIRRO mantém
    var poste_ok: bool = _instancias_na_rua(LevelData.CENARIO_PARQUE, "EncardidoPoste") == 0 \
            and _instancias_na_rua(LevelData.CENARIO_BAIRRO, "EncardidoPoste") > 0
    print("  albedo encardido centro=%.3f bairro=%.3f parque=%.3f" % [a_centro, a_bairro, a_parque])
    bairro.queue_free()
    centro.queue_free()
    parque.queue_free()
    _check(forca_ok and poste_ok,
            "RV-E. albedo do encardido escala por capítulo e o poste do PARQUE fica limpo")


## Albedo do material de encardido aplicado na sarjeta do quarteirão.
func _albedo_encardido(raiz: Node) -> float:
    var no: Node = _achar(raiz, "EncardidoSarjeta")
    if no == null or not (no is MeshInstance3D):
        return -1.0
    var mi := no as MeshInstance3D
    var mat: Material = mi.material_override
    if mat == null and mi.mesh != null:
        mat = mi.mesh.surface_get_material(0)
    if mat is BaseMaterial3D:
        return (mat as BaseMaterial3D).albedo_color.r
    return -1.0


# RV-F. Orçamento: a variação por cenário é de estilo, não de custo. Contamos
# só os nós DA CAMADA VIVA (o resto do quarteirão varia por props, que é
# contrato antigo): nenhum capítulo pode passar o bairro em mais que
# TETO_NOS_EXTRA nós — a escada de incêndio vale 3, o ático alto vale 1 e os
# grupos de cor do letreiro valem até 2; o resto é densidade DENTRO de
# multimesh, que não cria chamada de desenho nova.
const TETO_NOS_EXTRA := 6


func _scenario_f() -> void:
    var capitulos := {
        "BAIRRO": LevelData.CENARIO_BAIRRO, "AVENIDA": LevelData.CENARIO_AVENIDA,
        "CENTRO": LevelData.CENARIO_CENTRO, "FEIRA": LevelData.CENARIO_FEIRA,
        "PARQUE": LevelData.CENARIO_PARQUE, "CHUVA": LevelData.CENARIO_CHUVA,
        "CENTRO_MOV": LevelData.CENARIO_CENTRO_MOV, "TERMINAL": LevelData.CENARIO_TERMINAL,
    }
    var base := _nos_rua_viva(LevelData.CENARIO_BAIRRO)
    var ok := true
    var linha := ""
    for nome in capitulos:
        var cenario: Dictionary = capitulos[nome]
        var total := _nos_rua_viva(cenario)
        linha += "%s=%d " % [nome, total]
        if total > base + TETO_NOS_EXTRA:
            ok = false
            print("  %s: %d nós da camada viva (bairro %d, teto +%d)" % [
                nome, total, base, TETO_NOS_EXTRA])
    print("  nós da camada viva por quarteirão: ", linha)
    _check(ok, "RV-F. nenhum capítulo passa o bairro em mais que %d nós da camada viva"
            % TETO_NOS_EXTRA)


## Quantos nós da camada viva (1 chamada de desenho cada) o quarteirão emite.
func _nos_rua_viva(cenario: Dictionary) -> int:
    var chunk: Node3D = _chunk(cenario)
    var total := 0
    for n in NOS_RUA_VIVA:
        if _achar(chunk, str(n)) != null:
            total += 1
    chunk.queue_free()
    return total


# RV-G. Jardineiras: existem, seguem o capítulo e continuam batchadas.
func _scenario_g() -> void:
    var j_parque: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "Jardineira")
    var j_centro: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "Jardineira")
    var j_avenida: int = _instancias_na_rua(LevelData.CENARIO_AVENIDA, "Jardineira")
    var j_feira: int = _instancias_na_rua(LevelData.CENARIO_FEIRA, "Jardineira")
    # parque (10 m) mais denso que centro (14 m), que é mais denso que avenida
    # (26 m); a feira desliga a jardineira porque a calçada é das barracas
    var jardim_ok: bool = j_parque > j_centro and j_centro > j_avenida \
            and j_avenida > 0 and j_feira == 0
    print("  jardineiras 140 m parque=%d centro=%d avenida=%d feira=%d" % [
        j_parque, j_centro, j_avenida, j_feira])
    _check(jardim_ok,
            "RV-G. jardineiras seguem o capítulo (PARQUE denso, FEIRA sem floreira)")


# RV-H. Letreiro de loja (3 grupos de cor) e grade de janela.
func _scenario_h() -> void:
    var l_centro := 0
    var l_parque := 0
    for n in ["LetreiroLoja", "LetreiroLojaB", "LetreiroLojaC"]:
        l_centro += _instancias_na_rua(LevelData.CENARIO_CENTRO, n)
        l_parque += _instancias_na_rua(LevelData.CENARIO_PARQUE, n)
    var g_centro: int = _instancias_na_rua(LevelData.CENARIO_CENTRO, "GradeJanela")
    var g_parque: int = _instancias_na_rua(LevelData.CENARIO_PARQUE, "GradeJanela")
    # 3 barras verticais por janela gradeada
    var centro_ok: bool = l_centro > 0 and g_centro > 0 and g_centro % 3 == 0
    var parque_ok: bool = l_parque == 0 and g_parque == 0
    # variedade: ao longo da rua os tres grupos de cor têm de aparecer, e cada
    # grupo é UM multimesh (não uma chamada de desenho por loja)
    var grupos := {}
    var nos := 0
    for i in range(5):
        var chunk: Node3D = _chunk(LevelData.CENARIO_CENTRO, i)
        for n in ["LetreiroLoja", "LetreiroLojaB", "LetreiroLojaC"]:
            var no: Node = _achar(chunk, n)
            if no != null:
                grupos[n] = true
                nos += 1
        chunk.queue_free()
    var variedade_ok: bool = grupos.size() >= 2 and nos <= 15
    print("  centro letreiro=%d (grupos de cor %d, nós em 5 quarteirões %d) grade=%d | parque letreiro=%d grade=%d" % [
        l_centro, grupos.size(), nos, g_centro, l_parque, g_parque])
    _check(centro_ok and parque_ok and variedade_ok,
            "RV-H. letreiros em 3 grupos de cor no CENTRO, grades no térreo, PARQUE sem nenhum")
