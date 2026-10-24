extends Spatial
# Go 4: animated modular fighter visual. This is a jointed procedural *proxy*
# character, NOT a skinned cinematic model or a recovered MakeHuman asset.
# Separate pivot nodes permit per-limb motion without changing combat hit rules.

const HumanoidRig = preload("res://scripts/HumanoidRig.gd")
const SkinnedLimbs = preload("res://scripts/SkinnedLimbs.gd")
const SkinnedTorso = preload("res://scripts/SkinnedTorso.gd")
const SkinnedTransitions = preload("res://scripts/SkinnedTransitions.gd")
var skeletal_rig = null
const HEIGHTS = [1.86, 1.91, 1.80, 1.89, 1.91, 1.20, 1.99, 1.79, 2.05]
const ROBES = [false, true, false, false, true, true, true, true, false]
const ARMOUR = [false, false, false, false, false, false, true, false, true]
const TONES = [
    Color(0.77,0.56,0.42), Color(0.72,0.53,0.40), Color(0.82,0.62,0.47),
    Color(0.45,0.30,0.24), Color(0.76,0.57,0.43), Color(0.34,0.70,0.32),
    Color(0.12,0.12,0.16), Color(0.62,0.47,0.36), Color(0.57,0.62,0.62)]
const CLOTH = [
    Color(0.12,0.16,0.23), Color(0.28,0.18,0.15), Color(0.60,0.44,0.32),
    Color(0.26,0.23,0.40), Color(0.39,0.27,0.18), Color(0.47,0.30,0.23),
    Color(0.07,0.075,0.10), Color(0.19,0.15,0.20), Color(0.25,0.31,0.35)]

var fighter_index = 0
var body = null
var torso = null
var head = null
var left_arm = null
var right_arm = null
var left_elbow = null
var right_elbow = null
var left_leg = null
var right_leg = null
var left_knee = null
var right_knee = null
var saber = null
var cape = null
var running_clock = 0.0
var previous_pose = "idle"
var _handedness = 1.0
var breathing_clock = 0.0
# Go 14: smooth gait amplitude separately from instantaneous movement speed.
var gait_weight = 0.0
var impact_recovery = 0.0
# Go 15: transient pose envelopes. These are intentionally presentation-only;
# hit registration and invulnerability remain governed by CombatRules.
var guard_weight = 0.0
var hit_weight = 0.0
var last_hit_state = false
var last_attack_kind = "light"
# Go 16: smooth planted-foot transition and stance offsets (procedural proxies).
var left_plant_weight = 0.0
var right_plant_weight = 0.0
var left_foot = null
var right_foot = null
# Go 20: keep the rest/bind transform; animation offsets must never replace it.
var left_foot_rest = Vector3.ZERO
var right_foot_rest = Vector3.ZERO
# Go 17: bounded local stance compensation, eased out while idle/defeated.
var left_stance_offset = 0.0
var right_stance_offset = 0.0
# Go 18: animation-only upper-body inertia and locomotion transitions.
# These values never change collision, stamina, or attack timing.
var previous_motion_amount = 0.0
var motion_inertia = 0.0
var stride_cadence = 0.0
# Go 13: GPU-light procedural material detail, built once and shared per fighter.
var _surface_texture_cache = {}

# Texture masks intentionally remain grayscale so each fighter's palette can tint them.
# Fabric: broad woven ribs; skin: low-contrast mottling; metal: brushed striations.
# Avoid per-frame allocations and external assets; GLES2-friendly textures are cached.
func _surface_kind(label, metal):
    if label in ["Blade", "BladeLight"]:
        return "plain"
    if metal > 0.45:
        return "metal"
    if label in ["Face", "Jaw", "Nose", "Mouth", "Ear", "EyeWhite", "Iris", "Pupil", "Brow", "Cheek", "NasalBridge", "Chin", "BrowRidge", "Temple", "JawStubble", "Neck", "LongEar"]:
        return "skin"
    if label in ["Hair", "HairSide", "HairLock", "HairFringe"]:
        return "hair"
    if label in ["Grip", "Emitter"]:
        return "metal"
    return "fabric"

