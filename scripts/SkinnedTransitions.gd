extends MeshInstance
# Go 25: low-poly deforming fabric bridges around shoulder and upper-hip seams.
# Weights blend torso motion with upper-arm or upper-leg motion (Godot 3 format).
const RADIAL = 12

func create_for_skeleton(rig, tint):
    var spine = rig.find_bone("spine")
    var hips = rig.find_bone("hips")
    if spine < 0 or hips < 0:
        return false
    var verts = PoolVector3Array()
    var norms = PoolVector3Array()
    var uv = PoolVector2Array()
    var bone_ids = PoolIntArray()
    var weights = PoolRealArray()
    var faces = PoolIntArray()
    for side in [-1.0, 1.0]:
        var suffix = ".L" if side < 0.0 else ".R"
        var arm = rig.find_bone("upper_arm" + suffix)
        var leg = rig.find_bone("upper_leg" + suffix)
        if arm < 0 or leg < 0:
            return false
        # Shoulder-to-sleeve interface, progressing from chest to arm.
        _bridge(verts, norms, uv, bone_ids, weights, faces, [
            [Vector3(side * 0.30, 1.53, 0.0), 0.20, 0.12],
            [Vector3(side * 0.40, 1.54, 0.0), 0.18, 0.34],
            [Vector3(side * 0.49, 1.52, 0.0), 0.16, 0.78],
            [Vector3(side * 0.56, 1.48, 0.0), 0.15, 0.95]
        ], spine, arm)
        # Pelvis-to-trouser interface. Do not use a hard bone switch at the hip.
        _bridge(verts, norms, uv, bone_ids, weights, faces, [
            [Vector3(side * 0.20, 1.03, 0.0), 0.205, 0.08],
            [Vector3(side * 0.20, 0.96, 0.0), 0.194, 0.35],
            [Vector3(side * 0.20, 0.87, 0.0), 0.181, 0.78],
            [Vector3(side * 0.20, 0.79, 0.0), 0.169, 0.96]
        ], hips, leg)
    if verts.size() == 0 or bone_ids.size() != verts.size() * 4 or weights.size() != verts.size() * 4:
        return false
    var arrays = []
    arrays.resize(Mesh.ARRAY_MAX)
    arrays[Mesh.ARRAY_VERTEX] = verts
    arrays[Mesh.ARRAY_NORMAL] = norms
    arrays[Mesh.ARRAY_TEX_UV] = uv
    arrays[Mesh.ARRAY_BONES] = bone_ids
    arrays[Mesh.ARRAY_WEIGHTS] = weights
    arrays[Mesh.ARRAY_INDEX] = faces
    var surface = ArrayMesh.new()
    surface.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
    mesh = surface
    skeleton = NodePath("..")
    var fabric = SpatialMaterial.new()
    fabric.albedo_color = tint
    fabric.roughness = 0.88
    material_override = fabric
    return true

func _bridge(verts, norms, uv, bone_ids, weights, faces, rings, base_bone, moving_bone):
    var first = verts.size()
    for i in range(rings.size()):
        var ring = rings[i]
        # Use the bridge centerline as the surface axis. Shoulder bridges run
        # diagonally, so a purely horizontal radial normal gives false lighting.
        var before = rings[max(i - 1, 0)][0]
        var after = rings[min(i + 1, rings.size() - 1)][0]
        var axis = (after - before).normalized()
        if axis.length_squared() < 0.000001:
            axis = Vector3.UP
        for j in range(RADIAL):
            var theta = TAU * float(j) / float(RADIAL)
            var radial = Vector3(cos(theta), 0.0, sin(theta))
            var n = radial - axis * radial.dot(axis)
            if n.length_squared() < 0.000001:
                n = Vector3.FORWARD
            n = n.normalized()
            verts.append(ring[0] + radial * ring[1])
            norms.append(n)
            uv.append(Vector2(float(j) / float(RADIAL), float(i) / float(rings.size() - 1)))
            bone_ids.append(base_bone)
            bone_ids.append(moving_bone)
            bone_ids.append(0)
            bone_ids.append(0)
            weights.append(1.0 - ring[2])
            weights.append(ring[2])
            weights.append(0.0)
            weights.append(0.0)
        if i > 0:
            for j in range(RADIAL):
                var nxt = (j + 1) % RADIAL
                var a = first + (i - 1) * RADIAL + j
                var b = first + (i - 1) * RADIAL + nxt
                var c = first + i * RADIAL + j
                var d = first + i * RADIAL + nxt
                faces.append_array(PoolIntArray([a, b, c, b, d, c]))
