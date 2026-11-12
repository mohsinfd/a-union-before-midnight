"""Complete packed DH garrison records for save migrations.

Scenario construction calculates model stats; saved-game construction does not.
Use an engine-written same-country garrison as the layout/default oracle, then
apply the installed model and country's recorded upgrade modifiers explicitly.
"""
import copy,math
from audit_japan_baseline import parse,get,getall,num

def vals(n,k):return [v for _,v in get(n,k,[])]
def put(n,k,v):
    n[:]=[(key,value) for key,value in n if key!=k];n.append((k,v))
def packed(values):return [(None,str(v)) for v in values]
def model(target,kind,index):
    branch='brigades' if kind=='artillery' else 'divisions'
    return getall(parse((target/'db/units'/branch/(kind+'.txt')).read_text(encoding='latin1')),'model')[index]

def oracle(country,target):
    candidates=getall(country,'landdivision')+[d for f in getall(country,'landunit') for d in getall(f,'division')]
    for d in candidates:
        m=vals(d,'mod');a=vals(d,'all');land=vals(d,'land')
        if not(m and m[0]=='9' and len(a)==17 and len(land)==13 and float(a[7])>0 and float(land[4])>0):continue
        # Validate the field mapping against the actual native record, including
        # its artillery. Unknown brigades must never be silently approximated.
        base=model(target,'garrison',int(m[2]));up=get(get(country,'upgrade',[]),'garrison',[])
        brig=vals(d,'brig');extra=[];bu=[]
        if brig and brig[0]!='0':
            assert brig[0]=='1' and all(v=='0' for v in brig[1:5]),'Unsupported garrison oracle attachment'
            extra=model(target,'artillery',int(brig[5]));bu=get(get(country,'upgrade',[]),'artillery',[])
        checks=[(float(a[3]),num(base,'defaultorganisation')+num(up,'defaultorganisation')),
                (float(a[4]),num(base,'morale')+num(up,'morale')),
                (float(a[7]),num(base,'supplyconsumption')+num(up,'supplyconsumption')+num(extra,'supplyconsumption')+num(bu,'supplyconsumption'))]
        for i,key in ((0,'defensiveness'),(1,'toughness'),(2,'softness'),(3,'suppression'),(4,'softattack'),(5,'hardattack'),(6,'transportweight')):
            checks.append((float(land[i]),num(base,key)+num(up,key)+num(extra,key)+num(bu,key)))
        assert all(math.isclose(actual,wanted,abs_tol=.001) for actual,wanted in checks),checks
        return d
    raise AssertionError('No validated, nonzero native garrison profile in this country')

def complete(country,definition,target,restore=False):
    native=oracle(country,target);out=copy.deepcopy(native)
    current=vals(definition,'all');given_mod=vals(definition,'mod')
    index=int(given_mod[2]) if given_mod else int(get(definition,'model',4))
    base=model(target,'garrison',index);up=get(get(country,'upgrade',[]),'garrison',[])
    cap=float(current[1]) if current else float(get(definition,'max_strength',25))
    strength=cap if restore else (float(current[0]) if current else float(get(definition,'strength',cap)))
    assert 0<strength<=cap<=100
    for key in ('id','name'):put(out,key,copy.deepcopy(get(definition,key)))
    default_flags=(int(get(native,'flag'))&~3)|(1 if get(definition,'dormant')=='yes' else 0)|(2 if get(definition,'locked')=='yes' else 0)
    put(out,'flag',str(get(definition,'flag',default_flags)))
    m=given_mod[:] if given_mod else ['9','9',str(index),'0','9',str(index+1),'0','0','0']
    m[0]=m[1]=m[4]='9';m[2]=str(index);m[3]='0';m[5]=str(index+1)
    put(out,'mod',packed(m));out[:]=[(k,v) for k,v in out if k!='brig']
    a=[float(x) for x in vals(native,'all')]
    a[0]=strength;a[1]=cap;a[3]=num(base,'defaultorganisation')+num(up,'defaultorganisation')
    a[2]=min(float(current[2]) if current else 30,a[3])
    a[4]=num(base,'morale')+num(up,'morale');a[5]=float(current[5]) if current else 0
    a[6]=float(current[6]) if current else 0
    for i,key in ((7,'supplyconsumption'),(8,'fuelconsumption'),(9,'maxspeed'),(10,'airdefence'),(11,'airattack')):
        a[i]=max(0,num(base,key)+num(up,key))
    a[15]=num(base,'upgrade_cost_factor');a[16]=num(base,'upgrade_time_factor')
    land=[0.0]*13
    for i,key in ((0,'defensiveness'),(1,'toughness'),(2,'softness'),(3,'suppression'),(4,'softattack'),(5,'hardattack'),(6,'transportweight')):
        land[i]=num(base,key)+num(up,key)
    put(out,'all',packed(a));put(out,'land',packed(land))
    assert a[7]>0 and land[0]>0 and land[4]>0 and a[3]>0
    return out

def normalise_detachments(country,target,restore=False):
    """Touch only the explicitly reserved island-detachment identities."""
    count=0
    for kind in ('landdivision','landunit'):
        for obj in getall(country,kind):
            nodes=[obj] if kind=='landdivision' else getall(obj,'division')
            for d in nodes:
                if get(get(d,'id'),'type')!='28632':continue
                assert 1<=int(get(get(d,'id'),'id'))<=31
                d[:]=complete(country,d,target,restore=restore);count+=1
    return count
