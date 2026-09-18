extends Node
## RenderQuality - controlador de qualidade de renderizacao (Lote 2).
##
## Instale como autoload chamado "RenderQuality" (Projeto > Configuracoes do
## Projeto > Globais/Autoload). Nao declare class_name para nao conflitar com o
## nome do autoload.
##
## O que ele faz:
##   1. Descobre em tempo de execucao qual renderizador esta ativo
##      (RenderingServer.get_current_rendering_method) e ajusta o que existe:
##      Forward+ liga o que e exclusivo dele, Mobile e Compatibilidade caem para
##      os caminhos equivalentes.
##   2. Monta o clima do Lote 2 no WorldEnvironment: ceu procedural/fisico,
##      ACES, ajustes de cor, glow e nevoa; e ajusta o sol e a camera.
##   3. Cria um degrau de qualidade (escala de renderizacao + MSAA + DOF) que
##      cai quando o FPS cai e volta a subir quando o FPS fica estavel, sempre
##      reaplicando ceu/luz/camera depois de cada troca de cena (Lote 3).
##   4. Mede o resultado: menor luminancia da tela depois do tone mapping e
##      fracao de pixels estourados (prova numerica de que o quadro nao ficou
##      preto nem branco).
##
## Contrato com o jogo (game_3d.gd):
##   var rq := get_node_or_null("/root/RenderQuality")
##   if rq != null:
##       rq.apply(_render_profile())
##
## Fatos do engine conferidos na tag 4.7.2: tools/render_facts.json.

const VERSION := 2

## Janelas do controlador de FPS.
const DOWN_FPS := 52.0          ## abaixo disso: candidato a cair de degrau
const UP_FPS := 58.0            ## acima disso: candidato a subir de degrau
const DOWN_STREAK := 15         ## quadros seguidos ruins antes de cair
const UP_STREAK := 300          ## quadros seguidos bons antes de subir (~5 s)
const COOLDOWN_FRAMES := 150    ## respiro entre trocas de degrau
const MEASURE_WAIT := 30        ## quadros de aquecimento antes de medir
const REAPPLY_DEBOUNCE := 20    ## espera o mundo terminar de montar
const BOTTOM_TIER := 3          ## ultimo degrau (mais leve)

## Degraus de qualidade. "scale" e a escala 3D do viewport, "msaa" usa os
## valores numericos de Viewport.MSAA_* (0 = desligado, 1 = 2x, 2 = 4x),
## "dof" e a quantidade de desfoque de fundo e "sun_blur" a suavidade da sombra.
const TIERS := {
	"forward_plus": [
		{"name": "ultra", "scale": 1.0, "msaa": 2, "dof": 0.85, "sun_blur": 2.4},
		{"name": "alto", "scale": 0.9, "msaa": 1, "dof": 0.6, "sun_blur": 3.2},
		{"name": "medio", "scale": 0.8, "msaa": 0, "dof": 0.0, "sun_blur": 4.0},
		{"name": "leve", "scale": 0.72, "msaa": 0, "dof": 0.0, "sun_blur": 4.6},
	],
	"mobile": [
		{"name": "alto", "scale": 0.95, "msaa": 1, "dof": 0.75, "sun_blur": 3.0},
		{"name": "medio", "scale": 0.85, "msaa": 1, "dof": 0.45, "sun_blur": 3.8},
		{"name": "leve", "scale": 0.75, "msaa": 0, "dof": 0.0, "sun_blur": 4.6},
		{"name": "minimo", "scale": 0.68, "msaa": 0, "dof": 0.0, "sun_blur": 5.0},
	],
	"gl_compatibility": [
		{"name": "alto", "scale": 1.0, "msaa": 0, "dof": 0.0, "sun_blur": 4.0},
		{"name": "medio", "scale": 0.9, "msaa": 0, "dof": 0.0, "sun_blur": 4.4},
		{"name": "leve", "scale": 0.8, "msaa": 0, "dof": 0.0, "sun_blur": 4.8},
		{"name": "minimo", "scale": 0.7, "msaa": 0, "dof": 0.0, "sun_blur": 5.2},
	],
}

