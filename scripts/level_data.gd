class_name LevelData
extends RefCounted
## ETAPA 4 — dados autorais de fase (blueprint §7/§8).
##
## Duas camadas independentes: o cenário (aparência) continua procedural;
## o nível define apenas a camada de desafio (padrões de obstáculos e
## moedas), com distância longitudinal e corredor explícitos.
##
## Chaves de um nível:
##   id, version, name, phase_index, distance_m, chunk_length_m, chunks,
##   base_speed_mps, deadline_seconds, layout_seed,
##   patterns: [{kind, lane, at_m}], coins: [{kind, lane, at_m}]
##
## Corredores: E=0, C=1, D=2 (LANE_X). O piloto usa os três corredores
## existentes; a conversão visual para três corredores de calçada é trabalho
## de mundo/arte (M2+), não muda contratos de colisão.

const PILOT: Dictionary = {
    "id": "bairro_03",
    "version": 1,
    "name": "Rua do Ipê — antes das portas fecharem",
    "phase_index": 2,
    "distance_m": 336.0,
    "chunk_length_m": 28.0,
    "chunks": 12,
    "base_speed_mps": 6.0,
    "deadline_seconds": 66.0,
    "layout_seed": 103,
    # Roteiro fixo do blueprint §8 (módulo, situação, intenção).
    "patterns": [
        # M2 — cone baixo em C (~42 m): pular ou sair para E/D.
        {"kind": "cone", "lane": 1, "at_m": 42.0},
        # M3 — obstáculo baixo em D (~70 m): repetir ação; centro seguro.
        {"kind": "cone", "lane": 2, "at_m": 70.0},
        # M4 — barreira suspensa em C (~98 m): ensinar deslize.
        {"kind": "barrier", "lane": 1, "at_m": 98.0},
        # M5 — bloqueio alto em D (~126 m): praticar sem ações simultâneas.
        {"kind": "hydrant", "lane": 2, "at_m": 126.0},
        # M6 — banco em E (~154 m): desvio lateral contra volume sólido.
        {"kind": "bench", "lane": 0, "at_m": 154.0},
        # M7 — cone em C e banco em D na mesma estação (~182 m): escolher E
        # ou pular em C; nunca bloquear as três opções.
        {"kind": "cone", "lane": 1, "at_m": 182.0},
        {"kind": "bench", "lane": 2, "at_m": 182.0},
        # M9 — barreira em D com moedas na rota (~238 m); C livre: risco
        # opcional, conclusão não exige a recompensa.
        {"kind": "barrier", "lane": 2, "at_m": 238.0},
        # M10 — revisão: obstáculo baixo em C (~266 m): sem novidade.
        {"kind": "cone", "lane": 1, "at_m": 266.0},
    ],
    "coins": [
        # M1 — largada livre: três moedas no centro.
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        # M8 — respiro: jardim e moedas.
        {"kind": "coin", "lane": 1, "at_m": 202.0},
        {"kind": "coin", "lane": 1, "at_m": 210.0},
        {"kind": "coin", "lane": 1, "at_m": 218.0},
        # M9 — rota opcional com risco (deslizar sob a barreira paga).
        {"kind": "coin", "lane": 2, "at_m": 230.0},
        {"kind": "coin", "lane": 2, "at_m": 238.0},
        {"kind": "coin", "lane": 2, "at_m": 246.0},
        # M11 — ônibus visível: moedas guiam para o ponto.
        {"kind": "coin", "lane": 1, "at_m": 288.0},
        {"kind": "coin", "lane": 1, "at_m": 296.0},
        {"kind": "coin", "lane": 1, "at_m": 304.0},
    ],
}

const LEVELS: Array = [PILOT]


static func for_phase(index: int) -> Dictionary:
    for level in LEVELS:
        if int(level.get("phase_index", -1)) == index:
            return level
    return {}


static func has_level(index: int) -> bool:
    return not for_phase(index).is_empty()
