extends Node
# DEFEITO PLANTADO: ambiente vindo do ceu fora do ramo Forward+.
func _configure_environment(env: Environment) -> void:
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
