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

var _safe_top: float = 0.0
var _safe_bottom: float = 0.0
var _safe_left: float = 0.0
var _safe_right: float = 0.0

func _update_safe_area() -> void:
    var safe := DisplayServer.get_display_safe_area()
    var win := DisplayServer.window_get_size()
    if win.x == 0 or win.y == 0:
        return
    var sx: float = 720.0 / float(win.x) if win.x != 0 else 1.0
    var sy: float = 1280.0 / float(win.y) if win.y != 0 else 1.0
    _safe_left = float(safe.position.x) * sx
    _safe_top = float(safe.position.y) * sy
    _safe_right = float(win.x - safe.end.x) * sx
    _safe_bottom = float(win.y - safe.end.y) * sy

func _T(key: String) -> String:
    if has_node("/root/LocaleManager"):
        var lm = get_node_or_null("/root/LocaleManager")
        if lm and lm.has_method("tr_key"):
            return lm.call("tr_key", key)
    return key

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
    _update_safe_area()
    # SafeArea reage a resize/notch; LocaleManager troca idioma em runtime
    if has_node("/root/LocaleManager"):
        var _lm = get_node_or_null("/root/LocaleManager")
        if _lm and _lm.has_signal("locale_changed"):
            _lm.locale_changed.connect(func(_l: String): queue_redraw())
    queue_redraw()

func _process(delta: float) -> void:
    pulse += delta
    feedback_time = maxf(0.0, feedback_time - delta)
    feedback_flash = maxf(0.0, feedback_flash - delta * 2.8)
    queue_redraw()

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_SIZE_CHANGED:
        _update_safe_area()
        queue_redraw()

func set_state(next_state: Dictionary) -> void:
    state = next_state
    if bool(state.get("colorblind_mode", false)):
        state["phase_accent"] = _colorblind_accent(state.get("phase_accent", YELLOW))
    queue_redraw()

func _colorblind_accent(color: Color) -> Color:
    # Azul/laranja têm separação melhor que vermelho/verde em telas pequenas.
    if color.is_equal_approx(RED) or color.is_equal_approx(GREEN):
        return BLUE if color.is_equal_approx(GREEN) else GOLD
    return color

func show_feedback(title: String, detail: String, color: Color) -> void:
    feedback_title = title
    feedback_detail = detail
    feedback_color = _colorblind_accent(color) if bool(state.get("colorblind_mode", false)) else color
    feedback_time = 1.05
    if not bool(state.get("reduced_motion", false)):
        feedback_flash = maxf(feedback_flash, 0.055)
    queue_redraw()

func set_feedback_time(time_left: float, flash: float) -> void:
    feedback_time = maxf(feedback_time, time_left)
    feedback_flash = maxf(feedback_flash, flash)

func _draw() -> void:
    # Lote 16: SafeArea — escala+translada para dentro do notch (DisplayServer.get_display_safe_area)
    if _safe_top > 0.0 or _safe_bottom > 0.0 or _safe_left > 0.0 or _safe_right > 0.0:
        var sx: float = (720.0 - _safe_left - _safe_right) / 720.0
        var sy: float = (1280.0 - _safe_top - _safe_bottom) / 1280.0
        draw_set_transform(Vector2(_safe_left, _safe_top), 0.0, Vector2(sx, sy))
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
    _text(Vector2(60, 126), _T("MENU_TITLE_CORRE"), 62, YELLOW)
    _text(Vector2(60, 188), _T("MENU_TITLE_PRO_PONTO"), 52, WHITE)
    _text(Vector2(62, 218), _T("MENU_SUBTITLE"), 17, Color("#ffe4ad"))
    _panel(Rect2(420, 68, 246, 48), Color(0.04, 0.08, 0.17, 0.82), 22)
    _text(Vector2(444, 99), "● 3D", 15, CYAN)
    _text(Vector2(542, 99), "50 FASES", 14, WHITE)
    _button(Rect2(510, 132, 156, 46), "SOM: OFF" if AudioManager.muted else "SOM: ON", Color("#263958"), 13)
    _button(Rect2(420, 190, 118, 38), "MOV: OFF" if bool(state.get("reduced_motion", false)) else "MOV: ON", Color("#263958"), 11)
    _button(Rect2(544, 190, 122, 38), "CONTRASTE" if bool(state.get("high_contrast", false)) else "VISUAL", Color("#263958"), 10)
    _panel(Rect2(70, 564, 580, 104), Color("#f1b72f"), 22)
    draw_rect(Rect2(90, 574, 540, 4), Color(1, 1, 1, 0.35))
    _text_center(Vector2(360, 614), _T("MENU_PLAY_NOW"), 30, INK)
    _text_center(Vector2(360, 648), "rua à esquerda • calçadas à direita", 16, Color("#553526"))
    _button(Rect2(70, 700, 275, 82), _T("MENU_MAP"), Color("#2c9dc1"), 25)
    _button(Rect2(375, 700, 275, 82), _T("MENU_SHOP"), Color("#d65b75"), 25)
    _button(Rect2(70, 808, 275, 82), "CONQUISTAS", Color("#805ec7"), 21)
    _button(Rect2(375, 808, 275, 82), "DESAFIOS", Color("#4bad73"), 22)
        # Lote 16: toggle idioma pt_BR/en_US
    var _cur_lang: String = "pt_BR"
    if has_node("/root/LocaleManager"):
        var _lm2 = get_node_or_null("/root/LocaleManager")
        if _lm2 and _lm2.has_method("get_locale"):
            _cur_lang = _lm2.call("get_locale")
    _button(Rect2(470, 885, 110, 34), _cur_lang, Color("#314563"), 11)
    _text(Vector2(485, 907), "IDIOMA", 9, MUTED)
    _panel(Rect2(70, 930, 580, 80), Color("#172844"), 18)
    _text(Vector2(102, 970), "COMO JOGAR", 22, WHITE)
    _text(Vector2(102, 995), "swipe ← → troca de faixa • ↑ pula • ↓ desliza • toque dash", 14, MUTED)
    _panel(Rect2(48, 1055, 624, 105), Color(0.04, 0.08, 0.17, 0.82), 20)
    _text(Vector2(72, 1095), "★ %03d / 150" % int(state.get("stars", 0)), 24, YELLOW)
    _text(Vector2(425, 1095), "R$ %03d" % int(state.get("coins", 0)), 22, Color("#8ee5bb"))
    if state.has("rubi"):
        _text(Vector2(545, 1095), _T("RUBI_LABEL") % int(state.get("rubi", 0)) if "%d" in _T("RUBI_LABEL") else "Rubi %d" % int(state.get("rubi", 0)), 14, Color("#ff7ab8"))
    _text(Vector2(72, 1140), "🔥 %02d dias" % int(state.get("streak", 0)), 17, Color("#ffb86b"))
    _text(Vector2(330, 1140), "NÍVEL %02d • XP %d/%d" % [int(state.get("xp_level", 1)), int(state.get("xp_into_level", 0)), int(state.get("xp_into_level", 0)) + int(state.get("xp_to_next_level", 250))], 14, Color("#f9c8ae"))
    _text(Vector2(72, 1178), "ônibus impossível • humor brasileiro • câmera 3D", 14, Color("#d3e5ef"))
    _draw_banner_if_needed(1210)

