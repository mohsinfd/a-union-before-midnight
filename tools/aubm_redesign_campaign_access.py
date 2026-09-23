"""Bounded staged campaign access, independent of a national route or opt-in.

Pure transform AFTER diplomacy/cooperation. Only enumerated opponent lifecycles
in authored module 43 are changed. Full sovereignty/hostility/milestone/consent
conditions outside the exact old access wrapper survive. Treaty benefits,
training, commands and province/reward data are not rewritten.

Friendly alliances do not bar ordinary enemy objectives. India must exist, be
sovereign and not be allied with the relevant former/current imperial enemy.
This is NOT an authorization for a separate peace or puppet transaction; their
other existing transaction gates remain. Native timers and transactions still
need engine testing. Unlisted families remain pending.
"""
from __future__ import annotations

from dh_save_spans import Node, parse, replace

MARKER = "# AUBM_STAGED_CAMPAIGN_ACCESS_V1"
SOURCE_MODULE = "43_wartime_settlements.txt"
LEGACY_SOVEREIGN = (
    "flag = ind_aubm_route_sovereign NOT = { ispuppet = IND } "
    + " ".join("NOT = { alliance = { country = IND country = " + tag + " } }"
               for tag in ("ENG", "GER", "SOV", "JAP", "USA"))
    + " " + " ".join("NOT = { flag = ind_aubm_commitment_" + route + " }"
                     for route in ("allied", "german", "soviet", "japan")))
SIAM_ROUTES = " ".join("flag = ind_aubm_route_" + r
                       for r in ("sovereign", "allied", "german", "soviet"))

# Each list is a reviewed lifecycle, including invalidation and foreign reply
# leaves. Editing only the Indian menu would otherwise strand the callback.
FAMILIES = {
    "war_observation": (9289804, 9289805),
    "nanjing": (9289850, 9289851, 9289852, 9289853,
                9289900, 9289901, 9289902, 9289903, 9289904, 9289905,
                9289940, 9289941),
    "indochina": tuple(range(9294010, 9294020)),
    "siam": tuple(range(9297000, 9297009)),
    "japan": (9289920, 9289921, 9289922, 9289923),
    "soviet": (9282036, 9282037, 9282038, 9282040, 9282043, 9282044,
               9282046, 9289870, 9289910, 9289911, 9289912, 9289914,
               9289915, 9289916, *range(9289942, 9289952)),
}
EVENT_FAMILY = {eid: family for family, ids in FAMILIES.items() for eid in ids}
OPPONENT = {eid: ("SOV" if family == "soviet" or eid == 9289805 else "JAP")
            for eid, family in EVENT_FAMILY.items()}
UNHANDLED_FAMILIES = (
    "Colonial petitions, equal reconstruction treaties and southern conference",
    "Canal defence, Himalayan protectorate and replacement training",
    "Authored route charters, partner benefits and postwar congresses",
    "General British/German/American campaigns and transaction eligibility",
)


def canonical(node):
    return tuple((f.key, canonical(f.value) if isinstance(f.value, Node) else f.value)
                 for f in node.fields)


OLD_SOVEREIGN = canonical(parse(LEGACY_SOVEREIGN))
OLD_SIAM_ROUTES = canonical(parse(SIAM_ROUTES))


def sovereign_enemy_guard(enemy):
    return ("exists = IND NOT = { ispuppet = IND } "
            "NOT = { alliance = { country = IND country = " + enemy + " } }")


def predicate_roots(event):
    """Topmost condition blocks, including action/conditional-command gates."""
    def visit(node):
        for f in node.fields:
            if not isinstance(f.value, Node):
                continue
            if f.key in {"trigger", "decision", "decision_trigger"}:
                yield f.value
            elif f.key == "command" or (f.key or "").startswith("action"):
                yield from visit(f.value)
    yield from visit(event)


def access_edits(event, enemy):
    edits, kinds = [], []

    def visit(node):
        for f in node.fields:
            if isinstance(f.value, Node):
                signature = canonical(f.value)
                if f.key == "AND" and signature == OLD_SOVEREIGN:
                    edits.append((f.start, f.end,
                                  "AND = { " + sovereign_enemy_guard(enemy) + " }"))
                    kinds.append("sovereign_route_and_unrelated_bloc_exclusions")
                elif f.key == "OR" and signature == OLD_SIAM_ROUTES:
                    # Siam already carries its real war, sovereignty and enemy
                    # alliance checks around this purely ideological whitelist.
                    edits.append((f.start, f.end, "exists = IND"))
                    kinds.append("siam_route_whitelist")
                else:
                    visit(f.value)
            elif f.key == "flag" and f.value == "ind_lib1_enabled":
                edits.append((f.start, f.end, "exists = IND"))
                kinds.append("manual_liberator_opt_in")

    for root in predicate_roots(event):
        visit(root)
    return edits, kinds


def transform(files: dict[str, str]):
    output, reviews, seen = dict(files), {}, set()
    for path, text in files.items():
        if str(path).replace("\\", "/").rsplit("/", 1)[-1] != SOURCE_MODULE:
            continue
        edits = []
        for ef in parse(text).fields:
            if ef.key != "event" or not isinstance(ef.value, Node):
                continue
            event = ef.value
            eid = int(event.get("id"))
            if eid not in OPPONENT:
                continue
            seen.add(eid)
            changes, kinds = access_edits(event, OPPONENT[eid])
            already = MARKER in text[event.start:event.end]
            if changes:
                edits.extend(changes)
                if not already:
                    edits.append((event.start + 1, event.start + 1, "\n " + MARKER + "\n"))
            reviews[eid] = [{
                "dimension": "campaign_access", "status": "reviewed", "path": path,
                "family": EVENT_FAMILY[eid], "opponent": OPPONENT[eid],
                "changed_predicates": len(changes), "changes": sorted(set(kinds)),
                "detail": ("Removed only matched route/opt-in wrappers; battlefield, consent, "
                           "pending, terminal and transaction conditions remain." if changes or already
                           else "Continuation inspected: no matching route/opt-in wrapper to remove."),
                "caveats": ["Native timers and peace/government transactions remain unverified.",
                            "Historical participation flags remain; automatic war observers now need no opt-in."]}]
        output[path] = replace(text, edits)
    for eid in OPPONENT.keys() - seen:
        reviews[eid] = [{"dimension": "campaign_access", "status": "pending", "path": None,
                        "family": EVENT_FAMILY[eid],
                        "detail": "Authored lifecycle event absent; no generated event invented."}]
    return output, reviews
