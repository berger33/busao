extends Node
# DEFEITO PLANTADO: paleta da referencia trocada por cores frias.
const SUN_CREAM := Color(0.60, 0.75, 0.95)
const SHADOW_TINT := Color(0.55, 0.70, 0.90)
func _configure_environment(env: Environment) -> void:
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
