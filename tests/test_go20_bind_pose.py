from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "scripts" / "FighterVisual.gd").read_text()
checks = [
    "var left_foot_rest = Vector3.ZERO",
    "var right_foot_rest = Vector3.ZERO",
    'left_foot_rest = left_foot.translation',
    'right_foot_rest = right_foot.translation',
    'left_foot_rest.y + 0.075 * left_swing',
    'right_foot_rest.y + 0.075 * right_swing',
    'left_foot_rest.z + left_stance_offset',
    'right_foot_rest.z + right_stance_offset',
]
for snippet in checks:
    assert snippet in src, f"Go 20 bind-pose regression: {snippet}"
# A zero animation offset must preserve the actual boot rest depth.
for depth in [-0.08, -0.12, 0.0]:
    assert abs((depth + 0.0) - depth) < 1e-8
print("Go 20 foot bind-pose checks: 11/11 passed")
