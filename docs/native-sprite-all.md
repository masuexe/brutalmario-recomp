# Native all-gap combined target review

## Result

This target carries every `cheap-demo` gap record that has an install so far:
11 records. It also carries slots `10` to `14`, which the first combined target
`demo11-native-sprite10-14` holds alone.

Four rooms now match the donor in every captured sample: `12D`, `155`, `158`
and `15C`. Room `155` needed slot `3B`, which only this target provides.

## Records

| Slot | Install offset | Code view | Rooms |
| --- | ---: | --- | --- |
| `0F` | `1606498` | `AE:EFE6` | `085`, `110` |
| `10` | `1606514` | `A4:A61F` | `12D`, `156`, `157`, `15B`, `15C` |
| `11` | `1606530` | `AA:B03C` | `155`, `156`, `158`, `159` |
| `12` | `1606546` | `AB:9253` | `155`, `157`, `159`, `15B`, `15C` |
| `13` | `1606562` | `AC:C3E4` | `157`, `15C`, `15D` |
| `14` | `1606578` | `AD:8000` | `157`, `15C` |
| `19` | `1606658` | `AF:F6C4` | `000`, `100` |
| `22` | `1606802` | `B0:E042` | `075`, `088` |
| `3B` | `1607202` | `B1:9587` | `13F`, `141` |
| `55` | `1607618` | `B2:B9F4` | `0AF`, `0B1`, `0B3`, `0B5`, `0B6` |
| `92` | `1608594` | `B3:DEB3` | `00D`, `162`, `163`, `164`, `165`, `166` |

Each record keeps the type-1 layout. Each code block keeps its low 16 address
bits and changes its bank byte only. No record needs a dispatch table or a
source-bank call patch.

## Packs

The target mounts 13 packs: 11 code blocks, the sprite 9E code block and the
graphics block. The code banks are `A4`, `AA` to `AF` and `B0` to `B3`.

## Built target

| Item | Value |
| --- | --- |
| Target ROM | `bba8a831eedf675d598ce1d9ed4e593f33fa613b216e62585c5c8e88bd2a6169` |
| Binary | `BrutalMarioDemo11NativeAllSpriteGapsSNESRecomp` |

## Room result

| Room | Samples matched | Note |
| --- | ---: | --- |
| `12D` | 3 of 3 | exact |
| `155` | 4 of 4 | exact, and only this target holds slot `3B` |
| `156` | 1 of 3 | a load-phase shift moves the later samples |
| `157` | 2 of 3 | the first sample differs |
| `158` | 3 of 3 | exact |
| `159` | 2 of 3 | the first sample differs |
| `15B` | 2 of 3 | the first sample differs |
| `15C` | 3 of 3 | exact |

The run reports no `BRK` and 13 module views: `A4`, `A5`, `AA` to `AF`, `B0` to
`B3` and `B6`.

## Load phase

A target loads a room a few frames before the donor. This section measures that
offset with a 10-frame dump step over 240 frames. The tool reads
`spritefine-<room>-{donor,native}-v1` and compares the row series.

| Room | Offset | Frames with the same mode | Rows equal | Note |
| --- | ---: | ---: | ---: | --- |
| `157` | -20 | 21 | 19 | two mode-change frames differ |
| `159` | -30 | 21 | 19 | two mode-change frames differ |
| `15B` | -20 | 21 | 19 | two mode-change frames differ |
| `156` | -20 | 21 | 9 | a constant 4-pixel gap remains |


## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite-all scaffold
python3 tools/m1.py --target demo11-native-sprite-all generate
python3 tools/m1.py --target demo11-native-sprite-all build
python3 tools/m1.py --target demo11-native-sprite-all native --script recomp/inputs/sprite12-room155-shared.script --capture spriteall-155-native-v1
python3 tools/qualify_sprite_all_gap.py
```

The qualification tool is `tools/qualify_sprite_all_gap.py`. Its report is
`local/reports/native-sprite-all-final.json`, SHA-256
`8b7c4c52b45b53359668421be0a16125bad18d838e8acc0077bd778d441aa942`.

The tool `tools/qualify_phase_alignment.py` measures an offset for any room.
Its report is `local/reports/native-sprite-phase.json`, SHA-256
`6f052595217ff857868edc8e60fcc86ac62f9405f45ad33238ab61d9118e7bbb`.

## Limits

This document claims the static review, the built target and entry parity for
four rooms. It does not claim the other four rooms, movement, a course pass or
a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_all.py` and pass 6/6. The full suite passes
256/256 tests. The log is `local/reports/unit-tests-phase.log`.