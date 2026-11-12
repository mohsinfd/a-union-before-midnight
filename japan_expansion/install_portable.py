"""Build from a user's local Blood and Iron foundation; never starts the game."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',required=True,type=Path)
    parser.add_argument('--base-root',required=True,type=Path)
    parser.add_argument('--no-shortcut',action='store_true')
    args=parser.parse_args()
    game=args.game_root.resolve();base=args.base_root.resolve();target=game/'Mods/Japan Rising JX1 Alpha2'
    if not (game/'Darkest Hour.exe').is_file():parser.error('The game folder must contain Darkest Hour.exe')
    for marker in ('scenarios/1933.eug','db/units/division_types.txt','config/tech_names.csv'):
        if not (base/marker).is_file():parser.error('The Blood and Iron folder is missing '+marker)
    if target==base or target.is_relative_to(base) or base.is_relative_to(target):
        parser.error('The foundation and Japan Rising destination must be separate folders')
    try:import PIL
    except ImportError:parser.error('Install Pillow first: python -m pip install -r requirements.txt')
    os.environ['JAPAN_RISING_GAME_ROOT']=str(game);os.environ['JAPAN_RISING_BASE_ROOT']=str(base)
    (HERE/'local_paths.json').write_text(json.dumps({'game_root':str(game),'base_root':str(base)},indent=2)+'\n')
    # Build refuses to replace files while the game process is running.
    for script,tail in (('build.py',['spec']),('build.py',['install']),
                        ('UNIQUE_UNIT_EVENTS_review.py',[]),('ENEMY_TRANSPORT_AI_review.py',[]),
                        ('PLAYER_COPY_review.py',[]),('validate.py',[]),('portable_verify.py',[])):
        print('Running '+script+' '+' '.join(tail),flush=True)
        subprocess.run([sys.executable,str(HERE/script),*tail],cwd=HERE,check=True)
    # Only the player-operated launcher can start the engine. Set its local
    # folder without changing global PATH, Python or Git settings.
    launcher=HERE/'Launch Japan Rising Alpha2.ps1'
    script=launcher.read_text(encoding='utf-8')
    escaped=str(game).replace("'","''")
    script,count=re.subn(r"(?m)^\s*\$gameRoot = '[^\r\n]*'",lambda m:"    $gameRoot = '"+escaped+"'",script,count=1)
    assert count==1;launcher.write_text(script,encoding='utf-8')
    if not args.no_shortcut:
        def q(value):return "'"+str(value).replace("'","''")+"'"
        powershell=("$taskShell=New-Object -ComObject WScript.Shell; "
                    "$taskDesktop=[Environment]::GetFolderPath('Desktop'); "
                    "$taskLink=$taskShell.CreateShortcut((Join-Path $taskDesktop 'Japan Rising JX1 Alpha2.lnk')); "
                    "$taskLink.TargetPath=(Join-Path $PSHOME 'powershell.exe'); "
                    "$taskLink.Arguments="+q('-NoProfile -ExecutionPolicy Bypass -File "'+str(launcher)+'"')+"; "
                    "$taskLink.WorkingDirectory="+q(game)+"; $taskLink.Save()")
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',powershell],check=True)
    print('Installed and offline-validated '+str(target)+'. Start a new 1933 campaign. The game was not run.')


if __name__=='__main__':main()
