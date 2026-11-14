"""Evidence-checked, separate-save repair for the February 1934 Nagoya failure."""
import hashlib,json,re,shutil
import build as b


def run():
    folder=b.TARGET/'scenarios/save games';source=folder/'autosave.eug'
    raw=source.read_bytes();text=raw.decode('latin1');original=text
    assert 'year = 1934' in text[:400] and 'month = february' in text[:400]
    assert 'We went with Okay in Rural recovery: workshops or reserve rolls? - work completed.' in text
    changes=[]
    def change(old,new,label):
        nonlocal text
        assert text.count(old)==1,(label,text.count(old))
        text=text.replace(old,new,1);changes.append((old,new,label))
    for key,old,new in [('DONE',0,1),('PENDING',1,0),('SELECTED_0',1,0)]:
        m=re.search(r'JX_prewar_rural_works_'+key+r' = '+str(old)+r'\b',text);assert m
        change(m[0],m[0][:-1]+str(new),'Close Nagoya '+key)
    assert not re.search(r'event = \{ tag = JAP id = 2860174[01] hour =',text)
    m=re.search(r'(?m)^province = \{[ \t]*\r?\n[ \t]*id = 1557\b',text);assert m
    # The inspected province has no saved IC override: it inherits five IC.
    end=text.find('\nprovince =',m.end());chunk=text[m.start():end]
    assert not re.search(r'\bic\s*=',chunk)
    import csv
    rows=csv.DictReader(b.read(b.GAME/'map/Map_1/Province.csv').splitlines(),delimiter=';')
    base=float(next(r for r in rows if r['Id']=='1557')['IC']);assert base==5
    line=re.search(r'id = 1557[^\n]*\n',chunk)[0]
    ending='\r\n' if '\r\n' in text else '\n'
    newchunk=chunk.replace(line,line+'\tic = { size = 8 current_size = 8 } '+ending,1)
    change(chunk,newchunk,'Deliver the paid three fully working factories, five to eight')
    registry='event = "db\\events\\japan_rising\\timer_reliability.txt"'
    assert registry not in text
    text+=ending+registry+ending
    # Prove that reversing only the documented edits reproduces every byte.
    reverse=text[:-(len(ending+registry+ending))]
    for old,new,label in reversed(changes):
        assert reverse.count(new)==1,label
        reverse=reverse.replace(new,old,1)
    assert reverse==original
    backup=b.HERE/'backups/before_R15_1_timer_repair/autosave.eug'
    if backup.exists():assert backup.read_bytes()==raw
    else:backup.write_bytes(raw)
    target=folder/'JAPAN_R15_1_NAGOYA_REPAIRED_1934_FEB_1.eug'
    if target.exists():assert target.read_bytes()==text.encode('latin1')
    else:target.write_bytes(text.encode('latin1'))
    cfg=source.with_suffix('.eug.cfg')
    if cfg.exists():shutil.copy2(cfg,target.with_suffix('.eug.cfg'))
    assert source.read_bytes()==raw
    report=dict(source=str(source),repaired_save=str(target),source_sha256=hashlib.sha256(raw).hexdigest(),
                repaired_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                date='1934-02-01',province=1557,ic_before=5,ic_after=8,
                changes=[label for _,_,label in changes]+['Register repaired timing module in this saved campaign'],
                other_gameplay_bytes_unchanged=True,source_untouched=True,game_run=False)
    (b.HERE/'R15_1_SAVE_REPAIR.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
