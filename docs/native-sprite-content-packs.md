# Custom sprite content packs

## Question

Can the data of a custom sprite live outside the cartridge image, as level data
and music data do? The proposed data holds the code and the graphics.

## Answer

Yes. The project already delivers two of the four parts of a custom sprite from
external files. Graphics are the missing part, and the delivery mechanisms for
graphics already exist.

A custom sprite needs four parts: the code block, the record, the shared
engine dependencies and the graphics.

| Part | Delivery | Status |
| --- | --- | --- |
| Code block | Executable bank pack, one bank per pack | In use by 36 sprite modules |
| Record | 16-byte table patch in the image | In use |
| Shared tables | Pinned image bytes | In use |
| Graphics | See below | Open |

## Graphics delivery options

| Option | Mechanism | Change to the game |
| --- | --- | --- |
| A. ROM range | The region provider replaces a byte range | None, if the game reads the compressed stream from the image |
| B. Fixed bank | A graphics pack is mapped at a fixed bank | The graphics pointer must name the pack bank |
| C. Decoded VRAM | A hook writes reviewed words into VRAM | A small native hook at room entry |

The region provider already replaces byte ranges for the music pack. The sprite
9E pilot already mounts a graphics pack at a fixed bank. Option C was tested on
2026-11-05.

## Experiment: decoded VRAM injection

The test packs the donor OBJ region `0x6000..0x7FFF` as a list of
(address, count, words). The build injects a room-scoped writer. The capture
runs room `175` with `BM_VRAM_PATCH_ROOM=0x175`.

Result:

- the candidate VRAM became byte-identical to the donor in the OBJ region;
- 1,206 bytes changed;
- the change persisted in the later samples;
- the framebuffer did not change.

Conclusion: the delivery mechanism works. The slot `99` frame difference is
not caused by the VRAM tile content.

## Proposed pack

One manifest per sprite slot. The manifest pins the code, the record and the
graphics. The runtime mounts the files through the shared content loader.

```json
{
  "schema": 1,
  "id": "sprite99-content",
  "slot": "99",
  "donor": "demo-only-1",
  "record": {"offset": 1608706, "before": "...", "after": "..."},
  "code": {"pack_file": "sprite99-code.bin", "address": "8BA6FC",
           "size": 1391, "sha256": "..."},
  "graphics": {
    "kind": "vram",
    "pack_file": "sprite99-gfx.bin",
    "ranges": [{"vram": "6000", "words": 4096, "sha256": "..."}],
    "rooms": ["174", "175", "176"],
    "trigger": "room-enter"
  },
  "open": ["frame parity with the donor"]
}
```

Rules:

1. One manifest holds one slot.
2. Every payload has a size and a SHA-256.
3. The graphics ranges must not overlap another slot or a mapped bank.
4. The trigger is a room or a sprite spawn, never a global change.
5. The build refuses a manifest that does not match its pins.

## Recommended order

1. Use option A when the compressed graphics stream is known. It needs no game
   code change.
2. Use option C when the stream is absent or generated. The 2026-11-05 test
   proves the mechanism.
3. Keep the code in executable packs. Do not move code into the image again.
4. Review the graphics dependency of each slot before a pack: tiles, palette,
   OAM timing and the room scope.

## Open items

- The cause of the slot `99` frame difference stays open. The VRAM content is
  excluded.
- No slot has a reviewed graphics pack yet. Slot `99` is the first candidate
  after the frame difference is resolved.
- The hook is diagnostic. A production hook needs a manifest, a hash check and
  a room scope.
- The test gates are not written: pack hash, range overlap, room scope and a
  donor frame comparison.