func _draw_map() -> void:
    _draw_ui_background()
    _header(_T("MAP_TITLE"), "★ %03d / 150" % int(state.get("stars", 0)))
    _text(Vector2(30, 126), "Brasil sem Freio • capítulo %d / 5" % (int(state.get("map_page", 0)) + 1), 17, MUTED)
    if state.has("weekly_event"):
        var _we: Dictionary = state.get("weekly_event", {})
        var _we_title: String = str(_we.get("title", "Evento"))
        var _we_desc: String = str(_we.get("desc", ""))
        _panel(Rect2(430, 100, 260, 44), Color("#2a1f3a") if str(_we.get("id",""))=="semana_motoboy" else Color("#1f2f3a"), 10)
        _text(Vector2(442, 120), _we_title, 11, YELLOW)
        _text(Vector2(442, 135), _we_desc, 9, MUTED)
    var next_unlock: int = int(state.get("next_unlock_stars", 0))
    if next_unlock > 0:
        _text(Vector2(430, 126), "próximo marco: ★ %d" % next_unlock, 14, GOLD)
    else:
        _text(Vector2(430, 126), "todos os marcos liberados", 14, GREEN)
    var cards: Array = state.get("cards", [])
    for local_index in cards.size():
        var card: Dictionary = cards[local_index]
        var col: int = local_index % 2
        var row: int = int(float(local_index) / 2.0)
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
    _draw_banner_if_needed(1215)

func _fmt_time(t: float) -> String:
    var s := int(maxf(0.0, t))
    return "%02d:%02d" % [int(s / 60.0), s % 60]

