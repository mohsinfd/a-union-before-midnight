# CLEANUP1-T1: wartime navigation tooltip crash

## Evidence

The September 8 crash happened after loading the February 1, 1942 save. History ends on February 2 at 11:00. `savedebug.txt` reports successful scenario validation, not a parser failure.

Windows Event 1000 records exception `0xc0000005` at executable offset `0x2cb67`. The matching dump is `Darkest Hour.exe.22972.dmp`. At instruction `0x42cb67`, the engine dereferences its game pointer loaded from `0xd0ca90`. That pointer contains `0x69272067`, text bytes rather than a valid object pointer. The same memory region contains a contiguous 130,222-byte rendered condition string beginning at `0xcf3904`. It includes the mod's liberation, route, war and puppet conditions. The corrupted pointer lies 102,796 bytes into that text.

The compiled Peace Talks decision contained 298,943 characters of combined child conditions. Top-level page-link action predicates reached 225,887 characters. This is strong evidence of a tooltip buffer overrun caused by the new navigation aggregation, not evidence of damaged campaign state. The exact engine buffer capacity is not established.

## Focused correction

- All four wartime root decisions use only their short common human/war/build eligibility checks.
- Pure links from roots to topic pages use only the human-player check, not every descendant's combined conditions.
- Actual entries, campaign options, settlement checks, commands, rewards, timers and balance remain unchanged.
- Topic pages can be empty except for Cancel and Back. This is the deliberate small usability tradeoff.
- A regression test limits root decision predicates to under 512 characters and root-to-topic link predicates to under 64 characters.

This correction addresses the demonstrated top-level aggregation problem. It is not a claim that every existing large individual event has been engine-tested or that all possible crashes are eliminated.

## Continue

Restart normally, confirm the loading/menu badge says `27-CLEANUP1-T1`, and load the same `CLEANUP1_India_1942-02-01.eug`. No save edits or new campaign are required for this script correction. The base one-time event notice still says CLEANUP1. The hotfix identity is recorded separately in the installation receipt.

Installation uses the existing backed-up installer without save migration. No game launch is performed. Runtime confirmation still requires the next playtest, including hovering over the four root decisions and opening their topic pages.
