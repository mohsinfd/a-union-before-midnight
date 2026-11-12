"""Paid Japanese military programmes buy time savings, not unfunded queues."""
import re
from catalog import EVENTS,cmd,flag

REPORT=[]
NAMES={'marine':'Marine','d_10':'Naval Base Force','d_11':'Jungle Light Infantry','d_12':'Special Naval Landing Division',
       'd_01':'Imperial Guards','carrier':'fleet carrier','light_carrier':'light carrier',
       'destroyer':'destroyer','light_cruiser':'light cruiser','submarine':'submarine',
       'naval_bomber':'naval bomber','tactical_bomber':'tactical bomber','multi_role':'multirole fighter',
       'interceptor':'interceptor','paratrooper':'paratrooper','transport_plane':'transport aircraft',
       'motorized':'motorised infantry','armor':'armour','bergsjaeger':'mountain infantry',
       'infantry':'infantry','garrison':'garrison','cavalry':'cavalry','engineer':'engineer brigade'}


def apply(source,names,read,parse,get,getall,num):
    if REPORT:return
    import specialist_units
    by={e.key:e for e in EVENTS};changed={}
    for e in list(EVENTS):
        match=re.fullmatch(r'(.+)_finish_(\d+)',e.key)
        if e.country!='JAP' or not match:continue
        parent=by[match[1]];option=int(match[2]);a=e.actions[0]
        old=[parse(c) for c in a.commands]
        if not any(get(c,'type')=='build_division' for c in old):continue
        marker='PRODUCTION_'+parent.key+'_'+str(option)
        benefits=[];commands=[];seen=set();orders=[]
        useful=[c for c in old if get(c,'type') not in {'setflag','clrflag'}]
        old_eight=bool(useful) and all(get(c,'type')=='build_division' for c in useful)
        for text,c in zip(a.commands,old):
            typ=get(c,'type')
            if typ not in {'build_division','build_brigade','add_brigade'}:
                commands.append(text);continue
            unit=get(c,'which') if typ=='build_division' else get(c,'value')
            orders.append({'unit':unit,'count':int(num(c,'when',1)) if typ!='add_brigade' else 1})
            if unit in seen:continue
            seen.add(unit)
            models=specialist_units.models(unit) if unit in specialist_units.CLASSES else getall(parse(read(source/'db/units'/('divisions' if typ=='build_division' else 'brigades')/(unit+'.txt'))),'model')
            days=min(30,max(1,int(num(models[0],'buildtime')*.25)))
            if parent.key=='snlf' and unit=='d_12':days=60 if option==0 else 30
            benefits.append({'unit':unit,'name':NAMES.get(unit,unit.replace('_',' ')),
                             'days':days,'previous_eight_days':8 if old_eight else 0})
        commands=[cmd('build_time',which=b['unit'],when='on_upgrade',value=-b['days']) for b in benefits]+commands+[flag(marker)]
        a.commands=commands
        label='Speed up '+', '.join(b['name'] for b in benefits)
        parent.actions[option].name=label if len(label)<=72 else 'Improve construction for these forces'
        e.title=parent.title+' - production improvement ready'
        e.desc='Basic construction time is reduced by '+', '.join(str(b['days'])+' days for '+b['name'] for b in benefits)+'. Normal research, policy and gearing modifiers still apply. Place your own orders when ready; each needs normal IC and manpower. This event creates no units or production lines. The setup bill was paid when work began.'
        REPORT.append({'parent':parent.key,'finish':e.key,'option':option,'marker':'JX_'+marker,
                       'benefits':benefits,'old_orders':orders})
        changed[parent.key]=parent
    # Rewrite both alternatives using their actual awards. Do not leave the old
    # number-of-divisions promise next to a construction discount.
    def summary(finish):
        parts=[]
        for text in finish.actions[0].commands:
            c=parse(text);typ=get(c,'type');u=get(c,'which');v=get(c,'value')
            if typ=='build_time':parts.append(NAMES.get(u,str(u).replace('_',' '))+': basic construction time reduced by '+str(-num(c,'value'))+' days')
            elif typ=='gain_tech':parts.append('the listed research blueprint')
            elif typ=='tc_mod':parts.append(str(v)+' percent more transport capacity')
            elif typ=='max_organization':parts.append(str(v)+' more organisation for '+NAMES.get(u,str(u)))
            elif typ=='transport_pool':parts.append(str(v)+' convoy transports')
            elif typ=='escort_pool':parts.append(str(v)+' convoy escorts')
            elif typ=='construct':parts.append(str(v)+' '+str(u).replace('_',' ')+' at '+names.get(int(get(c,'where')),str(get(c,'where'))))
            elif typ=='activate_unit_type':parts.append('unlock '+NAMES.get(u,str(u)))
            elif typ=='new_model':parts.append('unlock model '+str(v)+' of '+NAMES.get(u,str(u)))
            elif typ=='trigger' and 'activate_d_12' in text:parts.append('unlock Special Naval Landing Divisions')
            elif typ in {'supplies','oilpool','manpowerpool'}:parts.append(str(v)+' '+{'oilpool':'oil','manpowerpool':'manpower'}.get(typ,typ))
        return '; '.join(dict.fromkeys(parts))+'.'
    for key,p in changed.items():
        prices={get(parse(c),'type'):-num(parse(c),'value') for c in p.actions[0].commands if get(parse(c),'type') in {'money','supplies'}}
        delay=next(int(get(parse(c),'when')) for c in p.actions[0].commands if get(parse(c),'type')=='event')
        choices=[by.get(key+'_finish_'+str(i)) for i in range(2)]
        p.desc='Invest in training, tools and production methods for the forces you want to build. Choose the improvement below. Unit construction stays in your hands; this programme adds no formations or queue entries.\n\n'+ '\n\n'.join(('First choice: ' if i==0 else 'Alternative: ')+summary(e) for i,e in enumerate(choices) if e)
        p.desc+='\n\nSetup costs '+str(int(prices.get('money',0)))+' money and '+str(int(prices.get('supplies',0)))+' supplies. Work takes '+str(delay)+' days. Each selected improvement is awarded once. You may delay or dismiss the proposal.'
        if key=='snlf':
            p.desc='Build a separate naval assault force. SNLF divisions use 12 manpower, lighter supply and transport loads, and better landing modifiers. They have less firepower and defence than a full Marine division.\n\n'+p.desc
            p.actions[0].name='Expand SNLF production'
            p.actions[1].name='Train assault troops and engineers'
