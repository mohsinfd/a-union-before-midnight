# Southeast Asia Victory Matrix

This is the gameplay-facing specification for the Alpha 21 Southeast Asian
campaign. The short answer is **yes**: the land and sea victory system is
available under every Indian command path. Allied, German, Soviet, Japanese
and sovereign India use the same operational tests. Alignment changes the
political interpretation of a victory; it does not change the ports India has
to secure.

The Japanese partnership also retains its older, stricter Southern Theatre
Directive. That is a separate treaty ledger, not the universal Southeast Asia
test.

## How The Layers Fit Together

| Layer | What it proves | Alignment-neutral? | Can it make peace or transfer land? |
| --- | --- | --- | --- |
| Country campaign | India defeated one named legal opponent | Yes | It can open that opponent's separate settlement file |
| Land operation | India completed one Southeast Asian land result | Yes | No |
| Sea lane | India holds a usable port chain and a large enough surface fleet | Yes | No |
| Southeast Asian theatre | India has three distinct results across both land and sea | Yes | It executes nothing directly; combined with a **current** anti-Japanese friendly liberation, it can support an optional weaker Southern Armistice offer |
| Wartime charter | The current route converts military credit into Allied, German, Soviet, Japanese or sovereign political standing | No; this is the route-specific layer | It opens the appropriate postwar Delhi congress after peace |
| Japanese Southern Theatre Directive | India fulfilled the division of labour agreed with Tokyo | Japan route only | It can open the Delhi-Tokyo Indian Ocean settlement |

This separation is deliberate. An operational award never silently annexes a
province, makes peace with a whole faction or treats a friendly liberation as
a conquest of the friendly legal owner. The Japanese Southern Armistice is a
separate player choice and foreign-response chain. Its theatre route requires
both the permanent theatre record and at least one current anti-Japanese
friendly liberation; it is not a command inside the theatre achievement itself.

## Alignment And Named Wartime Focuses

The full flexible Southeast Asian theatre result is accepted directly by the
following named focuses:

| Indian command path | Wartime charter | Focuses that directly accept the Southeast Asian theatre result |
| --- | --- | --- |
| Allied | The Delhi Allied War Charter | **Eastern Ocean Command** and **Anti-Colonial Liberation Mandate** |
| German | The Delhi-Berlin Division of War | **Dismantle Britain's imperial system** and **Win the southern resource race** |
| Soviet | The Delhi Socialist War Charter | **Anti-Imperial Ocean War** and **A Republican Asian Order** |
| Japanese | The Delhi-Tokyo Wartime Charter | **Indian Southern Sphere** |
| Sovereign / independent | The Sovereign Indian War Charter | **Build an Indian Ocean League** |

The other focuses remain valid, but measure another front. For example, the
German Eurasian focus looks toward the Soviet Union, the Soviet Anti-Fascist
focus looks toward Europe, and the sovereign Continental Arc looks north. A
published country victory outside the selected focus is still caught by the
route's **India Wins Beyond the Charter's Named Front** fallback, so choosing a
continental focus does not make an unexpected Asian war worthless.

Autonomous Indian Socialism uses the socialist/Soviet charter lifecycle while
remaining outside Moscow's formal alliance. Its battlefield tests are still
the same alignment-neutral tests.

A partial land operation, friendly liberation or sea lane remains operational
credit and does not consume the route's one wartime-achievement slot. Only the
completed mixed theatre publishes the route-level campaign victory. Separately
won named-country campaigns still use **India Wins Beyond the Charter's Named
Front** when they genuinely fall outside the selected focus.

## Land Results

There are seven distinct land categories. Several legal owners or campaign
files may feed one category, but repeated victories inside the same row never
count twice toward the three-result theatre test.

