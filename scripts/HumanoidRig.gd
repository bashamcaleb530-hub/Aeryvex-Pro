extends Skeleton
# Go 21: Actual Godot 3 Skeleton bone hierarchy and pose bridge.
# It mirrors the current articulated proxy. A skinned mesh must be imported
# and bound to these bone names before the bones can deform character skin.
const BONES = [
    ["hips", "", Vector3(0, 0.98, 0)],
    ["spine", "hips", Vector3(0, 0, 0)],
    ["head", "spine", Vector3(0, 0.82, 0)],
    ["upper_arm.L", "hips", Vector3(-0.49, 0.55, 0)],
    ["lower_arm.L", "upper_arm.L", Vector3(0, -0.51, 0)],
    ["upper_arm.R", "hips", Vector3(0.49, 0.55, 0)],
    ["lower_arm.R", "upper_arm.R", Vector3(0, -0.51, 0)],
    ["upper_leg.L", "hips", Vector3(-0.20, -0.02, 0)],
    ["lower_leg.L", "upper_leg.L", Vector3(0, -0.52, 0)],
    ["foot.L", "lower_leg.L", Vector3(0, -0.48, -0.08)],
    ["upper_leg.R", "hips", Vector3(0.20, -0.02, 0)],
    ["lower_leg.R", "upper_leg.R", Vector3(0, -0.52, 0)],
    ["foot.R", "lower_leg.R", Vector3(0, -0.48, -0.08)]
]

func _ready():
    if get_bone_count() == 0:
        build_bones()

func build_bones():
    for spec in BONES:
        add_bone(spec[0])
    for spec in BONES:
        var bone = find_bone(spec[0])
        if spec[1] != "":
            set_bone_parent(bone, find_bone(spec[1]))
        set_bone_rest(bone, Transform(Basis(), spec[2]))

func update_from_pivots(pivots):
    # Real bone poses, rather than animation metadata. No collision changes.
    for bone_name in pivots.keys():
        var index = find_bone(bone_name)
        var pivot = pivots[bone_name]
        if index >= 0 and is_instance_valid(pivot):
            set_bone_pose(index, Transform(Basis(pivot.rotation), Vector3.ZERO))

func validate_rig():
    if get_bone_count() != BONES.size():
        return false
    for spec in BONES:
        if find_bone(spec[0]) < 0:
            return false
    return true
