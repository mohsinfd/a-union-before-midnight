# Alpha 23 Route Campaign Matrix

This document is the player-facing and maintainer-facing map of Alpha 23's
authored wartime routes. It is grounded in
`tools/generate_aubm_bespoke_route_arcs.py`, its generated
`mod/db/events/aubm_v4/51_bespoke_route_arcs.txt`, and the route charter and
peace-congress lifecycle in `mod/db/events/aubm_v4/48_route_wartime_consequences.txt`.

> Verification boundary: this is a static review of the implemented event
> conditions and effects. It does **not** claim that Alpha 23 has completed a
> runtime playtest, balance soak, campaign launch test, or full-route playthrough.
> Difficulty labels below are design estimates, not measured results.

## How the authored route system works

- Event `9289499`, **Authored Strategic Campaigns**, is the route-aware
  dispatcher beneath the National War Cabinet. It opens the current route
  board, an available compact-partner crisis, or the shared campaign ledger. It
  does not declare war.
- Each route has one status board, one compact-partner crisis, one zero-reward
  secondary-theatre ledger and one partner-collapse event.
- Each route offers four primary charters. A charter has four authored stages:
  activation, intermediate milestone, three-way strategic dilemma and
  culmination.
- Normal activation requires 1937 or later, the Alpha 23 route contract, the
  current route, the selected charter and a relevant Indian war. Migration
  catch-up may acknowledge a culmination that was already earned in an older
  save.
- A dilemma choice can alter resources, dissent, relations, military modifiers
  or political flags. It does not itself transfer territory or replace the
  country-specific settlement systems.
- Culmination records the selected focus, grants the route's Congress
  entitlement and closes the one-primary-focus lifecycle. Unrelated victories
  remain secondary: they do not complete, block or relabel the selected focus
  and cannot open the peace Congress by themselves.
- After a dilemma, an eligible partner may recognize the doctrine, counter with
  narrower consultation or refuse support. The generated AI chances are
  55/30/15. Refusal does not invalidate the Indian focus.

### Event map

| Route | Charter selection | Status / crisis / secondary / collapse | Focus stages |
| --- | --- | --- | --- |
| Allied | `9283210` | `9289500` / `9289501` / `9289503` / `9289504` | `9289505-9289520` |
| German | `9283211` | `9289540` / `9289541` / `9289543` / `9289544` | `9289545-9289560` |
| Soviet | `9283212` | `9289580` / `9289581` / `9289583` / `9289584` | `9289585-9289600` |
| Japanese | `9283213` | `9289620` / `9289621` / `9289623` / `9289624` | `9289625-9289640`; grand ledger `9289645-9289652` |
| Sovereign | `9283214` | `9289660` / `9289661` / `9289663` / `9289664` | `9289665-9289680` |

## War inheritance and expected difficulty

The important distinction is legal command, not flavor text. A formal Darkest
Hour alliance shares wars through the engine. A separate-command compact does
not. The compact crisis appears only when the partner has entered one of the
listed major wars and India is still outside it.

The four major-power compact crises offer the same legal postures:

1. Seek formal entry through the alignment review; completing formal accession
   means inheriting all of that alliance's live wars.
2. Retain separate command and open the legal campaign docket for the named
   enemy set.
3. Spend 600 supplies and 150 money on limited support while remaining outside
   the war.
4. Remain outside and review peaceful withdrawal or realignment.

The sovereign Delhi-system crisis is different because India has no binding
major-power compact to withdraw from. It offers an independent Indian response
plan, a legal pairwise campaign docket, material support while staying out, or
armed neutrality with continued Delhi Pact talks.

