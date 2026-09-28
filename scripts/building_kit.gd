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
    "clouds": 0.18,
    "sky_top": Color(0.18, 0.52, 0.92),
    "sky_horizon": Color(0.78, 0.86, 0.96),
    "fog_color": Color(0.88, 0.92, 0.98),
    "fog_density": 0.002,
    "fog_begin": 80.0,
    "fog_end": 600.0,
    "sun_rotation": Vector3(-42.0, 160.0, 0.0),
    "sun_color": Color(1.0, 0.96, 0.88),
    "sun_energy": 1.45,
    "shadow_distance": 90.0,
    "shadow_tint": Color(0.48, 0.54, 0.65),
    "ambient_energy": 1.15,
    "sky_energy": 1.25,
    "tonemap_white": 1.0,
    "exposure": 0.52,
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

## ETAPA 5 — spec base com overrides profundos (fase autoral referencia o
## proprio perfil de cenario, ex.: Rua do Ipe com deck de tres corredores e
## ipe amarelo). O spec em disco nao muda; nada e mutado no cache.
static func spec_with_overrides(base: Dictionary, overrides: Dictionary) -> Dictionary:
    if overrides.is_empty():
        return base
    var resultado: Dictionary = base.duplicate(true)
    _mesclar_spec(resultado, overrides)
    return resultado


static func _mesclar_spec(alvo: Dictionary, fonte: Dictionary) -> void:
    for chave in fonte:
        if typeof(fonte[chave]) == TYPE_DICTIONARY and typeof(alvo.get(chave)) == TYPE_DICTIONARY:
            _mesclar_spec(alvo[chave], fonte[chave])
        else:
            alvo[chave] = fonte[chave]


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
        mat.normal_scale = float(cfg.get("normal_scale", 1.0))
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
    if mat is StandardMaterial3D and cfg.has("normal_scale") and mat.normal_enabled:
        mat.normal_scale = float(cfg["normal_scale"])
    var escala := float(cfg.get("uv_escala", 1.0))
    mat.uv1_scale = Vector3(escala, escala, escala)
    mat.uv1_triplanar = bool(cfg.get("triplanar", false))
    # L27 polimento: triplanar world + sharpness (spec world_spec.json L22)
    if bool(cfg.get("triplanar", false)):
        mat.uv1_world_triplanar = true
        var sharp := float(cfg.get("triplanar_sharpness", 3.0))
        if sharp > 0.0:
            mat.uv1_triplanar_sharpness = sharp
        else:
            mat.uv1_triplanar_sharpness = 3.0
    # anisotropia 16x para PBR 4K sem blur em rasante
    mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
    # Altura de relevo / heightmap parallax (só ativa se escala > 0.0)
    var h_scale := float(cfg.get("height_scale", 0.0))
    if cfg.has("height_map") and h_scale > 0.0001 and mat is ORMMaterial3D:
        var height_tex: Texture2D = _textura(String(cfg["height_map"]))
        if height_tex != null:
            mat.heightmap_enabled = true
            mat.heightmap_texture = height_tex
            mat.heightmap_scale = h_scale
    elif cfg.has("height_map") and h_scale > 0.0001 and mat is StandardMaterial3D:
        var height_tex2: Texture2D = _textura(String(cfg["height_map"]))
        if height_tex2 != null:
            mat.heightmap_enabled = true
            mat.heightmap_texture = height_tex2
            mat.heightmap_scale = h_scale
    if chave == "vidro" and mat is StandardMaterial3D:
        var sm := mat as StandardMaterial3D
        sm.clearcoat_enabled = true
        sm.clearcoat = 0.85
        sm.clearcoat_roughness = 0.05
        sm.metallic = 0.25
        sm.roughness = 0.08
    elif chave in ["folhagem", "esfera_verde"] and mat is StandardMaterial3D:
        var sm := mat as StandardMaterial3D
        if ResourceLoader.exists("res://assets/textures/folhagem_realista.png"):
            sm.albedo_texture = ResourceLoader.load("res://assets/textures/folhagem_realista.png")
            sm.albedo_color = Color(0.85, 0.95, 0.82, 1.0)
            sm.normal_enabled = true
            sm.normal_texture = ResourceLoader.load("res://assets/textures/folhagem_realista_normal.png")
            sm.normal_scale = 0.65
            sm.roughness_texture = ResourceLoader.load("res://assets/textures/folhagem_realista_roughness.png")
            sm.roughness = 0.85
            sm.uv1_scale = Vector3(2.5, 2.5, 2.5)
            sm.uv1_triplanar = true
            sm.uv1_world_triplanar = true
    _material_cache[cache_key] = mat
    return mat


static func _tem_textura(nome: String) -> bool:
    return ResourceLoader.exists("%s%s_albedo.png" % [PBR_DIR, nome])


static func _textura(arquivo: String) -> Texture2D:
    var caminho := PBR_DIR + arquivo
    # exists() antes do load: arquivo ausente vira cor plana silenciosa em
    # vez de triplicar erro no log (o material() ja trata null).
    if not ResourceLoader.exists(caminho):
        return null
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


## Multimesh com COR POR INSTANCIA: mesma malha, mesmo material, uma chamada de
## desenho — usado nos letreiros de loja, onde repetir a mesma cor em toda a rua
## entregaria o truque. Exige material com vertex_color_use_as_albedo.
static func _multimesh_cores(mesh: Mesh, mat: Material, xforms: Array, cores: Array,
        pai: Node3D, nome: String) -> MultiMeshInstance3D:
    var mm := MultiMesh.new()
    mm.transform_format = MultiMesh.TRANSFORM_3D
    mm.use_colors = true
    mm.mesh = mesh
    mm.instance_count = xforms.size()
    for i in xforms.size():
        mm.set_instance_transform(i, xforms[i])
        mm.set_instance_color(i, cores[i] if i < cores.size() else Color.WHITE)
    var no := MultiMeshInstance3D.new()
    no.name = nome
    no.multimesh = mm
    no.material_override = mat
    no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    pai.add_child(no)
    return no


## Material dos letreiros: cor vem da instância do multimesh.
static func _mat_letreiro() -> StandardMaterial3D:
    var ck := "letreiro"
    if _material_cache.has(ck):
        return _material_cache[ck]
    var m := StandardMaterial3D.new()
    m.albedo_color = Color.WHITE
    m.vertex_color_use_as_albedo = true
    m.roughness = 0.55
    m.metallic = 0.0
    _material_cache[ck] = m
    return m


## Geometria da secao transversal (layout "rua_esquerda"):
##   x < 0: pista de rolamento | guia | x > 0: calcada (deck de corrida +
##   faixa lateral de props). Todas as bordas saem do spec — nada fixo aqui.


## Drop-in de mobiliario (Lote 6): se existir assets/props/<nome>.glb (modelo
## original em escala real, ver assets/props/LEIA-ME.md), ele substitui a
## versao procedural do kit. Escala 1:1, origem no chao.
static func _prop_glb(nome: String) -> Node3D:
    var path := "res://assets/props/" + nome + ".glb"
    if not ResourceLoader.exists(path):
        return null
    var cena := load(path) as PackedScene
    if cena == null:
        return null
    return cena.instantiate() as Node3D


static func _scene_glb(nome: String) -> Node3D:
    var path := "res://assets/scene/" + nome + ".glb"
    if not ResourceLoader.exists(path):
        return null
    var cena := load(path) as PackedScene
    if cena == null:
        return null
    return cena.instantiate() as Node3D


static func _marca(no: Node3D, superficie: String, colisor: String = "estatico") -> void:
    no.set_meta("superficie", superficie)
    no.set_meta("colisor", colisor)


static func _xform(pos: Vector3, escala: Vector3 = Vector3.ONE, giro_y: float = 0.0) -> Transform3D:
    var b := Basis.from_euler(Vector3(0.0, giro_y, 0.0))
    b = b.scaled(escala)
    return Transform3D(b, pos)


## Gerador deterministico do quarteirao: mesma semente do spec, mesmo leiaute.
## Transform inclinado no plano vertical (giro no eixo X local): os cabos da
## fiação aérea descem e sobem entre postes, e caixa/barra continuam sendo a
## mesma malha unitária do multimesh.
static func _xform_x(pos: Vector3, escala: Vector3, giro_x: float) -> Transform3D:
    var b := Basis.from_euler(Vector3(giro_x, 0.0, 0.0))
    b = b.scaled(escala)
    return Transform3D(b, pos)