func _draw_run() -> void:
    # Topo translúcido moderno (deixa o céu, prédios e iluminação solar visíveis)
    draw_rect(Rect2(0, 0, 720, 108), Color(0.02, 0.04, 0.08, 0.38))
    # Cápsula de fase e cenário
    _panel(Rect2(18, 18, 215, 68), Color(0.05, 0.10, 0.18, 0.65), 16)
    _hud_icon(Vector2(39, 42), "route", CYAN)
    _text(Vector2(58, 42), "%02d  %s" % [int(state.get("phase_index", 0)) + 1, str(state.get("phase_name", "CORRE")).to_upper()], 16, WHITE)
    _text(Vector2(58, 64), "%s • %s" % [str(state.get("location", "Brasil")), str(state.get("scenario_weather", "sol")).to_upper()], 11, CYAN)
    # Cápsula de distância e moedas
    _panel(Rect2(245, 18, 175, 68), Color(0.05, 0.10, 0.18, 0.65), 16)
    _hud_icon(Vector2(260, 43), "distance", YELLOW)
    _text(Vector2(278, 43), "%03d m" % int(state.get("distance", 0.0)), 20, YELLOW)
    _hud_icon(Vector2(260, 68), "coin", GOLD)
    _text(Vector2(278, 68), "R$ %02d" % int(state.get("coins_run", 0)), 15, Color("#8ee5bb"))
    draw_circle(Vector2(382, 63), 7.5, GOLD)
    draw_arc(Vector2(382, 63), 6.0, 0.0, TAU, 16, Color(1.0, 0.94, 0.60, 0.90), 1.2)
    draw_circle(Vector2(382, 63), 3.0, Color(1.0, 0.78, 0.22, 0.80))
    var combo: int = int(state.get("combo", 0))
    if combo > 1:
        _panel(Rect2(245, 92, 175, 24), Color(1, 0.63, 0.25, 0.16), 8)
        _text_center(Vector2(332, 108), "COMBO x%02d" % combo, 11, GOLD)
    # Cápsula de vidas
    _panel(Rect2(432, 18, 172, 68), Color(0.05, 0.10, 0.18, 0.65), 16)
    var hearts: int = int(state.get("hearts", 3))
    var max_hearts: int = int(state.get("max_hearts", 3))
    _hud_icon(Vector2(446, 45), "heart", RED)
    _text(Vector2(463, 46), "♥".repeat(hearts) + "♡".repeat(maxi(0, max_hearts - hearts)), 22, RED)
    _text(Vector2(463, 68), "VIDA • ROTA SEGURA", 10, Color("#d9e3f0"))
    # ETAPA 1 — prazo de partida do ônibus (o relógio que era a "espera no ponto").
    if not bool(state.get("endless", false)):
        var time_left: float = float(state.get("time_left", 0.0))
        var urgent: bool = time_left < 10.0
        _panel(Rect2(18, 112, 215, 30), Color(1, 0.25, 0.2, 0.25) if urgent else Color(0.05, 0.10, 0.18, 0.65), 10)
        _text_center(Vector2(125, 132), "ÔNIBUS " + _fmt_time(time_left), 14, RED if urgent else YELLOW)
    # Botão de pausa translúcido arredondado
    _panel(Rect2(616, 18, 80, 68), Color(0.12, 0.22, 0.38, 0.70), 16)
    _text_center(Vector2(656, 56), "Ⅱ" if str(state.get("run_mode", "playing")) == "paused" else "▮▮", 20, WHITE)
    var total: float = maxf(1.0, float(state.get("run_total", 400.0)))
    var progress: float = clampf(float(state.get("distance", 0.0)) / total, 0.0, 1.0)
    # Rota do ônibus: trilho discreto + marcador móvel, mais legível que
    # apenas uma linha de progresso solta.
    draw_line(Vector2(28, 96), Vector2(688, 96), Color(0.75, 0.86, 0.92, 0.20), 3.0)
    draw_line(Vector2(28, 96), Vector2(28 + 660 * progress, 96), state.get("phase_accent", YELLOW), 4.0)
    draw_circle(Vector2(28 + 660 * progress, 96), 5.0, Color("#fff8e7"))
    draw_circle(Vector2(688, 96), 7.0, Color("#ffd34e"))
    _text_center(Vector2(688, 101), "●", 9, INK)
    if bool(state.get("in_approach", false)) and not bool(state.get("boarding", false)):
        _panel(Rect2(252, 118, 246, 30), Color(0.20, 0.78, 0.72, 0.22), 10)
        _text_center(Vector2(375, 138), "PONTO À FRENTE • PREPARE-SE", 12, CYAN)
    if float(state.get("dash_cooldown", 0.0)) <= 0.0:
        _panel(Rect2(518, 118, 178, 30), Color(1, 0.72, 0.24, 0.15), 10)
        _text_center(Vector2(607, 138), "DASH PRONTO", 12, YELLOW)
    else:
        _text(Vector2(535, 138), "DASH %0.1f" % float(state.get("dash_cooldown", 0.0)), 12, MUTED)
    # Controles ficam ocultos durante a corrida normal: o cenário permanece
    # limpo e o jogador só recebe uma instrução quando realmente precisa.
    if str(state.get("tutorial_hint", "")) != "" and float(state.get("distance", 0.0)) < float(state.get("first_session_hint_distance", 70.0)):
        _panel(Rect2(55, 180, 610, 58), Color(0.05, 0.16, 0.25, 0.93), 15)
        _text_center(Vector2(360, 216), str(state.get("tutorial_hint", "")), 15, CYAN)
        _text_center(Vector2(360, 236), "gesto para agir • toque curto para dash", 10, Color("#a9dce5"))
    var _mode_run: String = str(state.get("run_mode", "playing"))
    if _mode_run == "countdown":
        draw_rect(Rect2(0, 0, 720, 1280), Color(0.02, 0.04, 0.08, 0.42))
        var cd_left: float = float(state.get("countdown_left", 0.0))
        var cd_num: int = clampi(int(ceilf(cd_left / 0.8)), 1, 3)
        _text_center(Vector2(360, 560), str(cd_num), 130, YELLOW)
        _text_center(Vector2(360, 655), "o ônibus sai em", 20, MUTED)
        _text_center(Vector2(360, 708), _fmt_time(float(state.get("deadline", 0.0))), 34, WHITE)
    elif _mode_run == "boarding":
        draw_rect(Rect2(0, 0, 720, 1280), Color(0.02, 0.04, 0.08, 0.30))
        _panel(Rect2(75, 480, 570, 210), Color("#122945"), 22)
        _text_center(Vector2(360, 555), "PEGUEI O PONTO!", 36, GREEN)
        _text_center(Vector2(360, 605), "as portas fecham...", 18, MUTED)
        _text_center(Vector2(360, 655), "toque para pular", 13, CYAN)
    elif _mode_run == "paused":
        draw_rect(Rect2(0, 0, 720, 1280), Color(0.02, 0.04, 0.08, 0.62))
        _panel(Rect2(65, 470, 590, 285), PANEL, 24)
        _text_center(Vector2(360, 545), "PAUSA NO PONTO", 34, YELLOW)
        _text_center(Vector2(360, 590), "Respira. A rua continua lá.", 19, MUTED)
        _button(Rect2(80, 635, 560, 82), "CONTINUAR", GREEN, 24)