| Route | Separate-command crisis watches | Formal-alliance consequence | Expected planning burden |
| --- | --- | --- | --- |
| Allied | Britain or the United States fighting Germany or Japan while India remains outside. | Alliance with Britain or the United States shares that coalition's live wars. There is no fictional opt-out after accession. | **Moderate.** Strong partners and several achievable Asian or European objectives, but formal entry can create simultaneous German and Japanese wars. |
| German | Germany fighting Britain, the Soviet Union or the United States while India remains outside. | Formal Axis entry with Germany shares Berlin's live wars. | **High.** The principal authored fronts are long-range: Persia-Caucasus, Suez-Africa or Southeast Asia. Germany's survival cannot be assumed. |
| Soviet | The Soviet Union fighting Germany, Japan or Britain while India remains outside. | Formal Comintern entry shares Moscow's live wars. | **Moderate-high.** The route supports both continental and maritime strategies, but formal entry can merge very different European and Asian wars. |
| Japanese | Japan fighting Britain, the United States or the Soviet Union while India remains outside. | Formal alliance with Japan shares every live Japanese war, including China when that war already exists. | **High**, and **very high** for the optional four-theatre grand campaign. The compact preserves selective entry; the full grand-campaign completion eventually requires formal-alliance China command boundaries. |
| Sovereign | A Delhi-system partner fighting Japan or the Soviet Union while India remains outside. | There is no default major-power alliance to inherit wars from. India opens pairwise campaigns deliberately unless it later realigns. | **High.** India owns the logistics, declarations and settlement leverage without a major-power safety net. |

## Allied route

**Play identity:** win recognition inside or beside the Allied system without
letting Indian formations and political aims disappear into generic coalition
service.

| Charter and stage events | Play identity and activation | Intermediate milestone | Three-way dilemma | Culmination criteria and political meaning |
| --- | --- | --- | --- | --- |
| **Eastern Ocean Command**<br>`9289505 / 9509 / 9513 / 9517` | Fight Japan, Malaya (`U05`), the Netherlands or Australia. Build an Indian-led Asian theatre; Allied victories elsewhere do not substitute for Indian command. | **The Burma-Andaman Hinge Holds:** either the Bay of Bengal sea lane is current, or India controls both Rangoon (`1415`) and Port Blair (`1421`). | **Who Commands the Eastern Advance?**<br>1. Joint board, Indian field command: +300 supplies, +1 dissent.<br>2. Asian liberation mandate: -200 money, -2 belligerence.<br>3. Reserve eastern settlements to Delhi: -150 money, +2 dissent, sovereign credit. | Complete the Southeast Asia theatre, an Indian Southern Command victory, or a major Japanese victory stage. Delhi is recognized as the Allied Eastern Command; legal country settlements remain separate. |
| **Continental Expeditionary Command**<br>`9289506 / 9510 / 9514 / 9518` | Fight Germany, Italy or Turkey. Suez, the Gulf and Mediterranean are staging systems for an Indian-command European result. | **The Expedition Reaches the Western Arc:** a live Western Command, or an Italian or Turkish regional victory. | **The Continental Command Debate**<br>1. Reinforce the main European front: -500 supplies, -1 dissent.<br>2. Make the Mediterranean India's responsibility: -250 money, +1 TC.<br>3. Sovereign Indian mandate: +2 dissent, sovereign credit. | A limited or major German result, or the European-capital victory flag. India earns a direct European settlement voice. |
| **Anti-Colonial Liberation Mandate**<br>`9289507 / 9511 / 9515 / 9519` | Fight Japan, Germany, Italy or the Netherlands in a war capable of restoring an Asian or African government. | **A Liberated Government Returns:** a current Malayan, East Indies, Indochinese or Philippine liberation, or an Ethiopian or South African regional victory. | **The Liberation Clause**<br>1. Immediate sovereignty: -300 money, -3 belligerence.<br>2. Published transition timetable: -150 money, -1 dissent.<br>3. Temporary Indian protection: -500 supplies, +2 dissent. | Requires both a Southeast Asian or Southern Command victory **and** a Western Command, Persian, Ethiopian or South African result. Coalition war becomes an Indian decolonization claim without bypassing local settlements. |
| **Sovereign Free Command**<br>`9289508 / 9512 / 9516 / 9520` | Any Indian war. Cooperate with the Allies without accepting a named coalition theatre. | **An Independent Indian Theatre Is Established:** any live Southern, Western or Northern Command. | **Equality without Integrated Command**<br>1. Consultation for replacement stocks: +500 supplies, +1 dissent.<br>2. Parallel belligerency: -150 money, -1 dissent.<br>3. Separate Indian peace authority: +2 dissent, sovereign credit. | A decisive great-power result, or victories in any two of Southern, Western and Northern Commands. The Allies must credit an independent Indian war system. |

### Allied partner war and collapse

- The compact crisis names Germany or Japan. Formal accession instead shares
  the Allied war system.
