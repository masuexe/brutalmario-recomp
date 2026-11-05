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

The object tiles that the actors use are `384`, `386`, `416` and `418`. Their
bytes in the product capture are identical to the `cheap-demo` reference
capture. The sprite art is therefore present.

The room frame differs from the `cheap-demo` reference in 25,880 pixels.

## Room 173

One slot `07` actor spawns at `(200,96)` and moves to `(200,231)`. It uses
object tiles `0` and `2`, and both hold art.

The room leaves gameplay after frame `256`: mode `0x0B` then `0x0E`. The
`cheap-demo` and `demoOnly1` images hold the same sprite list, but the
`cheap-demo` level block differs from the product block in 826 bytes.

## What the survey does not establish

- The frame comparison pairs a `cheap-demo` reference frame with a product
  frame at a different frame index. The pixel count is not a parity claim.
- Injecting the full `cheap-demo` VRAM for room `167` changed the stored VRAM
  but not the rendered frame. The remaining difference is outside the
  injected range, most likely the object attribute table and the actor
  positions.
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
