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

## ETAPA 10 — avenida do lote 16-20: mesmo deck dos tres corredores, com
## palmeiras no lugar da arvore comum (identidade do capitulo).
const CENARIO_AVENIDA: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {"arvore": {"glb": "palmeira"}},
}

## ETAPA 11 — centro histórico do lote 21-25: mesmo deck dos três
## corredores, com ipês na praça, bancos e postes de ferro mais densos e
## rua de comércio antigo (pesos do kit: loja e reboco dominam; vitrines
## com toldo e molduras vêm do building_kit, camada viva do cenário).
const CENARIO_CENTRO: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "ipe_amarelo"},
        "banco": {"espacamento_m": 10.0},
        "poste": {"espacamento_m": 10.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 1, "reboco": 4, "loja": 5, "obra": 0}},
}

## ETAPA 11 — largo da fase 25: o centro + a igreja ao lado do ponto.
const CENARIO_LARGO: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "ipe_amarelo"},
        "banco": {"espacamento_m": 10.0},
        "poste": {"espacamento_m": 10.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 1, "reboco": 4, "loja": 5, "obra": 0}},
    "marco": "igreja",
}

## ETAPA 12 — feira livre do lote 26-30: mesmo deck dos três corredores,
## árvore comum (16 m) de volta no lugar do ipê, banco na rotina do kit,
## lixeira densa (12 m), galpões e lojas no fundo; barracas dos dois lados
## a cada 56 m, pulando as que caem sobre travessias (bloco "feira", lido
## por _spawn_feira; visual puro, sem colisão).
const CENARIO_FEIRA: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "arvore", "espacamento_m": 16.0},
        "banco": {"espacamento_m": 18.0},
        "lixeira": {"espacamento_m": 12.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 3, "reboco": 3, "loja": 3, "obra": 1}},
    "feira": {"passo_m": 56.0, "x_m": 6.4, "margem_cruzamento_m": 6.0},
}

## ETAPA 13 — parque e orla do lote 31-35: mesmo deck dos três corredores,
## palmeiras em alameda (8 m, cada uma com o canteiro do kit), bancos de
## praça, lixeira esparsa, casas baixas no fundo (1-2 pisos: horizonte
## aberto); quiosques dos dois lados a cada 112 m, pulando as que caem
## sobre travessias (bloco "quiosques", lido por _spawn_quiosques); a
## paleta "orla" fixa a luz aberta do capítulo (lida por
## _render_profile_world; sombras de contato preservadas).
const CENARIO_PARQUE: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "palmeira", "espacamento_m": 8.0},
        "banco": {"espacamento_m": 12.0},
        "lixeira": {"espacamento_m": 18.0},
    },
    "predios": {
        "tipo_pesos": {"tijolo": 2, "reboco": 4, "loja": 2, "obra": 0},
        "pisos": [1, 2],
    },
    "quiosques": {"passo_m": 112.0, "x_m": 6.4, "margem_cruzamento_m": 6.0},
    "paleta": {
        "nome": "orla",
        "sol": [1.0, 0.95, 0.85],
        "nevoa": [0.86, 0.83, 0.76],
        "sombra": [0.33, 0.39, 0.48],
        "ceu_alto": [0.30, 0.50, 0.76],
        "ceu_horizonte": [0.85, 0.84, 0.80],
        "sol_rotacao": [-9.0, 170.0, 0.0],
        "sol_energia": 1.15,
        "energia_ambiente": 0.66,
        "nevoa_densidade": 0.35,
        "exposicao": 0.55,
        "nuvens": 0.25,
    },
}

## ETAPA 13 — orla da fase 35: o parque + a guarita ao lado do ponto.
const CENARIO_ORLA: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "palmeira", "espacamento_m": 8.0},
        "banco": {"espacamento_m": 12.0},
        "lixeira": {"espacamento_m": 18.0},
    },
    "predios": {
        "tipo_pesos": {"tijolo": 2, "reboco": 4, "loja": 2, "obra": 0},
        "pisos": [1, 2],
    },
    "quiosques": {"passo_m": 112.0, "x_m": 6.4, "margem_cruzamento_m": 6.0},
    "paleta": {
        "nome": "orla",
        "sol": [1.0, 0.95, 0.85],
        "nevoa": [0.86, 0.83, 0.76],
        "sombra": [0.33, 0.39, 0.48],
        "ceu_alto": [0.30, 0.50, 0.76],
        "ceu_horizonte": [0.85, 0.84, 0.80],
        "sol_rotacao": [-9.0, 170.0, 0.0],
        "sol_energia": 1.15,
        "energia_ambiente": 0.66,
        "nevoa_densidade": 0.35,
        "exposicao": 0.55,
        "nuvens": 0.25,
    },
    "marco": "guarita",
}

## ETAPA 14 — rua molhada do lote 36-40: mesmo deck dos três corredores,
## árvore comum, bancos e lixeiras na rotina, casas e lojas no fundo; o
## clima fixo do nível ("chuva": garoa de 700 partículas, sem relâmpago;
## poças do ambiente aparecem com o molhado) carrega o capítulo — sem
## quiosques, barracas ou marco. O rodízio global daria noite urbana às
## fases 36 e 40 (índices 35 e 39); a paleta "dia" as mantém legíveis
## (36: garoa de dia; 40: sol de volta), e o motor clareia aos poucos
## (transição de estado + secagem). 37–39 usam o rodízio (manhã, tarde
## dourada e nublado sobre a chuva).
const CENARIO_CHUVA: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "arvore", "espacamento_m": 12.0},
        "banco": {"espacamento_m": 14.0},
        "lixeira": {"espacamento_m": 18.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 3, "reboco": 4, "loja": 2, "obra": 1}},
    "clima": "chuva",
    "paleta": {
        "nome": "chuva_dia",
        "sol": [1.0, 0.93, 0.80],
        "nevoa": [0.84, 0.79, 0.70],
        "sombra": [0.33, 0.39, 0.48],
        "ceu_alto": [0.32, 0.48, 0.72],
        "ceu_horizonte": [0.82, 0.80, 0.76],
        "sol_rotacao": [-9.0, 170.0, 0.0],
        "sol_energia": 1.1,
        "energia_ambiente": 0.62,
        "nevoa_densidade": 0.5,
        "exposicao": 0.51,
        "nuvens": 0.3,
    },
}
const CENARIO_CHUVA_CICLO: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "arvore", "espacamento_m": 12.0},
        "banco": {"espacamento_m": 14.0},
        "lixeira": {"espacamento_m": 18.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 3, "reboco": 4, "loja": 2, "obra": 1}},
    "clima": "chuva",
}
const CENARIO_SOL: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "arvore", "espacamento_m": 12.0},
        "banco": {"espacamento_m": 14.0},
        "lixeira": {"espacamento_m": 18.0},
    },
    "predios": {"tipo_pesos": {"tijolo": 3, "reboco": 4, "loja": 2, "obra": 1}},
    "clima": "limpo",
    "paleta": {
        "nome": "sol",
        "sol": [1.0, 0.93, 0.80],
        "nevoa": [0.84, 0.79, 0.70],
        "sombra": [0.33, 0.39, 0.48],
        "ceu_alto": [0.32, 0.48, 0.72],
        "ceu_horizonte": [0.82, 0.80, 0.76],
        "sol_rotacao": [-9.0, 170.0, 0.0],
        "sol_energia": 1.1,
        "energia_ambiente": 0.62,
        "nevoa_densidade": 0.5,
        "exposicao": 0.51,
        "nuvens": 0.3,
    },
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

