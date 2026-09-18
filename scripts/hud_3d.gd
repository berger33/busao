class_name RunnerHUD3D
extends Control
## HUD 2D sobre o mundo 3D. Mantém a leitura mobile, mas deixa o cenário
## completamente livre para a câmera em terceira pessoa.

const WHITE := Color("#fff8e7")
const MUTED := Color("#a9b9ca")
const INK := Color("#07101f")
const BG := Color("#0b1224")
const PANEL := Color("#14233f")
const BLUE := Color("#63c8ed")
const CYAN := Color("#63e6d2")
const YELLOW := Color("#ffd34e")
const GOLD := Color("#ffb83e")
const RED := Color("#f2635e")
const GREEN := Color("#54d18b")
const VIOLET := Color("#ac8cff")

var state: Dictionary = {}
var feedback_title := ""
var feedback_detail := ""
var feedback_color := YELLOW
var feedback_time := 0.0
var feedback_flash := 0.0
var pulse := 0.0

func _ready() -> void:
    set_process(true)
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    queue_redraw()

func _process(delta: float) -> void:
    pulse += delta
    feedback_time = maxf(0.0, feedback_time - delta)
    feedback_flash = maxf(0.0, feedback_flash - delta * 2.8)
    queue_redraw()

func set_state(next_state: Dictionary) -> void:
    state = next_state
    queue_redraw()

func show_feedback(title: String, detail: String, color: Color) -> void:
    feedback_title = title
    feedback_detail = detail
    feedback_color = color
    feedback_time = 1.05
    feedback_flash = maxf(feedback_flash, 0.055)
    queue_redraw()

func set_feedback_time(time_left: float, flash: float) -> void:
    feedback_time = maxf(feedback_time, time_left)
    feedback_flash = maxf(feedback_flash, flash)

func _draw() -> void:
    var current_screen: int = int(state.get("screen", 0))
    match current_screen:
        0: _draw_menu()
        1: _draw_map()
        2: _draw_run()
        3: _draw_results()
        4: _draw_shop()
        5: _draw_achievements()
        6: _draw_daily()
        7: _draw_how_to()
    _draw_feedback()

func _draw_menu() -> void:
    _draw_gradient(Color("#08152f"), Color("#173c5a"))
    for i in 9:
        var x: float = float(18 + i * 91)
        draw_line(Vector2(x, 250 + (i % 3) * 22), Vector2(x - 86, 520), Color(1, 0.82, 0.42, 0.12), 2.0)
    draw_circle(Vector2(568, 228), 90 + sin(pulse * 1.4) * 5.0, Color(1.0, 0.72, 0.35, 0.10))
    _panel(Rect2(38, 62, 310, 173), Color(0.04, 0.08, 0.17, 0.74), 26)
    _text(Vector2(60, 126), "CORRE", 62, YELLOW)
    _text(Vector2(60, 188), "PRO PONTO", 52, WHITE)
    _text(Vector2(62, 218), "runner 3D brasileiro", 17, Color("#ffe4ad"))
    _panel(Rect2(420, 68, 246, 48), Color(0.04, 0.08, 0.17, 0.82), 22)
    _text(Vector2(444, 99), "● 3D", 15, CYAN)
    _text(Vector2(542, 99), "50 FASES", 14, WHITE)
    _panel(Rect2(70, 564, 580, 104), Color("#f1b72f"), 22)
    draw_rect(Rect2(90, 574, 540, 4), Color(1, 1, 1, 0.35))
    _text_center(Vector2(360, 614), "CORRER AGORA", 30, INK)
    _text_center(Vector2(360, 648), "rua à esquerda • calçadas à direita", 16, Color("#553526"))
    _button(Rect2(70, 700, 275, 82), "MAPA", Color("#2c9dc1"), 25)
    _button(Rect2(375, 700, 275, 82), "LOJA", Color("#d65b75"), 25)
    _button(Rect2(70, 808, 275, 82), "CONQUISTAS", Color("#805ec7"), 21)
    _button(Rect2(375, 808, 275, 82), "DESAFIOS", Color("#4bad73"), 22)
    _panel(Rect2(70, 930, 580, 80), Color("#172844"), 18)
    _text(Vector2(102, 970), "COMO JOGAR", 22, WHITE)
    _text(Vector2(102, 995), "swipe ← → troca de faixa • ↑ pula • ↓ desliza • toque dash", 14, MUTED)
    _panel(Rect2(48, 1055, 624, 105), Color(0.04, 0.08, 0.17, 0.82), 20)
    _text(Vector2(72, 1095), "★ %03d / 150" % int(state.get("stars", 0)), 24, YELLOW)
    _text(Vector2(425, 1095), "R$ %03d" % int(state.get("coins", 0)), 22, Color("#8ee5bb"))
    _text(Vector2(72, 1140), "🔥 %02d dias" % int(state.get("streak", 0)), 17, Color("#ffb86b"))
    _text(Vector2(330, 1140), "rua + duas calçadas", 15, Color("#f9c8ae"))
    _text(Vector2(72, 1178), "ônibus impossível • humor brasileiro • câmera 3D", 14, Color("#d3e5ef"))

