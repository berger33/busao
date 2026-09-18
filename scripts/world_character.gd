extends Node3D
## NPC humano 3D usado pelos obstáculos de calçada.
##
## Pedestres não são mais cabeças/cápsulas isoladas: cada ocorrência instancia
## o mesmo humanoide Quaternius skinned do corredor, com corpo, rosto, olhos,
## cabelo, roupa PBR e esqueleto real. O modo de mundo desliga a AnimationLibrary
## pesada para manter muitos NPCs leves, mas mantém o asset humano completo.

const RUNNER_CHARACTER_SCRIPT = preload("res://scripts/runner_character.gd")
const TEXTURE_PHONE = preload("res://assets/textures/vidro_azul.svg")

var profile_id: String = "maria"
var role: String = "pedestrian"
var avatar_scale: float = 0.82
var avatar: Node3D
var idle_time := 0.0
var phone_attachment: BoneAttachment3D

func configure(next_profile: String, next_role: String, next_scale: float = 0.82) -> void:
    profile_id = next_profile
    role = next_role
    avatar_scale = next_scale

func _ready() -> void:
    avatar = RUNNER_CHARACTER_SCRIPT.new() as Node3D
    avatar.name = "HumanPedestrian3D"
    avatar.set("character_id", profile_id)
    avatar.call("set_world_mode", true)
    avatar.scale = Vector3.ONE * avatar_scale
    add_child(avatar)
    call_deferred("_attach_role_details")

func _process(delta: float) -> void:
    if avatar == null:
        return
    idle_time += delta
    var idle_bob := sin(idle_time * 2.0 + float(get_instance_id() % 17)) * 0.008
    avatar.position.y = idle_bob
    avatar.rotation.y = sin(idle_time * 0.72) * 0.012
    if phone_attachment:
        phone_attachment.rotation.z = sin(idle_time * 1.7) * 0.04

func _attach_role_details() -> void:
    if avatar == null or role != "old_lady":
        return
    var skeleton := avatar.get("skeleton") as Skeleton3D
    if skeleton == null or skeleton.find_bone("hand_r") < 0:
        return
    phone_attachment = BoneAttachment3D.new()
    phone_attachment.name = "PedestrianPhoneAttachment"
    phone_attachment.bone_name = "hand_r"
    skeleton.add_child(phone_attachment)
    var phone := MeshInstance3D.new()
    phone.name = "PedestrianPhone3D"
    var phone_mesh := BoxMesh.new()
    phone_mesh.size = Vector3(0.10, 0.20, 0.026)
    phone.mesh = phone_mesh
    var phone_material := StandardMaterial3D.new()
    phone_material.albedo_color = Color("#263d57")
    phone_material.albedo_texture = TEXTURE_PHONE
    phone_material.metallic = 0.35
    phone_material.roughness = 0.28
    phone.material_override = phone_material
    phone.position = Vector3(0.07, 0.11, -0.055)
    phone.rotation_degrees = Vector3(10.0, 0.0, -8.0)
    phone_attachment.add_child(phone)
