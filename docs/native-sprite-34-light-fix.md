# Sprite 34 light circle: the working fix

## Result

Product r25 shows the light circle in room `16A`. The user accepted the result
in play on 2026-11-05.

## How the circle works

The circle is not a sprite tile. The program uses an HDMA window effect:

| Register | Product r22 | Product r25 |
| --- | --- | --- |
| `hdmaen` | `00` | `30` |
| `window` | `0, 255, 0, 0` | `15, 39, 0, 0` |
| `windowsel` | `0` | `3` |

Channels `4` and `5` feed the window from WRAM `7F:DF00` and `7F:E100`.
This is why the object attribute table does not change between r22 and r25.

## Cause

Two programs exist for sprite 34. The `cheap-demo` program names eleven rooms
and room `16A` is not one of them. The `boss` program names thirteen rooms,
including `16A`, and it sets a dedicated state for that room.

Product r22 holds the `cheap-demo` program. Room `16A` therefore placed a
sprite that the program ignored.

## Fix

Product r25 replaces the program with the `boss` program and maps it into bank
`0x80`.

| Item | Value |
| --- | --- |
| Module recipe | `config/native-content/sprite34-boss-module.json` |
| Donor | `boss` |
| Program size | 5645 bytes |
| Program SHA-256 | `8e3ee73d44ee6a0b231d712a00b26c59bd8d52b5c4a4ceb30435f6d279a3b153` |
| Native address | `80CDFE` |
| Record | `013600003f8319640dce807ccf800000` |
| Rooms | `0EA` `0EB` `0EC` `0ED` `0EE` `108` `152` `153` `15E` `167` `169` `16A` `16D` |

## The bank rule

The module must not use bank `0xC0`. A bank above `0xBF` aliases into the low
LoROM mirror, and the runtime then fails to resolve the pack for most reads.

| Bank | Resolutions | Executed instructions | Sprite timer | Sprite position |
| --- | ---: | ---: | --- | --- |
| `0xC0` | 47,434 | 8,183 | stays `00` | stays `(0,1680)` |
| `0x80` | 3,967,482 | 610,928 | reaches `01` | moves to `(27,1680)` |

Use a bank between `0x80` and `0xBF` for a sprite code pack.

## Verification

`tools/qualify_product_sprite_34_light.py` checks these items:

- the r25 image identity and the r22 lineage;
- the module size, slot, bank and record;
- the candidate changes only the six record pointer bytes;
- room `16A` reaches state `0E`, advances its timer and moves;
- room `167` keeps state `0C` and the accepted frame.

| Measurement | Room `16A` | Room `167` |
| --- | --- | --- |
| State | `0E` | `0C` |
| Timer `$151C` | `01` | `103` |
| Position | `(27,1680)` | `(106,274)` |
| Frame equals the parent | no | yes |

Report: `local/reports/product-r25-sprite-34-light.json`.

## User acceptance

The user started the r25 build and reported that the room works. This
confirms the circle, the terrain effect and the frame rate.

The user also tested rooms `15E` and `16D`. Both behave as expected. They do
not show the light circle, because the program gives them other states.

## Remaining placement

The `boss` program names thirteen rooms. The product image places slot `34`
in fourteen rooms, so one placement has no branch:

| Room | Low byte | In the program list |
| --- | --- | --- |
| `192` | `92` | no |

Room `192` holds data that starts with `FF` bytes. Its level header reads
`FF 30 FF 60`, which is not a normal header. Treat room `192` as an unused
entry, not as a missing light circle.

## Deferred issues

- Product r24 is superseded. Its one-byte patch made room `16A` take the
  platform branch, which does not change the terrain.