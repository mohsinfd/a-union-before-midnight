"""Portable local foundation paths; no game launch and no download of game data."""
import json,os
from pathlib import Path

HERE=Path(__file__).resolve().parent
config_path=HERE/'local_paths.json'
CONFIG=json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}


def choose(env,key,candidates,marker):
    explicit=os.environ.get(env) or CONFIG.get(key)
    if explicit:return Path(explicit).expanduser().resolve()
    for candidate in candidates:
        if (candidate/marker).exists():return candidate.resolve()
    return candidates[0].resolve()


game_candidates=[Path(os.environ.get('PROGRAMFILES(X86)',r'C:\Program Files (x86)'))/'Steam/steamapps/common/Darkest Hour A HOI Game',
                 Path(r'C:\GOG Games\Darkest Hour')]
GAME=choose('JAPAN_RISING_GAME_ROOT','game_root',game_candidates,'Darkest Hour.exe')
SOURCE=choose('JAPAN_RISING_BASE_ROOT','base_root',[
    HERE.parent.parent/'Blood and Iron v1.1',GAME/'Mods/Blood and Iron v1.1',
    GAME/'Mods/Blood and Iron',Path.home()/'Downloads/Blood and Iron v1.1'],'scenarios/1933.eug')
ART_ROOT=Path(os.environ.get('JAPAN_RISING_ART_CACHE',str(HERE/'art'))).expanduser()
