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