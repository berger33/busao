extends Control
## LoadingScreen — Lote 14 (Vidro)
## Overlay CanvasLayer para cold start <2.8 s. Mock progress: 0→1 em ~0.9s
## Uso: game_3d.gd instancia em _ready, chama set_progress() e fade_out()
## Design: fundo #0b1224, barra amarela, logo "CORRE PRO PONTO"

const BG := Color("#0b1224")
const PANEL := Color("#14233f")
const YELLOW := Color("#ffd34e")
const WHITE := Color("#fff8e7")
const MUTED := Color("#a9b9ca")

var progress: float = 0.0
var _fade: float = 0.0
var _visible_layer: bool = true

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_STOP
    z_index = 100

func set_progress(p: float) -> void:
    progress = clampf(p, 0.0, 1.0)
    queue_redraw()

func fade_out(duration: float = 0.35) -> void:
    var t := 0.0
    while t < duration:
        t += get_process_delta_time()
        _fade = clampf(t / duration, 0.0, 1.0)
        queue_redraw()
        await get_tree().process_frame
    _visible_layer = false
    visible = false
    queue_free()

func _draw() -> void:
    if not _visible_layer:
        return
    var alpha := 1.0 - _fade
    # fundo
    draw_rect(Rect2(Vector2.ZERO, size), Color(BG.r, BG.g, BG.b, alpha))
    # logo
    var cx := size.x * 0.5
    var cy := size.y * 0.42
    var title := "CORRE"
    var subtitle := "PRO PONTO"
    draw_string(ThemeDB.fallback_font, Vector2(cx - 92, cy - 14), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 62, Color(WHITE.r, WHITE.g, WHITE.b, alpha))
    draw_string(ThemeDB.fallback_font, Vector2(cx - 110, cy + 40), subtitle, HORIZONTAL_ALIGNMENT_LEFT, -1, 52, Color(YELLOW.r, YELLOW.g, YELLOW.b, alpha))
    draw_string(ThemeDB.fallback_font, Vector2(cx - 78, cy + 66), "carregando a avenida...", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(MUTED.r, MUTED.g, MUTED.b, alpha * 0.9))
    # barra
    var bar_w := 420.0
    var bar_h := 10.0
    var bar_x := cx - bar_w * 0.5
    var bar_y := cy + 92
    # track
    draw_rect(Rect2(Vector2(bar_x, bar_y), Vector2(bar_w, bar_h)), Color(0.12, 0.18, 0.28, alpha), true)
    # fill
    draw_rect(Rect2(Vector2(bar_x, bar_y), Vector2(bar_w * progress, bar_h)), Color(YELLOW.r, YELLOW.g, YELLOW.b, alpha), true)
    # borda
    draw_rect(Rect2(Vector2(bar_x, bar_y), Vector2(bar_w, bar_h)), Color(1,1,1, alpha*0.08), false, 1.0)
    # percent
    var pct := "%d%%" % int(progress * 100)
    draw_string(ThemeDB.fallback_font, Vector2(cx - 18, bar_y + 28), pct, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(MUTED.r, MUTED.g, MUTED.b, alpha))
    # dica
    draw_string(ThemeDB.fallback_font, Vector2(cx - 150, size.y - 42), "Dica: desvie dos obstáculos • pegue o ônibus antes da partida!", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(MUTED.r, MUTED.g, MUTED.b, alpha*0.85))
