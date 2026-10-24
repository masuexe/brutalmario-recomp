# Demo 1-1 lower-inner Valley Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World lower-inner node: map 6, X `$0178`, Y `$01C8`;
translevel `$3B`; room `$117`. It is the wiki **Valley Star**, the eighth Star
Road level. The wiki describes Super Mario 64 cap powers (Wing, Metal and
Vanish caps) with Kirby's Dream Course visuals, a normal exit at the goal
Question Sphere, and the secret as collecting all 100 coins to receive a
Power Star. The level has no Yoshi Coins. The
[Star World BGM checkpoint](demo11-star-bgm.md) already plays Iceberg Ocean
(slot `60`) with the cap cue (slot `79`); the cap music checks stay pinned by
`tools/qualify_demo11_lower_inner_music.py`.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-lower-inner --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-lower-inner-{route,goal,death}.script`. They use map,
player and camera shortcuts, Start pauses and damage immunity as labelled
fixtures. They do not write coin totals, actor state, life totals, the ending
flag, the goal timer, exit destinations or SRAM.

| Route | Reference and native result |
| --- | --- |
| Real-input traversal | room `$117`, mode `$14`, lives 4, coins 4; checkpoint `$08E5/$0110` |
| Former wall | later samples ride the warp-star chain and reach about `$0D21/$0100`; the old `$0522` stop no longer blocks |
| 100-coin start | before pickups: mode `$14`, room `$117`, coins 0, lives 4 |
| Coin progression | the real coin counter reaches 91, 98 and 99 on the late samples |
| Rollover and extra life | the 100th coin resets the counter to 0 and raises lives `4→5` |
| Ending | the real `$1493` timer becomes nonzero and `$141C=1` |
| Overworld return | mode `$0E`, translevel flag `$1EDD=$8F`, `$13CE=1`, lives 5 |
| Saved result | `SRAM[$3B]=$8F` and the copy at `SRAM[$1E8]=$8F` |
| Reset and File A reload | mode `$0E`, flag `$8F`; the saved state reloads (the file load resets the life count to 4, as documented) |
| Death | real pit death returns to the hub in mode `$0E` at room `$117` with lives `4→3`; re-entry loads room `$117` with lives 3 |

The restored custom slots are exercised here: slot `$30` (caps and the
100-coin controller) and slot `$37` (warp-star movement). Both include room
`$117` in the pinned dependency sets.

## Host and line parity

The native build matches the reference capture on all goal and death samples
exactly. The real-input traversal has small position phase differences (at
most 3 pixels in X and 2 in Y), which the check tolerates.

Fresh demoOnly1-line captures on the `star-world-lower-inner` target use the
same scripts and match every route sample on mode, room, X, Y, lives, coins,
hub flag, ending flag, goal timer and save state. Only the pre-entry menu
samples differ, and those are not part of the route.

Captures: `d11-li-<route>-{ref,native}` and `d11-li-only1-<route>-ref`.
Report: `local/reports/demo11-star-lower-inner-route.json`. Suite log:
`local/reports/demo11-star-lower-inner-route-line.log`.

`tools/qualify_demo11_star_lower_inner_route.py` checks both hosts, the real
traversal past the former wall, the coin rollover and extra life, the ending
and overworld return, the SRAM flag copies, the reload, death/re-entry, the
head and build identities and the demoOnly1 parity. The Demo 1-1 line suite
passes **30/30**. The whole-line byte audit is unchanged: 23 recipes, 105,090
changed bytes inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled map/player/camera shortcuts, Start pauses and
  damage immunity. The coin pickups, rollover, extra life, ending, save, key
  exit and deaths are real guest actions.
- An unassisted 100-coin route is not claimed. The five Dragon Coin placements
  are also outside this checkpoint; the level has no Yoshi Coins in the wiki,
  but no Dragon Coin coverage is asserted.
- The save flag and SRAM constants are recipient-local. The demoOnly1 line
  matches them on these scripts.
- The cap music checks remain pinned by the separate lower-inner music
  qualifier.

## Sources

- https://brutalmario.fandom.com/wiki/Valley_Star
- https://brutalmario.fandom.com/wiki/Music
- https://wikiwiki.jp/kitikumario/
- [Community walkthrough reference](walkthrough-reference.md)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-lower-inner-goal.script --capture fresh-li-goal-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-lower-inner-goal.script --capture fresh-li-goal-native
python3 tools/qualify_demo11_star_lower_inner_route.py
python3 tools/check_demo11_line.py
```
