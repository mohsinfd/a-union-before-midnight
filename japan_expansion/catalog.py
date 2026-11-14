"""Authoritative Japan expansion event specification and executable event model.

No game files are touched by importing this module. Symbolic @event references
are resolved by the builder, so documentation and script cascades share IDs.
"""
from dataclasses import dataclass, field
import re

VERSION = "JX 1.1 ALPHA 2 R15"
MOD_NAME = "Japan Rising JX1 Alpha2"
BASE_ID = 28600000


@dataclass
class Action:
    name: str
    commands: list[str] = field(default_factory=list)
    gate: str = ""
    chance: int = 0


@dataclass
class Event:
    key: str
    title: str
    desc: str
    country: str = "JAP"
    gate: str = ""
    actions: list[Action] = field(default_factory=list)
    decision: bool = False
    ready: str = ""
    year: int = 1933
    offset: int = 7
    persistent: bool = False
    triggered: bool = False
    art: str = "naval"
    module: str = "opening"
    purpose: str = ""
    id: int = 0
    start_month: str = "january"
    start_day: int = 0


EVENTS: list[Event] = []


def event(key, title, desc, **kwargs):
    assert not any(e.key == key for e in EVENTS), key
    e = Event(key=key, title=title, desc=desc, id=BASE_ID + len(EVENTS) + 1, **kwargs)
    EVENTS.append(e)
    return e


def cmd(kind, **kwargs):
    return "type = " + kind + " " + " ".join(f"{k} = {v}" for k,v in kwargs.items())


def flag(name):
    return cmd("setflag", which="JX_" + name)


def clear(name):
    return cmd("clrflag", which="JX_" + name)


def later(key, days=1, country="JAP"):
    return cmd("event", which="@"+key, where=country, when=days)


def fire(key):
    return cmd("trigger", which="@"+key)


def cond(gate, command):
    return "trigger = { " + gate + " } " + command


def human():
    return "ai = no NOT = { ispuppet = JAP }"


def active():
    return human() + " flag = JX_ACTIVE"


def pacific():
    return "flag = JX_PACIFIC"


def puppet(tag):
    return f"puppet = {{ country = {tag} country = JAP }}"


def control(province, tag="JAP"):
    return f"control = {{ province = {province} data = {tag} }}"


def owned(province, tag="JAP"):
    return f"owned = {{ province = {province} data = {tag} }}"


def war(tag):
    return f"war = {{ country = JAP country = {tag} }}"


def money(value):
    return cmd("money", value=value)


def supplies(value):
    return cmd("supplies", value=value)


def blueprint(tech):
    return cmd("gain_tech", which=tech)


def no_state(key):
    return f"NOT = {{ flag = JX_{key}_DONE flag = JX_{key}_PENDING flag = JX_{key}_WAIT flag = JX_{key}_DISMISSED }}"


def paid_project(key, title, desc, *, year=1933, gate="", money_cost=150,
                 supply_cost=600, days=180, reward=None, alternative=None,
                 art="industry", module="industry", finish_gate=""):
    """Two funded alternatives plus temporary and permanent refusal.

    Completion checks are action gates because scheduled triggered events do not
    reliably obey normal date/trigger conditions. Invalid completion refunds the
    exact upfront payments and clears pending state, without granting rewards.
    """
    alternatives = [("Fund the programme", reward or [])]
    if alternative:
        alternatives.append(alternative)
    actions = []
    for i,(label, rewards) in enumerate(alternatives):
        finish = f"{key}_finish_{i}"
        actions.append(Action(label, [money(-money_cost), supplies(-supply_cost), flag(key+"_PENDING"), later(finish,days)],gate=f"money = {money_cost} supplies = {supply_cost}",chance=100 if i==0 else 0))
        valid = f"flag = JX_{key}_PENDING {finish_gate}"
        acts = [Action("Put the programme to work", rewards + [flag(key+"_DONE"),clear(key+"_PENDING")],gate=valid,chance=100)]
        if finish_gate:
            acts.append(Action("The project cannot finish; return the funds",[money(money_cost),supplies(supply_cost),clear(key+"_PENDING"),flag(key+"_WAIT"),later(key+"_return",90)],gate=f"flag = JX_{key}_PENDING NOT = {{ AND = {{ {finish_gate} }} }}"))
        event(finish,title+" - completed",f"The funded programme is ready. {desc} The payment was made when work began; this event does not charge it again.",actions=acts,triggered=True,art=art,module=module,purpose="Checks pending state and ownership before granting this project's selected reward.")
    actions += [Action("Ask again in three months",[flag(key+"_WAIT"),later(key+"_return",90)]),Action("Drop this proposal permanently",[flag(key+"_DISMISSED")])]
    event(key,title,desc+f"\n\nFunding costs {money_cost} money and {supply_cost} supplies. Work takes {days} days. You can delay or dismiss this proposal even if you cannot fund it.",decision=True,gate=active()+" "+no_state(key)+" "+gate,ready="",year=year,persistent=True,actions=actions,art=art,module=module)
    event(key+"_return",title+" - proposal returns","",triggered=True,actions=[Action("",[clear(key+"_WAIT")])],art=art,module=module,purpose="Hidden cooldown reset; no reward and no route state.")


