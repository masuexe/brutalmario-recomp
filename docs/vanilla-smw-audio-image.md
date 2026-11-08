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

The vanilla header has ten bytes:

| Offset | Content |
| --- | --- |
| +0 | pattern pointer 0 |
| +2 | pattern pointer 1 |
| +4 | pattern pointer 2 |
| +6 | `FF` and `00` |
| +8 | self pointer, equal to the header address plus two |

A scan of the dumped image with that layout finds only two headers,
`13DC` and `1440`. Most vanilla songs do not use this layout.

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
