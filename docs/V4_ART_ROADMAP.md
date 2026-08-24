# V4.2 Visual Roadmap

## Objective

Give India a coherent, historically grounded visual identity without restoring
the Blood and Iron dependency or redistributing uncertain donor assets.

Archival photographs are preferred when a public-domain or clearly licensed
source exists. Alternate-history scenes use original generated reconstructions
and are labelled as such in the art manifest. Generated reconstructions must
not be described as historical photographs.

## Current Baseline

- All 4,343 campaign entries resolve to valid picture references.
- All 102 custom event-picture files are byte-distinct and locally sourced.
- The strict event-art and provenance gate passes with zero issues.
- All redistributed custom minister and military-leader portraits are
  byte-distinct; unresolved new leader likenesses use the stock
  `unknownleader` token.
- All 31 technology-team images are byte-distinct.
- Personnel pictures use the correct Darkest Hour dimensions and indexed format.
- The current personal build contains 41 independently addressed Indian unit
  families, 591 descriptors, 553 animated bitmap strips and 44 palettes.
- Forty sprite families are rebuilt from a locally installed Blood and Iron
  donor and one from Darkest Hour core; provenance and hashes are recorded.
- The personal sprite gate passes, but donor assets are not cleared for public
  redistribution.
- V4 uses Darkest Hour Full model and production-screen panels for ordinary
  units. Donor-derived special-unit cards are excluded; reserved models 33-40
  currently use the engine's missing-art placeholder pending original panels.

## Phase 1: Event Art - Complete

Replace every fallback copy with a subject-specific image and give the 45 V4
events a coherent visual set.

Priority groups:

1. The 1933 settlement, cabinet and union-integration sequence.
2. Army command, airfield security, fleet and procurement programmes.
3. Allied, German, Soviet, Japanese and non-aligned strategic routes.
4. Abyssinia, Spain, China and the European crisis sequence.
5. Wartime settlements, liberated-territory policy and demobilization.

Exit criteria:

- No two custom event-picture names contain identical bytes.
- Every custom event image is a 400x116, 24-bit BMP.
- Every archival image has a source, creator and licence record.
- Every generated image is marked as an original reconstruction.
- No swastika, prohibited emblem, watermark or embedded text appears.

Completed outputs:

- `docs/v4_event_art_manifest.csv`
- `docs/art_manifest.csv`
- `assets/event-gallery.png`
- `tools/art_sources/v4_events`

## Phase 2: Personnel And Technology Teams

The current files are distinct, so this phase is an identity and provenance
audit rather than a bulk replacement.

- Confirm every portrait against the named person.
- Prefer an archival likeness over a reconstruction when licensing permits.
- Retain reconstructions only for people without a usable historical image.
- Confirm each technology-team scene represents the named institution and its
  research specialties.
- Rebuild the personnel and technology-team galleries after corrections.

## Phase 3: Model Panels And Production Art

Create an original India namespace for the models most likely to appear in an
India campaign:

- infantry, mountain, Gurkha, marine and airborne formations;
- cavalry, motorized, mechanized and armoured formations;
- interceptor, fighter, tactical, naval and transport aircraft;
- destroyers, cruisers, battleships, carriers, submarines and transports.

Panels must remain readable at Darkest Hour production-screen scale and may
not reuse another mod's SKIF or model artwork.

## Phase 4: Map Sprites - Source Set Archived

The core service set includes:

- khaki infantry;
- green Gurkha and mountain troops;
- motorized and armoured columns;
- fighter and bomber silhouettes;
- destroyer, cruiser, capital-ship, carrier, submarine and transport
  silhouettes.

The archived experiment contains 13 original visual families and source data
for 32 Darkest Hour unit types. Source sheets are preserved under
`tools/art_sources/v4_sprites`, but generated `C-IND` descriptors, bitmaps and
palettes are excluded from the stable live overlay.

Exit criteria:

- stock fallback renderer present: complete;
- no custom descriptor, bitmap or palette in the live overlay: complete;
- extended in-engine soak without a DirectDraw crash: required before any
  bespoke service-sprite package returns.

Archived development outputs:

- `docs/v4_sprite_manifest.csv`
- `assets/sprite-comparison.png`
- `tools/build_v4_service_sprites.py`
- `tools/audit_v4_sprites.py`
- `tools/art_sources/v4_sprites`

## Phase 5: Release Packaging

- Run `tools/audit_v4_art.py --strict`.
- Rebuild all galleries and machine-readable manifests.
- Regenerate installer hashes.
- Deploy to the isolated V4 folder.
- Perform one scenario-load visual pass and one model-upgrade smoke test.