- Partner-collapse event `9289504` watches the selected British partner losing
  London (`29`) or the selected American partner losing province `1809`.
- The four responses are: fund relief (-1200 supplies, -250 money, +1 dissent);
  assume independent eastern command (+500 supplies, +2 dissent); demand
  colonial guarantees (-300 money, -2 belligerence); or prepare disengagement
  (+1 dissent and return to alignment review).

## German route

**Play identity:** use Berlin as a continental partner while making the
Caucasus, British imperial system, southern resource arc or a parallel Indian
war produce an Indian settlement claim.

| Charter and stage events | Play identity and activation | Intermediate milestone | Three-way dilemma | Culmination criteria and political meaning |
| --- | --- | --- | --- | --- |
| **The Eurasian Link against Moscow**<br>`9289545 / 9549 / 9553 / 9557` | Fight the Soviet Union through Persia, Afghanistan, Xinjiang or another lawful corridor. A declaration alone is insufficient. | **Indian Command Reaches the Caucasus Gate:** a live Northern Command, Indian control of Baku (`713`) or Indian control of Tashkent (`1103`). | **The Caucasus or Central Asia?**<br>1. Baku and Caucasus: -600 supplies, +1 land mountain attack.<br>2. Central Asia: -500 supplies, +1 land desert movement.<br>3. Sovereign mobile front: -200 money, -1 dissent, sovereign credit. | A Northern Command victory or a limited/major Soviet campaign result. Berlin must credit the southern front as an independent Indian contribution. |
| **Dismantle Britain's Imperial System**<br>`9289546 / 9550 / 9554 / 9558` | Fight Britain through the Gulf, Suez and East Africa. One captured port is a raid, not a completed system. | **The Western Ocean Corridor Opens:** a live Western Command or limited British result. | **How Will the Imperial System Break?**<br>1. Suez hinge: -650 supplies, +1 TC.<br>2. East African coast: -250 money, -350 supplies.<br>3. Sovereign successor governments: -3 belligerence, -1 dissent. | Requires a Western Command victory plus a limited or major British result. Delhi, not Berlin, owns the Indian Ocean claim. |
| **Win the Southern Resource Race**<br>`9289547 / 9551 / 9555 / 9559` | Fight Britain, Malaya, the Netherlands or Australia and establish a land-and-sea theatre before Tokyo defines the settlement. | **The Straits Enter Indian Command:** current Malacca lane, victory over Malaya, or a live Southern Command. | **The Delhi-Tokyo Resource Question**<br>1. Coordinate shipping with Japan: +300 supplies, +15 Japanese relations.<br>2. Exclude Japan: -250 money, -30 Japanese relations, +1 dissent.<br>3. Sovereign Southeast Asian partners: -2 belligerence, -1 dissent. | Complete the flexible Southeast Asia theatre or a Southern Command victory. The result is Indian credit, not an automatic German or Japanese transfer. |
| **Sovereign Parallel War**<br>`9289548 / 9552 / 9556 / 9560` | Any Indian war. Consult Berlin but retain India's choice of enemy, theatre and peace terms. | **A Parallel Indian Front Exists:** any live Southern, Western or Northern Command. | **The Limits of Berlin Consultation**<br>1. Share intelligence, separate settlements: +1 intelligence, -1 dissent.<br>2. Limited German logistics mission: +500 supplies, +1 dissent.<br>3. Refuse every veto: -20 German relations, +1 dissent, sovereign credit. | A decisive great-power result, a major British or Soviet result, or both Western and Northern Command victories. India is Berlin's partner, not its client. |

### German partner war and collapse

- The compact crisis names Britain, the Soviet Union and the United States.
- Collapse event `9289544` fires if Germany exists but no longer controls Berlin
  (`163`), or Germany has ceased to exist while Italy survives. It does not
  apply a passive German buff.
- India may open a Caucasus lifeline (-1500 supplies, -300 money, +2 dissent),
  force a Suez diversion (-900 supplies, +1 TC, +2 dissent), continue as an
  independent belligerent (+250 money, +1 dissent), or prepare disengagement
  (+1 dissent).

## Soviet route

**Play identity:** define whether Indian socialism is anti-fascist,
anti-imperial, republican-Asian or strategically autonomous rather than treating
every Soviet relationship as one generic Comintern campaign.

