"""Protect finite paid US imports without changing rates, costs or duration."""
import re
from catalog import EVENTS,Action,event,cmd,flag,active

REPORT={}
CLOSED='PAID_US_IMPORTS_CLOSED'


def apply():
    if REPORT:return REPORT
    from build import parse,get,serialise
    before={e.key:e.id for e in EVENTS};rows=[]
    for e in list(EVENTS):
        if e.module!='early' or not e.decision:continue
        changed=False
        for i,a in enumerate(e.actions):
            for j,text in enumerate(list(a.commands)):
                node=parse(text)
                if get(node,'type')!='trade' or get(node,'which')!='USA' or get(node,'where')!='JAP':continue
                node=[(k,'1' if k=='value' else v) for k,v in node]
                if get(node,'value') is None:node.append(('value','1'))
                a.commands[j]=serialise(node)
                marker='PAID_US_'+e.key.upper()
                a.commands.append(flag(marker))
                a.gate+=' NOT = { flag = JX_'+CLOSED+' embargo = { country = USA country = JAP value = 1 } embargo = { country = JAP country = USA value = 1 } }'
                rows.append(dict(event=e.key,choice=i,marker=marker,days=int(get(node,'when')),
                                 oil=float(get(node,'oil',0)),metal=float(get(node,'metal',0)),
                                 supplies=float(get(node,'supplies',0)),money=float(get(node,'money',0))))
                changed=True
        if changed:
            e.desc=re.sub(r' This is an ordinary cancellable trade:.*?Oil over the engine limit still decays\.','',e.desc)
            e.desc+=' These are fixed-term contracts. Deliveries and payments continue until the stated expiry; war or an embargo ends American trade. Storage losses still apply.'
    assert rows,'No paid American imports were found'
    markers=sorted({r['marker'] for r in rows})
    purchased='OR = { '+' '.join('flag = JX_'+m for m in markers)+' }'
    closure=active()+' exists = USA '+purchased+' NOT = { flag = JX_'+CLOSED+' } OR = { war = { country = JAP country = USA } embargo = { country = USA country = JAP value = 1 } embargo = { country = JAP country = USA value = 1 } event = 2049026 }'
    event('paid_us_imports_end','American deliveries stop',
          'War or an embargo has ended American trade with Japan. The fuel and metal contracts stop, along with their daily payments. Their earlier handling fees are spent. No replacement imports are granted.',
          gate=closure,offset=1,actions=[Action('Acknowledge the loss of American supplies',
              [cmd('end_trades',which='USA',where='JAP'),flag(CLOSED)],gate=closure,chance=100)],
          module='purchase_reliability',art='diplomacy',
          purpose='End protected paid imports on war or embargo; never renew expired contracts.')
    assert all(next(e.id for e in EVENTS if e.key==k)==v for k,v in before.items())
    REPORT.update(contracts=rows,closed_flag=CLOSED,old_ids=before,events=len(EVENTS))
    return REPORT