## Fase 11 — "Sob o andaime" (PLANO_50_FASES): andaime com vão para
## deslize e apoios laterais; buracos conhecidos. Clímax: barra suspensa
## seguida de desvio, nunca salto obrigatório sob a barra.
const FASE_11: Dictionary = {
    "id": "bairro_11",
    "version": 1,
    "name": "Sob o andaime",
    "phase_index": 10,
    "distance_m": 392.0,
    "chunk_length_m": 28.0,
    "chunks": 14,
    "base_speed_mps": 6.6,
    "deadline_seconds": 72.0,
    "layout_seed": 111,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "scaffold", "lane": 1, "at_m": 72.0},
        {"kind": "pothole", "lane": 2, "at_m": 100.0},
        {"kind": "scaffold", "lane": 0, "at_m": 128.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "scaffold", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 2, "at_m": 184.0},
        {"kind": "scaffold", "lane": 1, "at_m": 266.0},
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

## Fase 12 — "Poças da manhã": poças bem delimitadas; atravessar molha o
## pé (lentidão determinística, sem dano); pular resolve. Clímax: rota seca
## simples versus moedas com salto sobre a poça.
const FASE_12: Dictionary = {
    "id": "bairro_12",
    "version": 1,
    "name": "Poças da manhã",
    "phase_index": 11,
    "distance_m": 392.0,
    "chunk_length_m": 28.0,
    "chunks": 14,
    "base_speed_mps": 6.6,
    "deadline_seconds": 72.0,
    "layout_seed": 112,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "puddle", "lane": 1, "at_m": 72.0},
        {"kind": "bench", "lane": 0, "at_m": 100.0},
        {"kind": "puddle", "lane": 2, "at_m": 128.0},
        {"kind": "scaffold", "lane": 1, "at_m": 156.0},
        {"kind": "puddle", "lane": 0, "at_m": 184.0},
        {"kind": "puddle", "lane": 1, "at_m": 184.0},
        {"kind": "puddle", "lane": 1, "at_m": 266.0},
        {"kind": "bench", "lane": 2, "at_m": 266.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 2, "at_m": 122.0},
        {"kind": "coin", "lane": 2, "at_m": 128.0},
        {"kind": "coin", "lane": 1, "at_m": 240.0},
        {"kind": "coin", "lane": 1, "at_m": 246.0},
        {"kind": "coin", "lane": 1, "at_m": 252.0},
        {"kind": "coin", "lane": 1, "at_m": 344.0},
        {"kind": "coin", "lane": 1, "at_m": 352.0},
        {"kind": "coin", "lane": 1, "at_m": 360.0},
    ],
}

## Fase 13 — "Ciclovia na praça": ciclista cruza à frente com aviso visível
## (travessia rápida, 3,0 m/s); floreiras limitam um corredor. Clímax:
## ciclista em janela fixa, seguido de trecho livre e cone baixo.
const FASE_13: Dictionary = {
    "id": "bairro_13",
    "version": 1,
    "name": "Ciclovia na praça",
    "phase_index": 12,
    "distance_m": 420.0,
    "chunk_length_m": 28.0,
    "chunks": 15,
    "base_speed_mps": 6.8,
    "deadline_seconds": 72.0,
    "layout_seed": 113,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "planter", "lane": 0, "at_m": 72.0},
        {"kind": "cyclist", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 18.5},
        {"kind": "cone", "lane": 2, "at_m": 128.0},
        {"kind": "planter", "lane": 1, "at_m": 156.0},
        {"kind": "cyclist", "lane": 0, "at_m": 184.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 18.5},
        {"kind": "bench", "lane": 0, "at_m": 212.0},
        {"kind": "cyclist", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 18.5},
        {"kind": "planter", "lane": 1, "at_m": 296.0},
        {"kind": "cone", "lane": 1, "at_m": 322.0},
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

## Fase 14 — "Olha a moto": moto atravessa no cruzamento (4,5 m/s) com som
## + sinal visual antes da passagem; caminho seguro explícito. Clímax: dois
## cruzamentos com comportamentos ensinados separadamente.
const FASE_14: Dictionary = {
    "id": "bairro_14",
    "version": 1,
    "name": "Olha a moto",
    "phase_index": 13,
    "distance_m": 420.0,
    "chunk_length_m": 28.0,
    "chunks": 15,
    "base_speed_mps": 6.8,
    "deadline_seconds": 73.0,
    "layout_seed": 114,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "moto_cross", "lane": 2, "at_m": 72.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 4.5, "lead_m": 12.3},
        {"kind": "hydrant", "lane": 2, "at_m": 100.0},
        {"kind": "cyclist", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 18.5},
        {"kind": "moto_cross", "lane": 0, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 4.5, "lead_m": 12.3},
        {"kind": "bench", "lane": 1, "at_m": 184.0},
        {"kind": "moto_cross", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 4.5, "lead_m": 12.3},
        {"kind": "cone", "lane": 2, "at_m": 296.0},
        {"kind": "moto_cross", "lane": 0, "at_m": 312.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 4.5, "lead_m": 12.3},
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

## Fase 15 — "Desvio de obra": combina andaime, buraco, poça e passagem
## dinâmica; nada novo. Pulo → trecho livre → deslize → escolha de corredor
## no cruzamento.
const FASE_15: Dictionary = {
    "id": "bairro_15",
    "version": 1,
    "name": "Desvio de obra",
    "phase_index": 14,
    "distance_m": 448.0,
    "chunk_length_m": 28.0,
    "chunks": 16,
    "base_speed_mps": 7.0,
    "deadline_seconds": 73.0,
    "layout_seed": 115,
    "scenery": CENARIO_TRES_CALCADAS,
    "patterns": [
        {"kind": "pothole", "lane": 1, "at_m": 44.0},
        {"kind": "scaffold", "lane": 1, "at_m": 100.0},
        {"kind": "puddle", "lane": 2, "at_m": 128.0},
        {"kind": "cyclist", "lane": 2, "at_m": 156.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 19.0},
        {"kind": "bench", "lane": 0, "at_m": 184.0},
        {"kind": "moto_cross", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 4.5, "lead_m": 12.7},
        {"kind": "cone", "lane": 1, "at_m": 240.0},
        {"kind": "scaffold", "lane": 1, "at_m": 296.0},
        {"kind": "cyclist", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 19.0},
        {"kind": "pothole", "lane": 1, "at_m": 312.0},
        {"kind": "puddle", "lane": 2, "at_m": 312.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 400.0},
        {"kind": "coin", "lane": 1, "at_m": 408.0},
        {"kind": "coin", "lane": 1, "at_m": 416.0},
    ],
}

