extends Node
## Coloque como filho do visual da personagem. Godot 4.7.2.
## Clona as AnimationLibraries desta instancia, remove somente tracks hair.*
## e aplica SpringBoneSimulator3D apos as animacoes do corpo.

@export var skeleton: Skeleton3D
@export_range(0.0, 10.0, 0.05) var stiffness: float = 3.0
@export_range(0.0, 1.0, 0.01) var damping: float = 0.45
## SpringBone usa um parametro de velocidade, nao aceleracao m/s².
@export_range(0.0, 3.0, 0.01) var spring_gravity: float = 0.60
@export var reset_distance: float = 2.5

var simulator: SpringBoneSimulator3D
var removed_hair_tracks: int = 0
var configured: bool = false
var _last_position: Vector3
const HAIR_BONES := ['hair.01', 'hair.02', 'hair.03']
const LOOPS := ['idle', 'run_loop', 'jump_air', 'crouch_loop', 'crouch_run_loop']
const IMPORT_ALIASES := {'run': 'run_loop', 'crouch': 'crouch_loop', 'crouch_run': 'crouch_run_loop'}

func _ready() -> void:
	call_deferred('configure')

func _all_nodes(node: Node) -> Array[Node]:
	var result: Array[Node] = [node]
	for child in node.get_children():
		result.append_array(_all_nodes(child))
	return result

func configure() -> void:
	if configured:
		return
	var nodes := _all_nodes(get_parent())
	if skeleton == null:
		for node in nodes:
			if node is Skeleton3D:
				skeleton = node as Skeleton3D
				break
	if skeleton == null:
		push_error('Cabelo: Skeleton3D nao encontrado.')
		return
	for bone_name in HAIR_BONES:
		if skeleton.find_bone(bone_name) < 0:
			push_error('Cabelo: osso ausente: '+bone_name)
			return
	if not skeleton.global_basis.get_scale().is_equal_approx(Vector3.ONE):
		push_warning('Cabelo: mantenha escala 1,1,1 para a simulacao em metros.')
	for node in nodes:
		if node is AnimationPlayer:
			_prepare_animations(node as AnimationPlayer)
	for bone_name in HAIR_BONES:
		skeleton.reset_bone_pose(skeleton.find_bone(bone_name))
	simulator = SpringBoneSimulator3D.new()
	simulator.name = 'FisicaRaboDeCavalo'
	skeleton.add_child(simulator)
	simulator.setting_count = 1
	simulator.set_root_bone_name(0, HAIR_BONES[0])
	simulator.set_end_bone_name(0, HAIR_BONES[2])
	simulator.set_extend_end_bone(0, true)
	simulator.set_end_bone_length(0, 0.20224)
	# +Y local e o comprimento dos ossos exportados pelo Blender.
	simulator.set_end_bone_direction(0, SkeletonModifier3D.BONE_DIRECTION_PLUS_Y)
	simulator.set_center_from(0, SpringBoneSimulator3D.CENTER_FROM_WORLD_ORIGIN)
	simulator.set_stiffness(0, stiffness)
	simulator.set_drag(0, damping)
	simulator.set_gravity(0, spring_gravity)
	simulator.set_gravity_direction(0, Vector3.DOWN)
	simulator.set_radius(0, 0.028)
	simulator.mutable_bone_axes = false
	simulator.set_enable_all_child_collisions(0, true)
	_add_sphere('Cabeca', 'head', Vector3(0, 1.567, -0.012), 0.088)
	_add_capsule('Torax', 'chest', Vector3(0, 1.265, -0.015), 0.101, 0.332)
	_add_capsule('Costas', 'spine', Vector3(0, 1.115, -0.03), 0.084, 0.298)
	_last_position = skeleton.global_position
	configured = true
	simulator.reset()

func _prepare_animations(player: AnimationPlayer) -> void:
	for library_name in player.get_animation_library_list():
		var original: AnimationLibrary = player.get_animation_library(library_name)
		var local_library := original.duplicate(true) as AnimationLibrary
		for animation_name in local_library.get_animation_list():
			var animation: Animation = local_library.get_animation(animation_name)
			var canonical: String = IMPORT_ALIASES.get(String(animation_name), String(animation_name))
			for track in range(animation.get_track_count()-1, -1, -1):
				var path: NodePath = animation.track_get_path(track)
				for part in range(path.get_subname_count()):
					if String(path.get_subname(part)) in HAIR_BONES:
						animation.remove_track(track)
						removed_hair_tracks += 1
						break
			animation.loop_mode = Animation.LOOP_LINEAR if canonical in LOOPS else Animation.LOOP_NONE
			if canonical != String(animation_name) and not local_library.has_animation(canonical):
				local_library.remove_animation(animation_name)
				local_library.add_animation(canonical, animation)
		player.remove_animation_library(library_name)
		player.add_animation_library(library_name, local_library)

func _bone_offset(bone_name: String, point: Vector3) -> Vector3:
	return skeleton.get_bone_global_rest(skeleton.find_bone(bone_name)).affine_inverse()*point

func _add_sphere(label: String, bone_name: String, center: Vector3, radius: float) -> void:
	var collision := SpringBoneCollisionSphere3D.new()
	collision.name = label
	simulator.add_child(collision)
	collision.bone_name = bone_name
	collision.radius = radius
	collision.position_offset = _bone_offset(bone_name, center)

func _add_capsule(label: String, bone_name: String, center: Vector3, radius: float, height: float) -> void:
	var collision := SpringBoneCollisionCapsule3D.new()
	collision.name = label
	simulator.add_child(collision)
	collision.bone_name = bone_name
	collision.radius = radius
	collision.height = height
	collision.position_offset = _bone_offset(bone_name, center)
	var rest: Transform3D = skeleton.get_bone_global_rest(skeleton.find_bone(bone_name))
	collision.rotation_offset = rest.basis.inverse().get_rotation_quaternion()

func _physics_process(_delta: float) -> void:
	if not configured:
		return
	# Teleporte/reinicio nao deve lancar a tranca como um chicote.
	if skeleton.global_position.distance_to(_last_position) > reset_distance:
		simulator.reset()
	_last_position = skeleton.global_position

func reset_after_teleport() -> void:
	if configured:
		simulator.reset()
		_last_position = skeleton.global_position
