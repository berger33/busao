extends Node3D
## Humanoide 3D principal do runner.
##
## Personagem 100% original Blender headless 4.5
## (tools/blender/build_humanos.py): Humano_M/F rigged/skinned
## com 6 clips Idle/Walk/Sprint/Jump/Crouch em
## assets/characters/humanos_originais/. Lote 26 removeu totalmente o
## legado Quaternius (assets/characters/quaternius/ 86 MB CC0): não há
## mais fallback Quaternius; primitivas só em diagnóstico extremo.

const CHARACTER_DATA = preload("res://scripts/character_data.gd")
const TEXTURE_CREATOR_TOP = preload("res://assets/textures/tecido_realista.png")
const TEXTURE_CREATOR_TOP_N = preload("res://assets/textures/tecido_realista_normal.png")
const TEXTURE_CREATOR_TOP_R = preload("res://assets/textures/tecido_realista_roughness.png")
const TEXTURE_CREATOR_DENIM = preload("res://assets/textures/jeans_realista.png")
const TEXTURE_CREATOR_DENIM_N = preload("res://assets/textures/jeans_realista_normal.png")
const TEXTURE_CREATOR_DENIM_R = preload("res://assets/textures/jeans_realista_roughness.png")
const TEXTURE_CREATOR_METAL = preload("res://assets/textures/metal_pintado_realista.png")
const TEXTURE_CREATOR_METAL_N = preload("res://assets/textures/metal_pintado_realista_normal.png")
const TEXTURE_CREATOR_METAL_R = preload("res://assets/textures/metal_pintado_realista_roughness.png")
const TEXTURE_CREATOR_RUBBER = preload("res://assets/textures/borracha_realista.png")
const TEXTURE_CREATOR_RUBBER_N = preload("res://assets/textures/borracha_realista_normal.png")
const TEXTURE_CREATOR_RUBBER_R = preload("res://assets/textures/borracha_realista_roughness.png")
# Lote 28 Passo 2 — PBR 4K pele/cabelo (acaba com aspecto plástico cru)
const TEXTURE_SKIN = preload("res://assets/textures/pele_realista.png")
const TEXTURE_SKIN_N = preload("res://assets/textures/pele_realista_normal.png")
const TEXTURE_SKIN_R = preload("res://assets/textures/pele_realista_roughness.png")
const TEXTURE_HAIR = preload("res://assets/textures/cabelo_realista.png")

const MODEL_ROOT := "res://assets/characters/humanos_originais" # L26: alias legado (antes quaternius 86 MB) agora aponta para humanos originais; sem CC0
const BASE_ROOT := MODEL_ROOT + "/base"
const PARTS_ROOT := MODEL_ROOT + "/parts"
const ANIMATION_LIBRARY_PATH := MODEL_ROOT + "/animation/UAL1_Standard.res"
const ANIMATION_SOURCE_PATH := MODEL_ROOT + "/animation/UAL1_Standard.glb"
# Lote 19 — humanos 100% originais Blender (preferencial, do zero, PBR)
const ORIGINAL_ROOT := "res://assets/characters/humanos_originais"
const ORIGINAL_BODY_PATHS: Dictionary = {
    "M": ORIGINAL_ROOT + "/Humano_M.glb",
    "F": ORIGINAL_ROOT + "/Humano_F.glb",
}
const PERSONAGENS_ROOT := "res://assets/characters/personagens" # Lote 28: 20 GLBs dedicados
# Primeiro marco do novo pipeline: a heroína terá um asset dedicado, sem
# compartilhar a malha simplificada do elenco. O fallback mantém o jogo jogável
# enquanto o GLB passa pela validação visual.
const HERO_ASSET_PATH := PERSONAGENS_ROOT + "/hero_julia.glb"
const GINGER_ASSET_PATH := PERSONAGENS_ROOT + "/ginger+woman.glb"
const MODEL_SCALE := 1.03  # 1.77*1.03=1.82 realista (era 1.18->2.09)
const MODEL_FLOOR_OFFSET := 0.012
const CLOTHING_INFLATE := 0.008
const PLAYER_HEIGHT := 1.82 # L27 polimento: altura realista brasileira (era 2.15 gigante vs porta 2.4)
## O GLTF humano original (ex-Quaternius) é exportado olhando para +Z: as sobrancelhas e os olhos
## ficam nesse eixo e as costas no lado oposto. O corredor avança para -Z (fundo
## da tela), então o modelo é girado 180 graus — sem isso ele corre de costas
## para o sentido do movimento, de frente para a câmera.
const MODEL_FACING_YAW := PI
## Velocidade de solo que o clipe Sprint_Loop cobre sozinho: o ciclo dura 0,667 s
## e desloca o pé ~1,35 m (medido por cinemática direta dos ossos do GLB), o
## equivalente a ~4 m/s. A cadência da animação é escalada pela velocidade real
## do jogo para o pé não patinar no asfalto.
const LOCOMOTION_CLIP_SPEED := 4.0
const RUN_CURB_X := -1.525   # guia rua/calcada (espelha game_3d; sombra no chao certo)
const RUN_STREET_Y := -0.15
const LOCOMOTION_MAX_PLAYBACK := 2.2

const BODY_PATHS: Dictionary = {
    "M": BASE_ROOT + "/Superhero_Male_FullBody.gltf",
    "F": BASE_ROOT + "/Superhero_Female_FullBody.gltf",
}
const OUTFIT_PATHS: Dictionary = {
    "M": [
        PARTS_ROOT + "/Male_Peasant_Body.gltf",
        PARTS_ROOT + "/Male_Peasant_Arms.gltf",
        PARTS_ROOT + "/Male_Peasant_Legs.gltf",
        PARTS_ROOT + "/Male_Peasant_Feet.gltf",
    ],
    "F": [
        PARTS_ROOT + "/Female_Peasant_Body.gltf",
        PARTS_ROOT + "/Female_Peasant_Arms.gltf",
        PARTS_ROOT + "/Female_Peasant_Legs.gltf",
        PARTS_ROOT + "/Female_Peasant_Feet.gltf",
    ],
}

# The imported body keeps the source bone names. Region splitting lets the
# actual garments cover torso, arms, legs and feet without skin poke-through.
const REGION_BONES: Dictionary = {
    "head": ["Head", "neck_01"],
    "torso": ["spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"],
    "arms": [
        "upperarm_l", "lowerarm_l", "hand_l",
        "upperarm_r", "lowerarm_r", "hand_r",
        "thumb_01_l", "thumb_02_l", "thumb_03_l",
        "thumb_01_r", "thumb_02_r", "thumb_03_r",
        "index_01_l", "index_02_l", "index_03_l",
        "index_01_r", "index_02_r", "index_03_r",
        "middle_01_l", "middle_02_l", "middle_03_l",
        "middle_01_r", "middle_02_r", "middle_03_r",
        "ring_01_l", "ring_02_l", "ring_03_l",
        "ring_01_r", "ring_02_r", "ring_03_r",
        "pinky_01_l", "pinky_02_l", "pinky_03_l",
        "pinky_01_r", "pinky_02_r", "pinky_03_r",
    ],
    "legs": ["pelvis", "thigh_l", "calf_l", "thigh_r", "calf_r"],
    "feet": ["foot_l", "ball_l", "foot_r", "ball_r"],
}

var character_id: String = "ze"
var gender: String = "M"
var model_root: Node3D
## Pivô acima do modelo: recebe o balanço lateral enquanto o modelo guarda o
## giro de 180° em `model_root`. Separar os dois evita depender da ordem de
## Euler para o sinal da inclinação.
var model_pivot: Node3D
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
# Animação procedural do herói mesh-only enquanto o rig final não está disponível.
var mesh_parts: Dictionary = {}
var mesh_part_rest: Dictionary = {}
var runner_shadow: MeshInstance3D
var current_clip := ""
var world_mode := false
var using_external_animation := false
static var _biblioteca_cache: AnimationLibrary = null
var primary_asset_loaded := false
var use_animation_library := true
var motion_clock := 0.0
var bone_indices: Dictionary = {}
var rest_rotations: Dictionary = {}

# --- Física Secundária de Movimento (Hair Spring, Spine Dynamics & Body Lean) ---
var _hair_pitch: float = 0.0
var _hair_pitch_vel: float = 0.0
var _hair_yaw: float = 0.0
var _hair_yaw_vel: float = 0.0
var _spine_roll: float = 0.0
var _spine_roll_vel: float = 0.0
var _last_jump_h: float = 0.0

