# Corridor graphics handoff

> Superseded for room 190 by [the verified r3 background repair](native-corridor-background.md).
> The map/pixel byte roles below were reversed: the actual map is equal.
> Resource `1E5` was missing; r3 restores it. Remaining work is the 191/192 font.


This document gives a new agent the state of the corridor graphics work for rooms
190, 191 and 192. It records what is correct, what is defective, which ideas I rejected and
which action comes next.

## 1. The deliverable that works

Target `demo11-native-product-r2` is a verified build. It holds the product ROM
plus two patches: the mazo extended graphics `1E6` stream and its pointer.

| Item | Value |
| --- | --- |
| Target | `demo11-native-product-r2` |
| ROM digest | `d7a36d90...` |
| Patch count | 2 |
| Tests | `tests/test_product_r2.py`, 6 tests |
| Full suite | 313 tests, all pass |

The build shows a clean boss face, the cloud layer and the health bar in room 190.
The product baseline shows a broken boss face in the same room.

Do not edit the product baseline. Add a descendant target.

## 2. How to play

```sh
# The verified build.
python3 tools/play_native_target.py --target demo11-native-product-r2

# The accepted baseline, for comparison.
python3 tools/play_native_target.py --target demo11-native-product

# Jump to one room with the practice cheats.
python3 tools/play_native_cheats.py --target demo11-native-product-r2 --room 0x190
python3 tools/play_native_cheats.py --target demo11-native-product-r2 --room 0x191
python3 tools/play_native_cheats.py --target demo11-native-product-r2 --room 0x192
```

The `--room` option writes the room number and enters the level. A room write does
not reload the graphics. Read section 6 before you trust a frame from this path.

## 3. The defect, with measurements

Room 190 is a Mode 7 boss room. The product frame holds the correct sky colours,
the correct clouds, the correct boss and the correct floor. It also holds a set of
thin vertical lines over the sky. The mazo frame holds the same elements and no
lines.

The lines come from the Mode 7 map. The map is the word array at VRAM bytes
`0x0000` to `0x7FFF`, and the cell value is the high byte of each word.

| Build | Most used map tiles | Row 3, first 16 cells |
| --- | --- | --- |
| product | `16`, `0`, `15`, `31`, `26` | `0 0 15 0 0 15 0 15 0 0 15 0 0 15 0 15` |
| mazo | `16`, `0`, `9`, `7`, `5` | `0 3 9 5 7 12 12 12 0 4 9 7 12 11 11 11` |

The product map repeats two tile numbers in a short cycle. One cycle gives one
line. The mazo map holds a long run of decreasing numbers, which gives a smooth
field.

The product map is stable. Two different entries give 16036 equal cells of 16384.

## 4. What is equal in both ROMs

These checks found no difference. Do not repeat them.

| Item | Result |
| --- | --- |
| Room 190 level stream | byte equal |
| Level header tables at index `0x30` and `0x190` | equal on all nine tables |
| Corridor graphics `0xC4` and `0xAF` | byte equal |
| Base graphics `0x00` to `0x31`, decoded | equal |
| Extended graphics `0xC1` | byte equal |
| Graphics selectors `$0D9A`, `$0D9B`, `$0D9D` | equal |
| Tile base `bg_tile_adr` | equal, 1031 |
| Registers `bgsc` and `tm` | equal |
| Room metadata for 190, 191, 192 | equal, `01 00 FF...` |

## 5. Ideas that I rejected

| Idea | Test | Result |
| --- | --- | --- |
| Missing corridor graphics | graphics data comparison | the data is present and equal |
| Wrong graphics selectors | register comparison | equal |
| Wrong level header | patch the nine header bytes of index `0x6A` | the registers do not change |
| Wrong translevel | room 190 content copied into room `0x10C`, entered at translevel `0x30` | the lines stay |
| Empty extended graphics slots | fill `0x0BE`, `0x0D9`, `0x0DA` from mazo | no pixel differs |
| Renderer fault alone | whole-image VRAM pack | the frame changes, so the renderer reads VRAM |

The translevel test is the important one. Room 190 content under translevel
`0x30` still shows the lines. The level header therefore does not select the map.

## 6. Traps that cost time

1. A room write does not reload the graphics. A frame from a room write can hold
   the previous scene.
2. A mazo capture that sends no input dies in room 190. The death animation is a
   dark blue swirl. It looks like a background. Read the mode and the room before
you compare a frame.
3. The message box in rooms 191 and 192 is a window, not a Layer 3 picture. It
   must hold Japanese text.
4. The reference host writes VRAM and WRAM. It does not write CGRAM, because the
   stock core has no debug exports. A palette comparison needs a patched core.
5. The Mode 7 map and the Mode 7 character data share the same VRAM words. A pack
   cannot replace the map alone.
6. Target directory names use a sanitised title. `R190in10c` becomes `R190In10C`.
   A wrong binary name gives a missing-file error at the generate step.

## 7. Tools that work

| Tool | Use |
| --- | --- |
| `tools/play_native_target.py` | start a native target |
| `tools/play_native_cheats.py` | start a target and jump to a room |
| `tools/probe_reference.py` | capture the reference host |
| `tools/fb_to_png.py` | convert a frame dump to PNG |
| `tools/render_vram_tiles.py` | render a VRAM range as a tile sheet |
| `tools/m1.py` | scaffold, generate, build and run a target |
| `BM_DIAG_VRAM_PATCH` | apply a room scoped VRAM pack at run time |

The VRAM pack format is a run list. It starts with a 32-bit run count. Each run
holds a 16-bit start word, a 16-bit run length and a 16-bit value.

## 8. How to get a live mazo frame of room 190

The mazo build keeps the boss health in its own bytes. These bytes fall as the bar
empties:

| Address | Entry value | Value before death |
| --- | --- | --- |
| `0x0D85` | 64 | 0 |
| `0x0D8F` | 64 | 0 |
| `0x0381` | 72 | 10 |
| `0x01DF` | 72 | 10 |

Write those bytes back every 30 frames. The player then stays in mode `0x14`,
room `0x190`, for more than 720 frames.

```sh
python3 tools/probe_reference.py --manifest config/mazo-donor.json \
  --rom local/content-versions/mazo/rom.sfc \
  --script recomp/inputs/mazo-190-hplock-fixture.script --capture mhp
```

Frame `local/captures/mhp/h24` is a good reference. The image is at
`local/reports/screenshots/room190-mazo-live.png`.

## 9. The next action

Find the source of the Mode 7 map. Three checks are open:

1. Trace the writes to VRAM words `0x0000` to `0x3FFF` during the room 190 load.
   The ROM read trace sees reads only. A write trace on the PPU port is the direct
   method.
2. Compare the two maps against every graphics and level block in both ROMs. A
   match gives the source block.
3. Decompress the mazo map and search for it as a byte sequence in the product ROM.
   A missing block gives the transfer.

The second and third checks need no playtest. Start there.

## 10. Rooms 191 and 192

The message window in these rooms must draw Japanese text:

```
ゴールした そのなかに
モンスターが ？
```

The product draws a repeat of two or three level shapes instead. So the font is
not at the character base that the window uses.

These checks found nothing:

- Base graphics `0x00` to `0x31` are equal in both ROMs.
- Extended graphics `0x0BE`, `0x0D9` and `0x0DA` change no pixel.
- No font block loads when the window opens. The largest new read is 73 bytes.
- A glyph search over 2305 decoded RATS blocks of mazo found no match. The glyph
  bytes came from a screenshot, so the grid alignment is an estimate.

The next check is the character base that the window uses, and the level load that
must fill it.