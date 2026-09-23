# 27-BALANCE1 — fresh-campaign playtest patch

13 September 2026. Target: the existing Steam mod **AUBM Terrain Prototype P1**.
This is a delta on the actually installed Candidate5/Jade1 plus campaign fixes,
not a rebuild from the older repository overlay. Start a **new 1933 campaign**.
Old saves are neither migrated nor balance-compatible with the new naval cycle.
They remain on disk, untouched. The installer keeps a complete delta backup.

Installed locally on 13 September 2026: **118 delta files**. Post-install checks
matched **993 input/output hashes** with zero mismatches. **29 save-folder files**
were unchanged. All **34 regression tests pass**, including backup, conflict
refusal and rollback tests in temporary directories. The full registered set
contains **8,902 events in 158 files**, with no syntax/duplicate-ID errors found.
The actual Steam launcher setting still selects AUBM Terrain Prototype P1.
This evidence does not replace an in-engine launch or campaign playtest.

## What should feel different

India still grows into a powerful naval and industrial state. The purpose is to
keep that enjoyable catch-up while making resource investment, specialist forces
and enemy reactions matter. No new alliance route or strategic menu was added.
The extra resource projects are finite choices; AI support stays hidden.

### Navy: a modest brake, not a small-navy campaign

The mature national-yard standard remains **25% off the base schedule in peace**.
War adds 15 rather than 25 points: **40% instead of 50%**. Returning to peace
removes exactly those 15 points. Normal technology effects still stack; daily
IC cost, ship combat stats and existing naval programme rewards are unchanged.

That is not merely a 10% change in the finished build time. The local engine
documentation says relative schedule commands use **model 0's time for every
model**. For a model6 light cruiser (1,090 days, with a 960-day model0 baseline),
an illustrative 221-day technology reduction gives 389 days under the old war
standard, 485 under the new one, and 869 with that technology but no Indian yard
bonus. Engine rounding and other modifiers can change actual queue dates. This
illustrates why India's catch-up remains strong despite the smaller headline
advantage.

The tests exercise repeated fresh-game peace/war transitions. They do **not**
make the old -50% save state compatible. The old campaign would mix standards.

### Industry and resources are balanced together

Maximum direct factories across the seven development events fall from **140
to 114 IC**. The development/resource chains' maximum cumulative positive
general factory-output additions fall from **16 to 4 percentage points**.
This is a limit on these chains, not a universal cap on every Indian modifier.
Political, technology, minister and other existing modifiers still apply.

Every major new factory package now expands provincial raw-material production.
Lower-factory choices offer stronger mines, fuel, transport, research or immediate
stores. Resource programmes no longer compound factory demand with extra generic
IC multipliers. Costs and the actual improved provinces are checked before paying.

| Development event | Choices after BALANCE1 |
|---|---|
| Emergency Reconstruction | 20 IC and basic supporting mines with no dissent penalty; 14 IC with stronger mines, roads and relief; or 10 IC with ready supplies and less manpower committed. |
| Steel, Coal and Machine Tools | 24 IC and a small output improvement; 18 IC with stronger mining; or 12 IC with lower outlay. |
| Power for a Continent | 18 IC/70 energy; 14 IC/95 energy; or 10 IC/45 energy plus roads and relief. |
| Second National Plan | 26 IC plus supporting materials; 20 IC plus stronger materials, fuel and transport; or 12 IC plus research. |
| Industrial Power | Final 8 IC, supporting resources and a reduced output improvement. |
| Federal Works | Eight regional links +10 infrastructure and relief; four trunk links +20 infrastructure and transport; or no central spending with only modest relief. |

Resource investments are permanent additions to the named provinces, **not
automatic refills of national stockpiles**. Losing the provinces matters.

| Resource event | Main production choices |
|---|---|
| Survey | Diversified 24 energy/12 metal/6 rares, or eastern 32 energy/16 metal. |
| Coal corridor | 70 energy/20 metal plus railways, or cheaper 50 energy/14 metal. |
| Tata-Bhilai | 60 metal/35 energy plus transport, or cheaper 45 metal/28 energy without a manpower levy. Neither adds another IC multiplier. |
| Assam | Protected 50 oil/24 energy with roads, or faster 65 oil with unrest. |
| Central grid | Integrated 80 energy/25 metal with roads, or power-first 105 energy/16 metal. |
| Refineries | Coastal 90 oil, or inland 80 oil with 20 energy output permanently committed to conversion. |
| Rare materials | Domestic 40 rares/18 metal daily, or a one-time import reserve of 10,000 rares, 6,000 metal and 4,000 oil. |
| Resource security | Domestic 90 energy/50 metal/12 rares/30 oil, or smaller mines with immediate trade reserves. |
| Completed grid | Another 35 energy/20 metal/12 rares/20 oil and transport improvement. |
| 1941: Fuel for a World Fleet | 80 oil/20 energy, or 40 oil/80 energy/40 metal/20 rares. Requires the refinery programme. |
| 1943: Resources for a Long War | 100 oil/20 energy, or 50 oil/80 energy/40 metal/20 rares. Requires the 1941 project. |