| Charter and stage events | Play identity and activation | Intermediate milestone | Three-way dilemma | Culmination criteria and political meaning |
| --- | --- | --- | --- | --- |
| **Anti-Fascist Expedition**<br>`9289585 / 9589 / 9593 / 9597` | Fight Germany, Italy or Turkey as an Indian anti-fascist expedition. | **The Persian-Caucasus Supply Line Functions:** a live Western Command or an Italian or Turkish regional victory. | **Command of the Anti-Fascist Expedition**<br>1. Coordinate with Moscow: +350 supplies, +1 dissent.<br>2. Reserve the Mediterranean to Delhi: -200 money, +1 TC.<br>3. Autonomous socialist belligerency: +1 dissent, autonomous-socialism flag. | A limited/major German result or European-capital victory. Delhi earns its own anti-fascist settlement claim. |
| **Anti-Imperial Ocean War**<br>`9289586 / 9590 / 9594 / 9598` | Fight Britain, the Netherlands, Portugal or the United States and break a colonial maritime system. | **An Imperial Ocean Arc Breaks:** a live Western Command, completed Southeast Asia theatre or limited British result. | **Whose Anti-Imperial War?**<br>1. Joint socialist maritime board: +350 supplies, +1 dissent.<br>2. Local sovereign settlements: -250 money, -3 belligerence.<br>3. Indian security belt: -450 supplies, +2 dissent. | Requires a Western Command victory plus a Southeast Asia or Southern Command victory. It produces an Indian anti-imperial system distinct from Soviet territorial priorities. |
| **A Republican Asian Order**<br>`9289587 / 9591 / 9595 / 9599` | Fight Japan, China, the Chinese Communists, Siam, Malaya or the Netherlands in an Asian constitutional campaign. | **An Asian Political Centre Is Secured:** victory in China or Siam, or an Indochina/Philippines land result. | **The Political Form of Republican Asia**<br>1. League of equal republics: -300 money, -2 belligerence.<br>2. Joint Delhi-Moscow guarantee: +350 supplies, +1 dissent.<br>3. National roads to socialism: -1 dissent, autonomous-socialism flag. | Requires a China/Siam regional victory plus a Southeast Asia theatre or limited/major Japanese result. Local constitutional settlements remain authoritative. |
| **Autonomous Indian Socialism**<br>`9289588 / 9592 / 9596 / 9600` | Any Indian war under a socialist domestic programme without transferring command to Moscow. | **An Autonomous Socialist Theatre Exists:** any live Southern, Western or Northern Command. | **Cooperation without a Veto**<br>1. Equal scientific contracts: -250 money, +1 research.<br>2. Intelligence only: +1 intelligence, -1 dissent.<br>3. Refuse supervision: -20 Soviet relations, +1 dissent, autonomous-socialism flag. | A decisive great-power result or victories in any two national commands. Indian socialism wins on its own ledger. |

### Soviet partner war and collapse

- The compact crisis names Germany, Japan and Britain. Formal Comintern entry
  shares Moscow's live wars.
- Collapse event `9289584` watches Moscow (`572`), or Soviet disappearance while
  Communist China survives.
- India may send an emergency arsenal (-1400 supplies, -200 money, +1 dissent),
  open an eastern diversion (-700 supplies, +1 TC, +2 dissent), proclaim
  autonomous socialist command (-1 dissent), or prepare disengagement
  (+1 dissent).

## Japanese route

**Play identity:** preserve the existing Delhi-Tokyo southern and northern
systems while adding explicit China-Philippines, Indian Ocean and multi-theatre
command politics.

