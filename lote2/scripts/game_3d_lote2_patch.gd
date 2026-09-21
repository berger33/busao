# ---------------------------------------------------------------------------
# LOTE 2 - parte que vai DENTRO de scripts/game_3d.gd
#
# Este arquivo e um roteiro de colagem. Ele nao e carregado pelo jogo: serve
# para mostrar exatamente o que acrescentar e o que trocar em game_3d.gd.
# Cada bloco esta marcado com ONDE entra.
# ---------------------------------------------------------------------------


# ===========================================================================
# BLOCO 1 - constantes novas (cole junto das outras constantes do topo)
# ===========================================================================
const RQ_PATH := "/root/RenderQuality"      # autoload do Lote 2
const RENDER_FOV := 49.0                    # era 59.0 (retrato: menos distorcao)
const RENDER_FOV_RUN := 52.0                # era 64/69 na corrida
const RENDER_CAMERA_Y := 2.65               # era 4.85 (camera no ombro, nao no telhado)
const RENDER_CAMERA_Z := 6.2                # era 9.4
const RENDER_CAMERA_FAR := 380.0            # era 125 (deixa a serra/skyline entrar)


# ===========================================================================
# BLOCO 2 - perfil de clima do Lote 2 (cole junto das outras funcoes)
#
# Este dicionario e a unica fonte dos numeros de ceu/luz/camera do Lote 2.
# Quem aplica e o autoload RenderQuality (scripts/render_quality.gd), que
# escolhe sozinho o caminho de cada renderizador e mede o resultado.
# ===========================================================================
func _render_profile() -> Dictionary:
	return {
		"sky_mode": "auto",                       # Forward+ usa ceu fisico; o resto, procedural
		"clouds": 0.3,
		"sky_top": Color(0.32, 0.48, 0.72),       # azul do alto
		"sky_horizon": Color(0.82, 0.80, 0.76),   # horizonte lavado (nevoa)
		"fog_color": Color(0.84, 0.79, 0.70),     # nevoa creme da referencia
		"fog_density": 0.5,
		"fog_begin": 30.0,
		"fog_end": 260.0,
		"sun_rotation": Vector3(-9.0, 170.0, 0.0),  # sol baixo, quase de frente
		"sun_color": Color(1.0, 0.93, 0.80),      # sol creme
		"sun_energy": 1.1,
		"shadow_distance": 68.0,
		"shadow_tint": Color(0.33, 0.39, 0.48),   # sombra azulada da referencia
		"ambient_energy": 0.62,
		"sky_energy": 1.0,
		# 0,51 e a exposicao que a auditoria de tom resolveu para a calcada ao sol
		# cair em ~128/255 (luma da referencia). Confira em tools/audit_render_tone.py.
		"tonemap_white": 1.0,
		"exposure": 0.51,
		"brightness": 1.02,
		"contrast": 1.06,
		"saturation": 0.94,
		"glow": 0.5,
		"fov": RENDER_FOV,
		"far": RENDER_CAMERA_FAR,
		"dof_far": 48.0,
		"dof_transition": 28.0,
		"deband": true,
	}


func _apply_render_quality() -> void:
	var rq := get_node_or_null(RQ_PATH)
	if rq == null:
		return
	rq.apply(_render_profile())


# ===========================================================================
# BLOCO 3 - chamada no fim do _ready()
#
# Procure o final da funcao _ready() (aquela que monta o mundo) e acrescente
# a ultima linha:
# ===========================================================================
# func _ready() -> void:
#     ...codigo antigo...
#     _apply_render_quality()      # <-- LINHA NOVA (Lote 2)
#
# Se o jogo troca de capitulo em outra funcao (a que chama _setup_world() de
# novo), chame _apply_render_quality() TAMBEM no fim dela. O autoload ainda
# reaplica sozinho quando o mundo e refeito, mas a chamada explicita deixa o
# clima do novo capitulo instantaneo.


# ===========================================================================
# BLOCO 4 - camera do jogo (_update_camera)
#
# No trecho onde a camera e posicionada/animada, troque os numeros fixos:
#
#   position = Vector3(..., 4.85, 9.4)   ->  Vector3(..., RENDER_CAMERA_Y, RENDER_CAMERA_Z)
#   fov = 59.0                           ->  fov = RENDER_FOV
#   fov = 64.0  (ou 69.0)                ->  fov = RENDER_FOV_RUN
#   camera.far = 125.0                   ->  camera.far = RENDER_CAMERA_FAR
#
# Se o valor do FOV for calculado com uma conta (ex.: 59.0 + velocidade), troque
# a base 59.0 por RENDER_FOV e mantenha a parcela da velocidade.
#
# Por que: na referencia o personagem ocupa ~1/3 da altura e o ceu aparece no
# terco de cima. Com a camera em 4,85 m de altura e FOV 59 o ceu quase nao
# entra no quadro. Em retrato, KEEP_WIDTH (o autoload configura) faz o FOV
# valer na horizontal, que e o que interessa para enquadrar rua + ceu.
# ===========================================================================


# ===========================================================================
# BLOCO 5 - o que NAO precisa mexer
#
# - _setup_world() continua criando o WorldEnvironment, o ceu, o sol e a
#   camera: o autoload so ajusta os valores depois (e reajusta em toda troca
#   de capitulo).
# - Os materiais PBR do Lote 1 (assets/textures/pbr/) entram no Lote 3, quando
#   as superficies forem refeitas.
# - Nada de PCSS: light_angular_distance e exclusivo do Forward+; no celular a
#   suavidade da sombra vem de shadow_blur, que o autoload ja configura.
# ===========================================================================
