#!/usr/bin/env python3
"""Image-guided likeness repair. Existing images are only temporary references.
Place approved SINGLE-character photos at roster/approved_refs/00.png ... 13.png.
Never overwrites source/reference/GLB. Creates candidate PNGs and a review sheet.
Requires existing aeryvex_ai_env, SDXL, GPU, internet. T4 uses offload.
"""
import json,re,os,argparse,subprocess,sys
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("--project",default="/kaggle/working/Aeryvex-Pro-Godot4")
ap.add_argument("--start",type=int,default=0)
ap.add_argument("--count",type=int,default=14)
args=ap.parse_args()
root=Path(args.project)
spec=json.loads((root/"roster/appearance_blueprints_first14.json").read_text())
source=root/"roster/approved_refs"
source.mkdir(exist_ok=True,parents=True)
from PIL import Image,ImageOps,ImageDraw
# IMPORTANT: existing AI-generated references are not original visual blueprints.
missing=[]
for c in spec[args.start:args.start+args.count]:
 if not (source/f"{c['id']:02}.png").exists():
  missing.append(f"{c['id']:02}.png {c['name']}")
if missing:
 print("REFERENCE IMAGES MISSING: To fix the likeness, upload ONE clear FULL-BODY character image per entry.",flush=True)
 print("Place approved reference PNGs in:",source)
 for item in missing:print(" -",item)
 print("No model was generated or replaced. Existing 14 meshes remain safe.")
 sys.exit(2)
import torch
from diffusers import AutoPipelineForText2Image
print("Loading SDXL + actual image-conditioning adapter...",flush=True)
pipe=AutoPipelineForText2Image.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0",torch_dtype=torch.float16,use_safetensors=True)
pipe.load_ip_adapter("h94/IP-Adapter",subfolder="sdxl_models",weight_name="ip-adapter_sdxl.bin")
pipe.set_ip_adapter_scale(0.82)
pipe.enable_model_cpu_offload()
rows=[]
for c in spec[args.start:args.start+args.count]:
 i=c["id"];name=c["name"]
 p=source/f"{i:02}.png"
 slug=re.sub("[^a-z0-9]+","_",name.lower()).strip("_")
 folder=root/"art/character_models"/f"{i:02}_{slug}"/"likeness_review"
 folder.mkdir(parents=True,exist_ok=True)
 image=Image.open(p).convert("RGB")
 prompt=(f"One full body 3D videogame character model of {name} from {c['reference_era']}, "
         f"{c['species']}, {c['face_and_anatomy']}, {c['costume']}, "
         "single person only, arms slightly spread, head to boots visible, neutral upright pose, white studio backdrop, no weapons")
 print(f"IMAGE-GUIDED: {i+1}/42 {name}",flush=True)
 try:
  candidate=pipe(prompt=prompt,ip_adapter_image=image,negative_prompt="character turnaround sheet, collage, inset faces, multiple figures, captions, borders, cropped limbs, text, watermarks, weapons",num_inference_steps=25,guidance_scale=6.0,width=768,height=1024).images[0]
  candidate.save(folder/"candidate_guided.png")
  rows.append((name,image,candidate))
 except Exception as e:
  print(f"FAILED {name}: {e}",flush=True)
  continue
# Reference-vs-candidate sheet; no silent automatic approval.
W,H=720,520
board=Image.new("RGB",(W,len(rows)*H),"white")
d=ImageDraw.Draw(board)
for idx,(name,ref,candidate) in enumerate(rows):
 y=idx*H
 for j,im in enumerate((ref,candidate)):
  im=ImageOps.contain(im,(344,460))
  board.paste(im,(j*360+(360-im.width)//2,y+25))
 d.text((8,y+6),name+" / ORIGINAL REFERENCE (left) vs IMAGE-GUIDED (right)",fill="black")
out=root/"roster/first14_image_guided_review.jpg"
board.save(out,quality=90)
print("COMPLETED CANDIDATES:",len(rows),"/",args.count)
print("REVIEW SHEET:",out)
print("NO GLBs OVERWRITTEN. Review first, reconstruct accepted inputs separately.")
