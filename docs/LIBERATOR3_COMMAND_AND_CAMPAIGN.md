# LIBERATOR3 / COMMAND-RESERVE1

Implemented for the active **AUBM Terrain Prototype P1** installation and the
reviewed **1 August 1941** campaign. This extends LIBERATOR2; it does not replace
its deep Chinese, Soviet, Japanese or independent-mission victory requirements.
No manpower, supplies, production, unit-strength, tech or combat-stat buffs were
added by this patch. No game was launched for verification.

## Load-crash correction: LIBERATOR3-HOTFIX1

The user's first engine load failed with `unknown lhs in game-event: action_e`
at line 20060 of module 43. The generator incorrectly continued legacy button
names beyond `action_d`; Darkest Hour requires repeated plain `action` blocks
for extra buttons. Earlier synthetic tests accepted those invalid names and
the static validator did not reject them. The earlier “zero errors” result was
therefore insufficient evidence of engine compatibility.

HOTFIX1 corrects only those button-key tokens, preserving every button, condition,
effect and option order. The generator and validators now explicitly enforce the
native grammar, including checks of repeatable plain actions. **Use the same
LIBERATOR3_India_1941-08-01.eug save.** No save, commander, AI, resource, unit,
history or visual change is needed. Crash evidence and the previous module are
backed up under `tmp/liberator3-hotfix1-<timestamp>`.

The syntax error is confirmed by the engine log; the corrected file still needs
the user's next load to confirm there is no further engine-level error. No game
was launched or controlled for this correction.

## Which save to load

Use **LIBERATOR3_India_1941-08-01.eug**, not the unchanged original autosave.
Its display title begins LIBERATOR3. The matching `.eug.cfg` is an identical
copy of the original settings companion. Do not move the `.eug` alone.

The repair adds unassigned reserve leaders and removes Japan's obsolete Indian
partnership AI restrictions. Every pre-existing byte in India's country block
is preserved, except for inserting the new leader records. Existing leaders,
assigned commands, reorganisations, units, equipment, production, research,
resources and domestic policy are untouched. Global wars, alliances, flags and
history are unchanged. Other countries except the scoped Japanese AI edit are
byte-identical. The save's display title and companion-settings path change.

The original autosave is never overwritten. Installer receipts and backups are
under `tmp/liberator3-install-<timestamp>`; the active mod receives `LIBERATOR3.json`.
The separate **A Union Before Midnight V4.2** installation, visuals, launcher
selection and original saves are protected. A new campaign is not required.

## Commander capacity

The expansion is a fictional, alternate-history academy reserve, marked **(R)**
in leader names. It uses the game's anonymous portrait, not mislabelled historical
photographs. No original officer's rank, skill, traits, dates or portrait changes.
New officers start at skill 2 or 3, with maximum skill 5 or 6, ordinary promotion
schedules and specialist rather than universally stacked traits.

| Availability | Added land | Added naval | Added air |
| --- | ---: | ---: | ---: |
| 1933 intake | 80 | 30 | 40 |
| 1936 intake | 40 | 20 | 20 |
| 1939 intake | 40 | 15 | 20 |
| 1944 intake | 40 | 10 | 20 |
| Total additions | 200 | 75 | 100 |

The source roster has **245 land, 80 naval and 98 air** officers active in 1939,
and **284/90/120** in 1944. The repaired 1941 save retains its already-loaded
historical officers, including officers still present past source end dates;
therefore it has **256 land, 80 naval and 98 air currently available**, counting
assigned officers. Do not equate source year filtering with the live save pool.

Planning envelope: roughly **600 land divisions in 200 corps, 300 ships in 60
fleets, and 240 air wings in 80 groups**, with reserve commanders. This is not an
unlimited pool or a promise of one leader for every individual ship/division.
Normal command limits and promotion penalties still apply.

The pre-1944 reserve alone adds at least 24 commando and 24 armoured specialists,
12 each for jungle, mountain, hills and winter work, 24 submarine commanders,
24 naval superior tacticians, and 20 each of naval-air, ground-attack and
strategic-bombing specialists. Existing specialists remain additional.

## Japan's abandoned-partnership AI

The reviewed save retained India's senior-partner profile even after lawful
withdrawal: protect India, avoid Indian land fronts and ignore many Indian Ocean
naval areas. The repaired save removes those restrictions immediately, restores
independent southern targeting, and preserves unrelated Japanese research,
production and other AI state.

For future games and unmodified compatible saves, a guarded Japanese maintenance
event runs once after a real rupture, provided the partnership and alliance are
both absent. A renewed partnership rearms this cleanup for a later withdrawal.
It is not a continuous override of Japan's normal wartime AI. It declares no war,
creates no troops and provides no resources. This does not guarantee Japan will
choose a particular war or solve all opponent-AI weaknesses.

## Wait for Japanese aggression

Enable the sovereign Liberator programme from 1940 and remain sovereign.
The programme observes countries at peace with Japan. If Japan subsequently
attacks one, a notification tells India that optional intervention is available.

1. Continue waiting, without cost, if you are not ready.
2. Open **Respond to Japanese Aggression** when ready.
3. Review the declaration and then explicitly confirm **Declare war on Japan
   now: +2 dissent**.

The +2 is the scripted dissent charge. Engine alliance/puppet and declaration
rules still apply. India does not join Britain or America, and an existing
Indian-Soviet war continues. Every confirmation rechecks sovereign status and a
still ongoing witnessed Japanese war. Cancel at either page does nothing.
If Japan attacks India directly, India is already at war and needs no intervention
decision. Existing unrelated declarations remain available by their old rules.

