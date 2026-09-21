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

## Fase 6 — "Na porta da padaria" (PLANO_50_FASES): hidrante, lixeira e
## orelhão como bloqueios altos; cones como revisão. Clímax: alternância de
## bloqueio alto em E e D, com a rota C sempre legível.
const FASE_6: Dictionary = {
    "id": "bairro_06",
    "version": 1,
    "name": "Na porta da padaria",
    "phase_index": 5,
    "distance_m": 364.0,
    "chunk_length_m": 28.0,
    "chunks": 13,
    "base_speed_mps": 6.2,
    "deadline_seconds": 71.0,
    "layout_seed": 106,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "trash", "lane": 0, "at_m": 44.0},
        {"kind": "hydrant", "lane": 2, "at_m": 72.0},
        {"kind": "cone", "lane": 1, "at_m": 100.0},
        {"kind": "payphone", "lane": 0, "at_m": 128.0},
        {"kind": "hydrant", "lane": 0, "at_m": 156.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "trash", "lane": 2, "at_m": 184.0},
        {"kind": "cone", "lane": 0, "at_m": 184.0},
        {"kind": "hydrant", "lane": 0, "at_m": 260.0},
        {"kind": "trash", "lane": 2, "at_m": 274.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 232.0},
        {"kind": "coin", "lane": 1, "at_m": 238.0},
        {"kind": "coin", "lane": 1, "at_m": 244.0},
        {"kind": "coin", "lane": 1, "at_m": 316.0},
        {"kind": "coin", "lane": 1, "at_m": 324.0},
        {"kind": "coin", "lane": 1, "at_m": 332.0},
    ],
}

## Fase 7 — "Passagem de pedestres": primeiro pedestre atravessa após
## preparar o movimento (espera visível + travessia em tempo fixo); bancos
## fixos. Clímax: pedestre cruza um corredor, rota lateral livre.
## Travessia: from_x -> to_x a cross_mps, com lead_m de aviso.
const FASE_7: Dictionary = {
    "id": "bairro_07",
    "version": 1,
    "name": "Passagem de pedestres",
    "phase_index": 6,
    "distance_m": 364.0,
    "chunk_length_m": 28.0,
    "chunks": 13,
    "base_speed_mps": 6.3,
    "deadline_seconds": 70.0,
    "layout_seed": 107,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "bench", "lane": 0, "at_m": 44.0},
        {"kind": "crosser", "lane": 2, "at_m": 72.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "cone", "lane": 1, "at_m": 100.0},
        {"kind": "crosser", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "bench", "lane": 1, "at_m": 156.0},
        {"kind": "crosser", "lane": 2, "at_m": 158.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "crosser", "lane": 0, "at_m": 234.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "cone", "lane": 1, "at_m": 234.0},
        {"kind": "crosser", "lane": 2, "at_m": 250.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 40.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 198.0},
        {"kind": "coin", "lane": 1, "at_m": 204.0},
        {"kind": "coin", "lane": 1, "at_m": 210.0},
        {"kind": "coin", "lane": 1, "at_m": 316.0},
        {"kind": "coin", "lane": 1, "at_m": 324.0},
        {"kind": "coin", "lane": 1, "at_m": 332.0},
    ],
}

## Fase 8 — "Hora da entrega": carrinho de entrega com travessia lateral e
## aviso; lixeiras e pedestres como revisão. Clímax: carrinho + banco criam
## escolha anunciada entre dois caminhos (corredor livre declarado).
const FASE_8: Dictionary = {
    "id": "bairro_08",
    "version": 1,
    "name": "Hora da entrega",
    "phase_index": 7,
    "distance_m": 392.0,
    "chunk_length_m": 28.0,
    "chunks": 14,
    "base_speed_mps": 6.4,
    "deadline_seconds": 73.0,
    "layout_seed": 108,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "trash", "lane": 2, "at_m": 44.0},
        {"kind": "crosser", "lane": 2, "at_m": 72.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "cart", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 52.0},
        {"kind": "cone", "lane": 1, "at_m": 128.0},
        {"kind": "cart", "lane": 0, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 52.0},
        {"kind": "bench", "lane": 1, "at_m": 184.0},
        {"kind": "cart", "lane": 2, "at_m": 186.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 52.0},
        {"kind": "trash", "lane": 0, "at_m": 212.0},
        {"kind": "crosser", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "cart", "lane": 2, "at_m": 266.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 52.0},
        {"kind": "cone", "lane": 2, "at_m": 266.0},
        {"kind": "cart", "lane": 0, "at_m": 282.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 52.0},
        {"kind": "bench", "lane": 1, "at_m": 282.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 240.0},
        {"kind": "coin", "lane": 1, "at_m": 246.0},
        {"kind": "coin", "lane": 1, "at_m": 252.0},
        {"kind": "coin", "lane": 1, "at_m": 344.0},
        {"kind": "coin", "lane": 1, "at_m": 352.0},
        {"kind": "coin", "lane": 1, "at_m": 360.0},
    ],
}

