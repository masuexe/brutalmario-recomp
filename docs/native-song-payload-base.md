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
