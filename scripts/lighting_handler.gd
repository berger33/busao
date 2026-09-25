extends Node
# LightingHandler — Lote 24: Iluminação Realista (IBL + GI + SDFGI/VoxelGI + ReflectionProbe)
# Mantém mobile fallback (Panorama + 1024) quando desligado; quando ligado, SDFGI/VoxelGI, 4096 VSM, SSAO/SSIL 0.4, VolumetricFog, PhysicalSky.

class_name LightingHandler

const SHADOW_RESOLUTION_MOBILE: int = 2048
const SHADOW_RESOLUTION_REALISTA: int = 4096
const SHADOW_MAX_DISTANCE_REALISTA: float = 96.0
const SHADOW_BIAS_REALISTA: float = 0.012 # sombra de contato mais firme, sem peter-panning
const SHADOW_NORMAL_BIAS_REALISTA: float = 0.45 # L27: peter-panning 1.2→0.45
const SHADOW_OPACITY_REALISTA: float = 0.82
const SDFGI_ENABLED: bool = true
const VOXELGI_SIZE: Vector3 = Vector3(28.0, 12.0, 28.0) # por quarteirão
const REFLECTION_PROBE_SIZE: Vector3 = Vector3(28.0, 16.0, 28.0)
const VOLUMETRIC_FOG_DENSITY: float = 0.012
const VOLUMETRIC_FOG_ALBEDO: Color = Color("#b9cbd0")
const SSAO_ENABLED: bool = true
const SSIL_ENABLED: bool = true
const SSAO_INTENSITY: float = 0.4
const SSIL_INTENSITY: float = 0.4

static func _get_rendering_method() -> String:
    if RenderingServer.has_method("get_current_rendering_method"):
        return String(RenderingServer.get_current_rendering_method())
    return String(ProjectSettings.get_setting("rendering/renderer/rendering_method", "mobile"))

static func _is_forward_plus() -> bool:
    return _get_rendering_method() == "forward_plus"

static func _supports_ssao() -> bool:
    var method := _get_rendering_method()
    # No Godot 4: Forward+ e gl_compatibility suportam SSAO; mobile não suporta
    return method == "forward_plus" or method == "gl_compatibility"