| Land category | Direct Indian victory that counts | Friendly anti-Japanese liberation that counts |
| --- | --- | --- |
| Indochina | India controls **Hanoi (1395)** and **Saigon (1399)** in a live war against the U03 Indochina administration or France, with the relevant legal ownership still verified | Japan must previously have occupied both hubs; both must be restored to India or a friendly U03, French, IDC or Vietnamese legal owner; an Indian land formation or direct Indian control must prove participation at one of the two hubs |
| Philippines | India controls **Manila (1565)** and **Davao (1579)** in a live war against the same Philippine, American or Japanese legal owner | Japan must previously have occupied both hubs; both must be restored to India or a friendly Philippine/American legal owner; an Indian land formation or direct Indian control must prove participation at one hub |
| Malaya | A Malaysia campaign victory at **Kuala Lumpur (1438)**, a Singapore campaign victory at **Singapore (1432)**, or the British Malaya result requiring **Singapore and Kuala Lumpur together** | Japan must previously have occupied Singapore and Kuala Lumpur; both must be restored to India or the friendly British, Malaysian or Singaporean legal owner; an Indian land formation or direct Indian control must prove participation at one hub |
| East Indies | A U05 or colonial Netherlands Batavia result at **Batavia (1647)**, or an Indonesian country victory at **Jogjakarta (1654)** | Japan must previously have occupied Batavia; Batavia must be restored to India or the friendly U05, Dutch or Indonesian legal owner; an Indian land formation or direct Indian control in Batavia must prove participation |
| Siam | The Siamese country result at **Bangkok (1423)** | No special friendly-owner shortcut; the normal Siam campaign remains the source |
| Burma | The Burmese country result at **Rangoon (1415)** | No separate legal-owner shortcut is needed for Indian-held territory; the Japanese-war defensive and Southern Command ledgers already test Indian control of Rangoon |
| Borneo | The Brunei result at **Bandar Seri Begawan (1625)** or the Sarawak result at **Kuching (1624)** | No special friendly-owner shortcut; either country campaign feeds the one Borneo category |

Historical victory or completed-settlement credit counts. This prevents a
peaceful constitutional settlement from deleting a victory that India already
earned. It also means that fighting Malaysia and Singapore in succession is
still one **Malaya** category, while fighting Brunei and Sarawak in succession
is still one **Borneo** category.

### Friendly-Owner Liberation Proof

The anti-Japanese liberation path exists because Darkest Hour normally returns
a liberated allied province to its legal owner immediately. Requiring the map
to show `IND` as controller forever would therefore fail even when Indian
troops did the fighting.

The Alpha 21 proof has four safeguards:

1. India must be at war with Japan.
2. The system must first observe Japan occupying the complete published hub
   set while its legal owner is also fighting Japan and is not fighting India.
3. The complete hub set must later be back under India or an eligible friendly
   legal owner.
4. India must directly control at least one hub or have at least one Indian
   land division garrisoning a hub when the liberation is recorded.

The occupation history prevents pre-war friendly bases from becoming free
victories. The Indian control/garrison proof prevents another ally's liberation
from being credited to India. Keep the Indian unit in a listed hub until the
liberation event appears.

A friendly liberation grants operational achievement and modest campaign
credit only. By itself it does **not** open terms against the friendly owner,
transfer its territory, create a pending armistice or end India's war with
Japan. It may contribute one land category toward the full theatre result. If
that theatre record is complete and at least one liberation remains current,
the combination supplies the live Japan-specific leverage needed for Delhi's
optional Southern Armistice offer.

## Sea-Lane Results

The initial sea-lane award requires India to be at war, to have a relevant
Southeast Asian opponent, to satisfy the port chain, and to field at least the
listed number of ready surface combatants.

| Sea lane | Required operational chain | Minimum ready surface fleet |
| --- | --- | ---: |
| Bay of Bengal | **Rangoon (1415)** and **Port Blair (1421)** | 8 |
| Malacca | **Singapore (1432)** and **Kuala Lumpur (1438)**, plus either **Palembang (1636)** or **Batavia (1647)** | 12 |
| Java Sea | **Batavia (1647)** and **Soerabaja (1653)** | 16 |
| South China Sea | **Singapore (1432)** plus either **Saigon (1399)** or **Manila (1565)** | 18 |

