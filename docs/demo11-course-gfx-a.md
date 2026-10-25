# Demo 1-1 course graphics candidate A

Date: 2026-10-26. This is a candidate checkpoint. It is not the current head.

## Problem

Room 0x173 selects seven extended graphics IDs that the Demo 1-1 line leaves
null: `1AB`, `201`, `202`, `286`, `287`, `288` and `289`. The room
stalls at Mario Start.

## Donor

The 7hero donor has all seven IDs. cheap-demo and the other legacy donors have
only `1AB`, `201` and `202`.

| ID | Donor | Compressed size |
| --- | --- | ---: |
| `1AB` | 7hero | 2052 |
| `201` | 7hero | 2396 |
| `202` | 7hero | 2038 |
| `286` | 7hero | 2764 |
| `287` | 7hero | 3182 |
| `288` | 7hero | 1965 |
| `289` | 7hero | 2766 |

## Candidate

`demo11-course-gfx-a` descends from `demo11-star-bgm`.

| Item | Value |
| --- | --- |
| ROM SHA-256 | `38bc2d436c545c6030d7871029184426eab25680ae187bb430c519cbebddd8b1` |
| Allocation | file offset `0x1CB000`, 17531 bytes |
| Assets | seven shared-pointer graphics ports |
| Room records | unchanged |
| Native binary SHA-256 | `167cdfc10b849d911dab8c7dc554059b058830235b47ebeb957fb5eabd8599f8` |

The room record already selects the IDs. The candidate installs the graphics
data and the pointer slots only. Each pointer points to a RATS block inside the
allocation.

## Verification

`tools/qualify_demo11_course_gfx_a.py` checks these items:

- the base and candidate identities;
- the unchanged room record;
- each donor pointer and the decoded and compressed data hashes;
- each empty base slot and the installed RATS block;
- the decoded and compressed stream from the candidate;
- no changed byte outside the allocation and the pointer slots;
- the capture ROM identity and the recorded stall.

The capture still stalls at mode `12` after the graphics install. Room 0x173
also requests song 0x1A, and that slot is null. The graphics port is a building
block, not a playability claim.

## Suite

The suite now reports **35/35**.

## Next steps

1. Find a source for the null song `1A` (and the other low-range requests).
2. Port the remaining 52 missing extended graphics IDs used by the stalled
   rooms. Many rooms need several IDs, so batch them by free bank region.
3. Re-test the stalled rooms after each batch.
