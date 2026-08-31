# A Union Before Midnight Design

## Product Goal

India begins on 1 January 1933 as a sovereign continental union that inherited
British India, Burma and Ceylon. It is unusually large and capable, but starts
with unfinished institutions, weak research coverage, limited money and armed
forces that require deliberate modernization.

A strong campaign should make India a second- or third-rank great power by the
peak of the Second World War. It should not receive an automatic victory. The
intended 1940 industrial range is roughly 150-209 effective IC depending on
investment choices, with higher wartime capacity paid for through finance,
dissent, manpower and strategic exposure.

## Foundation

- Runtime foundation: Darkest Hour Full.
- Playable country: India only; the complete world simulation remains active.
- Scenario date: 1 January 1933.
- Indian territory: undivided British India, Burma, Ceylon, Port Blair and
  Lakshadweep.
- External territory: British Malaya and Singapore, Portuguese Goa, and the
  independent kingdoms of Nepal and Bhutan.
- Borrowed ideas are reimplemented as original event logic. The build does not
  require Blood & Iron or another donor mod at runtime.

## Design Rules

1. Automatic one-option events cannot silently deduct resources.
2. Costly programmes are decisions with visible resource gates and long windows.
3. No major action is a strictly weaker version of another action.
4. Industrial rewards are distributed and capped; late events cannot keep
   stacking infrastructure above 100 or bases above 10.
5. Free capital ships and advanced formations are rare. The player must fund a
   doctrine, shipyard or procurement chain before a commissioning reward.
6. Cabinets change only through explicit constitutional mandates or recovery
   from a stray stock election.
7. Strategy is revisable at peace. Alliance entry remains available after war
   begins unless India is fighting the prospective partner.
8. Foreign policy creates events and material effects in the recipient country,
   followed by a visible answer to India.
9. War milestones react to world state, not one fragile stock-event ID.
10. Great-power leverage is earned through commitment, theatre results and
    sustained war effort, then spent at the peace conference.

## Strategic Campaigns

- Allied: sovereign British cooperation, naval and air integration, Burma or
  Middle East war commands, the Atlantic Charter and a postwar settlement.
- German: blockade-running industry, mobile doctrine, Gulf or Indian Ocean war
  aims, authoritarian reckoning and a revisionist settlement.
- Soviet: industrial planning, deep operations, Tashkent-Persia or eastern
  command, domestic socialist settlement and postwar autonomy choices.
- Japanese: a bilateral Delhi-Tokyo path outside German leadership, China and
  Bose disputes, Imphal, separate command and an Asian settlement.
- Non-aligned: the Delhi conference, multiple suppliers, armed neutrality,
  Asian liberation, mediation and an independent postwar order.

The five strategic route frameworks remain valid through 1964. Orientation,
formal alliance, separate-command compact, bilateral enemy, campaign result and
constitutional settlement are independent state layers. Coalition entry or
departure therefore cannot silently erase a valid Indian war or victory.

## World Pressure

India receives state-based reactions to the fall of France, Italian entry, the
Iraq crisis, the Persian Corridor, Pacific war, Singapore, Indian Ocean raids,
Rangoon and Imphal, the turn in Europe, the defeat of Germany, atomic war and
the defeat of Japan. Earlier modules cover Abyssinia, Spain, China, Anschluss,
Munich, Prague, Albania, Poland and Barbarossa.

The 1937 partnership decisions are no longer Indian declarations into a
vacuum. Britain, Germany, Japan, China, Siam and the Soviet Union answer with
their own AI-weighted terms. A rejected partnership can push India back toward
non-alignment; an accepted independent-Asia programme can become a binding
Delhi Pact with China, Siam or both. The ratification text explicitly warns
that an alliance also accepts every current and future war obligation.

## Current Scope

- 4,577 custom event entries across 57 India and foreign-response modules.
- 103 player decisions and 4,474 automatic events or foreign replies.
- 236 practical opponent tags: 26 bespoke campaign systems and 210 generated
  country lifecycles, including later successor states.
- Three constitutional governments, a 1936 mandate and a 1946 postwar mandate.
- Annual budgets from 1934, capped domestic debt and separable foreign credit.
- Three regional naval commands with a reduced capital-ship programme.
- Path-specific AI profiles, wartime systems and 1946-64 continuation content.
- India-specific leaders, ministers, technology teams, cleared event art and
  counters. Public builds use stock sprite families and omit donor model panels;
  the validated animated India sprite package is an optional local-only profile.

## Release Gates

1. Parser structure, event-ID uniqueness and command-schema validation.
2. Cross-event target, country, date and flag validation.
3. Province ownership and construction guard validation.
4. Cumulative infrastructure and base-cap analysis.
5. Unit-type, model, attachment, leader, minister and technology-team validation.
6. Stable-cabinet and stock-election suppression contracts.
7. Persistent budget, strategy and commitment recurrence contracts.
8. Late path and coalition-entry availability contracts.
9. Opening treasury, combat pacing, event-art and sprite audits.
10. Idempotent rebuild, exact installer manifest and verified separate deployment.

Static gates greatly reduce delayed Darkest Hour crashes. A closed-engine
playthrough remains the final check for executable behavior that no file parser
can observe.