Alpha 21 recognizes current friendly-owner liberation credit at the port
hinges where legal control normally snaps back:

- Current Malaya liberation can satisfy the Singapore/Kuala Lumpur side of the
  Malacca lane.
- Current Batavia liberation can satisfy the Batavia alternative on the
  Malacca lane. Direct Indian control of Palembang remains the other
  alternative.
- Current Malaya liberation can satisfy the Singapore hinge of the South China
  Sea lane.
- Current Indochina or Philippine liberation can satisfy the corresponding
  Saigon or Manila hinge of the South China Sea lane.
- Batavia-only liberation does **not** satisfy Java Sea Command. That lane
  still needs Batavia and Soerabaja as a two-base operating system, plus the
  sixteen-ship screen.

Reusing a port is allowed. For example, a Malayan land result and Malacca Sea
Gate are distinct results because the latter also proves the East Indies link
and a twelve-ship fleet.

## The Flexible Three-Result Theatre Victory

The event **India Wins the Southeast Asian Operational Theatre** requires three
distinct results spanning both arms of the campaign. Exactly either of these
structures is valid:

- **Two different land categories plus one sea lane**, or
- **One land category plus two different sea lanes**.

Three land results without a sea lane do not qualify. Three sea lanes without a
land result do not qualify. Two flags belonging to the same land category do
not qualify as two land results.

Examples that qualify:

- Malaya + East Indies + Malacca;
- Indochina + Philippines + South China Sea;
- a friendly liberation of Malaya + Bay of Bengal + Malacca;
- Siam + Java Sea + South China Sea.

Examples that do not qualify:

- Malaysia + Singapore + East Indies with no sea lane, because the first two
  are one Malaya category and both arms are not represented;
- Bay of Bengal + Malacca + Java Sea with no land result;
- Batavia liberation + the U05 Batavia convention + one sea lane, because both
  Batavia achievements are one East Indies category.

Once the flexible theatre victory has been earned, it is permanent campaign
credit. It grants supplies, oil, money, lower dissent/belligerence and sovereign
settlement standing. It grants no province and executes no peace itself. The
historical theatre flag alone does **not** make a Japanese offer available. In
a live India-Japan war, it must be backed by at least one currently maintained
Malayan, East Indies, Indochinese or Philippine anti-Japanese liberation.

## Batavia: Four Different Thresholds

Batavia appears in several systems, but they are intentionally not
interchangeable.

| Situation | Threshold | Result |
| --- | --- | --- |
| Friendly anti-Japanese liberation | Prior Japanese occupation of **Batavia**, followed by friendly restoration with Indian control or an Indian land garrison | One East Indies land result; no peace and no territory transfer |
| Direct war against U05 or colonial Netherlands | India controls legally owned **Batavia** during that pairwise war | Opens the Batavia Convention against that legal owner; sovereign or protected Indonesia can be proposed from Batavia alone |
| Direct Indian mandate in the Batavia Convention | Batavia plus one additional centre legally owned by the same opponent: **Balikpapan (1632), Palembang (1636), Soerabaja (1653), or Manado (1659)** | Makes the costly direct-administration choice available |
| Java Sea Command | **Batavia and Soerabaja**, plus 16 ready surface combatants | One sea-lane result only |
| Japanese partnership East Indies objective | **Palembang, Batavia and Soerabaja** under Indian control | Three points in Tokyo's separate Southern Theatre Directive |

Therefore India does not have to occupy every Dutch East Indies victory
province merely to obtain a defensible political result. Batavia is the local
convention threshold. The wider requirements exist only for direct rule, a
specific naval command or the stricter Japanese treaty ledger.

The Batavia Convention talks only to the verified legal owner. U05 and the
colonial Netherlands have separate dockets; one cannot cede the other's land.
Their normal response is 50% acceptance, 35% commercial counteroffer and 15%
refusal. A lapsed Batavia claim cancels before delivery.

