extends Node
# DEFEITO PLANTADO: MSAA 3D aplicado no caminho de Compatibilidade.
func _configure_viewport() -> void:
	if _method == "gl_compatibility":
		get_viewport().msaa_3d = 1
