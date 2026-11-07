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

When a donor song uses base `6800`, make a `5400` payload. Use
`tools/adapt_song_base.py`. It does these steps:

1. Read the sequence header and the two pattern pointers.
2. Read the eight channel pointers of each pattern.
3. Walk every channel track and collect the target of command `e9`.
4. Subtract `1400` from those pointer fields only.
5. Set the sequence self-pointer at song offset `6` to `5402`.
6. Keep the destination field at `5400`.

The sequence header must then look like a product song header, for example
`f4610462ff000254` against the product song `1e572e57ff000254`.

## Do not relocate every word

A blanket pass over the source range corrupts note parameters. The room `0F5`
song holds 66 real pointer fields and 115 words that are note or parameter
values in the same range. Revision r35 moved all 181 words and the melody
was wrong. Revision r36 moves the 66 pointer fields and the melody is
correct.

## Command table

The walk needs the parameter byte count of each command at or above `da`.
These counts are in use:

| Command | Bytes | Notes |
| --- | ---: | --- |
| `da` | 1 | |
| `db` | 1 | |
| `dc` | 1 | The parameter holds a volume value, for example `20` or `40`. |
| `dd` | 1 | Not seen in the tested songs. |
| `de` | 1 | |
| `df` | 1 | |
| `e0` | 1 | |
| `e2` | 1 | |
| `e7` | 1 | |
| `e8` | 2 | The room `0F5` song fails without this entry. |
| `e9` | 3 | The first two bytes are an ARAM pointer. |
| `ef` | 3 | |
| `f0` | 0 | |
| `f1` | 3 | |
| `f2` | 3 | |

Commands below `80` are a duration. Commands `80` to `d9` are a note value.

## Limits

- The walk raises an error for a command that is not in the table. Add the
  command only after you confirm its parameter count.
- The relocation keeps the song data. The reference render of a relocated
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