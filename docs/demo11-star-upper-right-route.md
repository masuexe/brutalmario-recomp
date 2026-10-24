# Demo 1-1 upper-right Plains Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World upper-right node: map 6, X `$01C8`, Y `$0168`;
translevel `$02`; room `$002`. It is the wiki **Plains Star**, the fifth Star
Road level. The wiki describes a maze of breakable Super Mario Bros. 3 bricks,
a cape feather, and the keyhole secret exit in the brick maze. The
[Star World BGM checkpoint](demo11-star-bgm.md) already plays the wiki-correct
Freiluftmusik slot `32`; this replaces the old legacy slot `5D` substitute
from the demoOnly1 line.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-upper-right --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-upper-right-{entry,coins-save,death}.script`. They
use map, player and camera shortcuts and damage immunity as labelled fixtures.
They do not write coin counters, DK bits, enemy state, exit destinations,
completion flags or SRAM.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$12`→`$13`→`$14`, room `$002`, spawn at `$0080/$1080`, lives 4 |
| Low Map16 guard | buffer `$C800..$DFFF` is byte-identical from layout to active |
| Ordinary controls | walk reaches X `$00B6`; jump and later samples stay active at X `$00D2` |
| Course music | reference requests slot `32`; the legacy `5D` request is absent |
| Five DK coins | real collisions at `$01C0/$0F90`, `$0040/$0F30`, `$00B0/$0DE0`, `$0070/$0D10` and `$00D0/$0B70` |
| Coin 5 | lives `4→5` and the saved DK bit `$1F2F=$20` |
| Upward pipe | from `$0108/$0AB0` enters the real goal room `$048` at `$0028/$0140` |
| Real goal tape | returns to the map in mode `$0E` |
| Normal-clear save | hub flag `$1EA4=$86`; `SRAM[2]=$86` and `SRAM[$01AF]=$86` |
| Console reset reload | File A load keeps `$86` and the DK bit; re-entry loads room `$002` |
| Death | a real fall returns to the hub in mode `$0E` at `$010E/$012E` with lives `4→3`; re-entry loads room `$002` with lives 3 |

## Host and line parity

The native build matches the reference capture on every checked field. Only
the entry `jump` and `later` Y values differ by 16 pixels, which is the jump
animation phase.

Fresh demoOnly1-line captures on the `star-world-upper-right` target use the
same scripts and match the new line on mode, room, X and Y for every route
sample. The course music is intentionally different: the donor line still
requests the old slot `5D`, while this line requests the wiki-correct `32`.

Captures: `d11-ur-<route>-{ref,native}` and `d11-ur-only1-<route>-ref`.
Report: `local/reports/demo11-star-upper-right-route.json`. Suite log:
`local/reports/demo11-star-upper-right-route-line.log`.

`tools/qualify_demo11_star_upper_right_route.py` checks the head identity, the
three routes on both hosts, every value above, the Map16 guard, the music
request, the native build identity and the demoOnly1 parity. The Demo 1-1 line
suite passes **28/28**. The whole-line byte audit is unchanged: 23 recipes,
105,090 changed bytes inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled coordinate shortcuts and damage immunity. The coins,
  pipe, goal tape and deaths are real guest actions.
- The **Plains Star keyhole secret exit is not covered** here. The recorded
  wiki route is: find the backward-animated brick near the top right, take its
  P-Switch, go down the level, press the switch to convert the bricks, and fall
  to the key and keyhole.
- An unassisted full traversal is not claimed. The long brick course needs a
  separate route pass.
- The save flag constants are recipient-local. The demoOnly1 line uses the same
  normal-clear value on these scripts.

## Sources

- https://brutalmario.fandom.com/wiki/Plains_Star
- https://brutalmario.fandom.com/wiki/Music
- https://wikiwiki.jp/kitikumario/
- [Community walkthrough reference](walkthrough-reference.md)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-right-coins-save.script --capture fresh-ur-coins-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-right-coins-save.script --capture fresh-ur-coins-native
python3 tools/qualify_demo11_star_upper_right_route.py
python3 tools/check_demo11_line.py
```
