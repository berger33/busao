extends Node3D
## Animal 3D de mundo. O cachorro caramelo tem anatomia legível, materiais,
## olhos, focinho, orelhas, quatro patas, cauda articulada e coleira.

const TEXTURE_FUR = preload("res://assets/textures/pele_suave.svg")
const TEXTURE_RUBBER = preload("res://assets/textures/borracha.svg")
const TEXTURE_METAL = preload("res://assets/textures/metal_pintado.svg")

var species: String = "caramelo"
var fur_color := Color("#b8794d")
var body_root: Node3D
var tail: Node3D
var legs: Array[Node3D] = []
var motion_time := 0.0
var running := false

func configure(next_species: String = "caramelo") -> void:
    species = next_species

func _ready() -> void:
    if species == "caramelo":
        _build_caramelo()

func _process(delta: float) -> void:
    motion_time += delta
    if tail:
        tail.rotation.z = -0.72 + sin(motion_time * (8.0 if running else 3.8)) * (0.22 if running else 0.13)
    for index in legs.size():
        var leg := legs[index]
        leg.rotation.x = sin(motion_time * (10.0 if running else 2.8) + float(index) * PI) * (0.18 if running else 0.035)
    if body_root:
        body_root.position.y = sin(motion_time * (8.0 if running else 2.0)) * (0.025 if running else 0.008)

func set_running(value: bool) -> void:
    running = value

func _build_caramelo() -> void:
    body_root = Node3D.new()
    body_root.name = "CarameloDog3D"
    add_child(body_root)
    var fur := _material(fur_color, TEXTURE_FUR, 0.82)
    var face := _material(Color("#c28656"), TEXTURE_FUR, 0.84)
    var dark := _material(Color("#241b1a"), TEXTURE_RUBBER, 0.72)
    var eye := _material(Color("#10131c"), TEXTURE_RUBBER, 0.22)
    var inner_ear := _material(Color("#75412f"), TEXTURE_FUR, 0.88)
    var collar := _material(Color("#2e75a6"), TEXTURE_FUR, 0.46)
    var metal := _material(Color("#f0bd4a"), TEXTURE_METAL, 0.20, 0.82)

    _ellipsoid(body_root, Vector3(0.0, 0.56, 0.0), Vector3(0.72, 0.43, 0.50), fur, "DogBody")
    _ellipsoid(body_root, Vector3(0.40, 0.72, 0.0), Vector3(0.28, 0.30, 0.30), fur, "DogNeck")
    _ellipsoid(body_root, Vector3(0.53, 0.91, -0.04), Vector3(0.34, 0.31, 0.31), face, "DogHead")
    _ellipsoid(body_root, Vector3(0.77, 0.83, -0.20), Vector3(0.17, 0.14, 0.14), face, "DogMuzzle")
    _ellipsoid(body_root, Vector3(0.88, 0.84, -0.28), Vector3(0.07, 0.06, 0.05), dark, "DogNose")
    for side in [-1.0, 1.0]:
        _ellipsoid(body_root, Vector3(0.61, 0.99, side * 0.20), Vector3(0.055, 0.06, 0.055), eye, "DogEye")
        var ear := _ellipsoid(body_root, Vector3(0.43, 1.10, side * 0.19), Vector3(0.13, 0.22, 0.10), fur, "DogEar")
        ear.rotation.z = side * 0.18
        _ellipsoid(body_root, Vector3(0.43, 1.10, side * 0.205), Vector3(0.075, 0.14, 0.035), inner_ear, "DogEarInner")
    _torus(body_root, 0.20, 0.025, Vector3(0.40, 0.78, 0.0), collar, "DogCollar")
    _sphere(body_root, 0.065, Vector3(0.40, 0.62, -0.22), metal, "DogTag")
    for side in [-1.0, 1.0]:
        for front in [-1.0, 1.0]:
            var leg := _capsule(body_root, 0.075, 0.42, Vector3(front * 0.40, 0.27, side * 0.19), fur, "DogLeg")
            legs.append(leg)
            _ellipsoid(body_root, Vector3(front * 0.40, 0.06, side * 0.20), Vector3(0.10, 0.055, 0.12), dark, "DogPaw")
    tail = _capsule(body_root, 0.065, 0.46, Vector3(-0.67, 0.83, 0.13), fur, "DogTailBase")
    tail.rotation.z = -0.72
    var tail_tip := _ellipsoid(body_root, Vector3(-0.86, 1.00, 0.13), Vector3(0.10, 0.12, 0.10), fur, "DogTailTip")
    tail_tip.rotation.z = -0.36

func _material(color: Color, texture: Texture2D, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.albedo_texture = texture
    material.roughness = roughness
    material.metallic = metallic
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
    if texture == TEXTURE_FUR:
        material.subsurf_scatter_enabled = true
        material.subsurf_scatter_skin_mode = true
        material.subsurf_scatter_strength = 0.06
    return material

func _mesh(parent: Node3D, node_name: String, mesh: Mesh, material: Material) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.name = node_name
    node.mesh = mesh
    node.material_override = material
    node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
    parent.add_child(node)
    return node

func _ellipsoid(parent: Node3D, pos: Vector3, scale_value: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := SphereMesh.new()
    mesh.radius = 1.0
    mesh.height = 2.0
    mesh.radial_segments = 24
    mesh.rings = 14
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    node.scale = scale_value
    return node

func _sphere(parent: Node3D, radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    return _ellipsoid(parent, pos, Vector3.ONE * radius, material, node_name)

func _capsule(parent: Node3D, radius: float, height: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := CapsuleMesh.new()
    mesh.radius = radius
    mesh.height = height
    mesh.radial_segments = 16
    mesh.rings = 8
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    return node

func _torus(parent: Node3D, inner_radius: float, outer_radius: float, pos: Vector3, material: Material, node_name: String) -> MeshInstance3D:
    var mesh := TorusMesh.new()
    mesh.inner_radius = inner_radius
    mesh.outer_radius = outer_radius
    mesh.rings = 24
    mesh.ring_segments = 10
    var node := _mesh(parent, node_name, mesh, material)
    node.position = pos
    return node
