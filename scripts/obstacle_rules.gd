class_name ObstacleRules
extends RefCounted
## ETAPA 2 — regras autoritativas de resolução ação x obstáculo.
## Blueprint §4 (regras de erro) e §6 (biblioteca de obstáculos):
## cada família tem classe de altura/volume e ações válidas próprias.
##
## Classes:
##   LOW         silhueta baixa (cone): pulo resolve; deslize não.
##   GROUND      buraco/vala curta: pulo resolve.
##   FULL        volume sólido (banco, hidrante, orelhão, bicicleta,
##               lixeira, carrinho de entrega): só trocar de corredor
##               resolve; deslize não resolve.
##   VEHICLE     carro/caminhão/ônibus/moto/van parada: só trocar de
##               corredor; pulo não atravessa ônibus ou caminhão.
##   SOFT        pessoas e animais (inclui pedestre em travessia):
##               sem dano; esbarrão/tropeço com lentidão.
##   SLIDE_UNDER barra suspensa com vão inferior: só deslize resolve
##               (reservada para os IDs futuros de obra/toldo do §6).

enum Classe { LOW, GROUND, FULL, VEHICLE, SOFT, SLIDE_UNDER }

const CLASSES: Dictionary = {
    "cone": Classe.LOW,
    "pothole": Classe.GROUND,
    "bench": Classe.FULL,
    "hydrant": Classe.FULL,
    "payphone": Classe.FULL,
    "bicycle": Classe.FULL,
    "old_lady": Classe.SOFT,
    "vendor": Classe.SOFT,
    "dog": Classe.SOFT,
    "car": Classe.VEHICLE,
    "truck": Classe.VEHICLE,
    "bus_traffic": Classe.VEHICLE,
    "motorcycle": Classe.VEHICLE,
    "barrier": Classe.SLIDE_UNDER,
    # ETAPA 8 — lote 6-10 (blueprint S6): lixeira (FULL), pedestre em
    # travessia (SOFT), carrinho de entrega (FULL) e van parada (VEHICLE).
    "trash": Classe.FULL,
    "crosser": Classe.SOFT,
    "cart": Classe.FULL,
    "van": Classe.VEHICLE,
}

## Limite lateral de colisão (m): meia largura da personagem + meia do
## obstáculo. Corredores ficam a 3,25 m, então valores < 1,62 nunca
## pegam a personagem num corredor vizinho.
const HIT_WIDTHS: Dictionary = {
    "cone": 1.0,
    "pothole": 1.2,
    "bench": 1.3,
    "hydrant": 1.0,
    "payphone": 1.0,
    "bicycle": 1.1,
    "old_lady": 0.9,
    "vendor": 0.9,
    "dog": 0.9,
    "car": 1.3,
    "truck": 1.4,
    "bus_traffic": 1.4,
    "motorcycle": 1.0,
    "barrier": 1.3,
    "trash": 0.8,
    "crosser": 0.9,
    "cart": 1.3,
    "van": 1.3,
}

const DEFAULT_WIDTH := 1.2


static func classe_for(kind: String) -> int:
    return int(CLASSES.get(kind, Classe.FULL))


static func hit_width(kind: String) -> float:
    return float(HIT_WIDTHS.get(kind, DEFAULT_WIDTH))


## O pulo livra a personagem desta classe?
static func jump_clears(classe: int) -> bool:
    return classe == Classe.LOW or classe == Classe.GROUND or classe == Classe.SOFT


## O deslize livra a personagem desta classe?
static func slide_clears(classe: int) -> bool:
    return classe == Classe.SLIDE_UNDER


## Colisão sem dano (esbarrão/tropeço)?
static func is_soft(classe: int) -> bool:
    return classe == Classe.SOFT
