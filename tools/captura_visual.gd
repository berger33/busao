extends SceneTree
## Captura visual — renderiza quadros REAIS do jogo sob Xvfb (software GL)
## e grava PNGs em res://captures/ para revisão de direção de arte.
## Rodar (workflow screenshots.yml / local com display):
##   xvfb-run -a -s "-screen 0 800x1400x24" godot --path . \
##     --rendering-method gl_compatibility --rendering-driver opengl3 \
##     --resolution 720x1280 --script tools/captura_visual.gd
## Determinístico: sem entrada do usuário; o estado de cada tomada é montado
## por distância/elapsed (o mesmo mecanismo das suítes qa_etapa*).
## Código de saída 0 = capturas gravadas.

const SHOT_DIR := "res://captures"

var _game = null
var _spd := 8.0


func _initialize() -> void:
	print("== CAPTURA VISUAL (frames reais do engine) ==")
	DirAccess.make_dir_recursive_absolute(SHOT_DIR)
	var packed: PackedScene = load("res://scenes/main.tscn")
	_game = packed.instantiate()
	root.add_child(_game)
	await process_frame
	await process_frame
	_unlock_all()
	await _tomadas()
	print("CAPTURA_OK")
	quit(0)


func _unlock_all() -> void:
	var save: Node = _game.get_node("/root/GameSave")
	for i in range(0, 50):
		save.call("record_phase", i, 3, 10.0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(nome: String) -> void:
	# process_frame (e não frame_post_draw): o rasterizer dummy do headless
	# nunca emite frame_post_draw e o await penduraria; sob Xvfb o texture
	# da janela já contém o quadro anterior desenhado. A janela pode levar
	# alguns frames para materializar a textura após o boot — insiste até 60.
	var img: Image = null
	var dummy := RenderingServer.get_current_rendering_driver_name() == "dummy"
	for tentativa in range(2 if dummy else 60):
		await process_frame
		if tentativa < 1 or dummy:
			continue
		var tex: Texture2D = root.get_texture()
		if tex == null:
			continue
		img = tex.get_image()
		if img != null and not img.is_empty():
			break
		img = null
	if img == null:
		print("  shot %s: sem imagem de janela após 60 frames (dummy rasterizer?) — pulado" % nome)
		return
	var caminho := SHOT_DIR + "/" + nome + ".png"
	var err := img.save_png(caminho)
	print("  shot %s: %s (err=%d, %dx%d)" % [nome, caminho, err, img.get_width(), img.get_height()])


func _start(index: int) -> void:
	print("  -- tomada fase %d" % (index + 1))
	_game._start_run(index)
	if _game.run_director != null:
		_game.run_director.countdown_left = 0.0
	_spd = _game._phase_speed_for(index)
	await _frames(6)


func _at(dist: float, settle: int = 5) -> void:
	_game.distance = dist
	_game.elapsed = dist / _spd
	await _frames(settle)


func _lane(l: int, settle: int = 10) -> void:
	_game.player_lane = l
	await _frames(settle)


func _tomadas() -> void:
	# 1. Largada — corredor C, rua do Ipê à frente.
	_start(0)
	_at(10.0)
	_lane(1)
	await _shot("01_largada_fase1")
	# 2. Corrida no meio — obstáculos e moedas à frente.
	_at(52.0)
	await _shot("02_corrida_fase1")
	# 3. Rua (corredor E) com tráfego e travessia do caminhão (fase 18).
	_start(17)
	_lane(0)
	_at(58.0, 4)
	await _frames(24)
	await _shot("03_rua_travessia_fase18")
	# 4. Passagem de pedestres (fase 7) vista do corredor C.
	_start(6)
	_lane(1)
	_at(62.0, 4)
	await _frames(24)
	await _shot("04_pedestres_fase7")
	# 5. Calçada D com props/feira e deck (fase 9).
	_start(8)
	_lane(2)
	_at(46.0)
	await _shot("05_calcada_d_fase9")
	# 6. Chegada: o ônibus no ponto em frente ao abrigo (fase 20).
	_start(19)
	_lane(1)
	_at(_game.run_total - 10.0, 4)
	for i in range(90):
		await process_frame
		if String(_game.run_mode) != "playing":
			break
	await _frames(24)
	await _shot("06_chegada_onibus_fase20")
	# 7. Ponto da igreja (fase 25) — marco arquitetônico + paleta do nível.
	_start(24)
	_lane(1)
	_at(_game.run_total - 42.0, 8)
	await _shot("07_ponto_igreja_fase25")
	# 8. Final da campanha (fase 50): embarque dourado + terminal.
	_start(49)
	_lane(1)
	_at(_game.run_total - 12.0, 4)
	for i in range(90):
		await process_frame
		if String(_game.run_mode) != "playing":
			break
	await _frames(24)
	await _shot("08_final_fase50")
	# 9. Close na personagem (câmera congelada perto do runner).
	_start(0)
	_at(30.0)
	_lane(1, 6)
	Engine.time_scale = 0.02
	var pv: Node3D = _game.player_visual
	if pv != null and _game.camera != null:
		var alvo: Vector3 = pv.global_position + Vector3(0.0, 1.15, 0.0)
		_game.camera.global_position = pv.global_position + Vector3(1.35, 1.35, 1.9)
		_game.camera.look_at(alvo, Vector3.UP)
	await _frames(3)
	await _shot("09_close_personagem")
	Engine.time_scale = 1.0