# --- Overlay de bracos (sprint/walk): rampa, pose capturada e comprimentos ---
var _arm_w := 0.0
var _arm_have_from := false
var _arm_from: Dictionary = {}
var _arm_len_cache: Dictionary = {}

func _ready() -> void:
    set_character(character_id)

func set_world_mode(enabled: bool) -> void:
    # NPCs de mundo continuam COM a biblioteca de animacao (Idle/Walk/Driving
    # da Universal Animation Library): sem isso eles viram espantalho em
    # T-pose. O driver de corrida (set_motion) segue exclusivo do jogador,
    # que nunca chama set_world_mode.
    world_mode = enabled
    use_animation_library = true


func play_world_clip(clip: String, custom_speed := 1.0) -> void:
    if animation_player != null:
        animation_player.speed_scale = maxf(0.05, custom_speed)
    _play_clip(clip)

func set_character(next_id: String) -> void:
    character_id = CHARACTER_DATA.canonical_id(next_id)
    var profile: Dictionary = CHARACTER_DATA.get_character(character_id)
    gender = "F" if str(profile.get("gender", "M")) == "F" else "M"
    _clear_character()
    _build_shadow()
    # Lote 28: tenta GLB dedicado por personagem (assets/characters/personagens/<id>.glb) — bakeado Blender com paleta + props.
    var personalized_path := HERO_ASSET_PATH if character_id == "julia" and ResourceLoader.exists(HERO_ASSET_PATH) else (GINGER_ASSET_PATH if character_id == "ginger" and ResourceLoader.exists(GINGER_ASSET_PATH) else PERSONAGENS_ROOT + "/" + character_id + ".glb")
    var is_personalized := false
    var body_scene: PackedScene = null
    var body_path: String = personalized_path
    var is_original := false
    if ResourceLoader.exists(personalized_path):
        body_scene = load(personalized_path) as PackedScene
        if body_scene != null:
            is_personalized = true
            is_original = true
    # Lote 19: humano original Blender 100% do zero tem prioridade (sem CC0).
    if body_scene == null:
        var original_path: String = str(ORIGINAL_BODY_PATHS.get(gender, ""))
        body_path = original_path
        if original_path != "" and ResourceLoader.exists(original_path):
            body_scene = load(original_path) as PackedScene
            if body_scene != null:
                is_original = true
        if body_scene == null:
            body_path = str(BODY_PATHS.get(gender, BODY_PATHS["M"]))
            body_scene = load(body_path) as PackedScene
            is_original = false
    if body_scene == null:
        _build_fallback("asset principal não importado")
        return
    model_root = body_scene.instantiate() as Node3D
    if model_root == null:
        _build_fallback("cena GLTF inválida")
        return
    model_pivot = Node3D.new()
    model_pivot.name = "ModelPivot"
    add_child(model_pivot)
    model_root.name = "HumanoOriginal" if is_original else "QuaterniusHuman"
    model_root.rotation.y = MODEL_FACING_YAW
    var selected_scale := 0.72 if character_id == "ginger" else MODEL_SCALE
    model_root.scale = Vector3.ONE * selected_scale
    model_root.position.y = MODEL_FLOOR_OFFSET
    model_pivot.add_child(model_root)
    skeleton = _find_skeleton(model_root)
    if skeleton == null:
        # Hero procedural mesh-only: mantém a malha detalhada mesmo sem rig
        # Blender, enquanto o pipeline de animação avançada é preparado.
        # O root do jogo ainda fornece corrida, inclinação, salto e bob.
        _cache_mesh_only_parts(model_root)
        _configure_mesh_shadows(model_root)
        primary_asset_loaded = true
        return
    _cache_skeleton()
    if is_original:
        _apply_skin_tint(profile.get("skin", Color.WHITE))
        _apply_profile_palette(profile)
        # Lote 28: GLB dedicado já vem bakeado — evita duplicar props (duplo celular/mochila).
        if not is_personalized:
            _attach_creator_details(profile)
            _attach_batch2_details(profile)
        if use_animation_library:
            _setup_original_animation()
        _configure_mesh_shadows(model_root)
        primary_asset_loaded = true
        return
    _split_base_body()
    _attach_outfit(gender)
    _apply_skin_tint(profile.get("skin", Color.WHITE))
    _apply_profile_palette(profile)
    _attach_creator_details(profile)
    _attach_batch2_details(profile)
    if use_animation_library:
        _setup_animation_library()
    _configure_mesh_shadows(model_root)
    primary_asset_loaded = true

func _clear_character() -> void:
    if is_instance_valid(model_pivot):
        model_pivot.free()
    model_pivot = null
    model_root = null
    skeleton = null
    animation_player = null
    current_clip = ""
    using_external_animation = false
    primary_asset_loaded = false
    bone_indices.clear()
    rest_rotations.clear()
    mesh_parts.clear()
    mesh_part_rest.clear()
    _hair_pitch = 0.0
    _hair_pitch_vel = 0.0
    _hair_yaw = 0.0
    _hair_yaw_vel = 0.0
    _spine_roll = 0.0
    _spine_roll_vel = 0.0
    _last_jump_h = 0.0
    if is_instance_valid(runner_shadow):
        runner_shadow.free()
    runner_shadow = null

func _build_shadow() -> void:
    runner_shadow = MeshInstance3D.new()
    runner_shadow.name = "RunnerShadow"
    var st := SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    var segments := 24
    var rx := 0.36
    var rz := 0.54
    var center := Vector3.ZERO
    for i in range(segments):
        var a1 := float(i) / float(segments) * TAU
        var a2 := float(i + 1) / float(segments) * TAU
        var p1 := Vector3(cos(a1) * rx, 0.0, sin(a1) * rz)
        var p2 := Vector3(cos(a2) * rx, 0.0, sin(a2) * rz)
        st.set_color(Color(0.015, 0.02, 0.03, 0.40))
        st.add_vertex(center)
        st.set_color(Color(0.015, 0.02, 0.03, 0.0))
        st.add_vertex(p1)
        st.set_color(Color(0.015, 0.02, 0.03, 0.0))
        st.add_vertex(p2)
    runner_shadow.mesh = st.commit()
    runner_shadow.position = Vector3(0.0, 0.025, 0.0)
    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.015, 0.02, 0.03, 0.40)
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.no_depth_test = true
    runner_shadow.material_override = material
    add_child(runner_shadow)

func _find_skeleton(node: Node) -> Skeleton3D:
    var pending: Array[Node] = [node]
    while not pending.is_empty():
        var current: Node = pending.pop_back()
        if current is Skeleton3D:
            return current as Skeleton3D
        for child in current.get_children():
            pending.append(child)
    return null

func _find_mesh_instance(root: Node) -> MeshInstance3D:
    if root is MeshInstance3D:
        return root as MeshInstance3D
    for c in root.get_children():
        var r: MeshInstance3D = _find_mesh_instance(c)
        if r != null:
            return r
    return null

func _skinned_meshes(node: Node) -> Array[MeshInstance3D]:
    var found: Array[MeshInstance3D] = []
    var pending: Array[Node] = [node]
    while not pending.is_empty():
        var current: Node = pending.pop_back()
        if current is MeshInstance3D and (current as MeshInstance3D).skin != null:
            found.append(current as MeshInstance3D)
        for child in current.get_children():
            pending.append(child)
    return found

func _cache_mesh_only_parts(root: Node) -> void:
    for child in root.find_children("*", "Node3D", true, false):
        var part_name := str(child.name)
        if part_name in ["LeftThigh", "RightThigh", "LeftCalf", "RightCalf", "UpperArmL", "UpperArmR", "ForearmL", "ForearmR", "Torso"]:
            mesh_parts[part_name] = child
            mesh_part_rest[part_name] = {"position": child.position, "rotation": child.rotation}

