"""L4 additions appended after the old catalogue to preserve every existing ID."""
from catalog import EVENTS,Action,event,cmd,flag,fire,cond
from specialist_units import activation


ACTIVATION_ID=28601656  # First free ID after the complete R5 L3 catalogue.


def configure():
    e=next(e for e in EVENTS if e.key=='snlf')
    e.gate+=' technology = 1590'
    e.art='snlf'
    for i in range(2):
        finish=next(e for e in EVENTS if e.key=='snlf_finish_'+str(i))
        finish.art='snlf'
        finish.actions[0].commands=[c.replace('which = marine','which = d_12') for c in finish.actions[0].commands]
        finish.actions[0].commands.insert(0,fire('activate_d_12'))
        if i==1:finish.actions[0].commands.append(cmd('max_organization',which='d_12',value=3))
    rehearsal=next(e for e in EVENTS if e.key=='landing_rehearsal_finish_0')
    rehearsal.actions[0].commands += [flag('SNLF_REHEARSAL'),
        cond('flag = JX_SNLF_FORCE',cmd('river_attack',which='d_12',value=3))]


def append():
    e=event('activate_d_12','Special Naval Landing Divisions can now be recruited','',
          triggered=True,actions=[Action('Open SNLF recruitment',activation('d_12')+[cond('flag = JX_SNLF_REHEARSAL',cmd('river_attack',which='d_12',value=3))],gate='NOT = { flag = JX_SNLF_FORCE }',chance=100),
                                  Action('Recruitment is already open',[],gate='flag = JX_SNLF_FORCE')],
          module='snlf_cabinet',art='snlf',purpose='Once-only activation and catch-up. Existing IDs and units are preserved.')
    assert e.id==ACTIVATION_ID,'Old catalogue size changed; review ID compatibility'


configure()
