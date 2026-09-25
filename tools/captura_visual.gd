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
	# Guard fatal: se algum script do jogo falhou ao compilar, a cena
	# instancia "oca" (sem métodos) e as capturas saem sem o jogo — já
	# aconteceu com SpotLight vs SpotLight3D no CI. Não aceitar PNGs ocos.
	if _game == null or not _game.has_method("_start_run"):
		print("CAPTURA_FALHOU: main.tscn instanciou sem game_3d.gd funcional (script não compilou?)")
		quit(1)
		return
	root.add_child(_game)
	await process_frame
	await process_frame
	_silenciar_iaa()
	_diag_luz()
	_unlock_all()
	await _tomadas()
	print("CAPTURA_OK")
	quit(0)


## Diagnóstico de sombras/iluminação impresso no _log.txt do CI: responde de
## vez por que as capturas saem sem sombras direcionais (sol/ambiente/cast
## shadow/tier reais em runtime, não o que o código "acha" que configurou).
func _diag_luz() -> void:
	print("DIAG metodo: ", RenderingServer.get_current_rendering_method(),
		" driver: ", RenderingServer.get_current_rendering_driver_name())
	for s in _game.find_children("*", "DirectionalLight3D", true, false):
		print("DIAG luz: ", s.name, " visivel=", s.visible,
			" sombra=", s.shadow_enabled, " energia=", s.light_energy,
			" rot=", s.rotation_degrees, " max_dist=", s.directional_shadow_max_distance)
	for w in _game.find_children("*", "WorldEnvironment", true, false):
		var env = w.environment
		if env == null:
			continue
		print("DIAG env: ", w.name,
			" amb_src=", env.ambient_light_source,
			" amb_energy=", env.ambient_light_energy,
			" amb_color=", env.ambient_light_color,
			" bg_src=", env.background_mode,
			" fog=", env.fog_enabled, " fog_density=", env.fog_density,
			" glow=", env.glow_enabled, " glow_int=", env.glow_intensity)
	for p in _game.find_children("PredioD0", "", true, false):
		print("DIAG predio: ", p.name, " cast_shadow=", p.cast_shadow)
	for p in _game.find_children("Copa", "", true, false):
		print("DIAG copa: ", p.name, " cast_shadow=", p.cast_shadow)
		break
	for p in _game.find_children("Deck*", "", true, false):
		print("DIAG deck: ", p.name, " receive=", p.cast_shadow)
		break


func _unlock_all() -> void:
	var save: Node = _game.get_node("/root/GameSave")
	for i in range(0, 50):
		save.call("record_phase", i, 3, 10.0)


## IAA mock: no CI (sem singleton nativo) o manager "acha e baixa" um update
## alguns segundos apos o boot e o `update_downloaded` vaza o toast
## "ATUALIZACAO PRONTA" para os quadros. A captura desconecta os sinais e
## zera o timer do mock: nenhum toast de IAA aparece em tomada alguma.
func _silenciar_iaa() -> void:
	var up: Node = root.get_node_or_null("/root/InAppUpdateManager")
	if up == null:
		print("DIAG iaa: manager ausente (nada a silenciar)")
		return
	for sig_name in ["update_available", "update_downloaded", "update_failed", "update_installed"]:
		if not up.has_signal(sig_name):
			continue
		var sig: Signal = up.get(sig_name)
		for con in sig.get_connections():
			sig.disconnect(con["callable"])
			print("DIAG iaa: desconectado ", sig_name)
	if "_mock_timer" in up:
		up.set("_mock_timer", 0.0)
	print("DIAG iaa: mock silenciado")


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
	_medir_silhueta(img, nome)


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


## Modo captura (Lote 6): a camera do jogo orbita o runner e mira em
## player_x direto. O follow amortiza a faixa (x*0.16) e, em faixa lateral,
## deixa a personagem na borda do quadro — a orbita a centraliza.
func _orbit_on(yaw: float, pitch: float) -> void:
	_game._capture_mode = true
	_game._capture_yaw = yaw
	_game._capture_pitch = pitch


func _orbit_off() -> void:
	_game._capture_mode = false


