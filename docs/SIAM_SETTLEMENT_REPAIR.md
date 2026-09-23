# Siam settlement repair

India may force Siam out of Japan's camp and establish an Indian puppet after
holding Bangkok (1423) and Chiang Mai (1425) for 21 consecutive days. Both cities
must still belong to Siam. India must be fighting both Siam and Japan, and Siam
must be Japan's puppet or ally. Sovereign, Allied, German and Soviet Indian
routes qualify; membership of Japan's alliance does not. No LIBERATOR opt-in is
needed. This applies to new campaigns and saves that already load module 43.

The outcome preserves Siam's territory and armed forces. It is deliberately a
substantial reward for winning the Siam campaign, without an extra permanent
Indian economic modifier. India can cancel the offer and keep fighting.

## Sequence

1. `9297000` starts the hold; `9297001` resets it after a lost requirement.
2. `9297002` records readiness after 21 days; `9297003` offers the terms.
3. `9297004`, issued by **Siam**, ends puppet status and uses
   `leave_alliance when = 1`. Local DH documentation specifies that this leaves
   the old alliance and its inherited wars through white separate peace.
4. One day later, `9297005` checks that Siam has no master, alliance or war, that
   the two cities are Siam-owned and held by Siam or India, and that India is
   **still at war with Japan**. Only then does India make Siam its puppet.
5. `9297006` grants access from Siam. `9297007` confirms the actual Indian puppet
   relationship and continuing India-Japan war before recording completion.
6. Invalid replies close without forcing peace, declaring another war, changing
   a government or paying a reward. `9297008` cleans up if Siam disappears.

No event in this chain contains an Indian peace command. No script automatically
redeclares war to hide a failed withdrawal. A failed engine transition is left
visible and blocks the subsequent step.

The final cleanup build must block the old generic Siam negotiations while Siam
belongs to Japan or this sequence is pending. This includes already queued
callbacks and ratification. The new decision belongs under Peace Talks rather
than adding a permanent left-panel decision. Per-country pending and retry flags
are cleared when this offer is sent and when protection is confirmed.

## Verification and limits

`python -m unittest discover -s tools -p test_aubm_siam_settlement.py` checks gates,
the 21-day hold and reset, all four routes, parallel Soviet war eligibility,
stale replies, third-country alliance membership, failed Japanese-war checks,
completion idempotency, and command country/order. The tests supply expected
foreign-government states explicitly; they do not emulate Darkest Hour.

An isolated engine test must still check the actual coalition war list after
Siam leaves, after puppet creation, and after reloading a save. Test against the
user's six-member Japanese coalition and with an independent India-Soviet war.
India-Japan and India-Soviet must remain active; Siam-Japan puppet/alliance links
must be absent; Siam-India puppet status and Indian access must exist. Also test
loss of either city during the delay, a third party changing Siam's alignment,
and a stock Japanese surrender during the sequence. Until these checks pass,
this is a verified script design, not an engine-playtested peace fix.
