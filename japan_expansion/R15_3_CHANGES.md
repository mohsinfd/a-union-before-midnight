# R15.3 — specialist tooltip crash repair

The 18 November crash dump implicates the Mixed Brigade information tooltip.
Its description has 220 bytes; the displayed model label has 49. Together with
the separator they form a 270-byte string. Bytes 256–259 are `20 28 4D 69`:
the little-endian address `0x694d2820`, exactly the invalid instruction address
recorded by Windows. The same brigade label and description tail are on the
faulting stack. This is strong evidence of a 256-byte tooltip buffer overrun.

All new specialist descriptions are now short. The generator rejects a custom
unit description over 140 bytes, and the audit checks each description plus
model label and terminator against a conservative 224-byte limit. Names,
artwork, unit stats, research, upgrades, prices and rewards are unchanged.

Literal percentage signs in owned narrative localisation are written as the
word "percent". Stock formatted strings are left alone. This removes the
custom text's invalid-format pattern reported by the engine.

No campaign save is edited. All native event scripts and unit data files are
hashed against R15.2. Existing pending projects keep their original rules.
In the September 1938 autosave the Wuhan programme was funded before China's
July settlement; its later notice is that old programme becoming due. This
text repair does not alter its postwar delivery/refund rules.

Continue the normal latest autosave (1 September 1938). No new campaign and no
older repaired-save rollback is required for this text-only change.

The crash signature is reproduced and the new bounds checked offline. The game
is not launched; this does not assert that every possible crash is eliminated.
