extends Node3D
## Humanoide 3D principal do runner.
##
## O personagem de gameplay é um asset real do Quaternius Universal Base
## Characters: corpo humano skinned, cabelo, olhos e roupa modular com UV/PBR.
## O runner nunca depende de primitivas para a aparência principal. Primitivas
## só existem no fallback de diagnóstico caso o importador do GLTF falhe.

const CHARACTER_DATA = preload("res://scripts/character_data.gd")
const TEXTURE_CREATOR_TOP = preload("res://assets/textures/tecido_urbano.svg")
const TEXTURE_CREATOR_DENIM = preload("res://assets/textures/jeans_realista.png")
const TEXTURE_CREATOR_METAL = preload("res://assets/textures/metal_pintado.svg")
const TEXTURE_CREATOR_RUBBER = preload("res://assets/textures/borracha.svg")

const MODEL_ROOT := "res://assets/characters/quaternius"
const BASE_ROOT := MODEL_ROOT + "/base"
const PARTS_ROOT := MODEL_ROOT + "/parts"
const ANIMATION_LIBRARY_PATH := MODEL_ROOT + "/animation/UAL1_Standard.res"
const ANIMATION_SOURCE_PATH := MODEL_ROOT + "/animation/UAL1_Standard.glb"
const MODEL_SCALE := 1.18
const MODEL_FLOOR_OFFSET := 0.012
const CLOTHING_INFLATE := 0.008
const PLAYER_HEIGHT := 2.15

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
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
var runner_shadow: MeshInstance3D
var current_clip := ""
var using_external_animation := false
var primary_asset_loaded := false
var motion_clock := 0.0
var bone_indices: Dictionary = {}
var rest_rotations: Dictionary = {}

func _ready() -> void:
    set_character(character_id)

func set_character(next_id: String) -> void:
    character_id = CHARACTER_DATA.canonical_id(next_id)
    var profile: Dictionary = CHARACTER_DATA.get_character(character_id)
    gender = "F" if str(profile.get("gender", "M")) == "F" else "M"
    _clear_character()
    _build_shadow()
    var body_path: String = str(BODY_PATHS.get(gender, BODY_PATHS["M"]))
    var body_scene := load(body_path) as PackedScene
    if body_scene == null:
        _build_fallback("asset principal não importado")
        return
    model_root = body_scene.instantiate() as Node3D
    if model_root == null:
        _build_fallback("cena GLTF inválida")
        return
    model_root.name = "QuaterniusHuman"
    model_root.scale = Vector3.ONE * MODEL_SCALE
    model_root.position.y = MODEL_FLOOR_OFFSET
    add_child(model_root)
    skeleton = _find_skeleton(model_root)
    if skeleton == null:
        _build_fallback("esqueleto humano não encontrado")
        return
    _cache_skeleton()
    _split_base_body()
    _attach_outfit(gender)
    _apply_skin_tint(profile.get("skin", Color.WHITE))
    _apply_profile_palette(profile)
    _attach_creator_details(profile)
    _setup_animation_library()
    _configure_mesh_shadows(model_root)
    primary_asset_loaded = true

func _clear_character() -> void:
    if is_instance_valid(model_root):
        model_root.free()
    model_root = null
    skeleton = null
    animation_player = null
    current_clip = ""
    using_external_animation = false
    primary_asset_loaded = false
    bone_indices.clear()
    rest_rotations.clear()
    if is_instance_valid(runner_shadow):
        runner_shadow.free()
    runner_shadow = null

