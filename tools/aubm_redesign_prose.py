"""Pure, staged narrative catalogue; not a whole-mod prose certification.

Only explicitly authored entries below are reviewed. Unlisted events remain
pending. Inputs are authored event files, before generated UI/cleanup overlays.
Only quoted name/desc/decision_desc values change: game effects remain exact.
The engine still supplies the unchanged native command/effect tooltips.
"""
from __future__ import annotations

from hashlib import sha256
from dh_save_spans import Node, parse, replace


def entry(title, description, actions, caveat="Native gameplay and layout remain untested."):
    assert len(title) <= 58 and len(description) <= 500
    assert all(len(label) <= 58 for label in actions.values())
    return dict(title=title, description=description, actions=actions, caveat=caveat)


CANCEL = {"Cancel - close without changes": "Leave this for later"}
CATALOG = {
    9270002: entry("The First Cabinet",
        "Independence has put Delhi in charge; now it needs a government. Choose Gandhi and Nehru's civilian federation, Patel and Visvesvaraya's stronger executive, or Bose and Saha's mobilizing cabinet; each choice appoints the full ministry and changes domestic policy.", {
        "Gandhi-Nehru: -100 money, -250 supplies, -3 dissent": "Gandhi-Nehru: -100 money/-250 supplies/-3 dissent",
        "Patel: -200 money/-400 supplies/-1 dissent; defence reform": "Patel: -200 money/-400 supplies/-1 dissent",
        "Bose: -75 money, -200 supplies, +30 MP, +2 dissent": "Bose: -75 money/-200 supplies/+30 MP/+2 dissent"}),
    9270001: entry("One Flag, Many Provinces",
        "The flag has changed, but provincial offices still answer to different rules. Bargain for a common administration, leave more power with the provinces, or impose Delhi's authority; each funds different roads where ownership and existing infrastructure permit.", {
        "Negotiate: -150 money, -350 supplies, -10 MP, -5 dissent": "Negotiate: -150 money/-350 supplies/-10 MP/-5 dissent",
        "Provincial: -75 money, -200 supplies, -3 dissent": "Provincial freedom: -75 money/-200 supplies/-3 dissent",
        "Centralize: +150 money, -400 supplies, -5 MP, +4 dissent": "Centralize: +150 money/-400 supplies/-5 MP/+4 dissent"}),
    9270100: entry("Who Holds the Pen?",
        "The assembly must decide who can act in India's name. Parliament restrains intervention; a planning executive strengthens defence and intervention while reducing dissent by 2; a social constitution adds 15 manpower and moves policy toward state control.", {
        "Parliament: -3 dissent, less intervention; costs 100 money": "Parliament: -100 money/-3 dissent/-1 intervention",
        "Planning executive: defence/intervention +1; costs 150/200": "Planning executive: -150 money/-200 supplies",
        "Social rights: +15 manpower; +1 dissent, costs 75/150": "Social rights: -75 money/-150 supplies/+1 dissent"}),
    9270101: entry("The Village's Share",
        "Independence reaches the countryside through land, water and credit. Redistribution costs 75 money and 200 supplies; irrigation uses 10 manpower; the property bargain loses 15 manpower and improves British relations by 15, alongside the changes shown below.", {
        "Redistribute: +45 manpower, two rural routes; +5 dissent": "Redistribute land: +45 MP/+5 dissent; two roads",
        "Rural investment: -2 dissent, four routes; costs 200/550": "Irrigation: -200 money/-550 supplies/-2 dissent",
        "Property compact: +500 money, freer market; +4 dissent": "Keep landed property: +500 money/+4 dissent"}),
    9270102: entry("In Whose Words?",
        "A letter from Delhi must be understood across the Union. Multilingual service costs more money; a Hindustani standard costs 125 money; retaining English improves British relations by 20 and lowers intervention by 1, in addition to the effects below.", {
        "Multilingual: -250 money, -3 dissent, +1 research": "Many languages: -250 money/-3 dissent/+1 research",
        "Hindustani standard: +3 TC, +10 manpower; +2 dissent": "Hindustani: +3 TC/+10 MP/+2 dissent",
        "English service: -300 supplies, +1 dissent, +2 research": "English: -300 supplies/+1 dissent/+2 research"}),
    9270103: entry("India Chooses Again",
        "Three years of independence have tested every promise. Renew Gandhi and Nehru's coalition, appoint Patel and Visvesvaraya's development cabinet, or give Bose and Patel a mobilizing government; each replaces the full ministry, with policy changes shown in the effects.", {
        "Gandhi-Nehru: -5 dissent, -1 intervention; costs 150 money": "Gandhi-Nehru: -150 money/-5 dissent/-1 intervention",
        "Patel-Visvesvaraya: -2 dissent, +1 defence; costs 250/400": "Patel: -250 money/-400 supplies/-2 dissent/+1 defence",
        "Bose-Patel: -700 supplies, +2 dissent; mobilize": "Bose-Patel: -700 supplies/+2 dissent; mobilize"}),
    9282212: entry("Bangkok After the Fighting",
        "India must decide what its victory in Siam should mean. An eligible enemy can receive a peace offer with a 60/25/15 accept, counteroffer or refusal roll; after annexation, Delhi may seek a sovereign government or protectorate, or keep direct rule with occupation costs and +3 belligerence.", {
        "Offer pairwise peace: fixed 60/25/15": "Offer Siam peace: accept/counter/refuse 60/25/15",
        "Restore a sovereign government": "Authorize a sovereign Siamese government",
        "Create a protectorate: +4 dissent": "Seek a Siamese protectorate: +4 dissent",
        "Retain direct administration: +7 dissent": "Keep direct rule: +7 dissent/+3 belligerence"},
        "Government creation and puppet conversion require native verification; no outcome is certified."),
    9297003: entry("Break Tokyo's Hold on Bangkok",
        "Indian troops have opened a chance to change Siam's allegiance. Send terms for ending Japanese control and establishing Indian protection; the following steps must confirm Siam's position while India's war with Japan continues.", {
        "Demand an Indian puppet government": "Demand Siam leave Tokyo for Indian protection", **CANCEL},
        "This initiates a government transition; it does not prove that transition succeeds."),
    9289903: entry("A Price for China's Break with Tokyo",
        "The campaign has put Delhi in a position to demand a Chinese protectorate. Pay 350 money and 1,000 supplies for a reply in three days: 80% acceptance or 20% refusal, with a 90-day retry delay; acceptance opens further steps for the existing Nanjing government, not immediate annexation.", {
        "Demand an Indian puppet: 80% acceptance": "Demand protection: -350 money/-1000 supplies; 80%", **CANCEL},
        "Foreign-response and government transitions still require native verification."),
    9289905: entry("China's Next Allegiance",
        "The Nanjing government has consented to protection and recovered its key cities. Ratification orders Indian puppet status and grants +4 TC and 2,000 supplies at +3 dissent; alternatively, recognize its independence with an Indian guarantee and forgo this ratification.", {
        "Make China an Indian puppet: +3 dissent": "Ratify protection: +4 TC/+2000 supplies/+3 dissent",
        "Choose full independence; forgo this puppet ratification": "Guarantee independent China; forgo protection", **CANCEL},
        "The reward is scripted immediately; puppet conversion is not engine-certified."),
    9294013: entry("An Opening in Indochina",
        "Holding five provinces for 30 days gives India terms to put before Indochina's government. Pay 200 money and 750 supplies to demand a break with Tokyo: a reply follows in three days, with 80% acceptance or 20% refusal and a 90-day retry delay; a separate peace file cancels the pending offer.", {
        "Demand Tokyo withdrawal: 80%; pay 200 and 750 supplies": "Demand withdrawal: -200 money/-750 supplies; 80%", **CANCEL},
        "Withdrawal and subsequent government choices require native verification."),
    9294015: entry("Who Governs Indochina?",
        "Indochina has left Tokyo and recovered the five required provinces. Guarantee the existing government's independence for +1 TC and -1 dissent, or order Indian puppet status for +2 TC and +3 dissent; neither choice creates separate Vietnamese, Lao or Cambodian states.", {
        "Independent Indochina: +1 TC, -1 dissent": "Guarantee independent Indochina: +1 TC/-1 dissent",
        "Indian puppet Indochina: +2 TC, +3 dissent": "Order Indian protection: +2 TC/+3 dissent", **CANCEL},
        "Puppet conversion requires native verification; the independent action issues a guarantee, not access."),
    9289916: entry("What Victory Leaves Behind",
        "A lasting Central Asian settlement gives India a reason to invest at home. Spend 500 money and 2,000 supplies once on frontier logistics, or add 2 base IC each in Delhi, Bombay and Calcutta where India owns the sites; choosing one closes the other.", {
        "Frontier network: +8 TC and +5 supply output": "Frontier logistics: +8 TC/+5 supply output",
        "Indian industry: +6 base IC across three cities": "Build in India: up to +6 base IC", **CANCEL}),
    9289923: entry("Bring the Peace Home",
        "The home-island campaign and qualifying peace have opened an investment choice for India. Pay 500 money and 2,000 supplies once for ocean logistics and research, or add 2 base IC each in Delhi, Bombay and Calcutta where India owns the sites; this is investment, not Japanese reparations.", {
        "Blue-water future: logistics and research": "Ocean network: +8 TC/+5 supply output/+2 research",
        "Industrial future: +6 base IC in India": "Build in India: up to +6 base IC", **CANCEL}),
    9281913: entry("Across the Fronts",
        "India's commitments stretch from mountain passes to distant sea lanes. Choose a region to inspect its campaign position; opening a report makes no declaration of war or peace.", {
        "Inspect Southern Command": "Read the southern front report",
        "Inspect Western Command": "Read the western front report",
        "Inspect Northern Command": "Read the northern front report",
        "Inspect Global Command": "Read the wider war report", **CANCEL}),
    9282003: entry("Terms Beyond the Mountains",
        "Each northern conflict needs its own terms. Open Afghanistan, Tibet, Xinjiang or the Soviet negotiations to inspect the available settlement; opening a file does not end a war.", {
        "Settle Afghanistan": "Discuss peace with Afghanistan",
        "Settle Tibet": "Discuss Tibet's settlement",
        "Settle Xinjiang and Central Asia": "Discuss Xinjiang and Central Asia",
        "Open the Soviet armistice docket": "Discuss an armistice with Moscow"}),
    9282170: entry("Make the Victory Count",
        "A battlefield result gives Delhi a claim to press. Ask an eligible partner for recognition on a 60/25/15 recognition, conditional-support or refusal roll, keep the claim for India's own peace with -1 dissent, or inspect available great-power armistice terms; a sovereign request records India's own claim.", {
        "Ask the current partner: 60/25/15": "Present the claim: partner reply 60/25/15",
        "Reserve the result for India's separate peace": "Keep India's own claim: -1 dissent",
        "Open the great-power armistice board": "Review great-power armistice terms",
        "Continue operations before making a claim": "Let the fighting continue"}),
    9283212: entry("What Are We Fighting For?",
        "Cooperation with Moscow leaves India with choices about its own campaign. Name an anti-fascist, anti-imperial, republican Asian or autonomous objective; this records a war aim, without declaring war, moving troops or creating an alliance.", {
        "Anti-Fascist Expedition": "Set an anti-fascist campaign objective",
        "Anti-Imperial Ocean War": "Set an anti-imperial ocean objective",
        "A Republican Asian Order": "Set a republican Asian objective",
        "Autonomous Indian Socialism": "Set an autonomous Indian objective"},
        "Legacy charter flow still exists; prose alone does not replace global route mechanics."),
    9283214: entry("India's Purpose in This War",
        "India fights under its own command, but its victories need a purpose. Choose an ocean league, continental security, great-power influence or a republican federation as the campaign objective; this choice alone grants no territory, alliance or peace.", {
        "Build an Indian Ocean League": "Aim for an Indian Ocean league",
        "Secure the Continental Arc": "Aim for continental security",
        "Act as the World Balancer": "Aim to influence the great-power settlement",
        "Build a Republican Federation": "Aim for a republican federation"},
        "Legacy charter flow still exists; prose alone does not replace global route mechanics."),
    9289910: entry("Hold Beyond the Soviet Frontier",
        "The advance must survive a counterattack before Delhi can bargain from strength. Begin the 90-day hold of Baku, Tashkent, Astrakhan and Stalingrad, plus Sverdlovsk, Omsk or Moscow and two complete Soviet-owned republic territories; this records an attempt, not a peace settlement.", {
        "Begin the 90-day consolidation record": "Begin the 90-day hold"}, "The date-based hold mechanism remains unverified in the native engine."),
    9289912: entry("A Northern Claim to Press",
        "The campaign check now permits Delhi to press the northern settlement. Record readiness for negotiations and keep the required positions secure; this action changes no borders and issues no peace order.", {
        "Record the sustained campaign result": "Record readiness for northern negotiations"}, "The underlying 90-day hold requires native verification."),
    9289920: entry("Hold the Japanese Cities",
        "Tokyo, Osaka and Hiroshima are in Indian hands, but the campaign is not over. Begin a 60-day hold while fighting Japan; losing the required position interrupts the attempt, and starting it grants neither territory nor peace.", {
        "Begin the 60-day consolidation record": "Begin the 60-day hold"}, "The date-based hold mechanism remains unverified in the native engine."),
    9289922: entry("The Home-Island Claim",
        "The campaign check now records the home-island hold as earned. This preserves a qualifying achievement for later settlement and investment choices; Japan has not accepted peace through this action.", {
        "Record the sustained campaign result": "Record the earned home-island hold"}, "The underlying 60-day hold requires native verification."),
    9289698: entry("An Old Plan Falls Away",
        "A changed partnership or political direction has overtaken the old campaign plan. Close its active instructions and pending requests; this acknowledgement grants no reward and removes no earned historical achievement.", {
        "Archive the obsolete route contract": "Close the outdated campaign plan"},
        "Compatibility acknowledgement only; future route mechanics require separate redesign."),
}

