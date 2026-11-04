# External sprite graphics provider

## Result

Product r21 mounts the external sprite graphics provider. One reviewed pack
writes the donor VRAM into the candidate when the game enters room `175`.
The image bytes do not change.

| Item | Value |
| --- | --- |
| Target | `demo11-native-product-r21` |
| Parent | `demo11-native-product-r20` |
| ROM | `f4185fe22f57c66c338b800bbe423dcd915860c87cc2ec395baa7236cad5e567` |
| Binary | `0d70f479b2c477211f845636e1c716850f949877bd6215dab1904e930cf47973` |
| Config | `2252c6c6c22887f0aab5cdc5c86e9d87f1824000f3ccb8b79f4e8ac830d05677` |
| Manifest | `55314e2ac8eeda38ea54bcd37aa69acef05612a1db0bd7c8e5cb56df4454451c` |
| Pack | 8,200 bytes, `f1c825da2c3008c19ba3dc00bc89937b0d68bdf4b8bb894f20f44e131d3d1ed4` |
| Qualification | `486478a39081684e07af9bde20b74cc58d9f6d79778948f6b8afb462d3c6ab26` |

The ROM SHA-256 equals the r20 ROM SHA-256. The provider is a runtime feature,
not an image change.

## Mechanism

| Part | File | Role |
| --- | --- | --- |
| Pack builder | `tools/prepare_sprite_graphics_pack.py` | Turns a reviewed VRAM capture into a pack |
| Manifest review | `tools/native_sprite_graphics.py` | Validates the manifest, writes the header |
| Runtime | `recomp/native_sprite_graphics.c` | Mounts the packs, writes the ranges |
| Cartridge patch | `tools/patch_sprite_graphics.py` | Adds the mount and the tick call |

The runtime mounts every pack at content load. It reads one byte of room state
per frame. When the game is in gameplay mode and enters a room that the
manifest names, it writes the reviewed VRAM ranges once. A room that the
manifest does not name is never written.

The pack holds a range count and, for each range, a word address, a word count
and the words. The manifest holds the size, the SHA-256, the slot and the
room list.

## Qualification

| Check | Result |
| --- | --- |
| Pack size and SHA-256 | Match the manifest |
| Applied count in room `175` | 1 |
| Applied count in room `154` | 0 |
| Candidate VRAM inside the range, against the donor | 0 bytes differ |
| Candidate VRAM inside the range, against the parent | 1,206 bytes differ |
| Candidate VRAM outside the range, against the parent | 0 bytes differ |
| Room `154` VRAM, against the parent | Identical |

The provider therefore delivers the reviewed VRAM with a room scope and no
spill.

## Frame result

The candidate frame in room `175` is identical to the parent frame. The
reviewed VRAM does not change the picture.

The donor frame still differs from the candidate frame in 3,512 bytes. The
provider is correct, and the picture difference is a separate problem.

The next diagnostic must explain why the same VRAM, the same OAM and the same
BG registers produce a different frame. Candidates: the BG tilemap, a renderer
state that the capture does not record, or a sprite-to-BG interaction.

## Limits

- One pack exists. It covers room `175` only.
- The frame difference stays open.
- No game code was changed. The provider is a native adaptation.
- The qualification uses assisted room entry. It is not a route or a clear.
- The provider writes VRAM after the room starts. A later game upload can
  overwrite the range; the current check shows it persists to frame 512.

## Reproduction

```sh
python3 tools/prepare_sprite_graphics_pack.py --slot 99 --id sprite-graphics-99 \
  --donor demo-only-1 --capture donor175-native-oam-v2 --frame f512 \
  --ranges 3000:1000 --rooms 175 \
  --scope 'Reviewed decoded VRAM for custom sprite 99 in room 175.' \
  --manifest config/native-content/sprite-graphics-99.json \
  --output-directory local/native-modules/sprite-graphics-99
python3 tools/prepare_product_sprite_graphics.py
python3 tools/m1.py scaffold --target demo11-native-product-r21
python3 tools/m1.py generate --target demo11-native-product-r21
python3 tools/m1.py build --target demo11-native-product-r21
python3 tools/m1.py native --target demo11-native-product-r21 \
  --script recomp/inputs/native-modern-175.script \
  --capture product-r21-room175-gfx-v1
python3 tools/qualify_sprite_graphics_packs.py \
  --output local/reports/product-r21-sprite-graphics.json
python3 -m unittest tests.test_sprite_graphics_packs
```

## Next work

1. Explain the frame difference with a BG tilemap compare.
2. Add a manifest per slot that needs graphics.
3. Add the pack hash and the room scope to the product verification receipt.
