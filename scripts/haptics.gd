class_name Haptics
extends RefCounted
## Vibracao tatica (Android/iOS) para dano, derrota e marcos.
## Respeita `reduced_motion` (acessibilidade) e so vibra no OS real:
## no editor/desktop e no-op seguro. Acesso ao save via SceneTree (statico).

static func _save_node() -> Node:
    var loop := Engine.get_main_loop()
    if loop == null or not (loop is SceneTree):
        return null
    return (loop as SceneTree).root.get_node_or_null("/root/GameSave")

static func _allowed() -> bool:
    if not (OS.has_feature("android") or OS.has_feature("ios")):
        return false
    var save := _save_node()
    if save != null:
        var data: Dictionary = save.get("data")
        if bool(data.get("reduced_motion", false)):
            return false
    return true

static func tap() -> void:
    if _allowed():
        Input.vibrate_handheld(15)

static func damage() -> void:
    if _allowed():
        Input.vibrate_handheld(60)

static func defeat() -> void:
    if _allowed():
        Input.vibrate_handheld(120)

static func milestone() -> void:
    if _allowed():
        Input.vibrate_handheld(35)

static func boarding() -> void:
    if _allowed():
        Input.vibrate_handheld(50)