| Charter and stage events | Play identity and activation | Intermediate milestone | Three-way dilemma | Culmination criteria and political meaning |
| --- | --- | --- | --- | --- |
| **Indian Southern Sphere**<br>`9289625 / 9629 / 9633 / 9637` | Fight Britain, Malaya, the Netherlands or Australia. Burma-Andamans open the route; Malaya and the wider southern theatre decide it. | **Malaya Enters the Indian Sphere:** Japanese Malaya objective, current Malacca lane or a live Southern Command. | **The East Indies or Australia?**<br>1. East Indies resource arc: -600 supplies, +300 oil.<br>2. Carry command to Australia: -750 supplies, +1 TC.<br>3. Sovereign southern governments: -250 money, -2 belligerence. | Dedicated Japanese southern victory, completed Southeast Asia theatre or Southern Command victory. Tokyo recognizes Indian primacy; country settlements remain separate. |
| **Northern Coalition Campaign**<br>`9289626 / 9630 / 9634 / 9638` | Fight the Soviet Union either as a compact's separate Indian war or as a formal Delhi-Tokyo allied war. | **The Indian Northern Front Reaches a Strategic Centre:** live Northern Command, Baku (`713`) or Tashkent (`1103`). | **What Should Tokyo Do in the North?**<br>1. Discreet Japanese supply: +10 Japanese relations, +1 dissent.<br>2. Pressure the Soviet Far East: -200 money, -20 Soviet relations.<br>3. Preserve Japanese neutrality and Indian credit: -1 dissent, sovereign credit. | A limited/major Soviet result or Northern Command victory. Both compact and formal-alliance service can earn Indian Caucasus credit. |
| **Indian Ocean First**<br>`9289627 / 9631 / 9635 / 9639` | Fight Britain, the United States, Iraq, Saudi Arabia, Ethiopia or South Africa while Japan concentrates on China and the Pacific. | **The Red Sea and Gulf Hinge Opens:** a live Western Command, Suez (`900`), Aden (`1053`) or the Gulf objective (`1034`). | **Suez, Africa or the Tripartite Lifeline?**<br>1. Suez and Egypt: -650 supplies, +1 TC.<br>2. East African maritime system: -250 money, -350 supplies.<br>3. Sustain Germany: -800 supplies, +25 German relations, +1 dissent. | Requires a Western Command victory plus either a limited/major British result or an Ethiopian/South African regional victory. One port alone cannot complete the western road. |
| **Equal Asian Command**<br>`9289628 / 9632 / 9636 / 9640` | Any Indian war. Seek equality through Indian results in the Philippines, China, Siam or Southeast Asia and then a wider strategic result. | **India Shapes the Philippines or China War:** a Philippine result, China/Communist China/Siam victory, or completed Southeast Asia theatre. | **The Manila and China Division**<br>1. Japanese Pacific command with Indian consultation: +20 Japanese relations, +1 dissent.<br>2. Sovereign Philippine and Chinese settlement: -300 money, -3 belligerence.<br>3. Equal command over Indian-won theatres: -400 supplies, +2 dissent. | A decisive great-power result; Southeast Asia plus a China/Philippines result; or Southern plus Western/Northern Command victories. Delhi becomes Tokyo's second strategic centre. |

### Japanese partner war and collapse

- The compact crisis names Britain, the United States and the Soviet Union.
  Formal alliance shares all Japanese wars; if Japan is already fighting China,
  India inherits that war on accession.
- Collapse event `9289624` watches Tokyo (`1552`), or Japanese disappearance
  while Siam survives.
- India may assume full Asian command (-1200 supplies, +2 dissent), prioritize
  Suez and the Indian Ocean (-700 supplies, +1 TC, +1 dissent), sustain the
  Caucasus war to aid Germany (-1000 supplies, -250 money, +2 dissent), or
  prepare strategic separation (+1 dissent).

### Exact Delhi-Tokyo grand-campaign ledger

The optional ledger at `9289645` is available from the Japanese operations
board from 1937 under either a live Delhi-Tokyo compact or formal alliance. It
records a cumulative human campaign but never replaces the selected primary
charter, transfers territory or grants a second Congress entitlement.

#### Chapter 1: China, Philippines, Southeast Asia and Australia (`9289646`)

1. **China field-command boundary:** India must be formally allied with Japan,
   and both countries must be fighting China (`CHI`) or Communist China (`CHC`).
   Recording the boundary sets the China-posture milestone and coalition
   consultation.
2. **Philippines allocation:** requires the Philippines land result or either
   current/historical Philippines liberation flag.
3. **Southeast Asia-Australia chapter:** requires a Southeast Asia, Japanese
   southern or national Southern Command victory **and** the Australian regional
   victory flag.

Because final completion requires the formal-alliance China-posture flag, a
campaign that remains permanently on the separate-command compact can record
other chapters but cannot complete the full four-theatre acknowledgement. It
must first make the deliberate formal-alliance choice and accept inherited
Japanese wars.