func _animate_mesh_only(stride: float, crouching: bool, jumping: bool) -> void:
    if mesh_parts.is_empty():
        return
    var knee := 0.28 if crouching else (0.10 if jumping else 0.0)
    var swing := stride * (0.42 if not crouching else 0.18)
    _mesh_rotate("LeftThigh", swing + knee)
    _mesh_rotate("RightThigh", -swing + knee)
    _mesh_rotate("LeftCalf", maxf(0.0, -stride) * 0.35 + knee)
    _mesh_rotate("RightCalf", maxf(0.0, stride) * 0.35 + knee)
    _mesh_rotate("UpperArmL", -swing * 0.72)
    _mesh_rotate("UpperArmR", swing * 0.72)
    _mesh_rotate("ForearmL", 0.18)
    _mesh_rotate("ForearmR", -0.18)

func _mesh_rotate(part: String, pitch: float) -> void:
    var node := mesh_parts.get(part) as Node3D
    if node == null:
        return
    var rest: Dictionary = mesh_part_rest[part]
    node.rotation = rest["rotation"] + Vector3(pitch, 0.0, 0.0)

func _cache_skeleton() -> void:
    bone_indices.clear()
    rest_rotations.clear()
    for index in skeleton.get_bone_count():
        var bone_name: String = skeleton.get_bone_name(index)
        bone_indices[bone_name] = index
        rest_rotations[bone_name] = skeleton.get_bone_pose_rotation(index)

func _split_base_body() -> void:
    var body_mesh: MeshInstance3D
    for candidate in _skinned_meshes(model_root):
        var candidate_name := str(candidate.name).to_lower()
        if candidate_name.begins_with("superhero") or candidate_name.begins_with("sphere"):
            body_mesh = candidate
            break
    if body_mesh == null or not body_mesh.mesh is ArrayMesh:
        return
    var regions: Dictionary = _split_regions(body_mesh)
    var body_parent := body_mesh.get_parent()
    for region_name in regions:
        var region_mesh := MeshInstance3D.new()
        region_mesh.name = "BaseSkin_%s" % region_name
        region_mesh.mesh = regions[region_name]
        region_mesh.skin = body_mesh.skin
        region_mesh.transform = body_mesh.transform
        body_parent.add_child(region_mesh)
        # Keep the mesh beside the imported body, but explicitly bind it to the
        # one target Skeleton3D. This avoids relying on Godot's version-specific
        # default parent-skeleton behavior.
        region_mesh.skeleton = region_mesh.get_path_to(skeleton)
        region_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
    body_mesh.visible = false

func _split_regions(body_mesh: MeshInstance3D) -> Dictionary:
    var source_mesh := body_mesh.mesh as ArrayMesh
    var source_skin := body_mesh.skin
    var bind_regions: Dictionary = {}
    for bind_index in source_skin.get_bind_count():
        var bind_bone := str(source_skin.get_bind_name(bind_index))
        for region_name in REGION_BONES:
            if (REGION_BONES[region_name] as Array).has(bind_bone):
                bind_regions[bind_index] = region_name
                break
    var output: Dictionary = {}
    for surface_index in source_mesh.get_surface_count():
        var arrays: Array = source_mesh.surface_get_arrays(surface_index)
        var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
        var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
        var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
        var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
        if vertices.is_empty() or bones.is_empty() or weights.is_empty() or indices.is_empty():
            continue
        var influences: int = int(float(bones.size()) / float(vertices.size()))
        var region_indices: Dictionary = {}
        for triangle in range(0, indices.size(), 3):
            var votes: Dictionary = {}
            for corner in 3:
                var vertex_index: int = indices[triangle + corner]
                for influence in influences:
                    var weight: float = weights[vertex_index * influences + influence]
                    if weight <= 0.0:
                        continue
                    var region_name: String = str(bind_regions.get(bones[vertex_index * influences + influence], "torso"))
                    votes[region_name] = float(votes.get(region_name, 0.0)) + weight
            var best_region := "torso"
            var best_weight := -1.0
            for region_name in votes:
                if float(votes[region_name]) > best_weight:
                    best_region = str(region_name)
                    best_weight = float(votes[region_name])
            if not region_indices.has(best_region):
                region_indices[best_region] = PackedInt32Array()
            var bucket: PackedInt32Array = region_indices[best_region]
            bucket.append(indices[triangle])
            bucket.append(indices[triangle + 1])
            bucket.append(indices[triangle + 2])
            region_indices[best_region] = bucket
        for region_name in region_indices:
            var region_arrays: Array = arrays.duplicate()
            region_arrays[Mesh.ARRAY_INDEX] = region_indices[region_name]
            for custom_slot in [Mesh.ARRAY_CUSTOM0, Mesh.ARRAY_CUSTOM1, Mesh.ARRAY_CUSTOM2, Mesh.ARRAY_CUSTOM3]:
                region_arrays[custom_slot] = null
            if not output.has(region_name):
                output[region_name] = ArrayMesh.new()
            var rebuilt: ArrayMesh = output[region_name]
            rebuilt.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, region_arrays)
            rebuilt.surface_set_material(rebuilt.get_surface_count() - 1, source_mesh.surface_get_material(surface_index))
    return output

func _attach_outfit(body_gender: String) -> void:
    var outfit_paths: Array = OUTFIT_PATHS.get(body_gender, [])
    if character_id == "influencer":
        outfit_paths = [PARTS_ROOT + "/%s_Peasant_Feet.gltf" % ("Female" if body_gender == "F" else "Male")]
    for path_variant in outfit_paths:
        var outfit_scene := load(str(path_variant)) as PackedScene
        if outfit_scene == null:
            push_warning("Roupa humana não importada: %s" % path_variant)
            continue
        var outfit_root := outfit_scene.instantiate()
        for source_mesh in _skinned_meshes(outfit_root):
            var worn := source_mesh.duplicate() as MeshInstance3D
            worn.name = "QuaterniusOutfit_%s" % source_mesh.name
            worn.mesh = _inflate_mesh(worn.mesh)
            worn.transform = source_mesh.transform
            model_root.add_child(worn)
            # The modular GLTFs use the same named Skin binds as the body, but
            # their original skeleton path points at their temporary scene.
            # Rebind each garment to the live body skeleton after instancing.
            worn.skeleton = worn.get_path_to(skeleton)
            worn.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
            _tint_exposed_skin_materials(worn)
        outfit_root.free()

func _inflate_mesh(source: Mesh) -> Mesh:
    if not source is ArrayMesh:
        return source
    var input := source as ArrayMesh
    var output := ArrayMesh.new()
    for surface_index in input.get_surface_count():
        var arrays: Array = input.surface_get_arrays(surface_index)
        var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
        var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
        if vertices.size() == normals.size():
            for index in vertices.size():
                vertices[index] += normals[index] * CLOTHING_INFLATE
            arrays[Mesh.ARRAY_VERTEX] = vertices
        output.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
        output.surface_set_material(output.get_surface_count() - 1, input.surface_get_material(surface_index))
    return output

func _tint_exposed_skin_materials(mesh: MeshInstance3D) -> void:
    if mesh.mesh == null:
        return
    for surface_index in mesh.mesh.get_surface_count():
        var source_material := mesh.mesh.surface_get_material(surface_index)
        if source_material is BaseMaterial3D and str(source_material.resource_name).contains("Regular"):
            var skin_material := source_material.duplicate() as BaseMaterial3D
            skin_material.resource_name = "QuaterniusSkin"
            mesh.set_surface_override_material(surface_index, skin_material)

func _apply_skin_tint(skin_color: Color) -> void:
    if skeleton == null:
        return
    var tint := Color(skin_color.r / 0.72, skin_color.g / 0.48, skin_color.b / 0.36, 1.0)
    tint.r = clampf(tint.r, 0.62, 1.35)
    tint.g = clampf(tint.g, 0.62, 1.35)
    tint.b = clampf(tint.b, 0.62, 1.35)
    for mesh in _skinned_meshes(model_root):
        if mesh.mesh == null:
            continue
        var base_skin := str(mesh.name).begins_with("BaseSkin_")
        for surface_index in mesh.mesh.get_surface_count():
            var source_material := mesh.get_surface_override_material(surface_index)
            if source_material == null:
                source_material = mesh.mesh.surface_get_material(surface_index)
            var marked_skin := source_material is BaseMaterial3D and str(source_material.resource_name).contains("QuaterniusSkin")
            if not base_skin and not marked_skin:
                continue
            if source_material is BaseMaterial3D:
                var material := source_material.duplicate() as BaseMaterial3D
                material.albedo_color = tint
                # PBR 4K pele — acaba com plástico: poros via normal + variação de brilho
                material.albedo_texture = TEXTURE_SKIN
                material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
                material.normal_enabled = true
                material.normal_texture = TEXTURE_SKIN_N
                material.normal_scale = 0.52
                material.roughness = 1.0
                material.roughness_texture = TEXTURE_SKIN_R
                material.uv1_scale = Vector3(2.2, 2.2, 2.2)
                # Pele humana precisa responder à luz de forma macia: SSS
                # sutil, especular baixo e rim discreto removem o aspecto de
                # plástico sem deixar o rosto brilhando como porcelana.
                material.subsurf_scatter_enabled = true
                material.subsurf_scatter_skin_mode = true
                material.subsurf_scatter_strength = 0.18
                material.metallic = 0.0
                material.metallic_specular = 0.28
                material.rim_enabled = true
                material.rim = 0.06
                material.rim_tint = 0.72
                mesh.set_surface_override_material(surface_index, material)

