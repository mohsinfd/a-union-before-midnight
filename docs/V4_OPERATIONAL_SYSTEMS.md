# V4 Operational Systems

## Combat pacing

V4 changes the global combat model, not only India. Air and naval engagements
inflict more organization damage and substantially less strength damage. Fleets
and wings should usually disengage as battered, repairable formations instead
of losing half their material in the first few hours.

Catastrophe remains possible. Naval and air-to-naval critical hits retain a
5-6 percent chance and a 6x strength multiplier. A surprised carrier, an
out-screened battle line, or a wing kept in combat after losing cohesion can
still be destroyed. The new system reduces routine annihilation; it does not
make capital ships or aircraft immortal.

The global auto-retreat threshold rises from 5 to 12 organization. Support
Defence and Reserves use a 0.35 move-time multiplier instead of 0.5, so a
prepared reserve reacts 30 percent sooner.

## Corps and armies

Darkest Hour formations cannot contain subordinate formations or more than one
active leader. A literal hierarchy in which three major-generals report to a
lieutenant-general inside one counter is therefore impossible without changing
the executable.

V4 uses the closest low-micro model the engine supports:

- Twelve starting field corps contain exactly three units each.
- Corps are led by officers accelerated to lieutenant-general in 1933.
- Ceylon, Burma and princely forces remain territorial commands.
- A player may detach any division, assign a major-general and later merge it
  back into its named corps.
- Staff and joint exercises improve officers outside the visible corps counter,
  representing subordinate command experience the engine cannot award directly.
- Command-board rotations in 1940, 1942 and 1944 continue developing officers
  outside the visible corps counter.
- Theatre-command and headquarters modifiers model army-level coordination.

Darkest Hour assigns a new formation name before it can inspect the divisions
that the player later merges into that formation. Automatic composition-aware
labels such as "Armoured Corps" or "Combined Arms Corps" are therefore not
possible. V4 uses neutral numbered Indian Corps names for player-created land
formations. Divisions retain type-specific names, while scripted specialist
formations receive exact armoured, airborne, mountain or expeditionary names.

## Airfield survival

Darkest Hour exposes no command that finds every wing at a captured base and
rebases it to the nearest friendly field. V4 therefore does not claim automatic
evacuation that the engine cannot perform.

Instead, the system combines:

- air and naval scramble missions available from the start;
- an Airfield Security Act that immediately posts named guards to major bases;
- dispersal fields, observers and radar at major hubs;
- higher air organization and morale for timely disengagement;
- four-wing operational groups and a wartime forward-basing protocol.
- rebase orders resolve 35 percent faster, making a timely evacuation practical.

Threatened wings still need a player rebase order. The secured perimeter and
earlier warning are intended to provide the time to issue it.

## National manpower reserve

Darkest Hour's peacetime multiplier yields sovereign India only about 17
natural manpower per year, while the V4 rebase deliberately excludes India
from stock generic mobilization. Event-raised formations could therefore
exhaust the initial pool before India entered a war.

Event 9280840 supplies one trained recruit class per calendar year from 1934
through 1964. The base is 150 manpower, with transparent additive bonuses from
provincial army organization, the 1938 civic-service choice, the 1942 service
law and active war. Year-specific ledger flags make this save-compatible and
prevent any policy branch from disabling later recruitment.

Event 9280841 is a once-per-year wartime safety valve below 100 manpower. Its
three options exchange supplies and dissent for 120, 180 or 250 manpower. The
National Service Debate is state-based, no longer depends on naval logistics
and never requires an existing reserve to select a recruitment law.

Direct event formations enter a named corps at field-ready strength using the
latest researched model; their manpower is deducted explicitly. Production
authorizations reserve manpower for one current-model formation and begin it
with substantial funded progress at normal IC cost. Larger packages use
separate named contracts rather than hidden serial lines. This keeps formation
events meaningful without restoring fixed-cost exploits, concealing manpower
commitments or granting obsolete equipment.

## Historical officer corps

The 1936 officer expansion is guaranteed by calendar rather than by one army
reform flag. It wakes a broad real-world generation drawn from the undivided
Indian armed forces, including P. N. Thapar, J. K. Bhonsle, Mohammad Zaman
Kiani, Iftikhar Khan, Habibullah Khan Khattak, Mohammad Usman, Gurbaksh Singh
Dhillon, Prem Kumar Sahgal, Premindra Singh Bhagat, S. G. Karmarkar and Jal
Cursetji. Existing records now use full names for K. M. Cariappa, K. S.
Thimayya, S. M. Shrinagesh, Ram Dass Katari and Subroto Mukerjee, with ratings
suited to their documented service and plausible accelerated promotion after
1933 independence.

The scenario reaches land-command capacity 80 in 1933, 92 in 1936, 127 in
1939 and 189 in 1942. This is enough to command a great-power army without
turning every junior officer into a skill-five field marshal.

## Upgrade-path usability

Ordinary upgrades to the latest model remain automatic through the production
upgrade slider. Cross-type conversions such as battleship to carrier or
cruiser to light carrier are different: Darkest Hour exposes the target only
through a compiled per-division dialog. The documented event language can
activate models and alter upgrade costs, but it cannot assign a conversion
target to a selected group of existing formations.

Division model files can prescribe one fixed destination, such as a specific
cavalry model always becoming a specific motorized model. That removes the
target picker for every country and every unit using that model; it is not a
runtime "convert all" command and offers no selected-unit scope. Applying it
to stock militia or cavalry would silently rewrite AI modernization across the
world and could turn India's territorial security formations into costly field
infantry without a player choice, so V4.2 does not force those global paths.

The compact save tuple is deliberately not edited by V4. Its fields are not
documented, the old verbose format is explicitly marked unsafe by the engine,
and a guessed batch rewrite could lose attachments, experience or campaign
state. A true select-all conversion control requires an executable/UI change;
V4 keeps the proven conversion paths without claiming unsafe automation.

V4.2 restores manual naval refits from battleship or battlecruiser to carrier,
from heavy or light cruiser to light/escort carrier, and from suitable
transport hulls to light/escort carrier. It also exposes cavalry-to-motorized,
militia-to-infantry and garrison-to-infantry conversions. These are ordinary
upgrade jobs: they retain the engine's per-division target picker and consume
upgrade IC and time. Conversion time and cost are lower than a new formation,
but reinforcement and passive in-supply progress are disabled. A zero upgrade
slider now correctly halts both model upgrades and cross-type refits.
An eligible source formation must first be fully reinforced; after that, its
conversion progresses from the normal Upgrades allocation.

Only eligible source classes display a conversion. Destroyers, submarines and
ships that are already carriers have no invented carrier conversion route.
Darkest Hour provides no event or interface command for applying one conversion
choice to every selected unit, so each cross-type refit remains a deliberate
per-formation order.

## Naval hull progress

Named fleet programmes may inherit current-model hulls already under
construction. Positive `where` values represent remaining days while IC cost
remains governed by the engine. Validation permits this only for single naval
hulls in events 9271104, 9271105, 9271106, 9271109 and 9274009, capped at 730
days; fixed event costs remain forbidden.
