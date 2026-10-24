# Demo 1-1 upper-left Bay Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World upper-left node: map 6, X `$0128`, Y `$0168`;
translevel `$04`; room `$004`. It is the wiki **Bay Star**, the third Star
Road level. The wiki describes water currents and Super Mario 64 water-level
switches, and the secret exit as a top switch, a full water rise, two lower
levels, then the key and keyhole. The music is Podol from Romancing SaGa 3;
the [Star World BGM checkpoint](demo11-star-bgm.md) already selects slot `49`.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-upper-left --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-upper-left-{entry,water,coins-save,side-exit,death}.script`.
They poke map and player coordinates and damage immunity as labelled fixtures.
They do not write coin counters, Dragon Coin bits, water state, completion, exit
destinations or SRAM.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$12`→`$13`→`$14`, room `$004`, spawn at `$01A0/$0CB0`, lives 4 |
| Ordinary controls | left input moves the player to X `$0149`; jump and later samples stay active |
| Missing-graphics guard | low Map16 buffer `$C800..$DFFF` is byte-identical from layout to active; the old corruption is gone |
| Swimming | five real B presses move the player up from Y `$0CB0` to `$0CA4` |
| Water switch | platform contact changes the water target at `$7E:FFD0` from `$0CB0` to `$0C90` and the water settles there |
| Five Dragon Coins | real coin collisions at `$0180/$0BBF`, `$0020/$0B85`, `$0010/$0B68`, `$0040/$0B4A` and `$01D0/$0B20` |
| Coin 5 | lives `4→5` and the saved Dragon Coin bit `$1F2F=$08` |
| Screen-8 pipe | loads the real goal room `$048` at `$0028/$0140` |
| Real goal tape | returns to the map in mode `$0E` |
| Normal-clear save | hub flag `$1EA6=$85`, second flag `$1EA9=$03`, `SRAM[4]=$85`, `SRAM[7]=$03` |
| Console reset reload | File A load keeps `$85`, `$03` and the Dragon Coin bit; re-entry loads room `$004` again |
| Side exit | alternate pipe loads `$048`, then `$051`; leaving the `$051` edge returns to the hub in mode `$0E` at `$000D/$011E` without a life lost |
| Death | a real fall returns to the hub in mode `$0E` at `$010E/$012E` with lives `4→3`; re-entry loads room `$004` with lives 3 |

The two restored dependencies are exercised here: the room's missing ExGFX
stream (the Map16 guard) and custom sprite `$7A`, which provides the swim and
water-switch behavior.

## Host and line parity

Fresh demoOnly1-line captures on the `star-world-upper-left` target use the
same scripts and match the new line in every semantic field: mode, room, X, Y,
lives, hub flags, Dragon Coin bit, SRAM flag bytes and the water target. Only the
`selected` menu sample keeps a different leftover room byte, which is not part
of the route.

The native build matches the reference capture exactly on all of those fields.
The SRAM template differs in unrelated uninitialized bytes `0x8F..0x93`; the
checked flag bytes match.

Captures: `d11-ul-<route>-{ref,native}` and `d11-ul-only1-<route>-ref`.
Report: `local/reports/demo11-star-upper-left-route.json`. Suite log:
`local/reports/demo11-star-upper-left-route-line.log`.

`tools/qualify_demo11_star_upper_left_route.py` checks the head identity, all
five routes on both hosts, every value above, the Map16 guard, the native
build identity and the demoOnly1 parity. The Demo 1-1 line suite passes
**27/27**. The whole-line byte audit is unchanged: 23 recipes, 105,090 changed
bytes inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled coordinate shortcuts and damage immunity. The coins,
  water switch, pipes, goal and deaths are real guest actions.
- The **Bay keyhole secret exit is user-verified**. The user play-tested the
  course: all Dragon Coins are collectable, the normal exit is reachable, and
  the keyhole sits next to the normal-exit pipe. The key comes from the upper
  right question block at the start. The user considers the Bay Star test
  passed. Automated secret testing stays stopped.
- An unassisted full ascent is not claimed. The vertical cave still needs a
  full route pass.
- The save flag constants are recipient-local. The demoOnly1 line uses the same
  normal-clear value on these scripts.

## Sources

- https://brutalmario.fandom.com/wiki/Bay_Star
- https://brutalmario.fandom.com/wiki/Music
- https://brutalmario.fandom.com/wiki/Star_World
- https://wikiwiki.jp/kitikumario/ (Japanese Kitiku Mario wiki, user-provided
  route reference)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-left-water.script --capture fresh-ul-water-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-left-water.script --capture fresh-ul-water-native
python3 tools/qualify_demo11_star_upper_left_route.py
python3 tools/check_demo11_line.py
```
