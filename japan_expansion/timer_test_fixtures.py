"""Explicit elapsed-state fixtures, replacing preseeded event history in tests."""
def elapsed(world,source,days):
    import timer_reliability
    for row in timer_reliability.REPORT['pairs']:
        if row['source']==source:
            key='JX_'+row['flag']
            if days>=row['days']:world.flags[key]=1
            else:world.flags.pop(key,None)
