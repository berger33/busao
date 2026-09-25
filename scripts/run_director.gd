class_name RunDirector
extends RefCounted
## Diretor da corrida — máquina de estados, relógio e regra do prazo.
## Extraído de game_3d.gd (ETAPA 1 do plano de execução Corre pro Ponto).
##
## Estados: preparo -> contagem -> corrida -> aproximação -> embarque -> resultado
## Regra autoritativa: sucesso quando a personagem cruza a zona de embarque
## com tempo efetivo (consumido + penalidades) <= prazo. O prazo conta a partir
## do fim da contagem de largada; pausas suspendem o relógio (o jogo não chama
## update() pausado); cada impacto válido acrescenta penalidade visível.

enum State { PREPARO, CONTAGEM, CORRIDA, APROXIMACAO, EMBARQUE, RESULTADO }

const COUNTDOWN_SECONDS := 2.4      # 3-2-1 curto (0,8 s cada)
const APPROACH_DISTANCE_M := 90.0   # ponto e ônibus ficam visíveis
const APPROACH_NEAR_M := 45.0       # aviso de reta final
const BOARDING_ZONE_M := 28.0       # último trecho amplo, sem novidade

var state: int = State.PREPARO
var run_total := 0.0
var base_speed := 5.0
var deadline := 60.0                # segundos após o fim da contagem (+ bônus)
var countdown_left := 0.0
var time_used := 0.0                # tempo efetivo: corrida + penalidades
var penalty_total := 0.0
var finished := false
var success := false
var fail_reason := ""               # "atraso" | "folego"
var shortfall_m := 0.0              # metros que faltavam quando o ônibus partiu
var shortfall_s := 0.0              # segundos que faltavam (blueprint S5: informar os dois)
var _near_announced := false


func setup(p_run_total: float, p_base_speed: float, p_deadline: float, p_bonus: float = 0.0) -> void:
    run_total = p_run_total
    base_speed = p_base_speed
    deadline = p_deadline + p_bonus  # bônus de personagem (normalizar em M5)
    state = State.PREPARO
    countdown_left = 0.0
    time_used = 0.0
    penalty_total = 0.0
    finished = false
    success = false
    fail_reason = ""
    shortfall_m = 0.0
    shortfall_s = 0.0
    _near_announced = false


func begin_countdown() -> void:
    state = State.CONTAGEM
    countdown_left = COUNTDOWN_SECONDS


func time_left() -> float:
    return deadline - time_used


func in_time() -> bool:
    return time_used <= deadline


## Chamado a cada frame com dt já filtrado (pausa não chama).
## Eventos: "countdown_done", "approach", "approach_near", "deadline".
func update(dt: float, distance: float) -> Array:
    var events: Array = []
    if finished:
        return events
    match state:
        State.CONTAGEM:
            countdown_left -= dt
            if countdown_left <= 0.0:
                countdown_left = 0.0
                state = State.CORRIDA
                events.append("countdown_done")
        State.CORRIDA, State.APROXIMACAO:
            time_used += dt
            var remaining: float = maxf(0.0, run_total - distance)
            if state == State.CORRIDA and remaining <= APPROACH_DISTANCE_M:
                state = State.APROXIMACAO
                events.append("approach")
            if state == State.APROXIMACAO and not _near_announced and remaining <= APPROACH_NEAR_M:
                _near_announced = true
                events.append("approach_near")
            if time_used >= deadline:
                finished = true
                success = false
                fail_reason = "atraso"
                shortfall_m = remaining
                # Segundos estimados na velocidade base do percurso.
                shortfall_s = remaining / maxf(base_speed, 0.01)
                events.append("deadline")
    return events


## A chegada é avaliada antes da expiração no mesmo frame
## (ordem determinística, generosa com quem cruza no limite).
func crossed_boarding() -> bool:
    if finished:
        return false
    finished = true
    state = State.EMBARQUE
    success = in_time()
    if not success:
        fail_reason = "atraso"
        shortfall_m = 0.0
        shortfall_s = 0.0
    return success


func fail_out_of_breath(distance: float) -> void:
    if finished:
        return
    finished = true
    success = false
    fail_reason = "folego"
    shortfall_m = maxf(0.0, run_total - distance)


## Um impacto válido retira um ponto e acrescenta penalidade ao tempo consumido.
func register_impact(penalty_seconds: float) -> float:
    if finished:
        return 0.0
    penalty_total += penalty_seconds
    time_used += penalty_seconds
    return penalty_seconds