func _surface_texture(kind):
    if _surface_texture_cache.has(kind):
        return _surface_texture_cache[kind]
    var image = Image.new()
    image.create(64, 64, false, Image.FORMAT_RGBA8)
    image.lock()
    for y in range(64):
        for x in range(64):
            var grain = float((x * 67 + y * 113 + x * y * 17) % 97) / 96.0 - 0.5
            var shade = 0.93
            if kind == "fabric":
                shade = 0.91 + 0.065 * sin(float(x) * 1.57) + 0.035 * sin(float(y) * 1.57) + grain * 0.045
            elif kind == "skin":
                shade = 0.965 + grain * 0.040 + 0.010 * sin(float(x + y) * 0.31)
            elif kind == "metal":
                shade = 0.88 + 0.055 * sin(float(y) * 1.18) + grain * 0.018
            elif kind == "hair":
                shade = 0.88 + 0.085 * sin(float(x) * 1.1) + grain * 0.025
            shade = clamp(shade, 0.72, 1.0)
            image.set_pixel(x, y, Color(shade, shade, shade, 1.0))
    image.unlock()
    var tex = ImageTexture.new()
    tex.create_from_image(image, Texture.FLAG_REPEAT | Texture.FLAG_FILTER)
    _surface_texture_cache[kind] = tex
    return tex

func _material(color, metal = 0.0, glow = false, label = ""):
    var mat = SpatialMaterial.new()
    mat.albedo_color = color
    mat.metallic = metal
    var kind = _surface_kind(label, metal)
    mat.roughness = 0.75 if kind == "fabric" else (0.83 if kind == "skin" else (0.43 if kind == "hair" else 0.27))
    if not glow and kind != "plain":
        mat.albedo_texture = _surface_texture(kind)
        mat.uv1_scale = Vector3(2.5, 2.5, 1.0) if kind == "fabric" else Vector3(1.0, 1.0, 1.0)
    if glow:
        mat.emission_enabled = true
        mat.emission = color
        mat.emission_energy = 2.5
    return mat

func _block(parent, label, position, size, color, metal=0.0):
    var part = MeshInstance.new()
    part.name = label
    var mesh = CubeMesh.new()
    mesh.size = size
    part.mesh = mesh
    part.material_override = _material(color, metal, false, label)
    parent.add_child(part)
    part.translation = position
    return part

func _ball(parent, label, position, radius, color, metal=0.0):
    var part = MeshInstance.new()
    part.name = label
    var mesh = SphereMesh.new()
    mesh.radius = radius
    mesh.height = radius * 2.0
    mesh.radial_segments = 12
    mesh.rings = 6
    part.mesh = mesh
    part.material_override = _material(color, metal, false, label)
    parent.add_child(part)
    part.translation = position
    return part

# Go 9 realism pass: lightweight original modular detail, GLES2 compatible.
# Geometric materials are placeholders for future textured skinned characters.
func _taper(parent, label, position, height, top_radius, bottom_radius, color, metal=0.0):
    var part = MeshInstance.new()
    part.name = label
    var mesh = CylinderMesh.new()
    mesh.height = height
    mesh.top_radius = top_radius
    mesh.bottom_radius = bottom_radius
    mesh.radial_segments = 10
    part.mesh = mesh
    part.material_override = _material(color, metal, false, label)
    parent.add_child(part)
    part.translation = position
    return part

# Go 28: continuous sculpted head shell; replaces a spherical face on visible
# unhelmeted characters. Rings profile temples, cheekbones and tapered jaw.
# Original procedural geometry; deliberately not an actor likeness.
func _sculpted_head(parent, skin, index):
    var mesh_instance = MeshInstance.new()
    mesh_instance.name = "SculptedHeadShell"
    var mesh_tool = SurfaceTool.new()
    mesh_tool.begin(Mesh.PRIMITIVE_TRIANGLES)
    var slices = 24
    var rings = 15
    var width_scale = 1.0 + 0.04 * sin(float(index) * 2.17)
    var cheek_scale = 1.0 + 0.065 * cos(float(index) * 1.37)
    var jaw_scale = 0.90 + 0.045 * sin(float(index) * 1.81)
    var vertices = []
    for row in range(rings + 1):
        var t = float(row) / float(rings)
        var y = 0.285 - t * 0.59
        var outline = pow(max(0.0, 1.0 - pow((y + 0.005) / 0.31, 2.0)), 0.52)
        var jaw_taper = lerp(1.0, jaw_scale * 0.63, smoothstep(0.43, 0.98, t))
        var cheek_bulge = 1.0 + (cheek_scale - 1.0) * exp(-pow((t - 0.56) * 5.0, 2.0))
        for segment in range(slices + 1):
            var angle = float(segment) / float(slices) * TAU
            var x = sin(angle) * 0.288 * outline * width_scale * jaw_taper * cheek_bulge
            var z = cos(angle) * 0.254 * outline
            # The forward profile has a recessed eye socket and defined chin.
            if cos(angle) < -0.45:
                z *= 1.0 - 0.055 * exp(-pow((t - 0.37) * 10.0, 2.0))
                z -= 0.014 * exp(-pow((t - 0.89) * 10.0, 2.0))
            vertices.append(Vector3(x, y, z - 0.015))
    for row in range(rings):
        for segment in range(slices):
            var a = row * (slices + 1) + segment
            var b = a + slices + 1
            for id in [a, b, a + 1, a + 1, b, b + 1]:
                var v = vertices[id]
                mesh_tool.add_uv(Vector2(float(id % (slices + 1)) / float(slices), float(int(id / (slices + 1))) / float(rings)))
                mesh_tool.add_vertex(v)
    mesh_tool.generate_normals()
    mesh_instance.mesh = mesh_tool.commit()
    mesh_instance.material_override = _material(skin, 0.0, false, "Face")
    parent.add_child(mesh_instance)
    return mesh_instance

