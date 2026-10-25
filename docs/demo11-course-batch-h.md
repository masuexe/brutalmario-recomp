# Demo 1-1 graphics fix batches H and I

Date: 2026-10-26. These are candidate checkpoints. They are not the current
head.

## Fix batch H

The candidate descends from music batch G and ports ten extended graphics IDs
from 7hero.

| ID | Room |
| --- | --- |
| `10C` | `0x18` |
| `1C9` | `0x1B` |
| `1A5` | `0x103` |
| `209` | `0x116` |
| `15B` | `0x11C` |
| `228`, `229`, `22A`, `22B`, `22C` | `0x12D` |

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-h` |
| Base | `demo11-music-batch-g` |
| ROM SHA-256 | `a2d9e2c9f60a60e97bc5acc2a525d78224fcf42987d9688246f522445361a679` |
| Allocation | file offset `0x2A8000`, 19616 bytes |

## Fix batch I

The candidate adds six extended graphics IDs from 7hero for room `0x142`.

| ID | Room |
| --- | --- |
| `106`, `112`, `116`, `11B`, `139`, `13A` | `0x142` |

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-i` |
| Base | `demo11-fix-batch-h` |
| ROM SHA-256 | `d641b1bb174ba115480957e911ef9617e32cd9c5f6510e8b2ec1577aaa4f820f` |
| Native binary SHA-256 | `b4e1c6471dbc026efb7e8d598d85d953c2a57d044632dc5e7c0498dc6a517844` |
| Allocation | file offset `0x248000`, 16157 bytes |

## Verification

`tools/qualify_demo11_gfx_batches_hi.py` checks both recipe identities, the
donor data, the RATS blocks, the pointer slots, the captures and the native
build.

| Translevel | Head | Batch H / I |
| --- | --- | --- |
| `027` | stall `12` | gameplay `14` |
| `03A` | stall `12` | gameplay `14` |
| `040` | stall `12` | gameplay `14` |
| `051` | stall `12` | gameplay `14` |
| `066` | stall `12` | gameplay `14` |
| `018` | stall `12` | gameplay then death `0D` |
| `01B` | stall `12` | gameplay then death `0C` |

`018` and `01B` reach gameplay and then die because the scripts have no
controller input. The reference and native captures match on mode, room, lives
and translevel.

The suite now reports **40/40**.

## Limits

- Entry and short gameplay are the claims.
- The three unsupported songs and the low ids are still open.
- The candidate chain is not accepted as the head.

## Next steps

1. Re-run the survey on the chain to find the new remaining set.
2. Investigate the low-id source.
3. Decide the next head after the remaining stalls are resolved or deferred.
