extends SceneTree
## ETAPA 4 — Teste de aceitação headless da estrutura de fase piloto
## (blueprint §7/§8: módulos editáveis + validador de caminho).
## Rodar: godot --headless --path . -s res://tools/qa_etapa4_piloto.gd
## Cenários:
##   P. dados do piloto (bairro_03): 336 m, 12 módulos, 6,0 m/s, prazo 66 s;
##      velocidade e prazo da fase 3 vêm do nível.
##   Q. validador de caminho: rota legal na velocidade base e no impulso.
##   R. validador rejeita nível sem rota (bloqueio total numa estação).
##   R2. validador exige ação real quando as saídas laterais estão fechadas.
##   S. percurso montado: entidades exatamente iguais aos dados do nível.
##   T. determinismo: camada de desafio não depende de semente aleatória.
## Código de saída 0 = OK, 1 = falha.

var _failures: Array = []
var _game = null


func _initialize() -> void:
    print("== ETAPA 4 QA (headless) ==")
    var packed: PackedScene = load("res://scenes/main.tscn")
    _game = packed.instantiate()
    root.add_child(_game)
    await process_frame
    await process_frame
    _unlock_up_to_phase_3()
    _scenario_p()
    _scenario_q()
    _scenario_r()
    _scenario_r2()
    _scenario_s()
    _scenario_t()
    if _failures.is_empty():
        print("ETAPA4_QA_OK")
        quit(0)
    else:
        for f in _failures:
            print("FALHOU: ", f)
        print("ETAPA4_QA_FALHOU")
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


func _start_phase(index: int) -> void:
    _game._start_run(index)
    _game.run_director.countdown_left = 0.0
    _game.run_mode = "playing"
    _game.hearts = 3
    _game.invulnerability = 0.0
    _game.player_lane = 1
    _game.player_x = _game.LANE_X[1]


# P. Dados autorais do piloto + overrides de velocidade e prazo.
func _scenario_p() -> void:
    var level: Dictionary = LevelData.for_phase(2)
    _check(not level.is_empty()
            and str(level.get("id", "")) == "bairro_03"
            and int(level.get("chunks", 0)) == 12
            and absf(float(level.get("distance_m", 0.0)) - 336.0) < 0.01
            and absf(float(level.get("chunk_length_m", 0.0)) * 12.0 - 336.0) < 0.01,
            "P1. piloto bairro_03: 336 m em 12 módulos de 28 m")
    _check(absf(float(level.get("base_speed_mps", 0.0)) - 6.0) < 0.01
            and absf(float(level.get("deadline_seconds", 0.0)) - 66.0) < 0.01
            and level.get("patterns", []).size() == 9
            and level.get("coins", []).size() == 12,
            "P2. piloto: 6,0 m/s, prazo 66 s, 9 padrões + 12 moedas (§8)")
    _check(absf(_game._phase_speed_for(2) - 6.0) < 0.01
            and absf(_game._phase_deadline_for(2) - 66.0) < 0.01,
            "P3. fase 3 usa velocidade e prazo do nível")
    _start_phase(2)
    _check(absf(_game.run_total - 336.0) < 0.01,
            "P4. percurso da fase 3 tem a distância do nível (336 m)")


# Q. Validador de caminho aprova o piloto na velocidade base e no impulso.
func _scenario_q() -> void:
    var result: Dictionary = PatternValidator.validate(LevelData.PILOT)
    var route: Array = result.get("route", [])
    print("validador: valid=%s fator=%.2f rota=%d passos motivo=%s" % [
            str(result.get("valid")), float(result.get("speed_factor", 1.0)),
            route.size(), str(result.get("reason"))])
    _check(bool(result.get("valid", false)) and not route.is_empty(),
            "Q. validador aprova o piloto (base e impulso 1,22x) com rota")


# R. Validador rejeita nível com estação bloqueada nos três corredores.
func _scenario_r() -> void:
    var bad_level: Dictionary = {
        "base_speed_mps": 6.0,
        "patterns": [
            {"kind": "car", "lane": 0, "at_m": 50.0},
            {"kind": "car", "lane": 1, "at_m": 50.0},
            {"kind": "car", "lane": 2, "at_m": 50.0},
        ],
    }
    var result: Dictionary = PatternValidator.validate(bad_level)
    _check(not bool(result.get("valid", true)),
            "R. estação sem corredor livre -> validador rejeita")


# R2. Sem saída lateral, a rota precisa usar as ações de verdade:
# cone na esquerda exige pulo, barreira no centro exige deslize.
func _scenario_r2() -> void:
    var action_level: Dictionary = {
        "base_speed_mps": 6.0,
        "patterns": [
            {"kind": "cone", "lane": 0, "at_m": 60.0},
            {"kind": "bench", "lane": 1, "at_m": 60.0},
            {"kind": "bench", "lane": 2, "at_m": 60.0},
            {"kind": "barrier", "lane": 1, "at_m": 120.0},
            {"kind": "hydrant", "lane": 0, "at_m": 120.0},
            {"kind": "hydrant", "lane": 2, "at_m": 120.0},
        ],
    }
    var result: Dictionary = PatternValidator.validate(action_level)
    var actions: Array = []
    for m in result.get("route", []):
        actions.append(str(m["action"]))
    _check(bool(result.get("valid", false))
            and actions.has("jump") and actions.has("slide"),
            "R2. saída fechada -> rota com pulo e deslize obrigatórios")


func _entity_signature() -> String:
    var parts: Array = []
    for e in _game.entities:
        parts.append("%s|%d|%d|%s" % [
                str(e["kind"]), int(e["lane"]),
                int(roundf(float(e["distance"]) * 10.0)),
                "c" if bool(e["collectible"]) else "o"])
    parts.sort()
    return ";".join(parts)


func _expected_signature() -> String:
    var parts: Array = []
    for p in LevelData.PILOT.get("patterns", []):
        parts.append("%s|%d|%d|o" % [str(p["kind"]), int(p["lane"]), int(roundf(float(p["at_m"]) * 10.0))])
    for c in LevelData.PILOT.get("coins", []):
        parts.append("%s|%d|%d|c" % [str(c["kind"]), int(c["lane"]), int(roundf(float(c["at_m"]) * 10.0))])
    parts.sort()
    return ";".join(parts)


# S. Percurso montado bate exatamente com os dados do nível.
func _scenario_s() -> void:
    _start_phase(2)
    var expected: String = _expected_signature()
    var actual: String = _entity_signature()
    print("entidades: %d (esperado %d)" % [_game.entities.size(),
            LevelData.PILOT["patterns"].size() + LevelData.PILOT["coins"].size()])
    _check(_game.entities.size() == 21 and actual == expected,
            "S. fase 3 montada só com os módulos do nível (sem procedural)")


# T. Determinismo: camada de desafio independe de semente aleatória.
func _scenario_t() -> void:
    _game.rng.seed = 20240917
    _start_phase(2)
    var sig1: String = _entity_signature()
    _game.rng.seed = 777
    _start_phase(2)
    var sig2: String = _entity_signature()
    _check(sig1 == sig2 and sig1.length() > 0,
            "T. percurso do nível não depende de semente (dados autorais)")
