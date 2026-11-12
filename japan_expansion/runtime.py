"""Prepare a private executable/settings/log runtime for isolated engine tests.

Only this runtime directory is created. Vanilla resource junctions are read by
the game; the sole mod junction points at the newly built Japan installation.
"""
import json
from pathlib import Path
import shutil
import subprocess
from build import GAME,TARGET,HERE,MOD_NAME

RUNTIME=HERE/"runtime"


def junction(path,target):
    if path.exists():
        if path.resolve()!=target.resolve():raise RuntimeError("Unexpected junction target: "+str(path))
        return
    p=subprocess.run(["cmd.exe","/c","mklink","/J",str(path),str(target)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)


def prepare():
    RUNTIME.mkdir(exist_ok=True)
    for name in ("Darkest Hour.exe","libbz2.dll"):
        if not (RUNTIME/name).exists():shutil.copy2(GAME/name,RUNTIME/name)
    for folder in ("ai","avi","config","db","gfx","map","music","scenarios","sfx","tutorial"):
        junction(RUNTIME/folder,GAME/folder)
    (RUNTIME/"Mods").mkdir(exist_ok=True)
    junction(RUNTIME/"Mods"/MOD_NAME,TARGET)
    original=(GAME/"settings.cfg").read_text(encoding="latin1").splitlines()
    replacements={1:"0 # MUSIC",3:"6 # Custom resolution",4:"1280 # Width",5:"800 # Height",6:"1 # Windowed test runtime",7:"0 # Skip startup movie",8:"1 # Debug logging",14:MOD_NAME+" # Selected mod"}
    for line,value in replacements.items():original[line]=value
    (RUNTIME/"settings.cfg").write_text("\n".join(original)+"\n",encoding="latin1")
    result={"runtime":str(RUNTIME),"executable":str(RUNTIME/"Darkest Hour.exe"),"argument":"Mods\\"+MOD_NAME,"separate_settings":True,"user_game_processes_closed":False}
    (HERE/"RUNTIME.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":prepare()
