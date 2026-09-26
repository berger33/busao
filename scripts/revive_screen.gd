extends Control
## ReviveScreen — Lote 16 (Língua)
## Tela "Reviver?" com timer 5 s, botão ASSISTIR (-30s) vs DESISTIR.
## Mock-first: sem SDK, apenas emite sinais; GameAnalytics/Firebase log via AnalyticsManager.

signal watch_requested
signal give_up

const BG := Color("#0b1224")
const PANEL := Color("#14233f")
const YELLOW := Color("#ffd34e")
const RED := Color("#f2635e")
const CYAN := Color("#63e6d2")
const GREEN := Color("#54d18b")
const WHITE := Color("#fff8e7")
const MUTED := Color("#a9b9ca")

var time_left: float = 5.0
var rewarded_ready: bool = false
var _ticking: bool = true

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_STOP
    z_index = 95
    # SafeArea será aplicado pelo parent CanvasLayer via draw_set_transform? Aqui apenas desenha centralizado
    queue_redraw()

func setup(is_ready: bool) -> void:
    rewarded_ready = is_ready
    time_left = 5.0
    _ticking = true
    queue_redraw()

func _process(delta: float) -> void:
    if not _ticking:
        return
    time_left = maxf(0.0, time_left - delta)
    queue_redraw()
    if time_left <= 0.0:
        _ticking = false
        give_up.emit()

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch and event.pressed:
        _handle_tap(event.position)
    elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        _handle_tap(event.position)

func _handle_tap(pos: Vector2) -> void:
    # Botões: ASSISTIR (55, 600, 610, 72) e DESISTIR (55, 690, 610, 72) em coordenadas 720x1280
    # Ajusta para safe area? Aqui usa coordenadas locais já com transform do HUD, mas revive é tela cheia, então usa direto
    var r_watch := Rect2(55, 600, 610, 72)
    var r_give := Rect2(55, 690, 610, 72)
    if r_watch.has_point(pos):
        if not rewarded_ready:
            return
        _ticking = false
        watch_requested.emit()
    elif r_give.has_point(pos):
        _ticking = false
        give_up.emit()

func _T(key: String) -> String:
    if has_node("/root/LocaleManager"):
        var lm = get_node_or_null("/root/LocaleManager")
        if lm and lm.has_method("tr_key"):
            return lm.call("tr_key", key)
    return key

func _draw() -> void:
    # fundo escurecido
    draw_rect(Rect2(Vector2.ZERO, size), Color(0.04, 0.08, 0.17, 0.72))
    # painel central
    var panel_rect := Rect2(35, 260, 650, 520)
    # sombra
    draw_rect(Rect2(panel_rect.position + Vector2(0, 6), panel_rect.size), Color(0.01, 0.025, 0.07, 0.48))
    # painel
    var bg_col := PANEL
    draw_rect(panel_rect, bg_col)
    # borda sutil
    draw_rect(panel_rect, Color(1,1,1,0.08), false, 1.0)
    # título
    var title := _T("REVIVE_TITLE")
    if title == "REVIVE_TITLE":
        title = "VOLTAR AO PONTO?"
    draw_string(ThemeDB.fallback_font, Vector2(55, 320), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 36, YELLOW)
    var desc := _T("REVIVE_DESC")
    if desc == "REVIVE_DESC":
        desc = "o busão quase foi — assista para reviver"
    draw_string(ThemeDB.fallback_font, Vector2(55, 355), desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, MUTED)
    # timer circular / texto
    var timer_str := "%d s" % int(ceilf(time_left))
    # barra de tempo
    var bar_w := 580.0
    var bar_h := 8.0
    var bar_x := 70.0
    var bar_y := 400.0
    draw_rect(Rect2(Vector2(bar_x, bar_y), Vector2(bar_w, bar_h)), Color(0.12, 0.18, 0.28, 1.0))
    draw_rect(Rect2(Vector2(bar_x, bar_y), Vector2(bar_w * (time_left / 5.0), bar_h)), YELLOW if time_left > 1.5 else RED)
    draw_string(ThemeDB.fallback_font, Vector2(360 - 18, 430), timer_str, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, WHITE if time_left > 1.0 else RED)
    draw_string(ThemeDB.fallback_font, Vector2(70, 455), _T("REVIVE_INVINCIBLE") if _T("REVIVE_INVINCIBLE") != "REVIVE_INVINCIBLE" else "5 s invencível após reviver", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, CYAN)
    # botões
    var watch_col := CYAN if rewarded_ready else Color("#314563")
    var watch_label := _T("REVIVE_WATCH")
    if watch_label == "REVIVE_WATCH":
        watch_label = "ASSISTIR (-30s)"
    if not rewarded_ready:
        watch_label = "REVIVER • CARREGANDO..."
    # desenha botão watch
    _draw_button(Rect2(55, 600, 610, 72), watch_label, watch_col, 16)
    draw_string(ThemeDB.fallback_font, Vector2(70, 685), "assista e continue de onde parou", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, MUTED)
    # botão desistir
    _draw_button(Rect2(55, 720, 610, 72), _T("REVIVE_GIVE_UP") if _T("REVIVE_GIVE_UP") != "REVIVE_GIVE_UP" else "DESISTIR", Color("#293955"), 18)
    # dica
    draw_string(ThemeDB.fallback_font, Vector2(70, 770), "só 1 revive por corrida • sem repetir", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.65,0.72,0.8,0.9))
    # contorno timer quando acabando
    if time_left < 1.5:
        draw_rect(panel_rect, RED, false, 2.0)

func _draw_button(rect: Rect2, label: String, color: Color, font_size: int) -> void:
    # sombra
    draw_rect(Rect2(rect.position + Vector2(0, 4), rect.size), Color(0.01,0.025,0.07,0.48))
    draw_rect(rect, color)
    draw_rect(Rect2(rect.position + Vector2(3,3), Vector2(rect.size.x-6, 4)), Color(1,1,1,0.12))
    var ink := Color("#07101f") if color != Color("#293955") and color != Color("#314563") else Color("#fff8e7")
    var tw: float = float(label.length() * font_size) * 0.55
    draw_string(ThemeDB.fallback_font, Vector2(rect.position.x + rect.size.x*0.5 - tw*0.5, rect.position.y + rect.size.y*0.5 + 6), label, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, ink)