func _build_shadow() -> void:
    runner_shadow = MeshInstance3D.new()
    runner_shadow.name = "RunnerShadow"
    var shadow_mesh := QuadMesh.new()
    shadow_mesh.size = Vector2(1.05, 1.55)
    runner_shadow.mesh = shadow_mesh
    runner_shadow.rotation_degrees.x = -90.0
    runner_shadow.position = Vector3(0.0, 0.025, 0.06)
    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.015, 0.025, 0.04, 0.34)
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
        region_mesh.receive_shadow = true
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
        var influences: int = int(bones.size() / vertices.size())
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
            worn.receive_shadow = true
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
    # Keep the authored texture detail and multiply only the skin regions.
    var tint := Color(skin_color.r / 0.72, skin_color.g / 0.48, skin_color.b / 0.36, 1.0)
    tint.r = clampf(tint.r, 0.62, 1.35)
    tint.g = clampf(tint.g, 0.62, 1.35)
    tint.b = clampf(tint.b, 0.62, 1.35)
    for child in model_root.get_children():
        if not child is MeshInstance3D:
            continue
        var mesh := child as MeshInstance3D
        var base_skin := str(mesh.name).begins_with("BaseSkin_")
        if mesh.mesh == null:
            continue
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
        var garment_color := Color.WHITE
        if mesh_name.contains("outfit"):
            if mesh_name.contains("_body") or mesh_name.contains("_arms"):
                garment_color = shirt
            elif mesh_name.contains("_legs"):
                garment_color = pants
            elif mesh_name.contains("_feet"):
                garment_color = shoes
        for surface_index in mesh.mesh.get_surface_count():
            var source_material := mesh.get_surface_override_material(surface_index)
            if source_material == null:
                source_material = mesh.mesh.surface_get_material(surface_index)
            if not source_material is BaseMaterial3D:
                continue
            var material_name := str(source_material.resource_name).to_lower()
            if material_name.contains("quaterniusskin"):
                continue
            var tint := garment_color
            if material_name.contains("hair"):
                tint = hair.lightened(0.10)
            if tint == Color.WHITE:
                continue
            var material := source_material.duplicate() as BaseMaterial3D
            material.albedo_color = tint
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
        var top_mesh := CylinderMesh.new()
        top_mesh.top_radius = 0.27
        top_mesh.bottom_radius = 0.33
        top_mesh.height = 0.25
        top_mesh.radial_segments = 32
        var top := _creator_mesh(torso_attachment, "CreatorTexturedTop", top_mesh, top_material)
        top.position = Vector3(0.0, -0.02, 0.0)
        top.scale = Vector3(1.0, 1.0, 0.72)
        for index in 6:
            var sequin_mesh := SphereMesh.new()
            sequin_mesh.radius = 0.018
            sequin_mesh.height = 0.036
            sequin_mesh.radial_segments = 12
            sequin_mesh.rings = 6
            var sequin := _creator_mesh(torso_attachment, "CreatorSequin_%02d" % index, sequin_mesh, metal_material)
            sequin.position = Vector3(-0.16 + float(index % 3) * 0.16, 0.10 + float(index / 3) * 0.07, -0.245)
            sequin.scale = Vector3(1.0, 0.55, 0.42)

    var pelvis_attachment := _bone_attachment("pelvis", "CreatorPelvisAttachment")
    if pelvis_attachment:
        var shorts_mesh := CylinderMesh.new()
        shorts_mesh.top_radius = 0.30
        shorts_mesh.bottom_radius = 0.34
        shorts_mesh.height = 0.22
        shorts_mesh.radial_segments = 32
        var shorts := _creator_mesh(pelvis_attachment, "CreatorDenimShorts", shorts_mesh, denim_material)
        shorts.position = Vector3(0.0, -0.015, 0.0)
        shorts.scale = Vector3(1.0, 1.0, 0.70)

    for side in [-1.0, 1.0]:
        var foot_attachment := _bone_attachment("foot_l" if side < 0.0 else "foot_r", "CreatorBootAttachment_%s" % ("L" if side < 0.0 else "R"))
        if foot_attachment:
            var cuff_mesh := CylinderMesh.new()
            cuff_mesh.top_radius = 0.105
            cuff_mesh.bottom_radius = 0.13
            cuff_mesh.height = 0.17
            cuff_mesh.radial_segments = 24
            var cuff := _creator_mesh(foot_attachment, "CreatorBootCuff", cuff_mesh, boot_material)
            cuff.position = Vector3(0.0, -0.055, 0.0)

    var right_hand := _bone_attachment("hand_r", "CreatorPhoneAttachment")
    if right_hand:
        var phone_mesh := BoxMesh.new()
        phone_mesh.size = Vector3(0.105, 0.20, 0.025)
        var phone := _creator_mesh(right_hand, "CreatorPhone", phone_mesh, metal_material)
        phone.position = Vector3(0.07, 0.11, -0.055)
        phone.rotation_degrees = Vector3(12.0, 0.0, -10.0)

    for side in [-1.0, 1.0]:
        var arm_bone := "lowerarm_l" if side < 0.0 else "lowerarm_r"
        var bracelet_attachment := _bone_attachment(arm_bone, "CreatorBraceletAttachment_%s" % ("L" if side < 0.0 else "R"))
        if bracelet_attachment:
            var bracelet_mesh := TorusMesh.new()
            bracelet_mesh.inner_radius = 0.075
            bracelet_mesh.outer_radius = 0.018
            bracelet_mesh.rings = 24
            bracelet_mesh.ring_segments = 10
            var bracelet := _creator_mesh(bracelet_attachment, "CreatorBracelet", bracelet_mesh, metal_material)
            bracelet.position = Vector3(0.0, 0.10, 0.0)

    var tattoo_attachment := _bone_attachment("lowerarm_r", "CreatorTattooAttachment")
    if tattoo_attachment:
        var tattoo_mesh := BoxMesh.new()
        tattoo_mesh.size = Vector3(0.13, 0.10, 0.012)
        var tattoo := _creator_mesh(tattoo_attachment, "CreatorTattoo", tattoo_mesh, tattoo_material)
        tattoo.position = Vector3(0.0, 0.16, -0.065)

    var head_attachment := _bone_attachment("Head", "CreatorHeadDetails")
    if head_attachment:
        for side in [-1.0, 1.0]:
            var earring_mesh := TorusMesh.new()
            earring_mesh.inner_radius = 0.045
            earring_mesh.outer_radius = 0.014
            earring_mesh.rings = 20
            earring_mesh.ring_segments = 8
            var earring := _creator_mesh(head_attachment, "CreatorEarring", earring_mesh, metal_material)
            earring.position = Vector3(side * 0.19, 0.015, 0.085)
            earring.rotation_degrees = Vector3(90.0, 0.0, 0.0)

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
    instance.receive_shadow = true
    parent.add_child(instance)
    return instance