func _draw_results() -> void:
    _draw_gradient(Color("#08132b"), Color("#1c3c5a"))
    var result_data: Dictionary = state.get("result", {})
    var success: bool = bool(result_data.get("success", false))
    if success:
        _text_center(Vector2(360, 155), "PEGUEI O BUSÃO!" if not bool(result_data.get("endless", false)) else "ENDLESS CONCLUÍDO!", 38, YELLOW)
        _text_center(Vector2(360, 198), str(state.get("phase_name", "CORRE")), 18, WHITE)
        _panel(Rect2(65, 285, 590, 430), Color("#122945"), 24)
        if bool(result_data.get("endless", false)):
            _text_center(Vector2(360, 355), "%dm" % int(result_data.get("distance", 0)), 48, VIOLET)
            _text_center(Vector2(360, 404), "DISTÂNCIA NO ENDLESS", 14, MUTED)
        else:
            _text_center(Vector2(360, 355), "★".repeat(int(result_data.get("stars", 0))) + "☆".repeat(3 - int(result_data.get("stars", 0))), 58, YELLOW)
        _text_center(Vector2(360, 465), "%0.1f s" % float(result_data.get("time", 0.0)), 42, WHITE)
        _text_center(Vector2(360, 499), "TEMPO DE CORRIDA", 14, MUTED)
        _text(Vector2(105, 530), "MOEDAS NA PISTA", 15, MUTED)
        _text(Vector2(105, 566), "+%02d" % int(result_data.get("coins", 0)), 30, GREEN)
        _text(Vector2(370, 530), "BÔNUS DE CONCLUSÃO", 15, MUTED)
        _text(Vector2(370, 566), "+R$ %d" % int(result_data.get("reward", 0)), 30, GOLD)
        var reward_note := "replay com bônus fixo"
        if bool(result_data.get("endless", false)):
            reward_note = "recorde local" if bool(result_data.get("record", false)) else "endless replay com teto"
        elif bool(result_data.get("first_clear", false)):
            reward_note = "primeira conclusão"
        elif int(result_data.get("new_stars", 0)) > 0:
            reward_note = "nova estrela"
        _text_center(Vector2(360, 612), reward_note, 14, Color("#b9d8db"))
        var progress_note := "NOVO RECORDE!" if bool(result_data.get("record", false)) else ("+%d estrela(s) nesta corrida" % int(result_data.get("new_stars", 0)))
        var award_note := str(result_data.get("award_note", ""))
        if award_note != "":
            progress_note = "%s • %s" % [progress_note, award_note]
        _text_center(Vector2(360, 650), progress_note, 18, VIOLET if bool(result_data.get("record", false)) else MUTED)
        var xp_line := "+%d XP" % int(result_data.get("xp", 0))
        var levelup: Dictionary = result_data.get("levelup", {})
        if int(levelup.get("levels", 0)) > 0:
            xp_line = "%s • NÍVEL %d! +R$ %d" % [xp_line, int(levelup.get("level", 0)), int(levelup.get("coins", 0))]
            if int(levelup.get("rubi", 0)) > 0:
                xp_line = "%s • +%d Rubi" % [xp_line, int(levelup.get("rubi", 0))]
        _text_center(Vector2(360, 682), xp_line, 15, GREEN)
        var breakdown: Dictionary = result_data.get("reward_breakdown", {})
        if not breakdown.is_empty():
            _text_center(Vector2(360, 708), "base %d • fase %d • estrelas %d • perfeito %d" % [int(breakdown.get("base", 0)), int(breakdown.get("level", 0)), int(breakdown.get("stars", 0)), int(breakdown.get("perfect", 0))], 11, Color("#a9b9ca"))
        if not bool(result_data.get("endless", false)):
            var next_unlock := int(state.get("next_unlock_stars", 0))
            var stars_now := int(state.get("stars", 0))
            var star_progress := "★ %d acumuladas • catálogo liberado" % stars_now
            if next_unlock > 0:
                star_progress = "★ %d acumuladas • próximo marco ★ %d" % [stars_now, next_unlock]
            _text_center(Vector2(360, 738), star_progress, 13, CYAN)
    else:
        var fail_reason: String = str(result_data.get("fail_reason", "folego"))
        var fail_line: String = "Escolha sua rota cedo e desvie sem parar."
        if fail_reason == "atraso":
            fail_line = "Faltavam %d m (%d s) para o ponto quando o ônibus partiu." % [
                    int(result_data.get("shortfall_m", 0)), int(result_data.get("shortfall_s", 0))]
        elif fail_reason == "folego":
            fail_line = "O fôlego acabou antes do ponto."
        # Retenção D0–D30: dica por causa da derrota (a anterior falava de
        # "rua × calçadas", que não existe nas fases autorais: os 3
        # corredores são calçada).
        var tip_a := "Leia os 3 corredores antes de agir"
        var tip_b := "↑ pula o buraco • ↓ passa sob a barra"
        if fail_reason == "atraso":
            tip_a = "DASH nas retas economiza segundos"
            tip_b = "Cada impacto custa +2 s no relógio"
        _text_center(Vector2(360, 180), "O BUSÃO FOI EMBORA", 34, RED)
        _text_center(Vector2(360, 220), fail_line, 18, WHITE)
        _panel(Rect2(65, 330, 590, 220), Color("#2b223a"), 20)
        _text_center(Vector2(360, 390), "DICA 3D", 20, Color("#ffbf8b"))
        _text_center(Vector2(360, 438), tip_a, 18, WHITE)
        _text_center(Vector2(360, 470), tip_b, 18, MUTED)
    # Lote 11 — ofertas rewarded (revive 1x e 2x moedas)
    var rewarded_ready: bool = bool(state.get("rewarded_ready", false))
    var revive_available: bool = bool(state.get("revive_available", false))
    var double_available: bool = bool(state.get("double_available", false))
    if not success and revive_available:
        # revive ainda não usado e rewarded pronto
        var revive_color: Color = CYAN if rewarded_ready else Color("#314563")
        var revive_label: String = "▶ REVIVER COM ANÚNCIO (1×)" if rewarded_ready else "REVIVER • CARREGANDO..."
        _button(Rect2(55, 600, 610, 72), revive_label, revive_color, 16)
        _text_center(Vector2(360, 685), "assista e continue de onde parou • 5 s invencível", 12, MUTED)
    elif success and double_available:
        var reward_val: int = int(result_data.get("reward", 0))
        var dbl_color: Color = GOLD if rewarded_ready else Color("#314563")
        var dbl_label: String = "2× MOEDAS COM ANÚNCIO +%d" % reward_val if rewarded_ready else "2× MOEDAS • CARREGANDO..."
        _button(Rect2(55, 760, 610, 72), dbl_label, dbl_color, 16)
        _text_center(Vector2(360, 845), "dobra o bônus desta corrida • sem repetir", 12, MUTED)
    _button(Rect2(55, 880, 290, 88), "MAPA", BLUE, 24)
    var next_action_label := "PRÓXIMA FASE" if (success and not bool(result_data.get("endless", false)) and int(state.get("phase_index", 0)) < 49 and GameSave.is_phase_unlocked(int(state.get("phase_index", 0)) + 1)) else "TENTAR DE NOVO"
    _button(Rect2(375, 880, 290, 88), next_action_label, GOLD, 18)
    _button(Rect2(55, 1000, 610, 72), "MENU PRINCIPAL", Color("#293955"), 20)

