#!/usr/bin/env python3
"""Repair TripoSR bootstrap (re-entrant); leaves Godot and generated assets alone.
Uses Kaggle's torch + CUDA toolchain for torchmcubes source compilation.
"""
from pathlib import Path
import sys, subprocess
project=Path("/kaggle/working/Aeryvex-Pro-Godot4")
target=project/"tools/generate_42_gpu_appearance.py"
repo=Path("/kaggle/working/appearance_models/TripoSR")
if not target.exists():raise SystemExit("Missing GPU generator; fetch it first.")
if not (repo/"requirements.txt").exists():raise SystemExit("TripoSR checkout missing; run original bootstrap to clone first.")
# Modify the original generator to separate source-compiled torchmcubes from general dependencies.
s=target.read_text()
needle='''    subprocess.run([sys.executable,"-m","pip","install","-q","-r",str(triposr/"requirements.txt")],check=True)'''
replace='''    # torchmcubes needs local torch during build; disable isolated build for it.
    # Do not let requirements.txt build it in an isolated temporary interpreter.
    requirements = [line for line in (triposr/"requirements.txt").read_text().splitlines()
                    if "torchmcubes" not in line.lower()]
    fixed_requirements = tools/"requirements_no_torchmcubes.txt"
    fixed_requirements.write_text("\\n".join(requirements)+"\\n")
    subprocess.run([sys.executable,"-m","pip","install","-q","-r",str(fixed_requirements)],check=True)
    subprocess.run([sys.executable,"-m","pip","install","--no-build-isolation",
                    "git+https://github.com/tatsy/torchmcubes.git"],check=True)'''
if needle in s:
 s=s.replace(needle,replace,1)
 target.write_text(s)
 print("PATCHED source installer: compile torchmcubes with locally installed PyTorch")
else:
 print("Generator installer already changed, or unrecognized revision.")
try:
 import torch
 print("Python:",sys.version.split()[0],"Torch:",torch.__version__,"CUDA:",torch.cuda.is_available())
except Exception as e:print("Torch import issue:",repr(e))
print("Do not delete existing PNG or GLB outputs; rerun patched generator.")