## Ritmo GLOBAL em z: devolve as posições locais de um elemento que precisa
## continuar de um quarteirão para o outro (postes, fiação, setas, jardineiras).
## Sem isso o passo reinicia a cada 28 m e passos diferentes viram a mesma coisa.
## O intervalo é semiaberto: entra de margem_inicio até comprimento menos
## margem_fim, sem incluir o fim. Assim o elemento que cai exatamente na emenda
## aparece UMA vez só, no quarteirão de baixo — nem some nem duplica.
static func _ritmo_global(index: int, comprimento: float, passo: float,
        margem_inicio: float = 0.0, margem_fim: float = 0.0) -> Array:
    var saida: Array = []
    var p := maxf(1.0, passo)
    var z_base := float(index) * comprimento
    var k := int(floor(z_base / p))
    while true:
        var z := float(k) * p - z_base
        k += 1
        if z >= comprimento - margem_fim:
            break
        if z < margem_inicio:
            continue
        saida.append(z)
    return saida


static func _rng(spec: Dictionary, indice: int) -> RandomNumberGenerator:
    var rng := RandomNumberGenerator.new()
    rng.seed = int(spec.get("seed", 1)) * 7919 + indice * 104729
    return rng


## Material de cor chapada (cacheado): para adereços do coroamento (caixa
## d'água, ar-condicionado, grime) que não têm entrada no spec.
static func _mat_cor(chave: String, cor: Color, rugosidade: float, metalico: float = 0.0) -> StandardMaterial3D:
    var ck := "cor|%s" % chave
    if _material_cache.has(ck):
        return _material_cache[ck]
    var m := StandardMaterial3D.new()
    m.albedo_color = cor
    m.roughness = rugosidade
    m.metallic = metalico
    _material_cache[ck] = m
    return m


## ETAPA 17 — contrato da "rua viva": padrões de densidade/estilo do coroamento,
## dos decalques de asfalto e do encardido. O cenário da fase
## (level_data.gd -> CENARIO_*.rua_viva) entra por cima destes valores pelo mesmo
## deep-merge de spec_with_overrides que já vale para props/predios, então cada
## capítulo afina o mundo sem tocar em código. Passos em metros: passo MENOR =
## mais denso.
const RUA_VIVA_PADRAO := {
    "coroamento": {
        "platibanda": true,
        "ar_condicionado": true,
        "caixa_dagua_min_andares": 3,
        "escada_incendio": true,
        "escada_min_andares": 4,
        "escada_a_cada_lotes": 2,
    },
    "decalques": {
        "setas": true,
        "seta_passo_m": 16.0,
        "seta_comprimento_m": 1.3,
        "tampa_passo_m": 14.0,
        "remendo_passo_m": 15.0,
    },
    "encardido": {
        "albedo": 0.42,
        "sarjeta": true,
        "parede": true,
        "poste": true,
    },
    "fachada": {
        "toldo": true,
        "letreiro": true,
        "grade_janela": true,
        "grade_ate_andar": 1,
    },
    "rua": {
        "fiacao": true,
        "fiacao_cabos": 3,
        "fiacao_flecha_m": 0.45,
        "jardineira": true,
        "jardineira_passo_m": 22.0,
    },
}

## Paleta dos letreiros de loja: cor por instância dentro do MESMO multimesh
## (1 chamada de desenho para a rua inteira, sem repetir a mesma fachada).
const CORES_LETREIRO := [
    Color(0.86, 0.26, 0.20), Color(0.16, 0.42, 0.70), Color(0.94, 0.72, 0.16),
    Color(0.18, 0.52, 0.36), Color(0.78, 0.40, 0.14), Color(0.42, 0.28, 0.58),
]


## Bloco da rua viva já resolvido: padrão do kit + spec em disco + override do
## cenário. Chaves desconhecidas do spec são ignoradas pelo consumidor, mas
## ficam no dicionário para o auditor reclamar.
static func rua_viva(spec: Dictionary, bloco: String) -> Dictionary:
    var padrao: Dictionary = RUA_VIVA_PADRAO.get(bloco, {})
    var cfg = spec.get("rua_viva", {}).get(bloco, {})
    if typeof(cfg) != TYPE_DICTIONARY or cfg.is_empty():
        return padrao.duplicate(true)
    var resultado: Dictionary = padrao.duplicate(true)
    for chave in cfg:
        resultado[chave] = cfg[chave]
    return resultado


## Encardido (sujeira nas juntas): material escuro em blend MULTIPLICAR, para
## ESCURECER a superfície embaixo em vez de pintar um bloco preto. O albedo vem
## do cenário: menor = mais sujo, 1.0 = invisível. Cacheado por valor.
static func _mat_encardido(albedo: float = 0.42) -> StandardMaterial3D:
    var a := clampf(albedo, 0.05, 1.0)
    var ck := "encardido|%.3f" % a
    if _material_cache.has(ck):
        return _material_cache[ck]
    var m := StandardMaterial3D.new()
    m.albedo_color = Color(a, a * 0.952, a * 0.881, 1.0)
    m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    m.blend_mode = BaseMaterial3D.BLEND_MODE_MUL
    m.roughness = 1.0
    m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    m.cull_mode = BaseMaterial3D.CULL_DISABLED
    _material_cache[ck] = m
    return m


## Degrau de qualidade atual (0 = melhor, 3 = mais leve), lido do autoload
## RenderQuality de forma defensiva: adereços pesados (escada de incêndio,
## grime) só entram nos degraus altos. Sem o autoload (ou headless), assume 0.
static func _tier_atual() -> int:
    var loop := Engine.get_main_loop()
    if loop is SceneTree:
        var rq: Node = (loop as SceneTree).root.get_node_or_null("RenderQuality")
        if rq != null and rq.has_method("get_tier_index"):
            return int(rq.get_tier_index())
    return 0


static func _x_guia_esq(faixas: Dictionary) -> float:
    return -float(faixas.get("piso_borda_esq_m", 1.35)) - float(faixas.get("guia_largura_m", 0.35))


static func _x_rua_esq(faixas: Dictionary) -> float:
    return _x_guia_esq(faixas) - float(faixas.get("pista_m", 6.6))


static func _x_rua_centro(faixas: Dictionary) -> float:
    return _x_guia_esq(faixas) - float(faixas.get("pista_m", 6.6)) * 0.5


## Borda externa da faixa de props da calcada (lado direito do corredor).
static func _x_calcada(faixas: Dictionary) -> float:
    return -float(faixas.get("piso_borda_esq_m", 1.35)) + float(faixas.get("piso_central_m", 6.0)) + float(faixas.get("calcada_lateral_m", 2.5))


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
    _build_decalques_chao(spec, raiz, comprimento, faixas)
    _build_lajes(spec, raiz, rng, comprimento, faixas)
    _build_mosaicos(spec, raiz, rng, comprimento, faixas)
    _build_predios(spec, raiz, rng, comprimento)
    _build_arvores(spec, raiz, rng, comprimento)
    _build_mobiliario(spec, raiz, rng, comprimento, faixas, visibilidade)
    _build_folhas(spec, raiz, rng, comprimento, visibilidade)
    _build_passaros(spec, raiz, rng, comprimento, visibilidade)

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



