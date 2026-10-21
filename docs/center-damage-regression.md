# Center candidate: powered Mario damage regression

The user reported that powered Mario died instead of shrinking when launched
with `--restoration star-world-center`. The affected ROM was
`11ceb7737b5eba5322b1612702210c4af7dc9714ccb80babe12853a1f8123106`.

The recipe had changed `$00:F604` from `BRA +$17` to `BRA +$00`, describing
it as a star-launch repair. That interpretation was wrong. This branch
belongs to the normal damage routine: after setting action `$71=1` and
clearing Mario's power byte, it skips the death entry at `$00:F606`.
Removing the skip let the same hit set `$71=9` and start death instead.
The associated `$00:F61B` death-timer edit was unrelated to cannon travel.
Both edits have been removed; no runtime physics change is needed for
this regression.

The corrected ROM is
`6db0bb2e6f905a04c03c4ed4b9ebd9674b4a9b5aef7ede533c8f8fc644296d92`.
Other restoration targets did not inherit these two center-only edits.

`recomp/inputs/star-world-center-hurt.script` selects the existing lower-left
course on this ROM and gives Mario one initial mushroom-power fixture. Real
directional input then produces contact with a live Koopa. The script does
not write enemy, collision, hurt, invulnerability, life or goal state.

| Observation | Before, both hosts | Corrected, both hosts |
| --- | --- | --- |
| Before contact | Power 1, action 0, lives-minus-one 4 | Same |
| First sampled hurt | Power 0, action 9 | Power 0, action 1 |
| After shrink interval | Death action continues | Power 0, action 0, temporary immunity active |
| Lives at final sample | 4, death still running | 4, active gameplay |

Ignored capture directories are `center-hurt-before-reference2`,
`center-hurt-before-native`, `center-hurt-fixed-reference` and
`center-hurt-fixed-native`. Corrected entry and pit/death/re-entry captures
are `center-hurt-fix-entry-{reference,native}` and
`center-hurt-fix-death-{reference,native}`. These are bounded regression
checks, not acceptance of a complete center-course clear.

The user also reported insufficient cannon travel across the pit near the
second dragon coin, compared with cheap_demo. That is a separate open
issue. Do not reinterpret the damage branch as a launch control or claim
that this rollback fixes cannon travel. The center boss clear also remains
unqualified.

Restart the practice command to load the corrected ROM and executable:

```sh
python3 tools/play_demo_only1.py --restoration star-world-center --show-location
```