# Fingerprints of every command in the reviewed authored action set. Formatting
# and inserted no-effect cancellations do not invalidate a review; changed
# command semantics do. Run this pass BEFORE behavioural transformations.
REVIEWED_EFFECTS = {
    9281913: "6e1f79346f0b88aa1f86b01208cd6ad54b0b364e6945ec8e10ee6b6defc8e8d4",
    9282003: "a690167f17c3ffeb33fbb58109a3511c576e1140864ffda5e6807c0ebb5c5d64",
    9289910: "9c141e8cb24c595958e8cc2bb6bfcf431cfed3674d0cfd144bdba00c5c185357",
    9289912: "c071bda02bede6428d1fa253e5ba1abe8e59f6dbdc1bfd7cfd0cdb548577298c",
    9289920: "c5aaaf6516dea764514f963b21189cd7e25e20b41d340d9ea440c4dcc9b646f9",
    9289922: "6640265a295adf2cec154776c4bfe423e8759936864a9d129c23bb47c7a7c6d3",
    9289903: "2db718c46fd2e88fc6a1939c6677fa1e98b0360132e78630d0d5f42778515ae0",
    9289905: "752d80007d7c9f7e6b5d9c3ae96c618c7773b59cd3600497b66d30a83fd4d571",
    9289916: "713426f2d1947f9b43863fd92c9fb2da7afc41b3c388143ce6392c2a9b6b4bb7",
    9289923: "5149ae283431d7c7f37a7d86fec614d5da05fc13d86bf91453b8c5b089ff2403",
    9294013: "9b9221776c82a19f63fd610f5ec6117708d74890a804c88dd4926f9ef97054e3",
    9294015: "b617217038ab41732fff272d6fbf9dd518a9e1b796cd18e4652e26a0ba654e28",
    9297003: "31f9053031bf602b42ad2b1d13774d6cfabd59e716f09ad1bef146b0fc3fd4db",
    9282170: "89817f49e56ce87b896163fd664c64332670fee0d2fd5663ca06943a2e921dcc",
    9282212: "473e982e215fd69978ccb02c3ac5bd87992dc2e55abe2e9ac8d1b11411a743b4",
    9283212: "020dfe6381a3860cb8b117ecc6e0ccc357f964569b2dd723e8800230f786843f",
    9283214: "d5e0571423379ae5f5d0642fa577ad94b2041dee9ae2d836c5864354dc5f5271",
    9289698: "ffe8d5453659191e87ac16370e233e4d364efd460531b95c950261dcffcdcd89",
    9270002: "4bed53ebd9c236222a9d86f10036ada1886677a988e034db4103e1c63ecd8d26",
    9270001: "f0a11187d50ab8b6eb68294a1c67122ae105cc2f6700b353e933d35dbfce8580",
    9270100: "802dfa84cd41e76de603174b4ddf9b387cf6d447618f8180579f6fc955b4ef45",
    9270101: "07586ff8fe216a985ab244ab7350c47d9d85acdf6b4fbf701a24424b8f84fd17",
    9270102: "d14ad93393a2c310a221ae3a514457e7154103602246b60974a05f4cc92f992c",
    9270103: "6ed44680fdb3c7dba7a602608f1b00fe875477f854bb71b6c578e2c5e900c16c",
}