static func _build_piso(spec: Dictionary, raiz: Node3D, comprimento: float, _visibilidade: float) -> void:
    # Layout "rua_esquerda": deck de calcada no centro-direita (o corredor
    # passa por ele), faixa de props alem do deck e guia unica junto da pista.
    var f: Dictionary = spec.get("faixas", {})
    var piso := float(f.get("piso_central_m", 6.0))
    var borda_esq := float(f.get("piso_borda_esq_m", 1.35))
    var guia_l := float(f.get("guia_largura_m", 0.35))
    var guia_h := float(f.get("guia_altura_m", 0.15))
    var calcada := float(f.get("calcada_lateral_m", 2.5))
    var x_deck := -borda_esq + piso * 0.5
    # deck da calcada (as faixas central e direita do jogo caem aqui)
    var deck := _malha(_box(Vector3(piso, 0.40, comprimento)),
        material(spec, "piso_central"), Vector3(x_deck, 0.15 - 0.20, -comprimento * 0.5), raiz,
        "CalcadaDeck", false, 0.0)
    _marca(deck, "piso_central")
    # faixa lateral da calcada (arvores, postes, bancos e esferas)
    if calcada > 0.01:
        var x_lat := -borda_esq + piso + calcada * 0.5
        var faixa_lat := _malha(_box(Vector3(calcada, 0.40, comprimento)),
            material(spec, "calcada_lateral"),
            Vector3(x_lat, 0.15 - 0.20, -comprimento * 0.5), raiz,
            "CalcadaFaixa", false, 0.0)
        _marca(faixa_lat, "calcada_lateral")
    # guia unica entre a rua e a calcada (o topo fica guia_h acima do asfalto)
    var x_guia := -borda_esq - guia_l * 0.5
    var guia := _malha(_box(Vector3(guia_l, 0.40, comprimento)),
        material(spec, "guia"),
        Vector3(x_guia, guia_h - 0.20, -comprimento * 0.5), raiz,
        "Guia", true, 0.0)
    _marca(guia, "guia")
    # Encardido da sarjeta: faixa escura contínua no encontro guia/asfalto, onde
    # a água de chuva escorre e a sujeira assenta (junta meio-fio/pista).
    var grime: Dictionary = rua_viva(spec, "encardido")
    if _tier_atual() <= 2 and bool(grime.get("sarjeta", true)):
        var sarjeta_grime := _malha(_box(Vector3(0.28, 0.006, comprimento)),
            _mat_encardido(float(grime.get("albedo", 0.42))),
            Vector3(x_guia - guia_l * 0.5 - 0.14, 0.006, -comprimento * 0.5), raiz,
            "EncardidoSarjeta", false, 0.0)
        _marca(sarjeta_grime, "encardido", "nenhum")
    # Grelhas de sarjeta / bueiro de ferro fundido junto ao meio-fio
    var n_bueiros := int(comprimento / 14.0)
    for b in range(n_bueiros):
        var z_bueiro := 7.0 + float(b) * 14.0
        var bueiro := _malha(_box(Vector3(0.50, 0.012, 0.85)),
            material(spec, "estrutura_metalica"),
            Vector3(x_guia - guia_l * 0.5 - 0.26, 0.005, -z_bueiro), raiz,
            "BueiroSarjeta%d" % b, false, 0.0)
        _marca(bueiro, "sarjeta", "nenhum")

static func _build_pistas(spec: Dictionary, raiz: Node3D, comprimento: float, faixas: Dictionary) -> void:
    # a rua inteira fica do lado esquerdo do deck
    var pista := float(faixas.get("pista_m", 6.6))
    var no := _malha(_box(Vector3(pista, 0.40, comprimento)),
        material(spec, "pista"),
        Vector3(_x_rua_centro(faixas), -0.20, -comprimento * 0.5), raiz,
        "PistaE", false, 0.0)
    _marca(no, "pista")

static func _build_linhas(spec: Dictionary, raiz: Node3D, comprimento: float, faixas: Dictionary) -> void:
    if String(faixas.get("linha_amarela_modo", "junto_guia")) != "junto_guia":
        return
    var largura := float(faixas.get("linha_amarela_largura_m", 0.12))
    var afast := float(faixas.get("linha_amarela_afastamento_m", 0.30))
    var entre := float(faixas.get("linha_amarela_entre_m", 0.20))
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var guia_l := float(faixas.get("guia_largura_m", 0.35))
    # linha dupla amarela colada na guia (a borda direita da rua)
    var x_base := -borda_esq - guia_l
    for par in range(2):
        var x := x_base - afast - largura * 0.5 - float(par) * (largura + entre)
        var nome := "LinhaAmarela%d" % par
        var no := _malha(_box(Vector3(largura, 0.01, comprimento)),
            material(spec, "linha_amarela"),
            Vector3(x, 0.006, -comprimento * 0.5), raiz, nome, false, 0.0)
        _marca(no, "linha_amarela", "nenhum")

    # Faixa de pedestres zebrada de alto contraste e divisores seccionados na pista
    var index: int = int(raiz.get_meta("spec_index", 0))
    var tem_faixa_pedestre: bool = (index % 2 == 1)
    var z_faixa_ini := 4.2
    var n_zebras := 6
    var largura_zebra := 0.42
    var gap_zebra := 0.45
    var z_faixa_fim := z_faixa_ini + float(n_zebras) * largura_zebra + float(n_zebras - 1) * gap_zebra

    if tem_faixa_pedestre:
        var x_rua_ext := _x_rua_esq(faixas) + 0.35
        var x_rua_int := x_base - 0.25
        var largura_rua := absf(x_rua_int - x_rua_ext)
        var x_centro_faixa := (x_rua_ext + x_rua_int) * 0.5
        var xforms_zebra: Array = []
        for s in range(n_zebras):
            var z_zebra: float = z_faixa_ini + float(s) * (largura_zebra + gap_zebra) + largura_zebra * 0.5
            xforms_zebra.append(_xform(
                Vector3(x_centro_faixa, 0.008, -z_zebra),
                Vector3(largura_rua, 0.01, largura_zebra)))
        if not xforms_zebra.is_empty():
            var faixa_mesh := _multimesh(_box(Vector3.ONE), material(spec, "faixa_branca"), xforms_zebra, raiz, "FaixaPedestre", false, 0.0)
            _marca(faixa_mesh, "faixa_pedestre", "nenhum")

        # Piso podotatil amarelo de alerta na borda da calcada correspondente a travessia
        var z_alerta_centro := (z_faixa_ini + z_faixa_fim) * 0.5
        var comp_alerta := (z_faixa_fim - z_faixa_ini) + 0.3
        var podotatil := _malha(_box(Vector3(0.38, 0.014, comp_alerta)),
            material(spec, "linha_amarela"),
            Vector3(-borda_esq + 0.19, 0.155, -z_alerta_centro), raiz, "PisoPodotatil", false, 0.0)
        _marca(podotatil, "podotatil", "nenhum")

    # Linha tracejada divisoria de pistas no centro da rua (_x_rua_centro)
    var x_centro_rua := _x_rua_centro(faixas)
    var dash_len := 2.5
    var dash_gap := 3.5
    var dash_step := dash_len + dash_gap
    var xforms_dashes: Array = []
    var z_cursor := 1.2
    while z_cursor + dash_len < comprimento - 1.0:
        var overlaps_zebra := tem_faixa_pedestre and (z_cursor + dash_len >= z_faixa_ini - 0.6 and z_cursor <= z_faixa_fim + 0.6)
        if not overlaps_zebra:
            xforms_dashes.append(_xform(
                Vector3(x_centro_rua, 0.007, -(z_cursor + dash_len * 0.5)),
                Vector3(0.12, 0.01, dash_len)))
        z_cursor += dash_step
    if not xforms_dashes.is_empty():
        var dashes_mesh := _multimesh(_box(Vector3.ONE), material(spec, "faixa_branca"), xforms_dashes, raiz, "LinhaTracejada", false, 0.0)
        _marca(dashes_mesh, "linha_tracejada", "nenhum")

