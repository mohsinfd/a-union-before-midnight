# Player-request fix ledger

This is a compact audit of the specific small issues raised during the recent
playtests. It distinguishes a repair that is in the current **27-BALANCE1 +
27-ROSTER1 + ART2** local build from a proposal or a repair that still needs a
native Darkest Hour test. It does not rewrite saves.

## Installed and statically verified

- **Opening popup flood** — the first-week political rush was reduced to an acknowledgement, cabinet within 72 hours, and the Union on 6 January.
- **Retired/duplicate route noise** — 217 old route, wartime, Gurkha and frontier decision IDs were pre-slept so they cannot restart their old loops in a fresh game.
- **Mutually exclusive constitutional routes** — the 1934 and 1936 reviews now close each other correctly.
- **Early alliance lock-ins** — Tokyo now offers a genuine free defer, and a live great-power commitment blocks incompatible alignment offers.
- **Tokyo proposition forcing an early choice** — defer no longer sets the old flag that accidentally closed the later channel.
- **Cabinet/war-cabinet menu clutter** — unsafe legacy menus were redirected and the new progress boards are read-only rather than looping action menus.
- **Foreign credit charge** — the old service fee is no longer charged before a credit benefit is received.
- **Missing advertised research rewards** — the two recorded rewards that previously did nothing now have actual effects.
- **Village’s Share** — extreme dissent penalties and the property-settlement manpower/revenue imbalance were reduced.
- **Civil Service Settlement** — provincial recruitment no longer carries an arbitrary +2 dissent penalty.
- **Princes and Union** — accession versus statutory integration now has smaller, differentiated dissent and revenue trade-offs.
- **Delhi Communal Compact** — the easy -5 dissent choice was cut to -2 and the civil-code penalty removed.
- **Ambedkar / Equal Citizenship** — enforceable rights no longer imposes +3 dissent and gives a meaningful recruitment return.
- **Burma’s place in the Union** — autonomy and eastern administration have differentiated costs and neither option releases Burma.
- **League of Nations** — options now differ by relations, money, intervention and dissent without secretly selecting a bloc.
- **London Settlement** — commercial, defence and clean-break choices received less one-sided dissent/supply/revenue costs.
- **Rebuild the Indian Army** — citizen, mobile and professional paths now have separate military benefits; professional grants infantry morale.
- **Quetta–Delhi schools** — general, mountain and marine schools now have concrete HQ or branch-morale effects at lower branch-school cost.
- **Standing divisions** — smaller cadre and professional alternatives are less punitive and every option checks the resources it spends.
- **Provincial Forces / Indian Youth** — all choices unlock the inherited state troops; the one-army dissent penalty and excessive recruitment debits were removed.
- **Locked Indian units** — all eight inherited locked state divisions release through Provincial Forces, or automatically at India’s first war.
- **Flying Schools** — the central-school alternative now grants air organisation so it is not simply inferior to clubs/bases.
- **Airfield Security Act** — it now delivers early aircraft, airbase improvement and two field guards; it no longer hands out invalid ground-division packages.
- **Operational Air Group confusion** — its text now distinguishes Airfield Security’s delivered planes from later normal production.
- **Abyssinia wording** — labels and descriptions were shortened and plain-language costs/odds retained.
- **Mountain research gap** — Quetta–Delhi was confirmed as a valid, active 1933 mountain-training team rather than duplicating a team unnecessarily.
- **Thin commander pool** — 375 fictional reserve officers were added progressively, on top of the named roster, without artificial skill/rank inflation.
- **Duplicate ministers** — 34 redundant same-person/same-office entries were consolidated and seven distinct alternatives added.
- **Underused research teams** — four specialist roles were added and the roster audit gives every one of the 35 teams a leading research job.
- **Repeated stock officer art** — ART2 installs 311 individual reserve portraits, 64 retained unique portraits and nine historical commander photos; no stock image is reused for the new officers.
- **Navy catch-up too extreme** — naval construction support is now 25% in peace and 40% at war, rather than the previous 50% wartime headline.
- **Industry choices crowding out resources** — direct factories were reduced and the economy chain pairs industrial gains with energy, metal, rare-material, oil or supply pressure.
- **Late oil/fuel dead end** — 1941 and 1943 resource choices were added after the refinery chain rather than ending fuel support too early.
- **Soviet victory arriving too easily** — northern recognition now requires named deeper objectives and a sustained 60-day wartime hold.
- **Britain’s small speculative invasions** — British AI invasion weighting was reduced while key ports/strategic points receive stronger garrison priorities.
- **Italy abandoning Libya/Balkans** — Italian overseas and Balkan defence weighting was strengthened.
- **Germany never reinforcing Africa** — a guarded, paid German–Italian African reserve becomes available only under mid-war survival conditions.
- **Finland collapsing immediately** — Finland received a homeland-defence switch and a guarded German continuation-war reserve.
- **Germany leaving Norway open** — Oslo, Bergen, Trondheim and Narvik were given higher German garrison priority.
- **Major powers ignoring India** — seven major opponents now have guarded reactions to a human India, rather than treating it as a passive minor.
- **Version ambiguity** — the current scenario/menu identity is `27-ROSTER1`; the ART2 installation receipt identifies the art-only follow-up.

