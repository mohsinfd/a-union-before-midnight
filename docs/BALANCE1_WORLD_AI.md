# BALANCE1 world AI: bounded fresh-campaign changes

The transform is `tools/aubm_balance1_world_ai.py`. Its input/output is a full
dictionary of installed-relative paths and text; input is not mutated. Preserve
original bytes with Latin-1 transport. The new text is ASCII. It does not launch
the game, install anything, alter a save, or touch difficulty/combat statistics.

## Changes

- Finland keeps its homeland defensive AI throughout a Soviet war. Losing 2%
  of national provinces no longer switches it into its less defensive AI.
- An AI German/Italian alliance fighting Britain can recruit one Africa reserve
  corps after July 1940, after Germany holds Paris, and only while Italy controls
  Tripoli, Benghazi or Tobruk. Fallback ports are mutually exclusive. Cost: 30
  manpower, 6,000 supplies, 1,500 oil and 300 money. Two formations: 1938 light
  armour and 1939 motorised infantry, without attached free brigades. This is an
  explicit paid reserve reinforcement, not a transfer of pre-existing divisions.
- German Continuation War support requires June 1941 or later, an AI Finland
  allied to Germany, both fighting the USSR, and Finnish control of Petsamo or
  Helsinki. One two-division 1939 mountain reserve corps costs 30 manpower, 5,000
  supplies and 250 money. Never triggered by the Finnish Winter War alone.
- Both corps packages are permanently latched after deployment. No replacement
  corps appears if destroyed; no package when the ally or port is absent.
- Remove Finland from the Barbarossa overseas-expedition prohibition. This alone
  does not compel Germany to lend formations, hence the bounded support above.
- Germany gives Oslo, Bergen, Trondheim and Narvik explicit garrison priority.
  Values are merged into existing lists in each German garrison-bearing AI
  switch. The end-of-Norway-invasion switch also installs them.
- Italy gives its remaining Libyan and Balkan ports priority. Homeland defence
  retains overseas beach defence, raises overseas weighting from 0.1 to 0.5 and
  adds a 40-point reserve-behind-front priority. It still prioritises Italy.
- British attack settings no longer use maximum recklessness 3; speculative
  minimum odds below 1.0 become 1.0, and base attack odds below 1.2 become 1.2.
  Invasion selection gives greater weight to troops at and near a target. It
  does not prohibit historical landings or guarantee a minimum landing force.
- Soviet garrison priorities include Baku, Astrakhan, Tashkent and Dushanbe;
  Japanese priorities cover mainland Southeast Asian hubs and Batavia; British
  priorities include Suez, Baghdad, Rangoon and Singapore. Existing strategic
  priorities are retained, not replaced. These are priorities for existing
  forces, not free armies or hard division allocations.
- SOV, JAP, ENG, USA, GER, ITA and AST switch to a narrow human-front reaction
  while actually fighting human India: human-border garrison priority 150,
  reactive front distribution, reinforcement-request panic threshold 2.0.
  Real war/peace/alliance state determines activation, not Indian route flags.
  Peace/alliance/AI-India removes the reaction. Existing country AI-switch actions
  reapply the reaction conditionally, so historical switches do not erase it.

## Why 19 hidden events does not mean 19 new menu decisions

Fourteen are seven war-entry/exit pairs with local-state latches; they do not
fire repeatedly in unchanged state. Five are alternative-port versions of two
one-time paid German packages. The player gets no new decision-menu entries.
There are no monthly AI polling events and no recurring troop rewards.

## Verification and limits

Nine independent script-contract tests cover absent India, AI/human control,
peace, war, alliance, repeated activation, unavailable ports/resources, the
Winter War exclusion, unique paid packages, merged priorities, switch hooks,
collision rejection and idempotence. An installed-baseline dry run over 931
event/AI files produced 101 changed paths; all modified files parse, every AI
command target resolves, and a repeat transform changes zero files.

These are static checks, not a native campaign playtest. AI allocation and
shipping are heuristic. Two paid reserve divisions cannot guarantee Libya or
Finland survives; garrison priority cannot guarantee a defended Norwegian port
when Germany lacks deployable troops. A USSR already losing a major war may
still be vulnerable to a well-timed Indian invasion. This patch does not buff
the USSR/Germany economy or decide their war by scripted victory.

Local engine references: `Modding documentation/AI Files Modifiers.txt`, sections
garrison/front/invasion; `Modding documentation/event commands.txt`, AI checks,
control checks, country stockpile triggers, add_corps, add_division and resource
pool commands. No claim of historical troop transfer fidelity is made for the
paid reserve abstraction.
