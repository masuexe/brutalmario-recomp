# Native room 151 phase music

## Problem

The room 151 boss uses the sprite 9C program. That program requests music changes.
The expected songs are `$A5` (The Fierce Battle) for the second boss and `$AD`
for the defeat of the second boss.

The donor code writes two song values. The values `$23` and `$22` come from the
legacy donor engine. The music IDs are version-local. Slots `$23` and `$22` hold
valid payloads, but they are not the intended songs.

Playtest of the first candidate (r11) showed that the second-boss arrival played
`$AD`. Candidate r11 had the two slots in the wrong order. Candidate r12 swaps them.

## Fix

Target `demo11-native-product-r12` adds the recipe
`config/native-content/sprite9c-9f-phasebgm2-module.json`. The recipe copies
`sprite9c-9f-module.json` and adds two code patches.

| Donor site | Before | After | Event |
| --- | ---: | ---: | --- |
| `22:92FA` | `22` | `A5` | Second-boss arrival |
| `22:8E3A` | `23` | `AD` | Defeat of the second boss |

The second-boss arrival runs the animation routine near `22:92E6`. That routine
writes the first song. The defeat path runs the init routine at `22:8E22`. That
routine writes the second song. Candidate r11 set these two songs in the opposite
order.

The recipe leaves the write at `22:824A` (`$0B`) unchanged. The user did not report
that event.

The ROM is identical to r10 (`d29b121e...2f552`). Only the external module pack
changes. Pack `sprite9c-code.bin` stays in bank `9F` and stays 12412 bytes. Its
adapted SHA-256 is `d3d9fc13360de8c0f509b57c9abca6bf2fe307bed53c550d70fa581062846dc4`.

## Verification

`tests/test_product_r12.py` checks these items.

- The r12 ROM equals the r10 ROM.
- The config declares the `sprite-9c-phase-music` adaptation.
- The pack differs from r10 at only `0xE3A` and `0x12FA`.
- The new bytes are `AD` and `A5`.
- Song slots `A5` (2881 bytes) and `AD` (2152 bytes) are present.

Capture `r12-151` matches the r11 capture byte for byte. That covers the window
before the phase change.

## Limits

The phase change needs player damage. The test scripts do not damage the boss.
So automation does not exercise the two music writes. You must playtest the
second boss and the defeat.

## Reproduction

```sh
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r12')"
python3 tools/m1.py --target demo11-native-product-r12 scaffold
python3 tools/m1.py --target demo11-native-product-r12 generate
python3 tools/m1.py --target demo11-native-product-r12 build
python3 -m unittest tests.test_product_r12 -v
```
