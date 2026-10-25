# DemoOnly1 boss port for room 0x8F

Date: 2026-10-26. This document describes the demoOnly1 boss port for
room `0x8F`.

## Source

DemoOnly1 keeps the custom sprite record table at file `0x8308A`.
The record for sprite `0x42` is `012800003fbb39c46dc827b6c8270000`.
The record points to a RATS block at file `0x13C862` with 2623 bytes.
The block has eleven internal long references to its own bank.

## Change

The recipe `demo11-sprites-room8f-boss` installs the block at
`0x23:0xC862`. It patches the eleven internal long references to bank
`0x23`. It writes the record with the patched bank bytes.

Two graphics assets move to free the window:

| Graphics | Source | Destination | Size |
| --- | --- | --- | --- |
| `0x81` | `0x11F407` | `0x11BB60` | 2156 |
| `0x310` | `0x11C8DA` | `0x11F19C` | 2540 |

The first move frees a 2775-byte region. The second move uses that region.
A guard allocation of 256 bytes sits at `0x68E10`.

- Base: `demo11-sprites-native-records`
- ROM: `23f8ab7f06da772246827803de69186e88720c1d8938e7167328e5a7c1e9ecb8`
- Native binary: `bb2ff93736b3ff170dd0e3673a27f0a3e029555a302f7cccde306a89ebe8d994`

## Evidence

- Room `0x8F` reaches mode `0x14` and sprite `0x42` is active.
- The room spawns two or more `0x42` children, as demoOnly1 does.
- The room frame differs from the demoOnly1 frame by fewer than 500 pixels
  in the gameplay field. The native record chain differs by more than 18000
  pixels.
- `tools/qualify_demo11_sprites_room8f_boss.py` passes.
- Whole-line audit: 1,028,055 changed bytes, zero unexpected.
- Suite **77/77**; space budget passes.

## Acceptance

The user playtested the room on 2026-10-26. The boss matches the expected
demoOnly1 boss, including the large yellow ball. After the defeat, the boss
drops coins. A world conquest rate screen follows the drop. The user states
that this behavior is the author intent.

## Limits

- The automated capture does not defeat the boss. The long capture reaches
  the same defeat state as demoOnly1.
- The two moved graphics assets keep their decode. The qualifier checks the
  first decoded byte only.

## Survey

A survey of all 255 translevels on this chain gives 232 playable entries.
The result matches the `demo11-sprites-native-records` survey for every
translevel. The boss port changes no survey result.
