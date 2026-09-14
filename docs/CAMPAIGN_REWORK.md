# Campaign Rework

> Historical note: this page records the Alpha 12 campaign-rework stage. Alpha
> 18 introduced the permanent War Cabinet, five wartime charters and 236
> country-specific campaign lifecycles; Alpha 20 retains that design, adds
> binding alliance commitments and Southeast Asian operational outcomes, and
> preserves Alpha 19's launch correction and packaging hardening. See
> [Gameplay Changes and Alpha 20 Status](../GAMEPLAY_CHANGES.md) and the
> [Wartime Campaign Map](WARTIME_CAMPAIGN_MAP.md) for the current contract.

## What Changed

This build converts India's world role from a one-time orientation into a
campaign system:

1. Choose or revise an orientation while at peace.
2. Set the level of commitment: observation, economic support, limited military
   ties or armed autonomy.
3. Receive a real response from London, Berlin, Moscow, Tokyo, Washington,
   China, Siam, Iraq or Persia when relevant.
4. Enter a coalition before or during the war, or remain outside it.
5. Select an operational war plan and react to changing world theatres.
6. Build contribution through sustained effort or decisive battlefield choices.
7. Spend the resulting leverage at the peace table.

## Balance Changes

- Starting money rises from 2500 to 3000.
- The annual Union Budget opens in 1934 and cannot issue unlimited debt.
- Five unavoidable procedural deductions were removed.
- The 1934 default opening now leaves about 1080 money and 1000 supplies before
  daily production and trade; the prior ledger left 375 money.
- Industrial Maturity grants at most 8 provincial IC instead of 24.
- Arabian Sea and Bay of Bengal commands receive cruiser-escort forces rather
  than free battleships.
- The oceanic fleet remains a major three-year investment but grants a smaller
  task group.
- The wartime arsenal refits the existing fleet instead of queuing another light
  carrier in 1942.

## Stability Changes

- India is excluded from the stock mobilization chain.
- Conflicting stock Indian elections and Gandhi minister events are slept.
- Cabinet repair events now respect the 1936 mandate and cannot undo a player
  choice.
- Malaya and Singapore are treated as external British territory.
- Every strategic path remains live through 1964.
- Construction guards are checked against cumulative engine caps.
- Foreign event targets, unit types, ministers, teams and delayed commands are
  validated before deployment.

## Historical Test Installation

The campaign-rework candidate was deployed under a separate mod-directory name.
The existing V4 installation was not overwritten, allowing old saves and the
new candidate to coexist. A fresh 1933 start was required because event history,
scenario resources, stock-event sleeps and strategy flags changed.
