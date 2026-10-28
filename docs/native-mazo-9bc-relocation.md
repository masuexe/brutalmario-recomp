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

## Next action

1. Extend the module analysis to flag a long read to the source bank.
2. Re-derive the 9B and 9C recipes from that report.
3. Capture rooms `151` and `190` again and require the donor actor counts.
