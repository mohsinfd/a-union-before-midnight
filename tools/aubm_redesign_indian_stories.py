"""Twelve optional, finite Indian stories; pure append to the loaded module 32.

No routes, callbacks, diplomacy, units or permanent modifiers are introduced.
Season windows are deliberately disclosed: at most one story is offered in a
month, including when this stage is added to an old save. Month triggers use
the documented zero-based, >= semantics in DH's event commands.txt. Stock
commands and action triggers are also documented there. Native playtesting
remains pending. IDs 9398100..9398111 form this stage's explicit new-ID band.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

MARKER = "# AUBM_STAGED_INDIAN_STORIES_V1"
SOURCE_MODULE = "32_national_consolidation.txt"
NEW_EVENT_IDS = tuple(range(9398100, 9398112))

# Resource values are changes, not stock requirements. Every negative change
# generates a matching affordability predicate on both the offer and action.
# Manpowerpool is the documented effect; manpower is its stock trigger.
STORIES = [
    dict(id=9398100, title="The Workshop After the Whistle", war=False,
         months=(0, 2), season="January-February", year=1934,
         desc="After the shift, railway fitters offer to train apprentices on government repair orders. Under the workshop lamps, a pile of metal can become useful field equipment; surplus stores could instead be sold to help pay for the evening work.",
         options=[("Order repair kits: $160, 250 metal; +500 supplies",
                   dict(money=-160, metalpool=-250, supplies=500)),
                  ("Sell surplus: 300 supplies; +$100",
                   dict(supplies=-300, money=100))]),
    dict(id=9398101, title="A Map Folded at the Pass", war=False,
         months=(2, 4), season="March-April", year=1934,
         desc="Survey clerks and local carriers compare routes before the high passes reopen. On their creased maps, the long stretches between dependable markets matter as much as the ridgelines. A small purchasing mission must choose between fuel caches and pack stores.",
         options=[("Arrange fuel caches: $100, 200 supplies; +150 oil",
                   dict(money=-100, supplies=-200, oilpool=150)),
                  ("Buy pack stores: $150, 100 oil; +350 supplies",
                   dict(money=-150, oilpool=-100, supplies=350))]),
    dict(id=9398102, title="Night Shift at the Railway Yard", war=True,
         months=(4, 6), season="May-June", year=1934,
         desc="Wartime traffic keeps the railway yards lit after midnight. Workshop crews propose one extra contract: turn metal into field stores, or hire civilian carriers with a smaller mixed load. The yard cannot take both contracts before the rains; choose what the front needs most.",
         options=[("Make field stores: $200, 300 metal; +700 supplies",
                   dict(money=-200, metalpool=-300, supplies=700)),
                  ("Hire carriers: $350; +350 supplies, +100 oil",
                   dict(money=-350, supplies=350, oilpool=100))]),
    dict(id=9398103, title="Canvas Before the Rains", war=False,
         months=(6, 8), season="July-August", year=1934, minimum_dissent=1,
         desc="With public discontent already present, municipal committees ask for a monsoon reserve of canvas, medicine and food. Rain drums on the depot roofs while the requests accumulate. Release government stores, or pay civilian suppliers to carry more of the burden.",
         options=[("Open depots: $100, 500 supplies; -1 dissent",
                   dict(money=-100, supplies=-500, dissent=-1)),
                  ("Buy relief stocks: $300, 150 supplies; -1 dissent",
                   dict(money=-300, supplies=-150, dissent=-1))]),
    dict(id=9398104, title="The Cargo Before Dawn", war=True,
         months=(8, 10), season="September-October", year=1934,
         desc="Indian merchant sailors and dock agents have room for one additional wartime cargo contract. Fuel drums compete with crated field stores for the same purchasing budget. Before the loading gangs begin, the quartermaster needs a decision on what goes aboard.",
         options=[("Charter fuel cargo: $200, 150 supplies; +300 oil",
                   dict(money=-200, supplies=-150, oilpool=300)),
                  ("Charter field stores: $150, 100 oil; +350 supplies",
                   dict(money=-150, oilpool=-100, supplies=350))]),
    dict(id=9398105, title="A Bed on the Homeward Train", war=True,
         months=(10, 12), season="November-December", year=1934,
         desc="Medical volunteers offer a winter programme for returning soldiers and their families. One proposal funds rehabilitation for men nearing a return to service; another brings relief to households already voicing discontent. There is money for one commitment, and names waiting on both lists.",
         options=[("Fund recovery: $150, 500 supplies; +8 manpower",
                   dict(money=-150, supplies=-500, manpowerpool=8)),
                  ("Support families: $250, 250 supplies; -1 dissent",
                   dict(money=-250, supplies=-250, dissent=-1))]),
]

# Give each story its own calendar month: more variety without a crowded panel.
for story, season in zip(STORIES, ('January','March','May','July','September','November')):
    story['months'] = (story['months'][0], story['months'][0]+1)
    story['season'] = season
STORIES += [
    dict(id=9398106,title='The Match at Eden Gardens',war=False,months=(1,2),season='February',year=1935,
         desc='A packed cricket ground offers Delhi a rare afternoon without speeches. The organisers can sell a charity programme for the treasury, or invite railway workers and their families at government expense. The crowd will remember who was let through the gates.',
         options=[('Sell the charity programme: 200 supplies; +$100',dict(supplies=-200,money=100)),
                  ('Open the gates: $250, 150 supplies; -2 dissent',dict(money=-250,supplies=-150,dissent=-2))]),
    dict(id=9398107,title='A Voice from Bombay',war=False,months=(3,4),season='April',year=1935,
         desc='A new radio programme brings songs, crop reports and letters from listeners into the same hour. Commercial sponsors will pay for advertising time. Public broadcasts cost more, but let listeners hear something other than rumours about Delhi.',
         options=[('Take sponsorship: 150 supplies; +$100',dict(supplies=-150,money=100)),
                  ('Fund public broadcasts: $200; -1 dissent',dict(money=-200,dissent=-1))]),
    dict(id=9398108,title='A Cyclone off the Coast',war=True,months=(5,6),season='June',year=1935,
         desc='A coastal convoy has scattered in foul weather. Rescue launches have fuel for one sustained effort: search the fishing villages for surviving sailors, or tow the drifting supply barges before the sea takes them. Both crews are waiting for orders.',
         options=[('Search for survivors: $150, 100 oil; +6 manpower',dict(money=-150,oilpool=-100,manpowerpool=6)),
                  ('Recover the barges: $150, 150 oil; +600 supplies',dict(money=-150,oilpool=-150,supplies=600))]),
    dict(id=9398109,title='The Cinema Van',war=False,months=(7,8),season='August',year=1935,
         desc='A travelling cinema has reached a town that rarely sees a government visitor. Its reels mix comedy with news from across India. Keep the evening free for families, or sell tickets and use the receipts to meet the van\'s next repair bill.',
         options=[('Make admission free: $120, 50 oil; -1 dissent',dict(money=-120,oilpool=-50,dissent=-1)),
                  ('Sell tickets: 150 supplies, 50 oil; +$100',dict(supplies=-150,oilpool=-50,money=100))]),
    dict(id=9398110,title='The Harbour Blackout',war=True,months=(9,10),season='October',year=1935,
         desc='The port lights are out, but the last cargo is still on the quays. Dock workers offer to salvage the stranded stores. The harbour master wants the launches sent instead to collect merchant crews cut off across the inlet. Dawn is not far away.',
         options=[('Salvage the stores: $180, 150 oil; +550 supplies',dict(money=-180,oilpool=-150,supplies=550)),
                  ('Bring crews ashore: $120, 250 supplies; +6 manpower',dict(money=-120,supplies=-250,manpowerpool=6))]),
    dict(id=9398111,title='Letters from the Front',war=True,months=(11,12),season='December',year=1935,
         desc='Sacks of delayed letters fill the station office. The army can fund a holiday post and family allowance, or reserve the trains for recovered soldiers returning to their units. Neither order changes the war plan, but both matter to the people waiting on the platform.',
         options=[('Deliver letters and allowances: $220; -2 dissent',dict(money=-220,dissent=-2)),
                  ('Reserve troop trains: $150, 400 supplies; +8 manpower',dict(money=-150,supplies=-400,manpowerpool=8))]),
]

STOCK = {"money": "money", "supplies": "supplies", "metalpool": "metal",
         "oilpool": "oil", "manpowerpool": "manpower", "dissent": "dissent"}


def flag(story):
    return "ind_story_" + str(story["id"]) + "_done"


def availability(story):
    state = "at war" if story["war"] else "at peace"
    dissent = "; dissent at least 1" if story.get("minimum_dissent") else ""
    return (f"{story['season']}, {story['year']} onward; India {state}, not a puppet; alliances allowed"
            f"{dissent}; once only; an affordable option required")


def context(story):
    lo, hi = story["months"]
    parts = ["ai = no", "exists = IND", "NOT = { ispuppet = IND }",
             "atwar = " + ("yes" if story["war"] else "no"),
             f"year = {story['year']}", f"month = {lo}",
             "NOT = { flag = " + flag(story) + " }"]
    if hi < 12:
        parts.append(f"NOT = {{ month = {hi} }}")
    if story.get("minimum_dissent"):
        parts.append(f"dissent = {story['minimum_dissent']}")
    return " ".join(parts)


def affordable(effects):
    # Relief is not offered at zero dissent. This also prevents a meaningless
    # paid choice while keeping the recovery option available during calm.
    return " ".join(f"{STOCK[key]} = {-amount}" for key, amount in effects.items()
                    if amount < 0)


def render(story):
    gate = context(story)
    choices = " ".join("AND = { " + affordable(effects) + " }"
                       for _, effects in story["options"])
    tooltip = (availability(story) + ". Not now is free and leaves this story open. "
               "One stock exchange or relief programme; no permanent bonuses or new units.")
    lines = ["event = {", f" id = {story['id']}", " country = IND",
             " random = no", " persistent = yes",
             f" decision = {{ {gate} }}",
             f" decision_trigger = {{ {gate} OR = {{ {choices} }} }}",
             f" trigger = {{ {gate} OR = {{ {choices} }} }}",
             f' name = "{story["title"]}"', f' desc = "{story["desc"]}"',
             f' decision_desc = "{tooltip}"',
             ' picture = "india_v3_armed_forces"', " style = 2",
             " date = { day = 0 month = january year = 1934 }", " offset = 7",
             " deathdate = { day = 29 month = december year = 1964 }"]
    for letter, (label, effects) in zip("ab", story["options"]):
        lines += [f" action_{letter} = {{", f'  name = "{label}"',
                  f"  trigger = {{ {gate} {affordable(effects)} }}",
                  "  command = { type = setflag which = " + flag(story) + " }"]
        lines += [f"  command = {{ type = {key} value = {amount} }}"
                  for key, amount in effects.items()]
        lines.append(" }")
    lines += [' action_c = { name = "Not now - keep this offer open"',
              '  trigger = { ai = no }', ' }', '}']
    return "\n".join(lines)


def transform(files: dict[str, str]):
    """Return a copy and exact new-ID review records; never touch disk."""
    result = dict(files)
    matches = [key for key in files
               if PurePosixPath(key.replace("\\", "/")).name == SOURCE_MODULE]
    if len(matches) != 1:
        raise ValueError("Indian stories require exactly one loaded module 32")
    key = matches[0]
    if MARKER in files[key]:
        for story in STORIES:
            count = sum(len(re.findall(r"\bid\s*=\s*" + str(story["id"]) + r"\b", text))
                        for text in files.values())
            if count != 1 or render(story) not in files[key]:
                raise ValueError(f"Marked Indian story missing or changed: {story['id']}")
    if MARKER not in files[key]:
        found = {int(m.group(1)) for text in files.values()
                 for m in re.finditer(r"\bid\s*=\s*(\d+)", text)}
        collisions = sorted(found.intersection(NEW_EVENT_IDS))
        if collisions:
            raise ValueError(f"Indian story ID collision: {collisions}")
        result[key] = files[key] + "\n\n" + MARKER + "\n" + "\n\n".join(
            render(story) for story in STORIES) + "\n"
    records = {story["id"]: [dict(
        dimension="indian_stories", status="reviewed", title=story["title"],
        availability=availability(story),
        options=[dict(label=label, effects=dict(effects))
                 for label, effects in story["options"]],
        changes="New optional one-off story; costs and current context rechecked on actions",
        caveats=["Native decision UI and play-balance testing pending",
                 "Season windows are intentional and disclosed in the decision tooltip"])]
        for story in STORIES}
    return result, records
