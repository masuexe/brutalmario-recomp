# Remaining free-window custom sprites

Date: 2026-10-26. A scan of all 512 rooms found 95 custom placements whose
record was still the default. Fifteen of them had donor code that fits a free
bank window without relocations. This batch ports those fifteen sprites.

## Batch

- Base: `demo11-sprites-cc-lobby-full`
- Target: `demo11-sprites-remaining-free`
- Sprites: `0x1A`, `0x27`, `0x3D`, `0x4F`, `0x51`, `0x53`, `0x5C`, `0x6B`, `0x6D`, `0x70`, `0x73`, `0x77`, `0x7B`, `0x7D`, `0x8B`
- ROM: `fa986111901e2114c4ff411134e8616351fa6d76f09107ded19e4be368738aec`
- Native binary: `62d1c8b6bd946d9adddbf718f168eac48021f4ba8a6bb072c5aec7ea4f851c10`

Rooms for each sprite stay in the recipe. Four sprites had a window conflict
in this batch and stay open: `0x42`, `0x52`, `0x6F`
and `0x87`. Their windows need reviewed relocations.

## Evidence

Room-exit fixtures enter rooms `0x66`, `0x89`, `0x62`, `0x7C`,
`0xA0`, `0xA1`, `0xA7`, `0x9C` and `0x96`.
Rooms `0x89`, `0x62`, `0x96` and `0x7C` change.
The room frame shows the ported sprites. Rooms `0x89`, `0x62` and `0x96`
keep an identical HUD. Room `0x7C` changes its HUD because sprite `0x6D`
owns HUD content there. The other sampled rooms stay unchanged because the
sprite is idle or off screen in the capture window.

- `tools/qualify_demo11_sprites_remaining_free.py` passes.
- Whole-line audit: 930,155 changed bytes, zero unexpected.
- Suite **67/67**; space budget passes.

## Limits

- The fixtures use a room-exit poke. They qualify room entry, not a complete
  traversal.
- The user must playtest the ported sprite rooms.
- Ninety-five missing placements remain in total. Some need reviewed
  relocations, and some need code from a newer donor version.
