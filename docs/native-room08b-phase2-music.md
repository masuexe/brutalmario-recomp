# Boss 08B second phase: the music slot gap

## Result

Room `08B` reaches its second phase and the game stops. The cause is a music
slot that the recipient baseline leaves empty.

## Evidence

The slot `32` boss program writes the music register at three points.

| Pack offset | Instruction | Music id |
| --- | --- | --- |
| `0xC41` | `LDA #$19` then `STA $1DFB` | `0x19` |
| `0x1312` | `LDA #$1E` then `STA $1DFB` | `0x1E` |
| `0x1CF8` | `LDA #$1E` then `STA $1DFB` | `0x1E` |

The music table starts at `0F:E000`. Each slot holds a three-byte big-endian
pointer.

| Slot | product r27 | `cheap-demo` | `demo-1-1` |
| --- | --- | --- | --- |
| `0x02` | `468008` | `F2C3C5` | `000000` |
| `0x03` | `4BC948` | `E1A441` | `000000` |
| `0x05` | `4C8008` | `0C3BED` | `000000` |
| `0x06` | `4D9E60` | `F08466` | `000000` |
| `0x19` | **`000000`** | `CFEAE1` | `000000` |
| `0x1A` | `4DCBF0` | `BC5BF3` | `000000` |
| `0x1E` | **`000000`** | `0F6CE1` | `000000` |
| `0x24` | `13C691` | `217C7E` | `13C691` |

Slots `0x02`, `0x03`, `0x05`, `0x06` and `0x1A` are already filled by earlier
music batches. Slots `0x19` and `0x1E` are still empty, and no batch covers
them.

## How the failure works

`docs/demo11-low-id-music.md` records this failure mode. A music id below
`0x20` that points at a null slot stops the level load at mode `12`.

## Why a direct probe did not reproduce it

`recomp/inputs/native-music1e-probe.script` writes `$1DFB = 1E` in room `08B`
while the game runs. The mode stays at `14` for the whole probe, and `$1DFB`
reads back as `00`.

The register is a one-shot command. The engine clears it after it reads it.
The load stall happens when the engine reloads the level, not when it plays a
song in place.

## Why `cheap-demo` does not hold the answer directly

The `cheap-demo` table at `0F:E000` does not resolve these two slots either.

| Slot | `cheap-demo` pointer | LoROM valid | Bytes at the target |
| --- | --- | --- | --- |
| `0x18` | `EEA4E0` | yes | real data |
| `0x19` | `CFEAE1` | yes | **all zero** |
| `0x1B` | `F3A41E` | yes | real data |
| `0x1E` | `0F6CE1` | no | - |
| `0x1F` | `F1F01F` | yes | real data |
| `0x36` | `D5A4FF` | yes | real data |

`cheap-demo` plays these low ids with the original Super Mario World music
engine. The new family replaced that engine, and the new table has no entry
for the low ids. `docs/demo11-low-id-music.md` records the same limit.

## Audit of every requested id

Every installed sprite pack that writes `$1DFB` was scanned. Ten ids are
requested. Before r28, two of them pointed at null slots.

| Id | r27 | r28 | Packs that request it |
| --- | --- | --- | --- |
| `0x05` | ok | ok | sprite38, sprite3b, sprite3c |
| `0x0B` | ok | ok | sprite0f, sprite1c |
| `0x19` | **null** | ok | sprite32, sprite5d |
| `0x1E` | **null** | ok | sprite0f, sprite10, sprite11 |
| `0x21` | ok | ok | sprite14, sprite25 |
| `0x22` | ok | ok | sprite2d |
| `0x23` | ok | ok | sprite11, sprite12, sprite25 |
| `0x24` | ok | ok | sprite14, sprite25 |
| `0xA5` | ok | ok | sprite9c |
| `0xAD` | ok | ok | sprite9c |

No requested id is null in r28.

## Product r28 fills the two slots

Product r28 points slots `0x19` and `0x1E` at an installed boss-battle track.
The track is slot `0x33` (Last Battle). The image changes 6 bytes.

| Slot | r27 | r28 |
| --- | --- | --- |
| `0x19` | `000000` | `14F3EA` |
| `0x1E` | `000000` | `14F3EA` |

Room `08B` runs to frame `12720` in mode `14` with the row intact.

**Warning:** the track is not the original.

## An in-play change does not stall

A direct probe writes `$1DFB = 1E` while room `08B` runs. The mode stays at
`14` on product r27, where the slot is null. A null low slot therefore does
not stall an in-play music change. The stall in
`docs/demo11-low-id-music.md` applies to a level load.

Automation did not reproduce the second-phase freeze. The boss program plays
`$1E` when its `$15AC` counter enters certain ranges. That is animation
timing, not the phase change itself.

## Open question

The freeze needs a report of its exact form:

- Does the picture stop while the sound continues?
- Does the sound stop as well?
- Does the screen go black?
- Does the freeze start when the boss changes shape, or later?

## Fix plan for the exact track

The fix must install a real song payload into slots `0x19` and `0x1E`. The
form of an existing batch entry is:

- `source_address`: the group block in `cheap-demo`
- `source_group`: size and SHA-256 of that block
- `sequence_offset` and `source_data_offset`: where the song starts
- `pointer_address`: `0FE000 + slot * 3`
- `allocation`: a free ROM range for the adapted payload
- `adapted`: size and SHA-256 of the result

`config/restorations/demo11-music-batch-j.json` is the closest model. It fills
slots `0x36`, `0x3B`, `0x3E`, `0x42` and `0x43` from `cheap-demo`.

The `cheap-demo` pointers for the two missing slots are `CFEAE1` and `0F6CE1`.
These are not plain LoROM addresses, so the extraction must use the project
music tools and verify the result in play.

## Deferred issues

- The user reports that `cheap-demo` holds the correct second-phase music.
  The extraction task is open.
- Phase 2 was never reached by an automated fixture, because the fixture does
  not damage the boss.