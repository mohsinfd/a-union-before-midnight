"""Read-only, occurrence-complete inventory of DH event redesign coverage.

Static classification is not a prose review, reachability proof, or engine test.
``files`` maps module-relative paths to Latin-1-decoded source text. ``reviewed``
maps event IDs (int/string), or occurrence keys ``path#ordinal``, to records with
disposition, reasons, human_authored_reviewed, human_review_evidence,
engine_tested, and engine_test_evidence. Review flags require explicit evidence.
An optional source_sha256 binds a review to that exact event block.

CLI reads sources and optional JSON review/save-reference data, and only writes
the requested report. It never changes modules, installs a mod, or edits saves.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

try:
    from .dh_save_spans import Node, parse, walk
except ImportError:
    from dh_save_spans import Node, parse, walk


DISPOSITIONS = {"pending", "keep", "rewrite", "retire"}
LINK_COMMANDS = {"event", "trigger"}


def _id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _plain(value):
    """Represent repeated fields and bare atoms without losing their order."""
    if isinstance(value, Node):
        return [{"key": f.key, "value": _plain(f.value)} for f in value.fields]
    return value


def _requires_ai(node):
    """Only recognize mandatory positive AI guards in conjunctions.

    An AI predicate somewhere inside OR/NOT, an ai_chance, or one_action does
    not establish that a human cannot see the event. This is deliberately
    incomplete rather than an emulator of DH's predicate semantics.
    """
    return isinstance(node, Node) and any(
        (f.key == "ai" and f.value == "yes")
        or (f.key == "AND" and _requires_ai(f.value))
        for f in node.fields
    )


def _references(refs):
    """Accept {queued_ids: [...], history_ids: [...], slept_ids: [...]}.

    References are supplied observations, not proof that an event ran or was
    shown to a player. A bare iterable is shorthand for referenced_ids.
    """
    if refs is None:
        return {}
    if not isinstance(refs, dict):
        refs = {"referenced_ids": refs}
    allowed = {"queued_ids", "history_ids", "slept_ids", "referenced_ids"}
    if set(refs) - allowed:
        raise ValueError("Unknown save-reference fields: " + str(sorted(set(refs) - allowed)))
    result = {}
    for key, values in refs.items():
        parsed = [_id(v) for v in values]
        if None in parsed:
            raise ValueError(f"Non-numeric ID in {key}")
        result[key] = set(parsed)
    return result


def _review(record, digest):
    if record is None:
        record = {}
    if not isinstance(record, dict):
        raise ValueError("Review entries must be objects with explicit dispositions and evidence")
    disposition = record.get("disposition", "pending")
    if disposition not in DISPOSITIONS:
        raise ValueError(f"Invalid disposition: {disposition}")
    reasons = record.get("reasons", [])
    if isinstance(reasons, str):
        reasons = [reasons]
    if not isinstance(reasons, list) or not all(isinstance(r, str) and r.strip() for r in reasons):
        raise ValueError("Review reasons must be nonempty strings")
    if disposition != "pending" and not reasons:
        raise ValueError("A non-pending disposition requires reasons")
    result = {"disposition": disposition, "disposition_reasons": list(reasons),
              "human_authored_reviewed": False, "human_review_evidence": [],
              "engine_tested": False, "engine_test_evidence": [], "review_stale": False}
    for flag, evidence_key in (("human_authored_reviewed", "human_review_evidence"),
                               ("engine_tested", "engine_test_evidence")):
        value = record.get(flag, False)
        if not isinstance(value, bool):
            raise ValueError(f"{flag} must be boolean")
        evidence = record.get(evidence_key, [])
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list) or not all(isinstance(e, str) and e.strip() for e in evidence):
            raise ValueError(f"{evidence_key} must contain evidence descriptions or artifact paths")
        if value and not evidence:
            raise ValueError(f"{flag} requires {evidence_key}; static parsing is not evidence")
        result[flag], result[evidence_key] = value, evidence
    if record.get("source_sha256", digest) != digest:
        result.update(disposition="pending", human_authored_reviewed=False,
                      engine_tested=False, review_stale=True)
        result["disposition_reasons"].append("Review hash does not match this source event; review again.")
    if not result["disposition_reasons"]:
        result["disposition_reasons"] = ["UNREVIEWED: requires an explicit authored disposition."]
    return result


def inventory(files: dict[str, str], reviewed: dict | None = None, *,
              slept_1933_ids=None, latest_save_refs=None) -> dict:
    """Inventory every top-level event occurrence, including duplicate IDs.

    Unknown visibility, foreign receivers, internal-looking names, slept IDs,
    and unreachable-looking callbacks are never automatically disposed of.
    Callback targets absent from this input are unresolved *within this scope*;
    they may legitimately exist in stock files not supplied to this function.
    """
    reviews = reviewed or {}
    slept = _references({"slept_ids": slept_1933_ids or []})["slept_ids"]
    save_refs = _references(latest_save_refs)
    events, modules = [], []
    for path, text in sorted(files.items()):
        try:
            root = parse(text)
        except ValueError as exc:
            # Fail closed: no report may claim complete coverage of a bad file.
            raise ValueError(f"Cannot inventory {path}: {exc}") from exc
        occurrences = root.all("event")
        if any(not isinstance(ev, Node) for ev in occurrences):
            raise ValueError(f"{path}: expected event definitions, found scalar event field")
        modules.append({"path": path, "event_count": len(occurrences),
                        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
        for ordinal, ev in enumerate(occurrences, 1):
            eid, country = _id(ev.get("id")), ev.get("country")
            occurrence = f"{path}#{ordinal}"
            digest = hashlib.sha256(text[ev.start:ev.end].encode("utf-8")).hexdigest()
            record = reviews.get(occurrence, reviews.get(eid, reviews.get(str(eid))))
            actions, links, effects = [], [], []
            for af in ev.fields:
                if not (af.key == "action" or (af.key or "").startswith("action_")):
                    continue
                if not isinstance(af.value, Node):
                    raise ValueError(f"{occurrence}: malformed action {af.key}")
                action = af.value
                commands = [cmd for n in walk(action) for cmd in n.all("command")]
                if any(not isinstance(cmd, Node) for cmd in commands):
                    raise ValueError(f"{occurrence}: malformed command")
                action_effects = []
                for cmd in commands:
                    kind = cmd.get("type")
                    if kind in LINK_COMMANDS:
                        links.append({"target_id": _id(cmd.get("which")),
                                      "target_id_raw": cmd.get("which"), "command": kind,
                                      "action_index": len(actions),
                                      "country": cmd.get("where", cmd.get("country")),
                                      "where": cmd.get("where"),
                                      "delay": {k: cmd.get(k) for k in ("when", "days", "hours")
                                                if cmd.get(k) is not None},
                                      "conditional": isinstance(cmd.get("trigger"), Node)})
                    elif cmd.fields:
                        # Unknown commands are conservatively effects, never safe navigation.
                        action_effects.append(kind or "unknown_command")
                effects.extend(action_effects)
                actions.append({"key": af.key, "index": len(actions), "name": action.get("name"),
                                "trigger": _plain(action.get("trigger")),
                                "commands": [_plain(cmd) for cmd in commands],
                                "command_count": len(commands), "effect_commands": action_effects,
                                "empty_exit_candidate": not any(cmd.fields for cmd in commands)})
            ai_guard = _requires_ai(ev.get("trigger"))
            if country == "IND":
                visibility = "ai_only_guard_candidate" if ai_guard else "human_facing_candidate"
            elif country:
                visibility = "foreign_receiver_unreviewed"
            else:
                visibility = "unknown_visibility_unreviewed"
            entry = []
            if isinstance(ev.get("date"), Node):
                entry.append("calendar")
            if isinstance(ev.get("decision"), Node):
                entry.append("decision")
            if ev.get("random") == "yes":
                entry.append("random")
            if eid in save_refs.get("queued_ids", set()):
                entry.append("queued_in_latest_save")
            review = _review(record, digest)
            events.append({"id": eid, "id_raw": ev.get("id"), "occurrence": occurrence,
                           "module": path, "ordinal": ordinal,
                           "line": text.count("\n", 0, ev.start) + 1, "source_sha256": digest,
                           "country": country, "name": ev.get("name"), "description": ev.get("desc"),
                           "actions": actions, "action_count": len(actions), "direct_links": links,
                           "effect_commands": sorted(set(effects)),
                           "effect_class": "effectful" if effects else "navigation_only" if links else "no_effects",
                           "visibility": visibility, "mandatory_positive_ai_guard": ai_guard,
                           "human_facing_candidate": country == "IND" and not ai_guard,
                           "entry_points": entry,
                           "trigger": _plain(ev.get("trigger")), "decision": _plain(ev.get("decision")),
                           "date": _plain(ev.get("date")), "deathdate": _plain(ev.get("deathdate")),
                           "lifecycle": "persistent" if ev.get("persistent") == "yes" else "one_time_default",
                           "retirement": "proposed_by_review" if review["disposition"] == "retire" else "not_established",
                           "slept_in_1933": eid in slept,
                           "latest_save_references": sorted(k for k, ids in save_refs.items() if eid in ids),
                           "machine_reviewed": True,
                           "machine_review_scope": "structural_inventory_only",
                           "branch_closure": "unverified", **review})
    ids = Counter(ev["id"] for ev in events if ev["id"] is not None)
    inbound = {eid: [] for eid in ids}
    missing = []
    for ev in events:
        for link in ev["direct_links"]:
            ref = {"source_id": ev["id"], "source_occurrence": ev["occurrence"], **link}
            if link["target_id"] in ids:
                inbound[link["target_id"]].append(ref)
            else:
                missing.append(ref)
    for ev in events:
        ev["incoming_links"] = inbound.get(ev["id"], [])
        if ev["incoming_links"]:
            ev["entry_points"].append("direct_callback")
        if not ev["entry_points"]:
            ev["entry_points"].append("unknown_or_external_callback")
        ev["classification_reasons"] = [
            "Receiver and visible script fields identify candidates; visibility is not engine-proven.",
            "Sleep/history/queue observations do not prove permanent retirement or successful execution.",
        ]
    return {"schema_version": 1, "scope": "supplied_modules_only", "modules": modules, "events": events,
            "coverage": {"module_count": len(modules), "event_occurrences": len(events),
                         "unique_event_ids": len(ids), "all_occurrences_accounted_for": True,
                         "events_without_numeric_id": sum(ev["id"] is None for ev in events),
                         "machine_reviewed": len(events),
                         "human_authored_reviewed": sum(ev["human_authored_reviewed"] for ev in events),
                         "engine_tested": sum(ev["engine_tested"] for ev in events),
                         "human_facing_candidates": sum(ev["human_facing_candidate"] for ev in events),
                         "dispositions": {d: sum(ev["disposition"] == d for ev in events) for d in sorted(DISPOSITIONS)},
                         "visibility": dict(Counter(ev["visibility"] for ev in events))},
            "duplicate_ids": {str(eid): [ev["occurrence"] for ev in events if ev["id"] == eid]
                              for eid, count in sorted(ids.items()) if count > 1},
            "callback_missing": missing,
            "callback_missing_scope": "Targets absent from supplied modules; stock/external targets may exist.",
            "unmatched_review_keys": sorted(str(k) for k in reviews if not any(
                k in (ev["occurrence"], ev["id"], str(ev["id"])) for ev in events)),
            "limitations": ["Static inventory does not verify prose quality, runtime visibility, branch closure, or engine behavior.",
                            "machine_reviewed means structurally inventoried, not redesign completed.",
                            "Explicit review and test evidence are caller-supplied attestations, not independently verified."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="Root under which module paths are reported")
    parser.add_argument("--glob", action="append", dest="globs", help="Repeatable module pattern (default **/*.txt)")
    parser.add_argument("--reviewed", type=Path, help="JSON mapping of explicit review records")
    parser.add_argument("--slept-1933", type=Path, help="JSON array of slept event IDs")
    parser.add_argument("--latest-save-refs", type=Path, help="JSON object of observed queued/history/slept IDs")
    parser.add_argument("--output", type=Path, help="Report path; omitted means stdout")
    args = parser.parse_args()
    source_root = args.source_root.resolve(strict=True)
    paths = sorted({p for pattern in (args.globs or ["**/*.txt"]) for p in source_root.glob(pattern) if p.is_file()})
    if not paths:
        parser.error("No source modules matched")
    if args.output and (args.output.resolve() in {p.resolve() for p in paths}
                        or args.output.suffix.lower() != ".json"):
        parser.error("Output must be a separate .json report, never a source module")
    def read_json(path):
        return json.loads(path.read_text(encoding="utf-8")) if path else None
    report = inventory({p.relative_to(source_root).as_posix(): p.read_bytes().decode("latin1") for p in paths},
                       read_json(args.reviewed), slept_1933_ids=read_json(args.slept_1933),
                       latest_save_refs=read_json(args.latest_save_refs))
    rendered = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