## Cores de partida do Lote 2 (a referencia pede sol creme e sombra azulada).
const SUN_CREAM := Color(1.0, 0.93, 0.8)
const SKY_TOP := Color(0.32, 0.48, 0.72)
const SKY_HORIZON := Color(0.82, 0.8, 0.76)
const GROUND_BOTTOM := Color(0.36, 0.35, 0.35)
const GROUND_HORIZON := Color(0.72, 0.69, 0.63)
const FOG_CREAM := Color(0.84, 0.79, 0.7)
const SHADOW_TINT := Color(0.33, 0.39, 0.48)

var _method := "forward_plus"
var _adaptor := "?"
var _api := "?"

var _profile: Dictionary = {}
var _tier_index := 0
var _scale := 1.0
var _active := false
var _applying := false
var _pending := false
var _reapply_wait := 0
var _cooldown := COOLDOWN_FRAMES
var _drop_streak := 0
var _stable_streak := 0
var _measure_attempts := 0
var _min_luma := 1.0
var _blown_ratio := 0.0
var _attributes: CameraAttributesPractical = null
var _sky_signature := ""


func _ready() -> void:
	_method = String(RenderingServer.get_current_rendering_method())
	_adaptor = String(RenderingServer.get_video_adapter_name())
	if RenderingServer.has_method("get_video_adapter_api_version"):
		_api = String(RenderingServer.get_video_adapter_api_version())
	_tier_index = clampi(_tier_index, 0, max(0, _ladder().size() - 1))
	if get_tree() != null:
		get_tree().node_added.connect(_on_node_added)
	print("[render] metodo=%s adaptador='%s' api=%s degrau=%s" % [
		_method, _adaptor, _api, get_tier_name(),
	])


## Unico ponto de entrada do jogo. O dicionario aceita (todos opcionais):
## sky_mode (auto/physical/procedural/keep), clouds, sun_rotation, sun_color,
## sun_energy, shadow_distance, mode_scale (0..1 para pintar o ceu conforme o
## capitulo), fog_color, fog_density, fog_begin, fog_end, exposure, brightness,
## contrast, saturation, glow, fov, far, sky_energy, ambient_energy, deband.
func apply(new_profile: Dictionary) -> void:
	_profile = new_profile.duplicate(true)
	_reapply_wait = REAPPLY_DEBOUNCE
	_cooldown = COOLDOWN_FRAMES


func get_tier_name() -> String:
	return "%s-%s" % [_method, String(_tier().get("name", "?"))]


func get_tier_index() -> int:
	return _tier_index


func get_scale() -> float:
	return _scale


func is_forward_plus() -> bool:
	return _method == "forward_plus"


func get_last_min_luma() -> float:
	return _min_luma


func get_last_blown_ratio() -> float:
	return _blown_ratio


# ---------------------------------------------------------------------------
# Controlador de desempenho
# ---------------------------------------------------------------------------

func _process(_delta: float) -> void:
	if _reapply_wait > 0:
		_reapply_wait -= 1
		if _reapply_wait == 0:
			_run_apply()
		return
	if not _profile.is_empty() and _scale <= 0.0:
		_run_apply()
		return
	if not _active or _applying:
		return
	if _cooldown > 0:
		_cooldown -= 1
		return
	var fps := Engine.get_frames_per_second()
	if fps <= DOWN_FPS:
		_drop_streak += 1
		_stable_streak = 0
	elif fps >= UP_FPS:
		_stable_streak += 1
		_drop_streak = 0
	else:
		_drop_streak = 0
		_stable_streak = 0
	if _drop_streak >= DOWN_STREAK:
		_drop_streak = 0
		_shift_tier(1)
	elif _stable_streak >= UP_STREAK:
		_stable_streak = 0
		_shift_tier(-1)


func _shift_tier(step: int) -> void:
	var ladder := _ladder()
	var novo := clampi(_tier_index + step, 0, ladder.size() - 1)
	if novo == _tier_index:
		return
	_tier_index = novo
	_stable_streak = 0
	_drop_streak = 0
	_cooldown = COOLDOWN_FRAMES
	_pending = false
	_run_apply()


