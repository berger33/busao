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
	# 9. Close na personagem — Etapa 2 (WIB-6): a câmera de jogo segue o runner
	# todo frame (lerp com dt) e o card de fase podia vazar no quadro; aqui a
	# tomada é determinística: o countdown assenta, o HUD some, o tempo congela
	# e uma Camera3D própria (virando `current`) faz o close sem tocar no rig
	# de luz nem na câmera de jogo. O WeatherSystem (Lote 4) re-aplica as suas
	# bases capturadas do ready a cada 2 s (sol/névoa/ambiente); o que é da
	# família e persiste aqui: exposição/white do tonemap, pitch da sombra e o
	# fill/rim do rig da personagem (camada dela, sem shadow map).
	_start(0)
	_at(120.0)
	_lane(1, 6)
	await create_timer(1.2).timeout
	if _game.hud != null:
		_game.hud.visible = false
	# Close 3/4 de frente na orbita (yaw ~135 graus): camera a ~5,5 m a
	# frente-direita do runner, olhando o peito. A Camera3D propria da
	# versao anterior saia sem a personagem no quadro (a 1 fps o grab podia
	# pegar o frame previo, antes da nova camera renderizar); na orbita a
	# camera do jogo — que ja renderiza a personagem nas demais tomadas —
	# converge em 1-2 frames.
	_orbit_on(2.35, -0.06)
	await _frames(8)
	var pv: Node3D = _game.player_visual
	print("DIAG close: player_global=", pv.global_position if pv != null else "null",
		" visivel=", pv.visible if pv != null else "-",
		" cam_global=", _game.camera.global_position if _game.camera != null else "null",
		" cam=", _game.camera.name if _game.camera != null else "null")
	await _shot("09_close_personagem")
	_orbit_off()
	if _game.hud != null:
		_game.hud.visible = true
	await _frames(2)

	# 10/11 — os mesmos 4 climas do rig (WIB-6): nublado e chuva FORÇADOS via
	# WeatherSystem (spec re-aplica sol×0.78/0.48, névoa e molhado por cima da
	# base da família), na câmera de jogo: prova de sombra colada no pé e do
	# fill/rim sob luz difusa e sob luz mínima.
	_start(2)
	_at(24.0)
	_lane(1, 2)
	await create_timer(0.8).timeout
	if _game._clima != null:
		_game._clima.set_state("nublado")
	# Settle em relogio de parede: a 1 fps do llvmpipe, 320 frames = 5 min de
	# jogo e o folego expirava no meio da sequencia (o run morria e a tela de
	# carregamento/folego baixo vazava para o quadro).
	await create_timer(5.6).timeout
	await _shot("10_clima_nublado")
	if _game._clima != null:
		_game._clima.set_state("chuva")
	await create_timer(5.6).timeout
	await _shot("11_clima_chuva")
	if _game._clima != null:
		_game._clima.set_state("limpo")
	await create_timer(0.3).timeout