func _draw_map() -> void:
    _draw_ui_background()
    _header("MAPA 3D", "★ %03d / 150" % int(state.get("stars", 0)))
    _text(Vector2(30, 126), "Brasil sem Freio • capítulo %d / 5" % (int(state.get("map_page", 0)) + 1), 17, MUTED)
    var cards: Array = state.get("cards", [])
    for local_index in cards.size():
        var card: Dictionary = cards[local_index]
        var col: int = local_index % 2
        var row: int = int(local_index / 2)
        var rect := Rect2(25.0 + col * 340.0, 160.0 + row * 170.0, 330.0, 140.0)
        var unlocked: bool = bool(card.get("unlocked", false))
        var accent: Color = card.get("accent", BLUE)
        _panel(rect, Color("#1d3658") if unlocked else Color("#111d34"), 16)
        if unlocked:
            draw_rect(Rect2(rect.position, Vector2(5, rect.size.y)), accent)
        _panel(Rect2(rect.position + Vector2(10, 12), Vector2(52, 52)), accent if unlocked else Color("#303d53"), 13)
        _text_center(rect.position + Vector2(36, 47), "%02d" % (int(card.get("index", 0)) + 1) if unlocked else "LOCK", 13, INK if unlocked else MUTED)
        _text(rect.position + Vector2(76, 34), str(card.get("name", "Tela")), 18, WHITE if unlocked else MUTED)
        _text(rect.position + Vector2(76, 61), str(card.get("location", "Brasil")), 13, Color("#90a6bb"))
        _text(rect.position + Vector2(76, 80), str(card.get("scenario", "Brasil")), 11, accent)
        var stars: int = int(card.get("stars", 0))
        _text(rect.position + Vector2(18, 101), "★".repeat(stars) + "☆".repeat(3 - stars), 18, YELLOW)
        _text(rect.position + Vector2(172, 101), "DIF " + "★".repeat(int(card.get("difficulty", 1))), 13, accent)
        _text(rect.position + Vector2(18, 125), "RUA + CALÇADAS", 12, MUTED)
    _button(Rect2(25, 1080, 155, 72), "MENU", Color("#293955"), 18)
    _button(Rect2(190, 1080, 155, 72), "‹ ANTERIOR" if int(state.get("map_page", 0)) > 0 else "•", Color("#293955"), 16)
    _button(Rect2(355, 1080, 155, 72), "PRÓXIMO ›" if int(state.get("map_page", 0)) < 4 else "•", Color("#293955"), 16)
    if GameSave.data.get("endless_unlocked", false):
        _button(Rect2(520, 1080, 175, 72), "ENDLESS", VIOLET, 18)
    else:
        _text_center(Vector2(607, 1125), "★ 120 = TELA 50", 13, MUTED)
    _text_center(Vector2(360, 1205), "ESQUERDA = RUA   •   CENTRO/DIREITA = CALÇADA", 14, Color("#f9c8ae"))

