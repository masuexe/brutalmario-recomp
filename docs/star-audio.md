# Star music timing probe

Date: 2026-10-16. The user reported normal functionality after the first AOT
expansion, but perceived slower invincibility-star music compared with the
original. This is a reported audio concern, not an established tempo regression.
The version/comparison baseline was requested; pending clarification, this
probe uses Demo 1-1 and the pinned Snes9x 1.63 reference. It does not settle
a ZSNES 1.51 or demoOnly1 comparison.

## Method

The [diagnostic route](../recomp/inputs/star-audio.script) starts fresh, follows
the existing route into the first course, and requests the game's star song.
The pinned ROM's handler at `$01C580` sets `$1490=$FF`, requests song `$0D`
through `$1DFB`, and sets the high bit of `$0DDA`. The diagnostic mirrors those
WRAM changes; the route has `$0DDA=$30` before activation, so it writes `$B0`.
It then idles for 900 calls. This tests the guest music engine with the same
cue in both implementations; it is not a natural item-pickup playthrough or
an SPC tempo override. No ROM or user save is modified.

The separate native audio build contains the accepted 48-variant AOT
configuration and current runtime fixes. It runs at normal pacing with the
SDL dummy device at 32,000 Hz, matching the user's interactive configuration's
requested rate. Full-history WAVs contain generated DSP PCM at 32,040 Hz,
**before device resampling/playback**. The normal interactive executable and
its configuration are not replaced by this diagnostic build.

## Result

| Observation | Reference | Native |
| --- | ---: | ---: |
| Complete session PCM sample frames | 1,719,243 | 1,719,253 |
| Session PCM duration | 53.659270 s | 53.659582 s |
| Star timer at the first post-cue sample | `$68` | `$67` |
| Star timer 300 calls later | `$1D` | `$1C` |

The guest star-timer samples differ by one tick; they are not a measure of
musical tempo. Script bookkeeping also contributes frame calls, so the dump
receipts, rather than the nominal wait labels, define sample frames 2925/3225.

Within the star passage, six consecutive two-second energy-envelope windows
from 39.5 to 51.5 seconds all select **zero lag**, at a block resolution of
320 / 32,040 = approximately 9.99 ms. Correlations range from 0.957 to 0.964.
No progressively increasing native delay is observed. This supports similar
musical timing in generated PCM; it is not a BPM measurement, proof of
identical notes/timbre, or a fine-grained bound on all possible tempo errors.
The 10-sample whole-session difference is not itself a song-tempo measurement.

Native audio history starts at sample zero, with no ring overflow drops.
The dummy device reports four underflows / 2,132 missing output frames,
all within the initial first second; the cumulative counters remain stable
through the star passage. This is not a physical-device playback test.
The output path explicitly converts the DSP rate to the obtained device rate
and uses a bounded occupancy servo. The nominal 32,000-Hz device setting
alone therefore does not establish slower music. Device scheduling and the
historical emulator remain separate comparison questions.

Current conclusion: this Demo 1-1 probe does **not** reproduce a clear slowdown
of the generated star music relative to Snes9x. Do not label the user's
perception an illusion, dismiss a different original baseline, or change the
global APU clock/song tempo on this evidence. Record an exact-version ZSNES
comparison and actual output-device capture if the report persists there.
No audio-runtime fix is introduced in this round.

## Reproduction and evidence

```sh
python3 tools/m1.py build --audio
python3 tools/m1.py reference --script recomp/inputs/star-audio.script \
  --capture star-reference-new
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture star-native-new
python3 tools/analyze_music_timing.py \
  local/captures/star-reference-new/audio.wav \
  local/captures/star-native-new/audio.wav --start 39.5 --end 51.5
```

Local captures: `local/captures/star-audio-reference/` and
`local/captures/star-audio-native/`. Each contains a full WAV and an unprocessed
10-second `star-clip.wav` from seconds 40–50. Reports:
`local/reports/star-audio-comparison.json` and `star-audio-timing.json`.
The timing analyzer reuses the existing complete-history guard and rejects
rate mismatches and invalid intervals. It measures local envelope lag without
resampling or time-stretching either source.
