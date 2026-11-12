"""Read-only launch-path and active-install audit. Never executes a launcher."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import build


def audit():
    build.prepare_catalog()
    root,target=build.GAME.resolve(),build.TARGET.resolve()
    settings=build.read(root/'settings.cfg').splitlines()
    assert settings[13].split('#')[0].strip()=='Mods'
    assert settings[14].split('#')[0].strip()==build.MOD_NAME
    assert (root/'Darkest Hour.exe').is_file()
    manifest=json.loads((target/'JAPAN_RISING_BUILD.json').read_text())
    assert Path(manifest['target']).resolve()==target
    assert manifest['mod_name']==build.MOD_NAME and manifest['version']==build.VERSION
    assert manifest['state']=='installed-offline-validated','Final validation record is not published'
    receipt=json.loads((target/manifest['validation_receipt']).read_text())
    assert receipt['version']==manifest['version'] and receipt['state']==manifest['state']
    assert Path(receipt['target']).resolve()==target
    launcher=build.HERE/'Launch Japan Rising Alpha2.ps1'
    script=launcher.read_text()
    assert "$modFolderName = '"+build.MOD_NAME+"'" in script
    assert "$gameRoot = '"+str(build.GAME)+"'" in script
    assert 'installed-offline-validated' in script and '$receipt.version -ne $manifest.version' in script
    assert '$receipt.target -ne $modRoot' in script
    # Parse the actual PowerShell file without evaluating it or Start-Process.
    parse_script="$taskTokens=$null; $taskErrors=$null; [System.Management.Automation.Language.Parser]::ParseFile('"+str(launcher).replace("'","''")+"',[ref]$taskTokens,[ref]$taskErrors) | Out-Null; if($taskErrors.Count){$taskErrors | Out-String | Write-Output; exit 1}; Write-Output 'PowerShell syntax OK'"
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',parse_script],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    # Read only the relevant shortcut metadata; CreateShortcut on an existing
    # path does not save it and no Run/Exec/Start-Process method is invoked.
    shortcut_script="$taskShell=New-Object -ComObject WScript.Shell; $taskDesktop=[Environment]::GetFolderPath('Desktop'); $taskPath=Join-Path $taskDesktop 'Japan Rising JX1 Alpha2.lnk'; if(-not(Test-Path -LiteralPath $taskPath)){exit 1}; $taskLink=$taskShell.CreateShortcut($taskPath); @{path=$taskPath;target=$taskLink.TargetPath;arguments=$taskLink.Arguments;working_directory=$taskLink.WorkingDirectory}|ConvertTo-Json -Compress"
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',shortcut_script],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    shortcut=json.loads(result.stdout)
    assert str(launcher) in shortcut['arguments']
    assert Path(shortcut['working_directory']).resolve()==root
    assert Path(shortcut['target']).name.lower()=='powershell.exe'
    loc=build.read(target/'config/mods.csv')
    assert 'JX_welcome_NAME;' in loc and build.VERSION in loc
    assert 'JX_1933_SCENARIO;Japan Rising 1933 - '+build.VERSION in loc
    expected={r.split(';')[0]:r.split(';')[1] for r in build.localisation().splitlines() if ';' in r and not r.startswith('#')}
    loaded={r.split(';')[0]:r.split(';')[1] for r in loc.splitlines() if ';' in r and not r.startswith('#')}
    assert all(loaded.get(k)==v for k,v in expected.items()),'Installed engine-loaded English differs from the prepared catalogue'
    index=build.read(target/'db/events.txt')
    modules={e.module for e in build.EVENTS}
    for module in modules:
        line='event = "db\\events\\japan_rising\\'+module+'.txt"'
        assert index.count(line)==1,(module,'event registration count')
    hashes={}
    for relative in ['JAPAN_RISING_BUILD.json','config/mods.csv','db/events.txt']+[f'db/events/japan_rising/{m}.txt' for m in sorted(modules)]:
        hashes[relative]=hashlib.sha256((target/relative).read_bytes()).hexdigest()
    report={'version':build.VERSION,'target':str(target),'selected_mod':settings[14].split('#')[0].strip(),
            'shortcut':shortcut,'powershell_syntax':'PASS','registered_modules':len(modules),'loaded_english_matches':len(expected),
            'hashes':hashes,'game_launched':False,'launcher_executed':False,'save_edits':False}
    (build.HERE/'FINAL_INSTALL_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='hashes'},indent=2))


if __name__=='__main__':audit()
