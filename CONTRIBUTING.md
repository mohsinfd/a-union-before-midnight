# Contributing

Bug reports, balance observations, historical corrections and save-compatible
improvements are welcome.

## Before Reporting A Crash

Please include:

- Darkest Hour version and Blood and Iron version;
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

- event IDs: `9270000-9279999`;
- flags: `ind_v3_*` or a documented successor namespace;
- India event modules: `db/events/india_v3`.

Province construction must use the Blood and Iron Map_1 province ID, valid
ownership and an appropriate province role. Infrastructure and base commands
must retain their maximum-size guards.

Do not submit copyrighted material without a clear provenance and permission
record.