func _tomadas() -> void:
	# 1. Largada — corredor C, rua do Ipê à frente.
	_start(0)
	_at(10.0)
	_lane(1)
	await _shot("01_largada_fase1")
	# 2. Corrida no meio — obstáculos e moedas à frente.
	# O fade do loader corre em relogio de parede: a 1 fps do llvmpipe,
	# esperar so frames nao e suficiente para o fade terminar (no run
	# anterior o titulo + "100%" vazaram no quadro 02).
	await create_timer(4.0).timeout
	_at(52.0)
	await _shot("02_corrida_fase1")
	# 3. Rua (corredor E) com tráfego e travessia do caminhão (fase 18).
	# Orbita (modo captura): o follow amortiza a faixa (x*0.16) e deixaria a
	# personagem na borda esquerda em E; a orbita mira em player_x direto.
	_start(17)
	_lane(0)
	_orbit_on(0.0, -0.12)
	_at(58.0, 4)
	await _frames(24)
	await _shot("03_rua_travessia_fase18")
	_orbit_off()
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
	# 9. Close 3/4 de frente — Etapa 2 (WIB-6).
	# Aos 120 m a runner apanhava, hearts caía a 0 e o pisca de
	# invulnerabilidade NÃO restaurava player_visual.visible (game_3d
	# 1414-1417). O set anterior saiu com visivel=false e a câmera a 6 m,
	# alta demais para ler o rig. Aqui: rua curta (ela sobrevive), clima
	# limpo assentado, órbita grudada no peito, visibilidade forçada e
	# _process congelado para o pisca não apagá-la no grab.
	_start(0)
	_at(36.0, 8)
	_lane(1, 6)
	_restaurar_runner()
	_clima_para("limpo")
	if _game.hud != null:
		_game.hud.visible = false
	if _game._revive_screen != null:
		_game._revive_screen.visible = false
	_game._revive_pending = false
	# yaw 2.2 rad: a câmera de jogo fica em +Z (costas). cos(2.2)<0 põe a
	# órbita em −Z, que é a frente. Raio 2.7 m e altura 0.42 = peito, 3/4.
	_game._capture_radius = 2.7
	_game._capture_height = 0.42
	_orbit_on(2.2, -0.05)
	_game._snap_capture_camera()
	await _frames(6)
	_restaurar_runner()
	if _game._revive_screen != null:
		_game._revive_screen.visible = false
	_game.set_process(false)
	_game.set_physics_process(false)
	_diag_close()
	await _shot("09_close_personagem")
	_game.set_process(true)
	_game.set_physics_process(true)
	_game._capture_radius = 6.2
	_game._capture_height = 2.0
	_orbit_off()
	if _game.hud != null:
		_game.hud.visible = true
	await _frames(2)

	# 10/11 — nublado e chuva ASSENTADOS (snap), não no meio do lerp de 5 s
	# de jogo. A 1 fps o set_state nunca chegava no alvo (molhado 0.23 / 0.14
	# no set anterior) e o céu continuava o panorama de sol.
	_start(2)
	_at(28.0, 6)
	_lane(1, 4)
	_restaurar_runner()
	_clima_para("nublado")
	await create_timer(2.4).timeout
	_diag_close()
	await _shot("10_clima_nublado")
	_clima_para("chuva")
	await create_timer(2.8).timeout
	_diag_close()
	await _shot("11_clima_chuva")
	_clima_para("limpo")
	await create_timer(0.3).timeout


func _restaurar_runner() -> void:
	_game.hearts = maxi(int(_game.hearts), 3)
	_game.invulnerability = 0.0
	var pv: Node3D = _game.player_visual
	if pv != null:
		pv.visible = true


## Snap do WeatherSystem + família de luz no mesmo frame. O reapply do clima
## (2 s de jogo) não alcança a tomada: a 1 fps isso seria ~40 s de parede.
func _clima_para(nome: String) -> void:
	if _game._clima != null and _game._clima.has_method("snap_state"):
		_game._clima.snap_state(nome)
	if _game.has_method("_apply_scenario_atmosphere"):
		_game._apply_scenario_atmosphere()
	if _game._clima != null:
		_game._clima.set("_tempo_reassert", 2.0)