## Fase 16 — "O caramelo da praça" (PLANO_50_FASES): cachorro prepara na
## borda e cruza uma passagem (2,5 m/s); pedestres e bancos. Clímax:
## cruzamento do cachorro seguido de desvio anunciado, sem perseguição.
const FASE_16: Dictionary = {
    "id": "bairro_16",
    "version": 1,
    "name": "O caramelo da praça",
    "phase_index": 15,
    "distance_m": 420.0,
    "chunk_length_m": 28.0,
    "chunks": 15,
    "base_speed_mps": 7.0,
    "deadline_seconds": 71.0,
    "layout_seed": 116,
    "scenery": CENARIO_AVENIDA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "dog_cross", "lane": 2, "at_m": 72.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 2.5, "lead_m": 22.8},
        {"kind": "bench", "lane": 2, "at_m": 100.0},
        {"kind": "crosser", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 44.0},
        {"kind": "dog_cross", "lane": 0, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 2.5, "lead_m": 22.8},
        {"kind": "cone", "lane": 1, "at_m": 184.0},
        {"kind": "bench", "lane": 0, "at_m": 212.0},
        {"kind": "dog_cross", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 2.5, "lead_m": 22.8},
        {"kind": "bench", "lane": 1, "at_m": 296.0},
        {"kind": "cone", "lane": 2, "at_m": 312.0},
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

## Fase 17 — "Entregas da avenida": van, caixas baixas e carrinhos;
## praticar leitura de volumes. Clímax: rota rápida com salto e rota
## simples com desvio.
const FASE_17: Dictionary = {
    "id": "bairro_17",
    "version": 1,
    "name": "Entregas da avenida",
    "phase_index": 16,
    "distance_m": 448.0,
    "chunk_length_m": 28.0,
    "chunks": 16,
    "base_speed_mps": 7.2,
    "deadline_seconds": 73.0,
    "layout_seed": 117,
    "scenery": CENARIO_AVENIDA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "crate", "lane": 1, "at_m": 72.0},
        {"kind": "van", "lane": 2, "at_m": 100.0},
        {"kind": "cart", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 59.0},
        {"kind": "crate", "lane": 0, "at_m": 156.0},
        {"kind": "van", "lane": 2, "at_m": 156.0},
        {"kind": "cone", "lane": 1, "at_m": 184.0},
        {"kind": "bench", "lane": 0, "at_m": 212.0},
        {"kind": "crate", "lane": 1, "at_m": 296.0},
        {"kind": "van", "lane": 2, "at_m": 296.0},
        {"kind": "crate", "lane": 0, "at_m": 312.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 400.0},
        {"kind": "coin", "lane": 1, "at_m": 408.0},
        {"kind": "coin", "lane": 1, "at_m": 416.0},
    ],
}

## Fase 18 — "Travessia do caminhão": caminhão/ônibus cruza a área sinalizada
## (faixa zebrada) a 2,0 m/s, saindo da rua; corredor de escape amplo.
## Clímax: o veículo ocupa o cruzamento e a passagem lateral segue válida.
const FASE_18: Dictionary = {
    "id": "bairro_18",
    "version": 1,
    "name": "Travessia do caminhão",
    "phase_index": 17,
    "distance_m": 448.0,
    "chunk_length_m": 28.0,
    "chunks": 16,
    "base_speed_mps": 7.2,
    "deadline_seconds": 73.0,
    "layout_seed": 118,
    "scenery": CENARIO_AVENIDA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "truck_cross", "lane": 0, "at_m": 72.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 17.1},
        {"kind": "hydrant", "lane": 2, "at_m": 100.0},
        {"kind": "bus_cross", "lane": 0, "at_m": 128.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 28.8},
        {"kind": "cone", "lane": 1, "at_m": 156.0},
        {"kind": "truck_cross", "lane": 0, "at_m": 184.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 17.1},
        {"kind": "cone", "lane": 2, "at_m": 184.0},
        {"kind": "bench", "lane": 0, "at_m": 212.0},
        {"kind": "bus_cross", "lane": 0, "at_m": 296.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 28.8},
        {"kind": "hydrant", "lane": 0, "at_m": 296.0},
        {"kind": "truck_cross", "lane": 0, "at_m": 312.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 17.1},
        {"kind": "bench", "lane": 1, "at_m": 312.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 400.0},
        {"kind": "coin", "lane": 1, "at_m": 408.0},
        {"kind": "coin", "lane": 1, "at_m": 416.0},
    ],
}

## Fase 19 — "Últimas quadras": combina pedestre, obra e entrega em ordem
## conhecida. Três decisões separadas; último respiro revela o ponto.
const FASE_19: Dictionary = {
    "id": "bairro_19",
    "version": 1,
    "name": "Últimas quadras",
    "phase_index": 18,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.4,
    "deadline_seconds": 74.0,
    "layout_seed": 119,
    "scenery": CENARIO_AVENIDA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "crosser", "lane": 0, "at_m": 72.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 47.0},
        {"kind": "scaffold", "lane": 1, "at_m": 100.0},
        {"kind": "cart", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 60.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "bench", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 1, "at_m": 240.0},
        {"kind": "crosser", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -3.25, "cross_mps": 1.3, "lead_m": 47.0},
        {"kind": "bench", "lane": 1, "at_m": 296.0},
        {"kind": "scaffold", "lane": 2, "at_m": 312.0},
        {"kind": "puddle", "lane": 1, "at_m": 312.0},
        {"kind": "cart", "lane": 0, "at_m": 328.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 60.0},
        {"kind": "cone", "lane": 0, "at_m": 328.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 20 — "Peguei o ônibus!": encerra a campanha inicial com famílias já
## dominadas; três pontos de fôlego. Revisão em três blocos com recuperação;
## embarque marcante (moedas douradas na aproximação), sem truque final.
const FASE_20: Dictionary = {
    "id": "bairro_20",
    "version": 1,
    "name": "Peguei o ônibus!",
    "phase_index": 19,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 7.5,
    "deadline_seconds": 76.0,
    "layout_seed": 120,
    "scenery": CENARIO_AVENIDA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "pothole", "lane": 2, "at_m": 100.0},
        {"kind": "barrier", "lane": 1, "at_m": 128.0},
        {"kind": "crosser", "lane": 0, "at_m": 184.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 48.0},
        {"kind": "cart", "lane": 2, "at_m": 212.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 61.0},
        {"kind": "cyclist", "lane": 2, "at_m": 240.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 20.5},
        {"kind": "moto_cross", "lane": 2, "at_m": 324.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 4.5, "lead_m": 13.6},
        {"kind": "cone", "lane": 2, "at_m": 324.0},
        {"kind": "truck_cross", "lane": 0, "at_m": 352.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 17.8},
        {"kind": "bench", "lane": 1, "at_m": 352.0},
        {"kind": "scaffold", "lane": 1, "at_m": 380.0},
        {"kind": "cone", "lane": 2, "at_m": 380.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 148.0},
        {"kind": "coin", "lane": 1, "at_m": 154.0},
        {"kind": "coin", "lane": 1, "at_m": 160.0},
        {"kind": "coin", "lane": 1, "at_m": 288.0},
        {"kind": "coin", "lane": 1, "at_m": 294.0},
        {"kind": "coin", "lane": 1, "at_m": 300.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 434.0},
        {"kind": "coin", "lane": 1, "at_m": 440.0},
        {"kind": "golden", "lane": 1, "at_m": 460.0},
        {"kind": "golden", "lane": 1, "at_m": 468.0},
        {"kind": "golden", "lane": 1, "at_m": 476.0},
    ],
}