func _draw_run() -> void:
    draw_rect(Rect2(0, 0, 720, 132), Color(0.025, 0.055, 0.12, 0.93))
    draw_rect(Rect2(0, 128, 720, 4), Color(state.get("phase_accent", YELLOW), 0.6))
    _text(Vector2(24, 38), "%02d  %s" % [int(state.get("phase_index", 0)) + 1, str(state.get("phase_name", "CORRE")).to_upper()], 18, WHITE)
    _text(Vector2(24, 67), "%s • %s" % [str(state.get("location", "Brasil")), str(state.get("scenario_label", "Brasil"))], 12, MUTED)
    _text(Vector2(24, 88), str(state.get("scenario_weather", "sol")), 11, Color("#b9d8db"))
    _panel(Rect2(246, 17, 148, 70), Color("#152b4a"), 17)
    _text(Vector2(264, 43), "%03d m" % int(state.get("distance", 0.0)), 22, YELLOW)
    _text(Vector2(264, 70), "R$ %02d" % int(state.get("coins_run", 0)), 15, Color("#8ee5bb"))
    var combo: int = int(state.get("combo", 0))
    if combo > 1:
        _panel(Rect2(246, 92, 220, 27), Color(1, 0.63, 0.25, 0.14), 10)
        _text(Vector2(258, 112), "COMBO x%02d" % combo, 12, GOLD)
    var hearts: int = int(state.get("hearts", 3))
    var max_hearts: int = int(state.get("max_hearts", 3))
    _text(Vector2(474, 42), "♥".repeat(hearts) + "♡".repeat(maxi(0, max_hearts - hearts)), 24, RED)
    _text(Vector2(474, 70), "RUA / CALÇADA", 13, Color("#d9e3f0"))
    _panel(Rect2(620, 25, 72, 58), Color("#203a60"), 12)
    _text_center(Vector2(656, 61), "Ⅱ" if str(state.get("run_mode", "playing")) == "paused" else "▮▮", 21, WHITE)
    var total: float = maxf(1.0, float(state.get("run_total", 400.0)))
    var progress: float = clampf(float(state.get("distance", 0.0)) / total, 0.0, 1.0)
    draw_rect(Rect2(22, 116, 676, 6), Color("#0c1a30"))
    draw_rect(Rect2(22, 116, 676 * progress, 6), state.get("phase_accent", YELLOW))
    if float(state.get("dash_cooldown", 0.0)) <= 0.0:
        _panel(Rect2(518, 137, 178, 34), Color(1, 0.72, 0.24, 0.13), 12)
        _text(Vector2(535, 160), "DASH PRONTO", 13, YELLOW)
    else:
        _text(Vector2(535, 160), "DASH %0.1f" % float(state.get("dash_cooldown", 0.0)), 13, MUTED)
    _panel(Rect2(20, 1192, 680, 48), Color(0.025, 0.055, 0.12, 0.76), 16)
    _text_center(Vector2(360, 1222), "← → FAIXA     ↑ PULO     ↓ DESLIZA     TOQUE DASH", 14, Color(0.87, 0.93, 0.95, 0.82))
    if str(state.get("run_mode", "playing")) == "at_stop":
        _draw_stop_card()
    elif str(state.get("run_mode", "playing")) == "paused":
        draw_rect(Rect2(0, 0, 720, 1280), Color(0.02, 0.04, 0.08, 0.62))
        _panel(Rect2(65, 470, 590, 285), PANEL, 24)
        _text_center(Vector2(360, 545), "PAUSA NO PONTO", 34, YELLOW)
        _text_center(Vector2(360, 590), "Respira. A rua continua lá.", 19, MUTED)
        _button(Rect2(80, 635, 560, 82), "CONTINUAR", GREEN, 24)

