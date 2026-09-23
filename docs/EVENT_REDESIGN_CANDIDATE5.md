# Candidate 5: the remaining diplomatic endings

Staged on 10 September 2026. This consolidates Candidates 1-4 and completes the
bounded content goal: German territorial negotiations, a Moscow access agreement
and a consenting Indian Ocean partnership with a collective ending. It is not
an installable release or a claim that every older event is fully audited.

## Shared rules: fewer moving parts

Six subjects share one proposal/reply/ratification pattern: Baku, Tashkent,
Moscow, Egypt, Oman and Persia. Only one of these negotiations can be open at
a time. Each costs 500 money, disclosed before selection, and allows one attempt.
Fees are non-refundable. Not now is free. A pending decision allows waiting or
permanent closure, including if the recipient disappears or the reply is lost.

The foreign response is queued two days later. It rechecks the current context
and can accept or refuse. Closing beforehand makes that callback harmless.
After acceptance, closing does not reverse a completed territorial transfer,
access grant or pact. It may forfeit the Indian ratification benefit. India
grants any promised reciprocal rights only when the player ratifies verified
foreign terms; leaving them unratified can therefore leave a one-way concession.
There is no hidden automatic reversal or punishment for that situation.

India and the partner must be sovereign and completely at peace. The relevant
current alignment or compact and earned campaign milestone must be present.
The percentages below are foreign AI weights; a human foreign player retains
the choice. No transaction declares war, makes peace, changes an alliance,
creates a puppet or grants Indian national cores.

## Germany: whose flag flies over the city?

Available after the existing German Eurasian focus is completed, or India earns
the Soviet major-victory milestone. India must still be a German partner.

There are separate opportunities for Baku and Tashkent, **only while Germany
actually owns and controls that city**. If India or the USSR owns it, this is
not a proposal to magically acquire somebody else's land. These are conditional
postwar disputes, not guaranteed events in every Axis campaign.

| Indian proposal | German acceptance | Actual concession |
| --- | --- | --- |
| Transfer the city to India | 50% | Germany cedes that province; no core is added |
| Accept access instead of ownership | 80% | Germany grants India military access and a five-year non-aggression pact |

India ratifies a transfer only after it owns and controls the province. Access
terms require the access and pact to exist. Ratification gives +20 relations,
once; the territory or access is the main reward. Refusal causes no war and
cannot be spammed until it succeeds. Candidate 3's separate German-collapse
ending remains available under its own conditions.

## Moscow: where does military cooperation stop?

Available while a Soviet partner after completing the existing Soviet
anti-fascist focus or earning the German major-victory milestone.

| Indian proposal | Soviet acceptance | Terms and ratification payoff |
| --- | --- | --- |
| Separate military zones | 70% | Moscow ends access treaties in both directions and signs a five-year non-aggression pact; verified ratification gives -2 dissent |
| Joint workshops | 85% | Moscow grants access and signs the pact; India then grants reciprocal access and gains +2 research modifier |

This does **not** erase the earlier compact or remove existing economic
supervision modifiers. It negotiates actual military-access treaties. Formal
alliance membership still permits allied movement regardless of those access
treaties; the separate-zones option matters most to parallel compact partners.
The limitation is stated in the event, not concealed behind an autonomy label.

## Indian Ocean partnership: consenting members

Independent India may invite sovereign Egypt, Oman and Persia after one of:

- The national western-victory milestone.
- Limited victory against Britain.
- Completion of the existing sovereign Ocean or continental focus.

Candidate 3's generic closed-campaign flag is not accepted as victory proof,
because it can also mean abandonment. A target still under a puppet master is
ineligible. Candidate 4 can free Egypt or Oman in an Allied campaign, but it
does not automatically switch India to independence or enrol them here.

| Proposed membership | Partner acceptance | Actual bilateral terms |
| --- | --- | --- |
| Mutual defence | 70% | Reciprocal military access, five-year non-aggression pact and guarantees in both directions |
| Commercial partnership | 85% | Reciprocal military access and five-year non-aggression pact; no guarantee |

Foreign access, the pact and any foreign guarantee must be observed before
India ratifies and grants its reciprocal rights. These are a league's practical
rights, not an actual merged state, resource trade agreement or new formal
military alliance. Guarantees do not contain scripted automatic war declarations.

## The collective ending

Two currently sovereign, peaceful, ratified partners with access in both
directions and active pacts unlock **An Indian Ocean Charter**. Historical
acceptance flags alone do not qualify. Expired pacts, revoked access or a member
becoming a puppet can block an unclaimed charter.

Choose **one** permanent Indian institution:

- **Shipping federation:** pay 800 money for +5 transport-capacity modifier and
  +3 supply-production modifier. Any two verified members qualify.
- **Defence council:** pay 1,000 supplies for +3 naval organisation and +2 research
  modifier. Requires two mutual-defence members with both guarantees active.

The shipping federation is an association of sovereign countries, not federal
annexation. Non-aggression pacts last 1,800 game days; access and guarantees have
no scripted expiry. Indian institutional gains remain after the charter, even
if diplomacy later changes. There is no indefinite bonus stack or repeating
congress: the shared charter completion flag blocks both rewards thereafter.

## Scope, identifiers and release limits

Nineteen events (9398700-18) are appended to the already-loaded module 51, using
an explicit non-colliding registry. Every effect-bearing choice rechecks its
conditions. Repeated relationship checks were factored out of membership tests
to keep new action predicates below 6,000 bytes. Descriptions are limited to
500 bytes and titles/buttons to 58; this is not native visual verification.

This finishes the three scoped content areas with concrete, finite mechanics.
It does not promise equal amounts of narrative in every alignment or replace
all remaining legacy choice flags. The full older event lifecycle audit,
installed-compiler safety parity, native peace/release/queue tests, colour and
popup checks, installation and GitHub publication remain separate release work.
The live game and existing saves are not modified by staging.

## Verification

All **364 redesign tests passed** in the frozen consolidated toolchain, in
501.448 seconds. Command:
`python -m unittest discover -s tools -p "test_aubm_redesign*.py"`.
This includes the eleven new transaction tests and the full inherited redesign
regression suite, not only the latest content. No native game execution is claimed.

The consolidated build completed under `build/redesign/candidate5`, identified
as `EVENT-REDESIGN-CANDIDATE5`. It preserves all 5,553 original event IDs and
contains 5,621 events across 58 modules: 68 registered additions, 19 added in
this pass. Earlier candidate outputs remain intact. Fingerprints verify authored
inputs, installed custom/stock modules, toolchain and the protected May 9, 1942
save stayed unchanged during generation. The manifest remains `installable: false`.

After staged validation, Candidate 5 was manually copied into the configured
local mod. The installed 25 `india_v3` files, 33 `aubm_v4` files and
`scenarios/1933.eug` match the staged hashes. A recoverable backup is at
`build/redesign/candidate5/install-backup-20260910-195247`. This did not touch
saves or stock event files. Native launch and campaign transitions remain
unverified.

The presentation scan has zero hard errors and zero generated funding helpers.
Its conservative layout-risk count is 1,862 across the whole corpus, not a count
of confirmed broken windows. Native layout and the original colour issue are
still explicitly unverified. Installed-only fresh-campaign ID reconciliation
has no unresolved IDs; that is not full installed-compiler behavioural parity.
