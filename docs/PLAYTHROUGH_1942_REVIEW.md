# April 1942 Campaign Review

## Campaign State

The latest autosave is healthy and reached 1 April 1942 without a new crash
dump or a meaningful engine error in `savedebug.txt`. India is at peace and is
not a member of a major alliance. Its active path flags identify it as
non-aligned; Allied, Axis, Soviet and Japanese orientation flags are all clear.

India has 211 base IC, a 1.48 national IC modifier, 114 land divisions, 56 air
divisions and 39 ships. Money is 446, supplies are 16,261 and manpower is 939.
Energy, metal, rare materials and oil are abundant. The economy is therefore
militarily overpowered but still cash-constrained.

## Findings

1. Event pacing collapses after 1939. Japan and Siam are still fighting China,
   but Japan never attacked Britain, the Netherlands or the United States, so
   Pearl Harbor-dependent events never became eligible.
2. The player was effectively locked into non-alignment without a clear,
   repeatable strategic review. Picking sympathetic answers in world events did
   not constitute an explicit coalition choice.
3. Starting naval and aviation prerequisites were too weak. Current projects
   are mostly appropriate 1940-42 technologies, but historical research shows
   Carrier Integration completed only in 1937 and the 1918 Naval Bomber only in
   March 1942.
4. The 1942 carrier rewards were obsolete on arrival. The player already had
   two fleet carriers and two light carriers, while scheduled events were about
   to add still more free hulls.
5. The decisive balance issue is cumulative national-IC bonuses plus free and
   discounted formations. Province IC itself is not the main source.
6. Infrastructure, naval-base and air-base caps are currently respected. Port
   Blair and Kavaratti are suitable blue-water nodes and now have staged,
   capped development content.

## Implemented Response

- Add condition-driven world-war reactions through 1943, including China,
  Burma, Thailand, Malaya, the European war and Japan's southern strategy.
- Add a repeatable Strategic Council from 1940 so a peaceful India can choose
  or revise its grand strategy once per year.
- Add an annual Union Budget from 1935 with debt service and repayment.
- Add a save-compatible inherited-service archive to repair old naval and air
  prerequisites without restarting.
- Convert the late carrier giveaways into readiness, doctrine and escort
  programmes, and reduce the 1941 escort construction queues.
- Normalize the cumulative total-IC modifier once the mature economy exceeds
  200 base IC.
- Enforce complete action visibility for every resource-priced decision during
  every build.

The existing save is deliberately not edited. New events are triggered by
country state and missing compatibility flags, so they can enter naturally
after the save is resumed.