Each late project has one shared completion flag for its two alternatives and a
free defer. They consume money, supplies and manpower; no repeated grants or
free factories. These changes improve supply capacity but do not guarantee a
resource surplus at any fleet or army size. Trade, oil conservation, convoys and
working infrastructure still matter. No claim that a fresh campaign has already
proven these numerical choices balanced.

### Playtest repairs

See the [event-by-event repair record](BALANCE1_PLAYTEST.md) for all 21 existing
events and four hidden helpers. Main changes:

- Eight inherited locked state divisions now release with Provincial Forces,
  or at India's first war if that decision has not done it.
- Airfield Security now gives **early aircraft, two guards and base improvements**.
  Choose interception, a forward interceptor/bomber group, or air transport.
  Valid starting models and permitted attachments replace guessed model selection.
- Tokyo's early proposition has a free defer which genuinely preserves later
  talks. It is suppressed during Japanese war or an existing major commitment.
- Dissent no longer decides nearly every political choice. Army, schools,
  citizenship, Burma, League and London choices have more distinct benefits.
- Northern provisional recognition requires Baku/Astrakhan/Stalingrad, **or**
  Samarkand/Tashkent/Alma-Ata/Sverdlovsk, held for 60 days during Soviet war.
  Losing a required centre invalidates that attempt. Recovery requires a fresh
  hold; recognition still is not final Soviet surrender or automatic puppets.
- Fixed the malformed empty stock Japanese minister event5200093 by restoring
  a no-effect action wrapper. No new appointment or minister change is imposed.

The existing mountain-training team was already repaired in this installation;
it is not duplicated. The ambiguous early “Nationalise/Provincialise” report
needs an exact event name before it can be counted as resolved. Abyssinia text
is shorter; no explicit colour-control leak was found in that source. Actual
popup colours/layout remain a native-playtest check. Additional unnamed bugs
are not assumed fixed.

### World AI and opposition to India

See [the full AI change record](BALANCE1_WORLD_AI.md). Seven major opponents
(Britain, Japan, USSR, Germany, Italy, USA and Australia) get guarded reactive
human-front behaviour when actually fighting human India. It is not tied to a
pro-/anti-Japan route and does not generate armies for them. Stock AI switches
reapply the narrow response when relevant; peace/alliance disables it.

Finland retains homeland defence after small territorial losses. Germany can
provide finite paid African and Finnish reserve corps when the allied war and
friendly-port conditions exist. These are reserve-force abstractions, not
literal movement of existing formations. Italy retains overseas-defence capacity;
important Italian/Balkan, Norwegian, Soviet, British and Japanese points receive
garrison priorities. British attack/landing preferences become less speculative.

This does **not** promise a particular historical outcome, prevent Germany
losing, or make the USSR immune to a well-timed second front. Better use of
existing forces is the first correction; there is no blanket Axis combat buff
or infinite emergency army spawning. Native campaigns must establish effectiveness.

## Build, identification and rollback

Run `python tools/build_balance1.py` to stage and validate against its immutable
snapshot under `build/balance1/baseline`. `--install` writes only the declared
delta after checking live preimage hashes and confirming the game is closed.
The previous files are in `build/balance1/backups/<timestamp>`, accompanied by a
rollback manifest. The installer does not touch savegames, map art, portraits,
country colours, unit definitions or the original Blood and Iron installation.

Identification uses real text surfaces: the main-menu play button says
**PLAY 27-BALANCE1**, the 1933 scenario says
**India 1933 - 27-BALANCE1 [NEW GAME PLAYTEST]**, and the first Indian event says
**AUBM 27-BALANCE1 - New Campaign**. Legacy background artwork is unchanged;
the text label and install receipt identify this gameplay delta.

Validation results: `build/balance1/validation.json`. Exact installed hashes and
backup path: `build/balance1/install-receipt.json` and the matching receipt in
the live mod. Tests are static/regression checks; **no game was launched or
advanced** during this patch. This is ready for a fresh human playtest after a
successful install receipt, not a claim of completed in-engine balance testing.
