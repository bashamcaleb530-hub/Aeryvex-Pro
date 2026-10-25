#!/usr/bin/env python3
"""Aeryvex appearance repair: isolate subjects, preserve backups, reconstruct candidates.
For Kaggle existing 14 PNGs/GLBs. Never replaces game assets until visual approval.
"""
import os,re,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
root=Path("/kaggle/working/Aeryvex-Pro-Godot4")
assets=root/"art/character_models"
roster=json.loads((root/"roster/characters.json").read_text())[:14]
py="/kaggle/working/aeryvex_ai_env/bin/python"
tripo="/kaggle/working/appearance_models/TripoSR/run.py"
env=os.environ.copy()
env.update(OMP_NUM_THREADS="2",MKL_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",PYTHONUNBUFFERED="1")
# Main full-body image is generally left half of wide multi-panel sheets.
# For single image use original. Keep this a REVIEWABLE heuristic, not an assertion.
results=[]
for c in roster:
 i=c["id"];name=c["name"];slug=re.sub("[^a-z0-9]+","_",name.lower()).strip("_")
 folder=assets/f"{i:02d}_{slug}"
 imgp=folder/"front.png"
 if not imgp.exists(): results.append((name,"no reference"));continue
 img=Image.open(imgp).convert("RGB")
 w,h=img.size
 # Identify reference sheet: large width or asymmetric multiple panels.
 # Keep full image for roughly portrait original; crop only obviously landscape sheets.
 if w/h>1.14:
  crop=img.crop((0,0,int(w*.60),h))
 elif w/h>0.72:
  crop=img.crop((0,0,int(w*.68),h))
 else:
  crop=img.copy()
 target=folder/"likeness_review"
 target.mkdir(exist_ok=True)
 isolated=target/"isolated_source.png"
 if not isolated.exists():crop.save(isolated)
 # A white matte is okay; original detail retained for manual review.
 results.append((name,"source prepared"))
print("Prepared",len(results),"isolated reference candidates.")
print("Original PNGs and GLBs untouched.")
# Build side-by-side review from the original and isolated image.
tilew,tileh=270,360
board=Image.new("RGB",(tilew*4,tileh*7),"#eeeeee")
draw=ImageDraw.Draw(board)
for k,c in enumerate(roster):
 i=c["id"];slug=re.sub("[^a-z0-9]+","_",c["name"].lower()).strip("_")
 folder=assets/f"{i:02d}_{slug}"
 for j,fn in enumerate(["front.png","likeness_review/isolated_source.png"]):
  p=folder/fn
  cell=k*2+j;x=(cell%4)*tilew;y=(cell//4)*tileh
  if p.exists():
   im=ImageOps.contain(Image.open(p).convert("RGB"),(tilew-12,tileh-65))
   board.paste(im,(x+(tilew-im.width)//2,y+6))
  draw.text((x+6,y+tileh-50),c["name"][:30],fill="black")
  draw.text((x+6,y+tileh-29),"CURRENT" if j==0 else "ISOLATED",fill="black")
review=root/"roster/first14_source_crop_review.jpg";board.save(review,quality=92)
print("SOURCE REVIEW:",review)
print("Only proceed to reconstruction if the ISOLATED columns show one full-body character.")
