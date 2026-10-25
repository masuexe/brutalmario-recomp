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

## Verification notes

The 18 newly playable translevels keep a stable player position after the
level load finishes, so no start fall remains. Reference and native state
(mode, level, translevel, player position, sprite arrays) match on
`023`, `083`, `02D` and `069`. The framebuffers match
exactly for `083` and `02D`, and differ slightly in `023` and 
`069` at one sample, which is consistent with the earlier palette and
lighting phase findings.

## Remaining non-playable translevels

Twenty-two translevels still do not stay in gameplay. Most are unused rooms:
their level data is 6 to 24 bytes, or their level header is invalid. The
others deserve a user check:

| Translevel | Mode | Level data | Note |
| --- | --- | ---: | --- |
| `018` | `0D` | 4818 | active level, no-input death |
| `022` | `0D` | 1066 | custom sprites active, no-input death |
| `04E` | `0C` | 13189 | active level, no-input death |
| `01B` | `0C` | 1841 | active level |
| `069` | `0C` | 338 | moving start setup |
| `05F` | `17` | 328 | special mode |
| `04D` | `0E` | 263 | short room, likely unused |
| `088`/`089`/`097` | `0E` | 125-283 | short rooms, likely unused |
| `024`/`052`/`059`/`077`/`07B`/`08A`/`0AD`/`0BE`/`0EC`/`0FC`/`0FF` | `0B`/`0E` | 6-24 | unused rooms |

## User acceptance: level 0x023

The user played level `0x023` on `demo11-gfx-global13`. The image is
correct, and the third question block gives a bomb instead of the vanilla
item. The user considers this the custom sprite behaviour working.

## Playtest commands for the regained levels

The launcher option `--level-id` takes the Lunar Magic level number (the room
number), not the internal translevel byte. The gained levels map as follows:

| Translevel | Lunar Magic level |
| --- | --- |
| `023` | `0x023` |
| `02D` | `0x109` |
| `083` | `0x15F` |
| `069` | `0x145` |

## Further user acceptances

- Level `0x109` (translevel `02D`) is correct.
- Level `0x15F` (translevel `083`) is correct. The middle boss
  room black screen was a null music slot; see
  [the boss music retarget](demo11-boss-music-fix.md).
- Level `0x145` (translevel `069`) is normal, but the user reports that
  its custom sprite has no code. The runtime shows only sprite `01` falling from
  x=0; porting the donor record for `01` had no effect, so this needs more
  evidence.
- The user deferred the course music quality and the switch music event.

## Limits

- Entry and short idle gameplay are the automated claims.
- Translevel `069` behaviour needs a user check.
- Terrain collision is not qualified beyond the entry samples.