func _face_details(target, skin, index):
    # Eyes have sclera/iris/pupil, with simple brows, nose, ears and jaw.
    # No copyrighted face geometry or celebrity likenesses are included.
    var dark = Color(0.08, 0.08, 0.10)
    var iris = Color(0.25, 0.48, 0.56) if index % 2 == 0 else Color(0.35, 0.27, 0.16)
    _ball(target, "Jaw", Vector3(0, -0.14, -0.075), 0.205, skin.darkened(0.07))
    _taper(target, "Nose", Vector3(0, -0.055, -0.29), 0.14, 0.025, 0.067, skin.lightened(0.04))
    _block(target, "Mouth", Vector3(0, -0.175, -0.276), Vector3(0.145, 0.018, 0.012), skin.darkened(0.33))
    for side in [-1, 1]:
        _ball(target, "Ear", Vector3(side * 0.285, -0.03, 0.00), 0.074, skin)
        _ball(target, "EyeWhite", Vector3(side * 0.111, 0.047, -0.284), 0.055, Color(0.87, 0.85, 0.81))
        _ball(target, "Iris", Vector3(side * 0.111, 0.047, -0.335), 0.027, iris)
        _ball(target, "Pupil", Vector3(side * 0.111, 0.047, -0.359), 0.012, dark)
        _block(target, "Brow", Vector3(side * 0.113, 0.13, -0.278), Vector3(0.135, 0.033, 0.035), skin.darkened(0.55))
        _ball(target, "Cheek", Vector3(side * 0.19, -0.094, -0.176), 0.097, skin)

# Go 11: lightweight face proportions and layered hair; all meshes are original.
# These are deliberately low-poly preview assets, not photorealistic human scans.
func _face_shape(target, skin, index):
    var bridge = _ball(target, "NasalBridge", Vector3(0, -0.020, -0.268), 0.063, skin.lightened(0.045))
    bridge.scale = Vector3(0.74, 1.24, 0.78)
    var chin = _ball(target, "Chin", Vector3(0, -0.205, -0.177), 0.122, skin.darkened(0.025))
    chin.scale = Vector3(1.18, 0.53, 0.75)
    for side in [-1, 1]:
        var brow_ridge = _ball(target, "BrowRidge", Vector3(side * 0.126, 0.108, -0.244), 0.090, skin.darkened(0.065))
        brow_ridge.scale = Vector3(1.26, 0.48, 0.62)
        var temple = _ball(target, "Temple", Vector3(side * 0.219, 0.027, -0.073), 0.093, skin.darkened(0.035))
        temple.scale = Vector3(0.65, 1.42, 1.05)
    if index == 1 or index == 4:
        var beard = _ball(target, "JawStubble", Vector3(0, -0.173, -0.119), 0.213, skin.darkened(0.24))
        beard.scale = Vector3(0.88, 0.48, 0.79)

func _hair_layers(target, index):
    var tone = Color(0.16, 0.10, 0.07)
    if index == 1:
        tone = Color(0.70, 0.65, 0.59)
    elif index == 3:
        tone = Color(0.075, 0.065, 0.078)
    var long_hair = index == 0 or index == 1 or index == 4
    # Discrete tapered locks soften the silhouette without hair simulation.
    for side in [-1, 1]:
        for lock_index in range(3):
            var x = side * (0.19 + lock_index * 0.043)
            var length = 0.34 + (0.15 if long_hair else 0.0) - lock_index * 0.032
            var lock = _taper(target, "HairLock", Vector3(x, 0.035 - length * 0.38, 0.095), length, 0.050, 0.018, tone.lightened(lock_index * 0.038))
            lock.rotation_degrees.z = side * (8.0 + lock_index * 5.0)
    for lock_index in range(5):
        var fringe = _taper(target, "HairFringe", Vector3((lock_index - 2) * 0.087, 0.205, -0.188), 0.18, 0.065, 0.012, tone.lightened(lock_index * 0.025))
        fringe.rotation_degrees.z = 13.0 + lock_index * 4.0

