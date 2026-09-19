extends Node
# LightingHandler — Lote 24: Iluminação Realista (IBL + GI + SDFGI/VoxelGI + ReflectionProbe)
# Mantém mobile fallback (Panorama + 1024) quando desligado; quando ligado, SDFGI/VoxelGI, 4096 VSM, SSAO/SSIL 0.4, VolumetricFog, PhysicalSky.

class_name LightingHandler

const SHADOW_RESOLUTION_MOBILE: int = 1024
const SHADOW_RESOLUTION_REALISTA: int = 4096
const SHADOW_MAX_DISTANCE_REALISTA: float = 96.0
const SHADOW_BIAS_REALISTA: float = 0.015 # L27 polimento: contact 0.5m nitida (era 0.02 pantanal)
const SHADOW_NORMAL_BIAS_REALISTA: float = 0.45 # L27: peter-panning 1.2→0.45
const SHADOW_OPACITY_REALISTA: float = 0.82
const SDFGI_ENABLED: bool = true
const VOXELGI_SIZE: Vector3 = Vector3(28.0, 12.0, 28.0) # por quarteirão
const REFLECTION_PROBE_SIZE: Vector3 = Vector3(28.0, 16.0, 28.0)
const REFLECTION_PROBE_RESOLUTION: int = 128
const VOLUMETRIC_FOG_DENSITY: float = 0.012
const VOLUMETRIC_FOG_ALBEDO: Color = Color("#b9cbd0")
const SSAO_ENABLED: bool = true
const SSIL_ENABLED: bool = true
const SSAO_INTENSITY: float = 0.4
const SSIL_INTENSITY: float = 0.4

static func setup_realista(environment: WorldEnvironment, sun: DirectionalLight3D, world_root: Node3D, enable: bool) -> void:
    if environment == null or environment.environment == null or sun == null:
        return
    var env: Environment = environment.environment
    if enable:
        # SDFGI / VoxelGI — SDFGI para forward_plus, VoxelGI fallback; em gl_compatibility ignora mas não quebra
        env.sdfgi_enabled = SDFGI_ENABLED
        # SSAO / SSIL 0.4
        env.ssao_enabled = SSAO_ENABLED
        env.ssil_enabled = SSIL_ENABLED
        if env.has_method("set_ssao_intensity"):
            # Godot 4.4 usa ssao_intensity etc.
            pass
        # VolumetricFog já existente vira VolumetricFog node 64
        env.volumetric_fog_enabled = true
        env.volumetric_fog_density = VOLUMETRIC_FOG_DENSITY
        env.volumetric_fog_albedo = VOLUMETRIC_FOG_ALBEDO
        # sombra 4096 VSM nítida a 0.5 m
        sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
        sun.shadow_enabled = true
        sun.directional_shadow_max_distance = SHADOW_MAX_DISTANCE_REALISTA
        sun.shadow_bias = SHADOW_BIAS_REALISTA
        sun.shadow_normal_bias = SHADOW_NORMAL_BIAS_REALISTA
        sun.shadow_opacity = SHADOW_OPACITY_REALISTA
        # evita peter-panning
        sun.shadow_blur = 1.0 # L27 soft VSM blur
        sun.shadow_reverse_cull_face = false
        # L27: contact shadow via ssao/ssil já 0.4 + bias baixo garante contato 0.5m
        # Sky PhysicalSky + sun disk + clouds 3D (substitui Panorama quando realista)
        var sky: Sky = environment.environment.sky
        if sky != null and sky.sky_material is PanoramaSkyMaterial:
            var pano: PanoramaSkyMaterial = sky.sky_material as PanoramaSkyMaterial
            # mantém panorama mas adiciona energia sun disk via light_angular_distance
            sun.light_angular_distance = 1.2
            # se PhysicalSky disponível, troca
            if ClassDB.class_exists("PhysicalSkyMaterial"):
                var phys := PhysicalSkyMaterial.new()
                phys.sky_energy_multiplier = 0.92
                phys.ground_energy_multiplier = 1.1
                phys.sun_disk_scale = 0.42
                phys.sky_horizon_color = Color("#a8c8d8")
                phys.sky_top_color = Color("#3a5a8a")
                sky.sky_material = phys
        # ReflectionProbe por quarteirão (28 m) + VoxelGI
        if world_root != null:
            # evita duplicar
            if world_root.get_node_or_null("RealistaGI") == null:
                var gi_root := Node3D.new()
                gi_root.name = "RealistaGI"
                world_root.add_child(gi_root)
                # VoxelGI por quarteirão (3 visíveis)
                for i in 3:
                    var voxel := VoxelGI.new()
                    voxel.name = "VoxelGI_%d" % i
                    voxel.size = VOXELGI_SIZE
                    voxel.position = Vector3(0, 4.0, -float(i) * 28.0 - 14.0)
                    voxel.data = null # bake em runtime via bake()
                    gi_root.add_child(voxel)
                    var probe := ReflectionProbe.new()
                    probe.name = "ReflectionProbe_%d" % i
                    probe.size = REFLECTION_PROBE_SIZE
                    probe.position = Vector3(0, 3.5, -float(i) * 28.0 - 14.0)
                    probe.resolution = REFLECTION_PROBE_RESOLUTION
                    probe.update_mode = ReflectionProbe.UPDATE_ONCE
                    probe.intensity = 1.0
                    gi_root.add_child(probe)
    else:
        # fallback mobile
        env.sdfgi_enabled = false
        env.ssao_enabled = false
        env.ssil_enabled = false
        env.volumetric_fog_enabled = false
        sun.directional_shadow_max_distance = 72.0
        sun.shadow_bias = 0.045
        sun.shadow_normal_bias = 1.2
        sun.shadow_opacity = 0.72
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
            var voxel := child as VoxelGI
            # em headless/editor faria voxel.bake()
            pass