#### Chapter 2: Western Ocean Road (`9289647`)

The stages are ordered and record command only:

1. **Aden:** India controls province `1053`.
2. **Suez:** the Aden stage is recorded and India controls province `900`.
3. **East African ocean system:** the Suez stage is recorded and India has an
   Ethiopian regional victory, South African regional victory or national
   Western Command victory.

#### Chapter 3: Northern Coalition and Germany relief (`9289648-9289651`)

1. Record the northern posture when India has either a formal or compact
   Delhi-Tokyo relationship and is at war with the Soviet Union.
2. Record the Caucasus gate when India controls Baku (`713`) and either Tbilisi
   (`709`) or Astrakhan (`706`).
3. The relief decision is available only when **all** of the following remain
   true:

   - year 1937 or later and the Alpha 23 route contract is active;
   - India is on the Japanese route with a compact or formal Japanese alliance;
   - India is at war with the Soviet Union;
   - Germany exists, is at war with the Soviet Union and still controls Berlin
     (`163`);
   - India controls Baku and either Tbilisi or Astrakhan;
   - the one-time relief decision has not been handled.

4. Dispatching costs India **1200 supplies and 500 oil**. The German-scoped
   callback receives only **900 supplies and 350 oil**. Germany receives no
   passive global modifier. Berlin's acknowledgement then records delivered
   relief and Indian coalition credit.
5. **Defer** leaves the decision open. **Decline** preserves Indian stocks and
   permanently marks the relief decision handled for that campaign.

#### Four-theatre completion (`9289652`)

Completion requires every item below:

- the combined Southeast Asia-Australia chapter;
- the formal-alliance China-posture milestone;
- a regional victory over China or Communist China;
- the Philippines allocation milestone;
- completion of the Aden-Suez-East Africa chain;
- confirmed delivery of the Caucasus relief convoy.

The reward is 200 money, 300 supplies and -2 dissent. It sets a cumulative
secondary grand-campaign flag only; the selected Japanese charter remains the
sole primary route achievement.

## Sovereign route

**Play identity:** make non-alignment an active system of regional pacts,
pairwise wars and Indian-authored settlements rather than an empty sandbox.

| Charter and stage events | Play identity and activation | Intermediate milestone | Three-way dilemma | Culmination criteria and political meaning |
| --- | --- | --- | --- | --- |
| **Build an Indian Ocean League**<br>`9289665 / 9669 / 9673 / 9677` | Fight a sovereign southern or western war against Britain, the Netherlands, Malaya, Australia, Siam or Persia. | **A League Sea Gate Is Secure:** current Bay of Bengal, Malacca or Java lane, or a live Western Command. | **The League's Military Constitution**<br>1. Open sovereign league: -250 money, -2 belligerence.<br>2. Limited Indian bases: -450 supplies, +1 dissent, +1 TC.<br>3. Common fleet command: -300 money, +1 naval organization. | Complete Southeast Asia, Southern Command or Western Command victory. The League gains military foundations without automatic Indian ownership. |
| **Secure the Continental Arc**<br>`9289666 / 9670 / 9674 / 9678` | Fight the Soviet Union, Afghanistan, Persia, Tibet or Xinjiang through a frontier/northern campaign. | **A Continental Gate Is Secured:** victory in Afghanistan, Persia, Tibet or Xinjiang, or a live Northern Command. | **The Political Form of the Continental Arc**<br>1. Sovereign buffer league: -250 money, -2 belligerence.<br>2. Limited Indian bases: -500 supplies, +1 TC, +1 dissent.<br>3. Mobile guarantees: -150 money, -1 dissent. | A Northern Command victory, or paired western-frontier and Himalayan/Central Asian regional victories. India establishes a sovereign strategic arc. |
| **Act as the World Balancer**<br>`9289667 / 9671 / 9675 / 9679` | Fight Britain, Germany, the Soviet Union, Japan or the United States without accepting another capital's command. | **A Great Power Must Account for Delhi:** a limited great-power result or any live national command. | **How Should India Balance the War?**<br>1. Direct Delhi mediation: -300 money, -3 belligerence.<br>2. Sustain the weaker side: -600 supplies, +1 dissent.<br>3. Indian strategic autonomy: +150 money, +2 dissent. | A decisive or major great-power result. Delhi becomes a balancer in fact, not merely in diplomatic language. |
| **Build a Republican Federation**<br>`9289668 / 9672 / 9676 / 9680` | Fight a regional war capable of creating or restoring a sovereign government in China, Siam, Persia, Afghanistan, Africa, Malaya or the East Indies. | **A Regional Government Enters Settlement:** one listed regional victory or current Malaya/East Indies liberation. | **The Federation's Constitutional Promise**<br>1. Equal membership: -300 money, -3 belligerence.<br>2. Mutual guarantees under Delhi: -400 supplies, +1 dissent.<br>3. Temporary administration with exit: -200 money, -1 dissent. | Complete one exact pair—China+Siam, Persia+Afghanistan, Ethiopia+South Africa, or liberated Malaya+East Indies—or complete Southeast Asia plus any one listed China, Siam, Persia, Afghanistan, Ethiopia or South Africa result. Actual sovereignty still follows each local settlement event. |

