# Mario HP bar in room 0x128

Date: 2026-10-26. The user reports that room `0x128` has no Mario HP bar.
The room already fills the legacy row `$7F:FFE0..FFEF` and sets `$7F:FFDF`.
Demo 1-1 omits the legacy HUD upload for it, exactly like rooms `0xBC` and `0xCC`.

## Change

The recipe `demo11-hp-room128` extends the accepted HP shim. It
installs an 88-byte routine at `$40:2308` with a RATS header at
`$40:2300` and repoints the `$00:8DE1` hook. The new routine:

1. Calls the existing shim at `$3E:A008`.
2. Accepts rooms `0x00BC`, `0x00CC` and `0x0128`.
3. Requires game mode `0x14` and a nonzero `$7F:FFDF` flag.
4. Uploads the sixteen legacy characters to VRAM word `$5028` through DMA channel 1.

- Base: `demo11-sprites-cc`
- ROM: `d41eda4d1014f1796164fff5490ee840ed81908379c8b14f618c5e39f1b909a9`
- Native binary: `f3975d6ff4bbc02fabc3a84ae253c5e3c4cbfe75bf10875a6e5b22ec277b73d6`

## Evidence

A map-entry capture of translevel `0x04C` reaches room `0x128` in mode 
`0x14`, with `$7F:FFDF = 1` and the legacy row populated.
The fixed capture differs from the base only in the HUD. The gameplay field
is byte-identical. VRAM word `$5028` receives the buffer characters; the
DMA writes `VMDATAL` only, so the existing attribute bytes stay unchanged.

- `tools/qualify_demo11_hp_room128.py` passes.
- Whole-line audit: 889,012 changed bytes, zero unexpected.
- Suite **63/63**; space budget passes.

## Limits

- The capture uses a map entry, not a full course traversal.
- Only room `0x128` is added. Other rooms with the same legacy row
  would need their own reviewed additions.
