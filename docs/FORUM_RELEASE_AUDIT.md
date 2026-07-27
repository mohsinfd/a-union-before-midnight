# Forum Release Audit

## Candidate

This audit covers the V3.4.1 Open Beta release candidate for A Union Before
Midnight. It records technical checks; it is not legal advice or moderator
approval.

## Image Review

- Replaced `india_v3_german_panzer.bmp`,
  `india_v3_german_war_aims.bmp` and `walther_funk.bmp` with original,
  symbol-free reconstructions.
- Rebuilt the event gallery from the corrected outputs.
- Rebuilt two additional inherited unsafe images and one unrelated Italian
  composite under their original filenames, avoiding a global event-file
  override.
- Removed unrelated non-India model overrides from the managed overlay.
- Visually reviewed the distributed event-art, model-icon and personnel
  contact sheets. No swastika was identified in the current candidate.

The review is a human visual inspection, not an automated legal-symbol
classifier. Any public forum link should still be privately cleared with a
Darkest Hour moderator.

## Attribution

`docs/personnel_art_manifest.csv` records the source page, licence,
licence URL, creator, credit line, transformation notice and provenance for
each personnel portrait. The validator rejects a Creative Commons portrait
without complete creator and credit metadata.

## Outstanding Permission

The candidate depends on Blood and Iron v1.1 and distributes India-specific
derivatives of some foundation graphics and data. No written redistribution
permission from the Blood and Iron maintainer is recorded in this project.

Do not present V3.4.1 as cleared for forum publication until one of these is
complete:

1. Written permission is obtained and archived with its scope.
2. The package is redesigned so the remaining derivatives are generated from
   the user's installed foundation and the resulting distribution is approved.

The release must retain the full Blood and Iron contributor credits either
way.

## Testing Status

- Source validation: zero errors and zero warnings.
- Five deterministic strategic-route simulations reach 1940.
- Human playtesting reaches early 1937.
- The 1942-1964 content remains beta pending full-war, route and postwar
  playthroughs.

The candidate is suitable for continued private/open-beta testing after
permission review. It is not yet a stable release.
