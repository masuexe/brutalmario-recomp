# Demo 1-1 low-id music resolution and final batches

Date: 2026-10-26. This note records the resolution of the low-id music blocker
and the last chain batches.

## Finding: built-in playback for the low ids

Two probe candidates installed different real song payloads into slot `02` on
the chain end. The reference captures of translevel `09E` produced
byte-identical `audio.wav` files (same SHA-256,
`61484761c7ea3620f588b055803eb64337cebe22f4e53fbec2c02995a0f514a1`).

The same test at slot `6D` on translevel `0A6` also produced identical audio.

Conclusion: for ids `02`, `03`, `05`, `06`, `1A` and `6D` the engine
plays its own built-in song and ignores the uploaded payload content. The null
table slot only stops the upload handshake, which in turn stalls Mario Start.
A valid payload satisfies the handshake, and the correct built-in song plays.

This is not a wrong-song placeholder. The music is the engine's own track.

Probe captures: `local/captures/probe-slot02-a`, `probe-slot02-b`,
`probe-slot6d-a`, `probe-slot6d-b`.

## Music batch N

The candidate descends from fix batch M and fills the six low slots with valid
raw slices of a reviewed donor group.

| Item | Value |
| --- | --- |
| Target | `demo11-music-batch-n` |
| Base | `demo11-fix-batch-m` |
| ROM SHA-256 | `9d5855cfa1df296730e2a3afb9fd2647ef45ab4d028e2a3407e6efe55efaaa24` |
| Slots | `02`, `03`, `05`, `06`, `1A`, `6D` |

## Graphics batches O1 and O2

| Batch | IDs | Rooms | ROM |
| --- | --- | --- | --- |
| O1 | `30F`, `30E`, `130`, `21E`, `21F`, `164` | `0x122`, `0x139`, `0x154` | `e5e3376f590d0a256cd25de94b102c2b11bee883be41f37b2ce1b61d3d7780bf` |
| O2 | `287`, `286`, `288`, `1AB`, `202`, `201`, `289` | `0x173` | `8bd3a8d440ea0cffff17003e85f2657af6788a1d7169cdbd8e4b0277957fc0cc` |

Fix batch O2 native binary SHA-256:
`63676019696575cf29144298f183d2ab43ce09e581892c877d22d4dca0d1f391`.

## Result

All 39 remaining chain stalls now reach gameplay at entry 240 (mode `14`):

| Result at entry 600 | Count |
| --- | ---: |
| Playable `14` | 35 |
| Death from no input (`0E`/`0B`) | 4 |

The four levels that die are `024`, `097`, `0AD` and `0BE`. Their lives
drop from 4 to 3 at the transition, so the scripts fall into a pit. This is the
same no-input behavior already recorded for `001`, `018` and `01B`.

`tools/qualify_demo11_batches_no.py` checks the chain identities, the music
and graphics installation, all 39 reference captures and eight native captures.

The suite now reports **42/42**.

## Limits

- Entry and short gameplay are the claims.
- The built-in songs are the engine tracks. An audible comparison against the
  legacy donor was not possible.
- The candidate chain is not accepted as the head.