def country_definition(key, tag, name, capital, gate, *, old_tag=None,
                       bases=(), year=1941, art="asia", extra_desc=""):
    """Recipient-side separate peace: Japan never issues alliance-wide peace.

    Existing enemy government withdraws and ends its own war with Japan, then
    Japan establishes the agreed relationship. Manual-annexation release shares
    the same finalisation and confirmation. Neutral treaty states stay outside
    Japan's alliance. Recipient ownership is checked before any base secession.
    """
    old = old_tag or tag
    states = f"NOT = {{ flag = JX_{key}_SETTLED flag = JX_{key}_PENDING flag = JX_{key}_WAIT flag = JX_{key}_DISMISSED }}"
    colonial = f"OR = {{ {owned(capital)} {war('ENG')} {war('FRA')} {war('U05')} {war('HOL')} }}"
    absent_gate = re.sub(r"lost_national\s*=\s*\{[^}]*\}","",gate)
    existing = f"AND = {{ exists = {old} {war(old)} {gate} }}"
    if old != tag:
        existing += f" AND = {{ NOT = {{ exists = {old} }} exists = {tag} {war(tag)} {gate.replace('country = '+old,'country = '+tag)} }}"
    existence = f"OR = {{ {existing} AND = {{ NOT = {{ exists = {old} exists = {tag} }} {control(capital)} {colonial} {absent_gate} }} }}"
    base_text = ", ".join(str(p) for p in bases) or "no reserved ports"
    description = f"{name} can no longer hold its main centres. A puppet joins Japan's wars and rebuilds local forces. A neutral treaty state stays outside our alliance and grants access.\n\nA base treaty reserves only listed ports already held by Japan: {base_text}. Other land returns to the local government. This settlement does not end Japan's other wars. {extra_desc}"
    choices = [
        Action("Create a puppet and retain the listed naval bases",[flag(key+"_PUPPET"),flag(key+"_BASES"),flag(key+"_PENDING"),later(key+"_prepare")],chance=100),
        Action("Create a puppet; return all local ports",[flag(key+"_PUPPET"),flag(key+"_PENDING"),later(key+"_prepare")]),
        Action("Recognise a neutral state with Japanese access",[flag(key+"_NEUTRAL"),flag(key+"_PENDING"),later(key+"_prepare")]),
        Action("Not yet; ask again in three months",[flag(key+"_WAIT"),later(key+"_return",90)]),
        Action("Keep the occupation; dismiss this offer",[flag(key+"_DISMISSED")])]
    event(key,f"A settlement for {name}",description,decision=True,gate=active()+" "+pacific()+" "+states+" "+existence,ready="",year=year,persistent=True,actions=choices,art=art,module="settlements")
    # Save which ports were genuinely in Japanese hands before peace returns control.
    preparing = [cond(control(p),flag(key+f"_HELD_{p}")) for p in bases]
    preparing += [cond(f"exists = {old}",fire(key+"_withdraw"))]
    if old != tag:
        preparing += [cond(f"NOT = {{ exists = {old} }} exists = {tag} {war(tag)}",fire(key+"_withdraw_existing"))]
        event(key+"_withdraw_existing",f"{name} leaves its former alliance","",country=tag,triggered=True,actions=[Action("",[cond(f"ispuppet = {tag}",cmd("end_puppet")),cmd("leave_alliance",when=1),cmd("peace",which="JAP",value=1)])],module="settlements")
    for owner in ("ENG","FRA","U05","HOL","U02"):
        preparing += [cond(f"NOT = {{ exists = {old} exists = {tag} }} exists = {owner} {war(owner)}",fire(key+"_land_"+owner))]
        event(key+"_land_"+owner,f"{name}: occupied land changes hands","",country=owner,triggered=True,actions=[Action("",[])],module="settlements",purpose=f"Builder fills a checked list of {tag} provinces; only land both owned by {owner} and controlled by JAP can transfer.")
    create_if_absent = cond(f"NOT = {{ exists = {old} exists = {tag} }}",later(key+"_create",1))
    preparing += [create_if_absent,later(key+"_commit",3)]
    event(key+"_prepare",f"Preparing the {name} agreement","",triggered=True,actions=[Action("",preparing,gate=f"flag = JX_{key}_PENDING")],module="settlements",art=art)
    event(key+"_create",f"{name}: establish the local government","",triggered=True,actions=[Action("",[cmd("independence",which=tag,value=1,when=0)],gate=f"flag = JX_{key}_PENDING NOT = {{ exists = {old} exists = {tag} }}")],module="settlements")
    withdrawal = [cond(f"ispuppet = {old}",cmd("end_puppet")),cmd("leave_alliance",when=1),cmd("peace",which="JAP",value=1)]
    withdrawal_actions=[Action("Accept the agreed withdrawal",withdrawal,chance=100)]
    if old != tag:
        withdrawal_actions=[Action("Establish the agreed national government",withdrawal+[cmd("country",which=tag)],gate=f"NOT = {{ exists = {tag} }}",chance=100),Action("Unite with the existing local government",withdrawal+[later(key+"_merge",1,tag)],gate=f"exists = {tag}",chance=100)]
    event(key+"_withdraw",f"{name} leaves its former alliance",f"The government withdraws from its former alliance and accepts the Japanese settlement. If the new national government already exists, a follow-up unites the defeated state with it instead of leaving a separate rump country. Otherwise the state changes its country identity. The agreed puppet or neutral relationship follows.",country=old,triggered=True,actions=withdrawal_actions,art=art,module="settlements")
    commits = []
    if old != tag:
        commits += [cond(f"exists = {old} exists = {tag}",fire(key+"_merge"))]
    commits += [cond(f"flag = JX_{key}_PUPPET exists = {tag}",cmd("make_puppet",which=tag)),cond(f"exists = {tag}",cmd("access",which=tag)),cond(f"exists = {tag}",later(key+"_local",1,tag)),later(key+"_verify",3)]
    event(key+"_commit",f"Establishing the {name} agreement","",triggered=True,actions=[Action("",commits,gate=f"flag = JX_{key}_PENDING")],module="settlements",art=art)
    local_commands = [cmd("access",which="JAP"),cond(f"flag = JX_{key}_NEUTRAL",cmd("non_aggression",which=tag,where="JAP",when=1800)),cmd("ai",which='"jx/partner_land.ai"')]
    for p in bases:
        local_commands += [cond(f"flag = JX_{key}_BASES flag = JX_{key}_HELD_{p} {owned(p,tag)}",cmd("secedeprovince",which="JAP",value=p,when=1))]
    local_commands += [cond(f"NOT = {{ flag = JX_{key}_AID_GIVEN }}",supplies(800)),cond(f"NOT = {{ flag = JX_{key}_AID_GIVEN }}",cmd("manpowerpool",value=25)),cond(f"NOT = {{ flag = JX_{key}_AID_GIVEN }}",later(key+"_army",30,tag)),flag(key+"_AID_GIVEN")]
    event(key+"_local",f"{name}: the new agreement",f"The agreed government takes charge. Japan receives military access. Reserved bases transfer only if Japan held them before the settlement and this government owns them. A local supply reserve and an initial army programme help the state defend itself.",country=tag,triggered=True,actions=[Action("Carry out the agreement",local_commands,chance=100)],art=art,module="settlements")
    valid = f"exists = {tag} access = {{ country = {tag} country = JAP }} access = {{ country = JAP country = {tag} }} NOT = {{ {war(tag)} }} OR = {{ AND = {{ flag = JX_{key}_PUPPET {puppet(tag)} }} AND = {{ flag = JX_{key}_NEUTRAL NOT = {{ ispuppet = {tag} alliance = {{ country = JAP country = {tag} }} }} }} }}"
    for p in bases:
        valid += f" OR = {{ NOT = {{ flag = JX_{key}_BASES }} NOT = {{ flag = JX_{key}_HELD_{p} }} {owned(p)} }}"
    event(key+"_verify",f"{name}: check the agreement","",triggered=True,actions=[Action("",[flag(key+"_SETTLED"),clear(key+"_PENDING"),later(key+"_confirmed",1)],gate=valid,chance=100),Action("",[later(key+"_failed",1)],gate=f"NOT = {{ AND = {{ {valid} }} }}")],art=art,module="settlements")
    event(key+"_confirmed",f"{name}: agreement confirmed",f"The agreed government, Japanese access and any reserved Japanese-owned bases have been checked. The local defence programme follows in about a month. Japan's unrelated wars continue.",triggered=True,actions=[Action("The agreement is in force",[flag(key+"_ANNOUNCED")],chance=100)],art=art,module="settlements")
    event(key+"_failed",f"{name}: the agreement needs attention",f"The promised government, access or reserved base did not reach the agreed state. No completion reward has been given. You can retry the same terms or keep the present position and stop this agreement. Aid already delivered will not be paid twice.",triggered=True,actions=[Action("Try to apply the same terms again",[create_if_absent,later(key+"_commit",3)],chance=100),Action("Keep the present position; stop this agreement",[clear(key+"_PENDING"),flag(key+"_DISMISSED")])],art=art,module="settlements")
    event(key+"_return",f"{name}: offer available again","",triggered=True,actions=[Action("",[clear(key+"_WAIT")])],module="settlements")
    army_gate = f"NOT = {{ army = {{ country = {tag} size = 6 }} }} {control(capital,tag)} manpower = 18"
    force = [cmd("manpowerpool",value=-18),cmd("add_corps",which=f'"{name} Defence Command"',value="land",where=capital)]
    force += [cmd("add_division",which=f'"{name} Defence Division {i}"',value="infantry",when=9,where=-50) for i in range(1,4)]
    event(key+"_army",f"{name} builds a defence force",f"Local recruits form three infantry divisions at half strength. They require reinforcement and supplies. An existing army of six or more divisions receives no duplicate formation package.",country=tag,triggered=True,actions=[Action("Form the local defence force",force,gate=army_gate,chance=100),Action("Keep the existing forces",[supplies(200)],gate=f"NOT = {{ AND = {{ {army_gate} }} }}")],art="army",module="settlements")