## Fase 21 — "Rua das fachadas" (PLANO_50_FASES): reentrada tranquila no
## centro; bancos, floreiras e um pedestre por vez. Clímax: pedestre em E
## com banco em C, D livre.
const FASE_21: Dictionary = {
    "id": "bairro_21",
    "version": 1,
    "name": "Rua das fachadas",
    "phase_index": 20,
    "distance_m": 448.0,
    "chunk_length_m": 28.0,
    "chunks": 16,
    "base_speed_mps": 7.4,
    "deadline_seconds": 72.0,
    "layout_seed": 121,
    "scenery": CENARIO_CENTRO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "planter", "lane": 2, "at_m": 100.0},
        {"kind": "crosser", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 46.4},
        {"kind": "bench", "lane": 1, "at_m": 156.0},
        {"kind": "planter", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 2, "at_m": 212.0},
        {"kind": "crosser", "lane": 2, "at_m": 240.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 46.4},
        {"kind": "bench", "lane": 1, "at_m": 240.0},
        {"kind": "planter", "lane": 2, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
        {"kind": "bench", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 400.0},
        {"kind": "coin", "lane": 1, "at_m": 408.0},
        {"kind": "coin", "lane": 1, "at_m": 416.0},
    ],
}

## Fase 22 — "Entrega na livraria" (PLANO_50_FASES): caixas baixas e o
## carrinho entre vitrines; volumes baixos e altos em rota simples.
## Clímax: carrinho em D com caixa pulável em C, E livre.
const FASE_22: Dictionary = {
    "id": "bairro_22",
    "version": 1,
    "name": "Entrega na livraria",
    "phase_index": 21,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.5,
    "deadline_seconds": 74.0,
    "layout_seed": 122,
    "scenery": CENARIO_CENTRO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "crate", "lane": 1, "at_m": 72.0},
        {"kind": "cart", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 61.1},
        {"kind": "crate", "lane": 2, "at_m": 128.0},
        {"kind": "bench", "lane": 0, "at_m": 156.0},
        {"kind": "crate", "lane": 1, "at_m": 184.0},
        {"kind": "cone", "lane": 2, "at_m": 212.0},
        {"kind": "cart", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 61.1},
        {"kind": "crate", "lane": 1, "at_m": 240.0},
        {"kind": "crate", "lane": 0, "at_m": 296.0},
        {"kind": "bench", "lane": 2, "at_m": 324.0},
        {"kind": "cone", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 23 — "Foto na praça" (PLANO_50_FASES): dois pedestres em trajetórias
## separadas com espera visível; cruzamentos alternados, nunca simultâneos.
const FASE_23: Dictionary = {
    "id": "bairro_23",
    "version": 1,
    "name": "Foto na praça",
    "phase_index": 22,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.6,
    "deadline_seconds": 73.0,
    "layout_seed": 123,
    "scenery": CENARIO_CENTRO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "planter", "lane": 1, "at_m": 100.0},
        {"kind": "crosser", "lane": 0, "at_m": 128.0, "from_x": -4.9, "to_x": 3.25, "cross_mps": 1.3, "lead_m": 47.6},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "bench", "lane": 2, "at_m": 184.0},
        {"kind": "cone", "lane": 1, "at_m": 212.0},
        {"kind": "crosser", "lane": 2, "at_m": 240.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 47.6},
        {"kind": "planter", "lane": 1, "at_m": 268.0},
        {"kind": "bench", "lane": 2, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 24 — "Restauração da fachada" (PLANO_50_FASES): andaimes, vala curta
## e cone; deslize, respiro, salto e troca lateral, nessa ordem.
const FASE_24: Dictionary = {
    "id": "bairro_24",
    "version": 1,
    "name": "Restauração da fachada",
    "phase_index": 23,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 7.6,
    "deadline_seconds": 76.0,
    "layout_seed": 124,
    "scenery": CENARIO_CENTRO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "scaffold", "lane": 1, "at_m": 72.0},
        {"kind": "pothole", "lane": 2, "at_m": 128.0},
        {"kind": "cone", "lane": 1, "at_m": 156.0},
        {"kind": "bench", "lane": 0, "at_m": 184.0},
        {"kind": "scaffold", "lane": 0, "at_m": 212.0},
        {"kind": "cone", "lane": 2, "at_m": 212.0},
        {"kind": "pothole", "lane": 1, "at_m": 240.0},
        {"kind": "scaffold", "lane": 2, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 296.0},
        {"kind": "cone", "lane": 1, "at_m": 324.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 25 — "O ponto da igreja" (PLANO_50_FASES): revisão do centro com
## três padrões aprovados (P03/P05/P07/P08/P12); a igreja marca o ponto.
const FASE_25: Dictionary = {
    "id": "bairro_25",
    "version": 1,
    "name": "O ponto da igreja",
    "phase_index": 24,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 7.7,
    "deadline_seconds": 74.0,
    "layout_seed": 125,
    "scenery": CENARIO_LARGO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 2, "at_m": 44.0},
        {"kind": "crosser", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 29.0},
        {"kind": "planter", "lane": 0, "at_m": 128.0},
        {"kind": "scaffold", "lane": 1, "at_m": 156.0},
        {"kind": "bench", "lane": 2, "at_m": 184.0},
        {"kind": "cart", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 37.7},
        {"kind": "cone", "lane": 1, "at_m": 240.0},
        {"kind": "crate", "lane": 0, "at_m": 268.0},
        {"kind": "cone", "lane": 1, "at_m": 296.0},
        {"kind": "planter", "lane": 2, "at_m": 324.0},
        {"kind": "crosser", "lane": 2, "at_m": 352.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 48.3},
        {"kind": "bench", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 26 — "Abertura do mercado" (PLANO_50_FASES): reentrada tranquila
## no capítulo do Mercado; caixas puláveis e bancos sólidos entre barracas.
## Clímax: caixa em C com banco em D, E livre.
const FASE_26: Dictionary = {
    "id": "bairro_26",
    "version": 1,
    "name": "Abertura do mercado",
    "phase_index": 25,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.6,
    "deadline_seconds": 74.0,
    "layout_seed": 126,
    "scenery": CENARIO_FEIRA,
    "patterns": [
        {"kind": "crate", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "crate", "lane": 2, "at_m": 100.0},
        {"kind": "cone", "lane": 1, "at_m": 128.0},
        {"kind": "bench", "lane": 2, "at_m": 184.0},
        {"kind": "crate", "lane": 0, "at_m": 212.0},
        {"kind": "cone", "lane": 0, "at_m": 240.0},
        {"kind": "bench", "lane": 1, "at_m": 296.0},
        {"kind": "crate", "lane": 2, "at_m": 324.0},
        {"kind": "cone", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 27 — "Corredor de entregas" (PLANO_50_FASES): carrinhos em intervalos
## regulares (112 m), sentidos alternados; caixas e bancos como revisão.
## Clímax: carrinho E→D com caixa pulável em D, C livre.
const FASE_27: Dictionary = {
    "id": "bairro_27",
    "version": 1,
    "name": "Corredor de entregas",
    "phase_index": 26,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 7.7,
    "deadline_seconds": 76.0,
    "layout_seed": 127,
    "scenery": CENARIO_FEIRA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "crate", "lane": 0, "at_m": 72.0},
        {"kind": "cart", "lane": 2, "at_m": 140.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 60.4},
        {"kind": "cone", "lane": 2, "at_m": 168.0},
        {"kind": "bench", "lane": 1, "at_m": 196.0},
        {"kind": "cart", "lane": 0, "at_m": 252.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 60.4},
        {"kind": "crate", "lane": 2, "at_m": 280.0},
        {"kind": "cone", "lane": 0, "at_m": 308.0},
        {"kind": "bench", "lane": 2, "at_m": 336.0},
        {"kind": "crate", "lane": 1, "at_m": 364.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 28 — "Toldos da feira" (PLANO_50_FASES): barreiras altas (toldos) e
## caixas puláveis; deslize e salto alternados, sem travessia.
## Clímax: barreira em C com caixa em D, E livre.
const FASE_28: Dictionary = {
    "id": "bairro_28",
    "version": 1,
    "name": "Toldos da feira",
    "phase_index": 27,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 7.8,
    "deadline_seconds": 75.0,
    "layout_seed": 128,
    "scenery": CENARIO_FEIRA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "barrier", "lane": 2, "at_m": 72.0},
        {"kind": "crate", "lane": 0, "at_m": 100.0},
        {"kind": "barrier", "lane": 1, "at_m": 128.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "crate", "lane": 1, "at_m": 184.0},
        {"kind": "barrier", "lane": 0, "at_m": 212.0},
        {"kind": "bench", "lane": 2, "at_m": 240.0},
        {"kind": "crate", "lane": 0, "at_m": 268.0},
        {"kind": "barrier", "lane": 1, "at_m": 296.0},
        {"kind": "cone", "lane": 2, "at_m": 324.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 29 — "A esquina do mercado" (PLANO_50_FASES): van parada, pedestres e
## carrinhos num cruzamento; travessias separadas, nunca simultâneas.
## Clímax: van em D com pedestre D→E, C livre.
const FASE_29: Dictionary = {
    "id": "bairro_29",
    "version": 1,
    "name": "A esquina do mercado",
    "phase_index": 28,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 7.8,
    "deadline_seconds": 78.0,
    "layout_seed": 129,
    "scenery": CENARIO_FEIRA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "trash", "lane": 2, "at_m": 72.0},
        {"kind": "van", "lane": 0, "at_m": 100.0},
        {"kind": "cart", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 62.3},
        {"kind": "crosser", "lane": 1, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 48.9},
        {"kind": "bench", "lane": 0, "at_m": 184.0},
        {"kind": "van", "lane": 2, "at_m": 212.0},
        {"kind": "crosser", "lane": 2, "at_m": 212.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 29.0},
        {"kind": "crate", "lane": 0, "at_m": 240.0},
        {"kind": "cone", "lane": 1, "at_m": 268.0},
        {"kind": "cart", "lane": 0, "at_m": 296.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 37.7},
        {"kind": "cone", "lane": 2, "at_m": 324.0},
        {"kind": "crosser", "lane": 0, "at_m": 352.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 48.9},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 30 — "Fechou a feira" (PLANO_50_FASES): revisão do capítulo sem fechar
## a visão; respiro antes do ônibus (sem moeda dourada: não é final).
## Clímax: ciclista E→D com cone em D, C livre.
const FASE_30: Dictionary = {
    "id": "bairro_30",
    "version": 1,
    "name": "Fechou a feira",
    "phase_index": 29,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 8.0,
    "deadline_seconds": 75.0,
    "layout_seed": 130,
    "scenery": CENARIO_FEIRA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "barrier", "lane": 2, "at_m": 72.0},
        {"kind": "crate", "lane": 0, "at_m": 100.0},
        {"kind": "bench", "lane": 1, "at_m": 128.0},
        {"kind": "cart", "lane": 2, "at_m": 156.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 63.6},
        {"kind": "crosser", "lane": 0, "at_m": 184.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 50.2},
        {"kind": "van", "lane": 1, "at_m": 212.0},
        {"kind": "cone", "lane": 2, "at_m": 240.0},
        {"kind": "bench", "lane": 0, "at_m": 268.0},
        {"kind": "cyclist", "lane": 1, "at_m": 296.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 21.3},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 31 — "Alamedas do parque" (PLANO_50_FASES): início de capítulo
## com menor pressão; bancos, floreiras e cones entre palmeiras.
## Clímax: floreira em C com banco em D, E livre.
const FASE_31: Dictionary = {
    "id": "bairro_31",
    "version": 1,
    "name": "Alamedas do parque",
    "phase_index": 30,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.8,
    "deadline_seconds": 73.0,
    "layout_seed": 131,
    "scenery": CENARIO_PARQUE,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "planter", "lane": 2, "at_m": 100.0},
        {"kind": "cone", "lane": 2, "at_m": 128.0},
        {"kind": "bench", "lane": 1, "at_m": 156.0},
        {"kind": "planter", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 0, "at_m": 212.0},
        {"kind": "bench", "lane": 2, "at_m": 240.0},
        {"kind": "planter", "lane": 1, "at_m": 268.0},
        {"kind": "cone", "lane": 2, "at_m": 296.0},
        {"kind": "bench", "lane": 0, "at_m": 324.0},
        {"kind": "planter", "lane": 2, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 32 — "Passeio com o caramelo" (PLANO_50_FASES): cachorro e pedestres
## cruzam em eventos separados (56 m entre eles), com estáticos conhecidos.
## Clímax: pedestre em C com floreira em D, E livre.
const FASE_32: Dictionary = {
    "id": "bairro_32",
    "version": 1,
    "name": "Passeio com o caramelo",
    "phase_index": 31,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 8.0,
    "deadline_seconds": 73.0,
    "layout_seed": 132,
    "scenery": CENARIO_PARQUE,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "dog_cross", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 2.5, "lead_m": 26.1},
        {"kind": "planter", "lane": 1, "at_m": 128.0},
        {"kind": "crosser", "lane": 0, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 50.2},
        {"kind": "cone", "lane": 2, "at_m": 184.0},
        {"kind": "dog_cross", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 2.5, "lead_m": 26.1},
        {"kind": "bench", "lane": 1, "at_m": 240.0},
        {"kind": "crosser", "lane": 1, "at_m": 268.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 30.8},
        {"kind": "planter", "lane": 2, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
        {"kind": "bench", "lane": 2, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 33 — "Ciclistas da orla" (PLANO_50_FASES): dois ciclistas em momentos
## diferentes (112 m entre eles), janelas previsíveis, escape lateral livre.
## Clímax: ciclista em E com cone em D, C livre.
const FASE_33: Dictionary = {
    "id": "bairro_33",
    "version": 1,
    "name": "Ciclistas da orla",
    "phase_index": 32,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 8.0,
    "deadline_seconds": 73.0,
    "layout_seed": 133,
    "scenery": CENARIO_PARQUE,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "planter", "lane": 0, "at_m": 72.0},
        {"kind": "bench", "lane": 2, "at_m": 100.0},
        {"kind": "cyclist", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 21.7},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "planter", "lane": 1, "at_m": 184.0},
        {"kind": "bench", "lane": 0, "at_m": 212.0},
        {"kind": "cyclist", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 21.7},
        {"kind": "cone", "lane": 2, "at_m": 268.0},
        {"kind": "planter", "lane": 2, "at_m": 296.0},
        {"kind": "bench", "lane": 1, "at_m": 324.0},
        {"kind": "cone", "lane": 0, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 34 — "Manutenção do calçadão" (PLANO_50_FASES): vala, barra e cone;
## pulo e deslize combinados, com rota alternativa de moedas em D.
## Clímax: barreira em C com a rota D livre e premiada.
const FASE_34: Dictionary = {
    "id": "bairro_34",
    "version": 1,
    "name": "Manutenção do calçadão",
    "phase_index": 33,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 8.1,
    "deadline_seconds": 75.0,
    "layout_seed": 134,
    "scenery": CENARIO_PARQUE,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "pothole", "lane": 0, "at_m": 72.0},
        {"kind": "barrier", "lane": 2, "at_m": 100.0},
        {"kind": "cone", "lane": 2, "at_m": 128.0},
        {"kind": "pothole", "lane": 1, "at_m": 156.0},
        {"kind": "barrier", "lane": 0, "at_m": 184.0},
        {"kind": "cone", "lane": 0, "at_m": 212.0},
        {"kind": "barrier", "lane": 1, "at_m": 240.0},
        {"kind": "pothole", "lane": 2, "at_m": 268.0},
        {"kind": "cone", "lane": 1, "at_m": 296.0},
        {"kind": "barrier", "lane": 2, "at_m": 324.0},
        {"kind": "pothole", "lane": 0, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 2, "at_m": 232.0},
        {"kind": "coin", "lane": 2, "at_m": 240.0},
        {"kind": "coin", "lane": 2, "at_m": 248.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 35 — "O ônibus da orla" (PLANO_50_FASES): revisão de parque, ciclovia
## e manutenção em três blocos; aproximação limpa com a guarita no ponto.
## Clímax: barreira em C com cone em D, E livre, ônibus à vista.
const FASE_35: Dictionary = {
    "id": "bairro_35",
    "version": 1,
    "name": "O ônibus da orla",
    "phase_index": 34,
    "distance_m": 560.0,
    "chunk_length_m": 28.0,
    "chunks": 20,
    "base_speed_mps": 8.2,
    "deadline_seconds": 77.0,
    "layout_seed": 135,
    "scenery": CENARIO_ORLA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "planter", "lane": 2, "at_m": 100.0},
        {"kind": "cyclist", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 3.0, "lead_m": 22.3},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "pothole", "lane": 1, "at_m": 184.0},
        {"kind": "barrier", "lane": 2, "at_m": 212.0},
        {"kind": "crosser", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 51.4},
        {"kind": "bench", "lane": 1, "at_m": 268.0},
        {"kind": "dog_cross", "lane": 2, "at_m": 296.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 2.5, "lead_m": 26.7},
        {"kind": "planter", "lane": 0, "at_m": 324.0},
        {"kind": "barrier", "lane": 1, "at_m": 352.0},
        {"kind": "cone", "lane": 2, "at_m": 380.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 512.0},
        {"kind": "coin", "lane": 1, "at_m": 520.0},
        {"kind": "coin", "lane": 1, "at_m": 528.0},
    ],
}

## ETAPA 15 — centro movimentado do lote 41-45: mesmo deck dos três
## corredores, árvores esparsas, bancos espaçados, lixeiras e postes de
## avenida, lojas dominando com prédios altos (3-5 pisos); tempo seco
## fixo (volta da chuva); multidão de fundo nas calçadas (bloco
## "multidao", lido por _rebuild_multidao) e outdoors dos dois lados a
## cada 140 m, pulando os que caem sobre travessias (bloco "outdoors",
## lido por _spawn_outdoors) — visual puro, sem colisão.
const CENARIO_CENTRO_MOV: Dictionary = {
    "faixas": {"piso_central_m": 9.9, "piso_borda_esq_m": 4.95},
    "props": {
        "arvore": {"glb": "arvore", "espacamento_m": 24.0},
        "banco": {"espacamento_m": 18.0},
        "lixeira": {"espacamento_m": 12.0},
        "poste": {"espacamento_m": 14.0},
    },
    "predios": {
        "tipo_pesos": {"tijolo": 2, "reboco": 2, "loja": 5, "obra": 1},
        "pisos": [3, 5],
    },
    "clima": "limpo",
    "multidao": {"quantidade": 12, "x_min_m": 6.5, "x_max_m": 7.4},
    "outdoors": {"passo_m": 140.0, "x_m": 7.0, "margem_cruzamento_m": 6.0},
}

## Fase 36 — "Chuva passageira" (PLANO_50_FASES): clima novo com desafios
## fáceis; poças e cones, reaprender a leitura sem elevar a velocidade.
## Clímax: poça em C com cone em D, E livre e seco.
const FASE_36: Dictionary = {
    "id": "bairro_36",
    "version": 1,
    "name": "Chuva passageira",
    "phase_index": 35,
    "distance_m": 476.0,
    "chunk_length_m": 28.0,
    "chunks": 17,
    "base_speed_mps": 7.8,
    "deadline_seconds": 74.0,
    "layout_seed": 136,
    "scenery": CENARIO_CHUVA,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "puddle", "lane": 0, "at_m": 72.0},
        {"kind": "cone", "lane": 2, "at_m": 100.0},
        {"kind": "puddle", "lane": 2, "at_m": 128.0},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "puddle", "lane": 1, "at_m": 184.0},
        {"kind": "cone", "lane": 1, "at_m": 212.0},
        {"kind": "puddle", "lane": 0, "at_m": 240.0},
        {"kind": "cone", "lane": 2, "at_m": 268.0},
        {"kind": "cone", "lane": 0, "at_m": 296.0},
        {"kind": "puddle", "lane": 2, "at_m": 324.0},
        {"kind": "cone", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 428.0},
        {"kind": "coin", "lane": 1, "at_m": 436.0},
        {"kind": "coin", "lane": 1, "at_m": 444.0},
    ],
}

## Fase 37 — "Procurando piso seco" (PLANO_50_FASES): a poça em C cobra o
## pulo na rota de recompensa (moedas sobre ela); E e D seguem secos.
## Clímax: rota de recompensa (pulo com moedas) versus rota de conclusão.
const FASE_37: Dictionary = {
    "id": "bairro_37",
    "version": 1,
    "name": "Procurando piso seco",
    "phase_index": 36,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 8.0,
    "deadline_seconds": 74.0,
    "layout_seed": 137,
    "scenery": CENARIO_CHUVA_CICLO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "puddle", "lane": 2, "at_m": 72.0},
        {"kind": "bench", "lane": 0, "at_m": 100.0},
        {"kind": "puddle", "lane": 1, "at_m": 128.0},
        {"kind": "cone", "lane": 0, "at_m": 156.0},
        {"kind": "puddle", "lane": 0, "at_m": 184.0},
        {"kind": "bench", "lane": 2, "at_m": 212.0},
        {"kind": "puddle", "lane": 1, "at_m": 240.0},
        {"kind": "cone", "lane": 2, "at_m": 268.0},
        {"kind": "puddle", "lane": 2, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
        {"kind": "bench", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 120.0},
        {"kind": "coin", "lane": 1, "at_m": 128.0},
        {"kind": "coin", "lane": 1, "at_m": 136.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 38 — "Entrega debaixo d'água" (PLANO_50_FASES): carrinhos e pedestres
## com aviso reforçado; cada evento dinâmico seguido de solo seguro.
## Clímax: pedestre em C com cone em E, D livre.
const FASE_38: Dictionary = {
    "id": "bairro_38",
    "version": 1,
    "name": "Entrega debaixo d'água",
    "phase_index": 37,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 8.1,
    "deadline_seconds": 76.0,
    "layout_seed": 138,
    "scenery": CENARIO_CHUVA_CICLO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "puddle", "lane": 0, "at_m": 72.0},
        {"kind": "cart", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 66.0},
        {"kind": "cone", "lane": 2, "at_m": 128.0},
        {"kind": "crosser", "lane": 0, "at_m": 156.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 50.8},
        {"kind": "puddle", "lane": 1, "at_m": 184.0},
        {"kind": "cart", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.0, "lead_m": 66.0},
        {"kind": "bench", "lane": 2, "at_m": 240.0},
        {"kind": "crosser", "lane": 1, "at_m": 268.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 30.5},
        {"kind": "cone", "lane": 0, "at_m": 296.0},
        {"kind": "puddle", "lane": 2, "at_m": 324.0},
        {"kind": "bench", "lane": 1, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 39 — "Obra molhada" (PLANO_50_FASES): buraco, barra e poças longe das
## aterrissagens obrigatórias (poça nunca a <28 m do buraco no corredor).
## Clímax: barreira em D fechando a obra, C e E livres.
const FASE_39: Dictionary = {
    "id": "bairro_39",
    "version": 1,
    "name": "Obra molhada",
    "phase_index": 38,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 8.2,
    "deadline_seconds": 74.0,
    "layout_seed": 139,
    "scenery": CENARIO_CHUVA_CICLO,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "pothole", "lane": 0, "at_m": 72.0},
        {"kind": "barrier", "lane": 2, "at_m": 100.0},
        {"kind": "puddle", "lane": 2, "at_m": 128.0},
        {"kind": "pothole", "lane": 1, "at_m": 156.0},
        {"kind": "barrier", "lane": 0, "at_m": 184.0},
        {"kind": "puddle", "lane": 1, "at_m": 212.0},
        {"kind": "pothole", "lane": 2, "at_m": 240.0},
        {"kind": "barrier", "lane": 1, "at_m": 268.0},
        {"kind": "puddle", "lane": 0, "at_m": 296.0},
        {"kind": "cone", "lane": 0, "at_m": 324.0},
        {"kind": "barrier", "lane": 2, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 40 — "O sol voltou" (PLANO_50_FASES): revisão com o clima clareando;
## último trecho firme com sequência conhecida e ônibus ao sol.
## Clímax: barreira em C com cone em D, E livre, ônibus à vista.
const FASE_40: Dictionary = {
    "id": "bairro_40",
    "version": 1,
    "name": "O sol voltou",
    "phase_index": 39,
    "distance_m": 560.0,
    "chunk_length_m": 28.0,
    "chunks": 20,
    "base_speed_mps": 8.3,
    "deadline_seconds": 76.0,
    "layout_seed": 140,
    "scenery": CENARIO_SOL,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "puddle", "lane": 0, "at_m": 72.0},
        {"kind": "crosser", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 52.0},
        {"kind": "bench", "lane": 1, "at_m": 128.0},
        {"kind": "pothole", "lane": 2, "at_m": 156.0},
        {"kind": "barrier", "lane": 0, "at_m": 184.0},
        {"kind": "cyclist", "lane": 0, "at_m": 212.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 22.5},
        {"kind": "puddle", "lane": 1, "at_m": 240.0},
        {"kind": "cone", "lane": 2, "at_m": 268.0},
        {"kind": "crosser", "lane": 0, "at_m": 296.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 52.0},
        {"kind": "bench", "lane": 2, "at_m": 324.0},
        {"kind": "barrier", "lane": 1, "at_m": 352.0},
        {"kind": "cone", "lane": 0, "at_m": 380.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 512.0},
        {"kind": "coin", "lane": 1, "at_m": 520.0},
        {"kind": "coin", "lane": 1, "at_m": 528.0},
    ],
}

## Fase 41 — "A saída do escritório" (PLANO_50_FASES): pedestres,
## floreiras e bancos em dois grupos de decisões a 140 m um do outro,
## de volta ao tempo seco. Clímax: pedestre em E com floreira em C, D livre.
const FASE_41: Dictionary = {
    "id": "bairro_41",
    "version": 1,
    "name": "A saída do escritório",
    "phase_index": 40,
    "distance_m": 504.0,
    "chunk_length_m": 28.0,
    "chunks": 18,
    "base_speed_mps": 8.2,
    "deadline_seconds": 72.0,
    "layout_seed": 141,
    "scenery": CENARIO_CENTRO_MOV,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "crosser", "lane": 2, "at_m": 100.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.3, "lead_m": 51.4},
        {"kind": "bench", "lane": 1, "at_m": 100.0},
        {"kind": "planter", "lane": 0, "at_m": 128.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "cone", "lane": 0, "at_m": 184.0},
        {"kind": "bench", "lane": 2, "at_m": 212.0},
        {"kind": "crosser", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 51.4},
        {"kind": "planter", "lane": 1, "at_m": 240.0},
        {"kind": "cone", "lane": 1, "at_m": 268.0},
        {"kind": "bench", "lane": 0, "at_m": 296.0},
        {"kind": "cone", "lane": 2, "at_m": 324.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 456.0},
        {"kind": "coin", "lane": 1, "at_m": 464.0},
        {"kind": "coin", "lane": 1, "at_m": 472.0},
    ],
}

## Fase 42 — "Avenida das entregas" (PLANO_50_FASES): van, caixas e carrinho;
## moedas sobre as caixas de C premiam a rota técnica (pulo), E/D simples.
## Clímax: van em C com rotas E e D livres e anunciadas.
const FASE_42: Dictionary = {
    "id": "bairro_42",
    "version": 1,
    "name": "Avenida das entregas",
    "phase_index": 41,
    "distance_m": 532.0,
    "chunk_length_m": 28.0,
    "chunks": 19,
    "base_speed_mps": 8.3,
    "deadline_seconds": 74.0,
    "layout_seed": 142,
    "scenery": CENARIO_CENTRO_MOV,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "crate", "lane": 0, "at_m": 72.0},
        {"kind": "crate", "lane": 1, "at_m": 100.0},
        {"kind": "van", "lane": 2, "at_m": 128.0},
        {"kind": "cart", "lane": 2, "at_m": 156.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 67.6},
        {"kind": "crate", "lane": 2, "at_m": 184.0},
        {"kind": "van", "lane": 0, "at_m": 212.0},
        {"kind": "crate", "lane": 0, "at_m": 240.0},
        {"kind": "bench", "lane": 1, "at_m": 268.0},
        {"kind": "crate", "lane": 1, "at_m": 296.0},
        {"kind": "van", "lane": 1, "at_m": 324.0},
        {"kind": "cone", "lane": 2, "at_m": 352.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 92.0},
        {"kind": "coin", "lane": 1, "at_m": 100.0},
        {"kind": "coin", "lane": 1, "at_m": 108.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 484.0},
        {"kind": "coin", "lane": 1, "at_m": 492.0},
        {"kind": "coin", "lane": 1, "at_m": 500.0},
    ],
}

## Fase 43 — "Sinal aberto" (PLANO_50_FASES): moto, ciclista e ônibus em
## cruzamentos separados a 112 m; três leituras, nunca simultâneas.
## Clímax: ônibus cruza com o nariz em C, D livre e sinalizada.
const FASE_43: Dictionary = {
    "id": "bairro_43",
    "version": 1,
    "name": "Sinal aberto",
    "phase_index": 42,
    "distance_m": 560.0,
    "chunk_length_m": 28.0,
    "chunks": 20,
    "base_speed_mps": 8.4,
    "deadline_seconds": 76.0,
    "layout_seed": 143,
    "scenery": CENARIO_CENTRO_MOV,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "bench", "lane": 0, "at_m": 72.0},
        {"kind": "moto_cross", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 4.5, "lead_m": 15.2},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "planter", "lane": 1, "at_m": 184.0},
        {"kind": "cyclist", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 3.0, "lead_m": 22.8},
        {"kind": "bench", "lane": 2, "at_m": 268.0},
        {"kind": "cone", "lane": 0, "at_m": 296.0},
        {"kind": "bus_cross", "lane": 0, "at_m": 352.0, "from_x": -8.0, "to_x": 8.0, "cross_mps": 2.0, "lead_m": 33.6},
        {"kind": "planter", "lane": 2, "at_m": 380.0},
        {"kind": "cone", "lane": 1, "at_m": 408.0},
        {"kind": "bench", "lane": 0, "at_m": 436.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 512.0},
        {"kind": "coin", "lane": 1, "at_m": 520.0},
        {"kind": "coin", "lane": 1, "at_m": 528.0},
    ],
}

## Fase 44 — "Quadra em reforma" (PLANO_50_FASES): andaime, buraco e hidrante
## em padrão longo com respiros; saída ampla com o último cone em C.
## Clímax: hidrante em E com cone em C na saída, D livre.
const FASE_44: Dictionary = {
    "id": "bairro_44",
    "version": 1,
    "name": "Quadra em reforma",
    "phase_index": 43,
    "distance_m": 560.0,
    "chunk_length_m": 28.0,
    "chunks": 20,
    "base_speed_mps": 8.5,
    "deadline_seconds": 74.0,
    "layout_seed": 144,
    "scenery": CENARIO_CENTRO_MOV,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "scaffold", "lane": 2, "at_m": 72.0},
        {"kind": "pothole", "lane": 0, "at_m": 100.0},
        {"kind": "hydrant", "lane": 1, "at_m": 128.0},
        {"kind": "cone", "lane": 2, "at_m": 156.0},
        {"kind": "scaffold", "lane": 0, "at_m": 184.0},
        {"kind": "pothole", "lane": 1, "at_m": 212.0},
        {"kind": "hydrant", "lane": 2, "at_m": 240.0},
        {"kind": "cone", "lane": 0, "at_m": 268.0},
        {"kind": "scaffold", "lane": 1, "at_m": 296.0},
        {"kind": "pothole", "lane": 2, "at_m": 324.0},
        {"kind": "hydrant", "lane": 0, "at_m": 352.0},
        {"kind": "cone", "lane": 1, "at_m": 380.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 512.0},
        {"kind": "coin", "lane": 1, "at_m": 520.0},
        {"kind": "coin", "lane": 1, "at_m": 528.0},
    ],
}

