# Mazo 9B and 9C relocation check

## Result

The product target holds sprite 9B in bank `C8` and sprite 9C in bank `C9`.
Both records run with no `BRK`. Both rooms create fewer actors than the donor.

## Measured actor counts

| Build | Sprite | Mount bank | Actors at the fight | BRK |
| --- | --- | --- | ---: | ---: |
| product | 9C (room 151) | `C9` | 1 | 0 |
| standalone | 9C (room 151) | `A2` | 2, then 3 | 0 |
| product | 9B (room 190) | `C8` | 1 | 0 |
| standalone | 9B (room 190) | `A2` | 3, then 5 | 0 |

The same fixture runs on each build: `recomp/inputs/mazo-9c-native-fixture.script`
and `recomp/inputs/mazo-9b-native-fixture.script`.

## Isolation probes for sprite 9C

The probes use the same code bytes, the same base and the same tool. Only the
mount bank changes.

| Mount bank | Resolutions | Executed instructions | Actors | BRK |
| --- | ---: | ---: | ---: | ---: |
| `A2` | 1,227,003 | 196,398 | 2, then 3 | 0 |
| `C9` | 422,392 | 66,559 | 1 | 0 |
| `E0` | 218 | 0 | 0 | 1 |

The adapted program differs only in the 72 bank bytes of the self calls. Every
other byte is equal. The base ROM is `demo11-native-sprite9e`.

## Finding

The mount bank changes the behavior of sprite 9B and sprite 9C. Many other gap
sprites run in banks `A4` to `C9` and match the donor. Those sprites are fully
relocated. Sprite 9B and sprite 9C are not.

The likely cause is a read of the source bank that the recipe does not patch.
The source banks are `1E` for 9B and `22` for 9C. When the pack sits in `A2`,
the LoROM mirror puts it at the file offset of bank `22`, so the read finds the
module. When the pack sits in `C9`, the read finds the original ROM bytes.

This document records the evidence. It does not claim the cause is proven.

## Fix applied

Sprite 9B now mounts at bank `9E` and sprite 9C at bank `9F`. Both banks were
free and do not touch the Seven pack in bank `A2`.

| Sprite | Source | Old bank | New bank |
| --- | --- | --- | --- |
| 9B | `1EEFAE` | `C8` | `9E` |
| 9C | `228000` | `C9` | `9F` |

The product captures use the mazo fixtures.

| Room | Sprite | Actors before | Actors after | Donor |
| --- | --- | ---: | ---: | ---: |
| `151` | 9C | 1 | 2, then 3 | 2, then 3 |
| `190` | 9B | 1 | 3, then 5 | 3, then 5 |

Both rooms return to the map or hold the settled parts. The run holds no `BRK`.
The unchanged-route regression stays at 32 of 32.

Room `151` capture: `local/captures/prod2-151`. Room `190` capture:
`local/captures/prod2-190`.

## Open item

The exact bank rule is not yet known. Bank `9E` and bank `9F` work. Bank `C8`,
bank `C9` and bank `E0` do not. Bank `A2` also works. Pick a bank in the range
`9E` to `A2` for a future relocated module, and measure it.
## Next action

1. Rebuild the sprite-full target from the new recipes, or retire it.
2. Check whether other relocated modules in banks `C0` to `C9` show the same
   lowered actor counts. If they do, move them to the `9E` to `A2` range.