class_name BuildingKit
extends RefCounted
## Kit de construcao do cenario (Lote 3).
##
## Le resources/world_spec.json e monta um quarteirao de 28 m com: faixa central
## de lajes, guias, pistas com linha dupla amarela, calcadas laterais, predios,
## arvores, mobiliario e o horizonte lavado pela nevoa.
##
## Regras que o kit segue (e que o auditor cobra):
##   - materiais PBR do Lote 1 via ORMMaterial3D (albedo + normal + ORM);
##   - tudo que se repete (lajes, mosaicos, janelas, postes, folhas) vai em
##     MultiMesh, para nao estourar chamadas de desenho no Adreno 610;
##   - leiaute deterministico: semente fixa por quarteirao (nada de randf solto);
##   - cada superficie recebe nome e meta ("superficie", "colisor") para o Lote 5
##     (fisica) achar o que precisa sem varrer a arvore;
##   - nenhuma medida fixa no codigo: tudo vem do spec.
##
## Uso no jogo:
##   var kit := BuildingKit.ChunkStreamer.new()
##   add_child(kit)
##   kit.setup()
##   kit.update_head(distancia)   # a cada avanco do corredor

const SPEC_PATH := "res://resources/world_spec.json"
const PBR_DIR := "res://assets/textures/pbr/"

## Chaves que o perfil do Lote 2 (RenderQuality.apply) espera receber.
const PERFIL_PADRAO := {
	"sky_mode": "auto",
	"clouds": 0.30,
	"sky_top": Color(0.32, 0.48, 0.72),
	"sky_horizon": Color(0.82, 0.80, 0.76),
	"fog_color": Color(0.84, 0.79, 0.70),
	"fog_density": 0.50,
	"fog_begin": 30.0,
	"fog_end": 260.0,
	"sun_rotation": Vector3(-9.0, 170.0, 0.0),
	"sun_color": Color(1.0, 0.93, 0.80),
	"sun_energy": 1.10,
	"shadow_distance": 68.0,
	"shadow_tint": Color(0.33, 0.39, 0.48),
	"ambient_energy": 0.62,
	"sky_energy": 1.0,
	"tonemap_white": 1.0,
	"exposure": 0.51,
	"brightness": 1.02,
	"contrast": 1.06,
	"saturation": 0.94,
	"glow": 0.50,
	"fov": 49.0,
	"far": 380.0,
	"dof_far": 48.0,
	"dof_transition": 28.0,
	"deband": true,
}

static var _spec_cache: Dictionary = {}
static var _material_cache: Dictionary = {}
static var _avisou_textura := false


# ---------------------------------------------------------------------------
# Especificacao e paleta
# ---------------------------------------------------------------------------

static func load_spec(path: String = SPEC_PATH) -> Dictionary:
	if _spec_cache.has(path):
		return _spec_cache[path]
	var texto := FileAccess.get_file_as_string(path)
	if texto.is_empty():
		push_error("[world] nao consegui ler %s" % path)
		return {}
	var dados = JSON.parse_string(texto)
	if typeof(dados) != TYPE_DICTIONARY:
		push_error("[world] %s nao e um JSON valido" % path)
		return {}
	_spec_cache[path] = dados
	return dados


## Paleta do capitulo (spec.paletas) convertida no perfil que o Lote 2 aplica.
static func chapter_profile(spec: Dictionary, chapter_index: int) -> Dictionary:
	var paletas: Array = spec.get("paletas", [])
	if paletas.is_empty():
		return PERFIL_PADRAO.duplicate(true)
	var paleta: Dictionary = paletas[posmod(chapter_index, paletas.size())]
	var perfil := PERFIL_PADRAO.duplicate(true)
	perfil["sun_color"] = _cor(paleta.get("sol", [1.0, 0.93, 0.80]))
	perfil["fog_color"] = _cor(paleta.get("nevoa", [0.84, 0.79, 0.70]))
	perfil["shadow_tint"] = _cor(paleta.get("sombra", [0.33, 0.39, 0.48]))
	perfil["sky_top"] = _cor(paleta.get("ceu_alto", [0.32, 0.48, 0.72]))
	perfil["sky_horizon"] = _cor(paleta.get("ceu_horizonte", [0.82, 0.80, 0.76]))
	perfil["sun_rotation"] = _vetor(paleta.get("sol_rotacao", [-9.0, 170.0, 0.0]))
	perfil["sun_energy"] = float(paleta.get("sol_energia", 1.1))
	perfil["ambient_energy"] = float(paleta.get("energia_ambiente", 0.62))
	perfil["fog_density"] = float(paleta.get("nevoa_densidade", 0.5))
	perfil["exposure"] = float(paleta.get("exposicao", 0.51))
	perfil["clouds"] = float(paleta.get("nuvens", 0.3))
	var orcamento: Dictionary = spec.get("orcamento", {})
	perfil["shadow_distance"] = float(orcamento.get("sombra_max_m", 68.0))
	return perfil