def canonical(node):
    return [(f.key, canonical(f.value) if isinstance(f.value, Node) else f.value)
            for f in node.fields]


def actions(event):
    return [f.value for f in event.fields
            if f.key == "action" or (f.key or "").startswith("action_")]


def effect_bytes(text, event):
    """Exact direct command blocks, including nested conditional command text."""
    return tuple(tuple(text[f.start:f.end] for f in a.fields if f.key == "command")
                 for a in actions(event))


def transform(files: dict[str, str]):
    """Return new files and per-ID review records; unknown IDs remain pending.

    Extra no-effect cancel actions are tolerated. Unknown substantive actions
    cause the entire event to remain untouched and pending, never a partial
    reviewed rewrite. Original names (or exact already-rewritten names), never
    action indices, select the authored labels.
    """
    output, reviews, seen = dict(files), {}, set()
    for path, text in files.items():
        edits = []
        for ef in parse(text).fields:
            if ef.key != "event" or not isinstance(ef.value, Node):
                continue
            event = ef.value
            eid = int(event.get("id"))
            if eid not in CATALOG:
                continue
            seen.add(eid)
            spec = CATALOG[eid]
            authored = spec["actions"]
            by_name = {a.get("name"): a for a in actions(event)}
            expected = set(authored)
            matched = {old: by_name.get(old, by_name.get(new))
                       for old, new in authored.items()}
            extras = [a for name, a in by_name.items()
                      if name not in expected and name not in authored.values()]
            harmless = all(not a.all("command") and
                           ("cancel" in a.get("name", "").lower() or
                            a.get("name") == "Leave this for later") for a in extras)
            duplicate_names = len(by_name) != len(actions(event))
            if any(a is None for a in matched.values()) or not harmless or duplicate_names:
                reviews[eid] = [{"dimension": "prose", "status": "pending", "path": path,
                    "detail": "Action names differ from the reviewed authored source; no text changed."}]
                continue
            signature = [(old, [canonical(c) for c in a.all("command")])
                         for old, a in matched.items() if a.all("command")]
            if sha256(repr(signature).encode()).hexdigest() != REVIEWED_EFFECTS[eid]:
                reviews[eid] = [{"dimension": "prose", "status": "pending", "path": path,
                    "detail": "Commands differ from the reviewed authored snapshot; re-review prose against changed effects."}]
                continue
            changes = [(event.field("name"), spec["title"]),
                       (event.field("desc"), spec["description"])]
            if event.get("decision_desc") is not None:
                changes.append((event.field("decision_desc"), spec["description"]))
            changes.extend((matched[old].field("name"), new) for old, new in authored.items())
            for field, value in changes:
                if field.value != value:
                    edits.append((field.value_start, field.end, '"' + value + '"'))
            commands = effect_bytes(text, event)
            reviews[eid] = [{"dimension": "prose", "status": "reviewed", "path": path,
                "detail": "Explicit authored narrative; original action-name matching; effects unchanged.",
                "actions": list(authored), "caveats": [spec["caveat"]],
                "command_sha256": sha256(repr(commands).encode("utf-8")).hexdigest(),
                "native_effect_disclosure": "Unchanged engine command tooltips remain authoritative."}]
        output[path] = replace(text, edits)
    for eid in CATALOG.keys() - seen:
        reviews[eid] = [{"dimension": "prose", "status": "pending", "path": None,
                        "detail": "Authored event absent from supplied files; no generated ID invented."}]
    return output, reviews
