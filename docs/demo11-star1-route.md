# Demo 1-1 lower-left Star World course route acceptance

Date: 2026-10-24. Starting the systematic Star World route acceptance after the
exact-node music dispatch checkpoint. The lower-left course (map 6, X `$0128`,
Y `$01E8`; translevel `$05`, room `$005`) now carries the same bounded route
evidence that the demoOnly1 line accepted.

This is a qualification checkpoint. No ROM changed. The head remains
`demo11-node-music` (ROM
`77a4b7a970125db9c6b53d0619f6f9441c47538bd938bce6a8ee7c862de7240a`,
native binary
`6d31a9ede8ffc5591d525d8c5178b3b3ac0b60262adb785a7ac2e0f48bad8d63`).

```sh
python3 tools/play_demo_only1.py --restoration demo11-node-music --level star-world-1 --show-location
```

The launcher starts a fresh uncleared practice save at the lower-left node.
Enter the course normally. Completion turns the node into the existing portal.

## Routes and evidence

The tracked scripts are `recomp/inputs/star-world-1-{entry,goal,save,secret,side-exit}.script`.
They poke map coordinates, player coordinates and damage immunity as labelled
fixtures. They do not edit exit destinations, completion flags, events, Dragon Coin bits,
the key carried state or SRAM. The goal tape, key pickup, keyhole and map
transfers are real guest actions.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$12`→`$13`→`$14`, room `$005`, spawn and standing at `16/352` |
| Ordinary movement | run crosses `x>0x100`; jump reaches `y<0x140`; a real fall passes `y>0x200` |
| Death | returns to the hub, lives `4→3`; re-entry loads room `$005` with lives `3` |
| Normal goal | screen exit to room `$048`, real goal tape, overworld return |
| Normal clear save | flag `$89` in WRAM `$1EA7` and both SRAM copies (`SRAM[5]`, `SRAM[0x1B2]`) |
| Normal re-entry | the cleared node stays enterable; the `$89` flag persists |
| Console reset reload | File A reload keeps `$89`; re-entry keeps it |
| Secret keyhole | room `$054` loads, key carried (`$1470=1`), keyhole completes without losing a life |
| Secret save and warp | flag `$8B` in WRAM and both SRAM copies; the Warp Star reaches World 1, map 0 at `104/440` (`$0068/$01B8`) |
| Side exit | room `$048`→`$051` loads; leaving its edge returns to overworld mode `$0E` |

The scripted normal-clear values follow the demoOnly1 acceptance: the normal
goal sets `$89` and the keyhole sets `$8B`. They differ from the forest
course's `$8C/$8E` because the hub slot differs.

## Parity with the demoOnly1 line

Fresh reference captures on the `star-world-1` target use the same five scripts
and the same input paths. The new line matches them in every semantic field:
mode, room, lives, hub flag, both SRAM copies, map and map coordinates, and the
carried-key byte. Only moving positions differ, within animation tolerance:
`entry/jump` by 2/6 px, `entry/falling` by 2 px, and `secret/next` by 5 px.

Captures:

- `d11-star1-route-{entry,goal,save,secret,side-exit}-{ref,native}`
- `d11-star1-only1-{entry,goal,save,secret,side-exit}-ref` for the demoOnly1 line

Exact receipts and states are in `local/reports/demo11-star1-route.json`.
The suite log is `local/reports/demo11-star1-route-line.log`.

`tools/qualify_demo11_star1_route.py` checks the head identity, all five routes
on both hosts, every route value above, the save and reload chain, the secret
warp destination and the demoOnly1 parity. The Demo 1-1 line suite passes
**25/25**. The whole-line byte audit is unchanged: 22 recipes, 105,084 changed
bytes inside 139,275 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled map/player coordinate shortcuts and damage immunity.
  This is the same bounded boundary the demoOnly1 line accepted: it is not an
  unassisted full traversal.
- No loaded Dragon Coin placement exists in the four examined rooms, so Dragon Coin persistence is
  not applicable to this path. No audio acceptance is inferred.
- The course graphics recovery is pinned by the earlier Star1 graphics
  qualifier; this check adds the route behaviour.
- The sky secret and the remaining Star World routes stay open.

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-node-music \
  --script recomp/inputs/star-world-1-entry.script --capture fresh-star1-entry-ref
python3 tools/m1.py native --target demo11-node-music \
  --script recomp/inputs/star-world-1-entry.script --capture fresh-star1-entry-native
python3 tools/qualify_demo11_star1_route.py
python3 tools/check_demo11_line.py
```
