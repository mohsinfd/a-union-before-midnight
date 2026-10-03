# Contributing

Bug reports, balance observations, historical corrections and save-compatible
improvements are welcome.

## Before Reporting A Crash

Please include:

- Darkest Hour version and the A Union Before Midnight version/build marker;
- campaign date and selected strategic path;
- whether the crash repeats from the same save;
- the last 100 lines of `savedebug.txt`;
- the relevant autosave when redistribution is legally and practically
  possible;
- any manual edits or other overlays.

For deterministic crashes, note the exact date and whether the game crashes at
00:00, when an event window appears, when opening production or when viewing a
unit tooltip. Those distinctions matter in the Darkest Hour engine.

## Contributions

Keep changes within the A Union Before Midnight namespace whenever possible:

- legacy event IDs: `9270000-9279999`;
- V4 event IDs: the documented `9280000-9289999` allocation;
- flags: `ind_v3_*`, `ind_v4*` or `ind_aubm_*`, following the owning module;
- active V4 event modules: `db/events/aubm_v4`.

Province construction must use the Darkest Hour Full Map_1 province ID, valid
ownership and an appropriate province role. Infrastructure and base commands
must retain their maximum-size guards.

Do not submit copyrighted material without a clear provenance and permission
record.

