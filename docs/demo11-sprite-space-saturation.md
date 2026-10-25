# Custom sprite space saturation

Date: 2026-10-26. This note records why the remaining custom sprites do
not install.

## State

The chain `demo11-sprites-room8f-boss` holds 121 custom records.
36 placed sprites still have no record. The remaining code blocks have sizes
from 1009 to 14550 bytes.

## Blocker analysis

A sprite needs a free window at its low 16 bits in a bank from `0x20`
to `0x3F`. The analysis checks all 32 banks for each sprite.
Every window fails the allocator. No window overlaps a RATS block. The
windows hold raw data outside the RATS blocks.

The allocator can move a graphics asset only when a free run holds the
asset. The largest allocatable run is 2528 bytes. Many assets are larger.
The 19387-byte run at `0x27B448` holds two protected RATS blocks
(`0x278000`, 32768 bytes and `0x280000`, 6144 bytes). Both
blocks also exist in the demo 1-1 baseline.

## Orphan blocks

Two installed blocks no longer have a record. The record restores for
sprites `0x42` and `0x3D` made them orphans:

| Sprite | Block | Size |
| --- | --- | --- |
| `0x42` | `0x107BF9` | 772 |
| `0x3D` | `0x1EFC1B` | 756 |

No current sprite window becomes free when these two blocks are removed.
The blocks stay for a later reclamation pass.

## Next options

1. Find the pointer tables for the raw data in the blocked windows. Move
   that data, then install the sprite.
2. Deduplicate installed code blocks with equal bytes. Re-point the records
   and reclaim the duplicate windows.
3. Change the remaining sprite code to run at a different low 16 bits.
   This step needs a manual review of the absolute references.
