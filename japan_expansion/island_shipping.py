"""Finite shipping allowance for the retained local garrisons; no new offers."""
from catalog import EVENTS,cmd,cond,flag,active

APPLIED=False
DONE='ISLAND_SHIPPING_RESERVE_DONE'
RECIPIENTS=('island_muster_b1','base_gaps_b2_apply','haikou_b2_apply')


def apply():
    global APPLIED
    if APPLIED:return
    by_key={e.key:e for e in EVENTS}
    guard=active()+' country = JAP NOT = { flag = JX_'+DONE+' }'
    award=[cond(guard,cmd('transport_pool',which=-1,value=180)),
           cond(guard,cmd('escort_pool',which=-1,value=90)),cond(guard,flag(DONE))]
    explanation=(' The first local-defence call-up also transfers 180 convoy transports and 90 convoy escorts '
                 'to the national shipping pool, once across all these call-ups. They support island supply; '
                 'they are not troop-transport flotillas or combat destroyers. Route allocation remains under convoy management.')
    for key in RECIPIENTS:
        e=by_key[key]
        e.actions[0].commands[-1:-1]=award
        if e.desc:e.desc+=explanation
    by_key['island_callup'].desc+=explanation
    for key in ('merchant_prewar','merchant_prewar_finish_0','merchant_prewar_finish_1'):
        e=by_key[key]
        e.desc=e.desc.replace('120 convoy transports and 25 convoy escorts','160 convoy transports and 40 convoy escorts')
        e.desc=e.desc.replace('70 transports and 60 escorts','100 transports and 80 escorts')
    for key,transports,escorts in (('merchant_prewar_finish_0',160,40),('merchant_prewar_finish_1',100,80)):
        action=by_key[key].actions[0]
        action.commands=[cmd('transport_pool',which=-1,value=transports) if c.startswith('type = transport_pool ') else
                         cmd('escort_pool',which=-1,value=escorts) if c.startswith('type = escort_pool ') else c
                         for c in action.commands]
    APPLIED=True
