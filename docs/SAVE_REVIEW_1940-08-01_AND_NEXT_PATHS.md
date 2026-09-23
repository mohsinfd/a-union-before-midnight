# Latest-save review and next campaign choices

Reviewed 7 September 2026. This is advice and a read-only audit, not a gameplay patch.

## Which save and installation?

The newest save is `autosave.eug`, **1 August 1940**, written 7 September 2026 at
01:44 IST, in **AUBM Terrain Prototype P1**. The other installation's autosaves are
older. The active installation still has Alpha 27 / HYBRID-WORLD1 plus MENU-SAFETY1;
all four menu-hotfix file hashes match the installation receipt. Every event file
referenced by the latest save exists. No Indian event is currently queued.

The latest start-up log's province validation reports no errors. This is not proof
that all event branches are correct: the progression problems below are real.
No game was launched or advanced, and no save or installed event file was edited.

## What has changed in your campaign

- India is at peace, outside every formal alliance, with **sovereign** alignment.
  The Japanese compact has ended: commitment, partnership and senior/full-sphere
  flags are absent, the rupture flag is present, and the realignment cooldown has
  finished. The save cannot establish why you chose withdrawal.
- You retain 14 historical Tokyo influence, but that does not itself constitute a
  compact or alliance. No wartime charter has been selected.
- Nationalist and Communist China no longer exist. Japan's puppet U87 holds 102
  provinces and is in Japan's alliance. It currently has no deployed divisions of
  its own; Japanese troops remain the meaningful opponent there.
- Japan is also at peace. Joining it now does **not** start a Chinese or Allied war.
- Germany and its partners are fighting the British-led coalition, but Germany and
  the USSR are **not** at war. France still controls its capital. Helping Germany
  in the Caucasus is therefore a later conditional objective, not a task already
  available on the present map.
- The Netherlands has disappeared, but the separate **East Indies authority U05**
  still owns the islands. It is currently outside the listed alliances and wars.

### Military and economic assessment

Counts below are deployed formations, not equal-strength comparisons. Naval totals
include transports, submarines and flotillas. The latest save uses compressed unit
statistics; these counts come from land/naval/air group membership, not guessed
unit-type decoding.

| Country | Land divisions | Naval units | Air wings |
| --- | ---: | ---: | ---: |
| India | 146 | 131 | 58 |
| Japan | 126 | 123 | 25 |
| Britain | 98 | 188 | 28 |
| France | 103 | 82 | 4 |
| Australia | 19 | 13 | 4 |
| East Indies | 12 | 13 | 1 |
| United States | 33 | 139 | 20 |
| Soviet Union | 289 | 24 | 50 |

India has **0 dissent, 83.5 manpower, 3,896.6 supplies, 49,958.4 oil and 4,105.8
money**. Supplies rose from 2,818.2 in July; manpower fell from 145.3. Six infantry
serials still have ten divisions remaining between them. This does not mean their
entire manpower cost remains unpaid, but further serial starts compete with the
replacement pool. Reinforcement spending is currently zero, consistent with peace;
it must be revisited when casualties begin.

Your deliberate staging stacks and transport conversions are not treated as
mistakes. Before war, complete the reorganisation you intended: combat fleets under
appropriate leaders, transport groups separate from main engagements, and a reserve
for the Himalayan border. Nepal is presently in Britain's alliance.

My preparation target, not an event requirement: build roughly **8,000–10,000
supplies**, retain replacement manpower and avoid opening the American and Soviet
wars together. The present force is already large enough for a focused southern
campaign. The early East Indies/Australian land campaigns will probably be easier
with Japan freed from China; naval coverage, supply and wider war remain meaningful
constraints. Unit totals alone do not establish fleet superiority.

## My recommendation and the saves to use

**For a fresher challenge, use the August 1940 autosave and fight Japan through an
Allied Eastern Ocean Command route.** China's defeat gives that campaign a useful
adversary rather than removing an objective. A sovereign anti-Japanese war is the
harder, more independent alternative.