func _on_node_added(node: Node) -> void:
	if node is WorldEnvironment or node is DirectionalLight3D or node is Camera3D:
		_reapply_wait = REAPPLY_DEBOUNCE
		_cooldown = COOLDOWN_FRAMES


# ---------------------------------------------------------------------------
# Fases de aplicacao: pipeline -> mundo -> final (escala + medicao)
# ---------------------------------------------------------------------------

func _run_apply() -> void:
	if _applying:
		_pending = true
		return
	if _profile.is_empty():
		return
	_applying = true
	_pending = false
	_configure_viewport()
	await _wait_frames(2)
	_configure_world(1.0)
	await _wait_frames(MEASURE_WAIT)
	_configure_viewport()
	await _wait_frames(2)
	_measure()
	_measure_attempts = 0
	while _min_luma < 0.42 and _measure_attempts < 2:
		_measure_attempts += 1
		_configure_world(1.0 + 0.25 * float(_measure_attempts))
		await _wait_frames(MEASURE_WAIT)
		_measure()
	_active = true
	_applying = false
	print("[render] pronto: %s escala %.2f luminancia min %.3f" % [
		get_tier_name(), _scale, _min_luma,
	])
	if _pending:
		_pending = false
		_run_apply()


func _wait_frames(count: int) -> void:
	for _i in range(count):
		if get_tree() == null:
			return
		await get_tree().process_frame


func _configure_viewport() -> void:
	var vp := _render_viewport()
	if vp == null:
		return
	var cfg := _tier()
	_scale = float(cfg.get("scale", 1.0))
	vp.use_debanding = bool(_profile.get("deband", true))
	if _method != "gl_compatibility":
		# MSAA 3D e escala 3D existem em Forward+ e Mobile; no caminho de
		# Compatibilidade o jogo segue na resolucao cheia.
		vp.msaa_3d = int(cfg.get("msaa", 0))
		if _tier_index <= 1:
			vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR2
		else:
			vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR
		vp.scaling_3d_scale = clampf(_scale, 0.5, 1.0)


# ---------------------------------------------------------------------------
# Clima do mundo (ceu, ar, sol e camera)
# ---------------------------------------------------------------------------

func _configure_world(boost: float) -> void:
	if _profile.is_empty():
		return
	var we := _find_first("WorldEnvironment") as WorldEnvironment
	if we != null:
		if we.environment == null:
			we.environment = Environment.new()
		_configure_environment(we.environment, boost)
		_sync_camera_attributes(we)
	var sun := _find_first("DirectionalLight3D") as DirectionalLight3D
	if sun != null:
		_configure_sun(sun)
	var cam := _find_first("Camera3D") as Camera3D
	if cam != null:
		_configure_camera(cam)


func _configure_environment(env: Environment, boost: float) -> void:
	_configure_sky(env)
	env.background_mode = Environment.BG_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = float(_profile.get("tonemap_white", 1.0))
	env.tonemap_exposure = float(_profile.get("exposure", 1.0))
	if _method == "forward_plus":
		# Somente Forward+ aceita ambiente vindo do ceu.
		env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		env.ambient_light_sky_contribution = 1.0
		env.ambient_light_energy = float(_profile.get("sky_energy", 1.0))
	else:
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = _color_of("shadow_tint", SHADOW_TINT)
		env.ambient_light_energy = float(_profile.get("ambient_energy", 0.62)) * boost
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.glow_enabled = true
	env.glow_intensity = float(_profile.get("glow", 0.5))
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.glow_hdr_scale = 2.0
	env.glow_hdr_luminance_cap = 12.0
	if _method != "gl_compatibility":
		# glow_strength nao existe no caminho de Compatibilidade.
		env.glow_strength = 1.0
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	var fog := _color_of("fog_color", FOG_CREAM)
	fog = Color(fog.r * boost, fog.g * boost, fog.b * boost, 1.0)
	env.fog_light_color = fog
	env.fog_density = float(_profile.get("fog_density", 0.5))
	env.fog_depth_begin = float(_profile.get("fog_begin", 30.0))
	env.fog_depth_end = float(_profile.get("fog_end", 260.0))
	env.fog_sun_scatter = 0.25
	if _method == "forward_plus":
		env.fog_aerial_perspective = 0.35
	env.adjustment_enabled = true
	env.adjustment_brightness = float(_profile.get("brightness", 1.02))
	env.adjustment_contrast = float(_profile.get("contrast", 1.06))
	env.adjustment_saturation = float(_profile.get("saturation", 0.94))


