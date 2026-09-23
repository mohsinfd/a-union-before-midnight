# A Union Before Midnight 4.2.0-alpha.3

This playtest update repairs event-funded force construction and the 1934 army
rebuild. It can be used for a new campaign, and a repaired copy of the current
Alpha 2 autosave is supplied for the existing playthrough.

## Meaningful procurement rewards

- Event production always uses the current researched model and its normal
  daily IC cost.
- Every production authorization now funds progress on the first item instead
  of creating a full-cost line at zero percent.
- Only the first item receives inherited progress. Additional serial items
  start normally, so extending the line cannot multiply the event benefit.
- Fixed low-IC event costs remain prohibited.

## 1934 army rebuild

- The citizen, professional and mobile programmes now create named current-
  model cadres directly at 35 to 60 percent strength.
- Upfront manpower reflects cadre strength rather than a full-strength serial
  production line.
- Reinforcing those cadres to field strength remains a normal player expense.

## Manpower accounting

- Gurkha, standing-army, airborne, reconnaissance, wartime and jet-age direct
  grants now deduct their stated reduced-strength manpower.
- Obsolete full-strength manpower gates were reduced or removed where a
  mobilization grant itself supplies the recruits.
- Validation rejects any future Indian direct formation grant without an
  explicit cadre-manpower charge.

## Existing-save repair

- `Repair-V42-MobileCadreSave.ps1` removes the obsolete cavalry and infantry
  queue lines, refunds their reserved manpower and arms a one-time current-
  model cadre event.
- The original autosave remains untouched.

## Validation

- Event orders are rejected if they fix player IC cost or begin at zero
  progress.
- The game is not launched by the build, repair or deployment process.
