# Demo 1-1 graphics fix batches E and F

Date: 2026-10-26. These are candidate checkpoints. They are not the current
head.

## Fix batch E

The candidate descends from fix batch D and ports ten extended graphics IDs
from 7hero for rooms `0x15C` and `0x15D`.

| ID | Compressed size |
| --- | ---: |
| `24B` | 2240 |
| `24A` | 3155 |
| `173` | 1763 |
| `245` | 2318 |
| `236` | 1288 |
| `248` | 1895 |
| `249` | 2202 |
| `24D` | 1579 |
| `24C` | 2510 |
| `24F` | 1966 |

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-e` |
| Base | `demo11-fix-batch-d` |
| ROM SHA-256 | `15a4b70f8ef6666a932cf022fd8ac9ac4d7c2350fadab1def9650e7018845c53` |
| Allocation | file offset `0x1F2888`, 21252 bytes |

## Fix batch F

The candidate descends from fix batch E and ports six extended graphics IDs
from 7hero for room `0x144`.

| ID | Compressed size |
| --- | ---: |
| `131` | 3578 |
| `132` | 3601 |
| `133` | 2531 |
| `134` | 2674 |
| `135` | 2460 |
| `136` | 2343 |

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-f` |
| Base | `demo11-fix-batch-e` |
| ROM SHA-256 | `f656e5e7bce6313db1ae9c44d7f3d9f19c1213b325ff10079f0f858bd5823c2b` |
| Native binary SHA-256 | `0b122c80320abcbad9dae79f8d6db40bfb5505f43889c5aa5a8c3da15d695968` |
| Allocation | file offset `0x240000`, 17411 bytes |

## Verification

`tools/qualify_demo11_gfx_batches_ef.py` checks both recipe identities, the
donor decoded and compressed data, the RATS blocks, the pointer slots, the
reviewed captures and the native build.

| Translevel | Head | Fix batch E | Fix batch F |
| --- | --- | --- | --- |
| `080` | stall `12` | gameplay `14` | gameplay `14` |
| `081` | stall `12` | gameplay `14` | gameplay `14` |
| `068` | stall `12` | stall `12` | gameplay `14` |

The reference and native captures match on mode, room, lives and translevel at
entry 240 and 600.

The suite now reports **38/38**.

## Limits

- Entry and short gameplay are the claims.
- The candidate chain is not accepted as the head.
- The remaining stalls still need songs (`3C`, `3F`, `46`, `47`,
  `53`, `5B`, low ids) or more graphics batches.

## Next steps

1. Port the remaining graphics IDs for the stalled rooms.
2. Investigate the failed song derivations and the low ids.
3. Re-run the survey on the candidate chain and decide the next head.