func _draw_shop() -> void:
    _draw_ui_background()
    var scroll: float = float(state.get("shop_scroll", 0.0))
    var scroll_max: float = float(state.get("shop_scroll_max", 0.0))
    var characters: Array = state.get("characters", [])
    if int(state.get("shop_tab", 0)) == 0:
        for i in characters.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var card_y: float = 280.0 + row * 145.0 - scroll
            if card_y + 126.0 < 280.0 or card_y > 1125.0:
                continue
            var rect := Rect2(25.0 + col * 340.0, card_y, 330.0, 126.0)
            _character_card(rect, characters[i])
            # Lote 17: destaque semanal (15% OFF) — estrela no card featured
            var _feat: Dictionary = state.get("featured_item", {})
            if str(_feat.get("id","")) == str(characters[i].get("id","")):
                _text(rect.position + Vector2(rect.size.x - 62, 18), _T("FEATURED_DISCOUNT"), 10, YELLOW)
        # Sinks L17: reroll cor 40 R$ + skin extra 80 Rubi (aba personagens)
        _panel(Rect2(30, 240, 640, 34), Color(0.08,0.12,0.18,0.6), 8)
        _text(Vector2(42, 262), "Rubi: %d" % int(state.get("rubi", 0)), 12, Color("#ff7ab8"))
        _text(Vector2(140, 262), "Destaque: %s 15%% OFF" % str(state.get("featured_item", {}).get("id","—")) if state.has("featured_item") else "Destaque: —", 10, MUTED)
        _button(Rect2(500, 240, 140, 28), _T("REROLL"), Color("#63e6d2") if int(state.get("coins",0))>=40 else Color("#314563"), 10)
        _button(Rect2(500, 274, 140, 28), _T("SKIN_EXTRA"), Color("#ff7ab8") if int(state.get("rubi",0))>=80 else Color("#314563"), 9)
        _mask_band(126.0, 280.0)
        _mask_band(1125.0, 1280.0)
    elif int(state.get("shop_tab", 0)) == 1:
        var items: Array = state.get("items", [])
        for i in items.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var rect := Rect2(30.0 + col * 345.0, 280.0 + row * 175.0, 315.0, 150.0)
            _item_card(rect, items[i])
        _mask_band(126.0, 280.0)
    else:
        var packs: Array = state.get("billing_packs", [])
        for i in packs.size():
            var col: int = i % 2
            var row: int = int(float(i) / 2.0)
            var rect := Rect2(30.0 + col * 345.0, 280.0 + row * 155.0, 315.0, 135.0)
            # desfase para não desenhar fora da janela
            if rect.position.y + rect.size.y < 280.0 or rect.position.y > 1125.0:
                continue
            _billing_card(rect, packs[i])
        _text_center(Vector2(360, 1095), "compras únicas • sem loot box • teste: android.test.purchased", 10, MUTED)
    _header(_T("SHOP_TITLE"), "R$ %03d • Rubi %d" % [int(state.get("coins", 0)), int(state.get("rubi", 0))])
    _text(Vector2(30, 126), "%d brasileiros para correr do seu jeito." % characters.size(), 16, MUTED)
    # 3 abas: personagens | itens | pacotes
    _button(Rect2(30, 150, 210, 70), "PERSONAGENS", BLUE if int(state.get("shop_tab", 0)) == 0 else Color("#263958"), 14)
    _button(Rect2(250, 150, 210, 70), "ITENS", RED if int(state.get("shop_tab", 0)) == 1 else Color("#263958"), 16)
    _button(Rect2(470, 150, 210, 70), "PACOTES", GOLD if int(state.get("shop_tab", 0)) == 2 else Color("#263958"), 15)
    # linha remove_ads / info consent
    var remove_ads_owned: bool = bool(state.get("remove_ads", false))
    var remove_label: String = "✓ SEM ANÚNCIOS" if remove_ads_owned else "REMOVER ANÚNCIOS R$ 9,90"
    var remove_color: Color = GREEN if remove_ads_owned else Color("#d9a03a")
    _button(Rect2(30, 230, 330, 36), remove_label, remove_color, 11)
    _text(Vector2(375, 254), "restaurar compras →", 11, MUTED)
    _button(Rect2(545, 230, 135, 36), "RESTAURAR", Color("#263958"), 10)
    # conteúdo por aba — desloca para baixo por causa da linha remove_ads
    if int(state.get("shop_tab", 0)) == 0 and scroll_max > 0.0:
        var track_height: float = 875.0
        var thumb_height: float = maxf(72.0, track_height * (875.0 / (875.0 + scroll_max)))
        var thumb_y: float = 250.0 + (scroll / scroll_max) * (track_height - thumb_height)
        draw_rect(Rect2(703, 250, 6, track_height), Color(1, 1, 1, 0.10))
        draw_rect(Rect2(703, thumb_y, 6, thumb_height), Color(0.45, 0.85, 0.88, 0.55))
        _text_center(Vector2(676, 1128), "arraste a lista", 11, MUTED)
    _button(Rect2(45, 1135, 630, 70), "VOLTAR", Color("#293955"), 22)
    _draw_banner_if_needed(1210)

