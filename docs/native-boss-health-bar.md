# Boss health bar: the complete chain

## Result

The boss programs write the bar data. The data reaches WRAM. The data does
not reach the background map, so the bar and the boss label do not appear.

## The chain, step by step

| Step | Address | Result |
| --- | --- | --- |
| 1 | `21C34D` | The slot `32` init calls `JSR $DECD`. |
| 2 | `21DECD` | The routine writes `$7FFFDF` to `$7FFFE8`. |
| 3 | `$7FFFDF` | WRAM holds `01 0B 18 1C 1C FC 44 44 44 44`. |
| 4 | BG3 map | The product image does not receive this data. |

Both images hold the same data at step 3:

| Image | `$7FFFDF` to `$7FFFE8` |
| --- | --- |
| product r25 | `01 0B 18 1C 1C FC 44 44 44 44` |
| cheap-demo | `01 0B 18 1C 1C FC 44 44 44 44` |

The bytes decode to the label `B O S S` and a four-cell bar. Tiles `0B`,
`18`, `1C` form the label. Tile `44` forms the bar.

## Where the images differ

| Address | product r25 | cheap-demo |
| --- | --- | --- |
| `21DECD` writer | present | present |
| `32:D0E5` | `BD 02 16 A8` code | `41 7C 00 0C` data |
| `00:8F25` | `JSL $10A71D` | `INC $0DBF` |
| BG3 map row 1 | empty | label and bar |

The product keeps the recipient baseline form at `00:8F25`. The baseline
routes through `10:A71D`, which ends at `INC $0DBF`. The bar refresh therefore
depends on `$13CC`, and `$13CC` stays zero in every product capture.

## Evidence from the captures

| Capture | Room | BG3 label tiles | BG3 bar tiles |
| --- | --- | --- | --- |
| product r25 `f060` | `08B` | none | `58 59 59 58` only |
| cheap-demo `entry` | `08B` | `11 24 28 28` at entry 40 | `44 44 44 44` |

## Open issue

The bar refresh waits on `$13CC`. The feeder at `32:D0E5` exists in the product
image but never runs. The next step is to find what calls that feeder. The
cheap-demo image does not have the feeder at all, so it must reach the bar
through a different path.