class_name WeatherSystem
extends Node3D
## Clima do Lote 4: chuva, relampago, asfalto molhado, pocas e sonda de reflexo.
##
## Le resources/weather_spec.json (fonte unica da verdade) e aplica o estado de
## clima por cima do que o Lote 2/3 montou: energia do sol, densidade da nevoa,
## energia do ambiente, nuvens do ceu, brilho (rugosidade) dos materiais, pocas
## no asfalto, chuva em GPU e relampago com trovao.
##
## Regras:
##   - nenhum numero de clima fica no codigo: tudo vem do spec;
##   - semente fixa: os relampagos e as pocas saem sempre iguais (auditavel);
##   - orcamento do Adreno 610: chuva limitada, uma luz extra (sem sombra),
##     sonda de reflexo so no Forward+;
##   - o clima REAPLICA o estado a cada `transicoes.reaplicar_s` segundos, para
##     ganhar de qualquer outro sistema que mexa no sol/nevoa depois dele;
##   - `get_wetness()` fica pronto para o Lote 5 (fisica: atrito na pista molhada).
##
## Uso no jogo:
##   var clima := WeatherSystem.new()
##   add_child(clima)
##   clima.setup(_render_profile(), WORLD_Y_OFFSET)
##   clima.set_chapter(indice_do_capitulo)
##   clima.update_head(distancia_percorrida)   # junto do update_head do kit

const SPEC_PATH := "res://resources/weather_spec.json"
const KIT_SPEC_PATH := "res://resources/world_spec.json"

var spec: Dictionary = {}
var _perfil: Dictionary = {}
var _estado := "limpo"
var _indice_capitulo := 0
var _estado_suave := {}                 # estado atual interpolado (transicao)
var _transicao := {}
var _molhado := 0.0
var _alvo_molhado := 0.0
var _molhado_aplicado := -1.0
var _y_piso := 0.0

var _rng := RandomNumberGenerator.new()
var _sol: DirectionalLight3D = null
var _env: Environment = null
var _ceu_material: Material = null
var _camera: Camera3D = null
var _chuva: GPUParticles3D = null
var _luz_relampago: DirectionalLight3D = null
var _tira: ColorRect = null
var _pocas: MultiMeshInstance3D = null
var _sonda: ReflectionProbe = null
var _trovao: AudioStreamPlayer3D = null

var _base_sol := 1.1
var _base_nevoa := 0.5
var _base_ambiente := 0.62
var _base_nuvens := 0.3
var _base_turbidez := 10.0
var _bases_capturadas := false
var _base_materiais: Dictionary = {}
var _materiais: Dictionary = {}
var _metodo := "forward_plus"

var _proximo_relampago := 0.0
var _flash_aceso := 0
var _flash_apagado := 0
var _flash_restante := 0
var _trovao_espera := -1.0
var _tempo_reassert := 0.0
var _trecho := -2147483647
var _aviso_textura := false


# ---------------------------------------------------------------------------
# Montagem
# ---------------------------------------------------------------------------

func setup(perfil: Dictionary = {}, y_piso: float = 0.0) -> void:
    _perfil = perfil.duplicate(true)
    _y_piso = y_piso
    spec = _ler_spec(SPEC_PATH)
    if spec.is_empty():
        push_error("[clima] weather_spec.json ausente ou invalido; clima desligado")
        set_process(false)
        return
    _metodo = String(RenderingServer.get_current_rendering_method())
    _rng.seed = int(spec.get("seed", 1)) * 2654435761 + 17
    _transicao = spec.get("transicoes", {})
    _estado_suave = _estado_do_spec(_estado).duplicate(true)
    _capturar_bases()
    _montar_chuva()
    _montar_relampago()
    _montar_pocas()
    _montar_sonda()
    _montar_trovao()
    set_process(true)
    print("[clima] sistema pronto | metodo=%s | estados=%s" % [_metodo, ",".join(_nomes_dos_estados())])


func _ler_spec(caminho: String) -> Dictionary:
    var texto := FileAccess.get_file_as_string(caminho)
    if texto.is_empty():
        return {}
    var dados = JSON.parse_string(texto)
    if typeof(dados) != TYPE_DICTIONARY:
        return {}
    return dados


func _nomes_dos_estados() -> Array:
    var nomes: Array = []
    for chave in spec.get("estados", {}).keys():
        nomes.append(String(chave))
    return nomes


