# Room 167 custom sprite graphics: the wrong graphics ID in the object slot

## Result

Product r22 supplies the correct object tiles for room 167. The user accepted
the rendered result on 2026-11-05.

## Cause

`OBSEL` is `3` in room 167. Bits 0 to 2 of `OBSEL` give the object character
base, which is word `0x6000` or byte `0xC000`. Object tile `N` starts at byte
`0xC000 + N*32`.

The four slot `34` actors use object tiles `384`, `386`, `416` and `418`.
Those tiles start at bytes `0xF000`, `0xF040`, `0xF400` and `0xF440`.

| Image | Data at bytes `0xF000..0xFFFF` |
| --- | --- |
| product r20 | graphics `02` |
| cheap-demo reference | graphics `11` |

Graphics `11` holds the same bytes in both images. Graphics `02` does not.
The product image therefore loads the wrong graphics data in the slot that
the room actors read.

## Correction to an earlier note

An earlier note compared these tiles at byte `N*32` from the start of VRAM.
That is the wrong address. It reported that the tiles matched the reference.
The tiles do not match at the correct address.

## Fix

Product r22 descends from r21 and mounts a second external graphics pack.
The pack writes graphics `11` into VRAM words `0x7800` to `0x7FFF` when the
game enters room `167`. The image bytes do not change.

| Item | Value |
| --- | --- |
| Manifest | `config/native-content/sprite-graphics-167-obj.json` |
| Pack size | 4104 bytes |
| Pack SHA-256 | `85491c48d953b8a0ad15d61817b3f6bdb8d90201c6e6e6c44f53c9a3aff70562` |
| Room | `167` |
| Range | words `7800` to `7FFF` |
| Persist | true |

The pack needs no donor image. Graphics `11` is identical in the product
image and the cheap-demo image, so the pack takes the bytes from the product
image.

## Verification

`tools/qualify_product_sprite_graphics_167.py` checks these items:

- the r22 image identity and the r21 lineage;
- both packs and their pins;
- the pack applied count in each named room;
- the room 167 object slot equals the reference capture;
- the parent object slot does not equal the reference capture;
- the room 167 pack writes no byte below its range;
- the room 175 object range still matches its accepted donor measurement.

| Measurement | Result |
| --- | ---: |
| Applied frames in room `167` | 179 |
| Applied frames in room `175` | 514 |
| Object slot changed bytes in room `167` | 2766 |
| Object slot matches reference | true |
| Parent object slot matches reference | false |
| Bytes written below the room `167` range | 0 |
| Room `175` object bytes against the donor | 16 |

Report: `local/reports/product-r22-sprite-graphics.json`.

## Deferred issues

- The room `167` background still differs from the cheap-demo reference.
  Only the object character slot is supplied.
- The reference capture comes from a core that does not export object
  attribute memory, palette memory or PPU registers. The donor tile indices
  and palettes are unknown.
- Room `173` is not covered. Its level block differs from the product block
  and it leaves gameplay after frame `256`.

## Reproduction

```sh
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap;
native_sprite_gap.prepare('demo11-native-product-r22')"
python3 tools/m1.py scaffold --target demo11-native-product-r22
python3 tools/m1.py generate --target demo11-native-product-r22
python3 tools/m1.py build --target demo11-native-product-r22
python3 tools/m1.py native --target demo11-native-product-r22 \\
  --script recomp/inputs/native-room167-direct.script \\
  --capture r22-room167-v1
python3 tools/qualify_product_sprite_graphics_167.py \\
  --output local/reports/product-r22-sprite-graphics.json
```

## Evidence

- `local/captures/r22-room167-v1`
- `local/captures/r22-room175-v1`
- `local/captures/product-r20-room167-direct-v1`
- `local/captures/cheap167-pipe-ref-v1`
- `recomp/inputs/native-room167-direct.script`