func _draw_stop_card() -> void:
    draw_rect(Rect2(0, 190, 720, 860), Color(0.03, 0.06, 0.11, 0.48))
    _panel(Rect2(45, 650, 630, 300), Color("#122945"), 22)
    _text_center(Vector2(360, 710), "CHEGOU NO PONTO!", 31, YELLOW)
    _text_center(Vector2(360, 752), "o ônibus sai em", 18, MUTED)
    var wait: float = float(state.get("stop_wait", 0.0))
    _text_center(Vector2(360, 806), "%0.1f s" % wait, 42, RED if wait < 3.0 else WHITE)
    draw_rect(Rect2(105, 820, 510, 5), Color("#2b3c58"))
    var wait_total: float = maxf(0.01, float(state.get("stop_wait_total", 1.0)))
    draw_rect(Rect2(105, 820, 510 * clampf(wait / wait_total, 0.0, 1.0), 5), YELLOW if wait > 3.0 else RED)
    _button(Rect2(70, 835, 580, 86), "PEGAR O BUSÃO", YELLOW, 25)

func _draw_results() -> void:
    _draw_gradient(Color("#08132b"), Color("#1c3c5a"))
    var result_data: Dictionary = state.get("result", {})
    var success: bool = bool(result_data.get("success", false))
    if success:
        _text_center(Vector2(360, 155), "PEGUEI O BUSÃO!" if not bool(result_data.get("endless", false)) else "ENDLESS CONCLUÍDO!", 38, YELLOW)
        _text_center(Vector2(360, 198), str(state.get("phase_name", "CORRE")), 18, WHITE)
        _panel(Rect2(65, 285, 590, 430), Color("#122945"), 24)
        _text_center(Vector2(360, 355), "★".repeat(int(result_data.get("stars", 0))) + "☆".repeat(3 - int(result_data.get("stars", 0))), 58, YELLOW)
        _text_center(Vector2(360, 420), "%0.1f s" % float(result_data.get("time", 0.0)), 42, WHITE)
        _text_center(Vector2(360, 454), "TEMPO DE CORRIDA", 14, MUTED)
        _text(Vector2(105, 530), "MOEDAS", 15, MUTED)
        _text(Vector2(105, 566), "+%02d" % int(result_data.get("coins", 0)), 30, GREEN)
        _text(Vector2(370, 530), "RECOMPENSA", 15, MUTED)
        _text(Vector2(370, 566), "+R$ %d" % int(result_data.get("reward", 0)), 30, GOLD)
        _text_center(Vector2(360, 650), "NOVO RECORDE!" if bool(result_data.get("record", false)) else "O próximo ponto espera", 18, VIOLET if bool(result_data.get("record", false)) else MUTED)
    else:
        _text_center(Vector2(360, 180), "O BUSÃO FOI EMBORA", 34, RED)
        _text_center(Vector2(360, 220), "Use rua e calçada como rotas diferentes.", 18, WHITE)
        _panel(Rect2(65, 330, 590, 220), Color("#2b223a"), 20)
        _text_center(Vector2(360, 390), "DICA 3D", 20, Color("#ffbf8b"))
        _text_center(Vector2(360, 438), "Rua = mais obstáculos e mais moedas", 18, WHITE)
        _text_center(Vector2(360, 470), "Calçadas = leitura e atalhos", 18, MUTED)
    _button(Rect2(55, 880, 290, 88), "MAPA", BLUE, 24)
    _button(Rect2(375, 880, 290, 88), "TENTAR DE NOVO", GOLD, 18)
    _button(Rect2(55, 1000, 610, 72), "MENU PRINCIPAL", Color("#293955"), 20)

