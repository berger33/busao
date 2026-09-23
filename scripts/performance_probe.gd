class_name PerformanceProbe
extends Node
## Telemetria leve para QA: não altera a lógica da corrida.

var elapsed := 0.0
var frames := 0
var frame_sum := 0.0
var worst_frame := 0.0
var samples: Array[Dictionary] = []
var sample_interval := 1.0

func _process(delta: float) -> void:
    elapsed += delta
    frames += 1
    frame_sum += delta
    worst_frame = maxf(worst_frame, delta)
    if elapsed >= sample_interval:
        var avg := frame_sum / maxf(1.0, float(frames))
        samples.append({
            "fps": 1.0 / maxf(0.0001, avg),
            "frame_ms": avg * 1000.0,
            "worst_frame_ms": worst_frame * 1000.0,
            "renderer": str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "unknown")),
            "resolution": "%dx%d" % [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
        })
        if samples.size() > 120:
            samples.pop_front()
        elapsed = 0.0
        frames = 0
        frame_sum = 0.0
        worst_frame = 0.0

func snapshot() -> Dictionary:
    if samples.is_empty():
        return {"samples": 0, "status": "aguardando corrida"}
    var last: Dictionary = samples.back()
    return {"samples": samples.size(), "last": last, "average_fps": _average("fps"), "average_frame_ms": _average("frame_ms")}

func _average(key: String) -> float:
    var total := 0.0
    for sample in samples:
        total += float(sample.get(key, 0.0))
    return total / maxf(1.0, float(samples.size()))