func _costume_details(target, outfit, armored):
    var trim = outfit.lightened(0.25)
    # Diagonal-looking front panels at this small distance are inexpensive
    # independent mesh pieces and do not require imported texture resources.
    for side in [-1, 1]:
        _block(target, "Seam", Vector3(side * 0.31, 0.33, -0.218), Vector3(0.027, 0.60, 0.024), trim)
        _block(target, "ShoulderPlate", Vector3(side * 0.44, 0.55, 0), Vector3(0.23, 0.13, 0.46), trim, 0.6 if armored else 0.0)
    _block(target, "Collar", Vector3(0, 0.62, -0.10), Vector3(0.53, 0.10, 0.22), outfit.darkened(0.33))
    _block(target, "BeltPouch", Vector3(0.38, 0.02, -0.23), Vector3(0.14, 0.18, 0.12), outfit.darkened(0.42))

# Go 12: original layered costume geometry and anatomy accents, designed for GLES2.
# All accents use the same articulated parents as the base body so they follow poses.
func _anatomy_and_garments(target, outfit, skin, armored, index):
    var lining = outfit.darkened(0.24)
    var edge = outfit.lightened(0.16)
    # Shoulder-to-waist taper plus chest-depth anatomy: move with torso pivot.
    var chest_underlay = _ball(target, "UpperChestContour", Vector3(0, 0.43, -0.12), 0.31, lining)
    chest_underlay.scale = Vector3(1.42, 0.61, 0.60)
    var waist_contour = _ball(target, "WaistContour", Vector3(0, 0.02, 0.015), 0.24, lining)
    waist_contour.scale = Vector3(1.24, 0.62, 0.79)
    # Layered tunic fronts and stitched edges are distinct from the belt.
    for side in [-1, 1]:
        var fabric_panel = _block(target, "LayeredTunicPanel", Vector3(side * 0.16, 0.20, -0.272), Vector3(0.27, 0.68, 0.035), outfit.lightened(0.055))
        fabric_panel.rotation_degrees.z = side * 6.0
        var binding = _block(target, "TunicBinding", Vector3(side * 0.305, 0.19, -0.302), Vector3(0.027, 0.70, 0.018), edge)
        binding.rotation_degrees.z = side * 6.0
        _block(target, "BeltStrap", Vector3(side * 0.21, 0.045, -0.275), Vector3(0.095, 0.14, 0.028), lining)
        if armored:
            _taper(target, "BreastplateInset", Vector3(side * 0.22, 0.43, -0.255), 0.46, 0.19, 0.145, edge, 0.66)
    if index == 5:
        _block(target, "ShortTunicHem", Vector3(0, -0.35, 0.035), Vector3(0.61, 0.16, 0.48), edge)

func _joint_costume_detail(shoulder, elbow, hip, knee, foot, outfit, armored):
    var seam = outfit.darkened(0.28)
    # These meshes are parented to moving joints rather than the scene root.
    _ball(shoulder, "DeltoidContour", Vector3(0, -0.065, -0.023), 0.17, outfit.lightened(0.08))
    _taper(elbow, "WristCuff", Vector3(0, -0.395, 0), 0.13, 0.114, 0.105, seam, 0.36 if armored else 0.0)
    _taper(hip, "UpperThighLayer", Vector3(0, -0.16, -0.015), 0.29, 0.19, 0.157, outfit.lightened(0.055))
    _taper(knee, "KneeGuard", Vector3(0, -0.035, -0.111), 0.18, 0.111, 0.102, outfit.lightened(0.20), 0.58 if armored else 0.0)
    _block(foot, "BootToeCap", Vector3(0, -0.012, -0.16), Vector3(0.275, 0.115, 0.19), Color(0.10, 0.095, 0.092), 0.12)

func _pivot(parent, label, position):
    var node = Spatial.new()
    node.name = label
    parent.add_child(node)
    node.translation = position
    return node

func _limb(parent, side, is_arm, fabric, skin, armor):
    var side_label = "Left" if side < 0 else "Right"
    if is_arm:
        var shoulder = _pivot(parent, side_label + "Arm", Vector3(side * 0.49, 1.53, 0))
        _ball(shoulder, "Shoulder", Vector3.ZERO, 0.17, fabric)
        _taper(shoulder, "UpperArm", Vector3(0, -0.25, 0), 0.48, 0.155, 0.118, fabric, 0.25 if armor else 0.0)
        var elbow = _pivot(shoulder, "Elbow", Vector3(0, -0.51, 0))
        _ball(elbow, "Joint", Vector3.ZERO, 0.13, fabric)
        _taper(elbow, "Forearm", Vector3(0, -0.22, 0), 0.44, 0.124, 0.092, fabric)
        _ball(elbow, "Glove", Vector3(0, -0.49, 0), 0.11, skin if not armor else Color(0.16,0.16,0.19))
        return [shoulder, elbow]
    var hip = _pivot(parent, side_label + "Leg", Vector3(side * 0.20, 0.96, 0))
    _taper(hip, "Thigh", Vector3(0, -0.25, 0), 0.50, 0.18, 0.12, fabric)
    var knee = _pivot(hip, "Knee", Vector3(0, -0.52, 0))
    _ball(knee, "Joint", Vector3.ZERO, 0.12, fabric)
    _taper(knee, "Shin", Vector3(0, -0.22, 0), 0.45, 0.126, 0.085, fabric, 0.2 if armor else 0.0)
    var boot = _pivot(knee, "Foot", Vector3(0, -0.48, -0.08))
    _block(boot, "Boot", Vector3.ZERO, Vector3(0.28, 0.15, 0.45), Color(0.075,0.074,0.076))
    return [hip, knee]

