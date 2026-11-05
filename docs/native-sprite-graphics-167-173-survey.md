# Room 167 and 173 custom sprite graphics: first survey

## Scope

`local/r19-sprite-recheck.md` class B names rooms `167`, `16A` and `173` as
rooms where the custom sprite record is not a placeholder. The user note says
the sprite works but the custom tiles are absent.

This survey checks that claim against the current product line. It does not
install a graphics pack and it does not claim a fix.

## Records

| Slot | Rooms | Product r20 record | Donor |
| --- | --- | --- | --- |
| `34` | `167`, `16A` | `013600003f831964dbeb3e0eed3e0000` | `cheap-demo` |
| `07` | `173` | `013601063f031964d3f53dddf53d0000` | `cheap-demo` |

Both records hold a program. The bank byte differs from the donor because the
product line maps the code from an external pack. The slot is not a
placeholder, so a record install is not the missing part.

## Room 167

Four slot `34` actors spawn and move in room `167`. At frame `512` they hold
positions `(43,361)`, `(193,361)`, `(129,207)` and `(16,320)`.

The object tiles that the actors use are `384`, `386`, `416` and `418`.

An earlier draft of this note compared those tiles at byte `N*32` from the
start of VRAM. That is the wrong address. `OBSEL` is `3`, so the object
character base is byte `0xC000` and tile `N` starts at `0xC000 + N*32`.
See [native-sprite-graphics-167-fix.md](native-sprite-graphics-167-fix.md)
for the corrected measurement and for the difference that the two images hold.

## Room 173

One slot `07` actor spawns at `(200,96)` and moves to `(200,231)`. It uses
object tiles `0` and `2`, and both hold art.

The room leaves gameplay after frame `256`: mode `0x0B` then `0x0E`. The
`cheap-demo` and `demoOnly1` images hold the same sprite list, but the
`cheap-demo` level block differs from the product block in 826 bytes.

## What the survey does not establish

- The frame comparison pairs a `cheap-demo` reference frame with a product
  frame at a different frame index. The pixel count is not a parity claim.
- The reference capture comes from a core that does not export object
  attribute memory, palette memory or PPU registers. The donor tile indices
  and palettes are therefore unknown.
- The two frames come from different frame indices and different scroll
  positions. A pixel count between them is not a parity measurement.
- Room `173` leaves gameplay, so no graphics conclusion is possible there
  yet.

## Reproduction

```sh
python3 tools/m1.py native --target demo11-native-product-r20 \\
  --script recomp/inputs/native-room167-direct.script \\
  --capture product-r20-room167-direct-v1
python3 tools/probe_reference.py --manifest config/cheap-demo-donor.json \\
  --rom local/content-versions/cheap-demo/rom.sfc \\
  --script recomp/inputs/native-room167-entry.script \\
  --capture cheap167-pipe-ref-v1
```

## Next work

1. Capture both hosts at the same frame index and with the same fixture
   before any pixel comparison.
2. Find why room `173` leaves gameplay after frame `256`.
3. Compare the object attribute table of room `167` against the reference.
