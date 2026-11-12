# R11 — full minister integrity and playable campaign content

R11 adds 22 substantive gameplay encounters: six prewar programmes, eight country-specific operational decisions and eight American mainland encounters. Technical receivers and American responses are included in the generated event register; they are not advertised as dozens of extra player decisions. Existing R10 IDs stay fixed. This is a new-1933-campaign revision, without save edits or a running-game test.

## Ministers

All 383 Japanese appointments resolve to 90 valid personalities, with matching offices, 432 used command entries and 180 localisation references. No Generic fallback, missing trait, wrong office or duplicate appointment/personality ID was found. Eleven appointments are additions; six original rows deliberately differ from the clean 372-row source roster. Full row-by-row evidence is in MINISTER_INTEGRITY_ROSTER.csv.

All 13 custom trait descriptions are now generated from their actual commands. Naval/aircraft equipment research is distinguished from doctrine research, Fleet Carriers from Light Carriers/CAGs, and construction cost from time. This closes wording drift without silently buffing existing ministers.

## Before the Pacific war

Six manual preparations open in April 1933, June 1934, February 1935, May 1936, March 1938 and January 1940. They cover rural industry/reserves, carrier flying/protection, navigation/AA, amphibious organisation/assault training, medical recovery/fitness intake and dispersed/concentrated factory investment. Funding and selected outcome are explicit; there is one guarded completion notice and no recurring reminder. See PREWAR_CONTENT.md for exact costs, effects and checks.

## China, the Philippines, Indonesia and Malaya

Eight country-specific programmes provide alternatives with physical consequences: Shanghai Garrisons/Infantry; Wuhan Mountain Infantry/casualty recovery; Manila Interceptors/Naval Bombers; Philippine soldiers/merchant shipping; Soerabaja Destroyers/Light Cruiser; Indonesian oil/mineral exports; Singapore temporary spare-parts service/merchant replacement; Malayan rubber/tin versus energy/supplies.

Funded formations use researched ordinary models with complete native manpower costs. They arrive as equipped units, not zero-progress orders or retired custom classes. Each selected branch checks elapsed funding time and the required position at delivery. National stock awards still require ordinary convoy distribution. Puppet/neutral relations are preserved; neutral treaties qualify only for their stated civilian alternatives. Details: COUNTRY_CAMPAIGNS.md.

Existing Chinese aid opens from 1938; expedition/home-defence and reconstruction open from 1939 once a puppet actually exists. The military aid sends China 35 manpower and 3,000 supplies, replacing an unfunded infantry order. Both economic and military recipients now have distinct branch markers and one-time receipts; queued superseded aid refunds once instead of guessing the selection.

The Philippines settlement now also handles an absent Commonwealth while America legally owns occupied Philippine land. It transfers only Japanese-held Philippine provinces, then uses the existing local settlement chain. It does not make American peace. Puppet and neutral terms are independently checked.

## Invading America

The first landing, California corridor and Denver/Kansas City milestones offer finite captured stocks. Two manual Japanese support programmes fund replacement reserves or campaign supplies. America can form two bounded six-division reserve waves at safe American-owned rear hubs, paying real manpower and supplies; inadequate resources/research/sites yield a declared finite reserve budget instead. A separate one-time endurance budget supports a long defence. Japanese notices report the actual American outcome.

No new event forces a declaration, surrender, strategic route, alliance or province concession. Existing national surrender and Pacific armistice terms remain separate. Details: US_CAMPAIGN_CONTENT.md.

## Qualification

Focused tests execute compiled conditions and scheduled award/refund paths. The complete offer matrix supplies explicit eligibility witnesses and delivery traces. Installed static validation compares every generated event with current source. These are offline checks; actual engine UI, deployment/supply handling, AI movement and sustained Hard difficulty remain for the user's playtest. No game launch, save edit or Germany Overhaul modification is authorized by this delivery.
