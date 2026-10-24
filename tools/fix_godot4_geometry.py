#!/usr/bin/env python3
"""Post-conversion Godot 4 fixes for Aeryvex Pro geometry/rig APIs."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
changes=[
 ("scripts/FighterVisual.gd", "mesh_tool.add_uv(", "mesh_tool.set_uv("),
 ("scripts/HumanoidRig.gd", "Basis(pivot.rotation)", "Basis.from_euler(pivot.rotation)"),
]
for rel,old,new in changes:
 p=root/rel; s=p.read_text()
 if old in s:
  p.write_text(s.replace(old,new)); print("PATCHED",rel,old,"->",new)
 elif new in s:
  print("ALREADY PATCHED",rel)
 else:
  raise SystemExit("Expected expression missing in "+rel+": "+old)
print("Done. Re-run import and runtime diagnostics.")
