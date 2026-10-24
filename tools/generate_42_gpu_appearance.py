#!/usr/bin/env python3
"""GPU 42-character appearance asset batch. Run inside Kaggle with internet + GPU.
Run with --install once (or rerun); subsequent runs skip successful entries.
Requires Aeryvex full-42 roster JSON already installed.
Generates reference PNGs -> real GLB meshes via TripoSR -> Godot asset folders.
Generated 3D is a first-pass asset, NOT a rigged/verified likeness.
"""
import argparse, json, os, re, subprocess, sys, traceback
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--project",default="/kaggle/working/Aeryvex-Pro-Godot4")
ap.add_argument("--install",action="store_true")
ap.add_argument("--limit",type=int,default=42)
args=ap.parse_args()
root=Path(args.project); manifest=root/"roster/characters.json"
if not manifest.exists():raise SystemExit("Missing roster/characters.json; run 42-roster integration first")
characters=json.loads(manifest.read_text())
assert len(characters)==42
out=root/"art/character_models"; out.mkdir(parents=True,exist_ok=True)
tools=Path("/kaggle/working/appearance_models")
tools.mkdir(parents=True,exist_ok=True)
triposr=tools/"TripoSR"
if args.install:
    subprocess.run([sys.executable,"-m","pip","install","-q","diffusers>=0.30,<0.38","transformers>=4.44,<5","accelerate","safetensors","huggingface_hub","omegaconf","trimesh","rembg[cpu]","einops","imageio","imageio-ffmpeg"],check=True)
    if not (triposr/"run.py").exists():
        subprocess.run(["git","clone","--depth","1","https://github.com/VAST-AI-Research/TripoSR.git",str(triposr)],check=True)
    subprocess.run([sys.executable,"-m","pip","install","-q","-r",str(triposr/"requirements.txt")],check=True)
    # Some TripoSR environments need separately compiled torchmcubes; leave diagnostics visible.
import torch
if not torch.cuda.is_available():raise SystemExit("GPU unavailable. Enable Kaggle notebook GPU accelerator.")
from diffusers import AutoPipelineForText2Image
from PIL import Image