The country-scoped `attack = JAP` trigger is used, not simply “Japan is at war.”
A war already underway when observation begins is deliberately not relabelled
fresh aggression. The programme needs a peaceful baseline first. It covers all
340 playable country-table tags other than India, Japan and special sentinels.
Observers run daily; a war beginning before the first peaceful observation or
ending between daily checks can be missed. It cannot retrospectively attribute
an old war from a mid-war save. No promise of an exact Japanese attack date.

## Japanese-client Indochina

This is distinct from liberating Japanese-occupied territory belonging to a
friendly colonial owner. It handles **U03 as Japan's puppet and ally**, the actual
state in the reviewed save.

1. Fight Japan and U03. India must hold **Hanoi, Dong Hoi, Da Nang, Saigon and
   Can Tho**, with legal ownership still U03's.
2. Hold those conditions for **30 days**. Daily checks reset interrupted attempts.
3. Open **Indochina: End Japanese Puppet Rule**. Pay **200 money and 750 supplies**.
   Reply after three days: **80% accept, 20% refuse**, with a **90-day** refusal
   interval. Do not open another generic country-peace file while awaiting this
   reply: it invalidates the offer, without refunding committed aid.
4. Acceptance ends U03's Japanese mastery and uses documented
   `leave_alliance when = 1` to leave inherited alliance wars. India stays in its
   own Japanese war. U03 and its surviving forces remain; normal peace restores
   its occupied provinces. No provinces are silently transferred from Japan.
5. When the actual peaceful ownership/control state is verified, choose:
   - **Independent partner:** access, guarantee, +1 TC, -1 dissent.
   - **Indian puppet:** +2 TC, +3 dissent, normal puppet obligations. After two
     years and the required peace, full independence is optional.

Both count as **one live southern regional partner**, not separate Indochina
and Vietnam points. A later sovereign Vietnam can replace that regional slot.
No automatic Laos/Cambodia release; the existing friendly Vietnam petition
remains a separate constitutional option after sovereign recognition.
Losing the required relationship, hubs or peace removes current partner credit.
Rewards and ratification cannot be replayed.

## Progress and irreversible choices

Open **LIBERATOR3 - Campaign Progress Board** at peace or war. Its pages show:

- China: city control, 60-day hold, reply/cooldown and ratification state.
- USSR: strategic hubs, 90-day hold and a separate complete-republic checklist.
- Japan: optional home-island control, 60-day hold and historical completion.
- Indochina: five-province control, 30-day hold and negotiations.
- Southern peace: theatre achievement, Japan-war status and live partner slots.

Only applicable STATUS lines appear. Clicking a status line closes the page and
has no effect. Holds show **30-day bands**, not a fabricated exact countdown.
Small thematic subpages keep the visible lists short. Navigation is immediate:
reading these pages does not require unpausing or spending a game day.
Existing automatic hold-start, interruption and completion events remain the
notifications for major campaign unlocks. Every information page and decision
has an effect-free Cancel, with no return-to-cabinet loop.

The three-city Chinese independence offer now explicitly warns that acceptance
removes the four-city Indian-puppet demand. Puppet ratification's independent
alternative explicitly says it forgoes puppet ratification. The Soviet limited
peace counteroffer states that it creates **no republics**, ends that Soviet war's
deeper campaign, and leaves India's other wars running. The optional Japanese
home-island page distinguishes full armistice from limited peace.

## Developer and verification contract

- Module 43 remains in the existing save's event list; no scenario or save event
  index rewrite is needed.
- New event IDs: **9294000-9294999** for campaign/UI/AI maintenance;
  **9295000-9295999** for country observers. The ordered country registry in
  `tools/data/liberator3_country_ids.txt` is append-only. Never reorder it.
- New leader IDs: **252000-252374**, checked against the full installed leader
  database and the save. A second migration refuses to duplicate them.
- Regenerate using `generate_aubm_liberator.py` and `aubm_command_reserve.py`.
  Both have idempotent `--check` modes. Regenerate the event-art and installer
  manifests after code/data changes. No new artwork is generated by this patch.
- Executable tests cover current/old wars, wrong aggressor, route changes,
  concurrent Soviet war, cancel, stale offers, five-province holds, ownership,
  real peaceful ratification, distinct partner slots, commander size/traits and
  byte-preserving AI edits. The full actual-save migration also proves a lossless
  reverse-edit round trip and preserves all pre-existing Indian country bytes.
- **Not engine-playtested.** Script-level tests do not emulate actual peace,
  puppet/alliance war propagation, AI-fragment merging or event-window layout.
  First manual checks: save loads, reserve leaders appear, progress board opens
  and cancels; later, check the aggression notification and U03's real exit while
  India remains at war with Japan. Keep the untouched original save as fallback.

### Verified local deployment, 7 September 2026

Installed at 16:26:07 UTC into AUBM Terrain Prototype P1. The installer verified
1,902 protected files, backed up all three changed mod files and the original
save/settings, and created the named repaired save. Backup and receipt:
`tmp/liberator3-install-20260907T162607Z/receipt.json`.

Validation: **89 regression tests passed** (76 Liberator, 9 commander/migration,
4 menu-safety); full static audit **0 errors, 0 warnings**; strict art gate passed.
Japan, Southeast Asia, southern settlements (305), bespoke routes (2,388), wartime
(2,571) and diplomatic clarity (435) checks passed. Generated source is current
and repeatable. These are source/data checks, not a substitute for an engine test.
