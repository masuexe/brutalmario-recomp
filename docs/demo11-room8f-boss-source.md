# Room 0x8F boss source in demoOnly1

Date: 2026-10-26. The user reports that demoOnly1 contains the new boss code
for room `0x8F`, and that the boss drops coins after the defeat.
This note records where that code lives.

## Record table

DemoOnly1 does not use the demo 1-1 record table at `$18:8272`.
Its custom sprite loader copies record fields from `$B08A,y` with the
data bank set from the code bank, so the table is at `$0A:308A`
(file `0x8308A`). The table holds twelve custom records.

| Sprite | Record |
| --- | --- |
| `0x42` | `012800003fbb39c46dc827b6c8270000` |
| `0x43` | `012800003f9bb9c419a2131aa2130000` |

The `0x42` record points into a RATS block at file `0x13C862`
with 2623 bytes. A coverage capture of demoOnly1 room `0x8F` executes
that block 48 times.

## Port state

The block needs a free bank window at its low 16 bits (`0xC862`).
Every candidate bank in the current chain is occupied, so the port needs a
targeted rebalancing pass. The candidate recipe is at
`/tmp/demo11-sprites-room8f-boss.json` (not committed).

The child record `0x43` in demo 1-1 already has its own custom record with
different pointers. The demo 1-1 record stays for that ID.

## Limits

- The current committed chain `demo11-sprites-native-records` restores the
  default record for `0x42` and shows the native fallback sprite.
- The demoOnly1 boss port stays open until a window is free.

## Window feasibility: 2026-10-26

The boss block needs a free window at low 16 bits `0xC862` with 2623
bytes. The analysis covers banks `0x20` to `0x3F`. Every window is
blocked. The blockers are earlier sprite blocks, graphics assets and
unindexed RATS blocks.

The planner can move graphics assets only when a free run holds the asset.
The only usable run of `19387` bytes at `0x27B448` holds two RATS
headers (`0x278000`, 32768 bytes and `0x280000`, 6144 bytes).
Both headers are protected by the allocator. The other runs are smaller than
2258 bytes, so the graphics blockers cannot move.

Earlier sprite blocks cannot rebank either. Their low 16 bits are occupied in
every candidate bank. A future pass must first recover contiguous space, for
example by moving the large blocks at `0x278000` and `0x280000` or by
reviewing the installed blocks that no longer have a record.

## Survey note: 2026-10-26

The demo 1-1 survey route does not reach gameplay on the base target: most
entries stay in `mario-start-stall`. Compare the chain survey only with
an earlier chain survey, not with the base survey.
