"""Optional 1937 appointment agendas for ten documented source-roster people.

These are alternate policies, not claims about their historical appointments.
Source political events and existing appointment IDs are retained.
"""
# id, source appointment, personality id, trait, name, description, commands
APPOINTMENTS=[
 (286121,50063,1210,'jx materials first','Materials before expansion',
  'Domestic resources +8 percent; consumer-goods requirement +3 percent. This improves output, not trade imports.',
  [('resource','all',None,.08),('production','consumer',None,.03)]),
 (286122,50066,1211,'jx civil construction','Ports, railways and factories',
  'Infrastructure construction time -12 percent and factory time -5 percent; naval construction time +4 percent.',
  [('province','infra','time',-.12),('province','ic','time',-.05),('unit','navy','time',.04)]),
 (286123,50067,1212,'jx army workshops','Army workshops',
  'Supply production +10 percent; naval construction cost +5 percent.',
  [('production','supplies',None,.10),('unit','navy','cost',.05)]),
 (286124,50050,1213,'jx commercial diplomacy','Trade before commitments',
  'Diplomatic mission cost -15 percent; alliance acceptance chance -5 points. This changes neither current wars nor alliances.',
  [('diplomacy_cost','all',None,-.15),('diplomacy_chances','alliance',None,-5)]),
 (286125,50091,1214,'jx civilian bargain','A civilian bargain',
  'Consumer-goods requirement -5 percent; supply production -3 percent.',
  [('production','consumer',None,-.05),('production','supplies',None,-.03)]),
 (286126,50118,1215,'jx technical intelligence','Naval technical intelligence',
  'Naval research time -4 percent; aircraft research time +2 percent.',
  [('research','naval','time',-.04),('research','aircraft','time',.02)]),
 (286127,50149,1216,'jx heavy fleet','Heavy-gun fleet',
  'Battleship and battlecruiser attack +5 percent; carrier construction time +5 percent.',
  [('unit','battleship','attack',.05),('unit','battlecruiser','attack',.05),('unit','carrier','time',.05)]),
 (286128,50169,1217,'jx carrier concentration','Carrier concentration',
  'Carrier construction time -6 percent and organisation +3 percent; battleship construction time +8 percent.',
  [('unit','carrier','time',-.06),('unit','carrier','organisation',.03),('unit','battleship','time',.08)]),
 (286129,50153,1218,'jx fighter priority','Fighters over the fleet',
  'Interceptor construction cost -6 percent and organisation +3 percent; naval-bomber construction cost +4 percent.',
  [('unit','interceptor','cost',-.06),('unit','interceptor','organisation',.03),('unit','naval_bomber','cost',.04)]),
 (286130,50144,1219,'jx army cohesion','Army cohesion',
  'Land organisation +4 percent; national unit supply consumption +4 percent.',
  [('unit','land','organisation',.04),('supply_consumption',None,None,.04)]),
]

POSITIONS={'Head of Government':'HeadOfGovernment','Foreign Minister':'ForeignMinister',
           'Minister of Armament':'ArmamentMinister','Minister of Security':'MinisterOfSecurity',
           'Head of Military Intelligence':'MinisterOfIntelligence','Chief of Staff':'ChiefOfStaff',
           'Chief of Army':'ChiefOfArmy','Chief of Navy':'ChiefOfNavy','Chief of Air Force':'ChiefOfAir'}


def personalities(source,read):
    rows={int(r[0]):r for l in read(source/'db/ministers/ministers_jap.csv').splitlines()
          if (r:=l.split(';'))[0].isdigit()}
    return [(trait,pid,POSITIONS[rows[sid][1]],name,desc,commands)
            for mid,sid,pid,trait,name,desc,commands in APPOINTMENTS]


def rows(source,read):
    base={int(r[0]):r for l in read(source/'db/ministers/ministers_jap.csv').splitlines()
          if (r:=l.split(';'))[0].isdigit()}
    out=[]
    for mid,sid,pid,trait,name,desc,commands in APPOINTMENTS:
        r=base[sid].copy();r[0]=str(mid);r[3]='1937';r[4]=str(min(1951,int(r[4]),int(r[5])))
        # PA lies beside both the prewar cabinet and later FA government.
        # These are optional alternate appointments, never automatic replacements.
        r[6]='PA';r[7]=trait
        assert r[9].lower()!='unknownminister' and int(r[4])>=1937
        out.append(r)
    return out
