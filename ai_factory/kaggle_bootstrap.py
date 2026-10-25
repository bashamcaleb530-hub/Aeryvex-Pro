"""Kaggle one-cell bootstrap:
exec(__import__('urllib.request').request.urlopen('https://raw.githubusercontent.com/bashamcaleb530-hub/Aeryvex-Pro/aeryvex-original-game/ai_factory/kaggle_bootstrap.py').read().decode())
Only fetch trusted code you own. This runs the checked-in script.
"""
from pathlib import Path
from zipfile import ZipFile
import os, subprocess, urllib.request, shutil, json, sys

REPO_URL="https://github.com/bashamcaleb530-hub/Aeryvex-Pro.git"
BRANCH="aeryvex-original-game"
REPO=Path("/kaggle/working/Aeryvex-Pro-Original")
TOOLS=Path("/kaggle/working/aeryvex_tools")
GODOT=TOOLS/"Godot_v4.7.2-stable_linux.x86_64"
ART=REPO/"original_game"/"approved_heroes"
REFS=("kai.png","ryker.png","lyra.png")
ZIP="AetherWorld_Exact_Approved_Kai_Ryker_Lyra.zip"

def run(args,**kw):
    result=subprocess.run(args,check=True,text=True,**kw)
    return result

def setup_repo():
    if (REPO/".git").is_dir():
        run(["git","pull","--ff-only","origin",BRANCH],cwd=REPO)
    else:
        REPO.parent.mkdir(parents=True,exist_ok=True)
        run(["git","clone","--branch",BRANCH,"--single-branch",REPO_URL,str(REPO)])

def setup_godot():
    if GODOT.exists(): return
    TOOLS.mkdir(parents=True,exist_ok=True)
    name="Godot_v4.7.2-stable_linux.x86_64.zip"
    archive=TOOLS/name
    source="https://github.com/godotengine/godot/releases/download/4.7.2-stable/"+name
    print("Godot missing; installing...")
    urllib.request.urlretrieve(source,archive)
    with ZipFile(archive) as z:
        for member in z.namelist():
            if member==GODOT.name:
                z.extract(member,TOOLS)
    if not GODOT.is_file(): raise RuntimeError("Godot binary missing from release ZIP")
    GODOT.chmod(0o755)

def setup_art():
    ART.mkdir(parents=True,exist_ok=True)
    if all((ART/name).is_file() for name in REFS):
        print("Approved portraits present in repository.")
        return
    candidates=list(Path("/kaggle/input").rglob(ZIP)) + list(Path("/kaggle/working").glob(ZIP))
    for archive in candidates:
        with ZipFile(archive) as z:
            for member in z.namelist():
                name=Path(member).name
                if name in REFS or name=="approved_character_selection.png":
                    with z.open(member) as src,(ART/name).open("wb") as dest:
                        shutil.copyfileobj(src,dest)
        if all((ART/name).is_file() for name in REFS):
            break
    missing=[name for name in REFS if not (ART/name).is_file()]
    if missing:
        print("ASSET BLOCKER: approved character portraits not in GitHub or Kaggle input:",missing)
        print("Do not replace these with generated or unrelated artwork.")

def test_script(path):
    result=subprocess.run([str(GODOT),"--headless","--path",str(REPO/"original_game"),"--script",path],capture_output=True,text=True,timeout=180)
    output=result.stdout+"\n"+result.stderr
    success=result.returncode==0 and not any(x in output for x in ["SCRIPT ERROR:","ERROR:","FAIL:"])
    print(path,"PASS" if success else "FAIL", "exit",result.returncode)
    if not success: print(output[-8000:])
    return success

def main():
    setup_repo()
    setup_art()
    setup_godot()
    imp=subprocess.run([str(GODOT),"--headless","--path",str(REPO/"original_game"),"--editor","--quit"],capture_output=True,text=True,timeout=180)
    output=imp.stdout+"\n"+imp.stderr
    if imp.returncode or "SCRIPT ERROR:" in output or "ERROR:" in output:
        print("Godot import reported errors:",output[-8000:])
        sys.exit(1)
    tests=["res://tests/test_aether_world_menu.gd","res://tests/test_military_opening.gd","res://tests/test_player_ascension.gd"]
    outcomes=[test_script(t) for t in tests]
    print("Visual asset inventory:",{n:(ART/n).is_file() for n in REFS})
    print("Rigged models:",{n:(ART/(n[:-4]+".glb")).is_file() for n in REFS})
    if not all(outcomes): sys.exit(1)

if __name__=="__main__": main()