## Implemented, but needs a fresh-game engine test

- **India changing alliances after joining one** — commitment synchronisers are designed to keep a live pact exclusive and preserve peace-time withdrawal/re-alignment, but the engine sequence needs a real test.
- **Japan route with controlled war scope** — the Delhi–Tokyo compact is meant to preserve Indian war choice while formal membership inherits Japanese wars; verify this in the campaign.
- **Long-war Japanese, Chinese, Soviet and Indochina rewards** — deeper timers, client-state choices and reject-and-continue-war answers exist in the authored installed campaign layer, but settlement commands need native verification.
- **Soviet republic outcomes** — Central Asian protectorate/independence outcomes were expanded and made deeper, but are not certified by an engine playthrough.
- **Enemy AI taking India seriously** — reaction scripts and garrison priorities are installed; actual AI posture remains a playtest question.
- **Balance of alternative event choices** — the named opening choices above were repaired, but their final relative value needs player testing rather than assumed balance.
- **Yellow/white explanatory text spillover** — event prose was shortened and the installed text contains no explicit colour-control leak; actual popup rendering has not been checked in the game.
- **ART2 display in a new campaign** — files and mappings are installed and hash-verified, but the game has not been launched after this art install.

## Not claimed fixed / still open

- **One Flag, Many Provinces** — missed by BALANCE1: `Negotiate` combines -5 dissent with four infrastructure grants, while Provincial Freedom and Centralize do not offer enough distinct value to offset their weaker political outcome.
- **Terrain readability and the selected-province-style default** — Alpha 27/hybrid terrain did not pass your human visual review; no claim is made that it now matches Blood and Iron.
- **India’s map colour / pale jade versus grey** — this visual decision is not certified as installed in the current playable target.
- **Default grey/blue populated ports and airbases** — not certified as implemented.
- **A general at-war manpower mobilisation system** — not implemented as a proven yearly manpower answer; current changes only improve particular events and roster capacity.
- **Supply sufficiency for a large Indian armour/navy build** — resource pressure was reduced, but no promise is made that every build plan will be self-sufficient.
- **Every naval event adding the intended brigade only** — no blanket repair is claimed without a reproducible event-by-event audit.
- **Siam peace leaving a Japanese puppet / forced peace** — not certified repaired as a general settlement rule.
- **Japanese stock Asia events firing while India fights Japan** — not certified as globally suppressed.
- **Indonesia settlement failing to puppet India or leaving Japanese-owned provinces** — not certified repaired; use a fresh test before trusting this outcome.
- **Nepal and Bhutan delayed national-province lifecycle** — it is a documented staged proposal, explicitly not installed; voluntary integration is intended to mature after 1,080 days and conquest after a paid 1,800-day process.
- **Nepal/Bhutan diplomacy improving from Indian strength/relations** — current staged odds are fixed rather than diplomacy-sensitive; this remains a design limitation.
- **All historical crashes** — the known event-parser/action repair was made, but launch/save stability has not had enough native regression testing to call solved.
- **Every remaining event’s bureaucratic language and every unbalanced choice** — only the named opening/event set above was audited; a complete line-by-line polish pass is still open.

## What this means for the next campaign

Start a **new 1933** game for 27-ROSTER1 and ART2. Do not use an old autosave to
judge new leaders, minister entries, research-team coverage, economic balance,
or opening locks: saves preserve earlier state and portrait references. Treat
the items in the second section as explicit live-test objectives, not promises.
