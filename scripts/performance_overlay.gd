extends Control
## Overlay de QA ativado apenas com a variável BUSAO_PERF=1.
var probe: PerformanceProbe
func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    set_process(true)
func _process(_delta: float) -> void:
    queue_redraw()
func _draw() -> void:
    if probe == null: return
    var snap := probe.snapshot()
    var last: Dictionary = snap.get("last", {})
    var fps := float(snap.get("average_fps", 0.0))
    var ms := float(snap.get("average_frame_ms", 0.0))
    var color := Color("#69e6a4") if fps >= 55.0 else (Color("#ffd166") if fps >= 30.0 else Color("#ff6b6b"))
    draw_rect(Rect2(12, 12, 300, 116), Color(0.02, 0.04, 0.08, 0.88), true)
    draw_string(ThemeDB.fallback_font, Vector2(24, 38), "QA PERFORMANCE", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
    draw_string(ThemeDB.fallback_font, Vector2(24, 62), "FPS %.1f  |  %.1f ms" % [fps, ms], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, color)
    draw_string(ThemeDB.fallback_font, Vector2(24, 84), "Renderer: %s" % str(last.get("renderer", "—")), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("#c6d4e5"))
    draw_string(ThemeDB.fallback_font, Vector2(24, 104), "Resolução: %s" % str(last.get("resolution", "—")), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("#c6d4e5"))
    draw_string(ThemeDB.fallback_font, Vector2(24, 122), "Meta: 60 ideal • 30 mínimo", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, color)
