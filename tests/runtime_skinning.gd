extends SceneTree
# Go 26: validate real Godot mesh arrays and animated skeleton poses.
const Rig = preload("res://scripts/HumanoidRig.gd")
const Limbs = preload("res://scripts/SkinnedLimbs.gd")
const Torso = preload("res://scripts/SkinnedTorso.gd")
const Transitions = preload("res://scripts/SkinnedTransitions.gd")

func _init():
    call_deferred("run")

func fail_test(message):
    printerr("SKINNING FAILURE: " + message)
    quit(1)

func run():
    var rig = Rig.new()
    get_root().add_child(rig)
    if not rig.validate_rig():
        fail_test("Missing or invalid humanoid skeleton")
        return
    for source in [Limbs, Torso, Transitions]:
        var item = source.new()
        rig.add_child(item)
        if not item.create_for_skeleton(rig, Color(0.4, 0.5, 0.6)):
            fail_test("Could not construct skinned surface")
            return
        if item.mesh == null or item.mesh.get_surface_count() == 0:
            fail_test("Skinning surface missing")
            return
        for surface in range(item.mesh.get_surface_count()):
            var arrays = item.mesh.surface_get_arrays(surface)
            var verts = arrays[Mesh.ARRAY_VERTEX]
            var bones = arrays[Mesh.ARRAY_BONES]
            var weights = arrays[Mesh.ARRAY_WEIGHTS]
            var triangles = arrays[Mesh.ARRAY_INDEX]
            if verts.size() == 0 or weights.size() != verts.size() * 4 or bones.size() != weights.size():
                fail_test("Incorrect skin vertex / bone / weight layout")
                return
            if triangles.size() % 3 != 0:
                fail_test("Invalid triangle index buffer")
                return
            for vertex in range(verts.size()):
                var total = 0.0
                for influence in range(4):
                    var at = vertex * 4 + influence
                    if bones[at] < 0 or bones[at] >= rig.get_bone_count():
                        fail_test("Bone index out of range")
                        return
                    if weights[at] < -0.0001 or weights[at] > 1.0001:
                        fail_test("Skinning weight out of range")
                        return
                    total += weights[at]
                if abs(total - 1.0) > 0.001:
                    fail_test("Skinning weights do not sum to one")
                    return
            for idx in triangles:
                if idx < 0 or idx >= verts.size():
                    fail_test("Triangle index out of range")
                    return
    var shoulder = rig.find_bone("upper_arm.L")
    rig.set_bone_pose(shoulder, Transform(Basis(Vector3(0, 0, 1), 0.6), Vector3.ZERO))
    if abs(rig.get_bone_pose(shoulder).basis.get_euler().z - 0.6) > 0.01:
        fail_test("Skeleton pose rotation was not applied")
        return
    print("GO26_RUNTIME_SKINNING_PASS")
    quit(0)