func _draw_shop() -> void:
    _draw_ui_background()
    _header("LOJA DO PONTO", "R$ %03d" % int(state.get("coins", 0)))
    _text(Vector2(30, 126), "10 brasileiros para correr do seu jeito.", 16, MUTED)
    _button(Rect2(30, 150, 330, 70), "PERSONAGENS", BLUE if int(state.get("shop_tab", 0)) == 0 else Color("#263958"), 18)
    _button(Rect2(360, 150, 330, 70), "ITENS", RED if int(state.get("shop_tab", 0)) == 1 else Color("#263958"), 20)
    if int(state.get("shop_tab", 0)) == 0:
        var characters: Array = state.get("characters", [])
        for i in characters.size():
            var col: int = i % 2
            var row: int = int(i / 2)
            var rect := Rect2(25.0 + col * 340.0, 250.0 + row * 145.0, 330.0, 126.0)
            _character_card(rect, characters[i])
    else:
        _item_card(Rect2(30, 250, 315, 150), "Tênis turbo", "velocidade +", 200, CYAN)
        _item_card(Rect2(375, 250, 315, 150), "Mochila", "escudo extra", 180, GOLD)
        _item_card(Rect2(30, 425, 315, 150), "Fone", "ímã de moedas", 220, VIOLET)
        _item_card(Rect2(375, 425, 315, 150), "Café térmico", "slow-motion", 150, Color("#c68053"))
        _item_card(Rect2(30, 600, 315, 150), "Kit confete", "só estilo", 120, RED)
        _item_card(Rect2(375, 600, 315, 150), "Placa VIP", "atalho visual", 300, BLUE)
    _button(Rect2(45, 1135, 630, 70), "VOLTAR", Color("#293955"), 22)

func _character_card(rect: Rect2, character: Dictionary) -> void:
    var accent: Color = character.get("accent", BLUE)
    var owned: bool = bool(character.get("owned", false))
    var equipped: bool = bool(character.get("equipped", false))
    _panel(rect, Color("#254161") if owned else Color("#182b47"), 15)
    draw_circle(rect.position + Vector2(42, 43), 25, Color(accent, 0.24))
    _text_center(rect.position + Vector2(42, 51), str(character.get("gender", "")), 17, accent)
    _text(rect.position + Vector2(78, 30), str(character.get("name", "Corredor")), 16, WHITE)
    _text(rect.position + Vector2(78, 53), str(character.get("role", "brasileiro")), 12, accent)
    _text(rect.position + Vector2(16, 91), str(character.get("description", "")), 11, MUTED)
    var price: int = int(character.get("price", 0))
    var action: String = "EQUIPADO" if equipped else ("USAR" if owned else "R$ %d" % price)
    _button(Rect2(rect.end.x - 112, rect.position.y + 78, 96, 34), action, GREEN if owned else accent, 11)

func _shop_card(rect: Rect2, title: String, subtitle: String, price: int, color: Color) -> void:
    _panel(rect, Color("#223655"), 15)
    draw_circle(rect.position + Vector2(68, 63), 37, Color(color, 0.24))
    _text_center(rect.position + Vector2(68, 70), "★", 30, color)
    _text(rect.position + Vector2(130, 38), title, 22, WHITE)
    _text(rect.position + Vector2(130, 67), subtitle, 15, MUTED)
    _button(Rect2(rect.end.x - 150, rect.position.y + 34, 125, 55), "R$ %d" % price if price > 0 else "USAR", color, 16)

func _item_card(rect: Rect2, title: String, subtitle: String, price: int, color: Color) -> void:
    _panel(rect, Color("#223655"), 15)
    _text(rect.position + Vector2(22, 42), title, 21, WHITE)
    _text(rect.position + Vector2(22, 70), subtitle, 15, MUTED)
    _button(Rect2(rect.end.x - 126, rect.position.y + 42, 105, 52), "R$ %d" % price, color, 15)

