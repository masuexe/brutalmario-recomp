# Orphan sprite block cleanup

Date: 2026-10-26. The native record restores for sprites `0x42` and
`0x3D` left two installed code blocks with no record. This target zeroes
both blocks.

## Blocks

| Sprite | Block | Size |
| --- | --- | --- |
| `0x42` | `0x107BF9` | 772 |
| `0x3D` | `0x1EFC1B` | 756 |

Two code patches replace each block with zero bytes. No record points to
either block.

- Base: `demo11-sprites-room8f-boss`
- ROM: `eccde6612343e9513e6903264f21b80d3a9a02d7f11199100e5907531232ff40`
- Native binary: `d79f5940d04f2a40ae82cc30c858c74f10d11c71ab201269f8a638b28e815985`

## Evidence

- Room `0x8F` and room `0x13C` frames are byte-identical to
  the demoOnly1 boss chain.
- `tools/qualify_demo11_sprites_orphan_cleanup.py` passes.
- Whole-line audit: 1,027,211 changed bytes, zero unexpected.
- Suite **78/78**; space budget passes.

## Limits

The cleanup frees 1528 bytes. No remaining sprite window becomes free. The
space saturation remains, see [the space note](demo11-sprite-space-saturation.md).
