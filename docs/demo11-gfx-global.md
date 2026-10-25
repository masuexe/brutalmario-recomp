# Global extended graphics restoration

Date: 2026-10-26. After the world-by-world batches, 53 extended graphics IDs of
the remaining level rooms were still empty. The empty slots caused vertical-line
corruption, map returns and start deaths. Thirteen global batches close the
whole set.

## Cause

The level header of 36 level rooms referenced extended graphics IDs with an
empty pointer. The renderer then used corrupted tile data and the level often
returned to the map or killed Mario at the start. The user reported the
vertical-line symptom and the start fall.

## Batches

Thirteen batches port 53 IDs from 7hero onto `demo11-sprite-final`.

- The batches use one contiguous RATS allocation each.
- Every asset is a shared global graphics pointer, so no level header changes.
- The chain end is `demo11-gfx-global13`, ROM
  `86d3a5cd5e2feebbd189e98b84deb3300f670128c3062901b64d1a7d106d691f`.
- Native binary identity is recorded by `tools/qualify_demo11_gfx_global.py`.

## Coverage

All 149 level rooms with a valid header now have no empty extended graphics
slot. The 36 rooms that had gaps are fixed.

## Full-range survey

Survey on `demo11-gfx-global13`:

| Result | Count |
| --- | ---: |
| Playable | **233** |
| Mode `0E` | 14 |
| Mode `0C` | 4 |
| Mode `0D` | 2 |
| Mode `17` | 1 |
| Mode `0B` | 1 |

- Zero Mario Start stalls across 255 translevels.
- Eighteen translevels become playable: `023`, `02D`, `05E`, `063`,
  `065`, `06A`, `06B`, `06E`, `071`, `072`, `075`, `076`,
  `07A`, `07E`, `082`, `083`, `092`, `093`.
- Translevel `069` changed: it was playable on the sprite chain and now returns
  a death mode after 600 idle frames. The level starts on a moving setup. The
  user must confirm whether the new behaviour is correct.

The previous chain reported 216 playable, so the net gain is 17.

## Verification

- `tools/qualify_demo11_gfx_global.py`: chain identities, 53 donor assets,
  installed streams, room dependencies, slot coverage, captures, native build.
- `tools/qualify_demo11_gfx_global_range.py`: survey classes and receipts.
- Whole-line audit on the chain end: 581,481 changed bytes, zero unexpected.
- Suite reports **54/54**; the space budget guard still passes with 711,805
  free bytes and 124,631 bank-aligned bytes.

## Limits

- Entry and short idle gameplay are the automated claims.
- Translevel `069` behaviour needs a user check.
- Terrain collision is not qualified beyond the entry samples.
