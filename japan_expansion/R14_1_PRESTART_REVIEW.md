# R14.1 final pre-start review

The independent final review found one interrupted-transaction defect and two guide errors. No new gameplay content or balance changes are part of this correction. The game was not run.

- If China disappeared while a limited-peace reply was queued, its country-scoped receiver could never run and the Japanese pending flag remained. A Japanese-side daily check now clears the pending/accepted state, applies the normal 90-day waiting period and grants no peace or reward. It is appended after all 2,940 R14 events, preserving every released event ID.
- Corrected the current guide's large fuel-batch arithmetic: 45-day delivery plus 90-day recovery, about 88.9 oil/day over 135 days, using 177.8 energy, 11.85 supplies and 1.48 money daily on average. Balanced domestic works plus these batches provide about 131 oil/day under the existing efficiency assumptions; about 173 with the three developed southern fields.
- Corrected the specialist guide's current version label. Historical R13 counts remain labelled as historical.

## Pearl Harbor: manual versus automatic

The inherited manual decision requires the American embargo event to be at least 120 days old, the stated diplomatic eligibility, and at least six Japanese naval divisions/flotillas in Pearl Harbor Bay (province 2637). It does not require six separate fleets. The game checks the nonempty decision_trigger for manual readiness. The separate automatic trigger includes the Soviet-war restriction, additional Chinese/history conditions and its date/random checks. These are different branches; do not describe the automatic Soviet restriction as a universal manual block.

## Final player check

Use the Japan Rising JX1 Alpha2 shortcut and confirm R14.1 in the 1933 scenario/welcome. Make an opening manual save and test a reload before a long session. At the first paid-project completion check its concrete reward. At the first overseas air/naval deployment check the convoy carries both oil and supplies; extra convoy capacity does not prove the engine has assigned the route correctly.

Offline audit evidence is in R14_COLD_AUDIT.json, R14_INSTALL_RECEIPT.json and FINAL_INSTALL_REVIEW.json. Startup, actual UI rendering, automatic convoy allocation and long-campaign Hard balance remain player observations.
