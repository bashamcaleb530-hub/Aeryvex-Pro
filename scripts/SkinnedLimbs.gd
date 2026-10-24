extends MeshInstance
# Go 22: bone-weighted sleeve/trouser mesh bound to Godot 3 Skeleton.
# All coordinates are skeleton-local rest-space coordinates.
# 4 bone indices and 4 weights per vertex are required by Godot 3.
const SIDES = [-1.0, 1.0]
const RADIAL = 12

func create_for_skeleton(rig, color):
    var vertices = PoolVector3Array()
    var normals = PoolVector3Array()
    var uvs = PoolVector2Array()
    var bones = PoolIntArray()
    var weights = PoolRealArray()
    var indices = PoolIntArray()
    for side in SIDES:
        var suffix = ".L" if side < 0.0 else ".R"
        var shoulder = rig.find_bone("upper_arm" + suffix)
        var elbow = rig.find_bone("lower_arm" + suffix)
        var hip = rig.find_bone("upper_leg" + suffix)
        var knee = rig.find_bone("lower_leg" + suffix)
        # Rings overlap joints: smooth weights distribute deformation over the elbow/knee.
        _tube(vertices, normals, uvs, bones, weights, indices, [
            [Vector3(side * 0.49, 1.55, 0.0), 0.163, shoulder, elbow, 1.0],
            [Vector3(side * 0.49, 1.30, 0.0), 0.147, shoulder, elbow, 0.88],
            [Vector3(side * 0.49, 1.04, 0.0), 0.125, shoulder, elbow, 0.48],
            [Vector3(side * 0.49, 0.79, 0.0), 0.119, shoulder, elbow, 0.12],
            [Vector3(side * 0.49, 0.55, 0.0), 0.101, shoulder, elbow, 0.0]
        ])
        _tube(vertices, normals, uvs, bones, weights, indices, [
            [Vector3(side * 0.20, 0.96, 0.0), 0.19, hip, knee, 1.0],
            [Vector3(side * 0.20, 0.70, 0.0), 0.171, hip, knee, 0.90],
            [Vector3(side * 0.20, 0.45, 0.0), 0.133, hip, knee, 0.52],
            [Vector3(side * 0.20, 0.21, 0.0), 0.116, hip, knee, 0.11],
            [Vector3(side * 0.20, -0.04, 0.0), 0.102, hip, knee, 0.0]
        ])
    var arrays = []
    arrays.resize(Mesh.ARRAY_MAX)
    arrays[Mesh.ARRAY_VERTEX] = vertices
    arrays[Mesh.ARRAY_NORMAL] = normals
    arrays[Mesh.ARRAY_TEX_UV] = uvs
    arrays[Mesh.ARRAY_BONES] = bones
    arrays[Mesh.ARRAY_WEIGHTS] = weights
    arrays[Mesh.ARRAY_INDEX] = indices
    var geometry = ArrayMesh.new()
    geometry.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
    mesh = geometry
    skeleton = NodePath("..")
    var surface_material = SpatialMaterial.new()
    surface_material.albedo_color = color
    surface_material.roughness = 0.86
    material_override = surface_material
    return vertices.size() > 0 and bones.size() == vertices.size() * 4 and weights.size() == vertices.size() * 4

func _tube(vertices, normals, uvs, bones, weights, indices, rings):
    var start = vertices.size()
    for i in range(rings.size()):
        var ring = rings[i]
        for j in range(RADIAL):
            var theta = TAU * float(j) / float(RADIAL)
            var normal = Vector3(cos(theta), 0.0, sin(theta))
            vertices.append(ring[0] + normal * ring[1])
            normals.append(normal)
            uvs.append(Vector2(float(j) / float(RADIAL), float(i) / float(rings.size() - 1)))
            bones.append(ring[2])
            bones.append(ring[3])
            bones.append(0)
            bones.append(0)
            weights.append(ring[4])
            weights.append(1.0 - ring[4])
            weights.append(0.0)
            weights.append(0.0)
        if i > 0:
            for j in range(RADIAL):
                var last = (j + 1) % RADIAL
                var a = start + (i - 1) * RADIAL + j
                var b = start + (i - 1) * RADIAL + last
                var c = start + i * RADIAL + j
                var d = start + i * RADIAL + last
                indices.append_array(PoolIntArray([a, b, c, b, d, c]))
