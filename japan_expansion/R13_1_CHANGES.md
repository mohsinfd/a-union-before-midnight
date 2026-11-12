# Japan Rising R13.1 - enemy transports and portable source release

Eight existing ships are reassigned to transport groups at the same starting ports: five US screens and three British screens. Every ship ID, model, strength, equipment and port is preserved. Donor fleets retain at least their capital-screen requirement. No ships or resources are created. Allied fleets already under-screened are not stripped further.

Thirty existing Allied AI profiles transfer one to three production-allocation points from transports to destroyers, retaining the original total military allocation. The countries covered are the USA, Britain, Australia, New Zealand, Canada, France, Netherlands and Netherlands East Indies where an applicable profile exists. The pre-existing US 1942 invasion-caution changes remain. Japan's AI and global ship statistics are unchanged.

This improves initial transport protection and future screen availability. The naval AI can reorganise fleets: there is no supported minimum-screen-per-transport parameter in the shipped AI settings, and this release does not pretend to enforce one. Some initial groups still lack spare screens at their own ports. Guaranteed permanent escort composition remains an engine limitation; running behaviour was not tested.

All R13 specialist units, free first issues, upgrades and artwork remain. All 1,822 event IDs and 121 decision cards are unchanged. Garrison and national convoy support remain unchanged. R13.1 is intended for a new 1933 campaign; existing save fleet composition is not rewritten.

The public source release includes code, generated event specification, original generated illustrations, review evidence and a portable installer. It requires the user's own Darkest Hour and Blood and Iron v1.1 folders. It contains neither the game/foundation payload nor saved campaigns, crash dumps, credentials or temporary backups. Runtime paths accept JAPAN_RISING_GAME_ROOT/JAPAN_RISING_BASE_ROOT or a local_paths.json written by install_portable.py. Build artwork is retained under art/ and does not depend on the developer's image cache.