func _estado_do_spec(nome: String) -> Dictionary:
    var estados: Dictionary = spec.get("estados", {})
    if estados.has(nome):
        return estados[nome]
    return {}


# ---------------------------------------------------------------------------
# Chuva
# ---------------------------------------------------------------------------

func _montar_chuva() -> void:
    var cfg: Dictionary = spec.get("chuva", {})
    var malha_cfg: Array = cfg.get("malha_m", [0.02, 0.7, 0.02])
    var malha := BoxMesh.new()
    malha.size = Vector3(float(malha_cfg[0]), float(malha_cfg[1]), float(malha_cfg[2]))
    var mat := StandardMaterial3D.new()
    var cor: Array = cfg.get("cor", [0.72, 0.78, 0.9, 0.55])
    mat.albedo_color = Color(float(cor[0]), float(cor[1]), float(cor[2]), float(cor[3]))
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    mat.vertex_color_use_as_albedo = true
    mat.albedo_texture = null
    mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
    malha.material = mat

    var processo := ParticleProcessMaterial.new()
    processo.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
    var area: Array = cfg.get("area_m", [44.0, 26.0, 44.0])
    processo.emission_box_extents = Vector3(float(area[0]) * 0.5, float(area[1]) * 0.5, float(area[2]) * 0.5)
    processo.gravity = Vector3(0.0, -9.8, 0.0)
    processo.spread = 0.0
    processo.particle_flag_align_y = true
    processo.scale_min = 1.0
    processo.scale_max = 1.0
    processo.color = Color(1.0, 1.0, 1.0, 1.0)

    var chuva := GPUParticles3D.new()
    chuva.name = "Chuva"
    chuva.draw_pass_1 = malha
    chuva.process_material = processo
    chuva.lifetime = float(cfg.get("lifetime_s", 1.1))
    chuva.preprocess = 1.0
    chuva.explosiveness = 0.0
    chuva.randomness = 0.2
    chuva.fixed_fps = int(cfg.get("fixed_fps", 30))
    chuva.interpolate = true
    chuva.local_coords = true
    chuva.emitting = false
    chuva.amount = 0
    chuva.visibility_aabb = AABB(
        Vector3(-float(area[0]) * 0.5, -float(area[1]) * 0.5 - float(cfg.get("altura_m", 18.0)) * 0.5, -float(area[2]) * 0.5),
        Vector3(float(area[0]), float(area[1]) + float(cfg.get("altura_m", 18.0)), float(area[2])))
    add_child(chuva)
    _chuva = chuva


func _atualizar_chuva(estado_nome: String, suave: Dictionary) -> void:
    if _chuva == null:
        return
    var cfg: Dictionary = spec.get("chuva", {})
    var por_estado: Dictionary = cfg.get("estados", {})
    var dados: Dictionary = por_estado.get(estado_nome, {})
    var quantidade := int(dados.get("quantidade", 0))
    var orcamento: Dictionary = cfg.get("orcamento", {})
    var teto := int(orcamento.get("max_particulas_mobile", 1200))
    if _metodo != "mobile":
        teto = int(orcamento.get("max_particulas_desktop", teto))
    if quantidade > teto:
        quantidade = teto
    if quantidade <= 0:
        _chuva.emitting = false
        _chuva.amount = 0
        return
    _chuva.amount = quantidade
    _chuva.emitting = true
    var processo := _chuva.process_material as ParticleProcessMaterial
    if processo == null:
        return
    var v := float(dados.get("velocidade_ms", 20.0))
    processo.initial_velocity_min = v * 0.85
    processo.initial_velocity_max = v
    var incl: Array = dados.get("inclinacao", [0.0, -1.0, 0.0])
    processo.direction = Vector3(float(incl[0]), float(incl[1]), float(incl[2])).normalized()
    var escala := float(dados.get("escala", 1.0)) * (1.0 + 0.4 * float(suave.get("molhado_alvo", 0.0)))
    processo.scale_min = escala
    processo.scale_max = escala * 1.15


# ---------------------------------------------------------------------------
# Relampago e trovao
# ---------------------------------------------------------------------------