func _draw_banner_if_needed(y: float) -> void:
    var remove_ads_owned: bool = bool(state.get("remove_ads", false))
    if remove_ads_owned:
        _text_center(Vector2(360, y + 22), "sem anúncios • obrigado pelo apoio! ♡", 11, GREEN)
        return
    var banner_visible: bool = bool(state.get("banner_visible", false))
    # Mock banner 320x50 centrado — em produção é view nativa AdMob sobreposta
    var banner_rect := Rect2(200, y, 320, 50)
    var banner_color: Color = Color("#1a335a") if banner_visible else Color("#12233f")
    _panel(banner_rect, banner_color, 10)
    var label: String = "ANÚNCIO  320×50  •  AdMob" if banner_visible else "anúncio carregando..."
    _text_center(banner_rect.get_center() + Vector2(0,5), label, 11, MUTED if not banner_visible else Color("#d3e5ef"))
    _text_center(Vector2(360, y + 62), "Data Safety • UMP consent • banner mock no editor", 9, Color("#7a8da6"))

func _billing_card(rect: Rect2, pack: Dictionary) -> void:
    var title := str(pack.get("title", "Pacote"))
    var subtitle := str(pack.get("subtitle", ""))
    var price_label := str(pack.get("price_label", "R$ —"))
    var pack_id := str(pack.get("id",""))
    var is_remove := pack_id == "remove_ads"
    var owned: bool = bool(state.get("remove_ads", false)) if is_remove else false
    var accent: Color = GOLD if is_remove else CYAN
    if pack_id == "coin_pack_l": accent = VIOLET
    elif pack_id == "coin_pack_m": accent = BLUE
    elif pack_id == "starter_pack": accent = RED
    _panel(rect, Color("#2a4663") if owned else Color("#223655"), 15)
    _text(rect.position + Vector2(18, 36), title, 18, WHITE)
    _text(rect.position + Vector2(18, 62), subtitle, 12, MUTED)
    _text(rect.position + Vector2(18, 92), price_label, 14, accent)
    var btn_label: String = "ADQUIRIDO" if owned else "COMPRAR"
    var btn_color: Color = GREEN if owned else accent
    _button(Rect2(rect.end.x - 110, rect.position.y + 42, 92, 52), btn_label, btn_color, 12)

func _mask_band(y0: float, y1: float) -> void:
    # Reconstrói as faixas do gradiente de fundo para esconder cards que
    # atravessam os limites da janela da loja sem depender de clip nodes.
    var top := Color("#081329")
    var bottom := Color("#173858")
    for i in 16:
        var band_y: float = i * 80.0
        var band_bottom: float = band_y + 82.0
        if band_bottom <= y0 or band_y >= y1:
            continue
        var clipped_top: float = maxf(y0, band_y)
        var clipped_bottom: float = minf(y1, band_bottom)
        draw_rect(Rect2(0, clipped_top, 720, clipped_bottom - clipped_top), top.lerp(bottom, float(i) / 15.0))

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
    _text(rect.position + Vector2(16, 111), "efeito: " + str(character.get("effect", "equilíbrio")), 10, CYAN)
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

func _item_card(rect: Rect2, item: Dictionary) -> void:
    var title := str(item.get("title", "Item"))
    var subtitle := str(item.get("subtitle", "efeito"))
    var price := int(item.get("price", 0))
    var color: Color = item.get("accent", BLUE)
    var owned := bool(item.get("owned", false))
    _panel(rect, Color("#2a4663") if owned else Color("#223655"), 15)
    _text(rect.position + Vector2(22, 42), title, 21, WHITE)
    _text(rect.position + Vector2(22, 70), subtitle, 15, MUTED)
    var cosmetic := bool(item.get("cosmetic", false))
    var item_note := "cosmético • sem vantagem" if cosmetic else "efeito aplicado na próxima corrida"
    _text(rect.position + Vector2(22, 105), item_note if owned else "compra única • sem aleatoriedade", 11, CYAN if owned else MUTED)
    _button(Rect2(rect.end.x - 126, rect.position.y + 42, 105, 52), "ADQUIRIDO" if owned else "R$ %d" % price, GREEN if owned else color, 13)

