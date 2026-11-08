# Low-id course music dependency

Date: 2026-10-26. This note records the current blocker for about 30 stalled
translevels.

## Problem

Many stalled levels request song ids below `0x20`: `02`, `03`, `05`, `06`
and `1A`. The Demo 1-1 line leaves every one of these slots null. Both
new-family builds, demoOnly1 and 1-1, also leave them null. The legacy donor
groups cover ids `0x20` to `0x5F` only.

## Evidence: the request is the blocker

A probe candidate installed a known-good song payload (cheap-demo song `44`)
into slot `02` on the chain end. Translevel `09E` (room `0x17A`) then
reached and kept gameplay (mode `14` at entry 240 and 600).

This proves three points:

1. The stall is the null music slot, not graphics or another dependency.
2. The engine accepts any valid song payload at a low id.
3. The missing part is the correct song data.

## Silent payload does not work

A synthetic silent payload was built with a valid sequence header and empty
pattern tables. It did not clear the stall. Translevels `09E` and `024`
still stopped at mode `12`. The engine needs a complete, real song structure.

So a silent placeholder is not an option. The choice is either the correct
vanilla song data or a real but wrong song.

## Where the data is not

- The recipient table at `$0F:E000` is null for these ids on both new-family
  builds.
- The legacy group blocks start at id `0x20`. The validated mapping
  `song_id = 0x20 + 4 * group_index + slot` cannot reach low ids.
- The legacy ROMs share identical bytes at `$0F:E000`; that region is not a
  new-format payload table.

## Candidate sources to investigate

1. The legacy SPC program image. A donor APU trace shows the image near ROM
   file offset `0x70000`. If the legacy engine keeps the vanilla songs in
   that image, the sequence data can be extracted and repackaged.
2. A newer donor that stores vanilla songs as normal upload payloads. None of
   the local versions has a new-format payload for these ids.
3. The user can supply a reference recording or a ROM variant that has these
   songs.

## Resolution

Two probe payloads were installed at the same slot and the reference captures
had byte-identical audio. The engine plays its own built-in song for these ids
and ignores the payload content. A valid payload only satisfies the upload
handshake.

The user permitted a placeholder. The result is better than a placeholder: the
music is the engine's built-in track. Music batch N installs the handshake
payloads and all 39 remaining chain stalls reach gameplay.

See [the batch N note](demo11-course-batch-n.md).

## Correction, 2026-11-08

The resolution above is out of date for the current product engine.

The native product build writes a WAV file when `M1_AUDIO_WAV` is set. A probe
replaced the region block at slot `03` with the block of slot `42` and
captured room `122`. The audio changed:

| Build | PCM SHA-256 | RMS |
| --- | --- | ---: |
| r39, original block | `916a97971bd4a72c` | 2756.2 |
| probe, slot 42 block | `8890502975c37d6b` | 2687.5 |

The two captures differ, so the engine does play the payload for a low id. The
old note said the engine ignores the payload content. That was true for the
engine generation that the note tested. It is not true now.

The consequence is important. A low id needs the correct song data. A real but
wrong song plays, and the player hears the wrong music.

## Rules for a low id

1. Keep the table entry non-null. A null entry stalls the level load at mode
   `12`. Compare room `122` at r36, mode `14`, against r38, mode `12`.
2. Put the correct song data in the slot.
3. Capture room audio with `M1_AUDIO_WAV` and compare two builds with
   `tools/compare_audio.py`. A music-selection byte is not an audible match.

## Where the correct data is

The vanilla Super Mario World image holds the built-in songs, but in a
different format. See [the vanilla audio note](vanilla-smw-audio-image.md).
