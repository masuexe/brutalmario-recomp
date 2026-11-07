# Song payload base for the native port

Date: 2026-11-07. Revision r34.

## Finding

The product engine plays a song only when the upload block targets ARAM `5400`.

A song block has this layout:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

The legacy donor family stores most group songs with destination `6800`.
The product engine accepts the upload but does not start the sequence.
The previous song continues to play. The room music byte still reads the
new slot, so a byte check does not show the defect.

## Evidence

The room `0F5` song slot `53` held a `6800` block. Three payloads went
through `tools/render_song_payload.py` with the pinned reference host:

| Payload | Base | Silent fraction | Result |
| --- | --- | ---: | --- |
| r33 slot `53` | `6800` | 0.989 | no music |
| cheap-demo group 17 slot 3, unrelocated | `6800` | 0.989 | no music |
| r34 slot `53`, relocated | `5400` | 0.043 | music plays |

## Recipe rule

When a donor song uses base `6800`, make a `5400` payload. Do these steps:

1. Build the raw payload with `raw_group_song`.
2. Subtract `1400` from every 16-bit word in the song area in the range
   `[6800, 6800 + length)`.
3. Set the sequence self-pointer at song offset `6` to `5402`.
4. Keep the destination field at `5400`.

The sequence header must then look like a product song header, for example
`f4610462ff000254` against the product song `1e572e57ff000254`.

## Limits

- The blanket word relocation is safe for the group 17 slot 3 song. A song
  with note data that forms a value in the source range needs a command walk.
  `adapt_music` does that walk, but it rejects this song.
- The relocation keeps the song data. The reference render of the relocated
  payload is not compared with a legacy-engine render. The legacy engine is
  not in the reference set.
## Affected slots, revision r35

Revision r35 relocated these slots from base `6800` to base `5400`:

| Slot | Rooms that request it |
| --- | --- |
| `1A` | `173` |
| `36` | `01A`, `0C3`, `0C6`, `118`, `13E` |
| `3B` | `065` |
| `3C` | `041`, `060`, `063`, `064`, `103`, `11C` |
| `3E` | `0EA` to `0ED`, `108` |
| `3F` | `01B`, `0BD` |
| `42` | `027` to `030`, `075`, `088`, `124`, `12A` |
| `43` | `0A9`, `110`, `131`, `132` |
| `46` | `02D`, `07C`, `086`, `087`, `0B7` |
| `47` | `015`, `021`, `03E`, `044`, `057` to `05C`, `0F8` |
| `5B` | none |
| `6D` | `182` |
| `03`, `05`, `06` | `122`, `081`, `062` |

The last three are region pack blocks. They came from the r19 music batch and
were never in the reference image, which leaves those slots empty.

## Verification

The reference host rendered bare payloads through `tools/render_song_payload.py`.
That tool always targets base `5400`.

| Slot | Base before | Silent before | Base after | Silent after |
| --- | --- | ---: | --- | ---: |
| `03` | `6800` | 0.989 | `5400` | 0.043 |
| `47` | `6800` | 0.989 | `5400` | 0.215 |
| `36` | `6800` | 0.989 | `5400` | 0.091 |
| `5B` | `6800` | 0.989 | `5400` | 0.645 |
| `6D` | `6800` | 0.989 | `5400` | 0.043 |
| `42` | `6800` | 0.989 | `5400` | 0.086 |
| `4F` | `5400` | 0.043 | `5400` | 0.043 |

## Defect to review

Slots `03`, `05` and `06` hold the same block. Rooms `122`, `081` and `062`
therefore play the same song. This condition comes from the r19 music batch.
The user did not confirm it.
