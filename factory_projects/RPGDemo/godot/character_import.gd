extends Node3D
## Optional external GLB presentation. Gameplay capsule stays until integration succeeds.
var imported: Node3D
var animation_player: AnimationPlayer
var status := "MISSING_APPROVED_ASSET"
func configure(path: String, approval: Dictionary, mapping: Dictionary) -> bool:
	if typeof(approval.get("approved")) != TYPE_BOOL or approval.get("approved") != true:
		status = "APPROVAL_REQUIRED"
		return false
	for key in ["license", "author", "source", "reference_sha256"]:
		if str(approval.get(key, "")).is_empty():
			status = "PROVENANCE_REQUIRED"
			return false
	if not path.begins_with("res://assets/") or not path.ends_with(".glb") or not FileAccess.file_exists(path):
		status = "STAGE_APPROVED_GLB_REQUIRED"
		return false
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		status = "GLB_IMPORT_FAILED"
		return false
	var candidate := doc.generate_scene(state)
	if candidate == null:
		status = "SCENE_IMPORT_FAILED"
		return false
	for instance in candidate.find_children("*", "MeshInstance3D", true, false):
		instance.tree_exiting.connect(func(): instance.mesh = null)
	var rigs := candidate.find_children("*", "Skeleton3D", true, false)
	var players := candidate.find_children("*", "AnimationPlayer", true, false)
	if rigs.is_empty() or players.is_empty():
		candidate.free()
		status = "RIG_AND_ANIMATIONS_REQUIRED"
		return false
	var player: AnimationPlayer = players[0]
	for action in ["idle", "walk", "run", "jump", "attack", "hit", "defeat"]:
		if not player.has_animation(str(mapping.get(action, ""))):
			candidate.free()
			status = "MISSING_MAPPED_CLIP"
			return false
	if imported != null: imported.queue_free()
	imported = candidate
	animation_player = player
	add_child(imported)
	status = "IMPORTED_REQUIRES_BINDING_SCALE_AND_VISUAL_REVIEW"
	return true
func play_clip(clip: String) -> bool:
	if animation_player == null or not animation_player.has_animation(clip): return false
	animation_player.play(clip, 0.12)
	return true