## Decalques do asfalto (sobre a PistaE): tracejado divisor das faixas, setas
## de direção, tampas de esgoto e remendos. Tudo em multimesh (1 draw call por
## tipo). rng LOCAL (não toca a stream do quarteirão, senão mudaria as árvores).
static func _build_decalques_chao(spec: Dictionary, raiz: Node3D, comprimento: float,
        faixas: Dictionary) -> void:
    var index: int = int(raiz.get_meta("spec_index", 0))
    var rng2 := RandomNumberGenerator.new()
    rng2.seed = int(spec.get("seed", 1)) * 2657 + index * 40499 + 13
    var x_centro := _x_rua_centro(faixas)
    var pista := float(faixas.get("pista_m", 6.6))
    var lane := pista * 0.25
    var y := 0.009
    var mat_branco := material(spec, "faixa_branca")
    var cfg: Dictionary = rua_viva(spec, "decalques")
    # (o tracejado divisor central já é feito em _build_linhas -> LinhaTracejada)
    # setas de direção (uma por faixa a cada seta_passo_m), apontando o fluxo -z.
    # Passo e comprimento vêm do cenário: avenida usa setas densas, parque quase
    # nenhuma.
    # O ritmo das setas é GLOBAL (contado em z absoluto, não reiniciado a cada
    # quarteirão): assim o passo do cenário aparece de verdade na rua — antes,
    # com 28 m de quarteirão, 16 m e 24 m davam a mesma seta única por bloco.
    var hastes: Array = []
    var cabecas: Array = []
    var seta_passo := maxf(4.0, float(cfg.get("seta_passo_m", 16.0)))
    var seta_len := maxf(0.4, float(cfg.get("seta_comprimento_m", 1.3)))
    if bool(cfg.get("setas", true)):
        for za in _ritmo_global(index, comprimento, seta_passo, 1.0, 2.0):
            for lx in [x_centro - lane, x_centro + lane]:
                hastes.append(_xform(Vector3(lx, y, -za), Vector3(0.16, 0.01, seta_len)))
                for sgn in [-1.0, 1.0]:
                    cabecas.append(_xform(
                        Vector3(lx + sgn * 0.20, y, -(za + seta_len * 0.38)),
                        Vector3(0.16, 0.01, seta_len * 0.42), sgn * 0.7))
    if not hastes.is_empty():
        _multimesh(_box(Vector3.ONE), mat_branco, hastes, raiz, "SetaHaste", false, 0.0)
    if not cabecas.is_empty():
        _multimesh(_box(Vector3.ONE), mat_branco, cabecas, raiz, "SetaCabeca", false, 0.0)
    # 3 - tampas de esgoto redondas de ferro fundido na pista
    var tampas: Array = []
    var aros: Array = []
    # Contagem por passo real em metros: roundi(comprimento / passo). Com o
    # quarteirão de 28 m isso dá 1 tampa a cada tampa_passo_m de rua.
    var tampa_passo := maxf(4.0, float(cfg.get("tampa_passo_m", 14.0)))
    var n_tampas := maxi(1, int(round(comprimento / tampa_passo)))
    for i in range(n_tampas):
        var zt := rng2.randf_range(4.0, comprimento - 4.0)
        var xt := x_centro + rng2.randf_range(-lane, lane)
        tampas.append(_xform(Vector3(xt, 0.006, -zt)))
        aros.append(_xform(Vector3(xt, 0.004, -zt)))
    if not tampas.is_empty():
        _multimesh(_cyl(0.40, 0.015, 14), _mat_cor("aro_esgoto", Color(0.22, 0.22, 0.23), 0.8, 0.2),
                aros, raiz, "AroEsgoto", false, 0.0)
        _multimesh(_cyl(0.33, 0.022, 14), _mat_cor("tampa_esgoto", Color(0.15, 0.16, 0.17), 0.7, 0.3),
                tampas, raiz, "TampaEsgoto", false, 0.0)
    # 4 - remendos de asfalto irregulares (mancha mais escura e fosca)
    var remendos: Array = []
    var remendo_passo := maxf(4.0, float(cfg.get("remendo_passo_m", 15.0)))
    var n_rem := maxi(1, int(round(comprimento / remendo_passo)))
    for i in range(n_rem):
        var zr := rng2.randf_range(3.0, comprimento - 3.0)
        var xr := x_centro + rng2.randf_range(-pista * 0.4, pista * 0.4)
        remendos.append(_xform(Vector3(xr, 0.004, -zr),
                Vector3(rng2.randf_range(0.8, 1.6), 0.008, rng2.randf_range(1.0, 2.2)),
                rng2.randf_range(-0.3, 0.3)))
    if not remendos.is_empty():
        _multimesh(_box(Vector3.ONE), _mat_cor("remendo_asfalto", Color(0.10, 0.105, 0.11), 0.96),
                remendos, raiz, "RemendoAsfalto", false, 0.0)


static func _build_lajes(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, faixas: Dictionary) -> void:
    var lajes: Dictionary = spec.get("lajes", {})
    var faixa: Array = lajes.get("tamanho_m", [0.55, 0.80])
    var altura := float(lajes.get("altura_m", 0.05))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var inicio := -borda_esq
    var fim := -borda_esq + piso
    var paver_l := float(lajes.get("paver_largura_m", 0.0))
    var junta := float(lajes.get("junta_m", 0.014))
    var xforms: Array = []
    var coluna := 0
    var x := inicio
    while x < fim - 0.05:
        var largura := 0.0
        var z := 0.0
        if paver_l > 0.01:
            # bloqueta regular de calcada (juntas corridas, como na referencia)
            largura = minf(paver_l, fim - x)
            if coluna % 2 == 1:
                z = -float(lajes.get("paver_comprimento_m", 0.44)) * 0.5
        else:
            largura = rng.randf_range(float(faixa[0]), float(faixa[1]))
            largura = minf(largura, fim - x)
            if coluna % 2 == 1:
                z = -rng.randf_range(0.15, 0.45)
        while z < comprimento - 0.05:
            var prof := 0.0
            if paver_l > 0.01:
                prof = minf(float(lajes.get("paver_comprimento_m", 0.44)), comprimento - z)
            else:
                prof = rng.randf_range(float(faixa[0]), float(faixa[1]))
                prof = minf(prof, comprimento - z)
            xforms.append(_xform(
                Vector3(x + largura * 0.5, 0.15 + altura * 0.5, -(z + prof * 0.5)),
                Vector3(largura - junta, altura, prof - junta)))
            z += prof + junta
        x += largura + junta
        coluna += 1
    _multimesh(_box(Vector3.ONE), material(spec, "piso_central"), xforms, raiz, "Lajes", false, 0.0)
static func _build_mosaicos(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, faixas: Dictionary) -> void:
    var lajes: Dictionary = spec.get("lajes", {})
    var lado_m := float(lajes.get("mosaico_lado_m", 0.42))
    var variacao := float(lajes.get("mosaico_variacao_m", 0.06))
    var altura := float(lajes.get("altura_m", 0.004))
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var calcada := float(faixas.get("calcada_lateral_m", 2.5))
    var inicio := -borda_esq + piso
    var fim := inicio + calcada
    var xforms: Array = []
    var z := 0.0
    while z < comprimento - 0.05:
        var z_lado := minf(lado_m + rng.randf_range(-variacao, variacao), comprimento - z)
        var x := inicio
        while x < fim - 0.05:
            var x_lado := minf(lado_m + rng.randf_range(-variacao, variacao), fim - x)
            xforms.append(_xform(
                Vector3(x + x_lado * 0.5, 0.15 + altura * 0.5, -(z + z_lado * 0.5)),
                Vector3(x_lado - 0.005, altura, z_lado - 0.005)))
            x += x_lado + 0.005
        z += z_lado + 0.005
    _multimesh(_box(Vector3.ONE), material(spec, "calcada_lateral"), xforms, raiz, "Mosaicos", false, 0.0)

