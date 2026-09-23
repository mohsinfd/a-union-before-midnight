# Follow-up decisions: stronger settlements and clearer events

User feedback recorded 7 September 2026, after LIBERATOR1 installation.

**Status:** the current-playthrough decisions below were subsequently approved
and implemented in LIBERATOR2, with a deeper Soviet threshold than the initial
proposal. See [the current specification](LIBERATOR2_LONG_WAR_OUTCOMES.md).
The original proposals below are retained as design history, not current gates.
The all-event clarity audit at the end remains deferred until the playthrough ends.

## Current-playthrough revision to agree

### China: distinguish three genuinely different offers

The installed Nanjing offer frees the existing Chinese government from Japan;
it does not make China India's puppet. Its strategic benefit is removing a large
state from Tokyo's system, not transferring its factories or manpower to India.

Recommended extension:

1. **Independent Chinese partner:** retain the existing lighter settlement.
2. **Temporary Indian protectorate:** an explicit Indian puppet relationship,
   requiring stronger leverage than the existing three-city offer. Initial test
   proposal: add Chongqing to Nanjing, Shanghai and Wuhan and require sustained
   control. Make the protection demand less acceptable than simple independence.
3. **Continue the war:** no compulsory peace or automatic acceptance of reduced
   terms. A foreign counteroffer returns to an Indian confirmation decision.

For the protectorate, propose a constitutional review after two years and peace
with Japan. The player may grant full independence while negotiating continued
cooperation, or retain the protectorate with clearly stated political costs.
Release must not replay the original conquest or liberation reward.

The existing U87 government and units remain; this does not resurrect Chiang.
Japan-owned Shanghai remains a Japanese-war question. Puppet creation, alliance
membership and inherited wars need explicit engine verification before deployment.

### Tibet: Indian puppet is the requested end state

Tibet is a separate existing state in the reviewed save. China cannot transfer
Tibetan sovereignty simply by surrendering Nanjing. A Chinese outcome can unlock
a dedicated Delhi-Lhasa settlement, with Indian protection as the desired end
state; a Tibetan treaty or an earned Tibetan victory should supply the actual
authority to establish the puppet. The current game does not automatically
puppet Tibet after the Chinese offer succeeds.

### USSR: stronger leverage, stronger strategic reward

The existing protected-republic settlement already creates Indian puppets from
complete legally transferred territories. It has a 25% acceptance, 45% narrower
counteroffer and 30% refusal roll, and adds six dissent when implemented.
LIBERATOR1's new reconstruction and two-front conference currently accept only
the fully sovereign branch, excluding protected republics. That mismatch must be
resolved if the intended path becomes a client-state campaign.

Interpretation requiring confirmation: **"independent and Indian" means separate
Central Asian republics outside the USSR but under Indian puppet control**, not
directly annexed Indian provinces. These outcomes must not share an ambiguous label.

Recommended balance direction:

- Baku plus Tashkent or Astrakhan remains an operational milestone, not sufficient
  by itself to dismantle the Soviet southern empire.
- A protectorate settlement requires a broader offensive, complete territories
  for every republic demanded, and sustained control. Test Baku, Tashkent and
  Astrakhan plus at least two complete republic territories and a 60-day hold as
  an initial regional threshold, not an already validated balance claim.
- Soviet willingness must reflect the wider war. A secure USSR facing India alone
  should demand substantially more leverage, such as the fall of Stalingrad,
  than a USSR already suffering serious losses on another major front.
- Never grant five republics because India occupies enough land for only two.
  Moscow's fall remains relevant to a decisive great-power defeat; it need not
  be compulsory for every limited border peace.
- Protected republics should produce a visible Indian strategic sphere and
  explicit, bounded reconstruction/logistics benefits. Do not imply that their
  IC or manpower automatically becomes Indian IC or manpower.
- Give these states a later, optional transition to equal independence. Do not
  reissue conquest rewards or force an unrelated Indian war to end.

An existing design flaw to address with this revision: the base-rights counteroffer
event (9282044) has only an accept action and schedules ratification. Requesting
protected republics can therefore lead to peace on narrower terms without a
meaningful reject choice. Show the actual terms and allow refusal before peace.

### Suez stays an optional side quest

No change is needed to the current objective structure. Neither the southern
peace nor the two-front finale requires Suez. It should activate only when the
world situation presents the opportunity and India chooses the relevant war.
Do not make an Axis war compulsory for the Japan/Soviet campaign.

### Fresh campaigns

LIBERATOR1 is in the normal event index and works for fresh campaigns in the
updated installation, not just the reviewed save. Its current opt-in/date gates
begin in 1940. It is installed in AUBM Terrain Prototype P1; the separate normal
installation was intentionally not updated. No claim of a new public alpha or
published release is made.

For the eventual fresh-start clarity pass, introduce direction after the Union
opening rather than postponing the first useful explanation until 1940. Keep
later war, territory and resource gates intact; an early guide must not award
wartime credit, choose the player's route or force a declaration.

## Deferred until the current playthrough is finished: all-event clarity audit

This is explicitly the next phase, not a mass rewrite during the current save.
Audit all loaded AUBM events and reachable legacy/foreign callbacks, not just
LIBERATOR1. Separate retired unreachable text from content a human can encounter.

Acceptance requirements:

1. A selection states its action in ordinary language. Use "Make China an Indian
   puppet", not a poetic phrase concealing that consequence.
2. Surface immediate costs, war entry, inherited alliance wars, puppet status,
   permanent route commitments and any loss of control at the decision point.
3. Name the parties and distinguish negotiating from accepting or signing.
   A counteroffer may not silently become a binding peace.
4. Explain visible locked choices and the next attainable milestone. Distinguish
   an optional side quest from the selected campaign's required victory conditions.
5. Describe lasting versus temporary effects, recurring upkeep, cooldowns, annual
   versus one-time rewards and reversibility. A promise in prose must have a
   matching implementation.
6. Preserve no-effect Cancel/Not now exits; no menu may force a diplomatic choice
   merely to close it. No automatic return loop.
7. Add an early campaign-direction briefing and an accessible in-play objective
   summary that updates when the player's route or world situation changes.
8. Respect the engine's 58-byte action-label and 500-byte description limits.
   Use short labels plus explicit confirmation screens for complex consequences.
9. Preserve event IDs, history, paid credit and existing save compatibility where
   possible. Label text-only changes separately from intentional gameplay changes.
10. Test fresh starts, existing saves, every alliance/independent route, resource
    shortages, rejected offers and repeated menu visits. Include human readability
    checks; static syntax tests alone do not establish that choices feel clear.

Do not start this deferred rewrite or an automatic monitoring job just because
this note exists. Resume it when the user finishes the playthrough and asks to
begin that phase.