func _montar_relampago() -> void:
    var cfg: Dictionary = spec.get("relampago", {})
    var luz := DirectionalLight3D.new()
    luz.name = "LuzRelampago"
    luz.light_energy = 0.0
    luz.light_specular = 0.1
    luz.shadow_enabled = false
    luz.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
    luz.visible = false
    var cor: Array = cfg.get("cor", [0.85, 0.9, 1.0])
    luz.light_color = Color(float(cor[0]), float(cor[1]), float(cor[2]), 1.0)
    add_child(luz)
    _luz_relampago = luz

    var camada := CanvasLayer.new()
    camada.name = "CamadaRelampago"
    camada.layer = 100
    add_child(camada)
    var tira := ColorRect.new()
    tira.name = "TiraRelampago"
    tira.anchor_right = 1.0
    tira.anchor_bottom = 1.0
    tira.mouse_filter = Control.MOUSE_FILTER_IGNORE
    var alpha: float = float(cfg.get("tira_alpha", 0.2))
    tira.color = Color(float(cor[0]), float(cor[1]), float(cor[2]), 0.0)
    camada.add_child(tira)
    _tira = tira
    _tira.set_meta("alpha_pico", alpha)


func _montar_trovao() -> void:
    var cfg: Dictionary = spec.get("relampago", {}).get("trovejar", {})
    var caminho := String(cfg.get("arquivo", ""))
    if caminho.is_empty() or not ResourceLoader.exists(caminho):
        if not _aviso_textura:
            _aviso_textura = true
            push_warning("[clima] som do trovao ausente (%s); relampago segue sem audio" % caminho)
        return
    var audio := AudioStreamPlayer3D.new()
    audio.name = "Trovao"
    audio.stream = ResourceLoader.load(caminho)
    audio.max_distance = 600.0
    audio.volume_db = float(cfg.get("volume_db", [-9.0, -4.0])[0])
    add_child(audio)
    _trovao = audio


func _agendar_relampago() -> void:
    var cfg: Dictionary = spec.get("relampago", {})
    var faixa: Array = cfg.get("intervalo_s", [5.0, 12.0])
    _proximo_relampago = _rng.randf_range(float(faixa[0]), float(faixa[1]))


func _disparar_relampago() -> void:
    var cfg: Dictionary = spec.get("relampago", {})
    _flash_aceso = max(1, int(cfg.get("quadros_aceso", 3)))
    _flash_restante = max(0, int(cfg.get("piscadas", 2)) - 1)
    var trovejar: Dictionary = cfg.get("trovejar", {})
    var atraso: Array = trovejar.get("atraso_s", [0.8, 2.5])
    _trovao_espera = _rng.randf_range(float(atraso[0]), float(atraso[1]))
    # a luz do relampago vem da direcao da tempestade (oposta ao sol no ceu)
    if _luz_relampago != null and _sol != null:
        _luz_relampago.rotation = _sol.rotation
        _luz_relampago.rotation_degrees = _sol.rotation_degrees + Vector3(-35.0, 25.0, 0.0)


func _atualizar_relampago(delta: float) -> void:
    var ativo := _estado_tem_relampago()
    if not ativo:
        _flash_aceso = 0
        _flash_apagado = 0
        _flash_restante = 0
        if _luz_relampago != null:
            _luz_relampago.visible = false
            _luz_relampago.light_energy = 0.0
        if _tira != null:
            _tira.color.a = 0.0
        return
    _proximo_relampago -= delta
    if _proximo_relampago <= 0.0 and _flash_aceso <= 0 and _flash_apagado <= 0:
        _disparar_relampago()
        _agendar_relampago()
    if _flash_aceso > 0:
        _flash_aceso -= 1
        if _flash_aceso == 0 and _flash_restante > 0:
            _flash_restante -= 1
            _flash_apagado = 4
    elif _flash_apagado > 0:
        _flash_apagado -= 1
        if _flash_apagado == 0 and _flash_restante > 0:
            _flash_restante -= 1
            _flash_aceso = max(1, int(spec.get("relampago", {}).get("quadros_aceso", 3)) - 1)
    _mostrar_flash(_flash_aceso > 0)


func _mostrar_flash(aceso: bool) -> void:
    var cfg: Dictionary = spec.get("relampago", {})
    if _luz_relampago != null:
        _luz_relampago.visible = aceso
        _luz_relampago.light_energy = float(cfg.get("energia_pico", 0.0)) if aceso else 0.0
    if _tira != null:
        var pico: float = float(_tira.get_meta("alpha_pico", 0.2))
        var alvo := pico if aceso else 0.0
        var atual := _tira.color.a
        _tira.color = Color(_tira.color.r, _tira.color.g, _tira.color.b,
                lerpf(atual, alvo, 0.55))