def build_catalog():
    if EVENTS:
        return EVENTS
    event("welcome",f"Japan Rising - {VERSION}","Japan Rising builds on Blood and Iron. The 1933 diplomatic opening remains historical. Invest in industry, shipping and training; fight China to a clear settlement. After Pearl Harbor, choose your own wars and peace terms.\n\nNew country offers name their borders and bases. Delaying one offer never selects a permanent grand strategy. Start a new 1933 campaign for this build.",gate=human()+" NOT = { flag = JX_ACTIVE }",actions=[Action("Begin the campaign",[flag("ACTIVE")],chance=100)],offset=1,art="naval")
    event("pacific_open","The Pacific war has begun","Pearl Harbor opens the wider campaign. Country settlements, cooperation with Germany and an optional Soviet war now depend on the situation on the map. The Soviet war is not tied to a choice made in 1933.",gate=active()+" NOT = { flag = JX_PACIFIC } OR = { event = 2011025 event = 2049002 AND = { year = 1941 "+war("USA")+" } }",actions=[Action("Prepare for a long war",[flag("PACIFIC")],chance=100)],offset=1,art="pacific")

    paid_project("first_industry","The next industrial investment","Choose shipyard capacity or aircraft and engine works. Shipyards add six IC after nine months. Aircraft works add four IC and cut aircraft construction by twelve days; they finish on the same timetable.",money_cost=200,supply_cost=900,days=270,reward=[cmd("construct",which="ic",where=1552,value=3),cmd("construct",which="ic",where=1554,value=3)],alternative=("Fund aircraft works instead",[cmd("construct",which="ic",where=1552,value=4),cmd("build_time",which="air",when="on_upgrade",value=-12)]),finish_gate=control(1552)+" "+control(1554))
    paid_project("army_supply","Supply the expanding army","Modern depots and standard equipment improve supply output by 5 percent and transport capacity by 5 percent. Alternatively, spend the same funds on a four-IC industrial expansion. Neither choice supplies free divisions.",money_cost=150,supply_cost=700,days=180,reward=[cmd("industrial_modifier",which="supplies",value=5),cmd("tc_mod",value=5)],alternative=("Expand general industry instead",[cmd("construct",which="ic",where=1552,value=4)]),art="army",module="army",finish_gate=control(1552))
    paid_project("merchant_prewar","Expand the merchant marine","Commission 120 convoy transports and 25 convoy escorts. These are merchant shipping, not naval troop transports. The alternative produces 70 transports and 60 escorts for better-protected routes.",money_cost=120,supply_cost=600,days=150,reward=[cmd("transport_pool",which=-1,value=120),cmd("escort_pool",which=-1,value=25)],alternative=("Build fewer ships with more escorts",[cmd("transport_pool",which=-1,value=70),cmd("escort_pool",which=-1,value=60)]),module="shipping")
    paid_project("naval_school","Schools for a wider navy","Expand naval staff and engineering schools. Receive blueprints for the 1938 advanced naval-invasion and 1940 carrier-division doctrines. Alternatively, improve convoy defence and reconnaissance research.",year=1935,money_cost=130,supply_cost=500,days=180,reward=[blueprint(82320),blueprint(81730)],alternative=("Study convoy defence instead",[blueprint(8220),blueprint(8230)]),art="air",module="research")
    paid_project("pilot_school","Keep experienced pilots teaching","A deeper training system adds three air organisation and improves carrier-air-group construction by ten days. The alternative puts the investment into aircraft production, reducing air construction by fifteen days without the organisation benefit.",year=1935,money_cost=150,supply_cost=700,days=210,reward=[cmd("max_organization",which="air",value=3),cmd("build_time",which="cag",when="on_upgrade",value=-10),cmd("build_time",which="light_cag",when="on_upgrade",value=-10)],alternative=("Prioritise aircraft output",[cmd("build_time",which="air",when="on_upgrade",value=-15)]),art="air",module="air")
    paid_project("army_school","Learn from the China campaign","Fund field logistics: five percent more transport capacity and two points less attrition. Or train assault infantry for a modest five-point river and urban attack improvement. Neither option turns ordinary infantry into marines.",year=1937,gate=war("CHI"),money_cost=140,supply_cost=800,days=180,reward=[cmd("tc_mod",value=5),cmd("attrition_mod",value=2)],alternative=("Train assault infantry instead",[cmd("river_attack",which="infantry",value=5),cmd("urban_attack",which="infantry",value=5)]),art="army",module="army")
    paid_project("second_industry","Industry for a longer war","Build another six IC, or add four IC and five percent better supply production. These are physical factories, vulnerable to bombing and invasion.",year=1938,money_cost=250,supply_cost=1200,days=300,reward=[cmd("construct",which="ic",where=1552,value=3),cmd("construct",which="ic",where=1554,value=3)],alternative=("Balance industry with army supplies",[cmd("construct",which="ic",where=1552,value=4),cmd("industrial_modifier",which="supplies",value=5)]),finish_gate=control(1552)+" "+control(1554))
    paid_project("war_standard","Standard parts for wartime production","Standardise ship construction to reduce new naval hull times by forty days. Or standardise army and air production by fifteen days each. These are modest additions to existing technology benefits; cruiser conversions remain available.",year=1941,gate=pacific(),money_cost=300,supply_cost=1500,days=150,reward=[cmd("build_time",which="naval",when="on_upgrade",value=-40)],alternative=("Standardise army and aircraft production",[cmd("build_time",which="land",when="on_upgrade",value=-15),cmd("build_time",which="air",when="on_upgrade",value=-15)]))

    # Naval and military force programmes use actual stock unit types and paid queues.
    paid_project("fleet_order","The next carrier programme","Authorise two fleet carriers and two destroyers, or two light carriers and four destroyers. The fleet carriers use separate lines; repeated ships of other types use serial orders. The budget pays for preparations; construction still consumes normal IC and manpower. Air groups follow the model's normal attachment rules.",year=1941,gate=pacific(),money_cost=200,supply_cost=800,days=30,reward=[cmd("build_division",which="carrier",when=1),cmd("build_division",which="carrier",when=1),cmd("build_division",which="destroyer",when=2)],alternative=("Order light carriers and more screens",[cmd("build_division",which="light_carrier",when=2),cmd("build_division",which="destroyer",when=4)]),art="naval",module="navy")
    paid_project("escort_order","Keep the fleet screened","Fund preparations for six destroyers and 40 convoy escorts, or four light cruisers. Naval hulls enter the ordinary paid construction queue; convoy escorts arrive when the preparatory project completes.",year=1941,gate=pacific(),money_cost=150,supply_cost=600,days=45,reward=[cmd("build_division",which="destroyer",when=6),cmd("escort_pool",which=-1,value=40)],alternative=("Order four light cruisers",[cmd("build_division",which="light_cruiser",when=4)]),art="naval",module="navy")
    paid_project("home_docks","More room to repair the fleet","Tokyo and Hiroshima already have level-ten naval bases in this scenario. Build three naval-base levels at Kobe and three at Yokohama instead, spreading repair capacity across more ports. Or concentrate five levels and two AA levels at Kobe. Surviving ships still require reinforcement IC, supplies and time; sunk ships do not return.",year=1938,money_cost=200,supply_cost=900,days=240,reward=[cmd("construct",which="naval_base",where=1555,value=3),cmd("construct",which="naval_base",where=1550,value=3)],alternative=("Concentrate repairs and air defence at Kobe",[cmd("construct",which="naval_base",where=1555,value=5),cmd("construct",which="flak",where=1555,value=2)]),finish_gate=control(1555)+" "+control(1550),module="navy")
    paid_project("emergency_rebuild","Rebuild after a naval defeat","A serious combat loss allows a paid recovery programme. Choose two replacement light-carrier and four destroyer lines, or aircraft and convoy rebuilding. These are normal IC-funded orders. This programme is available only once, and no sunk hull returns.",year=1941,gate=pacific()+" losses = { type = carrier value = 1 }",money_cost=180,supply_cost=1200,days=30,reward=[cmd("build_division",which="light_carrier",when=2),cmd("build_division",which="destroyer",when=4)],alternative=("Rebuild naval aircraft and merchant shipping",[cmd("build_division",which="naval_bomber",when=2),cmd("transport_pool",which=-1,value=100)]),art="naval",module="navy")
    paid_project("naval_air_rebuild","Replace the fleet's aircraft","Improve CAG and light-CAG construction by fifteen days and add two naval-air morale. Alternatively, order three land-based naval-bomber wings at normal IC cost.",year=1942,gate=pacific(),money_cost=160,supply_cost=900,days=150,reward=[cmd("build_time",which="cag",when="on_upgrade",value=-15),cmd("build_time",which="light_cag",when="on_upgrade",value=-15),cmd("morale",which="air",value=2)],alternative=("Order land-based naval aircraft",[cmd("build_division",which="naval_bomber",when=3)]),art="air",module="air")
    paid_project("snlf","Expand the Special Naval Landing Forces","Prepare three naval-infantry divisions, or two marine divisions and two engineer brigades. Units enter normal paid production and use Japan's existing marine models. The programme also improves marine research with a current blueprint.",year=1937,money_cost=150,supply_cost=900,days=60,reward=[cmd("build_division",which="marine",when=3),blueprint(1600)],alternative=("Prepare two divisions with more engineers",[cmd("build_division",which="marine",when=2),cmd("add_brigade",value="engineer",when=4),cmd("add_brigade",value="engineer",when=4),blueprint(1600)]),art="army",module="units")
    paid_project("guards","A field force for difficult campaigns","Organise an Imperial Guards field force using Blood and Iron's elite infantry class. Three formations enter normal paid construction. Alternatively, form four mountain divisions. Elite troops still need supplies, upgrades and suitable commanders.",year=1939,money_cost=180,supply_cost=1000,days=90,reward=[cmd("activate_unit_type",which="d_01"),cmd("new_model",which="d_01",value=1),cmd("build_division",which="d_01",when=3)],alternative=("Build a larger mountain force",[cmd("build_division",which="bergsjaeger",when=4)]),art="army",module="units")
    paid_project("mobile_army","A mobile reserve for overseas war","Prepare three motorised divisions, or two armoured divisions. Orders use normal IC and manpower. The motorised option also adds five percent transport capacity; armour gets no free fuel.",year=1942,gate=pacific(),money_cost=170,supply_cost=1000,days=90,reward=[cmd("build_division",which="motorized",when=3),cmd("tc_mod",value=5)],alternative=("Prepare two armoured divisions",[cmd("build_division",which="armor",when=2)]),art="army",module="units")
    paid_project("base_guard","Defend the expanding base network","Prepare four garrison divisions with AA brigades at normal IC cost, or two marine divisions for a mobile island reserve. Rear-area garrisons do not need valuable commanders unless combat approaches.",year=1942,gate=pacific(),money_cost=100,supply_cost=700,days=45,reward=[cmd("build_division",which="garrison",value="anti_air",when=4)],alternative=("Create a mobile island reserve",[cmd("build_division",which="marine",when=2)]),art="army",module="units")

    # Resources: output stays in provinces and must travel through the convoy system.
    for key,title,province in [("sumatra_oil","Restore the Sumatran oilfields",1636),("borneo_oil","Restore the Borneo oilfields",1632),("java_oil","Repair Java's oil and port facilities",1653)]:
        paid_project(key,title,"Restore five daily provincial oil output and one naval-base level, or restore three oil output and expand the local airfield. The site must still be in friendly hands when work ends. Shipping the oil home remains your responsibility.",year=1941,gate=pacific()+" "+control(province),money_cost=150,supply_cost=900,days=120,reward=[cmd("add_prov_resource",which=province,where="oil",value=5),cmd("construct",which="naval_base",where=province,value=1)],alternative=("Support oil recovery with a larger airfield",[cmd("add_prov_resource",which=province,where="oil",value=3),cmd("construct",which="air_base",where=province,value=2)]),finish_gate=control(province),module="oil")
    paid_project("tankers","Tankers for the southern resources","Add 160 convoy transports and 30 escorts, or 100 transports and 70 escorts. Oil exists at the fields; it reaches Japan only when routes have ships and survive enemy attack.",year=1942,gate=pacific(),money_cost=180,supply_cost=1000,days=120,reward=[cmd("transport_pool",which=-1,value=160),cmd("escort_pool",which=-1,value=30)],alternative=("Protect a smaller tanker expansion",[cmd("transport_pool",which=-1,value=100),cmd("escort_pool",which=-1,value=70)]),module="shipping")
    paid_project("maritime_patrol","Aircraft over the shipping lanes","Order two naval-bomber wings and provide a convoy-defence blueprint, or fund 90 convoy escorts. Aircraft remain normal paid construction orders; escorts arrive at project completion.",year=1941,gate=pacific(),money_cost=130,supply_cost=700,days=90,reward=[cmd("build_division",which="naval_bomber",when=2),blueprint(8230)],alternative=("Build convoy escorts instead",[cmd("escort_pool",which=-1,value=90)]),art="air",module="shipping")
    paid_project("fuel_discipline","Make each tanker go further","Reduce carrier fuel use by 0.05 and destroyer fuel use by 0.02 per ship, and add 100 km naval-air range. Or improve army transport capacity by eight percent. Fuel savings are deliberately small; an active fleet still needs substantial oil.",year=1942,gate=pacific(),money_cost=160,supply_cost=800,days=150,reward=[cmd("fuel_consumption",which="carrier",value=-0.05),cmd("fuel_consumption",which="destroyer",value=-0.02),cmd("range",which="naval_bomber",value=100)],alternative=("Concentrate on army logistics",[cmd("tc_mod",value=8)]),module="oil")
    paid_project("synthetic","Synthetic fuel at home","Add six daily oil output in the home industrial area, consuming twenty daily provincial energy output. Alternatively, add four IC without the fuel conversion. This is a limited home programme, not unlimited off-map oil.",year=1943,gate=pacific(),money_cost=350,supply_cost=1800,days=300,reward=[cmd("add_prov_resource",which=1552,where="oil",value=6),cmd("add_prov_resource",which=1552,where="energy",value=-20)],alternative=("Build conventional industry instead",[cmd("construct",which="ic",where=1552,value=4)]),finish_gate=control(1552),module="oil")
    paid_project("shipping_emergency","An emergency merchant order","Commission 120 convoy transports, or 70 escorts. This one-time emergency programme is paid and delayed. It does not claim that an empty reserve means every merchant ship has been sunk.",year=1941,gate=pacific()+" NOT = { convoypool = 500 }",money_cost=130,supply_cost=700,days=90,reward=[cmd("transport_pool",which=-1,value=120)],alternative=("Build escorts instead",[cmd("escort_pool",which=-1,value=70)]),module="shipping")

    # Independent country resolutions, no shared theatre gate.
    country_definition("china","U87","China",1337,control(1337)+" "+control(1338)+" "+control(1299)+" lost_national = { country = CHI value = 55 }",old_tag="CHI",bases=(1338,),year=1937,extra_desc="Shanghai is the optional Japanese base. Other Chinese wars, including surviving Communist forces, are not silently settled.")
    # China is the deliberate pre-Pearl Harbor exception: military victory may be earlier.
    next(e for e in EVENTS if e.key=="china").gate = next(e for e in EVENTS if e.key=="china").gate.replace(pacific(),"")
    country_definition("india","IND","India",1459,control(1459)+" OR = { "+control(1447)+" "+control(1517)+" } lost_national = { country = U02 value = 35 }",old_tag="U02",bases=(1517,),extra_desc="Bombay is the optional Japanese base. Ordinary India starts as the British Raj; no Indian player-mod content is imported.")
    for args in [
        ("philippines","PHI","the Philippines",1565,control(1565)+" lost_national = { country = PHI value = 35 }",(1565,)),
        ("malaya","MLY","Malaya",1438,control(1438)+" "+control(1432), (1432,)),
        ("brunei","BRU","Brunei",1625,control(1625),()),
        ("sarawak","SAR","Sarawak",1624,control(1624),()),
        ("thailand","SIA","Thailand",1423,control(1423)+" lost_national = { country = SIA value = 40 }",()),
        ("burma","BUR","Burma",1415,control(1415)+" lost_national = { country = BUR value = 35 }",()),
        ("australia","AST","Australia",1707,control(1705)+" "+control(1707)+" lost_national = { country = AST value = 55 }",(1705,)),
        ("newzealand","NZL","New Zealand",1721,control(1721)+" "+control(1722)+" lost_national = { country = NZL value = 45 }",()),
        ("persia","PER","Persia",1085,control(1085)+" lost_national = { country = PER value = 45 }",()),
        ("iraq","IRQ","Iraq",1034,control(1034)+" lost_national = { country = IRQ value = 45 }",()),
        ("egypt","EGY","Egypt",787,control(787)+" lost_national = { country = EGY value = 45 }",())]:
        key,tag,name,cap,g,bases=args
        country_definition(key,tag,name,cap,g,bases=bases)
    country_definition("indonesia","INO","Indonesia",1647,control(1647)+" "+control(1653)+" lost_national = { country = U05 value = 35 }",old_tag="U05",bases=(1653,))

    # Colonial releases need an owner-side transfer rather than stealing allied land.
    for key,tag,name,cap,base in [("vietnam","VIE","Vietnam",1399,1399),("laos","LAO","Laos",1405,None),("cambodia","CMB","Cambodia",1400,None)]:
        country_definition(key,tag,name,cap,control(cap),bases=(base,) if base else ())

    # Existing stock settlements are repaired too, regardless of which chain created China.
    event("china_cores","China has a national government","The Chinese government's own provinces now count as its national territory. It can use its industry and recruit at home instead of treating almost the whole country as foreign occupation. Japan keeps its agreed bases.",country="U87",gate=puppet("U87")+" NOT = { flag = JX_CHINA_CORES }",actions=[Action("Begin reconstruction",[flag("CHINA_CORES"),cmd("ai",which='"jx/partner_land.ai"'),supplies(1800),later("china_recovery",90,"U87")],chance=100)],offset=2,art="asia",module="china")
    event("china_recovery","A Chinese army that can hold its ground","A small army receives a limited reconstruction draft. Existing large armies receive no duplicate units. The supply reserve supports local reinforcement before expeditionary service.",country="U87",triggered=True,actions=[Action("Rebuild the army",[supplies(1800),cond("NOT = { army = { country = U87 size = 12 } }",cmd("manpowerpool",value=50)),cond("NOT = { army = { country = U87 size = 12 } }",cmd("build_division",which="infantry",when=6))],chance=100)],art="army",module="china")
    for key,title,tag in [("china_mission","Equipment for the Chinese army","U87"),("india_mission","Equipment for the Indian army","IND")]:
        paid_project(key,title,"Send 1,500 supplies and 100 money to the partner. Or send 1,000 supplies and a normal paid infantry production order. This helps a real partner maintain an army; it does not transfer unlimited manpower to Japan.",year=1941,gate=puppet(tag),money_cost=120,supply_cost=1500,days=60,reward=[later(key+"_aid",1,tag)],alternative=("Help form another infantry division",[later(key+"_unit",1,tag)]),art="army",module="partners",finish_gate=puppet(tag))
        event(key+"_aid",title,"Japanese equipment and funds arrive for local reinforcement.",country=tag,triggered=True,actions=[Action("Use the equipment locally",[supplies(1500),money(100)],chance=100)],art="army",module="partners")
        event(key+"_unit",title,"Japanese supplies support another local formation, which still needs normal industrial funding.",country=tag,triggered=True,actions=[Action("Form the division",[supplies(1000),cmd("build_division",which="infantry",when=1)],chance=100)],art="army",module="partners")

    # Offensive milestones create assets and choices, not vague victory records.
    for key,title,province in [("hawaii","Hawaii: a forward base or a bargaining chip",1734),("singapore","Singapore: the fleet's western gate",1432),("hongkong","Hong Kong after the battle",1371),("suez","The fleet reaches Suez",900)]:
        paid_project(key,title,"Fortify and expand this captured naval base: two naval-base levels and one airfield level. Or expand its airfield by three levels and add two AA levels. Holding this base improves operations; it does not force an unrelated country to surrender.",year=1941,gate=pacific()+" "+control(province),money_cost=140,supply_cost=800,days=150,reward=[cmd("construct",which="naval_base",where=province,value=2),cmd("construct",which="air_base",where=province,value=1)],alternative=("Make it a stronger air base",[cmd("construct",which="air_base",where=province,value=3),cmd("construct",which="flak",where=province,value=2)]),art="pacific",module="bases",finish_gate=control(province))
    paid_project("australian_prep","Prepare for the Australian coast","Order two marine and four infantry divisions, or three tactical-bomber wings. All are ordinary paid production. The decision improves preparation without declaring war or guaranteeing a landing.",year=1942,gate=pacific()+" NOT = { puppet = { country = AST country = JAP } }",money_cost=200,supply_cost=1000,days=60,reward=[cmd("build_division",which="marine",when=2),cmd("build_division",which="infantry",when=4)],alternative=("Prepare a larger air campaign",[cmd("build_division",which="tactical_bomber",when=3)]),art="pacific",module="campaigns")
    paid_project("forward_air","Airfields along the invasion routes","Build two levels of airfield at Soerabaja, or improve the same base's port and AA. This award is infrastructure, not aircraft. Naval aircraft still need bases within range and a supply route.",year=1942,gate=pacific()+" "+control(1653),money_cost=120,supply_cost=700,days=120,reward=[cmd("construct",which="air_base",where=1653,value=2)],alternative=("Improve port facilities and air defence",[cmd("construct",which="naval_base",where=1653,value=1),cmd("construct",which="flak",where=1653,value=2)]),art="air",module="bases",finish_gate=control(1653))

    # Cooperation and a Soviet war are current-condition decisions, never a 1933 route.
    paid_project("german_exchange","A submarine mission to Germany","Send a limited technical mission. Gain carrier and armour research blueprints; Germany receives a small supply and fuel shipment. Or concentrate on maritime research, gaining escort and convoy-defence blueprints. This does not enter Germany's alliance or wars.",year=1942,gate=pacific()+" exists = GER NOT = { "+war("GER")+" }",money_cost=150,supply_cost=1200,days=120,reward=[blueprint(81730),blueprint(2050),later("german_delivery",1,"GER")],alternative=("Exchange maritime research only",[blueprint(8220),blueprint(8230),later("german_delivery",1,"GER")]),art="diplomacy",module="germany",finish_gate="exists = GER NOT = { "+war("GER")+" }")
    event("german_delivery","A Japanese mission arrives","A limited shipment arrives after the submarine mission. It cannot replace an open ocean trade route.",country="GER",triggered=True,actions=[Action("Receive the mission",[supplies(800),cmd("oilpool",value=500)],chance=100)],art="diplomacy",module="germany")
    event("soviet_choice","Open a Soviet front?","A Soviet war is available after Pearl Harbor even if Japan followed the historical policy in 1933. It is a separate Japanese decision. You will fight Soviet allies as diplomacy requires, while the American and British wars continue.\n\nPreparations cost 100 money and 1,000 supplies. Breaking a neutrality treaty is deliberate and carries two dissent. You can defer or dismiss the offer.",decision=True,gate=active()+" "+pacific()+" exists = SOV NOT = { "+war("SOV")+" flag = JX_SOVIET_DISMISSED flag = JX_SOVIET_WAIT flag = JX_SOVIET_PENDING }",ready="money = 100 supplies = 1000 army = 80",year=1941,persistent=True,actions=[Action("Prepare the operation; confirm before declaring war",[money(-100),supplies(-1000),flag("SOVIET_PENDING"),later("soviet_confirm",30)],chance=0),Action("Wait three months",[flag("SOVIET_WAIT"),later("soviet_return",90)],chance=100),Action("Do not propose a Soviet war again",[flag("SOVIET_DISMISSED")])],art="siberia",module="soviet")
    event("soviet_confirm","Confirm war with the Soviet Union","The preparations are complete. Declaring war breaks any Japanese-Soviet neutrality agreement, adds two dissent and leaves Japan's other wars running. You may still cancel; the supply preparations have already been spent.",triggered=True,actions=[Action("Declare the separate Soviet war",[cmd("end_non_aggression",which="JAP",where="SOV"),cmd("end_non_aggression",which="SOV",where="JAP"),cmd("war",which="SOV"),cmd("dissent",value=2),clear("SOVIET_PENDING"),flag("SOVIET_WAR")],gate="exists = SOV NOT = { "+war("SOV")+" }",chance=0),Action("Cancel the attack",[clear("SOVIET_PENDING"),flag("SOVIET_WAIT"),later("soviet_return",180)],chance=100)],art="siberia",module="soviet")
    event("soviet_return","The Soviet option is available again","",triggered=True,actions=[Action("",[clear("SOVIET_WAIT")])],module="soviet")
    paid_project("siberian_rail","Keep supplies moving into Siberia","Invest in the captured eastern railway: improve infrastructure by ten points at Vladivostok, Khabarovsk and Chita and add five percent transport capacity. Or order four mountain divisions for the deeper campaign. Provincial work needs continued control of those centres.",year=1942,gate=pacific()+" "+war("SOV")+" "+control(1191)+" "+control(1190)+" "+control(1169),money_cost=200,supply_cost=1500,days=180,reward=[cmd("construct",which="infrastructure",where=p,value=10) for p in (1191,1190,1169)]+[cmd("tc_mod",value=5)],alternative=("Train mountain troops instead",[cmd("build_division",which="bergsjaeger",when=4)]),art="siberia",module="soviet",finish_gate=control(1191)+" "+control(1190)+" "+control(1169))
    paid_project("med_expedition","A Japanese fleet in the Mediterranean","With Suez held, prepare two destroyers and two naval-bomber wings at normal IC cost. Or improve Alexandria's naval base if Japan holds it. Passage and supply follow the map; this decision cannot bypass Gibraltar or the Suez canal rules.",year=1942,gate=pacific()+" "+control(900)+" "+control(789),money_cost=180,supply_cost=1000,days=90,reward=[cmd("build_division",which="destroyer",when=2),cmd("build_division",which="naval_bomber",when=2)],alternative=("Expand the Alexandrian repair base",[cmd("construct",which="naval_base",where=789,value=2)]),art="naval",module="germany",finish_gate=control(900)+" "+control(789))

    # Endgame and postwar decisions are developed on the same engine-safe state model.
    paid_project("wartime_industry","Industry after the first victories","Build six more IC over a year, or improve supply production by eight percent and transport capacity by five percent. Captured territory and puppet armies do not remove the need to supply a growing navy and army.",year=1943,gate=pacific(),money_cost=400,supply_cost=2000,days=360,reward=[cmd("construct",which="ic",where=1552,value=3),cmd("construct",which="ic",where=1554,value=3)],alternative=("Sustain the forces already deployed",[cmd("industrial_modifier",which="supplies",value=8),cmd("tc_mod",value=5)]),module="industry",finish_gate=control(1552)+" "+control(1554))
    paid_project("late_fleet","The next generation of the fleet","Order two contemporary fleet carriers, or six destroyers and four submarines. All use ordinary IC and manpower. There is no free fleet when the historical war ends.",year=1945,gate=pacific(),money_cost=300,supply_cost=1600,days=60,reward=[cmd("build_division",which="carrier",when=2)],alternative=("Build a wider escort and submarine force",[cmd("build_division",which="destroyer",when=6),cmd("build_division",which="submarine",when=4)]),art="naval",module="postwar")
    paid_project("late_air","Aircraft for a changing war","Support aircraft and radar research, or order four multirole wings. The research option gives contemporary fighter and electronics blueprints selected by the build's verified technology table.",year=1945,money_cost=240,supply_cost=1200,days=180,reward=[blueprint(4060),blueprint(5310)],alternative=("Expand the air force now",[cmd("build_division",which="multi_role",when=4)]),art="air",module="postwar")
    paid_project("civil_recovery","Rebuild the civilian economy","At peace, build six IC or reduce dissent by three and improve supply output by five percent. Civilian recovery takes a year; renewed war before completion cancels and refunds this project.",year=1945,gate="atwar = no",money_cost=300,supply_cost=1000,days=360,reward=[cmd("construct",which="ic",where=1552,value=6)],alternative=("Restore living standards first",[cmd("dissent",value=-3),cmd("industrial_modifier",which="supplies",value=5)]),art="asia",module="postwar",finish_gate="atwar = no "+control(1552))
    for key,tag,name in [("china_autonomy","U87","China"),("india_autonomy","IND","India")]:
        event(key,f"A new agreement with {name}",f"{name} seeks more independence after years of cooperation. Release it from puppet status while retaining the alliance and mutual access, or maintain the present agreement with a 1,000-supply development grant. Ending puppet status is permanent; it does not automatically end alliance wars.",decision=True,gate=active()+" "+puppet(tag)+f" NOT = {{ flag = JX_{key}_DONE }}",ready="supplies = 1000",year=1947,actions=[Action("Grant sovereignty; keep the alliance and access",[cmd("end_mastery",which=tag),flag(key+"_DONE"),later(key+"_access",1,tag)],chance=0),Action("Keep the treaty and fund local development",[supplies(-1000),flag(key+"_DONE"),later(key+"_grant",1,tag)],chance=100)],art="diplomacy",module="postwar")
        event(key+"_access",f"{name} renews Japanese access","The new government confirms military access. Alliance membership is retained unless a later explicit agreement changes it.",country=tag,triggered=True,actions=[Action("Renew access",[cmd("access",which="JAP")],chance=100)],art="diplomacy",module="postwar")
        event(key+"_grant",f"{name} receives development aid","A Japanese grant supports local supply and reconstruction.",country=tag,triggered=True,actions=[Action("Use the grant",[supplies(1000),cmd("construct",which="ic",where=1459 if tag=="IND" else 1337,value=2)],chance=100)],art="asia",module="postwar")
    paid_project("naval_treaty","A naval limitation or another building programme","At peace, accept a limited domestic pause in new naval construction: receive civilian investment and modest dissent relief, while naval construction takes forty more days. Or fund an ordinary new carrier order. The pause expires after three years.",year=1947,gate="atwar = no",money_cost=200,supply_cost=700,days=60,reward=[cmd("construct",which="ic",where=1552,value=3),cmd("dissent",value=-2),cmd("build_time",which="naval",when="on_upgrade",value=40),flag("NAVAL_PAUSE"),later("naval_pause_end",1080)],alternative=("Keep expanding the fleet",[cmd("build_division",which="carrier",when=1)]),art="diplomacy",module="postwar",finish_gate="atwar = no "+control(1552))
    event("naval_pause_end","The naval construction pause expires","The temporary forty-day construction penalty ends. Civilian investment already completed remains in place.",triggered=True,actions=[Action("Restore normal naval planning",[cmd("build_time",which="naval",when="on_upgrade",value=-40),clear("NAVAL_PAUSE")],gate="flag = JX_NAVAL_PAUSE",chance=100)],art="naval",module="postwar")
    return EVENTS


build_catalog()
