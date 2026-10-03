# A Union Before Midnight 4.2.0-alpha.12

## May 1938 Playthrough Audit

- Confirmed that the tested campaign followed armed non-alignment with a
  commercial Japanese channel, not the sovereign Delhi-Tokyo partnership.
- Strategic orientation may now be reviewed annually from 1937 rather than
  remaining locked until 1940. The first menu explicitly identifies the second
  menu containing Germany, Japan and independent Asia.
- Tokyo's 1935 choices now state whether they unlock a future strategic compact.

## Naval Construction

- The National Dockyard Act now grants bounded, exact-hull construction-time
  improvements: 10 percent of model-zero time for capital ships, 15 percent for
  cruisers, and 20 percent for destroyers, submarines and transports.
- Costs remain normal. Battleships and carriers still require years, while the
  yards now provide a visible benefit. Existing contracts may preserve their
  original completion date; newly placed orders receive the standard.

## Event Isolation

- Replaced India's shared generic-election `sleepevent` workaround with a proper
  exclusion from `Election_day.txt` TAG lists.
- New campaigns no longer generate the repeated slept-election messages seen in
  the May 1938 log. Existing autosaves are not rewritten and may retain harmless
  serialized noise.

## Campaign Health

- The audited May 1938 save has 192 owned IC, 423 manpower, current-year research,
  no province ownership errors, no construction-cap overflow and no active crash
  signature.
- The Bay of Bengal Fleet is available but unfunded in that save; its chain is
  not blocked.

## Compatibility

The strategic review and dockyard-standard event can run from the current save.
No autosave modification is required. A new campaign is required only to remove
the already-serialized generic-election log noise completely.
