# Sky Star: accepted middle-right restoration stage

Date: 2026-10-20. The user reports that the Sky Star playtest found no
problems, sound is available again, and the heard audio is normal. This
accepts the current stage and makes `star-world-middle-right` the cumulative
baseline for subsequent restoration. The report does not itemize a secret
clear or all five Dragon Coins; those remain unqualified.

```sh
python3 tools/play_demo_only1.py --restoration star-world-middle-right --show-location
```

The launcher selects map 6 / `$0198,$01A8`, translevel `$09`, room `$009`
in an isolated fresh uncleared save. `--complete-all` is rejected because
completion can turn the course into a Warp Star. Existing saves and the two
original targets remain separate.

## Restored dependencies and identity

The [pinned recipe](../config/restorations/star-world-middle-right.json)
builds on the accepted upper-right restoration. It imports missing ExGFX
`$190/$193` under unused IDs `$FFA/$FF9` for both `$009` and its destination
`$09B`, restores the actual `$2E` intro/loop song, and supplies missing
custom sprites `$17` (fuel refill) and `$28` (rocket/boss barrel).
Recipient layout, sprite placements, exits, progress rules and shared runtime
remain unchanged. The temporary diagnostic `$5D` music substitution is absent.

The donor's `$29:E008` group contains four songs; `$2E` uses its third
eight-byte sequence header and track data `$7682..$7A17` (exclusive end).
The adapted single-song upload is 989 bytes, with a 981-byte song, distinct
intro/loop patterns and 35 relocated pointers. Graphics and code allocations,
source hashes, shared helpers, version-specific constructor/damage routines
and dependent room sets are pinned. Enabling shared sprite slots does not
accept every other room referencing them.

ROM SHA-256:
`b565937be20d4342602b895a36447382a6f3eeda8979c519210749332cecc284`.
Regular executable SHA-256:
`fdc4ea508ce150c52f4587d2ac107e444167e7cb8ec54bc6851277687a2ce8b5`.
The ROM, scaffold identity and build receipt have been checked together.
Do not use the earlier scaffold/build archived with the `stale-547f67fc` suffix.

## Existing automated evidence

| Tracked script | Result on reference and matching native build |
| --- | --- |
| `star-world-middle-right-goal.script` | Real directional input rides the rocket around the left-page obstacles. Finish occurs at Mario `$005A,$02B0`; walking enters the real screen-2 door, leading to `$09B`. A jump crosses the colored blocks and the goal tape returns to the hub. |
| `star-world-middle-right-death.script` | Waiting out the actual 300-second guest timer loses one life, returns to the hub and permits a fresh entry with rocket fuel `$0B`. |

The normal-clear flag changes from `$0C` to `$8C` in WRAM and both SRAM
copies, then survives console reset and File A load. The death route drops
extra lives from four to three and retains three on re-entry. Neither script
writes goal, fuel, coin, life or SRAM state. Their only map shortcut selects
the course before ordinary entry. Current captures are
`middle-right-goal-script`, `middle-right-goal-native`,
`middle-right-death-script` and `middle-right-death-native` under ignored
`local/captures/`. The unchanged code checkpoint's full suite passed 110
tests; recording this acceptance does not claim a newly rerun suite.

## Coverage limits retained for later investigation

The [investigation log](star-world-middle-right-investigation.md) preserves
the measured route limitations. A bottom refill followed by the measured
clean climb ends at Mario Y `$0477`, short of the secret finish condition
below `$0470`; the secret exit is not qualified. The two upper Dragon Coins lie
on opposite sides of a wall and the examined single-climb routes cannot
collect both. Five-coin completion and its saved bit are not qualified here.
These findings are not a reason to alter original fuel, terrain or exit rules
without a donor comparison establishing a restoration defect.

The user has authorized continuous automatic restoration/qualification and
commit/push. Do not require another whole-course playtest for routine progress.
Ask for a targeted human check only when essential behavior cannot be decided
from automatic evidence. Sound is available now; the current Sky Star report
does not retrospectively accept every earlier queued track.

## Local handoffs versus public documentation

Session handoffs under `.agents/*-handoff.md` contain transient local state,
capture paths and stop/resume instructions. They are ignored. Durable
recipes, tracked input routes, verified outcomes and coverage limits belong
in `docs/` and are committed. A handoff does not override newer user reports.
Future `.agents/` instructions or tools are not blanket-ignored.