## Fase 9 — "A van da esquina": veículo parado invade a borda; desvio pelo
## corredor aberto; nunca saltar o teto (VEHICLE). Clímax: van e barreira
## baixa (cone) em estações separadas.
const FASE_9: Dictionary = {
    "id": "bairro_09",
    "version": 1,
    "name": "A van da esquina",
    "phase_index": 8,
    "distance_m": 392.0,
    "chunk_length_m": 28.0,
    "chunks": 14,
    "base_speed_mps": 6.5,
    "deadline_seconds": 72.0,
    "layout_seed": 109,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "van", "lane": 0, "at_m": 72.0},
        {"kind": "hydrant", "lane": 2, "at_m": 100.0},
        {"kind": "van", "lane": 2, "at_m": 128.0},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "van", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 2, "at_m": 184.0},
        {"kind": "barrier", "lane": 1, "at_m": 212.0},
        {"kind": "van", "lane": 1, "at_m": 266.0},
        {"kind": "cone", "lane": 1, "at_m": 282.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 240.0},
        {"kind": "coin", "lane": 1, "at_m": 246.0},
        {"kind": "coin", "lane": 1, "at_m": 252.0},
        {"kind": "coin", "lane": 1, "at_m": 344.0},
        {"kind": "coin", "lane": 1, "at_m": 352.0},
        {"kind": "coin", "lane": 1, "at_m": 360.0},
    ],
}

## Fase 10 — "Feira de sábado": revisão de movimento lateral e bloqueios;
## faixa de corrida limpa entre barracas. Clímax: carrinho -> pedestre ->
## desvio de banco, com intervalo de recuperação mantido.
const FASE_10: Dictionary = {
    "id": "bairro_10",
    "version": 1,
    "name": "Feira de sábado",
    "phase_index": 9,
    "distance_m": 420.0,
    "chunk_length_m": 28.0,
    "chunks": 15,
    "base_speed_mps": 6.5,
    "deadline_seconds": 75.0,
    "layout_seed": 110,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "trash", "lane": 0, "at_m": 72.0},
        {"kind": "cart", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 53.0},
        {"kind": "crosser", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "bench", "lane": 1, "at_m": 156.0},
        {"kind": "cart", "lane": 0, "at_m": 184.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 53.0},
        {"kind": "hydrant", "lane": 0, "at_m": 212.0},
        {"kind": "crosser", "lane": 2, "at_m": 240.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "cone", "lane": 1, "at_m": 240.0},
        {"kind": "cart", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 53.0},
        {"kind": "crosser", "lane": 0, "at_m": 312.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 40.0},
        {"kind": "bench", "lane": 1, "at_m": 312.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 368.0},
        {"kind": "coin", "lane": 1, "at_m": 376.0},
        {"kind": "coin", "lane": 1, "at_m": 384.0},
    ],
}

const LEVELS: Array = [FASE_1, FASE_2, PILOT, FASE_4, FASE_5, FASE_6, FASE_7, FASE_8, FASE_9, FASE_10]


static func for_phase(index: int) -> Dictionary:
    for level in LEVELS:
        if int(level.get("phase_index", -1)) == index:
            return level
    return {}


static func has_level(index: int) -> bool:
    return not for_phase(index).is_empty()
