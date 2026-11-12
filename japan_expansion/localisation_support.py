"""Install and inspect strings through a filename this DH executable loads."""
import re

# These names are literal config references in the installed DH executable.
# Keep the authoring mirror separate; arbitrary config CSV names are not loaded.
ENGINE_CSV_NAMES={'boostertext.csv','darkest_hour.csv','doomsdaytext.csv','event_text.csv',
                  'extra_text.csv','famous_quotes.csv','messages.csv','models.csv','mods.csv',
                  'modtext.csv','new_text.csv','province_names.csv','scenario_text.csv',
                  'tech_names.csv','text.csv','tutorial.csv','unit_names.csv','world_names.csv'}


def install(source,target,payload,read,write):
    base=read(source/'config/mods.csv')
    from model_names_and_ai import remove_generic_model_conflicts
    from specialist_units import CLASSES,model_years
    # B&I left MODEL_50_0 = Political Leader in mods.csv, although the
    # registered roster stops at 49. Index 50 now belongs to Naval Base Force.
    base=remove_generic_model_conflicts(base,CLASSES,model_years)
    assert not any(l.startswith('JX_') for l in base.splitlines()),'Unexpected JX text in clean baseline'
    # Insert before the baseline's EOF markers, rather than appending behind them.
    write(target/'config/mods.csv',payload+'\n'+base)
    write(target/'config/japan_rising.csv',payload)


def loaded_names(target,game,read):
    names={}
    for name in sorted(ENGINE_CSV_NAMES):
        p=target/'config'/name
        if not p.exists():p=game/'config'/name
        if not p.exists():continue
        for line in read(p).splitlines():
            if line.startswith('#EOF'):break
            row=line.split(';')
            if len(row)>1 and not row[0].startswith('#'):names[row[0]]=row[1]
    return names


def review(target,game,payload,read):
    import hashlib
    exe=(game/'Darkest Hour.exe').read_bytes()
    assert b'config\\mods.csv' in exe,'Installed executable does not reference the chosen localisation file'
    mods=read(target/'config/mods.csv');names=loaded_names(target,game,read)
    expected={line.split(';')[0]:line.split(';')[1] for line in payload.splitlines() if line.startswith('JX_')}
    assert expected and all(value and names.get(key)==value for key,value in expected.items())
    actual=[line.split(';')[0] for line in mods.splitlines() if line.startswith('JX_')]
    assert len(actual)==len(set(actual))==len(expected),'Duplicate or missing generated keys'
    assert all(len(line.split(';'))==12 for line in payload.splitlines() if line.startswith('JX_'))
    first_eof=mods.find('#EOF')
    assert first_eof<0 or mods.rfind('\nJX_')<first_eof,'Strings installed after a baseline EOF marker'
    return {'result':'PASS','loaded_file':'config/mods.csv','resolved_generated_keys':len(expected),
            'executable_filename_verified':True,'game_executed':False,
            'mods_csv_sha256':hashlib.sha256((target/'config/mods.csv').read_bytes()).hexdigest()}
