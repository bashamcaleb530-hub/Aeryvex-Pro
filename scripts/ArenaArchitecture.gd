extends Spatial
# Go 31: modular architectural art pass. Pure visual nodes, no collision or gameplay changes.
# Reused materials and primitive meshes keep this suitable for modest GLES2 hardware.
var stone = SpatialMaterial.new()
var pale = SpatialMaterial.new()
var dark = SpatialMaterial.new()
var gold = SpatialMaterial.new()
var blue = SpatialMaterial.new()

func _mat(color, metal=0.0, rough=0.75):
    var m = SpatialMaterial.new()
    m.albedo_color = color
    m.metallic = metal
    m.roughness = rough
    return m

func _block(pos, scale, mat):
    var n = MeshInstance.new()
    var mesh = CubeMesh.new()
    mesh.size = scale
    n.mesh = mesh
    n.material_override = mat
    n.translation = pos
    add_child(n)
    return n

func _cylinder(pos, radius, height, mat, sides=12):
    var n = MeshInstance.new()
    var mesh = CylinderMesh.new()
    mesh.top_radius = radius
    mesh.bottom_radius = radius
    mesh.height = height
    mesh.radial_segments = sides
    n.mesh = mesh
    n.material_override = mat
    n.translation = pos
    add_child(n)
    return n

func _ready():
    stone = _mat(Color(0.37, 0.40, 0.47), 0.02, 0.72)
    pale = _mat(Color(0.72, 0.73, 0.68), 0.05, 0.49)
    dark = _mat(Color(0.095, 0.13, 0.21), 0.12, 0.48)
    gold = _mat(Color(0.48, 0.35, 0.18), 0.6, 0.33)
    blue = _mat(Color(0.18, 0.44, 0.65), 0.35, 0.27)
    # Center circular inlay: flush with floor so fighters are not elevated.
    _cylinder(Vector3(0, 0.017, 0), 5.2, 0.024, dark, 48)
    _cylinder(Vector3(0, 0.035, 0), 4.86, 0.024, gold, 48)
    _cylinder(Vector3(0, 0.047, 0), 4.68, 0.024, stone, 48)
    _cylinder(Vector3(0, 0.063, 0), 1.55, 0.018, blue, 32)
    _cylinder(Vector3(0, 0.075, 0), 1.39, 0.015, dark, 32)
    # Eight temple pillars well outside the middle fighting circle.
    for i in range(8):
        var angle = float(i) * PI / 4.0 + PI / 8.0
        var x = cos(angle) * 11.8
        var z = sin(angle) * 11.8
        _block(Vector3(x, 0.22, z), Vector3(2.3, 0.45, 2.3), dark)
        _block(Vector3(x, 0.53, z), Vector3(1.95, 0.25, 1.95), gold)
        _cylinder(Vector3(x, 2.6, z), 0.66, 3.9, pale, 16)
        _cylinder(Vector3(x, 4.53, z), 0.86, 0.30, gold, 16)
        _block(Vector3(x, 4.81, z), Vector3(2.1, 0.33, 2.1), pale)
    # Perimeter is visual-only, kept outside the 13-unit player arena boundary.
    for i in range(-3, 4):
        var p = float(i) * 4.0
        _block(Vector3(p, 2.0, -15.1), Vector3(3.78, 4.0, 0.38), dark)
        _block(Vector3(p, 2.0, 15.1), Vector3(3.78, 4.0, 0.38), dark)
        _block(Vector3(-15.1, 2.0, p), Vector3(0.38, 4.0, 3.78), dark)
        _block(Vector3(15.1, 2.0, p), Vector3(0.38, 4.0, 3.78), dark)
        # Vertical decorative slits and lower skirting.
        for side in [-1.0, 1.0]:
            _block(Vector3(p, 1.92, side * 14.82), Vector3(0.14, 2.75, 0.07), blue)
            _block(Vector3(side * 14.82, 1.92, p), Vector3(0.07, 2.75, 0.14), blue)
    for side in [-1.0, 1.0]:
        _block(Vector3(0, 3.93, side * 15.0), Vector3(30.0, 0.22, 0.7), gold)
        _block(Vector3(side * 15.0, 3.93, 0), Vector3(0.7, 0.22, 30.0), gold)
    # Four elevated architectural accents, decorative rather than collidable.
    for x in [-8.0, 8.0]:
        for z in [-8.0, 8.0]:
            _block(Vector3(x, 0.10, z), Vector3(2.2, 0.19, 2.2), gold)
            _block(Vector3(x, 0.20, z), Vector3(1.6, 0.14, 1.6), pale)

    # Architectural bands and wall relief remain noncolliding and outside the playable ring.
    for side in [-1.0, 1.0]:
        for height in [0.38, 3.6]:
            _block(Vector3(0, height, side * 14.74), Vector3(29.0, 0.12, 0.10), pale)
            _block(Vector3(side * 14.74, height, 0), Vector3(0.10, 0.12, 29.0), pale)
    for i in range(12):
        var angle = float(i) * PI / 6.0
        var r = 8.8
        _cylinder(Vector3(cos(angle)*r, 0.024, sin(angle)*r), 0.16, 0.028, gold, 8)
