# Sprite 34 light circle: room 16A fix

## Result

Product r24 shows the light circle in room `16A`. The user can play room `16A`
with the circle active.

## Cause

The sprite 34 init program reads the room number from `$010B` and compares it
with a fixed list. The list holds these rooms:

`EA` `08` `EB` `EC` `EE` `ED` `52` `53` `69` `67`

Room `16A` is not in the list. Control reached `RTL` at `3E:EC06` and returned.
The sprite state `$1504` stayed `00`, and the main loop had no branch for that
value. The circle never appeared.

## Fix

One byte changes at `3E:EC06`, file offset `0x1F6C06`:

| Before | After | Meaning |
| --- | --- | --- |
| `6B` | `EA` | `RTL` becomes `NOP` |

A room that matches no list entry now falls through to `3E:EC07`, which is
`JMP $ECB9`. That is the default branch. It sets `$1504` to `0C`, and the main
loop then runs the circle behaviour.

## Verification

`tools/qualify_product_sprite_34.py` checks these items:

- the r24 image identity and the r22 lineage;
- the single patched byte and its neighbours;
- the sprite state in room `16A` and the frame difference against r22;
- the sprite state in room `167` and the frame identity against r22.

| Measurement | r22 | r24 |
| --- | --- | --- |
| Room `16A` sprite state `$1504` | `00` | `0C` |
| Room `16A` sprite position at `r2` | `(16,1664)`, equal to the player | `(153,1707)` |
| Room `167` frame SHA-256 prefix | `d4531187ca20b70c` | `d4531187ca20b70c` |
| Room `167` sprite state `$1504` | `0C` | `0C` |

Report: `local/reports/product-r24-sprite-34.json`.

## Scope

The patch affects every room that places slot `34` and that the list does not
name. These rooms are `15E`, `16A`, `16D` and `192`. All other placements
already match a list entry, so their behaviour does not change.

## Deferred issues

- Room `16A` keeps the sprite placement from the recipient baseline. The
  program now handles it through the default branch, which is the same
  behaviour that room `167` uses.
- The `boss` image holds a newer sprite 34 program. That program names rooms
  `5E`, `6A` and `6D` and uses a separate branch block. This checkpoint does
  not port it.
- The slowdown that the user observed on the `boss` image is a hardware limit.
  The native build runs at full frame rate.