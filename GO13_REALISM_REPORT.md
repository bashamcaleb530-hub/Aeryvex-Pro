# Go 13 — Procedural Character Surface Materials

## Changes
- One shared 64x64 repeatable grayscale microtexture per surface type (skin, cloth, hair, metal).
- Deterministic fabric weave, subtle skin tones, hair striations and brushed-metal patterns.
- Surface-specific roughness, tiled fabric UVs, and glowing blades exempted from texture overlays.
- Cache prevents duplicate procedural texture generation per character instance.

## Limits
Textures are procedural details on existing low-poly geometry; these are **not** photographed, scanned, or photorealistic materials. Meshes do not yet have high-quality UVs, and texture behavior needs visual checking in Godot 3.6. No full runtime test has been performed in this environment.
