# A Union Before Midnight Art and Research Credits

## Scope

A Union Before Midnight contains a complete India-specific visual and research pass:

- 31 bespoke technology-team images.
- 44 distinct minister and military-leader portraits.
- 28 V3 event images.
- 101 researched minister, commander and technology-team assignments.

The machine-readable manifests under `tools/data` are the authoritative asset
and research records. The build validator requires exact coverage and checks
the packaged files against their recorded hashes.

## Personnel Portraits

`tools/data/personnel_art_manifest.csv` records the person, source page,
licence, licence URL and provenance for every active personnel portrait.

- 27 portraits are derived from historical photographs.
- 17 portraits are explicitly labelled plausible painted reconstructions.

A reconstruction is an original alternate-history game asset informed by the
person's career and period. It is not presented as an archival photograph or
as proof of an undocumented historical appearance.

## Technology Teams

All 31 technology-team source images are generated originals made for the
specific institution or team. They do not reuse a minister, commander or
another technology team's portrait. `tools/data/v32_art_manifest.csv` records
the source, output path, provenance and rendered SHA-256 hash.

## Event Art

The same V3.2 art manifest covers all 28 event images:

- Three are generated original campaign images.
- Twenty-five are distinct transformed period photographs already packaged
  with the Blood and Iron foundation.

These images are processed into Darkest Hour's required indexed bitmap format.
The packaged Blood and Iron photographs remain subject to the permissions and
credits of that project and its contributing graphic packs.

## Historical Traits

`tools/data/india_historical_traits.csv` records the exact active game
assignment, historical basis, alternate-history embellishment and research
source for:

- 41 V3 minister records.
- 29 V3 military leaders.
- 31 technology teams.

Traits are grounded in documented careers where possible. Earlier entry dates,
higher ceilings and cross-service roles are used only where the 1933
independence timeline makes the development plausible. The manifest makes those
embellishments explicit rather than presenting them as literal history.

## Foundation

A Union Before Midnight is built on Blood and Iron v1.1 by thewanderingknight. Blood and
Iron incorporates work from World in Flames 2, Edge of Darkness, Total Realism
Project, Francesco's Models Mod, Kazoo's SKIF Style Icons, Decriser's DEC Map,
the Official Graphic Pack, Horton13's Graphic Improvement Project,
tioperete's ProvincePics Project and the sprite and graphics contributors
credited in the original Blood and Iron release.

Public redistribution must retain the original Blood and Iron credits and
respect the permissions attached to the foundation and each archival source.