## The Two Japan-Specific Ledgers

### If India Is Fighting Japan

The great-power Japanese campaign remains stricter than the route-neutral
operational matrix:

| Japanese-war milestone | Exact objective |
| --- | --- |
| Ninety-day eastern defence | At the first review, India still controls **Rangoon (1415), Imphal (1442), and Port Blair (1421)** |
| Limited victory | India controls **Singapore and Kuala Lumpur**, plus either **Palembang + Batavia + Soerabaja** or **Manila + Davao** |
| Southern Armistice eligibility | While the Japanese war continues and before decisive victory supersedes this weaker path, either the **current direct limited-victory map** remains valid, or the permanent flexible theatre victory is backed by at least one **current** Malayan, East Indies, Indochinese or Philippine anti-Japanese liberation |
| Decisive victory | India controls both Okinawa provinces **1563 and 1564**, or **Tokyo (1552) and Osaka (1553)** |

Friendly-owner liberation credit does not pretend that India directly occupies
Japan or give India an automatic Japanese armistice. Instead, it gives India a
fair route-neutral operational path when allied territory reverts to its owner.
Once those results complete the full Southeast Asian theatre and at least one
qualifying liberation remains current, Delhi may offer a weaker southern peace
without first taking Okinawa, Tokyo or Osaka. An old theatre result carried
through a route change or a later war is not free leverage by itself.

The offer is optional. Delhi may submit it or decline and continue toward
Japan's inner perimeter. Submission reuses Japan's existing fixed response:

- **45% accept:** pairwise peace plus transfer of eligible southern positions;
- **35% counter:** pairwise peace with reciprocal base access; or
- **20% refuse:** the war continues and only Japan's docket returns after the
  existing 90-day retry period if the same live Japan-specific leverage still
  exists; otherwise the offer waits for a fresh recovery.

Only one southern offer can be in flight, and a shared terms-dispatch lock keeps
queued British, German, Soviet, Japanese and American dockets from colliding
with it. If India reaches the stronger decisive Japanese milestone during the
cooldown, the retry returns to the normal great-power armistice board instead
of downgrading that victory to the southern path.

Even on acceptance, a province transfers only when Japan legally owns it and
India actually controls it. The listed positions are **Rangoon (1415), Port
Blair (1421), Singapore (1432), Kuala Lumpur (1438), Palembang (1636), Batavia
(1647), and Soerabaja (1653)**. Territory belonging to Britain, Malaysia,
Singapore, U05, the Netherlands, Indonesia or another friendly legal owner is
never taken by this offer. Delhi performs the final pairwise ratification, so
only the India-Japan war ends and every unrelated war continues.

The inner-perimeter decisive victory remains the stronger direct Japanese
campaign result, but it is no longer the only route to a Japanese peace offer.

### If India Is Cooperating With Japan

The Delhi-Tokyo Southern Theatre Directive uses points:

| Objective | Hubs | Points |
| --- | --- | ---: |
| Burma-Andaman approach | Rangoon + Imphal + Port Blair | 1 |
| Malaya | Singapore + Kuala Lumpur | 2 |
| East Indies | Palembang + Batavia + Soerabaja | 3 |
| Australia | Darwin (1697) + Canberra (1707) + Sydney (1705) | 3 |

The partnership victory requires at least six points, current control of
Malaya, and current control of either the East Indies trio or the Australian
trio. This can open the dedicated Delhi-Tokyo Indian Ocean settlement. The
Japanese route's **Indian Southern Sphere** focus also accepts the newer
flexible Southeast Asian theatre result, but the flexible result by itself does
not bypass the stricter conditions for the treaty settlement.

## Multiple Countries And Pairwise Peace

India can run several country campaigns in the same war. They do not collapse
into one faction-wide surrender.

The normal sequence for each opponent is:

1. A separate campaign brief names that opponent's objective.
2. Indian capture records that opponent's victory and opens only that
   opponent's live claim.
