"""Explicit human-Japan replacement reserves; retain the existing event IDs."""
from catalog import EVENTS,Action,cmd,flag

APPLIED=False
RESERVES=(160,140,120)
DAILY=0.65
YEARS=5


def apply():
    global APPLIED
    if APPLIED:return
    APPLIED=True
    by={e.key:e for e in EVENTS}
    for i,(key,amount) in enumerate(zip(('national_callup_1941','national_callup_1942','national_callup_1943'),RESERVES)):
        e=by[key]
        commands=[]
        for c in e.actions[0].commands:
            if 'type = manpowerpool ' in c:c=cmd('manpowerpool',value=amount)
            elif 'type = free_manpower ' in c:c=cmd('free_manpower',value=DAILY)
            commands.append(c)
        e.actions[0].commands=commands
        e.actions[0].gate=f'year = {e.year} '+e.gate
        e.actions.append(Action('This call-up no longer applies',[],gate='NOT = { AND = { '+e.actions[0].gate+' } }'))
        if i==0:
            e.desc=f'The wider war releases {amount} manpower for replacements and new formations. A five-year recruitment programme adds another {DAILY:g} manpower daily, about {DAILY*365:.0f} per year. Wartime IC rises by 12%. Fund normal reinforcements and unit construction yourself. These are recruits, not ready divisions. The native mobilisation laws still govern their own effects.'
        else:
            e.desc=f'A further {amount} manpower is available for replacements and new formations. This wave needs continued war, its stated calendar year, and at least 300 days since the previous call-up. No units are created and no production orders are inserted.'
            if i==2:e.desc+=' Wartime IC also rises by another 8%.'
    e=by['national_mobilization_end']
    e.desc=f'The five-year recruitment supplement has ended. Its extra {DAILY:g} daily manpower is removed. Native national recruitment and mobilisation laws continue to apply. The reserve waves already granted are retained.'
    e.actions[0].commands=[cmd('free_manpower',value=-DAILY) if 'type = free_manpower ' in c else c for c in e.actions[0].commands]
    e.actions.append(Action('The recruitment supplement has already ended',[],gate='flag = JX_NATIONAL_MOBILIZATION_ENDED'))
