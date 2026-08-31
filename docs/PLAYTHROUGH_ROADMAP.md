# Playthrough Roadmap

This is the running backlog from the serious campaign playthrough. Items here
record player-facing problems and questions; inclusion does not assume that a
specific balance change is already correct.

## Resolved In The 1942 Review Build

### Resource-gated decision visibility

- **Observed:** Darkest Hour hides individual event actions whose resource
  triggers are not met. Decisions can therefore become selectable while their
  strongest or most strategically important choices are invisible. In 1935,
  `The Himalayan Settlement` displayed only three choices because the combined
  Nepal-and-Bhutan settlement required 400 money and 650 supplies. Similar
  uncertainty is now blocking the player from confidently resolving naval and
  steel decisions: with less than roughly 1,000 money, there is no way to know
  whether selecting a visible option permanently sacrifices a hidden route.
- **Resolution:** The build now calculates the maximum money, supplies and
  manpower required by every action and inserts that full-option gate into the
  parent decision. The rule is applied automatically during every deployment,
  so a future event edit cannot silently reintroduce the problem. The
  Himalayan Settlement also retains a clearly priced fourth option to approach
  both kingdoms. If the player initially approaches only Nepal or only Bhutan,
  a separate save-compatible completion decision remains available for the
  unresolved kingdom instead of the first choice closing the entire policy.
- **Acceptance criterion:** At any treasury level, the player can tell all
  permanent routes a decision offers before committing to one. No hidden
  action can be lost unknowingly by selecting an apparently complete decision.
- **Status:** Resolved and build-enforced across 42 decisions; the Himalayan
  one-country lockout is also resolved for new campaigns and existing saves.

### 1933 inherited technology baseline

- **Observed:** The June 1937 save confirms that India is still using two of
  seven research slots on the 1874 Turret Battleship and the 1920 Carrier
  Integration doctrine. Other active projects are appropriately dated from
  1930 to 1937. The gap is therefore concentrated in inherited prerequisites,
  especially naval construction and carrier aviation, rather than being a
  general shortage of capable research teams.
- **Resolution:** The 1933 setup now inherits the Raj's mature destroyer,
  cruiser, capital-ship, submarine, multirole, naval-bomber, seaplane, carrier
  aviation and foundational naval-doctrine branches. Modern hulls and wartime
  doctrine still require research. A one-time archive event grants the same
  curated baseline to saves created before this correction.
- **Acceptance criterion:** India begins with the mature nineteenth-century
  and Great War foundations plausibly inherited from the Raj, while modern
  capital ships, carrier operations, aircraft and doctrines still require
  sustained national investment.
- **Status:** Resolved for new games and existing saves.

### Peacetime finance and development debt

- **Observed:** India has negative 445.8 money on 1 June 1937, despite cheat
  support during the campaign. Resolved custom event actions have removed at
  least 12,885 money since 1933. However, the treasury improved by 254.6 during
  May 1937, roughly 8.2 money per day, while all seven research slots were
  active. The structural problem is therefore repeated large programme costs,
  not a permanently negative daily economy.
- **Resolution:** An annual Union Budget begins in 1934 and offers taxation,
  domestic bonds, foreign credit or austerity. Borrowing creates persistent
  annual service costs and can be retired through a separate treasury decision.
  A one-time full-stretch review also converts part of an overgrown industrial
  modifier into money, revenue or social stability instead of adding free cash.
- **Acceptance criterion:** A solvent player can fund several strategic
  programmes each budget cycle but cannot purchase every premium programme.
  Temporary debt is playable and visible; prolonged overextension compounds
  into real future costs rather than silently forcing a negative treasury.
- **Status:** Resolved as a recurring choice rather than a free-money pulse.

### Andaman and Lakshadweep blue-water bases

- **Observed:** Port Blair (1421) and Kavaratti (1612) are strategically ideal
  forward bases but begin at infrastructure 10 without naval or air bases.
  The current campaign has manually queued six naval and five air-base levels
  at Port Blair and five of each at Kavaratti. Existing content can fortify
  Port Blair, and Indian AI recognizes it as a naval base; Kavaratti has no
  corresponding development chain and is absent from the AI base lists.
- **Resolution:** Two staged investment decisions now develop Port Blair and
  Kavaratti as complementary forward stations with capped construction and
  full resource gates. Kavaratti is included in every Indian strategic-path AI
  naval, air and admiral-base list.
- **Acceptance criterion:** Both islands become useful blue-water nodes after
  deliberate investment without replacing Bombay, Karachi or the east-coast
  dockyards as principal home bases.
- **Status:** Resolved for player and AI.

### Slept-event log noise

- **Observed:** The 1933-37 campaign is stable and the validator reports no
  province errors, but `savedebug.txt` repeatedly attempts to execute slept
  stock election events 9000100, 9000113 and 9000150, producing roughly 75
  messages per event. This is not the source of a crash, but it obscures useful
  diagnostics and indicates that stock callers remain active.
- **Resolution:** The May 1938 campaign proved the earlier workaround was still
  noisy: 1,466 repeated slept-event messages were present. Alpha 12 removes
  India from the shared generic-election TAG lists and no longer sleeps those
  shared event IDs. Existing saves may retain their serialized log noise, but
  it remains non-fatal; new campaigns use the corrected isolation.
- **Acceptance criterion:** A hands-off 1933-37 run has no repeating slept
  election-event messages and no duplicated government changes.
- **Status:** Corrected for new campaigns in Alpha 12; current-save noise is
  harmless and intentionally left untouched.

## Remaining Campaign Questions

### Wartime balance after joining a coalition

- **Observed:** The April 1942 save remained peaceful and non-aligned while
  Japan and Siam continued their war in China. Consequently, the old content
  produced almost no Indian reaction after 1939.
- **Change:** Condition-driven China, Burma, Southeast Asia, European-war and
  Japanese-southern-strategy events now continue through 1943. An annual
  Strategic Council lets a peaceful India reconsider Allied, Soviet, Axis,
  Japanese, Asian-coalition or non-aligned strategy instead of being trapped
  by an early orientation flag.
- **Test question:** Once India enters a coalition, verify that the theatre
  pressure is demanding without creating unavoidable wars or duplicate entries.

### Late-game force scale

- **Observed:** In April 1942 India had 211 base IC, a 1.48 national IC
  modifier, 114 land divisions, 56 air divisions and 39 ships, with several
  capital ships still building. The strongest imbalance came from cumulative
  modifiers and free or heavily discounted formations rather than base IC.
- **Change:** The full-stretch review removes 10-15 points of the cumulative
  total-IC modifier. The 1941 destroyer/submarine plans are smaller, and the
  1942 naval events now improve doctrine, readiness and escorts instead of
  gifting carriers after the player has already built them.
- **Test question:** Measure effective IC and total forces in 1940 and 1942 on
  a no-cheat campaign before making a second reduction.