### Sovereign partner war and collapse

- The Delhi-system crisis watches China or Siam fighting Japan, and Persia or
  Afghanistan fighting the Soviet Union, while India remains outside.
- Its four responses are: publish an independent Indian plan; open the legal
  Japan/Soviet dockets; send 600 supplies and 150 money while staying outside;
  or maintain armed neutrality and Delhi Pact talks for +1 dissent. It does not
  claim to inherit a regional council's wars or offer an impossible coalition
  withdrawal.
- Collapse event `9289664` is deliberately narrower: it reacts to a recognized
  Siamese partner losing Bangkok (`1423`) or a recognized Chinese partner losing
  Nanjing (`1337`), provided India is not fighting that partner.
- India may mount relief (-1000 supplies, -200 money, +1 dissent), guarantee
  evacuation and reconstruction (-350 money, -2 belligerence, -1 dissent),
  assume direct command (-500 supplies, +3 dissent), or preserve neutrality
  (+150 money, +2 dissent).

## Route-specific political conclusions

A completed authored focus sets the route-specific Congress entitlement. Once
India is at peace, exactly one peace Congress may conclude the campaign. The
three mechanical packages are consistent, while their political identities are
route-specific:

| Route / Congress | Concert or league | Security sphere | Strategic autonomy |
| --- | --- | --- | --- |
| Allied `9283270` | **Equal Allied concert:** -4 dissent, -3 belligerence, +1 research and +25 relations with surviving Britain, USA, Australia and Canada. | **Indian Eastern Security Board:** +2 dissent, +3 TC, +1000 supplies. | **Free India cooperation:** leave the alliance and current commitment; +600 money, +3 supply output, -1 dissent. |
| German `9283271` | **Continental balance treaty:** -4 dissent, -3 belligerence, +1 research and +25 relations with surviving Germany, Italy, Turkey and Japan. | **Indian Eurasian security sphere:** +2 dissent, +3 TC, +1000 supplies. | **End pact; technical links:** leave the alliance and current commitment; +600 money, +3 supply output, -1 dissent. |
| Soviet `9283272` | **League of sovereign republics:** -4 dissent, -3 belligerence, +1 research and +25 relations with surviving Soviet Union, Mongolia, China and Communist China. | **Protected republican belt:** +2 dissent, +3 TC, +1000 supplies. | **Autonomous Indian socialism:** leave the alliance and current commitment; +600 money, +3 supply output, -1 dissent. |
| Japanese `9283273` | **Equal Delhi-Tokyo concert:** -4 dissent, -3 belligerence, +1 research and +25 relations with surviving Japan, Siam, China and Australia. | **Indian Ocean security sphere:** +2 dissent, +3 TC, +1000 supplies. | **Separate after victory:** leave the alliance and current commitment; +600 money, +3 supply output, -1 dissent. |
| Sovereign `9283274` | **Open Indian Ocean league:** -4 dissent, -3 belligerence, +1 research and +25 relations with surviving Afghanistan, Persia, Siam and Ethiopia. | **Defended republican sphere:** +2 dissent, +3 TC, +1000 supplies. | **Independent republic:** preserve/restore sovereign command; +600 money, +3 supply output, -1 dissent. |

The Congress defines India's postwar order. It does not retroactively transfer
provinces, override pairwise armistices or erase the conduct and settlement
history accumulated during the war.