**For your original conquest itinerary, the same August save can still join Japan.**
Treat it as a southern/ocean/Caucasus campaign, not a completable China grand-finale
run under the current rules.

| Save | What it offers |
| --- | --- |
| `autosave.eug` — 1 August 1940 | Best branch for alternate alignment; current forces and no active commitment/cooldown. Also usable for Japan, with the caveats below. |
| `oldautosave.eug` — 1 July 1940 | China is already gone and India is already sovereign. Going back one month does not restore the China campaign. |
| `AUBM_1939-01-01_safe_cabinet.eug` — 1 January 1939 | Nationalist China still exists and fights Japan. India retains the senior/full-sphere compact. Use this only if replaying the Chinese-war period matters enough to repeat nineteen months. |

The January save is **not** a guaranteed fix for the four-theatre achievement:
Japan already controls Nanjing, the fixed Indian Nationalist-China victory target.
The achievement requires Indian credit, not merely Japan winning. Choose the
January save for the actual Chinese war and original treaty position, not a promise
that all scripted completion conditions will work.

Before choosing a branch, manually save the August position under a permanent name
such as `India_1940-08-01_before_alignment`. This is a suggested name; I have not
created that save. Routine autosaving will otherwise replace this branching point.

## Japan: exact next choices from the August save

Timing below describes scripted delays and condition checks. It is not a fixed
historical timetable. Cabinet navigation generally schedules the next page one
game day later. Automatic events can appear in a different order.

### 1. Enter the alliance, if you accept the current re-entry penalty

Open **Convene the National War Cabinet** and select:

1. **Coalition membership and peaceful withdrawal**.
2. **Strategic compacts and sovereign command**.
3. **Tokyo, autonomous socialism or sovereign command**.
4. **Join Japan: +4 dissent; trade reversal +3, costs 300**.

This final choice is event 9281914. In this save the trade-only flag is absent and
the early bilateral policy is present, so the scripted cost is **+4 dissent**, not
the extra trade reversal charge. It creates a formal shared-war alliance. Since
Japan is currently at peace, entry itself starts no war.

**Important existing re-entry problem:** the same action unconditionally resets
Tokyo influence **14 → 1** and enters at **peer/core**, because the old senior/full
sphere flags were cleared on withdrawal. The already-paid resource guarantee and
equal-carrier-command flags remain used, so do not expect those decisions to restore
the lost score again. This is worth correcting before a Japan playthrough focused
on diplomatic progression. It was not changed during this review.

The compact alternative is **Negotiate a separate Tokyo compact** → **Send proposal:
-350 money, -600 supplies**. However, this recalculates opening influence at **6**
from the current historical flags, rather than preserving 14. It does not guarantee
a senior offer. Consequently neither button should be presented as a lossless
restoration of the old treaty.

### 2. Prepare, then open the British war deliberately

Do not wait for an assumed December 1941 event. Once your formations and reserves
are ready, return to the Cabinet and select:

1. **Great-power, regional and active campaign dockets**.
2. **Open great-power or regional campaign dockets**.
3. **Prepare war against the British-led coalition**.
4. **Declare war on Britain: +4 dissent** in **Confirm War Against Britain** (9281920).
5. A day later, acknowledge **The Declaration Reaches the Foreign Ministry** (9281925).

This is a real declaration, not just an operations plan. A formal Japanese alliance
shares wars; Britain normally brings its coalition, including Australia and Nepal.
Check the resulting diplomacy screen rather than paying for redundant declarations.

### 3. The first days of actual Indian war