func configure(index, blade_color):
    fighter_index = int(clamp(index, 0, HEIGHTS.size()-1))
    var outfit = CLOTH[fighter_index]
    var skin = TONES[fighter_index]
    var armored = ARMOUR[fighter_index]
    # Standard rig is 1.9m. Characters have distinct height and silhouette.
    var s = HEIGHTS[fighter_index] / 2.10
    scale = Vector3(s, s, s)
    body = _pivot(self, "Model", Vector3.ZERO)
    torso = _pivot(body, "Torso", Vector3(0, 0.98, 0))
    _taper(torso, "Chest", Vector3(0, 0.35, 0), 0.75, 0.48, 0.35, outfit, 0.2 if armored else 0.0)
    _block(torso, "Waist", Vector3(0, 0.00, 0), Vector3(0.64, 0.24, 0.40), outfit.darkened(0.15))
    _block(torso, "Belt", Vector3(0, 0.06, -0.21), Vector3(0.67, 0.13, 0.08), Color(0.22,0.19,0.14))
    _block(torso, "Buckle", Vector3(0, 0.07, -0.26), Vector3(0.16, 0.12, 0.04), Color(0.72,0.62,0.38), 0.7)
    _costume_details(torso, outfit, armored)
    _anatomy_and_garments(torso, outfit, skin, armored, fighter_index)
    for side in [-1, 1]:
        _block(torso, "FrontTabard", Vector3(side * 0.28, -0.35, -0.15), Vector3(0.22, 0.60, 0.11), outfit.lightened(0.14))
    _ball(torso, "Neck", Vector3(0, 0.66, 0), 0.13, skin)
    head = _pivot(torso, "Head", Vector3(0, 0.82, 0))
    if fighter_index == 6 or fighter_index == 8:
        _ball(head, "Face", Vector3(0, 0, -0.015), 0.30, skin, 0.55)
    else:
        _sculpted_head(head, skin, fighter_index)
    if fighter_index == 6 or fighter_index == 8:
        _block(head, "Helmet", Vector3(0, 0.15, 0), Vector3(0.57,0.34,0.53), outfit.lightened(0.14), 0.65)
        _block(head, "Visor", Vector3(0,0.025,-0.285), Vector3(0.46,0.13,0.06), Color(0.12,0.14,0.19), 0.7)
    elif fighter_index == 7:
        _block(head, "Hood", Vector3(0,0.16,0.1), Vector3(0.68,0.4,0.52), outfit)
    else:
        _face_details(head, skin, fighter_index)
        _face_shape(head, skin, fighter_index)
        _ball(head, "Hair", Vector3(0,0.17,0.06),0.30,Color(0.16,0.10,0.07) if fighter_index != 1 else Color(0.70,0.65,0.59))
        for side in [-1,1]:
            _block(head, "HairSide", Vector3(side*0.275, 0.005, 0.055), Vector3(0.105, 0.34, 0.29), Color(0.16,0.10,0.07) if fighter_index != 1 else Color(0.70,0.65,0.59))
        _hair_layers(head, fighter_index)
    if fighter_index == 5:
        for side in [-1,1]:
            _ball(head, "LongEar", Vector3(side*0.33,0.01,0),0.16,skin)
    var limbs = _limb(body, -1, true, outfit, skin, armored)
    left_arm = limbs[0]
    left_elbow = limbs[1]
    limbs = _limb(body, 1, true, outfit, skin, armored)
    right_arm = limbs[0]
    right_elbow = limbs[1]
    limbs = _limb(body, -1, false, outfit, skin, armored)
    left_leg = limbs[0]
    left_knee = limbs[1]
    left_foot = left_knee.get_node("Foot")
    limbs = _limb(body, 1, false, outfit, skin, armored)
    right_leg = limbs[0]
    right_knee = limbs[1]
    right_foot = right_knee.get_node("Foot")
    left_foot_rest = left_foot.translation
    right_foot_rest = right_foot.translation
    _joint_costume_detail(left_arm, left_elbow, left_leg, left_knee, left_foot, outfit, armored)
    _joint_costume_detail(right_arm, right_elbow, right_leg, right_knee, right_foot, outfit, armored)
    # Child of the RIGHT HAND, not a free-floating weapon at the root.
    var wrist = _pivot(right_elbow, "Wrist", Vector3(0, -0.50, 0))
    saber = _pivot(wrist, "Saber", Vector3(0,0.02,-0.02))
    _block(saber, "Grip", Vector3.ZERO, Vector3(0.11,0.38,0.11), Color(0.25,0.25,0.28),0.8)
    _block(saber, "Emitter", Vector3(0,0.23,0), Vector3(0.16,0.08,0.15), Color(0.62,0.64,0.68),0.8)
    var blade = _block(saber, "Blade", Vector3(0,0.84,0), Vector3(0.075,1.16,0.075), blade_color)
    blade.material_override = _material(blade_color,0.0,true)
    var light = OmniLight.new()
    light.name = "BladeLight"
    light.light_color = blade_color
    light.light_energy = 0.65
    light.omni_range = 2.0
    light.translation = Vector3(0,0.75,0)
    saber.add_child(light)
    if ROBES[fighter_index]:
        cape = _pivot(torso, "Cape", Vector3(0,0.62,0.23))
        _block(cape, "Drape", Vector3(0,-0.67,0.03), Vector3(0.96,1.38,0.12),outfit.darkened(0.12))
    if fighter_index == 8:
        # Distinctive cybernetic silhouette, still a proxy for final art.
        for side in [-1,1]:
            _block(torso,"CyborgPauldron",Vector3(side*0.60,0.49,0),Vector3(0.37,0.17,0.50),Color(0.64,0.67,0.64),0.8)
    # Keep a true Godot Skeleton synchronized with the procedural visuals.
    # A weighted mesh can be attached in a later asset-integration pass.
    skeletal_rig = HumanoidRig.new()
    skeletal_rig.name = "HumanoidSkeleton"
    body.add_child(skeletal_rig)
    # HumanoidRig._ready() builds bones when added to the active scene.
    # Do not build twice; duplicate bone names corrupt skinning resources.
    # MeshInstance is a child of Skeleton; Godot 3 skins weighted vertices
    # against that skeleton while the older jointed costume remains as fallback.
    var skinned_limbs = SkinnedLimbs.new()
    skinned_limbs.name = "WeightedSleevesAndTrousers"
    skeletal_rig.add_child(skinned_limbs)
    # Go 23: torso garment deforms with the skeleton's hips and spine.
    var skinned_torso = SkinnedTorso.new()
    skinned_torso.name = "WeightedTorsoGarment"
    skeletal_rig.add_child(skinned_torso)
    if skinned_torso.create_for_skeleton(skeletal_rig, outfit):
        # Hide only the coarse body base; collars/straps and other details stay.
        for piece in torso.get_children():
            if piece is MeshInstance and piece.name in ["Torso", "Chest", "Waist", "Body"]:
                piece.visible = false
    # Go 25: soften the costume junctions with continuously weighted bridges.
    var transitions = SkinnedTransitions.new()
    transitions.name = "WeightedShoulderHipTransitions"
    skeletal_rig.add_child(transitions)
    if not transitions.create_for_skeleton(skeletal_rig, outfit):
        transitions.queue_free()
    if skinned_limbs.create_for_skeleton(skeletal_rig, outfit):
        for pivot in [left_arm, right_arm, left_elbow, right_elbow, left_leg, right_leg, left_knee, right_knee]:
            for piece in pivot.get_children():
                if piece is MeshInstance and piece.name in ["UpperArm", "Forearm", "Thigh", "Shin"]:
                    piece.visible = false
    animate_pose(0.0,0.0,"idle","light",0.0,false,false,false,false)

