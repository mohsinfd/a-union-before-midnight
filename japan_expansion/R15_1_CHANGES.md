# Japan Rising R15.1 — completion timing repair

The R15 February 1934 autosave confirms a genuine failure: Nagoya's paid
workshops displayed a completion notice on 15 January but left the programme
pending and added no factories. The persistent funding event was missing from
both `history` and `save_date`, so the receipt selected its empty action.
The earlier offline simulator incorrectly recorded every persistent event.

The common fix uses the engine's saved delayed-event queue and finite global
maturity flags. A receipt sets its due flag before evaluating the original
reward/refund actions. Automatically polled later offers use queued elapsed
flags. Timers for Japanese investments survive a recipient's disappearance so
the existing Japanese refund watcher can still run. There are no new player
decisions, prices, rewards, diplomatic terms or original event IDs.

The separate repaired save is `JAPAN_R15_1_NAGOYA_REPAIRED_1934_FEB_1.eug`.
Nagoya changes from five to eight fully working factories. The project closes
without charging again. The new module is registered in that saved campaign.
The original autosave is preserved; all other gameplay bytes are unchanged.

Eight focused offline suites cover the reproduced failure, every prewar
alternative, regional deliveries/refunds, recovery, strategic commitments,
enemy responses and peace/postwar chains. The final audit reconciles every
original bill, reward, choice and non-timing condition against R15 and checks
the installed native scripts. No game was launched. This is source and saved
state verification, not an engine-tested claim or a long-campaign guarantee.