3. Loss suspends that claim; recovery restores it without paying the one-time
   reward again.
4. A surviving opponent answers separately. The standard country matrix uses
   60/25/15 accept/counter/refuse odds, improved to 75/20/5 by recognized
   coalition, consultation, sovereign or decisive-victory standing.
5. The foreign response never executes peace. Delhi must ratify the selected
   armistice, and that armistice ends only the India-target pairwise war.
6. Annexation opens a separate constitutional choice: restore a sovereign
   government, create a protected state, or accept the political and recurring
   cost of direct rule.

Local Southeast Asian files retain their disclosed exceptions. Britain's
standalone Malaya response is 55/30/15. U05 and colonial Netherlands answer the
Batavia Convention at 50/35/15. The Japanese Southern Armistice uses the
great-power Japan response of 45/35/20. Refusal creates only that country's
retry cooldown. Peace with Britain does not settle the Netherlands, Japan, the
United States or any other belligerent; each surviving country must be handled
through its own file.

Land operations, friendly liberations, sea lanes and the flexible theatre
victory are achievement events. They never send a multi-country peace command.
The completed theatre may unlock the separate optional Japanese Southern
Armistice chain described above; Tokyo must still answer and Delhi must still
ratify it.

## Suspension And Recovery

Every live claim is separated from its historical record:

- Direct land operations suspend when India no longer holds the full objective
  against the verified legal owner in a live war. Restoring the same legal and
  map conditions restores the current claim.
- Friendly anti-Japanese liberations keep permanent earned credit, but their
  current status suspends if any required hub ceases to be held by India or an
  eligible friendly authority. Recovery requires the complete friendly map,
  continued war with Japan and fresh Indian control/garrison proof.
- Sea lanes suspend when a required port chain or the fleet threshold is lost.
  Restoring both returns the current sea-lane status.
- Suspension never pays the achievement again, and it does not delete the
  historical flags already used by the flexible theatre ledger.

For the optional Japanese Southern Armistice, however, historical theatre
credit must be paired with at least one current liberation. Losing every
current liberation suspends that eligibility until a qualifying liberation is
proved again. Current direct Japanese campaign leverage is the alternative
path and follows its own suspension/recovery ledger.

## Alliance Exclusivity And Switching

India may have only one binding commitment family at a time: Allied, German,
Soviet or Japanese. Formal alliances and separate-command compacts both count
as commitments. While one is active:

- rival alliance conferences and legacy entry events are blocked;
- the live-state synchronizers cannot relabel India to a rival route, including
  after an engine-level faction merger;
- India may upgrade within the same family where a treaty explicitly permits
  it, but cannot use that upgrade to jump to another family;
- rival coalition partners are not valid declaration targets.

This is not a lifetime lock. India may explicitly withdraw only while at peace.
Withdrawal places India under sovereign command and starts a 90-day
realignment cooldown. After the cooldown expires, India may negotiate a new
commitment. A partner's collapse or a treaty rupture uses the same sovereign
fallback and reset. Verified battlefield and settlement history survives a
legitimate withdrawal; it cannot be used to keep two current alliance routes
active at once.

## Practical Playthrough Checklist

1. Pick one command relationship and one wartime charter focus.
2. Open the War Cabinet ledger before campaigning so the relevant country
   brief and theatre directive are visible.
3. For an anti-Japanese friendly liberation, let the occupation record fire,
   then retake the complete hub set and keep at least one Indian land division
   in a named hub until the liberation event appears.
4. Build toward 8, 12, 16 and 18 surface ships as the desired sea lanes demand.
5. Aim for either two different land rows plus one lane, or one land row plus
   two lanes.
6. Treat every peace docket as pairwise. Check the next surviving opponent's
   ledger instead of expecting one surrender to end the coalition war.
7. If changing alignment, finish India's wars, use the explicit withdrawal,
   wait through the 90-day reset, and then open the new conference.
