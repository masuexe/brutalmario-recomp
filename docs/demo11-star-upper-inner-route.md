# Demo 1-1 upper-inner Cave Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World upper-inner node: map 6, X `$0178`, Y `$0188`;
translevel `$07`; room `$007`. It is the wiki **Cave Star**, the fourth Star
Road level. The wiki describes a Donkey Kong Country 2 roller-coaster track
with a Skull Cart racing Koopas, a normal exit at the end of the track, and
the secret branch as defeating every Koopa so the goal block turns off. The
[Star World BGM checkpoint](demo11-star-bgm.md) already plays the wiki-correct
Fear Factory slot `51`.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-upper-inner --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-upper-inner-{entry,goal,death}.script`. They use
map/player shortcuts and player-X waits as labelled fixtures. The goal
script also sets two one-frame phase counters before entry so both hosts enter
the coaster on the same frame phase; it does not write hit counters, boss
state, screen exits or the level-end state.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$14`, room `$007`, lives 4; the player X high byte at `$95` reaches 1 at 180 frames and 3 at 600 frames (coaster progress; the race-position counter address is not identified) |
| Course music | reference requests the restored Cave Star slot `51` |
| Coaster finish | mode `$0D`, room `$007`, goal timer `$13CE=1` |
| Normal clear | mode `$0E`, hub flag `$1EA9=$81` |
| Saved result | `SRAM[7]=$81` and the copy at `SRAM[$1B4]=$81` |
| File A reload | mode `$0E`, flag `$81` |
| Low Map16 guard | the level buffer `$C800..$FFFF` is byte-identical from layout through graphics to active |
| Death | real pit death returns to the hub in mode `$0E` at room `$007` with lives `4→3`; re-entry loads room `$007` with lives 3 |

## Host and line parity

The goal and death samples match exactly between the native and reference
hosts. The entry coaster has a one-frame host phase difference: at 180 frames the
samples are one pixel apart and the coin counter reads 180 or 181; at 600
frames the coaster height differs. The check therefore compares mode, room and
player X high byte for the entry samples, and every field for the goal and death
samples.

Fresh demoOnly1-line captures on the `star-world-upper-inner` target use the
same scripts and match every route sample on mode, room, X, Y, lives, flag,
coin counter and player X high byte. Only the pre-entry menu samples differ.

Captures: `d11-ui-<route>-{ref,native}` and `d11-ui-only1-<route>-ref`.
Report: `local/reports/demo11-star-upper-inner-route.json`. Suite log:
`local/reports/demo11-star-upper-inner-route-line.log`.

`tools/qualify_demo11_star_upper_inner_route.py` checks both hosts, the player
X-high progression, the coaster finish, the normal clear and SRAM copies, the
File A reload, the low-Map16 guard, death/re-entry, the head and build
identities and the demoOnly1 parity. The Demo 1-1 line suite passes **31/31**.
The whole-line byte audit is unchanged: 23 recipes, 105,090 changed bytes
inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled map/player shortcuts and player-X waits. The
  coaster ride, finish, save, reload and deaths are real guest actions.
- The **secret branch is not covered**. The Japanese wiki route needs every
  Koopa defeated so the goal block turns off. This checkpoint did not identify
  the race-position counter address or the secret goal. A probe that walks past
  the normal finish falls into a pit and returns by death, without a secret
  flag.
- The entry coaster position is host-phase sensitive; the check compares the
  semantic state, not the exact coaster pixel.
- An unassisted full traversal and listening acceptance are not claimed. The
  save flag and SRAM constants are recipient-local.

## Sources

- https://brutalmario.fandom.com/wiki/Cave_Star
- https://brutalmario.fandom.com/wiki/Music
- https://wikiwiki.jp/kitikumario/
- [Community walkthrough reference](walkthrough-reference.md)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-inner-goal.script --capture fresh-ui-goal-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-inner-goal.script --capture fresh-ui-goal-native
python3 tools/qualify_demo11_star_upper_inner_route.py
python3 tools/check_demo11_line.py
```
