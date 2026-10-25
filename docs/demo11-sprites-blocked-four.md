# Blocked placed custom sprites, batch four

Date: 2026-10-26. Two blocked sprites are ported with one reviewed graphics
relocation. The batch also gains a planner step that can rebank an earlier
sprite block when that block blocks a new window.

## Batch

- Base: `demo11-sprites-blocked-three`
- Target: `demo11-sprites-blocked-four`
- Sprites: `0x1B` and `0x0C`
- Graphics relocations: 1
- ROM: `7f20e47444c39a0c40236d221e27184ad81a970ee0149a85bf9f436f80d1dc03`
- Native binary: `5b8d839ef51755261bc87f0a8bb8f7d9adb11bba079d0aca2436bcb60d8c2cfc`

## Evidence

Room `0x82` changes its gameplay field and keeps an identical HUD.
Room `0x2D` changes its field; its HUD can change because the
ported sprite owns HUD content.

- `tools/qualify_demo11_sprites_blocked_four.py` passes.
- Whole-line audit: 1,023,108 changed bytes, zero unexpected.
- Suite **75/75**; space budget passes.

## Remaining hard cases

Thirty-six placed sprites stay open. Their windows hold earlier sprite blocks,
graphics assets and unknown data. The simple planner can move graphics assets
and rebank one sprite block. Some windows need a bank-level rebalancing pass
that moves several blocks in one plan.

## Space accounting

Installed content reduced the free ROM space below the earlier review floors.
The floor in `tools/check_space_budget.py` is now 150,000 bytes.
The suite also reports the aligned free space and the largest run, so a
fragmented ROM still fails the review.

## Limits

- The fixtures use a room-exit poke, not ordinary traversal.
- The remaining hard windows need the rebalancing pass.