func _draw_achievements() -> void:
    _draw_ui_background()
    _header("CONQUISTAS", "%d / 8" % int(GameSave.data.get("achievements", []).size()))
    _text(Vector2(30, 126), "Histórias que merecem um vídeo curto.", 17, MUTED)
    var names: Array[String] = ["Peguei o busão!", "Sobrevivi à enchente", "Cachorro caramelo", "Jeitinho brasileiro", "Só mais um pouquinho", "Brasil sem freio", "Combo de respeito", "Maratonista"]
    for i in names.size():
        var y: float = 160.0 + i * 118.0
        _panel(Rect2(35, y, 650, 104), Color("#1d3658"), 17)
        _panel(Rect2(57, y + 17, 58, 58), VIOLET, 16)
        _text_center(Vector2(86, y + 54), "★", 30, INK)
        _text(Vector2(140, y + 38), names[i], 19, WHITE)
        _text(Vector2(140, y + 68), "complete no mundo 3D", 14, MUTED)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_daily() -> void:
    _draw_ui_background()
    _header("DESAFIOS DIÁRIOS", "R$ %03d" % int(state.get("coins", 0)))
    _text(Vector2(30, 126), "Três missões curtinhas para voltar amanhã.", 16, MUTED)
    var progress: Dictionary = state.get("daily_progress", {})
    var lines: Array[String] = ["corra 250 metros", "pegue 10 moedas", "termine sem dano"]
    var status: Array[String] = ["%dm / 250m" % mini(int(progress.get("meters", 0)), 250), "%d / 10 moedas" % mini(int(progress.get("coins", 0)), 10), "pronto" if bool(progress.get("clean", false)) else "termine sem dano"]
    for i in 3:
        var y: float = 200.0 + i * 190.0
        _panel(Rect2(35, y, 650, 145), Color("#1a2f4e"), 17)
        _text(Vector2(65, y + 43), ["Pé na tábua", "Troco certo", "Desvia que eu vou"][i], 25, WHITE)
        _text(Vector2(65, y + 78), lines[i], 17, MUTED)
        _text(Vector2(65, y + 116), status[i], 15, YELLOW)
        _button(Rect2(505, y + 43, 145, 58), "RESGATAR", GREEN, 15)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_how_to() -> void:
    _draw_ui_background()
    _header("COMO JOGAR", "MUNDO 3D")
    _panel(Rect2(35, 145, 650, 430), Color("#1e3150"), 20)
    _text(Vector2(68, 198), "AS TRÊS FAIXAS", 26, YELLOW)
    _text(Vector2(75, 260), "← RUA", 24, RED)
    _text(Vector2(310, 260), "carros, motos, ônibus, buracos", 18, WHITE)
    _text(Vector2(75, 320), "CENTRO", 24, CYAN)
    _text(Vector2(310, 320), "calçada, pedestres e bônus", 18, WHITE)
    _text(Vector2(75, 380), "DIREITA →", 24, GREEN)
    _text(Vector2(310, 380), "calçada, atalhos e ponto", 18, WHITE)
    _text(Vector2(75, 460), "TOQUE", 24, GOLD)
    _text(Vector2(310, 460), "dash + invencibilidade", 18, WHITE)
    _panel(Rect2(35, 620, 650, 330), Color("#1a2a45"), 20)
    _text(Vector2(68, 675), "LEITURA PROFISSIONAL", 24, CYAN)
    _text(Vector2(68, 730), "A rua tem mais obstáculos, mas também", 18, WHITE)
    _text(Vector2(68, 766), "oferece mais moedas. Calçadas dão segurança", 18, WHITE)
    _text(Vector2(68, 802), "e bônus. Troque de faixa antes de reagir.", 18, WHITE)
    _text(Vector2(68, 862), "↑ PULO   ↓ DESLIZA   A/D ou ←/→ FAIXA", 17, MUTED)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_feedback() -> void:
    if feedback_time > 0.0:
        var width: float = minf(640.0, 160.0 + float(feedback_title.length() + feedback_detail.length()) * 4.0)
        var y: float = 145.0 if int(state.get("screen", 0)) == 2 else 122.0
        var progress: float = clampf(feedback_time / 1.05, 0.0, 1.0)
        _panel(Rect2((720.0 - width) / 2.0, y, width, 68.0), Color(feedback_color, 0.18), 18)
        draw_rect(Rect2((720.0 - width) / 2.0, y + 65, width * progress, 3), feedback_color)
        _text_center(Vector2(360, y + 28), feedback_title, 20, WHITE)
        _text_center(Vector2(360, y + 52), feedback_detail, 13, feedback_color.lightened(0.22))
    if feedback_flash > 0.0:
        draw_rect(Rect2(0, 0, 720, 1280), Color(feedback_color, feedback_flash))

