#!/usr/bin/env python3
"""Prepare a 3-batch, low-CPU version of the existing Aeryvex generator.
Runs 14-character slices by replacing the loop enumeration with a start/stop slice.
Preserves cached PNG/GLB and uses the existing isolated Python environment.
"""
from pathlib import Path
p=Path("/kaggle/working/Aeryvex-Pro-Godot4/tools/generate_42_gpu_appearance.py")
if not p.exists():raise SystemExit("Original generator is missing")
s=p.read_text()
if "--start" not in s:
 s=s.replace('ap.add_argument("--limit",type=int,default=42)', 'ap.add_argument("--limit",type=int,default=42)\nap.add_argument("--start",type=int,default=0)')
 s=s.replace('for entry in characters[:args.limit]:','for entry in characters[args.start:args.start+args.limit]:')
 p.write_text(s)
 print("Patched generator for 14-character batches")
else:print("Already supports batches")