static func _build_predios(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float) -> void:
    var p: Dictionary = spec.get("predios", {})
    var pisos: Array = p.get("pisos", [2, 3])
    var pe := float(p.get("pe_direito_m", 3.0))
    var variacao := float(p.get("variacao_altura_m", 0.35))
    var largura_lote: Array = p.get("largura_lote_m", [7.0, 12.0])
    var recuo := float(p.get("recuo_calcada_m", 0.35))
    var profundidade := float(p.get("profundidade_m", 9.0))
    var telhado := float(p.get("telhado_altura_m", 0.35))
    var janela: Dictionary = p.get("janela", {})
    var faixas: Dictionary = spec.get("faixas", {})
    # Passe visual 2: prédios projetam sombra de verdade (antes sombra=false
    # fixo — o mundo inteiro ficava sem nenhuma sombra direcional, o maior
    # fator de "cara de placeholder" nas capturas). Continua controlável por
    # orçamento: "sombras_mundo": false no world_spec desliga.
    var sombras_mundo: bool = bool(spec.get("orcamento", {}).get("sombras_mundo", true))
    # Coroamento (massa do topo) e saliências: coletados por quarteirão e
    # emitidos em multimesh no fim — 1 draw call por tipo, não por prédio, para
    # não estourar o orçamento móvel (Moto G84) com dezenas de caixinhas.
    var xf_platibanda: Array = []
    var xf_ac: Array = []
    var xf_caixa: Array = []
    var xf_casa: Array = []
    var xf_recuo: Array = []
    var xf_grime_parede: Array = []
    var predios_escada: Array = []
    # Contrato da rua viva: o cenário da fase manda na densidade/estilo do topo
    # e do encardido. CENTRO empilha caixa d'água cedo, PARQUE dispensa escada.
    var coro: Dictionary = rua_viva(spec, "coroamento")
    var grime: Dictionary = rua_viva(spec, "encardido")
    var usa_platibanda: bool = bool(coro.get("platibanda", true))
    var usa_ac: bool = bool(coro.get("ar_condicionado", true))
    var caixa_min: int = int(coro.get("caixa_dagua_min_andares", 3))
    var fach: Dictionary = rua_viva(spec, "fachada")
    var usa_toldo: bool = bool(fach.get("toldo", true))
    var usa_letreiro: bool = bool(fach.get("letreiro", true)) and _tier_atual() <= 2
    var usa_grade: bool = bool(fach.get("grade_janela", true)) and _tier_atual() <= 2
    var grade_ate: int = int(fach.get("grade_ate_andar", 1))
    var xf_grade: Array = []
    var xf_letreiro: Array = []
    var cor_letreiro: Array = []
    var usa_escada: bool = bool(coro.get("escada_incendio", true))
    var escada_min: int = maxi(1, int(coro.get("escada_min_andares", 4)))
    var escada_passo: int = maxi(1, int(coro.get("escada_a_cada_lotes", 2)))
    for lado in [-1.0, 1.0]:
        # frente do lote: na borda externa da calcada (direita) ou no fim da
        # rua (esquerda). x_frente/x_centro sao magnitudes a partir do centro.
        var borda_mag := _x_calcada(faixas) if lado > 0.0 else absf(_x_rua_esq(faixas))
        var x_frente := borda_mag + recuo
        var x_centro := borda_mag + recuo + profundidade * 0.5
        var z := 0.0
        var lote := 0
        while z < comprimento - 0.6:
            # o ultimo lote fecha o quarteirao: pode ser estreito, mas nao pode
            # sobrar buraco (a rua ficaria com um vazio no fim do quarteirao)
            var largura := minf(rng.randf_range(float(largura_lote[0]), float(largura_lote[1])),
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
                "Predio%s%d" % [("D" if lado > 0.0 else "E"), lote], sombras_mundo)
            _marca(frente, "fachada")
            var teto := _malha(_box(Vector3(profundidade + 0.2, telhado, largura + 0.2)),
                material(spec, "telhado"),
                Vector3(lado * x_centro, altura + telhado * 0.5, -(z + largura * 0.5)), raiz,
                "Telhado%s%d" % [("D" if lado > 0.0 else "E"), lote], sombras_mundo)
            _marca(teto, "telhado")
            # --- Coroamento e saliências (só coleta; emite depois em multimesh).
            # Nada de rng aqui: a espécie/posição das árvores é sorteada depois
            # com o MESMO rng, então consumir a stream mudaria o cenário.
            if tipo != "obra":
                var cz := -(z + largura * 0.5)
                var topo := altura + telhado
                # platibanda: mureta na testeira (quebra o topo chapado da caixa)
                if usa_platibanda:
                    xf_platibanda.append(_xform(
                        Vector3(lado * (x_frente + 0.05), topo + 0.22, cz),
                        Vector3(0.16, 0.46, largura * 0.98)))
                # ar-condicionado saliente na fachada (1-2 conforme o prédio)
                var n_ac := (1 + (andares % 2)) if usa_ac else 0
                for a in range(n_ac):
                    var ay := pe * (1.25 + 0.9 * float(a))
                    if ay < altura - 0.5:
                        xf_ac.append(_xform(
                            Vector3(lado * (x_frente + 0.24), ay,
                                cz + largura * (0.22 - 0.4 * float(a))),
                            Vector3(0.5, 0.42, 0.62)))
                # caixa d'água a partir de caixa_dagua_min_andares pavimentos
                if andares >= caixa_min:
                    xf_caixa.append(_xform(Vector3(
                        lado * (x_centro - lado * profundidade * 0.16),
                        topo + 0.52, cz + largura * 0.12)))
                # topo alto: recuo (ático) OU casa de máquinas — nunca os dois
                # (evita interpenetração no telhado).
                if andares >= 5:
                    xf_recuo.append(_xform(
                        Vector3(lado * x_centro, topo + pe * 0.5, cz),
                        Vector3(profundidade * 0.72, pe, largura * 0.66)))
                elif andares >= 3:
                    xf_casa.append(_xform(
                        Vector3(lado * (x_centro + lado * profundidade * 0.12),
                            topo + 0.45, cz - largura * 0.12),
                        Vector3(profundidade * 0.34, 0.9, largura * 0.3)))
                # encardido na junta parede/calçada: banda escura rente à base
                # da fachada (respingo de chuva + poeira acumulada no rodapé)
                if bool(grime.get("parede", true)):
                    xf_grime_parede.append(_xform(
                        Vector3(lado * (x_frente - lado * 0.03), 0.30, cz),
                        Vector3(0.05, 0.34, largura * 0.94)))
                # escada de incêndio nos prédios altos (a cada N lotes)
                if usa_escada and andares >= escada_min and lote % escada_passo == 0:
                    predios_escada.append({
                        "lado": lado, "xf": x_frente, "cz": cz,
                        "larg": largura, "and": andares, "pe": pe})
            if tipo != "obra":
                _build_janelas(spec, raiz, rng, janela, lado, x_frente, z, largura, andares, pe, tipo, lote,
                        xf_grade if usa_grade else [], grade_ate)
            if tipo == "loja":
                _build_loja(spec, raiz, p, lado, x_frente, z, largura, lote, usa_toldo)
                if usa_letreiro:
                    var toldo_y := float(p.get("loja", {}).get("toldo_altura_m", 2.6))
                    xf_letreiro.append(_xform(
                        Vector3(lado * (x_frente - 0.14), toldo_y + 0.52, -(z + largura * 0.5)),
                        Vector3(0.10, 0.62, largura * 0.72)))
                    # cor pela ordem do letreiro no quarteirão (mais o índice do
                    # quarteirão, para a rua não repetir o mesmo par de fachadas):
                    # garante vizinhos de cores diferentes, sem depender do sorteio.
                    var ic := (cor_letreiro.size() + int(raiz.get_meta("spec_index", 0))) \
                            % CORES_LETREIRO.size()
                    cor_letreiro.append(CORES_LETREIRO[ic])
            z += largura
            lote += 1
    # --- Emite o coroamento coletado (poucos draw calls por quarteirão).
    var mat_reboco := material(spec, "fachada_reboco")
    if not xf_platibanda.is_empty():
        _multimesh(_box(Vector3.ONE), mat_reboco, xf_platibanda, raiz, "Platibanda", sombras_mundo)
    if not xf_recuo.is_empty():
        _multimesh(_box(Vector3.ONE), mat_reboco, xf_recuo, raiz, "RecuoTopo", sombras_mundo)
    if not xf_casa.is_empty():
        _multimesh(_box(Vector3.ONE), mat_reboco, xf_casa, raiz, "CasaMaquinas", sombras_mundo)
    if not xf_caixa.is_empty():
        _multimesh(_cyl(0.46, 1.0, 12), _mat_cor("caixa_dagua", Color(0.24, 0.36, 0.52), 0.55),
                xf_caixa, raiz, "CaixaDagua", sombras_mundo)
    if not xf_ac.is_empty():
        _multimesh(_box(Vector3.ONE), _mat_cor("ar_cond", Color(0.82, 0.82, 0.80), 0.5, 0.1),
                xf_ac, raiz, "ArCondicionado", false)
    # Grades de janela dos andares baixos e letreiros das lojas: um multimesh
    # cada para o quarteirão inteiro. O letreiro leva cor POR INSTANCIA, então
    # a rua fica variada sem custar uma chamada de desenho por loja.
    if not xf_grade.is_empty():
        var grade_no := _multimesh(_box(Vector3.ONE), material(spec, "estrutura_metalica"),
                xf_grade, raiz, "GradeJanela", false, 0.0)
        _marca(grade_no, "grade", "nenhum")
    if not xf_letreiro.is_empty():
        var letreiro_no := _multimesh_cores(_box(Vector3.ONE), _mat_letreiro(),
                xf_letreiro, cor_letreiro, raiz, "LetreiroLoja")
        _marca(letreiro_no, "letreiro", "nenhum")
    # Escada de incêndio: adereço pesado, só nos degraus de qualidade alto/médio.
    if not predios_escada.is_empty() and _tier_atual() <= 1:
        _build_escadas_incendio(spec, raiz, predios_escada)
    # Encardido: detalhe sutil, cai fora só no degrau mais leve (tier 3).
    if not xf_grime_parede.is_empty() and _tier_atual() <= 2:
        _multimesh(_box(Vector3.ONE), _mat_encardido(float(grime.get("albedo", 0.42))),
                xf_grime_parede, raiz, "EncardidoParede", false, 0.0)