func _apply_profile_palette(profile: Dictionary) -> void:
    if model_root == null:
        return
    var shirt: Color = profile.get("shirt", Color.WHITE)
    var pants: Color = profile.get("pants", Color.WHITE)
    var shoes: Color = profile.get("shoes", Color.WHITE)
    var hair: Color = profile.get("hair", Color.WHITE)
    for mesh in _skinned_meshes(model_root):
        if mesh.mesh == null:
            continue
        var mesh_name := str(mesh.name).to_lower()
        for surface_index in mesh.mesh.get_surface_count():
            var source_material := mesh.get_surface_override_material(surface_index)
            if source_material == null:
                source_material = mesh.mesh.surface_get_material(surface_index)
            if not source_material is BaseMaterial3D:
                continue
            var material_name := str(source_material.resource_name).to_lower()
            if material_name.contains("quaterniusskin"):
                continue
            var tint := Color.WHITE
            var pbr_kind := "" # tecido / jeans / borracha / cabelo / metal
            # Original Blender humano usa nomes Camisa/Calca/Sapato/Hair nos materiais
            if material_name.contains("camisa"):
                tint = shirt
                pbr_kind = "tecido"
            elif material_name.contains("calca"):
                tint = pants
                pbr_kind = "jeans"
            elif material_name.contains("sapato"):
                tint = shoes
                pbr_kind = "borracha"
            elif material_name.contains("hair"):
                tint = hair.lightened(0.10)
                pbr_kind = "cabelo"
            elif mesh_name.contains("outfit"):
                if mesh_name.contains("_body") or mesh_name.contains("_arms"):
                    tint = shirt
                    pbr_kind = "tecido"
                elif mesh_name.contains("_legs"):
                    tint = pants
                    pbr_kind = "jeans"
                elif mesh_name.contains("_feet"):
                    tint = shoes
                    pbr_kind = "borracha"
            if tint == Color.WHITE:
                continue
            var material := source_material.duplicate() as BaseMaterial3D
            material.albedo_color = tint
            material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
            # PBR 4K Passo 2 — aplica textura realista por tipo (mantém <500KB pois textura é runtime, não bake no GLB)
            match pbr_kind:
                "tecido":
                    material.albedo_texture = TEXTURE_CREATOR_TOP
                    material.normal_enabled = true
                    material.normal_texture = TEXTURE_CREATOR_TOP_N
                    material.normal_scale = 0.50
                    material.roughness = 1.0
                    material.roughness_texture = TEXTURE_CREATOR_TOP_R
                    material.uv1_scale = Vector3(3.0, 3.0, 3.0)
                "jeans":
                    material.albedo_texture = TEXTURE_CREATOR_DENIM
                    material.normal_enabled = true
                    material.normal_texture = TEXTURE_CREATOR_DENIM_N
                    material.normal_scale = 0.60
                    material.roughness = 1.0
                    material.roughness_texture = TEXTURE_CREATOR_DENIM_R
                    material.uv1_scale = Vector3(3.0, 3.0, 3.0)
                "borracha":
                    material.albedo_texture = TEXTURE_CREATOR_RUBBER
                    material.normal_enabled = true
                    material.normal_texture = TEXTURE_CREATOR_RUBBER_N
                    material.normal_scale = 0.34
                    material.roughness = 1.0
                    material.roughness_texture = TEXTURE_CREATOR_RUBBER_R
                    material.uv1_scale = Vector3(2.5, 2.5, 2.5)
                "cabelo":
                    material.albedo_texture = TEXTURE_HAIR
                    material.roughness = 0.82
                    material.uv1_scale = Vector3(1.8, 1.8, 1.8)
                    material.anisotropy_enabled = true
                    material.anisotropy = 0.34
                    material.rim_enabled = true
                    material.rim = 0.12
                    material.rim_tint = 0.68
            # tecidos e jeans ganham uma reflexão larga e fraca, como fibras
            # reais, em vez do brilho plástico dos materiais uniformes.
            if pbr_kind in ["tecido", "jeans"]:
                material.clearcoat_enabled = true
                material.clearcoat = 0.10
                material.clearcoat_roughness = 0.42
            elif pbr_kind == "borracha":
                material.clearcoat_enabled = true
                material.clearcoat = 0.16
                material.clearcoat_roughness = 0.30
            mesh.set_surface_override_material(surface_index, material)

func _attach_creator_details(profile: Dictionary) -> void:
    if character_id != "influencer" or skeleton == null:
        return
    var shirt_color: Color = profile.get("shirt", Color("#171824"))
    var denim_color: Color = profile.get("pants", Color("#4f7897"))
    var shoe_color: Color = profile.get("shoes", Color("#171a26"))
    var accent_color: Color = profile.get("accent", Color("#d7b9e9"))
    var top_material := _creator_material(TEXTURE_CREATOR_TOP, shirt_color, 0.48)
    var denim_material := _creator_material(TEXTURE_CREATOR_DENIM, denim_color.lightened(0.10), 0.70)
    var metal_material := _creator_material(TEXTURE_CREATOR_METAL, accent_color, 0.18, 0.82)
    var boot_material := _creator_material(TEXTURE_CREATOR_RUBBER, shoe_color, 0.34)
    var tattoo_material := StandardMaterial3D.new()
    tattoo_material.albedo_color = Color("#21152f")
    tattoo_material.roughness = 0.58

    var torso_attachment := _bone_attachment("spine_02", "CreatorTorsoAttachment")
    if torso_attachment:
        var top_mesh := _get_placeholder_mesh() # Cylinder placeholder
        var top := _creator_mesh(torso_attachment, "CreatorTexturedTop", top_mesh, top_material)
        top.position = Vector3(0.0, -0.02, 0.0)
        top.scale = Vector3(1.0, 1.0, 0.72)
        for index in 6:
            var sequin_mesh := _get_placeholder_mesh() # Capsule placeholder
            var sequin := _creator_mesh(torso_attachment, "CreatorSequin_%02d" % index, sequin_mesh, metal_material)
            var column := index % 3
            var row := int(float(index) / 3.0)
            sequin.position = Vector3(-0.16 + float(column) * 0.16, 0.10 + float(row) * 0.07, -0.245)
            sequin.scale = Vector3(1.0, 0.55, 0.42)

    var pelvis_attachment := _bone_attachment("pelvis", "CreatorPelvisAttachment")
    if pelvis_attachment:
        var shorts_mesh := _get_placeholder_mesh() # Cylinder placeholder
        var shorts := _creator_mesh(pelvis_attachment, "CreatorDenimShorts", shorts_mesh, denim_material)
        shorts.position = Vector3(0.0, -0.015, 0.0)
        shorts.scale = Vector3(1.0, 1.0, 0.70)

    for side in [-1.0, 1.0]:
        var foot_attachment := _bone_attachment("foot_l" if side < 0.0 else "foot_r", "CreatorBootAttachment_%s" % ("L" if side < 0.0 else "R"))
        if foot_attachment:
            var cuff_mesh := _get_placeholder_mesh() # Cylinder placeholder
            var cuff := _creator_mesh(foot_attachment, "CreatorBootCuff", cuff_mesh, boot_material)
            cuff.position = Vector3(0.0, -0.055, 0.0)

    var right_hand := _bone_attachment("hand_r", "CreatorPhoneAttachment")
    if right_hand:
        var phone_mesh := _get_placeholder_mesh() # Box placeholder
        var phone := _creator_mesh(right_hand, "CreatorPhone", phone_mesh, metal_material)
        phone.position = Vector3(0.07, 0.11, -0.055)
        phone.rotation_degrees = Vector3(12.0, 0.0, -10.0)

    for side in [-1.0, 1.0]:
        var arm_bone := "lowerarm_l" if side < 0.0 else "lowerarm_r"
        var bracelet_attachment := _bone_attachment(arm_bone, "CreatorBraceletAttachment_%s" % ("L" if side < 0.0 else "R"))
        if bracelet_attachment:
            var bracelet_mesh := _get_placeholder_mesh() # Torus placeholder
            var bracelet := _creator_mesh(bracelet_attachment, "CreatorBracelet", bracelet_mesh, metal_material)
            bracelet.position = Vector3(0.0, 0.10, 0.0)

    var tattoo_attachment := _bone_attachment("lowerarm_r", "CreatorTattooAttachment")
    if tattoo_attachment:
        var tattoo_mesh := _get_placeholder_mesh() # Box placeholder
        var tattoo := _creator_mesh(tattoo_attachment, "CreatorTattoo", tattoo_mesh, tattoo_material)
        tattoo.position = Vector3(0.0, 0.16, -0.065)

    var head_attachment := _bone_attachment("Head", "CreatorHeadDetails")
    if head_attachment:
        for side in [-1.0, 1.0]:
            var earring_mesh := _get_placeholder_mesh() # Torus placeholder
            var earring := _creator_mesh(head_attachment, "CreatorEarring", earring_mesh, metal_material)
            earring.position = Vector3(side * 0.19, 0.015, 0.085)
            earring.rotation_degrees = Vector3(90.0, 0.0, 0.0)