func _configure_sky(env: Environment) -> void:
	var mode := String(_profile.get("sky_mode", "auto"))
	if mode == "auto":
		mode = "physical" if _method == "forward_plus" else "procedural"
	if mode == "keep":
		return
	var signature := "%s|%s|%s|%s" % [
		mode, _profile.get("sky_top", SKY_TOP),
		_profile.get("sky_horizon", SKY_HORIZON), _profile.get("clouds", 0.3),
	]
	if env.sky != null and env.sky.sky_material != null and signature == _sky_signature:
		return
	var sky := env.sky
	if sky == null:
		sky = Sky.new()
		env.sky = sky
	sky.sky_material = _build_sky_material(mode)
	_sky_signature = signature


func _build_sky_material(mode: String) -> Material:
	if mode == "physical":
		var phys := PhysicalSkyMaterial.new()
		phys.rayleigh_color = _color_of("sky_top", SKY_TOP)
		phys.mie_color = _color_of("fog_color", FOG_CREAM)
		phys.turbidity = 6.0
		phys.mie_coefficient = 0.006
		phys.sun_disk_scale = 1.2
		phys.ground_color = GROUND_HORIZON
		phys.energy_multiplier = 1.0
		phys.use_debanding = true
		return phys
	var proc := ProceduralSkyMaterial.new()
	proc.sky_top_color = _color_of("sky_top", SKY_TOP)
	proc.sky_horizon_color = _color_of("sky_horizon", SKY_HORIZON)
	proc.sky_curve = 0.15
	proc.ground_bottom_color = GROUND_BOTTOM
	proc.ground_horizon_color = GROUND_HORIZON
	proc.ground_curve = 0.08
	proc.sun_angle_max = 6.0
	proc.sun_curve = 0.08
	proc.use_debanding = true
	if _method != "gl_compatibility":
		# nuvens: sky_cover e uma TEXTURA (equirretangular — o nuvens.png do
		# Lote 4, assets/textures/ceu/nuvens.png); a forca da cobertura vai na
		# tinta (sky_cover_modulate), como no WeatherSystem.
		var nuvens_caminho := "res://assets/textures/ceu/nuvens.png"
		var nuvens_tex := ResourceLoader.load(nuvens_caminho) as Texture2D
		if nuvens_tex != null:
			proc.sky_cover = nuvens_tex
			var forca := clampf(float(_profile.get("clouds", 0.3)), 0.0, 1.0)
			proc.sky_cover_modulate = Color(1.0, 0.97, 0.92) * forca
	return proc


func _configure_sun(sun: DirectionalLight3D) -> void:
	sun.rotation_degrees = _profile.get("sun_rotation", Vector3(-9.0, 170.0, 0.0))
	sun.light_color = _color_of("sun_color", SUN_CREAM)
	sun.light_energy = float(_profile.get("sun_energy", 1.1))
	sun.light_specular = 0.35
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = float(_profile.get("shadow_distance", 68.0))
	sun.directional_shadow_split_1 = 0.08
	sun.directional_shadow_split_2 = 0.22
	sun.directional_shadow_split_3 = 0.55
	sun.directional_shadow_blend_splits = true
	sun.directional_shadow_fade_start = 0.9
	sun.directional_shadow_pancake_size = 12.0
	sun.shadow_bias = 0.035
	sun.shadow_normal_bias = 1.0
	sun.shadow_opacity = 0.85
	sun.shadow_blur = float(_tier().get("sun_blur", 3.0))
	sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_AND_SKY
	if _method == "forward_plus":
		# PCSS: exclusivo do Forward+ (Light3D.light_angular_distance).
		# No Mobile/Compatibilidade o valor fica no padrao (0) e a suavidade
		# vem de shadow_blur.
		sun.light_angular_distance = 0.5


