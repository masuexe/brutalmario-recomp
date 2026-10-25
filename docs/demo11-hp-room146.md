# Mario HP bar in room 0x146

Date: 2026-10-26. A scan of all capture dumps found the rooms that fill the
legacy HP row `$7F:FFE0..FFEF` and set `$7F:FFDF`:

| Room | State |
| --- | --- |
| `0x009` | Already uploaded by the accepted recipient/fuel shim. |
| `0x0BC` | Fixed by `demo11-hp-bars`. |
| `0x0CC` | Fixed by `demo11-hp-bars`. |
| `0x128` | Fixed by `demo11-hp-room128`. |
| `0x146` | Fixed by this recipe. |

No other captured room sets that flag with a nonempty row.

## Change

The recipe `demo11-hp-room146` extends the accepted HP shim. It
installs a 93-byte routine at `$40:2408` with a RATS header at
`$40:2400` and repoints the `$00:8DE1` hook. The routine
accepts rooms `0xBC`, `0xCC`, `0x128` and `0x146`.
Its other conditions and the DMA upload stay the same.

- Base: `demo11-hp-room128`
- ROM: `616074b46151499792991d0728f0e10b88f3dc06896dac0a74c7e7e09b36f8f7`
- Native binary: `a831eeebd523a4422f263c7d4e5a3b28a4339a77ed7ed6855d3c94cb5bcefbd0`

## Evidence

A map-entry capture of translevel `0x06A` reaches room `0x146` in
mode `0x14`, with the legacy flag set and the row populated.
The fixed capture changes the HUD only. The gameplay field is byte-identical.
VRAM word `$5028` receives the row characters; the attribute bytes stay
unchanged because the DMA writes `VMDATAL` only.

- `tools/qualify_demo11_hp_room146.py` passes.
- Whole-line audit: 889,105 changed bytes, zero unexpected.
- Suite **64/64**; space budget passes.

## Limits

- The capture uses a map entry, not a full course traversal.
- The room scan covers captured rooms only. Unvisited rooms need a capture
  before any claim.
