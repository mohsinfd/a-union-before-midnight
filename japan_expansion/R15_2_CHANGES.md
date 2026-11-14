# Japan Rising R15.2 — purchase delivery repair

The April 1936 save confirms that the carrier-aircrew school and maritime
navigation trials took payment but never delivered. R15.1 rendered their
callback IDs as quoted strings. Its Python parser discarded that distinction,
so simulated delivery and AST comparisons failed to catch the native-format
problem. R15.2 resolves the entire quoted symbolic token into a bare integer.
The compiler now rejects quoted, unresolved, zero or out-of-range event targets
before parsing. This applies centrally to all generated event/trigger commands.

Paid US imports keep their prices, quantities, daily payments and original
durations, but use the native protected-trade setting. Ordinary AI cancellation
can no longer silently remove them. A single automatic notice ends US-Japan
trade on war or embargo. No permanent oil income or automatic renewal is added.

The repaired campaign is `JAPAN_R15_2_PURCHASES_RESTORED_1936_APR_1.eug`.
The autosave is updated to identical contents, and its original is backed up.

- After the first game hour: the carrier-aircrew school grants CAG/light CAG
  +8 morale and +5 maximum organisation; maritime trials grant Naval Bombers
  +300 km range and +2 surface detection, including their existing specialist
  mirrors. The original receipts apply these effects to current/future forces.
- The additional 24-oil contract expires on 3 August 1937, 08:00. The mixed
  24-oil/12-metal contract expires on 18 November 1936, 22:00. Each retains its
  payment of 4 supplies and 1 money daily. No setup fee is charged again, no
  extra full term is added, and no speculative stockpile backpay is granted.
- Starting and delivered shipping remains 800 transports and 165 escorts.
  The separate +60-transports project retains its 5 April, 09:00 delivery.
- All country/unit/production/resource state and provinces are preserved.
  Only owed receipt flags/callbacks, absent contracts, their protection markers,
  the global ID allocator, save label and module registry change.

Cold checks cover raw integer rendering, all generated native dispatches,
finite protected contracts, war/embargo closure, expiry, migration idempotence,
already-delivered rewards, existing matching contracts, expired agreements and
the prewar/regional/recovery/strategy/enemy/peace/postwar regressions. Original
event IDs, bills, reward quantities and programme durations are reconciled with
R15.1. Installed text and the Steam launcher target are checked. The game is
not launched; this is not a claim of completed engine playtesting.