func _estado_tem_relampago() -> bool:
    var lista: Array = spec.get("relampago", {}).get("estados", [])
    return lista.has(_estado)


func _atualizar_trovao(delta: float) -> void:
    if _trovao_espera < 0.0:
        return
    _trovao_espera -= delta
    if _trovao_espera > 0.0:
        return
    _trovao_espera = -1.0
    if _trovao == null:
        return
    var trovejar: Dictionary = spec.get("relampago", {}).get("trovejar", {})
    var faixa: Array = trovejar.get("volume_db", [-9.0, -4.0])
    _trovao.volume_db = _rng.randf_range(float(faixa[0]), float(faixa[1]))
    if _camera != null:
        var altura := float(spec.get("relampago", {}).get("trovejar", {}).get("altura_m", 0.0))
        var distancia := float(spec.get("relampago", {}).get("trovejar", {}).get("distancia_m", 0.0))
        _trovao.global_position = _camera.global_position + Vector3(0.0, altura, -distancia)
    _trovao.play()


# ---------------------------------------------------------------------------
# Pocas
# ---------------------------------------------------------------------------

func _montar_pocas() -> void:
    var cfg: Dictionary = spec.get("pocas", {})
    var malha := BoxMesh.new()
    malha.size = Vector3(1.0, 0.01, 1.0)
    var mat := StandardMaterial3D.new()
    var cor: Array = cfg.get("cor", [0.05, 0.06, 0.07, 1.0])
    mat.albedo_color = Color(float(cor[0]), float(cor[1]), float(cor[2]), float(cor[3]))
    mat.roughness = float(cfg.get("rugosidade", 0.06))
    mat.metallic = 0.0
    mat.metallic_specular = float(cfg.get("especular", 0.85))
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
    malha.material = mat
    var n: int = int(cfg.get("quantidade_por_trecho", 12)) * maxi(1, int(cfg.get("trechos_a_vista", 3)))
    var mm := MultiMesh.new()
    mm.transform_format = MultiMesh.TRANSFORM_3D
    mm.mesh = malha
    mm.instance_count = n
    var no := MultiMeshInstance3D.new()
    no.name = "Pocas"
    no.multimesh = mm
    no.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    no.visible = false
    add_child(no)
    _pocas = no


## Reposiciona as pocas no trecho em que o jogador esta (deterministico por trecho).
func update_head(distancia: float) -> void:
    if _pocas == null or spec.is_empty():
        return
    var kit := _ler_spec(KIT_SPEC_PATH)
    var trecho_m := float(kit.get("quarteirao", {}).get("comprimento_m", 28.0))
    var indice := int(floor(distancia / trecho_m))
    if indice == _trecho:
        return
    _trecho = indice
    _reconstruir_pocas(indice, trecho_m, kit)


func _reconstruir_pocas(trecho: int, trecho_m: float, kit: Dictionary) -> void:
    var cfg: Dictionary = spec.get("pocas", {})
    var quantas := int(cfg.get("quantidade_por_trecho", 12))
    var visiveis: int = maxi(1, int(cfg.get("trechos_a_vista", 3)))
    var faixas: Dictionary = kit.get("faixas", {})
    var piso := float(faixas.get("piso_central_m", 6.0))
    var borda_esq := float(faixas.get("piso_borda_esq_m", 1.35))
    var pista := float(faixas.get("pista_m", 6.6))
    var afast := float(cfg.get("afastamento_guia_m", 0.5))
    var x_rua_dir := -borda_esq - float(faixas.get("guia_largura_m", 0.35))
    var tam: Array = cfg.get("tamanho_m", [1.0, 1.0, 2.0, 1.0])
    var altura := float(cfg.get("altura_do_piso_m", 0.006))
    var mm: MultiMesh = _pocas.multimesh
    var total := quantas * visiveis
    if mm.instance_count != total:
        mm.instance_count = total
    var i := 0
    for passo in range(visiveis):
        var rng := RandomNumberGenerator.new()
        rng.seed = int(spec.get("seed", 1)) * 97 + (trecho + passo + 100000) * 7919
        for _n in range(quantas):
            var no_piso := rng.randf() < 0.4
            var x := 0.0
            var y := _y_piso + 0.15 + altura
            if no_piso:
                # pocas rasas no deck da calcada (por onde o corredor passa)
                x = rng.randf_range(-borda_esq + 0.4, -borda_esq + piso - 0.4)
            else:
                # pocas na pista, comecando coladas na guia
                x = x_rua_dir - afast - rng.randf_range(0.2, pista - 0.6)
                y = _y_piso + altura
            var z := -((float(trecho) + float(passo)) * trecho_m) - rng.randf_range(0.5, trecho_m - 0.5)
            var larg := rng.randf_range(float(tam[0]), float(tam[1]))
            var comp := rng.randf_range(float(tam[2]), float(tam[3]))
            var giro := rng.randf_range(-0.4, 0.4)
            var base := Basis.from_euler(Vector3(0.0, giro, 0.0)).scaled(Vector3(larg, 1.0, comp))
            mm.set_instance_transform(i, Transform3D(base, Vector3(x, y, z)))
            i += 1
    # as pocas tambem podem aparecer na calcada (poca rasa perto da guia)
    if _pocas.visible == false and _molhado >= float(cfg.get("aparecer_em", 0.45)):
        _pocas.visible = true


