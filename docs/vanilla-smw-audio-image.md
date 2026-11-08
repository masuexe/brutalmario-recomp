# Vanilla Super Mario World audio image

Date: 2026-11-08.

## Purpose

The product needs the built-in Super Mario World songs for song ids below
`20`. The product engine has no built-in set. A null table entry stalls the
level load. The goal is to port a vanilla song, for example the water theme
at id `03`.

## Donor

| Item | Value |
| --- | --- |
| File | `/home/harp/projects/sfc/roms/Super Mario World (U) [!].smc` |
| Size | 524288 |
| SHA-256 | `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b` |

That digest matches the value in `config/inputs.json`. The file is the base
image that the product IPS patch applies to.

## Upload chain

The code at `00:80E8` sets a 24-bit pointer to `0E:8000` and calls
`00:8079`. The pointer is a file offset of `0x70000`. The data is a chain of
chunks. Each chunk is a length word, an ARAM destination word and the data.
A zero length word ends the chain.

| Chunk file offset | Length | ARAM destination | Content |
| --- | ---: | --- | --- |
| `0x70000` | 3646 | `0500` | SPC driver code |
| `0x70E42` | 2667 | `5570` | music data |
| `0x718B1` | 5661 | `1360` | music data |
| `0x78000` | 80 | `8000` | sample directory |
| `0x78054` | 28448 | `8100` | sample data |

The code at `00:80FD` points at `0F:8000`, file offset `0x78000`, for the
samples. The code at `00:810A` uploads music data through `00:80F7` with a
pointer that the caller supplies.

## ARAM image

The image is reproducible with the reference host. Set
`SNESREF_APURAM_TRACE_FILE` and `SNESREF_HEADLESS`. The trace holds one
javascript object line per changed byte. Apply the lines in order to a 64 KB
buffer.

The result is `local/probes/vanilla-apu/aram.bin`. It holds 38183 non-zero
bytes. The music regions are `1360` to about `1DBF` and `5570` to about
`5BF7`.

## Sequence header format

The vanilla header has eight bytes, the same size as the product header:

| Offset | Content |
| --- | --- |
| +0 | pattern pointer 0 |
| +2 | pattern pointer 1 |
| +4 | `FF` and `00` |
| +6 | self pointer, equal to the header address |

The product header differs in one value. Its self pointer is the header
address plus two, for example `5402` against a base of `5400`.

The song table holds entries two bytes before the header. Entry `13DC` of the
first table addresses a header at `13DE`. Add two to each table entry to
reach the header.

The first table starts at `12DB` and holds these entries:

| Index | Entry | Header |
| ---: | --- | --- |
| 0 | `11BD` | `11BF` |
| 1 | `12CB` | `12CD` |
| 2 | `13E9` | `13EB` |
| 3 | `1518` | `151A` |
| 4 | `1659` | `165B` |
| 5 | `17AD` | `17AF` |
| 6 | `1916` | `1918` |
| 7 | `1A94` | `1A96` |
| 8 | `1C28` | `1C2A` |
| 9 | `1DD5` | `1DD7` |
| 10 | `1F9B` | `1F9D` |

The table ends at `12F1` with the value `E800`. That value is code, not an
address. The index is not yet confirmed as the music id.

## Open question

The custom engine in the product is an AddmusicK-derived engine. It expects an
eight-byte sequence header:

| Offset | Content |
| --- | --- |
| +0 | pattern pointer 0 |
| +2 | pattern pointer 1 |
| +4 | `FF` and `00` |
| +6 | self pointer, equal to the base plus two |

The vanilla song layout and command set differ from the AddmusicK layout. A
direct copy will not play. The remaining work is to convert a vanilla song to
an AddmusicK payload, or to find the same song in AddmusicK form.

## Next steps

1. Dump the ARAM image again while a water level runs. Then the active song
   is known and its data can be located without the id table.
2. Read the driver at ARAM `0500` to find the song id to address table.
3. Convert the selected song to an AddmusicK payload, then test it with
   `tools/render_song_payload.py`.

## Audio verification

The native build writes a WAV file when `M1_AUDIO_WAV` is set. Use it to
compare two builds with `tools/compare_audio.py`. This is evidence that the
payload content reaches the engine. A payload swap at slot `03` changed the
room `122` audio, so the engine does play the payload for low ids.

## Verified by direct comparison

The ROM chunk at `0x718B1` and the ARAM region at `1360` are identical. The
chunk header is four bytes. Compare from `0x718B5`, not from `0x718B1`. The
same rule holds for the chunk at `0x70E42`.

That check shows the reference host trace is correct.

## Only the boot image is in the dump

The dump came from the title screen at frame 900. It holds eight `FF 00`
pairs in the region `1360` to `2980` and none in `5570` to `5FE0`. A Super
Mario World image holds about thirty songs. Eight markers are too few.

Therefore the two chunks are the boot image only. Each level uploads its own
song later through `00:80F7`. The per-level song table is not found yet.

## Searches that failed

| Search | Result |
| --- | --- |
| Three-byte LoROM pointer table in the ROM | none with 12 of 20 valid blocks |
| Two-byte table pointing at valid blocks in bank `0E` | none with a strict block test |
| Strict upload blocks in bank `0E` | zero |
| Pointer table inside the driver `0500` to `0E42` | no clean run |

A valid block test needs all of these: a length from `32` to `6000`, an ARAM
destination from `0100` to `7C00`, the pair `FF 00` at header offset `+4`, and
a self pointer equal to the destination.

## What to do next

1. Dump the APU RAM while a water level runs. Compare that dump with the boot
   dump. The extra bytes are the level song, and its upload destination shows
   the ARAM base.
2. Or read the driver code at ARAM `0500` and find the routine that handles
   the song request port. The table it reads is the song table.
3. Or take a recording of the vanilla water theme and compare it with product
   slot renders. A match gives the slot without any format conversion.