func weapon():
    return saber

func animate_pose(delta, speed, attack_phase, attack_kind, progress, guarding, dodging, staggered, defeated):
    if body == null:
        return
    var amount = clamp(speed / 5.0, 0.0, 1.0)
    # Blend starts and stops instead of snapping feet to an arbitrary cycle.
    var gait_blend = 1.0 - exp(-max(delta, 0.0) * 7.0)
    gait_weight = lerp(gait_weight, amount, gait_blend)
    # Freeze idle leg phase while standing; reduces perpetual foot shuffling.
    # Faster movement increases cadence without abruptly changing the cycle.
    var cadence_target = 3.2 + 5.8 * gait_weight
    var cadence_alpha = 1.0 - exp(-max(delta, 0.0) * 5.0)
    stride_cadence = lerp(stride_cadence, cadence_target, cadence_alpha)
    running_clock += delta * stride_cadence * gait_weight
    # Lean briefly into acceleration and back during braking. Damped to avoid
    # sudden torso snaps when a controller stick returns to center.
    var acceleration = (amount - previous_motion_amount) / max(delta, 0.016)
    motion_inertia = lerp(motion_inertia, clamp(acceleration * 1.7, -8.0, 8.0), 1.0 - exp(-max(delta, 0.0) * 6.0))
    previous_motion_amount = amount
    breathing_clock += delta * 1.7
    var stride = sin(running_clock) * gait_weight
    var plant = max(0.0, sin(running_clock)) * gait_weight
    var anti_plant = max(0.0, -sin(running_clock)) * gait_weight
    var idle_breath = sin(breathing_clock)
    var blend = 1.0 - exp(-delta * 12.0)
    if delta <= 0.0:
        blend = 1.0
    var attack = attack_phase != "idle"
    var envelope_blend = 1.0 - exp(-max(delta, 0.0) * 14.0)
    if delta <= 0.0:
        envelope_blend = 1.0
    guard_weight = lerp(guard_weight, 1.0 if guarding and not defeated else 0.0, envelope_blend)
    # A new stun produces a short upper-body recoil, then naturally settles.
    if staggered and not last_hit_state:
        hit_weight = 1.0
    last_hit_state = staggered
    hit_weight = max(0.0, hit_weight - max(delta, 0.0) * 2.2)
    if defeated:
        hit_weight = 0.0
    var blade_swing = 0.0
    var shoulder_swing = 0.0
    if attack:
        if attack_phase == "windup":
            var ease_in = progress * progress * (3.0 - 2.0 * progress)
            blade_swing = -60.0 * ease_in
            shoulder_swing = -43.0 * ease_in
        elif attack_phase == "active":
            # Fast middle contact, softened endpoints (no abrupt hinge snap).
            var contact = progress * progress * (3.0 - 2.0 * progress)
            blade_swing = -60.0 + 145.0 * contact
            shoulder_swing = -43.0 + 95.0 * contact
        elif attack_phase == "recovery":
            var settle = 1.0 - progress * progress * (3.0 - 2.0 * progress)
            blade_swing = 85.0 * settle
            shoulder_swing = 52.0 * settle
        if attack_kind == "heavy":
            blade_swing *= 1.2
            shoulder_swing *= 1.16
    var guard_raise = 29.0 * guard_weight
    var stagger_tilt = -12.0 * hit_weight if not defeated else 0.0
    var dodge_tilt = -21.0 if dodging else 0.0
    torso.rotation_degrees.z = lerp(torso.rotation_degrees.z,stagger_tilt + dodge_tilt + (6.0*stride if not attack else -8.0),blend)
    var combat_twist = 0.0
    if attack:
        combat_twist = -20.0 if attack_kind == "heavy" else 13.0
    var twist_target = combat_twist * (0.35 + 0.65 * progress) if attack else 2.5 * stride
    twist_target += 7.0 * hit_weight
    torso.rotation_degrees.y = lerp(torso.rotation_degrees.y, twist_target, blend)
    # A small sagittal lean connects the upper body to starts and stops.
    # Heavy weapon swings retain precedence over locomotion inertia.
    var locomotion_lean = (-motion_inertia * 0.65 - 3.0 * gait_weight) if not (attack or defeated) else 0.0
    # The head counter-turns to keep attention near the opponent during swings.
    head.rotation_degrees.y = lerp(head.rotation_degrees.y, -torso.rotation_degrees.y * 0.57,blend)
    head.rotation_degrees.z = lerp(head.rotation_degrees.z, -torso.rotation_degrees.z * 0.22, blend)
    # Low-frequency breathing at rest, restrained two-step bounce at speed.
    var step_bob = (1.0 - cos(2.0 * running_clock)) * 0.018 * gait_weight
    body.translation.y = lerp(body.translation.y, 0.018 * idle_breath * (1.0-gait_weight) + step_bob, blend)
    left_leg.rotation_degrees.x = lerp(left_leg.rotation_degrees.x, -30.0*stride if not defeated else 0.0,blend)
    right_leg.rotation_degrees.x = lerp(right_leg.rotation_degrees.x, 30.0*stride if not defeated else 0.0,blend)
    # Smoothed alternating stance: the planted foot keeps near-neutral pitch,
    # while the swing foot lifts on the second half of the cycle.
    var stance_blend = 1.0 - exp(-max(delta, 0.0) * 10.0)
    left_plant_weight = lerp(left_plant_weight, clamp(0.5 + 0.5 * sin(running_clock), 0.0, 1.0) * gait_weight, stance_blend)
    right_plant_weight = lerp(right_plant_weight, clamp(0.5 - 0.5 * sin(running_clock), 0.0, 1.0) * gait_weight, stance_blend)
    var left_swing = max(0.0, -sin(running_clock)) * gait_weight
    var right_swing = max(0.0, sin(running_clock)) * gait_weight
    left_knee.rotation_degrees.x = lerp(left_knee.rotation_degrees.x, 9.0 * gait_weight + 30.0 * left_swing, blend)
    right_knee.rotation_degrees.x = lerp(right_knee.rotation_degrees.x, 9.0 * gait_weight + 30.0 * right_swing, blend)
    # Local translation lifts a swing foot without moving the combat collider.
    left_foot.translation.y = lerp(left_foot.translation.y, left_foot_rest.y + 0.075 * left_swing, blend)
    right_foot.translation.y = lerp(right_foot.translation.y, right_foot_rest.y + 0.075 * right_swing, blend)
    # When each foot is in its support phase, move its visual pivot backward
    # relative to the character's travel; return it forward during swing.
    # This is a cheap, bounded visual approximation, not true world-space IK.
    var travel = clamp(speed / 5.0, 0.0, 1.0)
    var phase_sine = sin(running_clock)
    var left_target = -0.105 * travel * max(0.0, phase_sine)
    var right_target = -0.105 * travel * max(0.0, -phase_sine)
    if defeated or dodging:
        left_target = 0.0
        right_target = 0.0
    var contact_blend = 1.0 - exp(-max(delta, 0.0) * 12.0)
    if delta <= 0.0:
        contact_blend = 1.0
    left_stance_offset = lerp(left_stance_offset, left_target, contact_blend)
    right_stance_offset = lerp(right_stance_offset, right_target, contact_blend)
    left_foot.translation.z = left_foot_rest.z + left_stance_offset
    right_foot.translation.z = right_foot_rest.z + right_stance_offset
    # Contact-aware toe pitch reduces visibly sliding planted feet.
    var left_pitch = -left_leg.rotation_degrees.x * 0.40 - left_knee.rotation_degrees.x * 0.55
    var right_pitch = -right_leg.rotation_degrees.x * 0.40 - right_knee.rotation_degrees.x * 0.55
    left_foot.rotation_degrees.x = lerp(left_foot.rotation_degrees.x, lerp(left_pitch, 0.0, left_plant_weight), blend)
    right_foot.rotation_degrees.x = lerp(right_foot.rotation_degrees.x, lerp(right_pitch, 0.0, right_plant_weight), blend)
    left_arm.rotation_degrees.x = lerp(left_arm.rotation_degrees.x, 18.0-12.0*stride+guard_raise,blend)
    left_arm.rotation_degrees.z = lerp(left_arm.rotation_degrees.z, -3.0 - 14.0 * guard_weight - 8.0 * hit_weight, blend)
    right_arm.rotation_degrees.x = lerp(right_arm.rotation_degrees.x, 45.0+10.0*stride+guard_raise+shoulder_swing-18.0*hit_weight,blend)
    right_arm.rotation_degrees.z = lerp(right_arm.rotation_degrees.z, 3.0 + 9.0 * guard_weight, blend)
    left_elbow.rotation_degrees.x = lerp(left_elbow.rotation_degrees.x,-9.0 - 19.0 * guard_weight,blend)
    right_elbow.rotation_degrees.x = lerp(right_elbow.rotation_degrees.x,-16.0 - 12.0 * guard_weight,blend)
    saber.rotation_degrees.z = lerp(saber.rotation_degrees.z,blade_swing,blend)
    if cape != null:
        # Cloth proxy lags behind locomotion; not a physics simulation.
        cape.rotation_degrees.x = lerp(cape.rotation_degrees.x, 5.0 + 11.0 * gait_weight + 3.5 * stride, 1.0-exp(-max(delta, 0.0)*4.0))
    # Defeat is a visibly separate state. A later go will replace proxies with
    # proper skeletal assets and timed, authored animations.
    if defeated:
        torso.rotation_degrees.x = lerp(torso.rotation_degrees.x, 66.0,blend)
        right_arm.rotation_degrees.x = lerp(right_arm.rotation_degrees.x,-25.0,blend)
    else:
        torso.rotation_degrees.x = lerp(torso.rotation_degrees.x, locomotion_lean, blend)
    if skeletal_rig != null:
        skeletal_rig.update_from_pivots({
            "spine": torso, "head": head,
            "upper_arm.L": left_arm, "lower_arm.L": left_elbow,
            "upper_arm.R": right_arm, "lower_arm.R": right_elbow,
            "upper_leg.L": left_leg, "lower_leg.L": left_knee,
            "foot.L": left_foot, "upper_leg.R": right_leg,
            "lower_leg.R": right_knee, "foot.R": right_foot
        })
    previous_pose = attack_phase
