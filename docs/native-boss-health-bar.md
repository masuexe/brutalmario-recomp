# Boss health bar: the fix

## Result

Product r26 shows the boss label and the health bar in rooms `08A`, `08B`
and `091`. The bars match the `cheap-demo` reference byte for byte.

## Cause

The product image already has a complete bar upload routine. It sits at
`40:A508`. The routine writes the background map from the legacy buffer
`$7FFFDF`.

The routine starts with a room gate. The gate accepts only these rooms:

`00BC` `00CC` `0128` `0146` `00CF`

Rooms `08A`, `08B` and `091` are not in that list. The routine therefore
returns before it draws the bar.

## The boss programs are correct

Each boss program writes the bar data at init. Slot `32` does this at
`21DECD`. The data is correct in every image:

`01 0B 18 1C 1C FC 44 44 44 44`

Byte `01` at `$7FFFDF` is the enable flag. Bytes `0B 18 1C 1C` form the label.
Bytes `44 44 44 44` form the bar.

## Fix

Product r26 adds a room gate shim at `40:A570`. The shim checks the three new
rooms, then chains to the existing routine.

| Item | Value |
| --- | --- |
| Hook | `00:8DE1` changes `2208A540` to `2270A540` |
| Shim | `40:A570`, 34 bytes |
| Shim size | fits in the 48 free bytes at `40:A569` to `40:A599` |

The shim tests `$010B` against `008A`, `008B` and `0091`. A match jumps to the
upload tail at `40:A52C`. No match chains to the old gate at `40:A510`.

## Verification

`tools/qualify_product_boss_hp_row.py` checks the image and the captures.

| Room | Label tiles | Bar tiles |
| --- | --- | --- |
| `08A` | `1E 15 1D 12 16 0A` (`ULTIMA`) | `FD FD FD FD` |
| `08B` | `0B 18 1C 1C` (`BOSS`) | `44 44 44 44` |
| `091` | `21 0A 17 FC 0B 12 0E` (`XAN BIE`) | `FD FD FD FD` |

Room `08B` matches the `cheap-demo` reference row byte for byte.

## Product r30: the flag replaces the room list

The original routine tests the boss request flag `$7FFFDF` already, at
`40:A537`. A fixed room list sits in front of that test.

Product r30 replaces the list with a direct jump to `40:A52C`. That path
tests `$0100 == 14` and `$7FFFDF`, so every boss room draws the row.

| Room | Label | Bar | Frames |
| --- | --- | --- | --- |
| `0BB` | `BOSS` | 8 cells | `f0300` to `f2400` |
| `03B` | `KRACKO` | 4 cells | `f0600` to `f3000` |
| `14E` | `REACTOR` | 4 cells, counts down | `f0600` to `f3000` |
| `08A` | `ULTIMA` | 6 cells | `f420` to `f12720` |
| `08B` | `BOSS` | 4 cells | `f060` to `f12720` |
| `091` | `XAN BIE` | 6 cells | `f060` to `f12720` |

### The flag is the correct signal

| Frame | Room | `$7FFFDF` | Buffer |
| --- | --- | --- | --- |
| boss | `0BB` | `01` | `BOSS` and the bar |
| after the change | `000` | `00` | all zero |

The engine clears the flag and the buffer when the room changes. A room
without a boss cannot show a stale row.

### Shim

```
7D0D  JSL $3EA008
7D11  PHP / REP #$20 / PHA
7D15  LDA $010B
7D18  CMP #$008A
7D1B  BNE $7D2C
7D1D  LDA #$00FC / STA $7FFFED / STA $7FFFEE / STA $7FFFEF
7D2C  JML $40A52C
```

The shim keeps the room `08A` tail fix. The draw decision comes from the flag.

## Product r28 regression

| Room | Result |
| --- | --- |
| `08A` | label `ULTIMA` and the bar from `f420` to `f12720`; the row tail is `FC` |
| `08B` | label `BOSS` and the bar from `f060` to `f12720` |
| `091` | label `XAN BIE` and the bar from `f060` to `f1920` |
| `167` | four slot `34` actors at state `0C` on every frame |
| `16A` | slot `34` at state `0E` in mode `14` |

The row holds for the whole run.

| Room | First frame with the row | Frames checked to |
| --- | --- | --- |
| `08A` | `f420` | `f12720` |
| `08B` | `f060` | `f12720` |
| `091` | `f060` | `f12720` |

The `entry` frame has no row in any room, because the boss init runs after
that frame.

Report: `local/reports/product-r26-boss-hp-row.json`.

## Deferred issues

- The bar length does not change with the boss health in these rooms. The
  reference images behave the same way.
- Rooms `009`, `07E` and `130` also place boss programs. They keep the
  previous behavior.