## Escada de incêndio de ferro na fachada: montante + patamar por andar +
## lance diagonal. Tudo coletado em 3 multimesh (montantes, patamares, lances)
## para o quarteirão inteiro — barato mesmo com vários prédios.
static func _build_escadas_incendio(spec: Dictionary, raiz: Node3D, lista: Array) -> void:
    var montantes: Array = []
    var patamares: Array = []
    var lances: Array = []
    for e in lista:
        var lado: float = float(e["lado"])
        var x_frente: float = float(e["xf"])
        var cz: float = float(e["cz"])
        var larg: float = float(e["larg"])
        var andares: int = int(e["and"])
        var pe: float = float(e["pe"])
        var x_face := lado * (x_frente + 0.22)   # afastada da fachada
        var z_esq := cz + larg * 0.30            # encostada num terço do lote
        # dois montantes verticais
        var altura_total := float(andares) * pe
        for dz in [-0.5, 0.5]:
            montantes.append(_xform(
                Vector3(x_face, altura_total * 0.5, z_esq + dz),
                Vector3(0.06, altura_total, 0.06)))
        # um patamar por andar e um lance diagonal ligando os andares
        for andar in range(andares):
            var y := pe * float(andar + 1) - 0.1
            patamares.append(_xform(
                Vector3(x_face, y, z_esq),
                Vector3(0.44, 0.06, 1.05)))
            if andar < andares - 1:
                lances.append(_xform(
                    Vector3(x_face, y + pe * 0.5, z_esq + 0.28),
                    Vector3(0.40, 0.05, pe * 1.1),
                    0.0))
    var mat_metal := material(spec, "estrutura_metalica")
    if not montantes.is_empty():
        _multimesh(_box(Vector3.ONE), mat_metal, montantes, raiz, "EscadaMontante", false)
    if not patamares.is_empty():
        _multimesh(_box(Vector3.ONE), mat_metal, patamares, raiz, "EscadaPatamar", false)
    if not lances.is_empty():
        var lance_mesh := _box(Vector3.ONE)
        var mm := MultiMesh.new()
        mm.transform_format = MultiMesh.TRANSFORM_3D
        mm.mesh = lance_mesh
        mm.instance_count = lances.size()
        for i in lances.size():
            # inclina o lance ~35° no plano vertical (eixo x local)
            var t: Transform3D = lances[i]
            t.basis = Basis.from_euler(Vector3(0.6, 0.0, 0.0)) * t.basis
            mm.set_instance_transform(i, t)
        var no := MultiMeshInstance3D.new()
        no.name = "EscadaLance"
        no.multimesh = mm
        no.material_override = mat_metal
        no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
        raiz.add_child(no)


static func _tipo_predio(p: Dictionary, rng: RandomNumberGenerator) -> String:
    var pesos: Dictionary = p.get("tipo_pesos", {"tijolo": 1})
    var total := 0
    for k in pesos.keys():
        total += int(pesos[k])
    var escolha := rng.randi_range(1, maxi(1, total))
    var acumulado := 0
    for k in pesos.keys():
        acumulado += int(pesos[k])
        if escolha <= acumulado:
            return String(k)
    return "tijolo"


## As grades vao para "grades" (coletor do quarteirao, emitido em 1 multimesh
## no _build_predios): grade de ferro nos andares ate grade_ate_andar, que e o
## que da cara de rua brasileira aos pavimentos baixos.
static func _build_janelas(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        janela: Dictionary, lado: float, x_frente: float, z: float, largura: float,
        andares: int, pe: float, tipo: String, indice: int = 0,
        grades: Array = [], grade_ate: int = 0) -> void:
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
            var yc := peitoril + ja * 0.5 + float(andar) * pe
            xforms.append(_xform(
                Vector3(lado * (x_frente - 0.03), yc, -zc),
                Vector3(0.06, ja, jl)))
            if andar < grade_ate:
                # tres barras verticais rentes ao vidro, por fora da moldura
                for b in range(3):
                    grades.append(_xform(
                        Vector3(lado * (x_frente + 0.03), yc,
                            -(zc + jl * (float(b) * 0.3 - 0.3))),
                        Vector3(0.035, ja * 0.96, 0.035)))
    _multimesh(_box(Vector3.ONE), material(spec, "vidro"), xforms, raiz,
            "Janelas%s%d" % [("D" if lado > 0.0 else "E"), indice], false)


static func _build_loja(spec: Dictionary, raiz: Node3D, p: Dictionary, lado: float,
        x_frente: float, z: float, largura: float, indice: int = 0,
        usa_toldo: bool = true) -> void:
    var loja: Dictionary = p.get("loja", {})
    var altura_toldo := float(loja.get("toldo_altura_m", 2.6))
    var prof := float(loja.get("toldo_profundidade_m", 1.1))
    var porta_l := float(loja.get("porta_largura_m", 1.6))
    var porta_a := float(loja.get("porta_altura_m", 2.4))
    if usa_toldo:
        var toldo := _malha(_box(Vector3(prof, 0.14, largura * 0.85)),
                material(spec, "linha_amarela"),
                Vector3(lado * (x_frente - prof * 0.5), altura_toldo, -(z + largura * 0.5)), raiz,
                "Toldo%s%d" % [("D" if lado > 0.0 else "E"), indice], false)
        _marca(toldo, "toldo")
    var porta := _malha(_box(Vector3(0.08, porta_a, porta_l)),
            material(spec, "zincado"),
            Vector3(lado * (x_frente - 0.04), porta_a * 0.5, -(z + largura * 0.5)), raiz,
            "Porta%s%d" % [("D" if lado > 0.0 else "E"), indice], false)
    _marca(porta, "porta")
    # Vitrine espelhada de vidro com reflexo PBR
    if largura * 0.8 > porta_l + 1.2:
        var vitrine_l := (largura * 0.8 - porta_l) * 0.45
        for s in [-1.0, 1.0]:
            var vitrine := _malha(_box(Vector3(0.06, porta_a - 0.3, vitrine_l)),
                    material(spec, "vidro"),
                    Vector3(lado * (x_frente - 0.03), (porta_a - 0.3) * 0.5 + 0.15, -(z + largura * 0.5 + s * (porta_l * 0.5 + vitrine_l * 0.5))),
                    raiz, "Vitrine%s%d_%s" % [("D" if lado > 0.0 else "E"), indice, ("A" if s < 0 else "B")], false)
            _marca(vitrine, "vidro")


