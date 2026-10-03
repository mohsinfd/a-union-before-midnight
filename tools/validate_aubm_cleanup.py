"""Validate the emitted overlay and record exactly which bytes were checked.

This is script/asset validation, never an assertion of DH engine playtesting.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import unittest
from PIL import Image
from build_aubm_cleanup import ROOT,OUTPUT,actions,body
from dh_save_spans import parse,Node,walk
from validate_v4 import KNOWN_COMMANDS,invalid_event_action_keys


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    patterns=['test_aubm_cleanup.py','test_aubm_shared_withdrawal.py','test_aubm_liberator*.py','test_aubm_siam_settlement.py',
              'test_aubm_context_guards.py','test_aubm_stock_settlement_guard.py',
              'test_aubm_command_reserve.py','test_aubm_menu_safety.py']
    suite=unittest.TestSuite()
    for pattern in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tools'),pattern=pattern))
    tested=unittest.TextTestRunner(verbosity=1).run(suite)
    if not tested.wasSuccessful():raise SystemExit('Cleanup regression suite failed; no deployment')
    manifest=json.loads((OUTPUT/'manifest.json').read_text())
    event_map={};new_edges=[];long_text=[];commands=Counter()
    from aubm_cleanup_presentation import audit
    presentation_issues=[]
    for rel,hashes in manifest['files'].items():
        p=OUTPUT/'mod'/rel;assert sha(p)==hashes['compiled'],rel
        text=p.read_bytes().decode('latin1');assert not invalid_event_action_keys(text),rel
        if hashes['origin']=='repository':presentation_issues.extend(rel+': '+x for x in audit(text))
        for ev in parse(text).all('event'):
            eid=int(ev.get('id'));assert eid not in event_map,('Duplicate ID',eid)
            aa=[]
            for af in actions(ev):
                cs=[]
                for c in af.value.all('command'):
                    typ=c.get('type');commands[typ]+=1
                    # Stock scripts have their own broader command vocabulary.
                    if hashes['origin']=='repository':assert typ in KNOWN_COMMANDS,(eid,typ)
                    cs.append(body(text,c))
                    if typ in ('event','trigger') and c.get('which'):
                        new_edges.append({'from':eid,'to':int(c.get('which')),'choice':af.value.get('name'),'gate':body(text,af.value.get('trigger')),'command_gate':body(text,c.get('trigger'))})
                aa.append({'name':af.value.get('name'),'gate':body(text,af.value.get('trigger')),'commands':cs})
            if len(ev.get('desc',''))>500:long_text.append({'id':eid,'module':rel,'bytes':len(ev.get('desc',''))})
            event_map[eid]={'module':rel,'country':ev.get('country'),'name':ev.get('name'),
                'decision':body(text,ev.get('decision')),'trigger':body(text,ev.get('trigger')),
                'description':ev.get('desc'),'actions':aa}
    # No generated internal callback may point at a missing newly reserved ID.
    missing=[e for e in new_edges if 9297000<=e['to']<=9297299 and e['to'] not in event_map]
    assert not missing,missing
    if presentation_issues:
        (OUTPUT/'presentation-errors.json').write_text(json.dumps(presentation_issues,indent=2)+'\n')
        raise ValueError(f'{len(presentation_issues)} compiled presentation errors: {presentation_issues[:12]}')
    (OUTPUT/'presentation-errors.json').write_text('[]\n')
    pictures=list((OUTPUT/'mod/gfx/interface/pics').glob('aubm_reserve_*.bmp'))
    assert len(pictures)==48
    for p in pictures:
        with Image.open(p) as im:assert im.size==(36,50) and im.mode=='RGB' and im.format=='BMP',p
    _,mapping=__import__('aubm_reserve_portraits').roster((ROOT/'mod/db/leaders/india.csv').read_bytes())
    compiled_roster=(OUTPUT/'mod/db/leaders/india.csv').read_bytes()
    expected,_=__import__('aubm_reserve_portraits').roster((ROOT/'mod/db/leaders/india.csv').read_bytes())
    assert expected==compiled_roster
    assert len(mapping)==375
    record={'build':'27-CLEANUP1','script_tests_passed':tested.testsRun,'engine_playtested':False,'presentation_errors':0,
        'manifest_sha256':sha(OUTPUT/'manifest.json'),'compiled_events':len(event_map),
        'event_links':len(new_edges),'portrait_files':48,'reserve_officers':375,
        'remaining_long_descriptions':long_text,
        'payload_hashes':{p.relative_to(OUTPUT/'mod').as_posix():sha(p) for p in (OUTPUT/'mod').rglob('*') if p.is_file()}}
    (OUTPUT/'event-flow.json').write_text(json.dumps({'events':event_map,'edges':new_edges},indent=2)+'\n',encoding='utf8')
    (OUTPUT/'validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in record.items() if k not in ('remaining_long_descriptions','payload_hashes')},indent=2))
    print('Remaining over-500-byte descriptions (reported, not silently truncated):',len(long_text))


if __name__=='__main__':main()
