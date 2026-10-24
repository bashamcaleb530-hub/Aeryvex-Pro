# Go 9 continuation — visual realism pass

This revision continues Go 9 without adding game modes. It adds inexpensive geometrical details to the existing original procedural fighters: individual eyes (sclera, iris, pupil), brows, cheeks, jaw, nose, mouth, ears, side hair, garment seams, collar, belt pouch, and shoulder plates. It preserves the Go 9 hero-vs-infantry systems and the earlier camera, combat, and squad changes.

**Limit:** This is a visual-detail *increment*, not photorealism or the promised skinned MakeHuman character pipeline. Faces remain stylized geometric approximations, with no facial animation. Realistic assets, materials, skinned rigs and motion work are still required. No Star Wars copyrighted model is included by this work.

## Tests performed
- All `tests/check*.py` static/source tests passed, including `tests/check_go9_realism.py`.
- ZIP integrity will be checked during packaging.
- Godot runtime, rendering, motion and performance are **not verified** here because the Godot executable is not installed in this environment. Run `tools/run_godot_tests.sh` and visually inspect characters on the target machine.

## Remaining realism-first work
1. Recover or create genuine textured, skinned character meshes and import in Godot.
2. Improve jointed procedural silhouettes or replace them with skeletal rigs.
3. Retarget keyframed locomotion and combat animations and correct clipping.
4. Upgrade materials, lighting, set dressing, visual effects and audio with performance checks on target laptop.
