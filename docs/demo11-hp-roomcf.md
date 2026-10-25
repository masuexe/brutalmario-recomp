# Mario HP bar in room 0xCF

Date: 2026-10-26. The user reports that room `0xCF` has no Mario HP bar.
The room fills the legacy HP row `$7F:FFE0..FFEF` and sets `$7F:FFDF`.
The chain omits the legacy HUD upload for it. This recipe extends the accepted
HP shim to room `0xCF`.

## Change

The recipe `demo11-hp-roomcf` installs a 98-byte routine at
`$40:2508` with a RATS header at `$40:2500`. It repoints the
`$00:8DE1` hook. The routine accepts rooms `0xBC`, `0xCC`,
`0x128`, `0x146` and `0xCF`. The other conditions and the
DMA upload stay the same.

- Base: `demo11-sprites-remaining-free`
- ROM: `925b004a02d195a6d12cc14220aa79ab1d88eae1e05236d519acfbf0e85e2aff`
- Native binary: `476247ce0671bc8bf6b4b5f389a7bdc9dafde4993901efa689bd107789eb1558`

## Evidence

A room-exit fixture enters room `0xCF` in game mode `0x14`. The
legacy flag is set and the row is populated. The fixed capture changes the
HUD only. The gameplay field is byte-identical. VRAM word `$5028` receives
the row characters; the attribute bytes stay unchanged.

- `tools/qualify_demo11_hp_roomcf.py` passes.
- Whole-line audit: 930,252 changed bytes, zero unexpected.
- Suite **68/68**; space budget passes.

## Limits

- The capture uses a room-exit fixture, not a full course traversal.
- The user must playtest the room `0xCF` HP bar.