# ---------------------------------------------------------------------------
# Sonda de reflexo
# ---------------------------------------------------------------------------

func _montar_sonda() -> void:
    var cfg: Dictionary = spec.get("sonda", {})
    var permitido := bool(cfg.get("ativo_forward_plus", true)) if _metodo == "forward_plus" \
            else bool(cfg.get("ativo_mobile", false))
    if not permitido:
        print("[clima] sonda de reflexo desligada no renderizador %s" % _metodo)
        return
    var tamanho: Array = cfg.get("tamanho_m", [52.0, 16.0, 64.0])
    var sonda := ReflectionProbe.new()
    sonda.name = "SondaClima"
    sonda.size = Vector3(float(tamanho[0]), float(tamanho[1]), float(tamanho[2]))
    sonda.intensity = float(cfg.get("intensidade", 0.55))
    sonda.box_projection = bool(cfg.get("box_projection", true))
    sonda.update_mode = ReflectionProbe.UPDATE_ALWAYS if bool(cfg.get("atualizar_sempre", false)) \
            else ReflectionProbe.UPDATE_ONCE
    sonda.max_distance = float(tamanho[2])
    sonda.enable_shadows = false
    add_child(sonda)
    _sonda = sonda


# ---------------------------------------------------------------------------
# Estado de clima
# ---------------------------------------------------------------------------

func set_chapter(indice: int) -> void:
    _indice_capitulo = indice
    var mapa: Array = spec.get("mapa_capitulo", [])
    if mapa.is_empty():
        return
    set_state(String(mapa[posmod(indice, mapa.size())]))


func set_state(nome: String) -> void:
    if spec.is_empty() or not spec.get("estados", {}).has(nome):
        return
    if nome == _estado:
        _aplicar_estado()
        return
    _estado = nome
    _agendar_relampago()
    _aplicar_estado()
    print("[clima] estado=%s molhado_alvo=%.2f chuva=%d" % [
        _estado, float(_alvo_molhado), _quantidade_de_chuva()])


func get_state() -> String:
    return _estado


func get_wetness() -> float:
    return _molhado


func _quantidade_de_chuva() -> int:
    var cfg: Dictionary = spec.get("chuva", {}).get("estados", {})
    return int(cfg.get(_estado, {}).get("quantidade", 0))


## Interpola o estado atual (a transicao e suave, sem "pulo" de luz).
func _atualizar_transicao(delta: float) -> void:
    var alvo := _estado_do_spec(_estado)
    if alvo.is_empty():
        return
    var segundos := maxf(0.1, float(_transicao.get("estado_s", 5.0)))
    var t := clampf(delta / segundos, 0.0, 1.0)
    for chave in alvo.keys():
        var valor = alvo[chave]
        if typeof(valor) == TYPE_FLOAT or typeof(valor) == TYPE_INT:
            if not _estado_suave.has(chave):
                _estado_suave[chave] = float(valor)
            _estado_suave[chave] = lerpf(float(_estado_suave[chave]), float(valor), t)


