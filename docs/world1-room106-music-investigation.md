# World 1 room 106 music: investigation state

Date 2026-10-24. Status: **root cause mapped, repair not yet complete**. The
user confirmed cheap_demo's room `106` music is correct and the demoOnly1-line
header-byte fix (commit `fbc09f2`, selection byte only) still sounded wrong.

## Confirmed mechanism (evidence: `local/probes/world1-survey/106-music-diagnostic/`)

- `$0DDA` is only a record; the real trigger is the `$1DFB` SPC pulse port.
  In cheap_demo, room 106 finally writes `$1DFB = 0x21` (frame ~2493) and the
  correct song uploads. In demo11 the same room writes `$1DFB = 0x49`
  (frame ~2455) - the wrong-music request.
- cheap's `0x21` request is produced by a per-level code block at SNES
  `$068400..` (watch PC `$068424` writes `$1DFB=0x21`, then clears `$1DFB`).
  demo11 has no such block; its physical layout there differs (level data).
- The cheap playback for room 106 uses a 9 KB ARAM region `$4600-$6B00`
  (sequences at `$460E-$4A9B` plus `$6A1B/$6A20`, samples elsewhere in the
  range). This region is uploaded on level entry - the boot-time ARAM does
  not contain it - and demo11's ARAM at the same range is entirely different.
  The region's ROM source in cheap is scattered (e.g. the sequence at ARAM
  `$460E` matches ROM `0x76188`, others at `0x7605F`, `0x76384`...), so it is
  not one contiguous upload block like room 138's four-song group.
- cheap's song-21 slot (`$0FE063`) points at a 1,276-byte self-contained
  sequence at SNES `$13A412`. demo11's song-21 slot is empty (`000000`).
- The shared selection stack is byte-identical in both ROMs
  (`$0DF130/$0DF13D`, `$0DA982`, `$05864E`); only inputs differ.

## Experiments on `demo11-room106-music` (local/ignored, not accepted)

1. Song-49 slot repointed at a copy of cheap song-21 data: `$1DFB` stays
   `0x49`, nothing uploads, playback unchanged (still the song-2F private
   payload at ARAM `$5400`). `$1DFB=0x49` does not behave as a table-driven
   BGM request on this engine.
2. Three-byte cheap branch variant of the level-music formula
   (`$009724 01->1E`, `$00972D/2E EA EA -> B0 0C`) plus the song-21 slot fill:
   `$0DDA`/playback unchanged. The room-106 `0x49` request does not pass
   through those bytes.

## Next steps

1. Trace upstream of the `$1DFB=0x49` write (watch PC `$009738`; the value
   `0x49` was loaded around trace PC `$0096E8-$0096F8` at frame 2455 in
   `d11-trace4.csv`) to find where `0x49` is selected - likely a per-level
   or per-translevel music table byte in demo11's engine.
2. Once the request can be steered to `0x21`, fill the song-21 slot (payload
   mechanism already proven by the room-138/room-010 private slots).
3. The 9 KB sample/sequence region upload must be reproduced; verify by
   comparing the resulting ARAM against `cheap-aram.bin` (`4600-$6B00`
   plus the `$003E0` directory), not by selection bytes alone.
4. Do not reuse the demoOnly1 `fbc09f2` header-byte change; selection parity
   is not an audible match.

Captures: `d11-route-*` (accepted route work) unchanged; this investigation
used fresh `106-music-diagnostic` files only.
