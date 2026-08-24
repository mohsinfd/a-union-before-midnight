# A Union Before Midnight Art And Research Credits

## Scope

A Union Before Midnight V4 includes an India-specific event, personnel and
research visual layer:

- 102 custom event-picture files used by 4,341 event and decision entries.
- 31 distinct technology-team images.
- 47 distinct minister and military-leader portraits.
- 101 researched minister, commander and technology-team assignments.
- 13 archived experimental India map-sprite source families covering 32 engine
  unit types; the stable live overlay uses Darkest Hour's fallback renderer.

The machine-readable records under `docs` are authoritative:

- `art_manifest.csv` records every custom event and technology-team output.
- `v4_event_art_manifest.csv` maps each V4 event ID to its source sheet,
  panel, picture name and rendered SHA-256 hash.
- `personnel_art_manifest.csv` records portrait identity and provenance.
- `india_historical_traits.csv` records historical and alternate-history
  support for active personnel and technology-team traits.
- `v4_sprite_manifest.csv` records each archived sprite family, covered unit
  type, source sheet, generated files and historical output hashes.

## Event Art

All 102 custom event pictures in V4 are original AI-assisted reconstructions
created for A Union Before Midnight. They are not archival photographs and
must not be represented as documentary images of events that did not occur.

The preserved source sheets are under `tools/art_sources/v4_events`. Each
picture is cropped and rendered as a `400x116`, 24-bit RGB bitmap for Darkest
Hour. The event-art release gate checks:

- exact event-ID and picture-name agreement;
- source-sheet presence and reconstruction disclosure;
- dimensions, encoding and output hashes;
- complete manifest coverage;
- absence of duplicate custom pictures.

The generated scenes intentionally avoid modern equipment, embedded captions,
watermarks, swastikas and fascist symbols. Historical flags or recognizable
marks are not required for an event to communicate its subject at game scale.

## Personnel Portraits

`personnel_art_manifest.csv` records the person, source page, licence, licence
URL, creator, required credit line and provenance for every active custom
portrait.

- 30 portraits are derived from historical photographs.
- 17 portraits are explicitly labelled plausible painted reconstructions.

A reconstructed portrait is an alternate-history game asset informed by the
person's career and period. It is not presented as an archival likeness or as
proof of an undocumented historical appearance.

## Technology Teams

All 31 technology-team images are distinct generated originals made for their
named institution or service. They do not reuse a minister, commander or
another technology team's portrait. The packaged `96x96` indexed bitmap is the
retained master for this release and is recorded in `art_manifest.csv`.

## Map Sprites

The 13 India service-sprite source families are original AI-assisted
illustrations generated for A Union Before Midnight. They are not derived from
Blood and Iron or another donor mod. The preserved sheets are under
`tools/art_sources/v4_sprites`, and `v4_sprite_manifest.csv` records their
relationship to 32 Darkest Hour unit types. They are research sources, not a
packaged animation payload.

The public build uses Darkest Hour Full's stock sprite keys and contains no
custom service-sprite descriptor, bitmap or palette. An explicitly selected
developer-only build can instead reconstruct 41 animated families: 40 from a
locally installed Blood and Iron v1.1 and one from Darkest Hour core. Those
generated files have a separate hash/provenance manifest, are excluded from Git
and public installer manifests, and are not redistribution-cleared.

## Historical Traits

`india_historical_traits.csv` records the active game assignment, historical
basis, alternate-history embellishment and research source for:

- 41 minister records;
- 29 military leaders;
- 31 technology teams.

Traits are grounded in documented careers where possible. Earlier entry dates,
higher ceilings and cross-service roles are used only where the 1933 Union
Settlement makes the development plausible. Those changes are identified as
alternate-history embellishments rather than literal history.

## Foundation

V4 is an overlay for the user's legally installed Darkest Hour Full. The
installer copies that local foundation into an isolated mod folder and applies
only the files in the release manifest. The repository does not distribute the
complete game.

V3 was developed against Blood and Iron. Public V4 installs do not require it
and deliberately exclude donor-derived model panels, map sprites, palettes, AI
files and event art. The original V4 event art and archived map-sprite source
sheets described above replace the former public visual fallbacks. Darkest Hour
Full model and production-screen panels remain the foundation for ordinary
units; reserved models 33-40 use the engine placeholder until an original V4
panel set is completed.

Darkest Hour, Hearts of Iron and related marks belong to their respective
owners. A Union Before Midnight is a non-commercial fan project and is not
affiliated with or endorsed by them.