| Event | Recommended exact choice | Scripted timing / consequence |
| --- | --- | --- |
| The Delhi-Tokyo Wartime Charter (9283213) | **Indian Southern Sphere** | Checks every 3 days once India is at war on the Japanese route. This chooses the primary arc; it does not declare war. |
| The Indian War Finance Act (9282080) | **Ordinary revenue: no cash, -1 dissent** | Checks every 3 days. You already have over 4,100 money; money is not your present bottleneck. Avoid unnecessary debt. |
| Mobilisation of the Indian Union (9282086) | **Limited service: +260 MP, -800 supplies, +2 dissent** | Checks every 4 days. Appropriate for the initial southern war. National service is the larger +450 MP/-1,200 supplies/+5 dissent option if you insist on several major fronts. |
| The Indian Southern Sphere Activates (9289625) | **Activate Indian Southern Sphere** | Checks every 2 days after the charter and a relevant southern war. |
| Decision: Open the India-Led Southern Theatre (9281140) | **Activate India's southern command ledger** | Use when visible; requires a qualifying southern war. Formal alliance avoids its separate-command +2 dissent charge. It can also add missing matching wars against Japan's southern enemies. |
| Southern Theatre Directive No. 1 (9281141) | **Issue the objective ledger** | Scheduled 2 days after activating the southern command decision. |

Charter selection and opening the operational ledger are separate actions. If the
southern theatre is already active, do not wait for its decision to return.

### 4. Take these objectives under Indian control

The existing Burma positions should give **The Burma-Andaman Approach Is Secure**:
hold Rangoon, Imphal and Port Blair; choose **Record one theatre point** (+300 supplies).

Then capture **Singapore and Kuala Lumpur**. In **India Controls Singapore and
Malaya**, choose **Record two theatre points**. The authored **Malaya Enters the
Indian Sphere** event adds **Record the intermediate objective** (+400 supplies).
The former checks every 5 days; the authored intermediate checks every 3 days.

After the intermediate, **The East Indies or Australia?** (9289633) checks every
2 days. Choose **Concentrate on the East Indies resource arc**: -600 supplies,
+300 oil. This selects the emphasis; it neither forbids a later Australian invasion
nor itself declares the East Indies war.

The islands still belong to **U05**, not the vanished Netherlands. If U05 remains
outside your wars, use Cabinet → **Great-power, regional and active campaign dockets**
→ **Open regional campaign dockets** → **Europe, the oceans and Africa** →
**Colonial and ocean powers** → **Declare war on the East Indies: +3 dissent**.

For the Japanese resource-arc objective you need **Palembang, Batavia and Soerabaja**,
not Batavia alone. Choose **Record three theatre points** in **The East Indies
Resource Arc Is Indian** (+500 oil/+200 rares; checks every 5 days).

Burma 1 + Malaya 2 + East Indies 3 = **six points**. While you still hold the required
Malayan and East Indies cities, **India Has Won the Southern Command** checks every
5 days. Choose **Open the Indian Ocean and Himalayan settlements**. This records
victory; it is not the same as accepting a separate peace.

For Australia, take **Darwin, Canberra and Sydney** and choose **Record three theatre
points** in **Australia Accepts the Reality of Indian Command**. Australian landings
are the next extension once the Malayan/East Indies sea lane is secure.

### 5. Do not accidentally end the alliance through a peace decision

You may see **Convene the Indian Ocean Settlement** (9281160) after southern victory.
**Do not select any of its settlement choices yet if your plan remains Australia,
Suez and Africa in the same formal-alliance war.** Its actions immediately leave the
formal Japanese alliance and issue separate-peace commands; the relationship then
continues as a compact. This happens when selecting the terms, not only after a
foreign acceptance. It is much more consequential than reviewing a ledger.

### 6. Optional later operations

- **Philippines:** capture Manila and Davao against their legal owner, then choose
  **Record the Philippine operation** in **The Manila-Davao Maritime Victory**.
  Do not assume a Japanese occupation gives India this credit. A Philippine/US war
  is separate from the British war and may substantially expand your opposition.
- **Suez/Africa:** open Cabinet → **Authored route campaigns and partner crises** →
  the Delhi-Tokyo board → **Open the multi-theatre Delhi-Tokyo grand-campaign ledger**
  → **Review the staged Aden-Suez-East Africa chapter**. Record Aden, then Suez.
  The current third-stage rule can award Africa from an overly broad western-victory
  flag; do not mistake this for proof you actually completed an African campaign.
