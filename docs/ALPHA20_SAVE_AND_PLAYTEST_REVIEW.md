# Alpha 20 Save and Playtest Review

Updated: 28 August 2026.

## Which Campaign Is Newest?

The installed save directory contains a newer game than the two developed
manual campaigns, but it is only an opening autosave:

| Save | Filesystem timestamp | In-game date | Assessment |
| --- | --- | --- | --- |
| `autosave.eug` | 25 August 2026 | 1 May 1933 | Newest game started; opening smoke/short start only |
| `oldautosave.eug` | 25 August 2026 | 1 April 1933 | Previous file in the same rotating opening autosave pair |
| `AltIndia_1941_December_2.eug` | 23 August 2026 | 2 December 1941 | Newest developed manual campaign; primary Alpha 20 review save |
| `inda firstIndia_1942_April_3.eug` | 20 August 2026 | 3 April 1942 | Older developed campaign despite its later in-game date |

Therefore, yes: another game was started after the manual campaigns. It did
not progress far enough to supersede the December 1941 save for gameplay
analysis. An exhaustive search of the Darkest Hour save directories found no
manually named AUBM V4.2 save newer than the 23 August file; the two 25 August
files are the rotating April/May 1933 opening autosave pair.

## What the December 1941 Save Actually Records

`AltIndia_1941_December_2.eug` contains the global Sino-Japanese, European,
German-Soviet, Japanese-American and Japanese-Allied wars. India is not listed
on either side of any live war.

The save records:

- `ind_aubm_jp_partnership = 1`;
- no formal Indian membership in the Allied, Axis, Comintern or Japanese
  coalition;
- no saved German or Soviet binding compact;
- no surviving War Cabinet declaration selector;
- Japanese entry into wars against the United States and the Allied bloc,
  without India inheriting those wars under its separate-command compact.

This means the user's recollection of initiating a war is not preserved as a
live Indian war in the opening autosave pair or either developed manual save.
It may have occurred in an unsaved session, or the pre-Alpha-20 delayed
declaration path may not have completed before the manual save. The
authoritative saved participant lists do not show India at war.

The save does preserve the reported alignment defect. India has a binding
Delhi-Tokyo partnership, yet the old Berlin entry family was not excluded by
that compact. A one-click Japan-to-Germany transfer was therefore possible even
though this particular file was saved before such a transfer completed.

## Additional Save-State Defect

The same campaign has both union-legitimacy and state-capacity gains, but has
neither the provincial-bargain nor coercion result and never recorded the 1934
review. The previous truth table accepted neither this mixed state nor a clean
recovery route, which could stall the later integration sequence.

Alpha 20 sends that state to the unfinished 1934 review. A dedicated validator
now checks every combination of the four relevant integration flags.

## Alpha 20 Event Response

### Binding alignment

- Allied, German, Soviet and Japanese binding commitments are mutually
  exclusive.
- A compact may still upgrade to the formal coalition of its own family.
- Delayed foreign replies must revalidate the selected commitment and the
  shared negotiation lock before changing India's status.
- India may withdraw to sovereign command only at peace, followed by a 90-day
  realignment cooldown.
- Old saves are canonicalized from live alliance and compact state. The
  migration precedence is Allied, German, Soviet, then Japanese; contradictory
  losing route and compact flags are cleared.
- War menus and delayed declarations exclude current coalition partners.

### Southeast Asian settlements

- Indian control of Batavia can open a local U05 settlement without every
  Southern Theatre province.
- Dutch-owned Batavia uses a separate colonial-Netherlands path; Amsterdam is
  a different Netherlands campaign.
- Indian control of Singapore and Kuala Lumpur can open a British Malaya-only
  settlement without requiring Borneo.
- A cession can transfer only provinces legally owned by the responding
  government. East Indies terms include western New Guinea provinces 1594-1601
  only when U05 or the Netherlands owns them.
- Local responses, refusals, retries and ratification use serialized dockets so
  one government's callback cannot clear or complete another government's
  file.

### Southeast Asian operational achievements

- Hanoi plus Saigon and Manila plus Davao are achievement-only land operations
  with reversible current standing and permanent earned credit. They
  deliberately do not add a second peace docket; the existing country campaign
  remains authoritative.
- Bay of Bengal, Malacca, Java Sea and South China Sea achievements require the
  named operating ports and 8, 12, 16 and 18 surface ships respectively.
- Losing an objective suspends current standing. Recovery restores it without
  paying the one-time reward again.
- A flexible theatre award accepts a combination of three land/sea results, so
  India need not occupy every Southeast Asian victory province.

## Recommended New Playthrough

1. Start a fresh 1933 campaign; do not use the opening May autosave as a full
   Alpha 20 test.
2. Save before the 1934 integration review and confirm the mixed legitimacy and
   capacity state can continue.
3. Take the Delhi-Tokyo compact. Confirm rival binding offers disappear while
   the Japanese formal upgrade remains available.
4. Declare one separate Indian war and verify India appears in that save's live
   war participant list.
5. Take Batavia before the full East Indies objective set and test one actual
   foreign response without reloading.
6. In a British war, take Singapore and Kuala Lumpur without Borneo and verify
   the Malaya-only docket.
7. Keep another war active while ratifying the local settlement; only the named
   bilateral war should end.
8. Lose and recover one required port before a delayed answer and again after
   an achievement. The first file should lapse safely; the earned reward should
   never duplicate.
9. Test one Hanoi-Saigon or Manila-Davao milestone and one fleet-backed sea
   lane, then verify the combined Southeast Asian award.
10. After all Indian wars end, withdraw to sovereign command. Rival alignment
    options must remain closed until the 90-day cooldown expires.