func _attach_batch2_details(profile: Dictionary) -> void:
    # Lote 2: cada corredor novo recebe 1-2 props simples presos ao esqueleto,
    # no mesmo padrão da Nina Creator, mas com materiais de cor sólida.
    if skeleton == null:
        return
    var shirt: Color = profile.get("shirt", Color.WHITE)
    var pants: Color = profile.get("pants", Color.WHITE)
    var accent: Color = profile.get("accent", Color.WHITE)
    match character_id:
        "chico":
            _attach_cap("PostmanCap", shirt, accent, true)
            _attach_strap("PostmanStrap", accent)
            _attach_side_pouch("PostmanBag", pants)
        "tiao":
            _attach_hat("VaqueroHat", accent, 0.30, 0.16, 0.16)
        "beto":
            _attach_torus("SurferNecklace", "neck_01", accent, 0.085, 0.014, Vector3(0.0, -0.01, 0.0))
            _attach_torus("SurferWristband", "lowerarm_r", accent, 0.068, 0.016, Vector3(0.0, 0.13, 0.0))
        "nilo":
            _attach_hat("BakerToque", shirt, 0.155, 0.15, 0.17)
            _attach_baker_tray("BakerTray", accent)
        "professor":
            _attach_tie("ProfessorTie", accent)
            _attach_hand_book("ProfessorBook", pants)
        "marta":
            _attach_bandana("FairBandana", shirt)
            _attach_apron("FairApron", shirt.lightened(0.18))
        "zilda":
            _attach_headscarf("GrannyScarf", shirt)
            _attach_side_pouch("GrannyPurse", accent)
        "clara":
            _attach_cap("NurseCap", shirt, accent, false)
            _attach_badge("NurseBadge", accent)
        "deise":
            _attach_torus("CaptainArmband", "upperarm_l", accent, 0.066, 0.02, Vector3(0.0, 0.17, 0.0))
        "cida":
            _attach_cap("DriverCap", shirt, accent, true)
            _attach_badge("DriverBadge", accent)