func _aplicar_estado() -> void:
    if spec.is_empty():
        return
    _capturar_bases()
    var suave := _estado_suave if not _estado_suave.is_empty() else _estado_do_spec(_estado)
    if _sol != null:
        _sol.light_energy = _base_sol * float(suave.get("sol_multiplicador", 1.0))
    if _env != null:
        _env.fog_density = _base_nevoa * float(suave.get("nevoa_multiplicador", 1.0))
        _env.ambient_light_energy = _base_ambiente * float(suave.get("ambiente_multiplicador", 1.0))
        _aplicar_nuvens(float(suave.get("nuvens", _base_nuvens)),
                float(suave.get("turbidez_extra", 0.0)), float(suave.get("cinza", 0.0)))
    _alvo_molhado = float(suave.get("molhado_alvo", 0.0))
    _atualizar_chuva(_estado, suave)


func _aplicar_nuvens(nuvens: float, turbidez_extra: float, cinza: float) -> void:
    if _ceu_material == null:
        if _env != null and _env.sky != null:
            _ceu_material = _env.sky.sky_material
    if _ceu_material == null:
        return
    var cfg_ceu: Dictionary = spec.get("ceu", {})
    var cor_alto := _cor(cfg_ceu.get("sobrecast_cor_alto", [0.6, 0.63, 0.67]))
    var cor_horizonte := _cor(cfg_ceu.get("sobrecast_cor_horizonte", [0.72, 0.74, 0.77]))
    var tinta := _cor(cfg_ceu.get("tinta_cobertura", [0.92, 0.94, 1.0]))
    var base_alto := _cor(_perfil.get("sky_top", [0.32, 0.48, 0.72]))
    var base_horizonte := _cor(_perfil.get("sky_horizon", [0.82, 0.80, 0.76]))
    if _ceu_material is ProceduralSkyMaterial:
        var proc := _ceu_material as ProceduralSkyMaterial
        proc.sky_top_color = base_alto.lerp(cor_alto, clampf(cinza, 0.0, 1.0))
        proc.sky_horizon_color = base_horizonte.lerp(cor_horizonte, clampf(cinza, 0.0, 1.0))
        proc.sky_energy_multiplier = lerpf(1.0, float(cfg_ceu.get("energia_minima", 0.5)),
                clampf(cinza, 0.0, 1.0))
        # nuvens: sky_cover e uma TEXTURA (equirretangular); a forca vem da tinta
        var minimo := float(cfg_ceu.get("cobertura_minima_para_textura", 0.02))
        if nuvens <= minimo:
            proc.sky_cover = null
        else:
            var caminho := String(cfg_ceu.get("textura", ""))
            if not caminho.is_empty() and ResourceLoader.exists(caminho):
                proc.sky_cover = ResourceLoader.load(caminho)
                proc.sky_cover_modulate = Color(tinta.r * nuvens, tinta.g * nuvens,
                        tinta.b * nuvens, clampf(nuvens, 0.0, 1.0))
            elif not _aviso_textura:
                _aviso_textura = true
                push_warning("[clima] textura de nuvens ausente (%s); ceu segue sem nuvens" % caminho)
    elif _ceu_material is PhysicalSkyMaterial:
        var fis := _ceu_material as PhysicalSkyMaterial
        fis.turbidity = clampf(_base_turbidez + turbidez_extra, 0.0, 40.0)
        fis.rayleigh_color = _cor(_perfil.get("sky_top", [0.32, 0.48, 0.72])).lerp(
                cor_alto, clampf(cinza, 0.0, 1.0))


static func _cor(v) -> Color:
    if v is Color:
        return v
    if v is Array and (v as Array).size() >= 3:
        var a: Array = v
        return Color(float(a[0]), float(a[1]), float(a[2]), 1.0)
    return Color.WHITE


func _atualizar_molhado(delta: float) -> void:
    var segundos := float(_transicao.get("molhagem_s", 3.0))
    if _alvo_molhado < _molhado:
        segundos = float(_transicao.get("secagem_s", 16.0))
    if segundos <= 0.0:
        _molhado = _alvo_molhado
    else:
        var passo := clampf(delta / segundos, 0.0, 1.0)
        _molhado = lerpf(_molhado, _alvo_molhado, passo)
    if absf(_molhado - _molhado_aplicado) < 0.004:
        return
    _molhado_aplicado = _molhado
    _aplicar_molhado(_molhado)
    if _pocas != null:
        var cfg: Dictionary = spec.get("pocas", {})
        _pocas.visible = _molhado >= float(cfg.get("aparecer_em", 0.45))


