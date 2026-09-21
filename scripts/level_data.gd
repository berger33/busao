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
    # ETAPA 5 — camada de cenario (independente do desafio): perfil que o
    # building_kit aplica so nesta fase. Deck de 9,9 m cobrindo os tres
    # corredores de corrida (bordas a 4,95 m) e ipe amarelo no lugar da
    # arvore comum — a Rua do Ipe le como rua de calcada larga.
    "scenery": {
        "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
        "props": {"arvore": {"glb": "ipe_amarelo"}},
    },
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

## ETAPA 7 — cenario compartilhado das fases do bairro: deck cobrindo os
## tres corredores de corrida (a fase 3 soma o ipe amarelo por conta propria).
const CENARIO_TRES_CALCADAS: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
}

## Fase 1 — "Saiu atrasada" (PLANO_50_FASES): aprender troca de corredor e
## pulo; cones baixos isolados; moedas guiam uma rota ampla. Clímax: dois
## cones em estações separadas, sempre com desvio disponível.
const FASE_1: Dictionary = {
    "id": "bairro_01",
    "version": 1,
    "name": "Saiu atrasada",
    "phase_index": 0,
    "distance_m": 224.0,
    "chunk_length_m": 28.0,
    "chunks": 8,
    "base_speed_mps": 5.5,
    "deadline_seconds": 55.0,
    "layout_seed": 101,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 40.0},
        {"kind": "cone", "lane": 0, "at_m": 68.0},
        {"kind": "cone", "lane": 2, "at_m": 96.0},
        {"kind": "cone", "lane": 1, "at_m": 146.0},
        {"kind": "cone", "lane": 2, "at_m": 162.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 116.0},
        {"kind": "coin", "lane": 1, "at_m": 122.0},
        {"kind": "coin", "lane": 1, "at_m": 128.0},
        {"kind": "coin", "lane": 1, "at_m": 178.0},
        {"kind": "coin", "lane": 1, "at_m": 186.0},
        {"kind": "coin", "lane": 1, "at_m": 194.0},
    ],
}

## Fase 2 — "A praça do bairro": distinguir obstáculo baixo de volume sólido
## (cone x banco). Clímax: banco ocupa um corredor, cone outro, terceiro livre.
const FASE_2: Dictionary = {
    "id": "bairro_02",
    "version": 1,
    "name": "A praça do bairro",
    "phase_index": 1,
    "distance_m": 280.0,
    "chunk_length_m": 28.0,
    "chunks": 10,
    "base_speed_mps": 5.8,
    "deadline_seconds": 61.0,
    "layout_seed": 102,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 40.0},
        {"kind": "bench", "lane": 0, "at_m": 68.0},
        {"kind": "cone", "lane": 2, "at_m": 96.0},
        {"kind": "bench", "lane": 1, "at_m": 124.0},
        {"kind": "cone", "lane": 0, "at_m": 150.0},
        {"kind": "bench", "lane": 2, "at_m": 152.0},
        {"kind": "bench", "lane": 1, "at_m": 210.0},
        {"kind": "cone", "lane": 2, "at_m": 210.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 176.0},
        {"kind": "coin", "lane": 1, "at_m": 182.0},
        {"kind": "coin", "lane": 1, "at_m": 188.0},
        {"kind": "coin", "lane": 1, "at_m": 240.0},
        {"kind": "coin", "lane": 1, "at_m": 248.0},
        {"kind": "coin", "lane": 1, "at_m": 256.0},
    ],
}

## Fase 4 — "Remendo na calçada": introduz o buraco curto (pulo), com
## cones e a barreira já conhecidos. Clímax: buraco seguido de banco,
## com aterrissagem e tempo de troca garantidos.
const FASE_4: Dictionary = {
    "id": "bairro_04",
    "version": 1,
    "name": "Remendo na calçada",
    "phase_index": 3,
    "distance_m": 336.0,
    "chunk_length_m": 28.0,
    "chunks": 12,
    "base_speed_mps": 6.0,
    "deadline_seconds": 68.0,
    "layout_seed": 104,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "pothole", "lane": 1, "at_m": 42.0},
        {"kind": "pothole", "lane": 2, "at_m": 70.0},
        {"kind": "cone", "lane": 2, "at_m": 98.0},
        {"kind": "pothole", "lane": 0, "at_m": 126.0},
        {"kind": "barrier", "lane": 1, "at_m": 154.0},
        {"kind": "pothole", "lane": 1, "at_m": 182.0},
        {"kind": "cone", "lane": 2, "at_m": 182.0},
        {"kind": "cone", "lane": 0, "at_m": 210.0},
        {"kind": "pothole", "lane": 1, "at_m": 210.0},
        {"kind": "pothole", "lane": 1, "at_m": 260.0},
        {"kind": "bench", "lane": 1, "at_m": 276.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 232.0},
        {"kind": "coin", "lane": 1, "at_m": 238.0},
        {"kind": "coin", "lane": 1, "at_m": 244.0},
        {"kind": "coin", "lane": 1, "at_m": 292.0},
        {"kind": "coin", "lane": 1, "at_m": 300.0},
        {"kind": "coin", "lane": 1, "at_m": 308.0},
    ],
}

## Fase 5 — "Primeiro compromisso": revisão das quatro primeiras sem
## obstáculo novo; baixo → alto → desvio, com recuperação entre ações.
const FASE_5: Dictionary = {
    "id": "bairro_05",
    "version": 1,
    "name": "Primeiro compromisso",
    "phase_index": 4,
    "distance_m": 364.0,
    "chunk_length_m": 28.0,
    "chunks": 13,
    "base_speed_mps": 6.2,
    "deadline_seconds": 69.0,
    "layout_seed": 105,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 40.0},
        {"kind": "barrier", "lane": 1, "at_m": 68.0},
        {"kind": "pothole", "lane": 2, "at_m": 96.0},
        {"kind": "bench", "lane": 0, "at_m": 124.0},
        {"kind": "cone", "lane": 2, "at_m": 152.0},
        {"kind": "cone", "lane": 0, "at_m": 178.0},
        {"kind": "bench", "lane": 1, "at_m": 178.0},
        {"kind": "pothole", "lane": 1, "at_m": 206.0},
        {"kind": "cone", "lane": 2, "at_m": 206.0},
        {"kind": "cone", "lane": 1, "at_m": 262.0},
        {"kind": "bench", "lane": 1, "at_m": 278.0},
        {"kind": "barrier", "lane": 1, "at_m": 294.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 234.0},
        {"kind": "coin", "lane": 1, "at_m": 240.0},
        {"kind": "coin", "lane": 1, "at_m": 246.0},
        {"kind": "coin", "lane": 1, "at_m": 316.0},
        {"kind": "coin", "lane": 1, "at_m": 324.0},
        {"kind": "coin", "lane": 1, "at_m": 332.0},
    ],
}

const LEVELS: Array = [FASE_1, FASE_2, PILOT, FASE_4, FASE_5]


static func for_phase(index: int) -> Dictionary:
    for level in LEVELS:
        if int(level.get("phase_index", -1)) == index:
            return level
    return {}


static func has_level(index: int) -> bool:
    return not for_phase(index).is_empty()