static func palette_name(spec: Dictionary, chapter_index: int) -> String:
	var paletas: Array = spec.get("paletas", [])
	if paletas.is_empty():
		return "padrao"
	return String(paletas[posmod(chapter_index, paletas.size())].get("nome", "?"))


# ---------------------------------------------------------------------------
# Materiais (PBR do Lote 1)
# ---------------------------------------------------------------------------

static func material(spec: Dictionary, chave: String) -> Material:
	var materiais: Dictionary = spec.get("materiais", {})
	if not materiais.has(chave):
		push_error("[world] material '%s' nao existe no spec" % chave)
		return StandardMaterial3D.new()
	var cache_key := "%d|%s" % [spec.get("seed", 0), chave]
	if _material_cache.has(cache_key):
		return _material_cache[cache_key]
	var cfg: Dictionary = materiais[chave]
	var nome_pbr = cfg.get("pbr", null)
	var mat: BaseMaterial3D
	if nome_pbr != null and _tem_textura(String(nome_pbr)):
		mat = ORMMaterial3D.new()
		mat.albedo_texture = _textura("%s_albedo.png" % nome_pbr)
		mat.normal_enabled = true
		mat.normal_texture = _textura("%s_normal.png" % nome_pbr)
		mat.normal_scale = 0.8
		mat.orm_texture = _textura("%s_orm.png" % nome_pbr)
	else:
		mat = StandardMaterial3D.new()
		if nome_pbr != null and not _avisou_textura:
			_avisou_textura = true
			push_warning("[world] texturas PBR de '%s' ausentes; usando cor plana (rode o Lote 1)" % nome_pbr)
	mat.albedo_color = _cor(cfg.get("cor", [1.0, 1.0, 1.0]))
	if cfg.has("rugosidade"):
		mat.roughness = float(cfg["rugosidade"])
	if cfg.has("metalico"):
		mat.metallic = float(cfg["metalico"])
	var escala := float(cfg.get("uv_escala", 1.0))
	mat.uv1_scale = Vector3(escala, escala, escala)
	mat.uv1_triplanar = bool(cfg.get("triplanar", false))
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_material_cache[cache_key] = mat
	return mat


static func _tem_textura(nome: String) -> bool:
	return ResourceLoader.exists("%s%s_albedo.png" % [PBR_DIR, nome])


static func _textura(arquivo: String) -> Texture2D:
	var caminho := PBR_DIR + arquivo
	var recurso := ResourceLoader.load(caminho)
	if recurso is Texture2D:
		return recurso
	return null


static func _cor(v) -> Color:
	if v is Color:
		return v
	if v is Array and (v as Array).size() >= 3:
		var a: Array = v
		return Color(float(a[0]), float(a[1]), float(a[2]), 1.0)
	return Color.WHITE


static func _vetor(v) -> Vector3:
	if v is Vector3:
		return v
	if v is Array and (v as Array).size() >= 3:
		var a: Array = v
		return Vector3(float(a[0]), float(a[1]), float(a[2]))
	return Vector3.ZERO


# ---------------------------------------------------------------------------
# Malhas e nos auxiliares
# ---------------------------------------------------------------------------

static func _box(size: Vector3) -> BoxMesh:
	var m := BoxMesh.new()
	m.size = size
	return m


static func _cyl(raio: float, altura: float, lados: int = 10) -> CylinderMesh:
	var m := CylinderMesh.new()
	m.top_radius = raio
	m.bottom_radius = raio
	m.height = altura
	m.radial_segments = lados
	m.rings = 1
	return m


static func _sphere(raio: float) -> SphereMesh:
	var m := SphereMesh.new()
	m.radius = raio
	m.height = raio * 2.0
	m.radial_segments = 16
	m.rings = 8
	return m


