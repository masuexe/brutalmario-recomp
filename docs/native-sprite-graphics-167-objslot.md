# Room 167 sprite graphics: the object slot holds a different graphics ID

## Scope

The user reports that room 167 shows the wrong sprite tiles and that the sprite
logic works. This note records what the images hold. It does not claim a fix.

## The object slot

`OBSEL` is `3` in room 167. Bits 0 to 2 of `OBSEL` give the object character
base. The base is word `0x6000`, which is byte `0xC000`. Object tile `N` then
starts at byte `0xC000 + N*32`.

The four slot `34` actors use object tiles `384`, `386`, `416` and `418`.
These tiles start at bytes `0xF000`, `0xF040`, `0xF400` and `0xF440`.

## What each image loads there

| Image | Data at bytes `0xF000..0xFFFF` |
| --- | --- |
| product r20 | graphics `02` of the product image |
| cheap-demo reference | graphics `11` of the cheap-demo image |

Graphics `11` has the same bytes in both images. Graphics `02` does not.

```text
r20   graphics 02 at 0xF000: tile 384 = 000001000000210023021b0a35273727...
cheap graphics 11 at 0xF000: tile 384 = 00000000000000000000000000000000...
```

The two images therefore place different data in the slot that the actors read.

## Injection test

A reviewed pack wrote graphics `11` into the object slot of the product image.
The stored VRAM then matched the reference byte for byte in that range.

| Measurement | Result |
| --- | ---: |
| Changed framebuffer pixels | 4623 |
| Pixels that converged to the reference | 0 |

The actor art changed. It did not become the reference art. The rendered
result showed brick tiles where the product image shows dark shapes.

## Why the comparison cannot close yet

- The reference capture comes from the `snesref` core. That core does not
  export object attribute memory, palette memory or PPU registers. The donor
  object attribute table is therefore unknown.
- The donor frame is at frame `256` after entry. The product frame is at frame
  `200`. The scroll positions and actor positions differ.
- A pixel count between these two frames is not a parity measurement.

## What the evidence does establish

1. The object slot holds graphics `02` in the product image.
2. The reference image holds graphics `11` in the same slot.
3. Writing graphics `11` into that slot changes the actor art.
4. Writing that data does not reproduce the reference art.

## Next work

1. Capture the donor with a core that exports object attribute memory and
   palette memory, so the donor tile indices and palettes are known.
2. Compare the donor and product frames at the same frame index and the same
   scroll position.
3. Find the code that selects graphics `02` for the object slot in room `167`.

## Evidence

- `local/captures/product-r20-room167-direct-v1`
- `local/captures/cheap167-pipe-ref-v1`
- `recomp/inputs/native-room167-direct.script`
- `recomp/inputs/native-room167-entry.script`