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

The walk needs the exact N-SPC parameter byte count of each command at or above
`da` (verified against `ARAM $043E` / `$0F58` in the `demo-1-1` SPC700 driver):

| Parameter bytes | Commands | Notes |
| ---: | --- | --- |
| 0 | `df`, `f0` | `df` is 0 bytes (`slot 6D` has `df e9 d7 6a 01`, which requires `df` = 0 to relocate the `e9` target). |
| 1 | `da`, `db`, `e0`, `e2`, `e4`, `e6`, `e7`, `ea`, `ee` | Instrument, pan, tempo, volume, transpose, vibrato off, etc. |
| 2 | `dc`, `e1`, `e3`, `e8`, `ed` | Fade/sweep and 2-byte parameter commands. |
| 3 | `dd`, `de`, `e5`, `e9`, `eb`, `ec`, `ef`, `f1`, `f2` | `e9` holds a 2-byte ARAM subroutine pointer followed by a 1-byte repeat count. |

Commands below `80` are a duration (with an optional second byte `< 80` for
quantization/velocity). Commands `80` to `d9` are a note, tie, rest or
percussion value.

## Defect to review (resolved in r41)

In r36–r39, Slots `03`, `05` and `06` held the same placeholder block, and Slot
`02` shared `468008` with Slot `4F`. Revision `demo11-native-product-r41`
replaces Slots `02`, `03`, `05`, `06` and `1A` with the relocated vanilla Super
Mario World tracks at `ARAM $5400`, unaliases Slot `02` to `4DD008` (`0x26D000`),
relocates the missed `$E9` pointer in Slot `6D` at `0x28019A`, and sets
`sample_group = 02` in `$0F:CF00` (`0x07CF00`) for all 33 restored slots.
