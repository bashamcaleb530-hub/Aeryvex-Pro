from pathlib import Path
s = (Path(__file__).resolve().parents[1]/"scripts/FighterVisual.gd").read_text()
checks=["func _surface_kind(", "func _surface_texture(", "_surface_texture_cache", "Image.FORMAT_RGBA8", "image.lock()", "image.unlock()", "Texture.FLAG_REPEAT", "mat.albedo_texture = _surface_texture(kind)", "mat.roughness", "mat.uv1_scale", "_material(color, metal, false, label)", '"skin"', '"metal"', '"fabric"', '"hair"']
for token in checks: assert token in s, token
assert s.count("func _material(")==1
assert s.count("func _surface_texture(")==1
print(f"GO13: {len(checks)+2}/{len(checks)+2} checks passed")
