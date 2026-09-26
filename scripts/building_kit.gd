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
static func _rng(spec: Dictionary, indice: int) -> RandomNumberGenerator:
    var rng := RandomNumberGenerator.new()
    rng.seed = int(spec.get("seed", 1)) * 7919 + indice * 104729
    return rng


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
            if tipo != "obra":
                _build_janelas(spec, raiz, rng, janela, lado, x_frente, z, largura, andares, pe, tipo, lote)
            if tipo == "loja":
                _build_loja(spec, raiz, p, lado, x_frente, z, largura, lote)
            z += largura
            lote += 1

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


static func _build_janelas(spec: Dictionary, raiz: Node3D, rng: RandomNumberGenerator,
        janela: Dictionary, lado: float, x_frente: float, z: float, largura: float,
        andares: int, pe: float, tipo: String, indice: int = 0) -> void:
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
            "Janelas%s%d" % [("D" if lado > 0.0 else "E"), indice], false)


static func _build_loja(spec: Dictionary, raiz: Node3D, p: Dictionary, lado: float,
        x_frente: float, z: float, largura: float, indice: int = 0) -> void:
    var loja: Dictionary = p.get("loja", {})
    var altura_toldo := float(loja.get("toldo_altura_m", 2.6))
    var prof := float(loja.get("toldo_profundidade_m", 1.1))
    var porta_l := float(loja.get("porta_largura_m", 1.6))
    var porta_a := float(loja.get("porta_altura_m", 2.4))
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
        # Seleciona entre ipê amarelo florido, árvore urbana e palmeira
        var arvore_nome: String = "ipe_amarelo" if (int(z * 7) % 3 == 0) else ("arvore" if (int(z * 7) % 3 == 1) else "palmeira")
        if cfg.has("glb"):
            arvore_nome = str(cfg["glb"])
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
    var zp := rng.randf_range(5.0, 9.0)
    while zp < comprimento - 3.0:
        var poste_glb := _prop_glb("poste")
        if poste_glb != null:
            # Junto a guia, braco de iluminacao virado para a rua (-X)
            poste_glb.position = Vector3(-borda_esq + 0.20, 0.15, -zp)
            poste_glb.rotation.y = PI
            raiz.add_child(poste_glb)
            _marca(poste_glb, "prop")
        zp += passo_poste * rng.randf_range(0.95, 1.10)

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