func _draw_ui_background() -> void:
    _draw_gradient(Color("#081329"), Color("#173858"))
    for i in 8:
        draw_circle(Vector2(40 + i * 102, 1060 - (i % 3) * 55), 95, Color(0.09, 0.25, 0.34, 0.18))
    for i in 7:
        var grid_y: float = 170.0 + i * 150.0
        draw_line(Vector2(0, grid_y), Vector2(720, grid_y - 92), Color(0.45, 0.78, 0.84, 0.045), 1.0)

func _draw_gradient(top: Color, bottom: Color) -> void:
    for i in 16:
        var t: float = float(i) / 15.0
        draw_rect(Rect2(0, i * 80, 720, 82), top.lerp(bottom, t))

func _header(title: String, right: String) -> void:
    draw_rect(Rect2(0, 0, 720, 112), Color(0.025, 0.055, 0.12, 0.94))
    draw_rect(Rect2(0, 108, 720, 4), Color(0.32, 0.82, 0.84, 0.45))
    _panel(Rect2(18, 27, 54, 58), Color("#1c3556"), 18)
    _text_center(Vector2(45, 67), "‹", 39, YELLOW)
    _text(Vector2(92, 48), title, 25, WHITE)
    _text(Vector2(92, 76), "CORRE PRO PONTO 3D", 13, MUTED)
    _panel(Rect2(492, 28, 205, 54), Color("#152a49"), 18)
    _text_center(Vector2(594, 62), right, 17, YELLOW)

func _panel(rect: Rect2, color: Color, radius: float = 12.0) -> void:
    draw_style_box(_make_box(Color(0.01, 0.025, 0.07, 0.48), radius), Rect2(rect.position + Vector2(0, 6), rect.size))
    draw_style_box(_make_box(color, radius), rect)
    if rect.size.x > radius * 2.0:
        draw_line(rect.position + Vector2(radius, 1), Vector2(rect.end.x - radius, rect.position.y + 1), Color(1, 1, 1, 0.12), 1.0)

func _button(rect: Rect2, label: String, color: Color, size: int = 20) -> void:
    _panel(rect, color, 15)
    draw_rect(Rect2(rect.position + Vector2(3, 3), Vector2(rect.size.x - 6, 4)), Color(1, 1, 1, 0.12))
    draw_line(rect.position + Vector2(14, rect.size.y - 6), rect.end - Vector2(14, 6), Color(0.02, 0.05, 0.1, 0.22), 2)
    _text_center(rect.position + rect.size / 2.0 + Vector2(0, 3), label, size, INK if color != Color("#293955") and color != Color("#263958") else WHITE)

func _make_box(color: Color, radius: float) -> StyleBoxFlat:
    var box := StyleBoxFlat.new()
    box.bg_color = color
    box.corner_radius_top_left = int(radius)
    box.corner_radius_top_right = int(radius)
    box.corner_radius_bottom_left = int(radius)
    box.corner_radius_bottom_right = int(radius)
    box.border_width_left = 1
    box.border_width_top = 1
    box.border_width_right = 1
    box.border_width_bottom = 1
    box.border_color = Color(1, 1, 1, 0.10)
    return box

func _text(pos: Vector2, value: String, size: int, color: Color) -> void:
    draw_string(ThemeDB.fallback_font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func _text_center(pos: Vector2, value: String, size: int, color: Color) -> void:
    var width: float = maxf(100.0, float(value.length() * size) * 0.72)
    draw_string(ThemeDB.fallback_font, Vector2(pos.x - width / 2.0, pos.y), value, HORIZONTAL_ALIGNMENT_CENTER, width, size, color)
