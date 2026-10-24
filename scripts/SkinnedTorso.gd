extends MeshInstance
# Go 23: continuous torso garment with weights blended between hips and spine.
# This is a lightweight skinned costume shell, not a realistic anatomical scan.
const SIDES = 16

func create_for_skeleton(rig, tint):
    var hip = rig.find_bone("hips")
    var spine = rig.find_bone("spine")
    var head = rig.find_bone("head")
    var left_shoulder = rig.find_bone("upper_arm.L")
    var right_shoulder = rig.find_bone("upper_arm.R")
    if hip < 0 or spine < 0 or head < 0 or left_shoulder < 0 or right_shoulder < 0:
        return false
    var verts = PoolVector3Array()
    var norms = PoolVector3Array()
    var uv = PoolVector2Array()
    var bone_ids = PoolIntArray()
    var weights = PoolRealArray()
    var faces = PoolIntArray()
    # Waist, rib cage, upper chest, shoulder line and neck collar.
    # Four normalized influences per vertex soften shoulder/neck articulation.
    # Spine weights increase with height to allow bending through the torso.
    var rings = [
        [0.94, 0.31, 0.215, 0.10],
        [1.13, 0.35, 0.235, 0.34],
        [1.32, 0.41, 0.25, 0.66],
        [1.48, 0.46, 0.24, 0.87],
        [1.57, 0.32, 0.215, 0.96],
        [1.67, 0.18, 0.17, 1.00]
    ]
    for i in range(rings.size()):
        var section = rings[i]
        for j in range(SIDES):
            var angle = TAU * float(j) / float(SIDES)
            var cs = cos(angle)
            var sn = sin(angle)
            verts.append(Vector3(cs * section[1], section[0], sn * section[2]))
            norms.append(Vector3(cs / section[1], 0, sn / section[2]).normalized())
            uv.append(Vector2(float(j) / float(SIDES), float(i) / float(rings.size() - 1)))
            var shoulder_band = clamp((section[0] - 1.30) / 0.27, 0.0, 1.0)
            var shoulder_side = clamp((abs(cs) - 0.35) / 0.65, 0.0, 1.0)
            var shoulder_weight = shoulder_band * shoulder_side * 0.24
            var neck_weight = clamp((section[0] - 1.52) / 0.15, 0.0, 1.0) * (1.0 - shoulder_side) * 0.32
            var torso_weight = 1.0 - shoulder_weight - neck_weight
            bone_ids.append(hip)
            bone_ids.append(spine)
            bone_ids.append(left_shoulder if cs < 0.0 else right_shoulder)
            bone_ids.append(head)
            weights.append((1.0 - section[3]) * torso_weight)
            weights.append(section[3] * torso_weight)
            weights.append(shoulder_weight)
            weights.append(neck_weight)
            if i > 0:
                var previous = (i - 1) * SIDES + j
                var previous_next = (i - 1) * SIDES + (j + 1) % SIDES
                var current = i * SIDES + j
                var current_next = i * SIDES + (j + 1) % SIDES
                faces.append_array(PoolIntArray([previous, current, previous_next, previous_next, current, current_next]))
    var surface = []
    surface.resize(Mesh.ARRAY_MAX)
    surface[Mesh.ARRAY_VERTEX] = verts
    surface[Mesh.ARRAY_NORMAL] = norms
    surface[Mesh.ARRAY_TEX_UV] = uv
    surface[Mesh.ARRAY_BONES] = bone_ids
    surface[Mesh.ARRAY_WEIGHTS] = weights
    surface[Mesh.ARRAY_INDEX] = faces
    if verts.size() == 0 or bone_ids.size() != verts.size() * 4 or weights.size() != verts.size() * 4:
        return false
    var built = ArrayMesh.new()
    built.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, surface)
    mesh = built
    skeleton = NodePath("..")
    var material = SpatialMaterial.new()
    material.albedo_color = tint
    material.roughness = 0.90
    material_override = material
    return true