static func _malha(mesh: Mesh, mat: Material, pos: Vector3, pai: Node3D, nome: String,
		sombra: bool = true, visibilidade: float = 0.0) -> MeshInstance3D:
	var no := MeshInstance3D.new()
	no.name = nome
	no.mesh = mesh
	no.material_override = mat
	no.position = pos
	no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if sombra \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if visibilidade > 0.0:
		no.visibility_range_end = visibilidade
	pai.add_child(no)
	return no


static func _multimesh(mesh: Mesh, mat: Material, xforms: Array, pai: Node3D, nome: String,
		sombra: bool = false, visibilidade: float = 0.0) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
	var no := MultiMeshInstance3D.new()
	no.name = nome
	no.multimesh = mm
	no.material_override = mat
	no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if sombra \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if visibilidade > 0.0:
		no.visibility_range_end = visibilidade
	pai.add_child(no)
	return no


## Fim da calcada lateral (borda de fora), calculado a partir do spec.
static func _x_calcada(faixas: Dictionary) -> float:
	return float(faixas.get("piso_central_m", 4.4)) * 0.5 \
			+ float(faixas.get("guia_largura_m", 0.35)) \
			+ float(faixas.get("pista_m", 8.0)) \
			+ float(faixas.get("guia_largura_m", 0.35)) \
			+ float(faixas.get("calcada_lateral_m", 3.0))