func _batch_material(color: Color, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.roughness = roughness
    material.metallic = metallic
    return material

func _attach_cap(node_name: String, crown_color: Color, visor_color: Color, with_visor: bool) -> void:
    var head := _bone_attachment("Head", node_name + "Attachment")
    if head == null:
        return
    var crown_mesh := _get_placeholder_mesh() # Cylinder placeholder
    var crown := _creator_mesh(head, node_name + "Crown", crown_mesh, _batch_material(crown_color, 0.62))
    crown.position = Vector3(0.0, 0.165, 0.0)
    if with_visor:
        var visor_mesh := _get_placeholder_mesh() # Box placeholder
        var visor := _creator_mesh(head, node_name + "Visor", visor_mesh, _batch_material(visor_color.darkened(0.25), 0.55))
        visor.position = Vector3(0.0, 0.105, 0.16)

func _attach_hat(node_name: String, color: Color, _brim_radius: float, _crown_radius: float, crown_height: float) -> void:
    var head := _bone_attachment("Head", node_name + "Attachment")
    if head == null:
        return
    var brim_mesh := _get_placeholder_mesh() # Cylinder placeholder
    var brim := _creator_mesh(head, node_name + "Brim", brim_mesh, _batch_material(color, 0.66))
    brim.position = Vector3(0.0, 0.135, 0.0)
    var crown_mesh := _get_placeholder_mesh() # Cylinder placeholder
    var crown := _creator_mesh(head, node_name + "Crown", crown_mesh, _batch_material(color.darkened(0.12), 0.66))
    crown.position = Vector3(0.0, 0.135 + crown_height * 0.5, 0.0)

func _attach_torus(node_name: String, bone_name: String, color: Color, _inner_radius: float, _outer_radius: float, offset: Vector3) -> void:
    var bone := _bone_attachment(bone_name, node_name + "Attachment")
    if bone == null:
        return
    var torus_mesh := _get_placeholder_mesh() # Torus placeholder
    var torus := _creator_mesh(bone, node_name, torus_mesh, _batch_material(color, 0.5))
    torus.position = offset
    torus.rotation_degrees.x = 90.0

func _attach_strap(node_name: String, color: Color) -> void:
    var torso := _bone_attachment("spine_02", node_name + "Attachment")
    if torso == null:
        return
    var strap_mesh := _get_placeholder_mesh() # Box placeholder
    var strap := _creator_mesh(torso, node_name, strap_mesh, _batch_material(color, 0.55))
    strap.position = Vector3(0.05, -0.02, -0.20)
    strap.rotation_degrees.z = 38.0

func _attach_side_pouch(node_name: String, color: Color) -> void:
    var pelvis := _bone_attachment("pelvis", node_name + "Attachment")
    if pelvis == null:
        return
    var pouch_mesh := _get_placeholder_mesh() # Box placeholder
    var pouch := _creator_mesh(pelvis, node_name, pouch_mesh, _batch_material(color, 0.6))
    pouch.position = Vector3(0.235, -0.06, -0.05)
    pouch.rotation_degrees.z = 12.0

func _attach_baker_tray(node_name: String, bread_color: Color) -> void:
    var hand := _bone_attachment("hand_l", node_name + "Attachment")
    if hand == null:
        return
    var tray_mesh := _get_placeholder_mesh() # Cylinder placeholder
    var tray := _creator_mesh(hand, node_name, tray_mesh, _batch_material(Color("#b9bec7"), 0.35, 0.55))
    tray.position = Vector3(0.0, 0.09, 0.0)
    for index in 3:
        var bread_mesh := _get_placeholder_mesh() # Capsule placeholder
        var bread := _creator_mesh(hand, "%sBread_%d" % [node_name, index], bread_mesh, _batch_material(bread_color, 0.7))
        bread.position = Vector3(-0.075 + float(index) * 0.075, 0.135, 0.0)
        bread.scale = Vector3(1.0, 0.78, 1.0)

func _attach_tie(node_name: String, color: Color) -> void:
    var torso := _bone_attachment("spine_02", node_name + "Attachment")
    if torso == null:
        return
    var knot_mesh := _get_placeholder_mesh() # Box placeholder
    var knot := _creator_mesh(torso, node_name + "Knot", knot_mesh, _batch_material(color.darkened(0.15), 0.55))
    knot.position = Vector3(0.0, 0.13, -0.215)
    var blade_mesh := _get_placeholder_mesh() # Box placeholder
    var blade := _creator_mesh(torso, node_name + "Blade", blade_mesh, _batch_material(color, 0.55))
    blade.position = Vector3(0.0, -0.045, -0.22)

func _attach_hand_book(node_name: String, color: Color) -> void:
    var hand := _bone_attachment("hand_l", node_name + "Attachment")
    if hand == null:
        return
    var book_mesh := _get_placeholder_mesh() # Box placeholder
    var book := _creator_mesh(hand, node_name, book_mesh, _batch_material(color, 0.72))
    book.position = Vector3(0.0, 0.11, 0.0)
    book.rotation_degrees.y = 12.0

func _attach_bandana(node_name: String, color: Color) -> void:
    var head := _bone_attachment("Head", node_name + "Attachment")
    if head == null:
        return
    var cloth_mesh := _get_placeholder_mesh() # Cylinder placeholder
    var cloth := _creator_mesh(head, node_name, cloth_mesh, _batch_material(color, 0.8))
    cloth.position = Vector3(0.0, 0.135, 0.0)

func _attach_apron(node_name: String, color: Color) -> void:
    var torso := _bone_attachment("spine_01", node_name + "Attachment")
    if torso == null:
        return
    var apron_mesh := _get_placeholder_mesh() # Box placeholder
    var apron := _creator_mesh(torso, node_name, apron_mesh, _batch_material(color, 0.8))
    apron.position = Vector3(0.0, -0.14, -0.20)

func _attach_headscarf(node_name: String, color: Color) -> void:
    var head := _bone_attachment("Head", node_name + "Attachment")
    if head == null:
        return
    var scarf_mesh := _get_placeholder_mesh() # Capsule placeholder
    var scarf := _creator_mesh(head, node_name, scarf_mesh, _batch_material(color, 0.82))
    scarf.position = Vector3(0.0, 0.07, -0.01)
    scarf.scale = Vector3(1.02, 0.72, 1.04)

func _attach_badge(node_name: String, color: Color) -> void:
    var torso := _bone_attachment("spine_02", node_name + "Attachment")
    if torso == null:
        return
    var badge_mesh := _get_placeholder_mesh() # Box placeholder
    var badge := _creator_mesh(torso, node_name, badge_mesh, _batch_material(color, 0.4, 0.3))
    badge.position = Vector3(0.125, 0.03, -0.215)


func _get_placeholder_mesh() -> Mesh:
    return ArrayMesh.new()

func _bone_attachment(bone_name: String, node_name: String) -> BoneAttachment3D:
    if skeleton == null or not bone_indices.has(bone_name):
        return null
    var attachment := BoneAttachment3D.new()
    attachment.name = node_name
    attachment.bone_name = bone_name
    skeleton.add_child(attachment)
    return attachment

func _creator_mesh(parent: Node3D, node_name: String, mesh: Mesh, material: Material) -> MeshInstance3D:
    var instance := MeshInstance3D.new()
    instance.name = node_name
    instance.mesh = mesh
    instance.material_override = material
    instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
    parent.add_child(instance)
    return instance

func _creator_material(texture: Texture2D, color: Color, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.albedo_texture = texture
    material.roughness = roughness
    material.metallic = metallic
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    if texture == TEXTURE_CREATOR_TOP:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_CREATOR_TOP_N
        material.normal_scale = 0.5
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_CREATOR_TOP_R
        material.uv1_scale = Vector3(3.0, 3.0, 3.0)
    elif texture == TEXTURE_CREATOR_DENIM:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_CREATOR_DENIM_N
        material.normal_scale = 0.6
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_CREATOR_DENIM_R
        material.uv1_scale = Vector3(3.0, 3.0, 3.0)
    elif texture == TEXTURE_CREATOR_METAL:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_CREATOR_METAL_N
        material.normal_scale = 0.4
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_CREATOR_METAL_R
    elif texture == TEXTURE_CREATOR_RUBBER:
        material.normal_enabled = true
        material.normal_texture = TEXTURE_CREATOR_RUBBER_N
        material.normal_scale = 0.3
        material.roughness = 1.0
        material.roughness_texture = TEXTURE_CREATOR_RUBBER_R
    return material

func _setup_original_animation() -> void:
    # O GLB original do Lote 19 já vem com AnimationPlayer e Skeleton no mesmo arquivo.
    var embedded: AnimationPlayer = _find_animation_player(model_root)
    if embedded == null:
        using_external_animation = false
        _apply_neutral_pose()
        return
    animation_player = embedded
    # Garante que as animações rodem em loop suave
    for anim_name in animation_player.get_animation_list():
        var anim: Animation = animation_player.get_animation(anim_name)
        if anim != null:
            anim.loop_mode = Animation.LOOP_LINEAR
    using_external_animation = _resolve_clip_name("Sprint_Loop") != "" or _resolve_clip_name("Idle_Loop") != "" or _resolve_clip_name("Walk_Loop") != ""
    if using_external_animation:
        _play_clip("Sprint_Loop" if not world_mode else "Walk_Loop")
    else:
        _apply_neutral_pose()

func _resolve_clip_name(clip: String) -> String:
    if animation_player == null:
        return ""
    if animation_player.has_animation(clip):
        return clip
    if animation_player.has_animation("body/" + clip):
        return "body/" + clip
    for lib_name in animation_player.get_animation_library_list():
        var prefixed := (lib_name + "/" + clip) if lib_name != "" else clip
        if animation_player.has_animation(prefixed):
            return prefixed
    return ""

func _setup_animation_library() -> void:
    animation_player = AnimationPlayer.new()
    animation_player.name = "QuaterniusAnimationPlayer"
    model_root.add_child(animation_player)
    animation_player.root_node = animation_player.get_path_to(model_root)
    var library: AnimationLibrary = null
    if ResourceLoader.exists(ANIMATION_LIBRARY_PATH):
        library = load(ANIMATION_LIBRARY_PATH) as AnimationLibrary
    # The compact .res is committed for a fast offline import. If it predates
    # the jump clip, use the original Godot-compatible Standard GLB as the
    # authoritative library; both share the Universal Humanoid rig.
    if library == null or not _library_has(library, "Jump_Loop"):
        library = _extract_animation_library_from_glb()
    if library == null:
        using_external_animation = false
        _apply_neutral_pose()
        return
    animation_player.add_animation_library("body", library)
    using_external_animation = animation_player.has_animation("body/Idle_Loop") and _library_drives_skeleton(library)
    if using_external_animation:
        _play_clip("Idle_Loop")
    else:
        _apply_neutral_pose()

func _library_has(library: AnimationLibrary, clip: String) -> bool:
    return library != null and library.has_animation(clip)

## A biblioteca precisa animar ESTE esqueleto: as trilhas guardam o osso no
## subcaminho (`Skeleton3D:pelvis`). Pacotes de animação de outro rig (por
## exemplo o Universal Humanoid, com Hips/LeftUpperLeg) não mexem em nenhum osso
## do corpo e precisam cair na pose procedural em vez de congelar o personagem.
func _library_drives_skeleton(library: AnimationLibrary) -> bool:
    if library == null or skeleton == null:
        return false
    var bones: Dictionary = {}
    for index in skeleton.get_bone_count():
        bones[skeleton.get_bone_name(index)] = true
    var checked := 0
    var matched := 0
    for clip_name in library.get_animation_list():
        var animation := library.get_animation(clip_name)
        if animation == null:
            continue
        for track in animation.get_track_count():
            if animation.track_get_type(track) != Animation.TYPE_ROTATION_3D:
                continue
            var path := animation.track_get_path(track)
            if path.get_subname_count() == 0:
                continue
            checked += 1
            if bones.has(str(path.get_subname(0))):
                matched += 1
        if checked > 0:
            break
    return checked > 0 and float(matched) / float(checked) >= 0.5

func _extract_animation_library_from_glb() -> AnimationLibrary:
    if _biblioteca_cache != null:
        return _biblioteca_cache
    if not ResourceLoader.exists(ANIMATION_SOURCE_PATH):
        return null
    var source_scene := load(ANIMATION_SOURCE_PATH) as PackedScene
    if source_scene == null:
        return null
    var source_root := source_scene.instantiate()
    var source_player := _find_animation_player(source_root)
    if source_player == null:
        source_root.free()
        return null
    var source_library: AnimationLibrary = null
    for library_name in source_player.get_animation_library_list():
        source_library = source_player.get_animation_library(library_name)
        if source_library != null and source_library.has_animation("Jump_Loop"):
            break
    source_root.free()
    _biblioteca_cache = source_library
    return source_library

func _find_animation_player(node: Node) -> AnimationPlayer:
    var pending: Array[Node] = [node]
    while not pending.is_empty():
        var current: Node = pending.pop_back()
        if current is AnimationPlayer:
            return current as AnimationPlayer
        for child in current.get_children():
            pending.append(child)
    return null

func _play_clip(clip: String) -> void:
    if not using_external_animation or animation_player == null:
        return
    var animation_name := _resolve_clip_name(clip)
    if animation_name == "":
        return
    if current_clip == clip:
        return
    current_clip = clip
    animation_player.play(animation_name, 0.12)

func _apply_neutral_pose() -> void:
    if skeleton == null:
        return
    for bone_name in rest_rotations:
        skeleton.set_bone_pose_rotation(int(bone_indices[bone_name]), rest_rotations[bone_name])
    _set_bone_extra("upperarm_l", Quaternion(Vector3.RIGHT, -1.29) * Quaternion(Vector3.FORWARD, 0.17))
    _set_bone_extra("upperarm_r", Quaternion(Vector3.RIGHT, -1.29) * Quaternion(Vector3.FORWARD, -0.17))
    _set_bone_extra("lowerarm_l", Quaternion(Vector3.FORWARD, 0.38))
    _set_bone_extra("lowerarm_r", Quaternion(Vector3.FORWARD, -0.38))

func _set_bone_extra(bone_name: String, extra: Quaternion) -> void:
    if not bone_indices.has(bone_name):
        return
    var index: int = int(bone_indices[bone_name])
    var base: Quaternion = rest_rotations.get(bone_name, Quaternion.IDENTITY)
    skeleton.set_bone_pose_rotation(index, base * extra)

## Pose sentada para NPCs de veiculo (motoqueiro): usada quando a biblioteca
## de animacao nao esta disponivel, para o piloto nunca aparecer em pe.
func apply_world_seated_pose() -> void:
    if skeleton == null or using_external_animation:
        return
    _apply_neutral_pose()
    _set_bone_extra("thigh_l", Quaternion(Vector3(1.0, 0.0, 0.0), -1.25))
    _set_bone_extra("thigh_r", Quaternion(Vector3(1.0, 0.0, 0.0), -1.25))
    _set_bone_extra("calf_l", Quaternion(Vector3(1.0, 0.0, 0.0), 1.30))
    _set_bone_extra("calf_r", Quaternion(Vector3(1.0, 0.0, 0.0), 1.30))
    _set_bone_extra("upperarm_l", Quaternion(Vector3.RIGHT, -0.85))
    _set_bone_extra("upperarm_r", Quaternion(Vector3.RIGHT, -0.85))


func _apply_procedural_fallback_pose(stride: float, crouching: bool, jumping: bool) -> void:
    if skeleton == null:
        return
    _apply_neutral_pose()
    var leg_swing := stride * 0.65
    var knee_bend := 0.54 if crouching else (0.18 if jumping else 0.0)
    # Pernas: balanço alternado com flexão do joelho
    _set_bone_extra("thigh_l", Quaternion(Vector3(1.0, 0.0, 0.0), leg_swing + knee_bend))
    _set_bone_extra("thigh_r", Quaternion(Vector3(1.0, 0.0, 0.0), -leg_swing + knee_bend))
    _set_bone_extra("calf_l", Quaternion(Vector3(1.0, 0.0, 0.0), maxf(0.0, -stride) * 0.75 + knee_bend))
    _set_bone_extra("calf_r", Quaternion(Vector3(1.0, 0.0, 0.0), maxf(0.0, stride) * 0.75 + knee_bend))
    # Tronco: leve inclinação atlética para a frente
    _set_bone_extra("spine_01", Quaternion(Vector3(1.0, 0.0, 0.0), 0.12))
    _set_bone_extra("spine_02", Quaternion(Vector3(1.0, 0.0, 0.0), 0.06))
    # Braços: cotovelos flexionados a ~80 graus e balanço alternado longitudinal (oposto às pernas)
    var arm_swing_l := -stride * 0.55
    var arm_swing_r := stride * 0.55
    _set_bone_extra("upperarm_l", Quaternion(Vector3.RIGHT, -1.31) * Quaternion(Vector3.FORWARD, 0.20 + arm_swing_l))
    _set_bone_extra("upperarm_r", Quaternion(Vector3.RIGHT, -1.31) * Quaternion(Vector3.FORWARD, -0.20 + arm_swing_r))
    _set_bone_extra("lowerarm_l", Quaternion(Vector3.FORWARD, 1.40))
    _set_bone_extra("lowerarm_r", Quaternion(Vector3.FORWARD, -1.40))

func set_motion(run_phase: float, is_running: bool, is_crouching: bool, jump_height: float, lane_velocity: float, speed: float = 0.0, dt: float = 0.016) -> void:
    motion_clock = run_phase
    var jumping := jump_height > 0.05
    var clip := "Sprint_Loop"
    if jumping:
        clip = "Jump_Loop"
    elif is_crouching:
        clip = "Crouch_Fwd_Loop" if is_running else "Crouch_Idle_Loop"
    elif is_running:
        clip = "Sprint_Loop"
    else:
        clip = "Sprint_Loop" if not world_mode else "Idle_Loop"

    if using_external_animation and _resolve_clip_name(clip) != "":
        _play_clip(clip)
    else:
        var stride := sin(run_phase * 0.82)
        if skeleton == null:
            _animate_mesh_only(stride, is_crouching, jumping)
        else:
            _apply_procedural_fallback_pose(stride, is_crouching, jumping)
    _match_playback_to_speed(speed, is_running, is_crouching, jumping)
    if runner_shadow != null:
        runner_shadow.position.y = _run_ground_y(global_position.x) + 0.025 - position.y
        var shadow_factor := 1.0 - clampf(jump_height * 0.12, 0.0, 0.24)
        runner_shadow.scale = Vector3.ONE * shadow_factor

    # --- Simulação de Física Secundária de Movimento (Hair Spring & Spine Dynamics) ---
    var delta_t: float = clampf(dt, 0.005, 0.05)
    var jump_v: float = (jump_height - _last_jump_h) / delta_t
    _last_jump_h = jump_height

    # 1. Pitch do rabo de cavalo e cabeça (cadência de passada, compressão de salto e aterrissagem)
    var cadence_impulse := sin(run_phase * 2.0) * (0.045 if is_running and not is_crouching else 0.0)
    var jump_inertia := -jump_v * 0.022
    var target_hair_pitch := clampf(cadence_impulse + jump_inertia + (0.05 if is_crouching else 0.0), -0.22, 0.26)
    var pitch_accel := 30.0 * (target_hair_pitch - _hair_pitch) - 7.5 * _hair_pitch_vel
    _hair_pitch_vel += pitch_accel * delta_t
    _hair_pitch += _hair_pitch_vel * delta_t

    # 2. Yaw/Sway lateral do rabo de cavalo (inércia centrífuga na troca de faixa)
    var target_hair_yaw := clampf(-lane_velocity * 0.055, -0.20, 0.20)
    var yaw_accel := 26.0 * (target_hair_yaw - _hair_yaw) - 7.0 * _hair_yaw_vel
    _hair_yaw_vel += yaw_accel * delta_t
    _hair_yaw += _hair_yaw_vel * delta_t

    # 3. Roll/Inclinação atlética da coluna vertebral (banca suave na curva e balanço sagital)
    var target_spine_roll := clampf(-lane_velocity * 0.038, -0.14, 0.14) + sin(run_phase) * (0.012 if is_running else 0.0)
    var roll_accel := 24.0 * (target_spine_roll - _spine_roll) - 8.0 * _spine_roll_vel
    _spine_roll_vel += roll_accel * delta_t
    _spine_roll += _spine_roll_vel * delta_t

    # 4. Aplicação no pivô e na curvatura da coluna (spine_02, spine_03)
    if model_pivot != null:
        var model_lean := clampf(_spine_roll * 0.50, -0.12, 0.12)
        model_pivot.rotation.z = lerpf(model_pivot.rotation.z, model_lean, 0.18)

    if skeleton != null:
        if bone_indices.has("spine_02"):
            var s2_base: Quaternion = rest_rotations.get("spine_02", Quaternion.IDENTITY)
            var s2_lean := Quaternion(Vector3.FORWARD, _spine_roll * 0.35)
            skeleton.set_bone_pose_rotation(int(bone_indices["spine_02"]), s2_base * s2_lean)
        if bone_indices.has("spine_03"):
            var s3_base: Quaternion = rest_rotations.get("spine_03", Quaternion.IDENTITY)
            var s3_lean := Quaternion(Vector3.FORWARD, _spine_roll * 0.45)
            var s3_pitch := Quaternion(Vector3.RIGHT, -_hair_pitch * 0.18)
            skeleton.set_bone_pose_rotation(int(bone_indices["spine_03"]), s3_base * s3_lean * s3_pitch)

    # 5. Cabeça dinâmica com look-at antecipatório e compensação elástica
    # L27 polimento: head look-at 12° na curva (suaviza imersão, audit 5.0→6.5)
    if skeleton != null and bone_indices.has("Head"):
        var look_yaw := clampf(lane_velocity * 0.04, -0.21, 0.21)
        var base_rot: Quaternion = rest_rotations.get("Head", Quaternion.IDENTITY)
        var look_rot := Quaternion(Vector3.UP, look_yaw + _hair_yaw * 0.35)
        var hair_pitch_rot := Quaternion(Vector3.RIGHT, _hair_pitch * 0.65)
        var target_head := base_rot * look_rot * hair_pitch_rot
        skeleton.set_bone_pose_rotation(int(bone_indices["Head"]), base_rot.slerp(target_head, 0.22))
    # --- Overlay de bracos (sprint/walk): bombeio sagital alternado; fora
    # desses clipes solta no ato (a pose volta ao baked do pulo/agacho/idle).
    if using_external_animation and skeleton != null \
            and (current_clip == "Sprint_Loop" or current_clip == "Walk_Loop"):
        _apply_arm_swing_overlay(delta_t)
    elif _arm_have_from:
        _arm_have_from = false
        _arm_w = 0.0
    # L27: foot IK placeholder removido (evita drift); plantar garantido por heightmap_scale + cadence já faz foot lock

## O jogo avança o cenário na velocidade real da corrida; a animação de sprint
## sozinha cobre ~4 m/s. Escalar a cadência mantém o pé plantado no chão (sem
## patinação) durante o dash e os capítulos rápidos.
## Overlay de bracos no sprint/walk (FK validado offline no julia.glb): o
## clipe baked gira o ombro no proprio eixo (twist) e varre o antebraco no
## plano lateral, com os dois bracos em fase (efeito "bater asa"). Aqui o
## ombro (eixo Z local = transversal) bombeia no plano sagital em antifase
## com a perna oposta, e o cotovelo fecha a frente / abre atras. A fase vem
## da posicao exata do clipe (imune a speed_scale); a entrada faz rampa de
## 0,12 s a partir da pose baked capturada.
func _apply_arm_swing_overlay(dt: float) -> void:
    if skeleton == null or animation_player == null:
        return
    var is_walk := current_clip == "Walk_Loop"
    var anim_name := _resolve_clip_name(current_clip)
    var clip_len := 0.667
    if anim_name != "":
        if not _arm_len_cache.has(anim_name):
            var anim := animation_player.get_animation(anim_name)
            _arm_len_cache[anim_name] = anim.length if anim != null else 0.667
        clip_len = float(_arm_len_cache[anim_name])
    var pos := 0.0
    if anim_name != "" and animation_player.current_animation == anim_name:
        pos = animation_player.current_animation_position
    # +1 = braco E a frente (perna D a frente): fracoes medidas no GLB.
    var phase := TAU * (pos / maxf(clip_len, 0.01) - (0.28 if is_walk else 0.30))
    var s := sin(phase)
    if not _arm_have_from:
        _arm_have_from = true
        _arm_w = 0.0
        _arm_from.clear()
        for bone_name in ["upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r"]:
            if bone_indices.has(bone_name):
                var idx: int = int(bone_indices[bone_name])
                var rest_q: Quaternion = rest_rotations.get(bone_name, Quaternion.IDENTITY)
                _arm_from[bone_name] = rest_q.inverse() * skeleton.get_bone_pose_rotation(idx)
    _arm_w = minf(1.0, _arm_w + dt / 0.12)
    var w := _arm_w * _arm_w * (3.0 - 2.0 * _arm_w)
    var mid := -5.0 if is_walk else -7.5
    # O balanço é em antifase: enquanto uma mão avança, a outra recua.
    # Antes ambas recebiam o mesmo sinal e pareciam bater asas juntas.
    var amp := 9.0 if is_walk else 14.0
    var ez_base := 28.0 if is_walk else 48.0
    var ez_pump := 3.0 if is_walk else 6.0
    _apply_arm_bone("upperarm_l", -78.0, mid + amp * s, w)
    _apply_arm_bone("upperarm_r", -78.0, -mid - amp * s, w)
    _apply_arm_bone("lowerarm_l", 0.0, ez_base - ez_pump * s, w)
    _apply_arm_bone("lowerarm_r", 0.0, -(ez_base - ez_pump * s), w)


func _apply_arm_bone(bone_name: String, x_deg: float, z_deg: float, w: float) -> void:
    if not bone_indices.has(bone_name):
        return
    var idx: int = int(bone_indices[bone_name])
    var rest_q: Quaternion = rest_rotations.get(bone_name, Quaternion.IDENTITY)
    # BACK (+Z = frente do esqueleto: modelo olha +Z, yaw PI leva a -Z no
    # mundo). FORWARD (-Z) invertia tudo: ombro para tras e cotovelo em
    # hiperextensao (mao 0,20 atras da linha do cotovelo, angulo impossivel).
    var target := Quaternion(Vector3.RIGHT, deg_to_rad(x_deg)) * Quaternion(Vector3.BACK, deg_to_rad(z_deg))
    var from_extra: Quaternion = _arm_from.get(bone_name, target)
    skeleton.set_bone_pose_rotation(idx, rest_q * from_extra.slerp(target, w))


## Chao sob o corredor (espelha game_3d._ground_y_for_x): a sombra acompanha
## o asfalto quando ele corre na faixa 0.
func _run_ground_y(x: float) -> float:
    var t := clampf((x - (RUN_CURB_X - 0.25)) / 0.5, 0.0, 1.0)
    var s := t * t * (3.0 - 2.0 * t)
    return lerpf(RUN_STREET_Y, 0.0, s)


func _match_playback_to_speed(speed: float, is_running: bool, is_crouching: bool, jumping: bool) -> void:
    if animation_player == null:
        return
    var playback := 1.0
    if using_external_animation and is_running and not is_crouching and not jumping and speed > LOCOMOTION_CLIP_SPEED:
        playback = clampf(speed / LOCOMOTION_CLIP_SPEED, 1.0, LOCOMOTION_MAX_PLAYBACK)
    animation_player.speed_scale = playback

func _configure_mesh_shadows(node: Node) -> void:
    # No Godot 4 existem apenas "cast_shadow" por instancia; o recebimento e dado
    # pelo material (BaseMaterial3D.disable_receive_shadows, falso por padrao).
    for mesh in _skinned_meshes(node):
        mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

func _build_fallback(reason: String) -> void:
    push_warning("Humanoide Quaternius indisponível (%s); ativando fallback de diagnóstico." % reason)
    if is_instance_valid(model_root):
        model_root.free()
    model_root = null
    primary_asset_loaded = false
    var fallback_root := Node3D.new()
    fallback_root.name = "HumanAssetFallback"
    if not is_instance_valid(model_pivot):
        model_pivot = Node3D.new()
        model_pivot.name = "ModelPivot"
        add_child(model_pivot)
    model_pivot.add_child(fallback_root)
    var body := MeshInstance3D.new()
    var body_mesh := _get_placeholder_mesh() # Capsule placeholder
    body.mesh = body_mesh
    body.position.y = 0.98
    var body_material := StandardMaterial3D.new()
    body_material.albedo_color = Color("#c98364")
    body_material.roughness = 0.62
    body.material_override = body_material
    fallback_root.add_child(body)
    var head := MeshInstance3D.new()
    var head_mesh := _get_placeholder_mesh() # Capsule placeholder
    head.mesh = head_mesh
    head.position.y = 1.92
    head.material_override = body_material
    fallback_root.add_child(head)
    model_root = fallback_root
    _configure_mesh_shadows(fallback_root)

func is_primary_asset_loaded() -> bool:
    return primary_asset_loaded
