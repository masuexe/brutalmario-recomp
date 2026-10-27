# Native sprite 10 to 14 combined target review

## Result

Earlier targets carried one gap record each. A room that places several gap
slots cannot show full actor parity in such a target. This target carries five
records at once: slots `10`, `11`, `12`, `13` and `14` from `cheap-demo`.

Three rooms now match the donor in every captured sample: `12D`, `158` and
`15C`.

## Records

| Slot | Record | Install offset | Code view |
| --- | --- | ---: | --- |
| `10` | `01360080398391002ea6a4d1a6a40000` | `1606514` | `A4: A61F` |
| `11` | `01360000f8a22d454bb0aa06b1aa0000` | `1606530` | `AA: B03C` |
| `12` | `01361080388101046292ab8092ab0000` | `1606546` | `AB: 9253` |
| `13` | `012200003b131944f3c3ac17c4ac0000` | `1606562` | `AC: C3E4` |
| `14` | `01360080388311440f80ad7080ad0000` | `1606578` | `AD: 8000` |

Each record keeps the type-1 layout. Each code block keeps its low 16 address
bits and changes its bank byte only.

## Packs

The target mounts seven packs. Five carry one code block each. The other two
carry the sprite 9E code block and the graphics block.

| Variable | Bank |
| --- | --- |
| `BM_SEVEN_CODE_PACK` | `A4` |
| `BM_SEVEN_CODE_PACK_2` | `AA` |
| `BM_SEVEN_CODE_PACK_3` | `AB` |
| `BM_SEVEN_CODE_PACK_4` | `AC` |
| `BM_SEVEN_CODE_PACK_5` | `AD` |
| `BM_NATIVE_SPRITE_PACK` | `A5` |
| `BM_NATIVE_GRAPHICS_PACK` | `B6` |

The runtime loads each pack from its own environment variable. The tool
`tools/native_sprite_gap.py` reads the key `manifests` and builds one pack for
each record.

## Built target

The target is `demo11-native-sprite10-14`. Its config is
`config/restorations/demo11-native-sprite10-14.json`.

| Item | Value |
| --- | --- |
| Target ROM | `1a0cc34578cb65da83d666a91369f632962dee5f6c0e178f5d0e90558aff55f0` |
| Binary | `BrutalMarioDemo11NativeSprites10To14SNESRecomp` |

## Room result

Each row gives the count of samples that match the donor.

| Room | Samples matched | Note |
| --- | ---: | --- |
| `12D` | 3 of 3 | exact |
| `155` | 3 of 4 | the fourth sample also places slot `3B` |
| `156` | 1 of 3 | the later samples differ in slot 11 X |
| `157` | 2 of 3 | the first sample differs in slot 11 spawn |
| `158` | 3 of 3 | exact |
| `159` | 2 of 3 | the first sample differs in slot 10 spawn |
| `15B` | 2 of 3 | the first sample differs in slot 10 spawn |
| `15C` | 3 of 3 | exact |

The first sample often differs because a later slot spawns one frame earlier in
the target. The later samples then agree.

The run reports no `BRK` and seven module views: `A4`, `A5`, `AA`, `AB`, `AC`,
`AD` and `B6`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite10-14 scaffold
python3 tools/m1.py --target demo11-native-sprite10-14 generate
python3 tools/m1.py --target demo11-native-sprite10-14 build
python3 tools/m1.py --target demo11-native-sprite10-14 native --script recomp/inputs/sprite12-room155-shared.script --capture sprite1014-155-native-v1
python3 tools/qualify_sprite1014_gap.py
```

The qualification tool is `tools/qualify_sprite1014_gap.py`. Its report is
`local/reports/native-sprite1014-final.json`, SHA-256
`38cfaa2f3d5d7d4356d8346d0f2122b298381b275ea220cf7a0f4d34c7f19a83`.

## Limits

This document claims the static review, the built target and entry parity for
three rooms. It does not claim the other five rooms, movement, a course pass or
a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_10_14.py` and pass 6/6. The full suite passes
250/250 tests. The log is `local/reports/unit-tests-sprite1014.log`.
