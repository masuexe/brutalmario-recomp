# Native room 151 phase music

## Problem

The room 151 boss uses the sprite 9C program. That program requests two music changes.

- When the second phase starts, the boss changes into another boss. The program writes song `$23`.
- When the second phase is defeated, the program writes song `$22`.

The expected songs are `$A5` (The Fierce Battle) for the second phase and `$AD` for the defeat.
Slots `$23` and `$22` hold valid payloads, but they are not the intended songs.
The values `$23` and `$22` come from the legacy donor engine. The music IDs are version-local.

## Fix

Target `demo11-native-product-r11` adds the recipe
`config/native-content/sprite9c-9f-phasebgm-module.json`. The recipe copies
`sprite9c-9f-module.json` and adds two code patches.

| Donor site | Before | After | Event |
| --- | ---: | ---: | --- |
| `22:8E3A` | `23` | `A5` | Second phase |
| `22:92FA` | `22` | `AD` | Second phase defeat |

The transition routine at `22:8DE2` stops the current sprite and calls the init
routine at `22:8E22`. That init routine writes the first song.
The defeat animation routine near `22:92E6` writes the second song.
The recipe leaves the first write at `22:824A` (`$0B`) unchanged. The user did
not report that event.

The ROM is identical to r10 (`d29b121e...2f552`). Only the external module pack
changes. Pack `sprite9c-code.bin` stays in bank `9F` and stays 12412 bytes. Its
adapted SHA-256 is `1244dd6b76d44fd059ed95137afa99bc796f3e3644062c0aeeb02562db5ee00d`.

## Verification

`tests/test_product_r11.py` checks these items.

- The r11 ROM equals the r10 ROM.
- The config declares the `sprite-9c-phase-music` adaptation.
- The pack differs from r10 at only `0xE3A` and `0x12FA`.
- The new bytes are `A5` and `AD`. The old bytes are `23` and `22`.
- Song slots `A5` (2881 bytes) and `AD` (2152 bytes) are present.

Captures `r11-151`, `r11-190`, `r11-191` and `r11-192` match the r10 captures
byte for byte. That covers the window before the phase change.

## Limits

The phase change needs player damage. The test scripts do not damage the boss.
So automation does not exercise the two music writes. You must playtest the
second phase and the defeat.

## Reproduction

```sh
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r11')"
python3 tools/m1.py --target demo11-native-product-r11 scaffold
python3 tools/m1.py --target demo11-native-product-r11 generate
python3 tools/m1.py --target demo11-native-product-r11 build
python3 -m unittest tests.test_product_r11 -v
```
