#!/usr/bin/env python3
"""Bind Kaggle-generated PBR-style textures into Godot 3.x source.

Run after copying PNGs into art/textures:
    python tools/integrate_gpu_textures.py
Idempotent: checks markers and won't patch twice.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / "art" / "textures"
REQUIRED = [
    "stone_floor_albedo.png", "stone_floor_roughness.png",
    "metal_trim_albedo.png", "metal_trim_roughness.png",
    "fabric_dark_albedo.png", "fabric_dark_roughness.png",
    "armor_plate_albedo.png", "armor_plate_roughness.png",
    "skin_albedo.png", "hair_dark_albedo.png",
]
missing = [x for x in REQUIRED if not (TEXTURES / x).is_file()]
if missing:
    raise SystemExit("Missing textures: " + ", ".join(missing))

def patch(path, before, after, marker):
    text = path.read_text()
    if marker in text:
        print("Already integrated:", path.name)
        return
    if before not in text:
        raise SystemExit(f"Could not find expected integration point in {path}. Source changed; review before patching.")
    path.write_text(text.replace(before, after, 1))
    print("Integrated:", path.name)

fighter = ROOT / "scripts" / "FighterVisual.gd"
fighter_before = '''func _surface_texture(kind):
    if _surface_texture_cache.has(kind):'''
fighter_after = '''# GPU_TEXTURE_INTEGRATION_V1
# Load GPU-produced assets only once per fighter; retain procedural fallback.
func _gpu_texture(kind):
    var files = {
        "skin": "skin_albedo.png",
        "hair": "hair_dark_albedo.png",
        "metal": "armor_plate_albedo.png",
        "fabric": "fabric_dark_albedo.png"
    }
    if not files.has(kind):
        return null
    var path = "res://art/textures/" + files[kind]
    if not ResourceLoader.exists(path):
        return null
    return load(path)

func _gpu_roughness(kind):
    var files = {
        "metal": "armor_plate_roughness.png",
        "fabric": "fabric_dark_roughness.png"
    }
    if not files.has(kind):
        return null
    var path = "res://art/textures/" + files[kind]
    if not ResourceLoader.exists(path):
        return null
    return load(path)

func _surface_texture(kind):
    if _surface_texture_cache.has(kind):'''
patch(fighter, fighter_before, fighter_after, "GPU_TEXTURE_INTEGRATION_V1")

fighter_text = fighter.read_text()
old = '''        mat.albedo_texture = _surface_texture(kind)
        mat.uv1_scale'''
new = '''        var generated = _gpu_texture(kind)
        mat.albedo_texture = generated if generated != null else _surface_texture(kind)
        var roughness_map = _gpu_roughness(kind)
        if roughness_map != null:
            mat.roughness_texture = roughness_map
            mat.roughness_texture_channel = SpatialMaterial.TEXTURE_CHANNEL_RED
        mat.uv1_scale'''
patch(fighter, old, new, "var generated = _gpu_texture(kind)")

arena = ROOT / "scripts" / "ArenaArchitecture.gd"
old_arena = '''func _ready():
    stone = _mat(Color(0.37, 0.40, 0.47), 0.02, 0.72)'''
new_arena = '''# GPU_ARENA_TEXTURE_INTEGRATION_V1
func _texture_material(albedo_file, roughness_file, fallback):
    var albedo_path = "res://art/textures/" + albedo_file
    if not ResourceLoader.exists(albedo_path):
        return fallback
    fallback.albedo_texture = load(albedo_path)
    if roughness_file != "":
        var roughness_path = "res://art/textures/" + roughness_file
        if ResourceLoader.exists(roughness_path):
            fallback.roughness_texture = load(roughness_path)
            fallback.roughness_texture_channel = SpatialMaterial.TEXTURE_CHANNEL_RED
    return fallback

func _ready():
    stone = _mat(Color(0.37, 0.40, 0.47), 0.02, 0.72)'''
patch(arena, old_arena, new_arena, "GPU_ARENA_TEXTURE_INTEGRATION_V1")
arena_text = arena.read_text()
old2 = '''    blue = _mat(Color(0.18, 0.44, 0.65), 0.35, 0.27)
    # Center circular inlay'''
new2 = '''    blue = _mat(Color(0.18, 0.44, 0.65), 0.35, 0.27)
    # The texture color is multiplied by the base color; set it neutral for full fidelity.
    stone = _texture_material("stone_floor_albedo.png", "stone_floor_roughness.png", stone)
    stone.albedo_color = Color(1, 1, 1)
    gold = _texture_material("metal_trim_albedo.png", "metal_trim_roughness.png", gold)
    gold.albedo_color = Color(0.94, 0.76, 0.49)
    # Center circular inlay'''
patch(arena, old2, new2, '# The texture color is multiplied')

print(f"Ready: {len(REQUIRED)} generated textures; import project in Godot 3.x to verify visuals.")