## Fase 45 — "Hora do pico" (PLANO_50_FASES): revisão do centro com obra e
## travessias em sequência anunciada; caminho limpo até o ponto.
## Clímax: hidrante em C com cone em D, E livre, ponto à vista.
const FASE_45: Dictionary = {
    "id": "bairro_45",
    "version": 1,
    "name": "Hora do pico",
    "phase_index": 44,
    "distance_m": 588.0,
    "chunk_length_m": 28.0,
    "chunks": 21,
    "base_speed_mps": 8.6,
    "deadline_seconds": 76.0,
    "layout_seed": 145,
    "scenery": CENARIO_CENTRO_MOV,
    "patterns": [
        {"kind": "cone", "lane": 1, "at_m": 44.0},
        {"kind": "hydrant", "lane": 0, "at_m": 72.0},
        {"kind": "cart", "lane": 2, "at_m": 128.0, "from_x": 4.9, "to_x": -5.5, "cross_mps": 1.0, "lead_m": 70.1},
        {"kind": "scaffold", "lane": 1, "at_m": 156.0},
        {"kind": "pothole", "lane": 2, "at_m": 184.0},
        {"kind": "crosser", "lane": 0, "at_m": 240.0, "from_x": -4.9, "to_x": 5.5, "cross_mps": 1.3, "lead_m": 53.9},
        {"kind": "van", "lane": 2, "at_m": 268.0},
        {"kind": "bench", "lane": 0, "at_m": 296.0},
        {"kind": "scaffold", "lane": 0, "at_m": 324.0},
        {"kind": "pothole", "lane": 1, "at_m": 352.0},
        {"kind": "cone", "lane": 2, "at_m": 380.0},
        {"kind": "hydrant", "lane": 1, "at_m": 408.0},
    ],
    "coins": [
        {"kind": "coin", "lane": 1, "at_m": 8.0},
        {"kind": "coin", "lane": 1, "at_m": 14.0},
        {"kind": "coin", "lane": 1, "at_m": 20.0},
        {"kind": "coin", "lane": 1, "at_m": 260.0},
        {"kind": "coin", "lane": 1, "at_m": 266.0},
        {"kind": "coin", "lane": 1, "at_m": 272.0},
        {"kind": "coin", "lane": 1, "at_m": 540.0},
        {"kind": "coin", "lane": 1, "at_m": 548.0},
        {"kind": "coin", "lane": 1, "at_m": 556.0},
    ],
}

const LEVELS: Array = [FASE_1, FASE_2, PILOT, FASE_4, FASE_5, FASE_6, FASE_7, FASE_8, FASE_9, FASE_10, FASE_11, FASE_12, FASE_13, FASE_14, FASE_15, FASE_16, FASE_17, FASE_18, FASE_19, FASE_20, FASE_21, FASE_22, FASE_23, FASE_24, FASE_25, FASE_26, FASE_27, FASE_28, FASE_29, FASE_30, FASE_31, FASE_32, FASE_33, FASE_34, FASE_35, FASE_36, FASE_37, FASE_38, FASE_39, FASE_40, FASE_41, FASE_42, FASE_43, FASE_44, FASE_45]


static func for_phase(index: int) -> Dictionary:
    for level in LEVELS:
        if int(level.get("phase_index", -1)) == index:
            return level
    return {}


static func has_level(index: int) -> bool:
    return not for_phase(index).is_empty()