func _aplicar_molhado(w: float) -> void:
    var tabela: Dictionary = spec.get("molhado", {}).get("materiais", {})
    var kit := _ler_spec(KIT_SPEC_PATH)
    for chave in tabela.keys():
        var mat := _material_do_kit(kit, String(chave))
        if mat == null:
            continue
        var cfg: Dictionary = tabela[chave]
        var r_seca := float(cfg.get("rugosidade_seca", 1.0))
        var r_molhada := float(cfg.get("rugosidade_molhada", r_seca))
        var albedo_molhado := float(cfg.get("albedo_molhado", 1.0))
        var especular_extra := float(cfg.get("especular_extra", 0.0))
        if not _base_materiais.has(chave):
            _base_materiais[chave] = {
                "cor": mat.albedo_color,
                "especular": mat.metallic_specular,
            }
        var base: Dictionary = _base_materiais[chave]
        mat.roughness = lerpf(r_seca, r_molhada, w)
        var cor: Color = base["cor"]
        mat.albedo_color = Color(cor.r * lerpf(1.0, albedo_molhado, w),
                cor.g * lerpf(1.0, albedo_molhado, w),
                cor.b * lerpf(1.0, albedo_molhado, w), cor.a)
        mat.metallic_specular = clampf(float(base["especular"]) + especular_extra * w, 0.0, 1.0)


func _material_do_kit(kit: Dictionary, chave: String) -> BaseMaterial3D:
    if _materiais.has(chave):
        return _materiais[chave]
    if kit.is_empty():
        return null
    var mat := BuildingKit.material(kit, chave)
    if mat is BaseMaterial3D:
        _materiais[chave] = mat
        return mat
    return null


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------

func _process(delta: float) -> void:
    if spec.is_empty():
        return
    _atualizar_transicao(delta)
    _atualizar_molhado(delta)
    _atualizar_relampago(delta)
    _atualizar_trovao(delta)
    _seguir_camera()
    _tempo_reassert -= delta
    if _tempo_reassert <= 0.0:
        _tempo_reassert = float(_transicao.get("reaplicar_s", 2.0))
        _aplicar_estado()


func _seguir_camera() -> void:
    var cam := _camera if _camera != null else _achar_camera()
    if cam == null:
        return
    _camera = cam
    if _chuva != null:
        var cfg: Dictionary = spec.get("chuva", {})
        var area: Array = cfg.get("area_m", [44.0, 26.0, 44.0])
        _chuva.global_position = cam.global_position + Vector3(0.0, float(area[1]) * 0.5 + 2.0, 0.0)
    if _sonda != null:
        _sonda.global_position = cam.global_position + Vector3(0.0, -4.0, -18.0)


func _achar_camera() -> Camera3D:
    var achados := get_tree().root.find_children("*", "Camera3D", true, false)
    if achados.is_empty():
        return null
    return achados[0] as Camera3D


## Captura os valores base (do perfil do Lote 2, ou do ambiente que ja existe).
func _capturar_bases() -> void:
    if _sol == null:
        var luzes := get_tree().root.find_children("*", "DirectionalLight3D", true, false)
        for no in luzes:
            var d := no as DirectionalLight3D
            if d != null and d.name != "LuzRelampago":
                _sol = d
                break
    if _env == null:
        var ambientes := get_tree().root.find_children("*", "WorldEnvironment", true, false)
        if not ambientes.is_empty():
            var we := ambientes[0] as WorldEnvironment
            if we != null:
                _env = we.environment
    if _bases_capturadas:
        return
    if not _perfil.is_empty():
        _base_sol = float(_perfil.get("sun_energy", _base_sol))
        _base_nevoa = float(_perfil.get("fog_density", _base_nevoa))
        _base_ambiente = float(_perfil.get("ambient_energy", _base_ambiente))
        _base_nuvens = float(_perfil.get("clouds", _base_nuvens))
    else:
        if _sol != null:
            _base_sol = _sol.light_energy
        if _env != null:
            _base_nevoa = _env.fog_density
            _base_ambiente = _env.ambient_light_energy
    if _env != null and _env.sky != null and _env.sky.sky_material is PhysicalSkyMaterial:
        _base_turbidez = (_env.sky.sky_material as PhysicalSkyMaterial).turbidity
    _bases_capturadas = true
    print("[clima] bases: sol=%.2f nevoa=%.2f ambiente=%.2f nuvens=%.2f" % [
        _base_sol, _base_nevoa, _base_ambiente, _base_nuvens])