static func _rng(spec: Dictionary, index: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = int(spec.get("seed", 1)) * 7919 + index * 104729
	return r


static func _xform(pos: Vector3, escala: Vector3 = Vector3.ONE, giro_y: float = 0.0) -> Transform3D:
	var b := Basis.from_euler(Vector3(0.0, giro_y, 0.0))
	b = b.scaled(escala)
	return Transform3D(b, pos)


static func _marca(no: Node3D, superficie: String, colisor: String = "estatico") -> void:
	no.set_meta("superficie", superficie)
	no.set_meta("colisor", colisor)


# ---------------------------------------------------------------------------
# Quarteirao
# ---------------------------------------------------------------------------

## Monta um quarteirao completo. base_z e o z local do inicio do trecho.
static func build_chunk(spec: Dictionary, index: int, base_z: float = 0.0) -> Node3D:
	var raiz := Node3D.new()
	raiz.name = "Quarteirao%03d" % index
	raiz.position = Vector3(0.0, 0.0, base_z)
	raiz.set_meta("spec_index", index)
	var faixas: Dictionary = spec.get("faixas", {})
	var rng := _rng(spec, index)
	var comprimento: float = float(spec.get("quarteirao", {}).get("comprimento_m", 28.0)) \
			+ rng.randf_range(-1.0, 1.0) * float(spec.get("quarteirao", {}).get("variacao_comprimento_m", 0.0))
	var visibilidade: float = float(spec.get("orcamento", {}).get("distancia_visibilidade_m", 150.0))

	_build_piso(spec, raiz, comprimento, visibilidade)
	_build_pistas(spec, raiz, comprimento, faixas)
	_build_linhas(spec, raiz, comprimento, faixas)
	_build_lajes(spec, raiz, rng, comprimento, faixas)
	_build_mosaicos(spec, raiz, rng, comprimento, faixas)
	_build_predios(spec, raiz, rng, comprimento)
	_build_arvores(spec, raiz, rng, comprimento)
	_build_mobiliario(spec, raiz, rng, comprimento, faixas, visibilidade)
	_build_folhas(spec, raiz, rng, comprimento, visibilidade)

	var contagem := {"malhas": 0, "multimesh": 0}
	_contar(raiz, contagem)
	print("[world] quarteirao %d: %.1f m, %d malhas (%d multimesh)" % [
		index, comprimento, int(contagem["malhas"]), int(contagem["multimesh"]),
	])
	return raiz


static func _contar(no: Node, contagem: Dictionary) -> void:
	for filho in no.get_children():
		if filho is MultiMeshInstance3D:
			contagem["malhas"] = int(contagem["malhas"]) + 1
			contagem["multimesh"] = int(contagem["multimesh"]) + 1
		elif filho is MeshInstance3D:
			contagem["malhas"] = int(contagem["malhas"]) + 1
		_contar(filho, contagem)


static func _build_piso(spec: Dictionary, raiz: Node3D, comprimento: float, visibilidade: float) -> void:
	var f: Dictionary = spec.get("faixas", {})
	var piso := float(f.get("piso_central_m", 4.4))
	var guia_l := float(f.get("guia_largura_m", 0.35))
	var guia_h := float(f.get("guia_altura_m", 0.15))
	var calcada := float(f.get("calcada_lateral_m", 3.0))
	var pista := float(f.get("pista_m", 8.0))
	var x_guia := piso * 0.5
	var x_pista := x_guia + guia_l
	var x_calcada := x_pista + pista + guia_l

	# base da faixa central (o piso de lajes entra em cima, em _build_lajes)
	var base := _malha(_box(Vector3(piso, 0.35, comprimento)),
			material(spec, "piso_central"), Vector3(0.0, -0.075, -comprimento * 0.5), raiz,
			"FaixaCentral", false, 0.0)
	_marca(base, "piso_central")
	# guias (internas e externas) e calcadas laterais, espelhadas
	for lado in [-1.0, 1.0]:
		var gi := _malha(_box(Vector3(guia_l, 0.40, comprimento)),
				material(spec, "guia"),
				Vector3(lado * (x_guia + guia_l * 0.5), -0.05, -comprimento * 0.5), raiz,
				"GuiaInterna%s" % ("D" if lado > 0.0 else "E"), true, 0.0)
		_marca(gi, "guia")
		var ge := _malha(_box(Vector3(guia_l, 0.40, comprimento)),
				material(spec, "guia"),
				Vector3(lado * (x_calcada - guia_l * 0.5), -0.05, -comprimento * 0.5), raiz,
				"GuiaExterna%s" % ("D" if lado > 0.0 else "E"), true, 0.0)
		_marca(ge, "guia")
		var ca := _malha(_box(Vector3(calcada, 0.35, comprimento)),
				material(spec, "calcada_lateral"),
				Vector3(lado * (x_calcada + calcada * 0.5 - guia_l), -0.075, -comprimento * 0.5), raiz,
				"Calcada%s" % ("D" if lado > 0.0 else "E"), false, 0.0)
		_marca(ca, "calcada_lateral")


static func _build_pistas(spec: Dictionary, raiz: Node3D, comprimento: float, faixas: Dictionary) -> void:
	var piso := float(faixas.get("piso_central_m", 4.4))
	var guia_l := float(faixas.get("guia_largura_m", 0.35))
	var pista := float(faixas.get("pista_m", 8.0))
	var x_pista := piso * 0.5 + guia_l + pista * 0.5
	for lado in [-1.0, 1.0]:
		var no := _malha(_box(Vector3(pista, 0.40, comprimento)),
				material(spec, "pista"),
				Vector3(lado * x_pista, -0.20, -comprimento * 0.5), raiz,
				"Pista%s" % ("D" if lado > 0.0 else "E"), false, 0.0)
		_marca(no, "pista")


static func _build_linhas(spec: Dictionary, raiz: Node3D, comprimento: float, faixas: Dictionary) -> void:
	if String(faixas.get("linha_amarela_modo", "junto_guia")) != "junto_guia":
		return
	var largura := float(faixas.get("linha_amarela_largura_m", 0.12))
	var afast := float(faixas.get("linha_amarela_afastamento_m", 0.30))
	var entre := float(faixas.get("linha_amarela_entre_m", 0.20))
	var piso := float(faixas.get("piso_central_m", 4.4))
	var guia_l := float(faixas.get("guia_largura_m", 0.35))
	var pista := float(faixas.get("pista_m", 8.0))
	var x_int := piso * 0.5 + guia_l
	var x_ext := x_int + pista
	for lado in [-1.0, 1.0]:
		var sufixo := "D" if lado > 0.0 else "E"
		for par in range(2):
			var x := 0.0
			if lado > 0.0:
				x = x_int + afast + largura * 0.5 + float(par) * (largura + entre)
			else:
				x = -(x_ext - afast - largura * 0.5 - float(par) * (largura + entre))
			var nome := "LinhaAmarela%s%d" % [sufixo, par]
			var no := _malha(_box(Vector3(largura, 0.01, comprimento)),
					material(spec, "linha_amarela"),
					Vector3(x, 0.006, -comprimento * 0.5), raiz, nome, false, 0.0)
			_marca(no, "linha_amarela", "nenhum")


static func _build_lajes(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float, faixas: Dictionary) -> void:
	var lajes: Dictionary = spec.get("lajes", {})
	var faixa: Array = lajes.get("tamanho_m", [0.55, 0.80])
	var altura := float(lajes.get("altura_m", 0.05))
	var piso := float(faixas.get("piso_central_m", 4.4))
	var xforms: Array = []
	var x := -piso * 0.5
	var coluna := 0
	while x < piso * 0.5 - 0.05:
		var largura := rng.randf_range(float(faixa[0]), float(faixa[1]))
		largura = min(largura, piso * 0.5 - x)
		var z := 0.0
		var deslocamento := float(lajes.get("junta_m", 0.014))
		if coluna % 2 == 1:
			z = -rng.randf_range(0.15, 0.45)
		while z < comprimento - 0.05:
			var prof := rng.randf_range(float(faixa[0]), float(faixa[1]))
			prof = min(prof, comprimento - z)
			xforms.append(_xform(
				Vector3(x + largura * 0.5, 0.10 + altura * 0.5, -(z + prof * 0.5)),
				Vector3(largura - deslocamento, altura, prof - deslocamento)))
			z += prof + deslocamento
		x += largura + deslocamento
		coluna += 1
	_multimesh(_box(Vector3.ONE), material(spec, "piso_central"), xforms, raiz, "Lajes", false, 0.0)


static func _build_mosaicos(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float, faixas: Dictionary) -> void:
	var lajes: Dictionary = spec.get("lajes", {})
	var lado_m := float(lajes.get("mosaico_lado_m", 0.42))
	var variacao := float(lajes.get("mosaico_variacao_m", 0.06))
	var altura := float(lajes.get("altura_m", 0.05))
	var calcada := float(faixas.get("calcada_lateral_m", 3.0))
	var x_borda := _x_calcada(faixas)
	var xforms: Array = []
	for lado in [-1.0, 1.0]:
		var z := 0.0
		while z < comprimento - 0.05:
			var z_lado := min(lado_m + rng.randf_range(-variacao, variacao), comprimento - z)
			var x := 0.0
			while x < calcada - 0.05:
				var x_lado := min(lado_m + rng.randf_range(-variacao, variacao), calcada - x)
				var x_abs := x_borda - calcada + x + x_lado * 0.5
				xforms.append(_xform(
					Vector3(lado * x_abs, 0.10 + altura * 0.5, -(z + z_lado * 0.5)),
					Vector3(x_lado - 0.01, altura, z_lado - 0.01)))
				x += x_lado + 0.01
			z += z_lado + 0.01
	_multimesh(_box(Vector3.ONE), material(spec, "calcada_lateral"), xforms, raiz, "Mosaicos", false, 0.0)


static func _build_predios(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float) -> void:
	var p: Dictionary = spec.get("predios", {})
	var pisos: Array = p.get("pisos", [2, 3])
	var pe := float(p.get("pe_direito_m", 3.4))
	var variacao := float(p.get("variacao_altura_m", 1.2))
	var largura_lote: Array = p.get("largura_lote_m", [7.0, 12.0])
	var recuo := float(p.get("recuo_calcada_m", 0.35))
	var profundidade := float(p.get("profundidade_m", 9.0))
	var telhado := float(p.get("telhado_altura_m", 0.35))
	var janela: Dictionary = p.get("janela", {})
	var x_frente := _x_calcada(spec.get("faixas", {})) + recuo
	var x_centro := x_frente + profundidade * 0.5
	for lado in [-1.0, 1.0]:
		var z := 0.0
		while z < comprimento - 0.6:
			# o ultimo lote fecha o quarteirao: pode ser estreito, mas nao pode
			# sobrar buraco (a rua ficaria com um vazio no fim do quarteirao)
			var largura := min(rng.randf_range(float(largura_lote[0]), float(largura_lote[1])),
					comprimento - z)
			var tipo := _tipo_predio(p, rng)
			var andares := rng.randi_range(int(pisos[0]), int(pisos[1]))
			var altura := float(andares) * pe + rng.randf_range(-variacao, variacao)
			var chave := "fachada_tijolo"
			if tipo == "reboco":
				chave = "fachada_reboco"
			elif tipo == "loja":
				chave = "fachada_reboco"
			elif tipo == "obra":
				chave = "fachada_reboco"
			var frente := _malha(_box(Vector3(profundidade, altura, largura)),
					material(spec, chave),
					Vector3(lado * x_centro, altura * 0.5, -(z + largura * 0.5)), raiz,
					"Predio%s%d" % ["E", "D"][int(lado > 0.0)], false)
			_marca(frente, "fachada")
			var teto := _malha(_box(Vector3(profundidade + 0.2, telhado, largura + 0.2)),
					material(spec, "telhado"),
					Vector3(lado * x_centro, altura + telhado * 0.5, -(z + largura * 0.5)), raiz,
					"Telhado%s%d" % ["E", "D"][int(lado > 0.0)], false)
			_marca(teto, "telhado")
			if tipo != "obra":
				_build_janelas(spec, raiz, rng, janela, lado, x_frente, z, largura, andares, pe, tipo)
			if tipo == "loja":
				_build_loja(spec, raiz, p, lado, x_frente, z, largura)
			z += largura


static func _tipo_predio(p: Dictionary, rng: RandomNumberGenerator) -> String:
	var pesos: Dictionary = p.get("tipo_pesos", {"tijolo": 1})
	var total := 0
	for k in pesos.keys():
		total += int(pesos[k])
	var escolha := rng.randi_range(1, max(1, total))
	var acumulado := 0
	for k in pesos.keys():
		acumulado += int(pesos[k])
		if escolha <= acumulado:
			return String(k)
	return "tijolo"


static func _build_janelas(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		janela: Dictionary, lado: float, x_frente: float, z: float, largura: float,
		andares: int, pe: float, tipo: String) -> void:
	var jl := float(janela.get("largura_m", 1.2))
	var ja := float(janela.get("altura_m", 1.5))
	var peitoril := float(janela.get("peitoril_m", 0.9))
	var colunas: Array = janela.get("colunas_por_lote", [2, 4])
	var xforms: Array = []
	for andar in range(andares):
		if tipo == "loja" and andar == 0:
			continue  # loja: o pavimento de baixo e vitrine, nao janela
		var colis := rng.randi_range(int(colunas[0]), int(colunas[1]))
		var passo := largura / float(colis + 1)
		for c in range(colis):
			var zc := z + passo * float(c + 1)
			xforms.append(_xform(
				Vector3(lado * (x_frente - 0.03), peitoril + ja * 0.5 + float(andar) * pe, -zc),
				Vector3(0.06, ja, jl)))
	_multimesh(_box(Vector3.ONE), material(spec, "vidro"), xforms, raiz,
			"Janelas%s" % ["E", "D"][int(lado > 0.0)], false)


static func _build_loja(spec: Dictionary, raiz: Node3D, p: Dictionary, lado: float,
		x_frente: float, z: float, largura: float) -> void:
	var loja: Dictionary = p.get("loja", {})
	var altura_toldo := float(loja.get("toldo_altura_m", 2.6))
	var prof := float(loja.get("toldo_profundidade_m", 1.1))
	var porta_l := float(loja.get("porta_largura_m", 1.6))
	var porta_a := float(loja.get("porta_altura_m", 2.4))
	var toldo := _malha(_box(Vector3(prof, 0.12, largura * 0.8)),
			material(spec, "estrutura_metalica"),
			Vector3(lado * (x_frente - prof * 0.5), altura_toldo, -(z + largura * 0.5)), raiz,
			"Toldo%s%d" % ["E", "D"][int(lado > 0.0)], false)
	_marca(toldo, "toldo")
	var porta := _malha(_box(Vector3(0.08, porta_a, porta_l)),
			material(spec, "madeira"),
			Vector3(lado * (x_frente - 0.04), porta_a * 0.5, -(z + largura * 0.5)), raiz,
			"Porta%s%d" % ["E", "D"][int(lado > 0.0)], false)
	_marca(porta, "porta")


static func _build_arvores(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float) -> void:
	var cfg: Dictionary = spec.get("props", {}).get("arvore", {})
	var passo := float(cfg.get("espacamento_m", 8.0))
	var tronco_h := float(cfg.get("tronco_altura_m", 2.4))
	var tronco_r := float(cfg.get("tronco_raio_m", 0.14))
	var copa_r := float(cfg.get("copa_raio_m", 1.7))
	var x := _x_calcada(spec.get("faixas", {})) - 1.5
	var z := rng.randf_range(1.0, passo)
	var lado := 1.0
	while z < comprimento:
		var base := Vector3(lado * x, 0.15, -z)
		var tronco := _malha(_cyl(tronco_r, tronco_h, 8), material(spec, "madeira"),
				base + Vector3(0.0, tronco_h * 0.5, 0.0), raiz, "Tronco", true)
		_marca(tronco, "arvore")
		var copa := _malha(_sphere(copa_r), material(spec, "folhagem"),
				base + Vector3(0.0, tronco_h + copa_r * 0.6, 0.0), raiz, "Copa", true)
		_marca(copa, "folhagem")
		var canteiro := _malha(_box(Vector3(1.1, 0.06, 1.1)), material(spec, "canteiro"),
				Vector3(lado * x, 0.13, -z), raiz, "Canteiro", false)
		_marca(canteiro, "canteiro")
		z += passo * rng.randf_range(0.85, 1.15)
		lado = -lado


static func _build_mobiliario(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float, faixas: Dictionary, visibilidade: float) -> void:
	var props: Dictionary = spec.get("props", {})
	var guia_l := float(faixas.get("guia_largura_m", 0.35))
	var piso := float(faixas.get("piso_central_m", 4.4))
	var x_poste := piso * 0.5 + guia_l * 0.5
	# postes: muitos, entao MultiMesh
	var cfg_poste: Dictionary = props.get("poste", {})
	var passo_poste := float(cfg_poste.get("espacamento_m", 2.2))
	var altura_poste := float(cfg_poste.get("altura_m", 0.95))
	var raio_poste := float(cfg_poste.get("raio_m", 0.06))
	var xforms: Array = []
	var z := 0.4
	while z < comprimento:
		for lado in [-1.0, 1.0]:
			xforms.append(_xform(Vector3(lado * x_poste, 0.15 + altura_poste * 0.5, -z)))
		z += passo_poste
	_multimesh(_cyl(raio_poste, altura_poste, 8), material(spec, "estrutura_metalica"),
			xforms, raiz, "Postes", true, visibilidade)
	# esferas verdes do calcamento direito (o objeto brilhante da referencia)
	var cfg_esfera: Dictionary = props.get("esfera_verde", {})
	var quantas := int(cfg_esfera.get("por_quarteirao", 0))
	for i in range(quantas):
		var zz := rng.randf_range(2.0, comprimento - 2.0)
		var esfera := _malha(_sphere(float(cfg_esfera.get("raio_m", 0.35))),
				material(spec, "esfera_verde"),
				Vector3(_x_calcada(faixas) - 2.2, 0.15 + float(cfg_esfera.get("raio_m", 0.35)), -zz), raiz,
				"EsferaVerde%d" % i, true, visibilidade)
		_marca(esfera, "prop")
	_build_prop_linear(spec, raiz, rng, comprimento, props, "banco", "madeira", 0.45, visibilidade)
	_build_prop_linear(spec, raiz, rng, comprimento, props, "lixeira", "zincado", 0.50, visibilidade)
	if rng.randf() < float(props.get("hidrante", {}).get("probabilidade", 0.0)):
		var zz := rng.randf_range(3.0, comprimento - 3.0)
		var hidrante := _malha(_cyl(0.12, 0.75, 8), material(spec, "estrutura_metalica"),
				Vector3(-(_x_calcada(spec.get("faixas", {})) - 2.0), 0.15 + 0.375, -zz), raiz,
				"Hidrante", true, visibilidade)
		_marca(hidrante, "prop")


static func _build_prop_linear(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float, props: Dictionary, nome: String, material_chave: String,
		altura: float, visibilidade: float) -> void:
	var cfg: Dictionary = props.get(nome, {})
	if cfg.is_empty():
		return
	var passo := float(cfg.get("espacamento_m", 999.0))
	var z := rng.randf_range(2.0, passo)
	while z < comprimento - 1.0:
		var lado := 1.0 if rng.randf() < 0.5 else -1.0
		var x_borda := BuildingKit._x_calcada(spec.get("faixas", {}))
		var no := _malha(_box(Vector3(0.6, altura, 1.6)), material(spec, material_chave),
				Vector3(lado * (x_borda - 1.6), 0.15 + altura * 0.5, -z), raiz, nome.capitalize(),
				true, visibilidade)
		_marca(no, "prop")
		z += passo * rng.randf_range(0.9, 1.2)


static func _build_folhas(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
		comprimento: float, visibilidade: float) -> void:
	var cfg: Dictionary = spec.get("props", {}).get("folhas_no_chao", {})
	var quantas := int(cfg.get("por_quarteirao", 0))
	if quantas <= 0:
		return
	var raio := float(cfg.get("raio_m", 0.05))
	var xforms: Array = []
	for i in range(quantas):
		var x := rng.randf_range(-2.1, 2.1)
		var z := rng.randf_range(0.5, comprimento - 0.5)
		xforms.append(_xform(Vector3(x, 0.155, -z), Vector3.ONE, rng.randf_range(0.0, TAU)))
	_multimesh(_box(Vector3(raio * 2.0, 0.006, raio * 2.0)), material(spec, "folhagem"),
			xforms, raiz, "Folhas", false, visibilidade)


# ---------------------------------------------------------------------------
# Horizonte (skyline lavado pela nevoa)
# ---------------------------------------------------------------------------

static func build_horizon(spec: Dictionary) -> Node3D:
	var raiz := Node3D.new()
	raiz.name = "Horizonte"
	var cfg: Dictionary = spec.get("horizonte", {})
	var rng := _rng(spec, -1)
	var d_min := float(cfg.get("distancia_min_m", 180.0))
	var d_max := float(cfg.get("distancia_max_m", 420.0))
	var alturas: Array = cfg.get("altura_m", [10.0, 34.0])
	var larguras: Array = cfg.get("largura_m", [12.0, 40.0])
	var passo := float(cfg.get("passo_m", 24.0))
	var lado := float(cfg.get("lado_m", 34.0))
	var nevoa := float(cfg.get("nevoa", 0.78))
	var paletas: Array = spec.get("paletas", [])
	var nevoa_cor := Color(0.84, 0.79, 0.70)
	if not paletas.is_empty():
		nevoa_cor = _cor(paletas[0].get("nevoa", [0.84, 0.79, 0.70]))
	var cor := _misturar(nevoa_cor, Color(0.55, 0.58, 0.62), nevoa)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = cor
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	var d := d_min
	while d <= d_max:
		var altura := rng.randf_range(float(alturas[0]), float(alturas[1]))
		var largura := rng.randf_range(float(larguras[0]), float(larguras[1]))
		var x := rng.randf_range(-lado, lado)
		var no := MeshInstance3D.new()
		no.name = "BlocoHorizonte"
		no.mesh = _box(Vector3(largura, altura, largura))
		no.material_override = mat
		no.position = Vector3(x, altura * 0.5, -d)
		no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		raiz.add_child(no)
		if rng.randf() < float(cfg.get("caixa_dagua_probabilidade", 0.0)):
			var caixa := MeshInstance3D.new()
			caixa.name = "CaixaDagua"
			caixa.mesh = _cyl(1.6, 2.4, 10)
			caixa.material_override = mat
			caixa.position = Vector3(x, altura + 1.2, -d)
			caixa.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			raiz.add_child(caixa)
		d += passo * rng.randf_range(0.8, 1.3)
	return raiz


static func _misturar(a: Color, b: Color, t: float) -> Color:
	return a.lerp(b, clampf(t, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Fluxo de quarteiroes (recicla os nos, sem alocar a cada avanco)
# ---------------------------------------------------------------------------

class ChunkStreamer extends Node3D:
	var spec: Dictionary = {}
	var comprimento_m: float = 28.0
	var visiveis: int = 5
	var horizonte: Node3D = null
	var _chunks: Array = []
	var _proximo: int = 0

	func setup(caminho_spec: String = "res://resources/world_spec.json") -> void:
		name = "Cenario"
		spec = BuildingKit.load_spec(caminho_spec)
		comprimento_m = float(spec.get("quarteirao", {}).get("comprimento_m", 28.0))
		visiveis = int(spec.get("quarteirao", {}).get("quarteiroes_visiveis", 5))
		horizonte = BuildingKit.build_horizon(spec)
		add_child(horizonte)
		for i in range(visiveis):
			var no := BuildingKit.build_chunk(spec, i, -float(i) * comprimento_m)
			_chunks.append(no)
			add_child(no)
		_proximo = visiveis

	## Chame a cada avanco do corredor (o mesmo ponto onde o jogo move o mundo).
	func update_head(distancia: float) -> void:
		var primeiro := int(floor(distancia / comprimento_m)) - 1
		for no in _chunks:
			var indice := int(no.get_meta("spec_index", 0))
			if indice < primeiro:
				_reconstruir(no, _proximo)
				_proximo += 1

	func _reconstruir(no: Node3D, indice: int) -> void:
		for filho in no.get_children():
			filho.queue_free()
			no.remove_child(filho)
		var novo := BuildingKit.build_chunk(spec, indice, -float(indice) * comprimento_m)
		no.set_meta("spec_index", indice)
		no.name = novo.name
		for filho in novo.get_children():
			novo.remove_child(filho)
			no.add_child(filho)
		novo.queue_free()

	func paleta_do_capitulo(indice: int) -> Dictionary:
		return BuildingKit.chapter_profile(spec, indice)
