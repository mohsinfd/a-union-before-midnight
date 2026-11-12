"""Map-checked initial supply routes, paid from existing convoy reserves."""
import csv,struct
from collections import deque
from audit_japan_baseline import parse,get,getall

def values(n,k):return [v for _,v in get(n,k,[])]
def put(n,k,v):
    n[:]=[(key,value) for key,value in n if key!=k];n.append((k,str(v)))

class Map:
    def __init__(self,game):
        root=game/'map/Map_1'
        self.rows={int(r['Id']):r for r in csv.DictReader((root/'Province.csv').read_text(encoding='latin1').splitlines(),delimiter=';') if r['Id'].isdigit()}
        n=max(self.rows)+1;raw=(root/'adjacent.tbl').read_bytes();ix=struct.unpack_from('<'+str(n+1)+'I',raw)
        start=4*(n+1);assert len(raw)==start+12*ix[-1]
        self.adj={p:{struct.unpack_from('<I',raw,start+12*i)[0] for i in range(ix[p],ix[p+1])} for p in range(n)}
        self.sea={p for p,r in self.rows.items() if r['Terrain']=='Ocean'}
        self.land={p:set(q for q in ns if q not in self.sea) for p,ns in self.adj.items() if p not in self.sea}
        # The installed map's special land/strait links supplement geometry.
        for r in csv.DictReader((root/'adj-defs.csv').read_text(encoding='latin1').splitlines(),delimiter=';'):
            try:a,z=int(r['From']),int(r['To'])
            except (ValueError,KeyError):continue
            if a not in self.land or z not in self.land:continue
            if r['Type'].lower()=='impassable':
                self.land[a].discard(z);self.land[z].discard(a)
            elif r['Type'].lower() in ('sea','river'):
                self.land[a].add(z);self.land[z].add(a)
    def component(self,start,allowed):
        seen={start};todo=[start]
        while todo:
            p=todo.pop()
            for q in self.land.get(p,()):
                if q in allowed and q not in seen:seen.add(q);todo.append(q)
        return seen
    def port(self,p):return self.rows[p]['Port Allowed']=='1'
    def route(self,start,end):
        assert self.port(start) and self.port(end)
        # Respect the actual port entrance rather than any adjacent sea tile.
        a=int(self.rows[start]['Port Seazone']);z=int(self.rows[end]['Port Seazone'])
        assert a in self.sea and z in self.sea and a in self.adj[start] and z in self.adj[end]
        prev={a:None};todo=deque([a])
        while todo and z not in prev:
            p=todo.popleft()
            for q in sorted(self.adj[p]&self.sea):
                if q not in prev:prev[q]=p;todo.append(q)
        assert z in prev,(start,end)
        path=[z]
        while prev[path[-1]] is not None:path.append(prev[path[-1]])
        path=[start]+list(reversed(path))+[end]
        assert all(y in self.adj[x] for x,y in zip(path,path[1:]))
        return path

def supply_routes(root,game):
    cs={get(c,'tag'):c for c in getall(root,'country')};j=cs['JAP'];mp=Map(game)
    globaldata=get(root,'globaldata');groups=[v for k,v in globaldata if k in ('alliance','allies','axis','comintern')]
    partners=next(set(values(g,'participant')) for g in groups if 'JAP' in values(g,'participant'))
    allowed={int(p) for tag in partners for p in values(cs[tag],'controlledprovinces')}
    controlled={p:tag for tag,c in cs.items() for p in map(int,values(c,'controlledprovinces'))}
    owned={p:tag for tag,c in cs.items() for p in map(int,values(c,'ownedprovinces'))}
    provinces={int(get(p,'id')):p for p in getall(root,'province')}
    guards=[int(get(f,'location')) for f in getall(j,'landunit') if any(get(get(d,'id'),'type')=='28632' for d in getall(f,'division'))]
    # Validate this map decoder against every pre-existing saved naval path.
    for c in cs.values():
        for route in getall(c,'convoy'):
            path=list(map(int,values(route,'path')))
            assert all(z in mp.adj[a] for a,z in zip(path,path[1:])),('existing route',path)
    added=[];covered=[];seen=set();native_ids={tuple(get(get(q,'id'),k) for k in ('type','id')) for c in cs.values() for q in getall(c,'convoy')}
    for p in guards:
        if p in seen:continue
        area=mp.component(p,allowed);seen|=area
        if int(get(j,'capital')) in area:
            covered.append({'guard_province':p,'reason':'home land/strait connection'});continue
        owner='JAP' if any(controlled.get(q)=='JAP' for q in area) else controlled[p]
        c=cs[owner]
        # A puppet island without a Japanese-controlled province must receive
        # its own owner's convoy; Japanese control is never fabricated.
        assert owner=='JAP' or owner in partners and get(c,'puppet')=='JAP',owner
        existing=[q for q in getall(c,'convoy') if get(q,'supplies')=='yes' and int(values(q,'path')[-1]) in area]
        if existing:
            covered.append({'guard_province':p,'owner':owner,'reason':'existing supply route','destination':int(values(existing[0],'path')[-1])});continue
        ports=[q for q in area if controlled.get(q)==owner and mp.port(q)]
        assert ports,('No usable local supply port',area)
        def port_score(q):
            return float(get(get(provinces.get(q,[]),'naval_base',[]),'size',0)),q==p,-q
        dest=max(ports,key=port_score)
        if owner=='JAP':origin=1560
        else:
            home=mp.component(int(get(c,'capital')),set(map(int,values(c,'controlledprovinces'))))
            choices=[q for q in home if owned.get(q)==owner and mp.port(q)]
            assert choices,('No capital-connected donor port',owner)
            origin=min(choices,key=lambda q:(len(mp.route(q,dest)),q))
        path=mp.route(origin,dest)
        # Initial reserve assignment includes a conservative margin. Native
        # auto-management remains responsible for subsequent recalculation.
        assigned=max(8,4*(len(path)-2)+4)
        reserve=int(get(c,'transports'));assert reserve>=assigned,(owner,reserve,assigned)
        put(c,'transports',reserve-assigned)
        serial=len(added)+1
        assert ('28634',str(serial)) not in native_ids
        route=[('id',[('type','28634'),('id',str(serial))]),('transports',str(assigned)),
               ('oil','yes'),('metal','no'),('energy','no'),('rare_materials','no'),('supplies','yes'),
               ('path',[(None,str(q)) for q in path])]
        c.append(('convoy',route))
        added.append({'owner':owner,'from':origin,'to':dest,'transports':assigned,'path':path,'supplies':True,'oil':True,'served_guard_provinces':sorted(set(guards)&area)})
    # Prove that every guard has a home connection or an explicit supply route
    # through its actual administrative owner, including Hainan.
    for p in guards:
        area=mp.component(p,allowed)
        if int(get(j,'capital')) in area:continue
        owners={controlled[q] for q in area if controlled.get(q) in partners}
        assert any(get(q,'supplies')=='yes' and int(values(q,'path')[-1]) in area for tag in owners for q in getall(cs[tag],'convoy')),p
    return {'added':added,'already_covered':covered,'guard_locations_checked':len(guards),'source':'installed map adjacency and port entrances; saved native convoy schema','delivery_engine_tested':False}
