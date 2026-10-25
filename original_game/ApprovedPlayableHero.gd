extends Node3D
# Appearance safeguard. Prefer real reviewed GLB; otherwise show exact reference-art
# sprite in the world. A sprite is NOT a playable 3D character model.
const IDS := ["kai","ryker","lyra"]
var visual_kind := "missing"
var chosen_id := "kai"
func apply_hero(index: int) -> String:
    index = clampi(index,0,2)
    chosen_id = IDS[index]
    for n in get_children():
        remove_child(n)
        n.queue_free()
    var glb := "res://approved_heroes/%s.glb" % chosen_id
    if ResourceLoader.exists(glb):
        var model = load(glb)
        if model is PackedScene:
            var instance: Node3D = model.instantiate()
            add_child(instance)
            visual_kind = "approved_glb_unverified"
            return visual_kind
    var png := "res://approved_heroes/%s.png" % chosen_id
    if ResourceLoader.exists(png):
        var sprite := Sprite3D.new()
        sprite.texture = load(png)
        sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
        sprite.pixel_size = 0.006
        sprite.position.y = 1.48
        sprite.shaded = false
        sprite.double_sided = true
        add_child(sprite)
        visual_kind = "approved_2d_reference_preview"
        return visual_kind
    visual_kind = "missing"
    return visual_kind