static func _build_arvores(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float) -> void:
    var cfg: Dictionary = spec.get("props", {}).get("arvore", {})
    var passo := float(cfg.get("espacamento_m", 8.0))
    var tronco_h := float(cfg.get("tronco_altura_m", 2.4))
    var tronco_r := float(cfg.get("tronco_raio_m", 0.14))
    var copa_r := float(cfg.get("copa_raio_m", 1.7))
    var faixas: Dictionary = spec.get("faixas", {})
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var calcada := float(faixas.get("calcada_lateral_m", 2.5))
    # direita: no meio da faixa de props; esquerda: alem do fim da rua
    var x_dir := -borda_esq + piso + calcada * 0.5
    var x_esq := _x_rua_esq(faixas) - 1.2
    var z := rng.randf_range(1.0, passo)
    var lado := 1.0
    while z < comprimento:
        var x := x_dir if lado > 0.0 else x_esq
        var base := Vector3(x, 0.15, -z)
        # A espécie é identidade de cenário e vem do perfil (props.arvore.glb):
        # ipê amarelo na "Rua do Ipê", palmeira na orla/avenida, comum no resto.
        # Sem override explícito a árvore é a COMUM — fase genérica não sorteia
        # ipê/palmeira (contrato das suítes de arte: W4, L4-D, L5-D, L7-D).
        var arvore_nome: String = str(cfg["glb"]) if cfg.has("glb") else "arvore"
        var arvore_glb := _scene_glb(arvore_nome)
        if arvore_glb == null:
            arvore_glb = _scene_glb("arvore")
        if arvore_glb != null:
            arvore_glb.position = base
            var s_var := rng.randf_range(0.92, 1.14)
            arvore_glb.scale = Vector3(s_var, s_var, s_var)
            arvore_glb.rotation.y = rng.randf_range(0.0, TAU)
            raiz.add_child(arvore_glb)
            _marca(arvore_glb, "arvore")
        else:
            # tronco conico (largo no pe, fino no topo) com casca
            var conico := CylinderMesh.new()
            conico.top_radius = tronco_r * 0.62
            conico.bottom_radius = tronco_r * 1.45
            conico.height = tronco_h
            conico.radial_segments = 9
            var tronco := _malha(conico, material(spec, "madeira"),
                    base + Vector3(0.0, tronco_h * 0.5, 0.0), raiz, "Tronco", true)
            _marca(tronco, "arvore")
            # galhos baixos (duas pernas de apoio inclinadas)
            for sinal in [-1.0, 1.0]:
                var galho := _malha(_cyl(tronco_r * 0.35, tronco_h * 0.55, 6),
                        material(spec, "madeira"),
                        base + Vector3(sinal * tronco_h * 0.10, tronco_h * 0.72, 0.0), raiz, "Galho", true)
                galho.rotation.z = sinal * 0.85
            # copa em cachos irregulares (nunca uma bola unica)
            var cachos := rng.randi_range(4, 5)
            for i in range(cachos):
                var angulo := TAU * float(i) / float(cachos) + rng.randf_range(-0.4, 0.4)
                var raio_cacho := copa_r * rng.randf_range(0.52, 0.78)
                var afast := copa_r * rng.randf_range(0.34, 0.62)
                var altura_cacho := tronco_h + copa_r * (0.55 + 0.16 * float(i % 2))
                var folha := _malha(_sphere(raio_cacho), material(spec, "folhagem"),
                        base + Vector3(cos(angulo) * afast, altura_cacho, sin(angulo) * afast),
                        raiz, "Copa", true)
                # copa achatada de verdade: mais larga que alta, sem forma de bola
                folha.scale = Vector3(1.0 + rng.randf_range(-0.1, 0.15), 0.62 + rng.randf_range(0.0, 0.14), 1.0 + rng.randf_range(-0.1, 0.12))
                _marca(folha, "folhagem")
            var coroa := _malha(_sphere(copa_r * 0.66), material(spec, "folhagem"),
                    base + Vector3(0.0, tronco_h + copa_r * 0.95, 0.0), raiz, "CoroaCopa", true)
            coroa.scale = Vector3(1.15, 0.58, 1.15)
            _marca(coroa, "folhagem")

        # Canteiro retangular moldado com granito e terra escura
        var moldura := _malha(_box(Vector3(1.4, 0.04, 1.4)), material(spec, "guia"),
                Vector3(x, 0.152, -z), raiz, "MolduraCanteiro", false)
        _marca(moldura, "guia")
        var canteiro := _malha(_box(Vector3(1.18, 0.045, 1.18)), material(spec, "canteiro"),
                Vector3(x, 0.154, -z), raiz, "Canteiro", false)
        _marca(canteiro, "canteiro")
        z += passo * rng.randf_range(0.85, 1.15)
        lado = -lado


static func _build_mobiliario(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, faixas: Dictionary, visibilidade: float) -> void:
    var props: Dictionary = spec.get("props", {})
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var calcada := float(faixas.get("calcada_lateral_m", 2.5))
    var x_faixa := -borda_esq + piso + calcada * 0.5
    # bancos de praca: assento de frente para a rua
    var cfg_banco: Dictionary = props.get("banco", {})
    var passo_banco := float(cfg_banco.get("espacamento_m", 14.0))
    var zb := rng.randf_range(3.0, passo_banco)
    while zb < comprimento - 3.0:
        _build_banco(spec, raiz, Vector3(x_faixa, 0.155, -zb), visibilidade)
        zb += passo_banco * rng.randf_range(0.9, 1.2)
    _build_prop_linear(spec, raiz, rng, comprimento, props, "lixeira", "zincado", 0.50, visibilidade)
    _build_prop_linear(spec, raiz, rng, comprimento, props, "orelhao", "estrutura_metalica", 1.80, visibilidade)

    # Postes de iluminacao publica de ferro fundido junto ao meio-fio
    var cfg_poste: Dictionary = props.get("poste", {})
    var passo_poste: float = float(cfg_poste.get("espacamento_m", 14.0))
    if passo_poste < 8.0:
        passo_poste = 14.0
    # ETAPA 18 — postes no ritmo GLOBAL (antes cada quarteirão sorteava o
    # primeiro poste e jogava um jitter no passo): é o que permite a fiação
    # aérea atravessar a emenda dos quarteirões sem cotovelo.
    var index: int = int(raiz.get_meta("spec_index", 0))
    var x_poste := -borda_esq + 0.20
    var postes_z: Array = _ritmo_global(index, comprimento, passo_poste)
    var xf_grime_poste: Array = []
    for zp in postes_z:
        var poste_glb := _prop_glb("poste")
        if poste_glb != null:
            # Junto a guia, braco de iluminacao virado para a rua (-X)
            poste_glb.position = Vector3(x_poste, 0.15, -zp)
            poste_glb.rotation.y = PI
            raiz.add_child(poste_glb)
            _marca(poste_glb, "prop")
        # encardido no pé do poste (mancha achatada no chão, mesma posição)
        xf_grime_poste.append(_xform(
            Vector3(x_poste, 0.156, -zp), Vector3(0.34, 0.01, 0.34)))
    _build_fiacao(spec, raiz, postes_z, x_poste, passo_poste,
            float(cfg_poste.get("altura_m", 3.65)))
    _build_jardineiras(spec, raiz, index, comprimento, x_faixa, visibilidade)
    var grime_poste: Dictionary = rua_viva(spec, "encardido")
    if not xf_grime_poste.is_empty() and _tier_atual() <= 2 \
            and bool(grime_poste.get("poste", true)):
        _multimesh(_box(Vector3.ONE), _mat_encardido(float(grime_poste.get("albedo", 0.42))),
                xf_grime_poste, raiz, "EncardidoPoste", false, 0.0)

    if rng.randf() < float(props.get("hidrante", {}).get("probabilidade", 0.0)):
        var zz := rng.randf_range(3.0, comprimento - 3.0)
        var hidrante_glb := _prop_glb("hidrante")
        if hidrante_glb != null:
            hidrante_glb.position = Vector3(_x_rua_esq(faixas) - 1.0, 0.15, -zz)
            raiz.add_child(hidrante_glb)
            _marca(hidrante_glb, "prop")
        else:
            var hidrante := _malha(_cyl(0.12, 0.75, 8), material(spec, "estrutura_metalica"),
                    Vector3(_x_rua_esq(faixas) - 1.0, 0.15 + 0.375, -zz), raiz,
                    "Hidrante", true, visibilidade)
            _marca(hidrante, "prop")

## Banco de praca: assento saliente de frente para a rua (encosto na faixa
## de props), com pe laterais, ripas do assento e do encosto.
static func _build_banco(spec: Dictionary, raiz: Node3D, pos: Vector3, visibilidade: float) -> void:
    var banco_glb := _prop_glb("banco")
    if banco_glb != null:
        banco_glb.position = pos
        # o GLB abre o assento para -Z; na calçada do kit a rua fica a oeste (-X)
        banco_glb.rotation.y = PI / 2.0
        raiz.add_child(banco_glb)
        _marca(banco_glb, "prop")
        return
    var madeira := material(spec, "madeira")
    var metal := material(spec, "estrutura_metalica")
    var corpo := Node3D.new()
    corpo.name = "BancoPraca"
    corpo.position = pos
    # comprimento ao longo da rua (Z); assento abre para -X (a rua fica a oeste)
    corpo.rotation.y = 0.0
    raiz.add_child(corpo)
    # pe laterais em aco
    for lado_z in [-0.72, 0.72]:
        var pe := _malha(_box(Vector3(0.44, 0.06, 0.08)), metal,
                Vector3(0.0, 0.03, lado_z), corpo, "BancoPe", true, visibilidade)
        _marca(pe, "prop")
        var haste := _malha(_box(Vector3(0.08, 0.44, 0.06)), metal,
                Vector3(0.0, 0.24, lado_z), corpo, "BancoHaste", true, visibilidade)
        _marca(haste, "prop")
        var encosto_pe := _malha(_box(Vector3(0.06, 0.52, 0.06)), metal,
                Vector3(0.26, 0.68, lado_z), corpo, "BancoEncostoPe", true, visibilidade)
        encosto_pe.rotation.x = -0.16
        _marca(encosto_pe, "prop")
    # ripas do assento (3) e do encosto (2), levemente inclinadas
    for i in range(3):
        var ripa := _malha(_box(Vector3(0.155, 0.035, 1.78)), madeira,
                Vector3(-0.19 + 0.165 * float(i), 0.455, 0.0), corpo, "BancoRipa", true, visibilidade)
        _marca(ripa, "prop")
    for i in range(2):
        var ripa_encosto := _malha(_box(Vector3(0.055, 0.135, 1.78)), madeira,
                Vector3(0.28 + 0.005 * float(i), 0.78 + 0.21 * float(i), 0.0), corpo,
                "BancoEncosto", true, visibilidade)
        ripa_encosto.rotation.x = -0.16
        _marca(ripa_encosto, "prop")