looks={
0:"young male warrior, shoulder-length brown hair, dark layered Jedi tunic",
1:"older aristocratic man, swept silver hair, short gray beard, dark brown tunic, maroon cape",
2:"bearded male Jedi, sandy hair, cream tunic, brown robe",
3:"bald dark-skinned Jedi master, beige tunic, brown cloak",
4:"tall Jedi man, long chestnut hair, beard, green-brown robe",
5:"small elderly green alien with large pointed ears, beige Jedi robe",
6:"towering black-armored masked Sith lord with domed helmet and flowing cape",
7:"elderly hooded pale Sith emperor, deeply wrinkled face, black robes",
8:"tall skeletal white-and-metal cyborg general, four-arm shoulder housing",
9:"young orange-skinned Togruta alien female, white-and-blue head tails, dark battle outfit",
10:"adult orange-skinned Togruta alien female, long white-and-blue head tails, gray warrior clothing",
11:"alien male Jedi with Kel Dor breathing mask, goggles, brown robe",
12:"green Nautolan alien Jedi, many head tentacles, brown tunic",
13:"red-and-white Togruta alien Jedi woman, striped head tails, flowing beige robe",
14:"blue-skinned Twi'lek alien Jedi woman, twin long lekku, brown warrior outfit",
15:"green Mirialan Jedi woman, tall dark headpiece, layered dark-green robes",
16:"olive-skinned Mirialan woman, patterned face tattoos, brown hooded Jedi robe",
17:"bearded male rebel Jedi, ponytail, green-brown armor vest",
18:"young male rebel Jedi, short dark hair, orange utility vest",
19:"red-haired male warrior, short windswept hair, blue poncho over tan tunic",
20:"blond male Jedi, black tunic and utility belt",
21:"red-and-black tattooed Zabrak alien male, small scalp horns, black robes",
22:"pale bald female assassin, gray fitted armor and dark wraps",
23:"large muscular yellow-and-black Zabrak alien male, scalp horns, heavy bronze armor",
24:"hooded masked Sith warrior, dark red robes and gray metallic mask",
25:"tall pale Pau'an male Inquisitor, severe face, dark armored suit",
26:"helmeted female Inquisitor, glossy black armor, red visor",
27:"hooded masked dark male knight, black robes and ribbed silver face mask",
28:"older gray-haired bearded male warrior, black-and-bronze heavy armor",
29:"young blond female dark apprentice, gray plated armor, pale skin",
30:"blue-and-silver Mandalorian bounty hunter, T visor helmet, jetpack",
31:"green weathered Mandalorian bounty hunter, dented T visor helmet, rocket pack",
32:"blue-skinned Duros male bounty hunter, broad brim cowboy hat, dark blue coat, breathing tubes",
33:"green Trandoshan reptilian bounty hunter, orange flight suit, scaled snout",
34:"tall skinny rust-colored humanoid assassin droid, cylindrical sensor head, mechanical joints",
35:"scarred male bounty hunter, white head bandages, tan padded armor",
36:"pale female bounty hunter, long orange ponytail, antenna implant, red costume",
37:"masked Kyuzo alien bounty hunter, extremely wide circular hat, beige armor cloak",
38:"female bounty hunter, sleek black armor with orange accents, dark helmet",
39:"silver beskar Mandalorian bounty hunter, chrome T visor helmet, brown cape",
40:"female Clawdite bounty hunter, purple head covering, dark purple uniform",
41:"large black-furred Wookiee bounty hunter, massive muscular body, gold bandolier"
}
pipeline=AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo",torch_dtype=torch.float16,variant="fp16")
pipeline=pipeline.to("cuda:0")
pipeline.set_progress_bar_config(disable=True)
report=[]
for entry in characters[:args.limit]:
    i=entry["id"];slug=re.sub(r"[^a-z0-9]+","_",entry["name"].lower()).strip("_")
    folder=out/f"{i:02d}_{slug}"; folder.mkdir(parents=True,exist_ok=True)
    ref=folder/"front.png"; final=folder/"character.glb"
    state={"id":i,"name":entry["name"],"reference":str(ref),"mesh":str(final),"status":"pending"}
    try:
        if not ref.exists():
            prompt=f"Full body single standing character centered, {looks[i]}, cinematic realistic 3D game character concept art, orthographic front view, neutral symmetrical A-pose, arms held slightly away from sides, feet fully visible, no weapon, highly detailed costume materials, soft studio lighting, clean solid white background, single subject"
            image=pipeline(prompt=prompt,num_inference_steps=4,guidance_scale=0.0,height=768,width=512).images[0]
            image.save(ref)
        state["status"]="reference_generated"
        if not final.exists():
            # TripoSR exports mesh.obj. Convert actual generated mesh to GLB using trimesh.
            subprocess.run([sys.executable,str(triposr/"run.py"),str(ref),"--output-dir",str(folder/"triposr"),"--device","cuda:0"],check=True,timeout=420,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            objs=list((folder/"triposr").rglob("*.obj"))
            if not objs:raise RuntimeError("TripoSR produced no OBJ mesh")
            import trimesh
            mesh=trimesh.load(str(objs[0]),force="scene")
            mesh.export(str(final))
        state["status"]="glb_generated"
    except Exception as exc:
        state["status"]="error"
        state["error"]=repr(exc)
        print(f"ERROR {i:02d} {entry['name']}: {exc}",flush=True)
    (folder/"generation_status.json").write_text(json.dumps(state,indent=2))
    report.append(state)
    print(f"{i+1}/42 {entry['name']}: {state['status']}",flush=True)
(root/"roster/appearance_generation_report.json").write_text(json.dumps(report,indent=2))
print("Generated GLBs:",sum(x["status"]=="glb_generated" for x in report))
print("Reference PNGs:",sum(x["status"] in ("reference_generated","glb_generated") for x in report))
print("Errors:",sum(x["status"]=="error" for x in report))
print("Production meshes still need orientation, materials, animation rigging and visual approval.")