func _creator_material(texture: Texture2D, color: Color, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.albedo_texture = texture
    material.roughness = roughness
    material.metallic = metallic
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    return material

func _setup_animation_library() -> void:
    animation_player = AnimationPlayer.new()
    animation_player.name = "QuaterniusAnimationPlayer"
    model_root.add_child(animation_player)
    animation_player.root_node = animation_player.get_path_to(model_root)
    var library := load(ANIMATION_LIBRARY_PATH) as AnimationLibrary
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
    using_external_animation = animation_player.has_animation("body/Idle_Loop")
    if using_external_animation:
        _play_clip("Idle_Loop")
    else:
        _apply_neutral_pose()

func _library_has(library: AnimationLibrary, clip: String) -> bool:
    return library != null and library.has_animation(clip)

func _extract_animation_library_from_glb() -> AnimationLibrary:
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
    var animation_name := "body/" + clip
    if not animation_player.has_animation(animation_name):
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
    _set_bone_extra("upperarm_l", Quaternion(Vector3(0.0, 0.0, 1.0), -1.38))
    _set_bone_extra("upperarm_r", Quaternion(Vector3(0.0, 0.0, 1.0), 1.38))

func _set_bone_extra(bone_name: String, extra: Quaternion) -> void:
    if not bone_indices.has(bone_name):
        return
    var index: int = int(bone_indices[bone_name])
    var base: Quaternion = rest_rotations.get(bone_name, Quaternion.IDENTITY)
    skeleton.set_bone_pose_rotation(index, base * extra)

func _apply_procedural_fallback_pose(stride: float, crouching: bool, jumping: bool) -> void:
    if skeleton == null:
        return
    _apply_neutral_pose()
    var leg_swing := stride * 0.62
    var knee_bend := 0.54 if crouching else (0.18 if jumping else 0.0)
    _set_bone_extra("thigh_l", Quaternion(Vector3(1.0, 0.0, 0.0), leg_swing + knee_bend))
    _set_bone_extra("thigh_r", Quaternion(Vector3(1.0, 0.0, 0.0), -leg_swing + knee_bend))
    _set_bone_extra("calf_l", Quaternion(Vector3(1.0, 0.0, 0.0), maxf(0.0, stride) * 0.32 + knee_bend))
    _set_bone_extra("calf_r", Quaternion(Vector3(1.0, 0.0, 0.0), maxf(0.0, -stride) * 0.32 + knee_bend))
    _set_bone_extra("upperarm_l", Quaternion(Vector3(0.0, 0.0, 1.0), -1.38 - stride * 0.42))
    _set_bone_extra("upperarm_r", Quaternion(Vector3(0.0, 0.0, 1.0), 1.38 + stride * 0.42))

func set_motion(run_phase: float, is_running: bool, is_crouching: bool, jump_height: float, lane_velocity: float) -> void:
    motion_clock = run_phase
    var jumping := jump_height > 0.05
    var clip := "Idle_Loop"
    if jumping:
        clip = "Jump_Loop"
    elif is_crouching:
        clip = "Crouch_Fwd_Loop" if is_running else "Crouch_Idle_Loop"
    elif is_running:
        clip = "Sprint_Loop"
    if using_external_animation and animation_player.has_animation("body/" + clip):
        _play_clip(clip)
    else:
        var stride := sin(run_phase * 0.82) if is_running and not is_crouching else 0.0
        _apply_procedural_fallback_pose(stride, is_crouching, jumping)
    if runner_shadow != null:
        runner_shadow.position.y = 0.025 - position.y
        var shadow_factor := 1.0 - clampf(jump_height * 0.12, 0.0, 0.24)
        runner_shadow.scale = Vector3.ONE * shadow_factor
    if model_root != null:
        var model_lean := clampf(lane_velocity * 0.018, -0.12, 0.12)
        model_root.rotation.z = lerpf(model_root.rotation.z, -model_lean, 0.16)

func _configure_mesh_shadows(node: Node) -> void:
    for mesh in _skinned_meshes(node):
        mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
        mesh.receive_shadow = true

func _build_fallback(reason: String) -> void:
    push_warning("Humanoide Quaternius indisponível (%s); ativando fallback de diagnóstico." % reason)
    if is_instance_valid(model_root):
        model_root.free()
    model_root = null
    primary_asset_loaded = false
    var fallback_root := Node3D.new()
    fallback_root.name = "HumanAssetFallback"
    add_child(fallback_root)
    var body := MeshInstance3D.new()
    var body_mesh := CapsuleMesh.new()
    body_mesh.radius = 0.34
    body_mesh.height = 1.32
    body.mesh = body_mesh
    body.position.y = 0.98
    var body_material := StandardMaterial3D.new()
    body_material.albedo_color = Color("#c98364")
    body_material.roughness = 0.62
    body.material_override = body_material
    fallback_root.add_child(body)
    var head := MeshInstance3D.new()
    var head_mesh := SphereMesh.new()
    head_mesh.radius = 0.34
    head_mesh.height = 0.68
    head.mesh = head_mesh
    head.position.y = 1.92
    head.material_override = body_material
    fallback_root.add_child(head)
    model_root = fallback_root
    _configure_mesh_shadows(fallback_root)

func is_primary_asset_loaded() -> bool:
    return primary_asset_loaded
