# Demo 1-1 lower-right Snow Star route acceptance

Date: 2026-10-25. This is a qualification checkpoint. No ROM changed. The head
stays `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`,
native binary
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`).

The course is the Star World lower-right node: map 6, X `$01C8`, Y `$01E8`;
translevel `$08`; room `$008`. It is the wiki **Snow Star**, the seventh Star
Road level. The wiki describes a seal cave with Santa's gift reward, the
normal exit as a match of three ? Goal Point blocks, and the secret as a stomp
on the seal that freezes the water to open the upper icy alcove with the key.
The [Star World BGM checkpoint](demo11-star-bgm.md) already plays the restored
Jingle Bells slot `54`.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --level star-world-lower-right --show-location
```

The launcher starts a fresh uncleared practice save at the node. Enter the
course normally.

## Routes and evidence

The tracked scripts are
`recomp/inputs/star-world-lower-right-{entry,enemies,coins-save,secret,death}.script`.
They use map/player coordinate shortcuts and damage immunity as labelled
fixtures. They do not write counters, DK bits, slot results, goal flags, exit
destinations, key state or SRAM.

| Route | Reference and native result |
| --- | --- |
| Entry | mode `$12`→`$13`→`$14`, room `$008`, spawn at `$0010/$0130`, lives 4 |
| Low Map16 guard | buffer `$C800..$FFFF` is byte-identical from layout to graphics |
| Ordinary controls | early, 180 and 600 frame samples stay active; right+jump input moves the player |
| Course music | reference requests the restored Snow Star slot `54` |
| Ice Ptooie | `plants_loaded` has custom sprite `$57` with `$C2` values 0 and 1 (enemy and generated projectile) |
| Penguin | `penguins_loaded` has custom sprite `$58` |
| Five DK coins | real collisions raise both counters from 1 to 5; coin 5 sets `$1F30=$80` and grants one life |
| End-wall transfer | the real end wall loads room `$026` in mode `$14` |
| Goal-point match | three custom-slot-9 sprites stop with `tile=$8C`; the real goal sphere sprite `$4A` appears |
| Normal clear | mode `$0E`, flag `$1EAA=$8A`, lives 5 |
| Normal save | `SRAM[8]=$8A` and `SRAM[$01B5]=$8A`; DK `$07D1=$80`; checksum bytes `$07DC..$07DD=$DA59` |
| Console reset reload | File A load and re-entry keep `$8A` and the DK bit |
| Secret reward | Santa's reward exposes the real key; `$1470=1` while Mario carries it |
| Keyhole secret | flag `$1EAA=$8B`; `SRAM[8]=$8B`; the resulting Warp Star reaches map 0 at `$0128,$0048` |
| Death | real fall returns to the hub in mode `$0E` with lives `4→3`; re-entry loads room `$008` with lives 3 |

The restored dependencies are exercised here: the Jingle Bells upload, the
Snow Star ExGFX set, the ice Ptooie sprite `$57`, the existing penguin `$58`
and the Santa reward visuals.

## Host and line parity

The native build matches the reference capture on every route state field:
mode, room, X, Y, lives, clear flag, DK bit, DK counters, map and map position,
and carried key. Both hosts satisfy the sprite assertions above.

Fresh demoOnly1-line captures on the `star-world-lower-right` target use the
same scripts and match every route state on the same fields. Only the pre-entry
menu samples differ, and those are not part of the route.

Captures: `d11-lr-<route>-{ref,native}` and `d11-lr-only1-<route>-ref`.
Report: `local/reports/demo11-star-lower-right-route.json`. Suite log:
`local/reports/demo11-star-lower-right-route-line.log`.

`tools/qualify_demo11_star_lower_right_route.py` checks both hosts, the low
Map16 guard, the music request, the loaded enemy sprites, the five coins, the
goal-point match, the goal sphere, the normal and secret saves, SRAM checksum
bytes, the secret Warp Star destination, death/re-entry, the head and build
identities and the demoOnly1 parity. The Demo 1-1 line suite passes **29/29**.
The whole-line byte audit is unchanged: 23 recipes, 105,090 changed bytes
inside 139,297 declared region bytes, zero unexpected.

## Limits

- The scripts use labelled coordinate shortcuts and damage immunity. The
  coins, end wall, slot match, goal sphere, Santa reward, keyhole and deaths
  are real guest actions.
- An unassisted full traversal is not claimed. Listening acceptance is not
  claimed; the audio evidence is the restored slot selection only.
- The save flag, DK bit and SRAM constants are recipient-local. The demoOnly1
  line matches them on these scripts.
- Shared sprite `$57` is used by other rooms; this check accepts only the
  Snow Star route.

## Sources

- https://brutalmario.fandom.com/wiki/Snow_Star
- https://brutalmario.fandom.com/wiki/Music
- https://wikiwiki.jp/kitikumario/
- [Community walkthrough reference](walkthrough-reference.md)

## Reproduce

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-lower-right-secret.script --capture fresh-lr-secret-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-lower-right-secret.script --capture fresh-lr-secret-native
python3 tools/qualify_demo11_star_lower_right_route.py
python3 tools/check_demo11_line.py
```
