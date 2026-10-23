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

## Update 2026-10-24 (second session): selection solved, uploader is the wall

Disassembly (trace-driven) of `$009728-$00973B` closed the selection path:
`LDA $0DDA` feeds `STA $1DFB`, with a dead `CMP #$40` and an override
`LDA #$16` behind `$0D9B == $C1` (never true on this line; verified across
all demo11-line captures). A four-byte patch now steers room106 anywhere:

- `$00972C`: `40 -> 49` (bind the comparison to the room106 request)
- `$00972D`: `EA EA -> F0 07` (BEQ to the override when the request is 0x49)
- `$009737`: override immediate (target request value)
- plus a filled target slot

Verified with the reference runner: requests `0x21` and `0x7F` both take
effect (`$0DDA` mirrors them). Experiments on the ignored
`demo11-room106-music` target:

| Exp | Slot/shape | Result |
| --- | --- | --- |
| 6 | slot 7F, payload `[len][base]+raw 1276B` | data lands at ARAM 5400 verbatim; directory not rebuilt; audible but quantitatively unlike cheap (band profile differs) |
| 7 | slot 21 (0x21 request) | same direct-copy behaviour; the built-in 0x21 path does not interpret the cheap loader script |
| 8 | slot 7F, 2F-shaped head+zeros+data | silent; the group head pointing at `1f1f...` parses to nothing |

Key structural facts learned: the driver's per-channel pointers live at
ARAM `$30-$3C` (cheap: `$685A..$6A23`; demo11 2F: `$548D..$5640` - the same
layout shifted by the payload base); the uploader **rewrites payload bytes
after upload** (2F's ROM head pointers `$56F3/$5703` become `$5651` in ARAM,
its data segment is re-laid-out with a zeroed gap), so a byte-identical
reproduction of cheap's ARAM through the payload channel is not possible
without knowing the source format the uploader consumes.

## Update 2026-10-24 (third pass): uploader internals

Instruction-tracing cheap after the `$1DFB=0x21` request (frames 2493-2560)
and watching the copy-engine source pointer `$8A` shows:

- the dominant copy loop is `$00B930..$00B991` (`LDA [$8A]` long-read,
  `STA [$00],Y` long-write, bank carry at `$00B98A`), a generic mover;
- right after the request it moves a series of small blocks whose source
  pointers all sit in WRAM `$0A00-$0AFF` (an engine work buffer), then a
  `$0010/$1000` alternating handshake (`$00EAD1` region) takes over - the
  audio bytes reach the SPC through port handshaking, not one ROM block;
- audio-relevant WAV gating: cheap renders **silent** without the
  `snes9x_echo_buffer_hack=enabled` core option; with it the reference
  segment shows rms ~642, zc ~1845, ~99.6% band mass at 440 Hz. exp6's
  direct-copy audio (rms ~1782, bands spread over 440/880) is audibly a
  different render, confirming the direct payload cannot reproduce cheap.

Consequence: the remaining work is reversing the port-level upload protocol
(WRAM-staged blocks plus the `$0010/$1000` handshake) - a multi-session
effort with real regression surface, not a byte recipe yet.

## Next steps

1. Trace the `$00EAD1` handshake loop and the WRAM `$0A00` staging area to
   enumerate the full block list the SPC receives for song 21, then replay
   that exact sequence through the slot-7F mechanism (or a small SNES-side
   replay stub in a descendant target).
2. Quantitative audio gates (cheap reference figures above) before any user
   listening check.
3. Do not reuse the demoOnly1 `fbc09f2` header-byte change; selection parity
   is not an audible match.

Captures: `d11-route-*` (accepted route work) unchanged; this investigation
used fresh `106-music-diagnostic` files only.