func _diag_close() -> void:
	var pv: Node3D = _game.player_visual
	var sol: DirectionalLight3D = _game.sun
	print("DIAG close: visivel=", pv.visible if pv != null else "-",
		" hearts=", _game.hearts,
		" player=", pv.global_position if pv != null else "null",
		" cam=", _game.camera.global_position if _game.camera != null else "null")
	if sol != null:
		print("DIAG sol: e=", sol.light_energy, " pitch=", sol.rotation_degrees.x,
			" yaw=", sol.rotation_degrees.y, " bias=", sol.shadow_normal_bias)
	for nome_luz in ["RunnerFill", "RunnerRim", "RunnerLift", "RunnerFront"]:
		var luz: Node = _game.find_child(nome_luz, true, false)
		if luz != null and luz is Light3D:
			print("DIAG rig: ", nome_luz, " e=", (luz as Light3D).light_energy, " vis=", luz.visible)


func _rel_lum(valor: float) -> float:
	var s := clampf(valor / 255.0, 0.0, 1.0)
	if s <= 0.04045:
		return s / 12.92
	return pow((s + 0.055) / 1.055, 2.4)


## Contraste da camisa (rosa) contra a rua ao lado. Meta WIB-6: ≥ 3:1.
## Estouro = fração de pixels com luminância > 245 (exposição estourada).
func _medir_silhueta(img: Image, nome: String) -> void:
	var w := img.get_width()
	var h := img.get_height()
	var shirt_sum := 0.0
	var shirt_n := 0
	var min_x := w
	var max_x := 0
	var min_y := h
	var max_y := 0
	var blown := 0
	var amostras := 0
	for y in range(0, h, 4):
		for x in range(0, w, 4):
			amostras += 1
			var c := img.get_pixel(x, y)
			var rl := (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) * 255.0
			if rl > 245.0:
				blown += 1
			if y < int(h * 0.28) or y > int(h * 0.82):
				continue
			if x < int(w * 0.12) or x > int(w * 0.88):
				continue
			var r := c.r * 255.0
			var g := c.g * 255.0
			var b := c.b * 255.0
			if r > 72.0 and r > g + 16.0 and r > b + 8.0 and g < 190.0 and b < 175.0:
				shirt_n += 1
				shirt_sum += rl
				min_x = mini(min_x, x)
				max_x = maxi(max_x, x)
				min_y = mini(min_y, y)
				max_y = maxi(max_y, y)
	var blown_pct := 100.0 * float(blown) / float(maxi(1, amostras))
	if shirt_n < 15:
		print("SILHUETA %s sem_camisa n=%d estouro=%.2f%%" % [nome, shirt_n, blown_pct])
		return
	var shirt_lum := shirt_sum / float(shirt_n)
	var bg_sum := 0.0
	var bg_n := 0
	var y1 := mini(h - 1, max_y + int(float(max_y - min_y) * 0.85))
	for y2 in range(min_y, y1, 3):
		for x2 in range(maxi(0, min_x - 42), maxi(0, min_x - 6), 3):
			var amostra := _lum_rua(img, x2, y2)
			if amostra < 0.0:
				continue
			bg_sum += amostra
			bg_n += 1
		for x3 in range(mini(w - 1, max_x + 6), mini(w, max_x + 42), 3):
			var amostra_dir := _lum_rua(img, x3, y2)
			if amostra_dir < 0.0:
				continue
			bg_sum += amostra_dir
			bg_n += 1
	if bg_n < 8:
		print("SILHUETA %s camisa=%.1f sem_fundo n=%d estouro=%.2f%%" % [nome, shirt_lum, shirt_n, blown_pct])
		return
	var bg_lum := bg_sum / float(bg_n)
	var rs := _rel_lum(shirt_lum)
	var rb := _rel_lum(bg_lum)
	var ratio := (maxf(rs, rb) + 0.05) / (minf(rs, rb) + 0.05)
	print("SILHUETA %s ratio=%.2f camisa=%.1f rua=%.1f n=%d estouro=%.2f%%" % [
		nome, ratio, shirt_lum, bg_lum, shirt_n, blown_pct])


func _lum_rua(img: Image, x: int, y: int) -> float:
	var c := img.get_pixel(x, y)
	var r := c.r * 255.0
	var g := c.g * 255.0
	var b := c.b * 255.0
	if r > 72.0 and r > g + 16.0 and r > b + 8.0:
		return -1.0
	return 0.2126 * r + 0.7152 * g + 0.0722 * b