func _configure_camera(cam: Camera3D) -> void:
	cam.fov = float(_profile.get("fov", 49.0))
	cam.near = 0.1
	cam.far = float(_profile.get("far", 380.0))
	var vp := _render_viewport()
	if vp != null:
		var size := vp.get_visible_rect().size
		if size.y >= size.x:
			# Retrato usa KEEP_WIDTH (doc do Camera3D).
			cam.keep_aspect = Camera3D.KEEP_WIDTH
	if _method == "gl_compatibility":
		return
	# Os atributos ficam no WorldEnvironment (valem para toda camera sem
	# atributos proprios). Aqui so ajustamos o desfoque se a camera ja tiver
	# atributos proprios definidos pelo jogo.
	var own := cam.attributes as CameraAttributesPractical
	if own == null or own == _attributes:
		return
	_apply_dof(own)


func _sync_camera_attributes(we: WorldEnvironment) -> void:
	if _method == "gl_compatibility":
		return
	if _attributes == null:
		_attributes = CameraAttributesPractical.new()
		if _method == "forward_plus":
			# Auto-exposicao: exclusivo do Forward+ (CameraAttributesPractical).
			_attributes.auto_exposure_enabled = true
			_attributes.auto_exposure_min_sensitivity = 40.0
			_attributes.auto_exposure_max_sensitivity = 400.0
			_attributes.auto_exposure_speed = 0.35
	if we.camera_attributes != _attributes:
		we.camera_attributes = _attributes
	_apply_dof(_attributes)


func _apply_dof(attrs: CameraAttributesPractical) -> void:
	if _method != "gl_compatibility":
		# DOF: so existe em Forward+ e Mobile (CameraAttributesPractical).
		var dof := float(_tier().get("dof", 0.0))
		attrs.dof_blur_amount = dof
		attrs.dof_blur_far_enabled = dof > 0.0
		attrs.dof_blur_far_distance = float(_profile.get("dof_far", 48.0))
		attrs.dof_blur_far_transition = float(_profile.get("dof_transition", 28.0))


# ---------------------------------------------------------------------------
# Medicao (prova numerica do resultado)
# ---------------------------------------------------------------------------

func _measure() -> void:
	var vp := _render_viewport()
	if vp == null:
		return
	var tex := vp.get_texture()
	if tex == null:
		return
	var img := tex.get_image()
	if img == null:
		return
	var w := img.get_width()
	var h := img.get_height()
	if w <= 0 or h <= 0:
		return
	var passo_luma := int(max(1.0, sqrt(float(w * h) / 20000.0)))
	var min_luma := 8.0
	var blown := 0
	var samples := 0
	var y := 0
	while y < h:
		var x := 0
		while x < w:
			var c := img.get_pixel(x, y)
			var l := 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b
			if l < min_luma:
				min_luma = l
			if l > 0.985:
				blown += 1
			samples += 1
			x += passo_luma
		y += passo_luma
	if samples <= 0:
		return
	_min_luma = min_luma
	_blown_ratio = float(blown) / float(samples)
	print("[render] medicao: luminancia min %.3f | estouro %.1f%% | escala %.2f | %s" % [
		_min_luma, _blown_ratio * 100.0, _scale, get_tier_name(),
	])


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

func _ladder() -> Array:
	var key := _method
	if not TIERS.has(key):
		key = "forward_plus"
	return TIERS[key]


func _tier() -> Dictionary:
	var ladder := _ladder()
	var idx := clampi(_tier_index, 0, ladder.size() - 1)
	return ladder[idx]


func _render_viewport() -> Viewport:
	# O viewport que importa e o da camera 3D (funciona tambem se o jogo
	# colocar o mundo dentro de um SubViewport).
	var cam := _find_first("Camera3D") as Camera3D
	if cam != null:
		var vp := cam.get_viewport()
		if vp != null:
			return vp
	return get_viewport()


func _find_first(cls: String) -> Node:
	if get_tree() == null:
		return null
	var found := get_tree().root.find_children("*", cls, true, false)
	if found.is_empty():
		return null
	return found[0]


func _color_of(key: String, fallback: Color) -> Color:
	var value = _profile.get(key, fallback)
	if value is Color:
		return value
	return fallback