- **Caucasus:** wait for a real German–Soviet war. The relief ledger requires India
  at war with the USSR, Indian control of **Baku plus Tbilisi or Astrakhan**, and
  German control of Berlin. Choose **Convene the Delhi-Tokyo-Berlin relief decision**,
  then **Dispatch one relief convoy: -1200 supplies/-500 oil**. No passive aid is
  credited just for being Japan's ally. The separate **Open an Independent Northern
  War against the Soviet Union** decision is for a compact, not a formal alliance;
  a formal ally uses the normal Soviet war docket and shares that war.

## Alternate routes from the latest save

### Recommended: Allied Eastern Ocean Command

No rollback or new game is necessary. Cabinet → **Coalition membership and peaceful
withdrawal** → **Choose London or Washington** → **Join Britain's coalition:
+3 dissent**. Acknowledge **India Enters the Allied War System** → **Record the Allied
alliance**. You inherit the existing war against Germany and its partners immediately.

In **The Delhi Allied War Charter**, choose **Eastern Ocean Command** (checks every
3 days after route recognition while at war). This **does not** declare war on Japan.
When ready, use the great-power docket → **Japan, the United States and return** →
**Prepare war against Japan** → **Repudiate Tokyo and declare war: +6 dissent**.
The declaration is processed the following day.

**Eastern Ocean Command Activates** begins once the relevant eastern war exists
(2-day checks). Later, in **Who Commands the Eastern Advance?**, I favour **Publish
an Asian liberation mandate** (-200 money/-2 belligerence) for the character of this
campaign. Defeat Japanese power in China and the western Pacific instead of joining
it. These are different goals from conquering friendly Australia or British Suez.

### Sovereign anti-Japanese war

Stay unaligned and use the same Japanese declaration docket when prepared. Choose
**Act as the World Balancer** in **The Sovereign Indian War Charter** for a great-power
balancing campaign. You keep choice over wars but lack guaranteed coalition cover.
This is my harder alternative, not a low-risk opening.

### Germany or the Soviet Union

Formal German entry is available through **Join Germany: merge wars, +4 dissent**;
it immediately brings the current Allied war. **Win the southern resource race** fits your
southern expansion, but joining Germany does not itself make you Japan's ally.
The separate Delhi-Berlin conference remains gated until Germany or India is at war
with the USSR; do not wait for that button just because the calendar reads 1940.

Formal Soviet entry is available through **Join the Soviet coalition: merge wars,
+4 dissent**. Moscow currently has no active war in this save, so no immediate war
charter should be expected merely from entry. A later anti-Japanese **A Republican
Asian Order** campaign offers a different ideological story, but not your original
anti-British/Japanese-allied itinerary.

## Confirmed limits and evidence

- **Four-theatre Japan completion is blocked in this August save.** Event 9289646
  requires simultaneous Indian/Japanese war with CHI or CHC to publish China-command
  boundaries. Event 9289652 additionally requires an Indian CHI/CHC victory. Both
  countries are gone; U87 is not accepted as a replacement. This is a missing
  post-China-victory branch, not a player error. Even the January save has a further
  practical obstacle: Japan already controls the fixed Nationalist victory target.
- **Re-entry loses influence.** 9281914 resets the number to 1. The separate
  conference 9281100 recalculates it to 6 for this save. Previously used political
  investments remain spent. Do not promise an immediate seniority review.
- **Peace changes alliance status.** 9281160 leaves the formal alliance as soon as
  a settlement option is selected. Read it as a strategic exit, not a reward claim.
- **African progress is too loosely defined.** 9289647 stage III accepts the general
  western-victory flag as an alternative to Ethiopian/South African victory.

Sources: the actual installed event files 32, 35, 41, 44, 46, 48, 50 and 51; the
three inspected save files; the MENU-SAFETY1 installation receipt; and the game's
installed event-command documentation for flag assignment and delayed events.
The latest save SHA-256 is
`df31a149f6ee23fd1136d10b2e2ff12abafe05c239da383f35a35f54cf0817c3`.
Detailed extracted evidence is in `tmp/save-review-2026-09-07`.