static func _build_prop_linear(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, props: Dictionary, nome: String, material_chave: String,
        altura: float, visibilidade: float) -> void:
    var cfg: Dictionary = props.get(nome, {})
    if cfg.is_empty():
        return
    var passo := float(cfg.get("espacamento_m", 999.0))
    var faixas: Dictionary = spec.get("faixas", {})
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var calcada := float(faixas.get("calcada_lateral_m", 2.5))
    var x_dir := borda_esq + piso + calcada * 0.5
    var x_esq := _x_rua_esq(faixas) - 1.0
    var z := rng.randf_range(2.0, passo)
    while z < comprimento - 1.0:
        var lado := 1.0 if rng.randf() < 0.5 else -1.0
        var x := x_dir if lado > 0.0 else x_esq
        var glb := _prop_glb(nome)
        if glb != null:
            # mobiliario original (Lote 6) em escala real, assentado no piso
            glb.position = Vector3(x, 0.15, -z)
            raiz.add_child(glb)
            _marca(glb, "prop")
        else:
            var no := _malha(_box(Vector3(0.6, altura, 1.6)), material(spec, material_chave),
                    Vector3(x, 0.15 + altura * 0.5, -z), raiz, nome.capitalize(),
                    true, visibilidade)
            _marca(no, "prop")
        z += passo * rng.randf_range(0.9, 1.2)

## Fiação aérea entre postes: 3 cabos por vão, cada um em 3 trechos que fazem a
## flecha (desce, atravessa, sobe). Tudo num multimesh só — o vão sai do ritmo
## global dos postes, então a rede continua de um quarteirão para o outro.
## Detalhe sutil: cai fora no degrau mais leve de qualidade.
static func _build_fiacao(spec: Dictionary, raiz: Node3D, postes_z: Array,
        x_poste: float, vao: float, altura_poste: float) -> void:
    var cfg: Dictionary = rua_viva(spec, "rua")
    if not bool(cfg.get("fiacao", true)) or postes_z.is_empty() or _tier_atual() > 2:
        return
    var n_cabos: int = clampi(int(cfg.get("fiacao_cabos", 3)), 1, 6)
    var flecha := maxf(0.05, float(cfg.get("fiacao_flecha_m", 0.45)))
    var y_topo := altura_poste - 0.35
    var trecho := vao / 3.0
    var giro: float = atan2(flecha, trecho)
    var comp_inclinado: float = sqrt(trecho * trecho + flecha * flecha)
    var cabos: Array = []
    for zp in postes_z:
        var z0 := float(zp)
        for c in range(n_cabos):
            var y := y_topo - float(c) * 0.16
            var x := x_poste - 0.10 - float(c) * 0.07
            # desce
            cabos.append(_xform_x(
                Vector3(x, y - flecha * 0.5, -(z0 + trecho * 0.5)),
                Vector3(0.03, 0.03, comp_inclinado), -giro))
            # atravessa no ponto mais baixo
            cabos.append(_xform_x(
                Vector3(x, y - flecha, -(z0 + vao * 0.5)),
                Vector3(0.03, 0.03, trecho), 0.0))
            # sobe para o próximo poste
            cabos.append(_xform_x(
                Vector3(x, y - flecha * 0.5, -(z0 + trecho * 2.5)),
                Vector3(0.03, 0.03, comp_inclinado), giro))
    if cabos.is_empty():
        return
    var no := _multimesh(_box(Vector3.ONE), _mat_cor("cabo", Color(0.09, 0.09, 0.10), 0.85),
            cabos, raiz, "FiacaoCabo", false, 0.0)
    _marca(no, "fiacao", "nenhum")


## Jardineiras de concreto na calçada (caixote + terra plantada), no ritmo
## global do capítulo. Dois multimesh para a rua inteira; adereço, entra só nos
## degraus de qualidade alto/médio.
static func _build_jardineiras(spec: Dictionary, raiz: Node3D, index: int,
        comprimento: float, x_faixa: float, visibilidade: float) -> void:
    var cfg: Dictionary = rua_viva(spec, "rua")
    if not bool(cfg.get("jardineira", true)) or _tier_atual() > 1:
        return
    var passo := maxf(4.0, float(cfg.get("jardineira_passo_m", 22.0)))
    var caixas: Array = []
    var plantas: Array = []
    for zj in _ritmo_global(index, comprimento, passo):
        caixas.append(_xform(Vector3(x_faixa + 0.35, 0.15 + 0.22, -float(zj)),
                Vector3(0.62, 0.44, 1.10)))
        plantas.append(_xform(Vector3(x_faixa + 0.35, 0.15 + 0.50, -float(zj)),
                Vector3(0.46, 0.34, 0.92)))
    if caixas.is_empty():
        return
    var caixa_no := _multimesh(_box(Vector3.ONE), material(spec, "guia"), caixas, raiz,
            "Jardineira", true, visibilidade)
    _marca(caixa_no, "jardineira")
    var planta_no := _multimesh(_box(Vector3.ONE), material(spec, "folhagem"), plantas, raiz,
            "JardineiraPlanta", false, visibilidade)
    _marca(planta_no, "folhagem", "nenhum")


static func _build_folhas(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, visibilidade: float) -> void:
    var cfg: Dictionary = spec.get("props", {}).get("folhas_no_chao", {})
    var quantas := int(cfg.get("por_quarteirao", 0))
    if quantas <= 0:
        return
    var raio := float(cfg.get("raio_m", 0.05))
    var faixas: Dictionary = spec.get("faixas", {})
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var piso := float(faixas.get("piso_central_m", 6.0))
    var calcada := float(faixas.get("calcada_lateral_m", 2.5))
    var xforms: Array = []
    for i in range(quantas):
        var x := rng.randf_range(-borda_esq + 0.2, -borda_esq + piso + calcada - 0.4)
        var z := rng.randf_range(0.5, comprimento - 0.5)
        xforms.append(_xform(Vector3(x, 0.155, -z), Vector3.ONE, rng.randf_range(0.0, TAU)))
    _multimesh(_box(Vector3(raio * 2.0, 0.006, raio * 2.0)), material(spec, "folhagem"),
            xforms, raiz, "Folhas", false, visibilidade)


static func _build_passaros(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        comprimento: float, visibilidade: float) -> void:
    var cfg: Dictionary = spec.get("props", {}).get("passaro", {})
    var quantas := int(cfg.get("por_quarteirao", 0))
    if quantas <= 0:
        return
    var xforms: Array = []
    for i in range(quantas):
        var lado := 1.0 if rng.randf() < 0.5 else -1.0
        var x := lado * rng.randf_range(1.2, 3.6)
        var no_chao := rng.randf() < 0.6
        var y := 0.16 if no_chao else rng.randf_range(2.0, 3.8)
        var z := rng.randf_range(1.5, comprimento - 1.5)
        var rot_y := rng.randf_range(0.0, TAU)
        xforms.append(_xform(Vector3(x, y, -z), Vector3(0.16, 0.12, 0.22), rot_y))
    _multimesh(_box(Vector3.ONE), material(spec, "zincado"),
            xforms, raiz, "Passaros", false, visibilidade)


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
    # nevoa = peso da cor de nevoa (antes os argumentos estavam invertidos:
    # nevoa 0.78 produzia blocos 78% cinza, os "cartões" duros no horizonte).
    var cor := _misturar(Color(0.55, 0.58, 0.62), nevoa_cor, nevoa)
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

    func setup(caminho_spec: String = "res://resources/world_spec.json", overrides: Dictionary = {}) -> void:
        name = "Cenario"
        spec = BuildingKit.spec_with_overrides(BuildingKit.load_spec(caminho_spec), overrides)
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
        # O no reciclado ocupa a posicao do novo indice (sem isso, o conteudo
        # reconstruido nasceria no lugar do quarteirao antigo, atras do corredor).
        no.position = novo.position
        for filho in novo.get_children():
            novo.remove_child(filho)
            no.add_child(filho)
        novo.queue_free()

    func paleta_do_capitulo(indice: int) -> Dictionary:
        return BuildingKit.chapter_profile(spec, indice)
