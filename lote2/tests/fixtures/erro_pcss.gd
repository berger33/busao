extends Node
# DEFEITO PLANTADO: PCSS (light_angular_distance) sem a guarda de Forward+.
func _configure_sun(sun: DirectionalLight3D) -> void:
	sun.shadow_blur = 3.0
	sun.light_angular_distance = 0.5
