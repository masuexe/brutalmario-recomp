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

## Fix plan

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