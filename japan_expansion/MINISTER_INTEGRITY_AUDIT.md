# Complete Japanese minister integrity audit

Checked all **383 installed Japanese appointments**, using **90 distinct personalities** and **482 command entries**. All resolve uniquely, match their office, and avoid Generic fallback. This is a full-roster check, not a Fujiwara-only spot check.

## What changed in the source

No minister balance values required correction. The new final hook generates all 13 added personality descriptions directly from the commands, closing a quiet wording gap: naval equipment research excludes naval doctrines; aircraft equipment research excludes air doctrines; Fleet Carrier means the carrier class, not Light Carrier or CAG; resource/all includes oil and money as well as materials. Cost, time, organisation, morale and chance-point effects are labelled separately. It also validates the complete generated roster after all personnel writers.

The 13 existing descriptions already had matching numeric magnitudes. Their duplicate entries in japan_rising.csv and mods.csv were identical. The new source wording improves scope and prevents later numerical copy drift; it does not claim an engine bug or silently buff every historical minister.

## Full roster and trait coverage

- Original rows: 372; unchanged original rows: 366; modified originals: 6; added appointments: 11.
- Trait names and office tokens resolve case-insensitively, as the native file itself uses mixed case. Head of State, all nine other offices, and default/all position semantics are handled. No used personality relies on the all-office default.
- Every used command type, which category and when scope is checked against the native minister metadata, including concrete custom unit targets. Numeric values must be finite and nonzero. Shared group effects and per-class effects are distinguished.
- Omitted when on unit/extra means both construction cost and time; omitted when on research means time; omitted which on unit/research/resource means all; production defaults to national production. Native Dismal Enigma uses the shipped combined-scope intelligence_network when=all form.
- All 180 used name/description keys resolve to nonempty English. Duplicate keys must agree. No missing or conflicting key was found.
- Dates, ideology codes, roster structure, unique appointment IDs and unique personality IDs/names were checked. Japanese IDs also have no collisions with other installed country minister rosters.
- 8 native rows start in 1999; these deliberate unavailable placeholders were reported and preserved. Validation is not a claim that all 383 appointments should be selectable in 1933.

## Every original-row modification

| ID | Name | Field changes |
| --- | --- | --- |
| 50010 | Yamamoto Isoroku | retirement: 1944 → 1951; end: 1944 → 1951 |
| 50131 | Abe Nobuyuki | trait: School of Fire Support → jx joint logistics |
| 50164 | Sugawara Michio | trait: Air Superiority Doctrine → jx pilot continuity |
| 50167 | Yamamoto Isoroku | retirement: 1944 → 1951; end: 1944 → 1951 |
| 50369 | Higashikuni Naruhiko | retirement: 1946 → 1951 |
| 50370 | Shimomura Sadamu | retirement: 1946 → 1951 |

All other original appointments retain their source fields. Original traits retain every native command. Three inherited personalities (Static Defence, Decisive Battle and Razor) also contain the five R9 concrete Jungle Light parity commands; that class is retired from new recruitment. No native formation effect was replaced or removed.

## All eleven added appointments

| ID | Person / office | Trait | Availability |
| --- | --- | --- | --- |
| 286120 | Nomura Naokuni / Chief of Navy | jx escort priorities | 1944–1951 |
| 286121 | Ikeda Shigeaki / Minister of Armament | jx materials first | 1937–1951 |
| 286122 | Fujiwara Ginjiro (Civil Works) / Minister of Armament | jx civil construction | 1937–1951 |
| 286123 | Kishi Nobusuke / Minister of Armament | jx army workshops | 1937–1951 |
| 286124 | Shigemitsu Mamoru / Foreign Minister | jx commercial diplomacy | 1937–1951 |
| 286125 | Kobayashi Seizo / Minister of Security | jx civilian bargain | 1937–1951 |
| 286126 | Maeda Minoru / Head of Military Intelligence | jx technical intelligence | 1937–1951 |
| 286127 | Nagano Osami / Chief of Navy | jx heavy fleet | 1937–1948 |
| 286128 | Ozawa Jisaburo / Chief of Navy | jx carrier concentration | 1937–1951 |
| 286129 | Tsukahara Nishizo / Chief of Air Force | jx fighter priority | 1937–1951 |
| 286130 | Umezu Yoshijiro / Chief of Army | jx army cohesion | 1937–1950 |

