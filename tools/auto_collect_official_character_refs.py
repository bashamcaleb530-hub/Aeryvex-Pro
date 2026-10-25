#!/usr/bin/env python3
"""Fetch official character images into Kaggle and run image guided candidate generation.
Sources are documented; automatic selection is NOT proof of era/likeness.
"""
import re, json, io, sys, subprocess, argparse
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw
ROOT=Path("/kaggle/working/Aeryvex-Pro-Godot4")
PAGES=[
("anakin-skywalker","Revenge of the Sith"),("count-dooku","Revenge of the Sith"),
("obi-wan-kenobi","Revenge of the Sith"),("mace-windu","Revenge of the Sith"),
("qui-gon-jinn","The Phantom Menace"),("yoda","Revenge of the Sith"),
("darth-vader","Revenge of the Sith"),("emperor-palpatine-darth-sidious","Return of the Jedi"),
("general-grievous","Revenge of the Sith"),("ahsoka-tano","The Clone Wars young"),
("ahsoka-tano","Rebels adult Fulcrum"),("plo-koon","Revenge of the Sith"),
("kit-fisto","Revenge of the Sith"),("shaak-ti","Revenge of the Sith")]
UA={"User-Agent":"Mozilla/5.0 (Aeryvex visual reference research prototype)"}
roster=json.loads((ROOT/"roster/characters.json").read_text())
refs=ROOT/"roster/approved_refs";refs.mkdir(exist_ok=True,parents=True)
manifest=[]
session=requests.Session();session.headers.update(UA)
def get_candidates(page):
 html=session.get(page,timeout=35);html.raise_for_status()
 soup=BeautifulSoup(html.text,"html.parser")
 choices=[]
 def add(url,alt,origin):
  if not url:return
  url=urljoin(page,url)
  if "lumiere-a.akamaihd.net" not in url and not any(x in url for x in ("starwars.com","disney")):return
  # Ignore logos / site chrome; hero / datapage images get highest priority.
  if not any(ext in url.lower() for ext in (".jpg",".jpeg",".png",".webp","/v1/images/")):return
  score=(14 if "databank_" in url.lower() else 0)+(8 if "databank" in alt.lower() else 0)
  score+=8 if origin=="img" else 2
  choices.append((score,url,alt,origin))
 for tag in soup.find_all("img"):
  add(tag.get("src") or tag.get("data-src"),tag.get("alt",""),"img")
  for key in ("data-src","data-original"):add(tag.get(key),tag.get("alt",""),"img")
 for tag in soup.find_all("meta"):
  if tag.get("property") in ("og:image","twitter:image") or tag.get("name")=="twitter:image":
   add(tag.get("content"),"social preview","meta")
 # The site frequently encodes its character image URL in page source.
 for m in re.finditer(r'https?[^" <\\]+?lumiere-a\.akamaihd\.net[^" <\\]+',html.text):
  raw=m.group(0).replace("\\u002F","/").replace("\\/","/")
  add(raw,"embedded","embedded")
 unique={}
 for q in choices:
  unique.setdefault(q[1],q)
 return sorted(unique.values(),reverse=True)
def download_candidate(url):
 r=session.get(url,timeout=45);r.raise_for_status()
 im=Image.open(io.BytesIO(r.content)).convert("RGB")
 if min(im.size)<220:raise ValueError("too small")
 if max(im.size)>3000:im.thumbnail((3000,3000))
 return im
for i,(slug,era) in enumerate(PAGES):
 page="https://www.starwars.com/databank/"+slug
 name=roster[i]["name"]
 path=refs/f"{i:02}.png"
 print(f"\n[{i:02}] {name} - official source {page}",flush=True)
 if path.exists():
  print("Keeping existing reference",path,flush=True)
  manifest.append(dict(id=i,name=name,source_page=page,image="existing",era=era,status="existing_not_verified"))
  continue
 try:
  choices=get_candidates(page)
  got=None
  for _,url,alt,origin in choices:
   try:
    im=download_candidate(url);got=(im,url,alt);break
   except Exception:continue
  if got is None:raise RuntimeError("No downloadable character image detected")
  im,url,alt=got
  im.save(path)
  print("Downloaded actual official-site image",path,im.size,flush=True)
  manifest.append(dict(id=i,name=name,source_page=page,image_url=url,alt=alt,era=era,status="auto_collected_NEEDS_era_and_likeness_review"))
 except Exception as exc:
  print("FAILED source:",str(exc),flush=True)
  manifest.append(dict(id=i,name=name,source_page=page,era=era,status="FAILED",error=str(exc)))
(ROOT/"roster/auto_reference_manifest.json").write_text(json.dumps(manifest,indent=2))
TW,TH=320,340
board=Image.new("RGB",(TW*4,TH*4),"#eeeeee")
d=ImageDraw.Draw(board)
for i,item in enumerate(manifest):
 x=(i%4)*TW;y=(i//4)*TH
 file=refs/f"{i:02}.png"
 if file.exists():
  im=ImageOps.contain(Image.open(file).convert("RGB"),(TW-12,TH-75))
  board.paste(im,(x+(TW-im.width)//2,y+6))
 else:d.text((x+8,y+35),"DOWNLOAD FAILED",fill="red")
 d.text((x+6,y+TH-64),f"{i:02} {item['name']}"[:41],fill="black")
 d.text((x+6,y+TH-44),item["era"][:42],fill="black")
 d.text((x+6,y+TH-24),"UNVERIFIED REFERENCE",fill="#9c391d")
sheet=ROOT/"roster/official_reference_contact_sheet.jpg";board.save(sheet,quality=92)
print("\nCONTACT SHEET:",sheet,flush=True)
print("REFERENCE FILES:",sum((refs/f"{i:02}.png").exists() for i in range(14)),"/14",flush=True)
print("Manifest:",ROOT/"roster/auto_reference_manifest.json",flush=True)
if any(not (refs/f"{i:02}.png").exists() for i in range(14)):
 print("Fix missing downloads before running IP Adapter.",flush=True)
 sys.exit(2)
if "--generate" in sys.argv:
 runner=ROOT/"tools/image_guided_likeness_first14.py"
 py="/kaggle/working/aeryvex_ai_env/bin/python"
 print("Running image-guided candidates; 3D GLBs remain untouched.",flush=True)
 sys.exit(subprocess.call([py,"-u",str(runner),"--project",str(ROOT),"--start","0","--count","14"]))