func _draw_achievements() -> void:
    _draw_ui_background()
    var catalog: Array = state.get("achievement_catalog", [])
    var unlocked_count := 0
    for item in catalog:
        if bool(item.get("unlocked", false)):
            unlocked_count += 1
    _header("CONQUISTAS", "%d / %d" % [unlocked_count, catalog.size()])
    _text(Vector2(30, 126), "Estados reais do seu perfil: conquista e badge ficam claros.", 15, MUTED)
    for i in catalog.size():
        var item: Dictionary = catalog[i]
        var y: float = 160.0 + i * 118.0
        var unlocked := bool(item.get("unlocked", false))
        var accent: Color = GREEN if unlocked else Color("#53647a")
        _panel(Rect2(35, y, 650, 104), Color("#214b50") if unlocked else Color("#182942"), 17)
        _panel(Rect2(57, y + 17, 58, 58), accent, 16)
        _text_center(Vector2(86, y + 54), "✓" if unlocked else "?", 27, INK if unlocked else MUTED)
        _text(Vector2(140, y + 38), str(item.get("name", "Conquista")), 19, WHITE if unlocked else MUTED)
        _text(Vector2(140, y + 68), "%s • %s • +R$ %d" % [str(item.get("kind", "achievement")).to_upper(), str(item.get("description", "")), int(item.get("reward", 0))], 14, CYAN if unlocked else MUTED)
        _text(Vector2(565, y + 57), "LIBERADO" if unlocked else "EM ABERTO", 11, GREEN if unlocked else Color("#8091a7"))
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_daily() -> void:
    _draw_ui_background()
    _header("DESAFIOS DIÁRIOS", "R$ %03d" % int(state.get("coins", 0)))
    _text(Vector2(30, 126), "Três objetivos curtos, sem streak punitivo e sem recompensa aleatória.", 15, MUTED)
    var progress: Dictionary = state.get("daily_progress", {})
    var targets: Dictionary = state.get("daily_targets", {"meters": 250, "coins": 10})
    var completed: Array = state.get("daily_completed", [])
    var meter_target := int(targets.get("meters", 250))
    var coin_target := int(targets.get("coins", 10))
    var lines: Array[String] = ["corra %d metros" % meter_target, "pegue %d moedas" % coin_target, "termine sem dano"]
    var ready_flags: Array[bool] = [int(progress.get("meters", 0)) >= meter_target, int(progress.get("coins", 0)) >= coin_target, bool(progress.get("clean", false))]
    var status: Array[String] = ["%dm / %dm" % [mini(int(progress.get("meters", 0)), meter_target), meter_target], "%d / %d moedas" % [mini(int(progress.get("coins", 0)), coin_target), coin_target], "pronto" if bool(progress.get("clean", false)) else "termine sem dano"]
    var titles: Array[String] = ["Pé na tábua", "Troco certo", "Desvia que eu vou"]
    for i in 3:
        var y: float = 200.0 + i * 190.0
        var claimed := i in completed
        var button_label := "RESGATADO" if claimed else ("RESGATAR" if ready_flags[i] else "EM ANDAMENTO")
        var button_color: Color = GREEN if claimed else (YELLOW if ready_flags[i] else Color("#314563"))
        _panel(Rect2(35, y, 650, 145), Color("#214b50") if claimed else Color("#1a2f4e"), 17)
        _text(Vector2(65, y + 43), titles[i], 25, WHITE)
        _text(Vector2(65, y + 78), lines[i], 17, MUTED)
        _text(Vector2(65, y + 116), status[i], 15, GREEN if ready_flags[i] else YELLOW)
        _button(Rect2(505, y + 43, 145, 58), button_label, button_color, 13)
    var weekly: Dictionary = state.get("weekly_progress", {})
    var weekly_target := int(state.get("weekly_target", 2500))
    var weekly_meters := int(weekly.get("meters", 0))
    var weekly_claimed := bool(state.get("weekly_claimed", false))
    var weekly_ready := weekly_meters >= weekly_target
    _panel(Rect2(35, 790, 650, 155), Color("#342d57") if not weekly_claimed else Color("#214b50"), 17)
    _text(Vector2(65, 830), "MARCO SEMANAL", 23, VIOLET if not weekly_claimed else GREEN)
    _text(Vector2(65, 862), "%dm / %dm • objetivo acumulado" % [mini(weekly_meters, weekly_target), weekly_target], 15, MUTED)
    _text(Vector2(65, 900), "sem pressão: o progresso fica até a virada da semana", 13, Color("#c6c5df"))
    _button(Rect2(505, 832, 145, 58), "RESGATADO" if weekly_claimed else ("RESGATAR" if weekly_ready else "EM ANDAMENTO"), GREEN if weekly_claimed else (YELLOW if weekly_ready else Color("#314563")), 12)
    # Lote 17: Baú diário (soft+ Rubi, 1/dia)
    var _chest: Dictionary = state.get("daily_chest", {})
    var _chest_claimed: bool = bool(_chest.get("claimed", false))
    var _chest_soft: int = int(_chest.get("soft", 0))
    var _chest_hard: int = int(_chest.get("hard", 0))
    _panel(Rect2(35, 970, 650, 110), Color("#3a2d1f") if _chest_claimed else Color("#2f3a1f"), 14)
    _text(Vector2(55, 1005), _T("CHEST_TITLE"), 20, YELLOW if not _chest_claimed else MUTED)
    _text(Vector2(55, 1030), (_T("CHEST_CLAIMED") if _chest_claimed else _T("CHEST_REWARD") % [_chest_soft, _chest_hard]) if "%d" in _T("CHEST_REWARD") else "+%d R$ +%d Rubi" % [_chest_soft, _chest_hard], 13, WHITE)
    _button(Rect2(505, 995, 145, 58), _T("CHEST_CLAIMED") if _chest_claimed else _T("CHEST_CLAIM"), GREEN if _chest_claimed else YELLOW, 12)
    _button(Rect2(45, 1110, 630, 70), "VOLTAR", Color("#293955"), 22)