static func setup_realista(environment: WorldEnvironment, sun: DirectionalLight3D, world_root: Node3D, enable: bool) -> void:
    if environment == null or environment.environment == null or sun == null:
        return
    var env: Environment = environment.environment
    if enable:
        var forward_plus := _is_forward_plus()
        # SDFGI / SSIL / VolumetricFog exigem renderer Forward+
        if forward_plus:
            env.sdfgi_enabled = SDFGI_ENABLED
            env.ssil_enabled = SSIL_ENABLED
            env.volumetric_fog_enabled = true
            env.volumetric_fog_density = VOLUMETRIC_FOG_DENSITY
            env.volumetric_fog_albedo = VOLUMETRIC_FOG_ALBEDO
        else:
            env.sdfgi_enabled = false
            env.ssil_enabled = false
            env.volumetric_fog_enabled = false

        # SSAO suportado apenas em Forward+ ou Compatibility
        if _supports_ssao():
            env.ssao_enabled = SSAO_ENABLED
            # Oclusão curta e concentrada: dá peso às juntas da calçada,
            # rodas e encontros parede/piso sem escurecer o cenário inteiro.
            env.ssao_radius = 2.0
            env.ssao_intensity = SSAO_INTENSITY
            # Godot 4: ssao_light_affect (o nome *_direct_* era Godot 3 e
            # explodia em runtime toda vez que o SSAO era aplicado).
            env.ssao_light_affect = 0.28
        else:
            env.ssao_enabled = false

        # Contraste físico mais natural: preserva detalhes nas altas luzes
        # enquanto mantém as sombras azuladas do céu. Passe visual 1:
        # saturação acima de 1.0 (era 0.96, lavado para celular) — runner
        # mobile pede cor viva; contraste um ponto acima para o sol bater.
        env.adjustment_enabled = true
        env.adjustment_brightness = 1.0
        env.adjustment_contrast = 1.12
        env.adjustment_saturation = 1.06

        # sombra 4096 VSM nítida a 0.5 m
        sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
        sun.shadow_enabled = true
        sun.directional_shadow_max_distance = SHADOW_MAX_DISTANCE_REALISTA
        sun.shadow_bias = SHADOW_BIAS_REALISTA
        sun.shadow_normal_bias = SHADOW_NORMAL_BIAS_REALISTA
        sun.shadow_opacity = SHADOW_OPACITY_REALISTA
        # A luz de contato ancora rodas, pés e mobiliário no piso; o blur
        # continua suave o suficiente para não parecer uma sombra recortada.
        sun.shadow_blur = 1.25
        sun.shadow_reverse_cull_face = false
        sun.distance_fade_enabled = true
        sun.distance_fade_begin = 72.0
        sun.distance_fade_shadow = 0.92
        sun.light_angular_distance = 0.55
        # L27: contact shadow via ssao/ssil já 0.4 + bias baixo garante contato 0.5m
        # Sky: calibra energia solar do panorama sem substituir o asset canônico
        var sky: Sky = environment.environment.sky
        if sky != null and sky.sky_material is PanoramaSkyMaterial:
            (sky.sky_material as PanoramaSkyMaterial).energy_multiplier = 0.96
            sun.light_angular_distance = 1.2
        # ReflectionProbe por quarteirão (28 m) + VoxelGI
        if world_root != null:
            var method := _get_rendering_method()
            # ReflectionProbe suportado em Forward+ e Mobile (não em gl_compatibility)
            if method != "gl_compatibility" and world_root.get_node_or_null("RealistaGI") == null:
                var gi_root := Node3D.new()
                gi_root.name = "RealistaGI"
                world_root.add_child(gi_root)
                for i in 3:
                    if forward_plus:
                        var voxel := VoxelGI.new()
                        voxel.name = "VoxelGI_%d" % i
                        voxel.size = VOXELGI_SIZE
                        voxel.position = Vector3(0, 4.0, -float(i) * 28.0 - 14.0)
                        gi_root.add_child(voxel)
                    var probe := ReflectionProbe.new()
                    probe.name = "ReflectionProbe_%d" % i
                    probe.size = REFLECTION_PROBE_SIZE
                    probe.position = Vector3(0, 3.5, -float(i) * 28.0 - 14.0)
                    probe.box_projection = true
                    probe.update_mode = ReflectionProbe.UPDATE_ONCE
                    probe.intensity = 1.0
                    gi_root.add_child(probe)
    else:
        # fallback mobile: mantém contato visual sem habilitar recursos caros.
        # Passe visual 1: mesma direção do modo realista (cor viva + contraste),
        # com metade do impulso para não estourar em tela OLED.
        env.adjustment_enabled = true
        env.adjustment_brightness = 1.0
        env.adjustment_contrast = 1.10
        env.adjustment_saturation = 1.05
        env.ssao_enabled = false
        # fallback mobile
        env.sdfgi_enabled = false
        env.ssao_enabled = false
        env.ssil_enabled = false
        env.volumetric_fog_enabled = false
        sun.directional_shadow_max_distance = 72.0
        sun.shadow_bias = 0.045
        sun.shadow_normal_bias = 0.78
        sun.shadow_opacity = 0.76
        sun.light_angular_distance = 0.6
        # remove GI realista se existir
        if world_root != null:
            var gi_root := world_root.get_node_or_null("RealistaGI")
            if gi_root != null:
                gi_root.queue_free()

static func bake_lightmaps(world_root: Node3D) -> void:
    # Lightmap bake para building_kit static (72×72 probe, AO 0.6) — placeholder para LightmapGI bake()
    if world_root == null:
        return
    var gi_root := world_root.get_node_or_null("RealistaGI")
    if gi_root == null:
        return
    for child in gi_root.get_children():
        if child is VoxelGI:
            # Em headless/editor faria (child as VoxelGI).bake()
            pass