The other two custom traits are Joint Logistics for Abe Nobuyuki as Chief of Staff (50131) and Pilot Continuity for Sugawara Michio as Chief of Air (50164), giving 13 custom personalities across 11 additions and two reassigned original appointments.

## Exact custom effects generated from commands

| Personality | Effects |
| --- | --- |
| jx escort priorities (1201) | Destroyer construction IC cost and time -4% (also convoy escorts). Troop transport construction IC cost and time -4% (also convoy transports). Fleet carrier construction time +3%. Active only while appointed. Other national modifiers still apply. |
| jx pilot continuity (1202) | Air division organisation +5%. Air division morale +5%. Air division construction time +3%. Carrier air group organisation +5%. Carrier air group morale +5%. Carrier air group construction time +3%. Light carrier air group organisation +5%. Light carrier air group morale +5%. Light carrier air group construction time +3%. Active only while appointed. Other national modifiers still apply. |
| jx joint logistics (1203) | Transport capacity +8%. National unit supply consumption -6%. Land division attack -3%. Active only while appointed. Other national modifiers still apply. |
| jx materials first (1210) | All resource output +8% (including oil and money; trade imports excluded). Consumer goods requirement +3%. Active only while appointed. Other national modifiers still apply. |
| jx civil construction (1211) | Infrastructure construction time -12%. Infrastructure construction IC cost -12%. Factory construction time -5%. Factory construction IC cost -5%. Naval division construction time +4%. Active only while appointed. Other national modifiers still apply. |
| jx army workshops (1212) | Supply production +10%. Naval division construction IC cost +5%. Active only while appointed. Other national modifiers still apply. |
| jx commercial diplomacy (1213) | Diplomatic mission cost -15%. Alliance acceptance modifier -5 points. Active only while appointed. Other national modifiers still apply. |
| jx civilian bargain (1214) | Consumer goods requirement -5%. Supply production -3%. Active only while appointed. Other national modifiers still apply. |
| jx technical intelligence (1215) | Naval equipment research time -4% (doctrines excluded). Aircraft equipment research time +2% (doctrines excluded). Active only while appointed. Other national modifiers still apply. |
| jx heavy fleet (1216) | Battleship attack +5%. Battlecruiser attack +5%. Fleet carrier construction time +5%. Active only while appointed. Other national modifiers still apply. |
| jx carrier concentration (1217) | Fleet carrier construction time -6%. Fleet carrier organisation +3%. Battleship construction time +8%. Active only while appointed. Other national modifiers still apply. |
| jx fighter priority (1218) | Interceptor construction IC cost -6%. Interceptor organisation +3%. Naval bomber construction IC cost +4%. Active only while appointed. Other national modifiers still apply. |
| jx army cohesion (1219) | Land division organisation +4%. National unit supply consumption +4%. Active only while appointed. Other national modifiers still apply. |

## Evidence and validation

- Every installed Japanese appointment resolves uniquely, matches its office and has valid dates/ideology; no Generic fallback.
- All original appointment IDs survive; exactly six original rows differ and eleven appointments were added.
- All Japanese appointment IDs are unique across the installed country minister rosters.
- All 180 used trait name/description keys resolve to nonempty English; duplicated keys have identical text.
- All 13 custom descriptions contain exactly their command magnitudes; alliance chance uses points, percentage commands use fractions.
- Final source hooks round-trip all 383 appointments and 482 used-trait commands; new subtype effects preserve their native parent magnitudes and penalties.
- All 6 negative fixtures are rejected: missing trait, office mismatch, duplicate appointment, bad ideology, bad category and bad timing.
- Installed roster/personality hashes are unchanged by this audit; no installation or game launch.

Primary evidence: installed and baseline db/ministers/ministers_jap.csv; native minister_personalities.txt header and definitions; db/units/division_types.txt and brigade_types.txt; all installed config CSV files. Full 383-row mapping is in MINISTER_INTEGRITY_ROSTER.csv; the JSON includes every normalized command, localisation source, original diff and installed-file hash.

Integration: call minister_integrity.apply() after force_delivery_audit.apply(), before localisation generation. Call minister_integrity.apply_personnel(TARGET, read, write, parse, serialise) after all other personnel writers. No additional installation files or new personality IDs are required.

Limits: this validates source and installed data against shipped command contracts. It does not launch the engine, appoint every minister, measure save-game cached effects, or claim every political event/ideology makes every person available. No saves or German mod files were edited.
