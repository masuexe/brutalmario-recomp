# Boss health bar: root cause and port plan

## Result

The boss sprites work. The health bar does not show because the recipient
baseline `demo-1-1` has no bar drawing routine.

## The bar routine

The official images draw the bar with one routine. The routine is 156 bytes.
It reads `$7FFFDF`, copies 16 bytes from the `$349F00` room table, and writes
the background map.

| Image | Routine address |
| --- | --- |
| `cheap-demo` | `34:9DF8` |
| `boss` | `10FEDE` |
| `7hero` | `10FEDE` |
| `demo-only-1` | `10FEDE` |
| `mazo` | `13:82AF` |
| `ow` | `34:9DF8` |
| `demo6`, `demo7` | `34:9E05` |
| `demo-1-1` | **absent** |

The product image takes `demo-1-1` as its baseline. Therefore the routine is
absent from the product image.

## The room table

The routine indexes a 4096-byte table at `$349F00`. The table gives 16 map
bytes for each room low byte.

| Image | Room `8B` entry |
| --- | --- |
| `boss` | `FC FC FC FC FC FC 3A 3B 3B 3A FC FC FC FC FC FC` |
| `demo-1-1` | all zero |
| product r25 | `88 0D 27 01 00 14 22 00 00 77 44 00 15 02 25 00` |

The product image holds different data at `$349F00`. A 2623-byte sprite block
starts at `$349EF0` and covers that address. The bar table is therefore absent
as well.

## What the boss programs do

The boss programs write the bar data to `$7FFFDF`. Slot `32` does this at
`21DECD` from its init at `21C34D`. The data is correct in both images:

`01 0B 18 1C 1C FC 44 44 44 44`

The bytes decode to the label `B O S S` and a four-cell bar. Tiles `0B`, `18`,
`1C` form the label. Tile `44` forms the bar.

## The port plan

The port needs three items:

1. The 156-byte bar routine.
2. The 4096-byte room table at `$349F00`.
3. A call to the routine each frame.

Item 3 is open. No direct call to the routine exists in any image. The
routine must be reached by an indirect jump or by a table of handlers.

## Open issue

The product image has 88 free bytes at `10FED0`. The routine needs 156 bytes.
The port must place the routine in a larger free area or in a native content
pack.