func _draw_how_to() -> void:
    _draw_ui_background()
    _header(_T("HOWTO_TITLE"), _T("HOWTO_SUBTITLE"))
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

func _hud_icon(center: Vector2, kind: String, color: Color) -> void:
    # Ícones vetoriais pequenos e consistentes: mantêm a leitura mesmo sem
    # depender de emoji/fonte externa no Android.
    draw_circle(center, 10.0, Color(color, 0.16))
    draw_arc(center, 9.0, 0.0, TAU, 18, Color(color, 0.65), 1.2)
    match kind:
        "heart":
            draw_circle(center + Vector2(-3, -1), 2.8, color)
            draw_circle(center + Vector2(3, -1), 2.8, color)
            var heart := PackedVector2Array([center + Vector2(-6, 0), center + Vector2(6, 0), center + Vector2(0, 6)])
            draw_colored_polygon(heart, color)
        "coin":
            draw_circle(center, 4.0, color)
            draw_line(center + Vector2(-2, 0), center + Vector2(2, 0), Color("#8b5b18"), 1.0)
        "distance":
            draw_line(center + Vector2(-5, 3), center + Vector2(5, 3), color, 1.5)
            draw_line(center + Vector2(-4, 3), center + Vector2(-1, -3), color, 1.5)
            draw_line(center + Vector2(1, -3), center + Vector2(4, 3), color, 1.5)
        "route":
            draw_line(center + Vector2(-5, 5), center + Vector2(5, -5), color, 1.6)
            draw_circle(center + Vector2(-5, 5), 2.0, color)
            draw_circle(center + Vector2(5, -5), 2.0, color)
        _:
            draw_circle(center, 3.0, color)

func _panel(rect: Rect2, color: Color, radius: float = 12.0) -> void:
    # Painel de vidro fumê: sombra curta, borda fina e reflexo superior dão
    # profundidade sem competir com o cenário 3D.
    var shadow := _make_box(Color(0.005, 0.012, 0.035, 0.58), radius + 1.0)
    shadow.shadow_color = Color(0.0, 0.0, 0.0, 0.30)
    shadow.shadow_size = 5
    shadow.shadow_offset = Vector2(0, 4)
    draw_style_box(shadow, rect)
    draw_style_box(_make_box(color, radius), rect)
    if rect.size.x > radius * 2.0:
        draw_line(rect.position + Vector2(radius, 1), Vector2(rect.end.x - radius, rect.position.y + 1), Color(1, 1, 1, 0.22), 1.0)
        draw_line(rect.position + Vector2(radius + 8, rect.size.y - 2), Vector2(rect.end.x - radius - 8, rect.size.y - 2), Color(0.25, 0.78, 0.86, 0.14), 1.0)

func _button(rect: Rect2, label: String, color: Color, font_size: int = 20) -> void:
    _panel(rect, color, 15)
    draw_rect(Rect2(rect.position + Vector2(4, 4), Vector2(rect.size.x - 8, 3)), Color(1, 1, 1, 0.18))
    draw_line(rect.position + Vector2(14, rect.size.y - 6), rect.end - Vector2(14, 6), Color(0.02, 0.05, 0.1, 0.28), 2)
    _text_center(rect.position + rect.size / 2.0 + Vector2(0, 3), label, font_size, INK if color != Color("#293955") and color != Color("#263958") else WHITE)

func _make_box(color: Color, radius: float) -> StyleBoxFlat:
    var box := StyleBoxFlat.new()
    box.bg_color = color
    box.corner_radius_top_left = int(radius)
    box.corner_radius_top_right = int(radius)
    box.corner_radius_bottom_left = int(radius)
    box.corner_radius_bottom_right = int(radius)
    var high_contrast := bool(state.get("high_contrast", false))
    var border_width := 2 if high_contrast else 1
    var border_alpha := 0.34 if high_contrast else 0.10
    box.border_width_left = border_width
    box.border_width_top = border_width
    box.border_width_right = border_width
    box.border_width_bottom = border_width
    box.border_color = Color(1, 1, 1, border_alpha)
    return box

func _text(pos: Vector2, value: String, font_size: int, color: Color) -> void:
    draw_string(ThemeDB.fallback_font, pos, value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _text_center(pos: Vector2, value: String, font_size: int, color: Color) -> void:
    var width: float = maxf(100.0, float(value.length() * font_size) * 0.72)
    draw_string(ThemeDB.fallback_font, Vector2(pos.x - width / 2.0, pos.y), value, HORIZONTAL_ALIGNMENT_CENTER, width, font_size, color)
