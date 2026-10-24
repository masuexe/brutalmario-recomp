# Demo 1-1 middle-right Sky Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World middle-right node: map 6, X `$0198`, Y `$01A8`;
translevel `$09`; room `$009`. It is the wiki **Sky Star**, the vertical
rocket climb. The [Star World BGM checkpoint](demo11-star-bgm.md) plays the
wiki-correct Grape Garden slot `58`. The user verified the secret ascent in
play; that route stays in [the sky secret report](demo11-sky-secret.md) and is
not retried here.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-middle-right --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-middle-right-{entry,goal,death}.script`. They use a
map shortcut and scripted rides as labelled fixtures. They do not write fuel,
completion, doors, exits or SRAM.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$14`, room `$009`, spawn `$0070/$0CBF`, lives 4, rocket fuel load `$1594=$0B` |
| Low Map16 guard | buffer `$C800..$FFFF` is byte-identical from layout to graphics |
| Ordinary controls | standing and walk samples stay in room `$009`; walking changes X |
| Rocket fuel load | the jump sample consumes one fuel unit and reaches `$1594=$0A` |
| Course music | reference requests the restored Sky Star slot `58` |
| Rocket finish | mode `$14`, room `$009`, coins 4, fuel 0, finish point at `$005A/$02B0` |
| Goal room | the top door and blocks land in room `$09B` |
| Normal clear | mode `$0E`, hub flag `$1EAB=$8C`, goal timer `$13CE=1` |
| Saved result | `SRAM[9]=$8C` and the copy at `SRAM[$1B6]=$8C` |
| File A reload | mode `$0E`, flag `$8C` |
| Death | real fall returns to the hub in mode `$0E` at room `$009` with lives `4→3`; re-entry loads room `$009` with lives 3 and the full fuel load |

## Host and line parity

The native build matches the reference capture on every route state field:
mode, room, X, Y, lives, hub flag, coins, rocket fuel and goal timer.

Fresh demoOnly1-line captures on the `star-world-middle-right` target use the
same scripts and match every route sample on the same fields. Only the
pre-entry menu samples differ, and those are not part of the route.

Captures: `d11-mr-<route>-{ref,native}` and `d11-mr-only1-<route>-ref`.
Report: `local/reports/demo11-star-middle-right-route.json`. Suite log:
`local/reports/demo11-star-middle-right-route-line.log`.

`tools/qualify_demo11_star_middle_right_route.py` checks both hosts, the
low-Map16 guard, the fuel load, the music request, the rocket finish and goal
room, the normal clear and SRAM copies, the reload, death/re-entry, the head
and build identities and the demoOnly1 parity. The Demo 1-1 line suite passes
**32/32**. The whole-line byte audit is unchanged: 23 recipes, 105,090 changed
bytes inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use a labelled map shortcut and scripted rides. The rocket ride,
  finish, top door, save, reload and death are real guest actions.
- The normal exit is qualified. The secret exit is user-verified and deferred;
  this checkpoint does not retry the ascent search.
- An unassisted full traversal and listening acceptance are not claimed.
- The save flag and SRAM constants are recipient-local. The demoOnly1 line
  matches them on these scripts.

## Sources

- https://brutalmario.fandom.com/wiki/Sky_Star
- https://brutalmario.fandom.com/wiki/Music
- https://wikiwiki.jp/kitikumario/
- [Community walkthrough reference](walkthrough-reference.md)
- [Sky secret investigation](demo11-sky-secret.md)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-middle-right-goal.script --capture fresh-mr-goal-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-middle-right-goal.script --capture fresh-mr-goal-native
python3 tools/qualify_demo11_star_middle_right_route.py
python3 tools/check_demo11_line.py
```
