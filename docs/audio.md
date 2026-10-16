# Demo 1-1 audio baseline

Date: 2026-10-15. The initial audio smoke gate now has both user listening
evidence and a reproducible recorded comparison. Exact cross-core waveform
and timing equivalence remain open.

Later update: the [boot timing fix](boot-timing.md) corrects the CPU/APU clock
ratio for the beam driver. Capture results below describe the earlier clock
model. The new short audio smoke capture and remaining manual listening
check are recorded separately in that investigation.

The later [star-music probe](star-audio.md) investigates a reported subjective
slowdown after AOT expansion. Generated Demo 1-1 star PCM shows no accumulating
lag against Snes9x in the measured passage; ZSNES and physical playback remain
unqualified.

## Manual evidence

The user played level 1-1 with audio enabled and reported that background
music and action effects sounded normal compared with their memory of
ZSNES 1.51. This is a listening observation, not a recorded ZSNES A/B test.
See [playtesting.md](playtesting.md).

## Capture method

The existing 6,104-frame route was run from a fresh session in the pinned
Snes9x 1.63 frontend and an isolated native audio build. Both runtime fixes
remain active. No ROM, guest logic, input timing, or interactive settings were
changed. The interactive executable was not replaced.

The diagnostic build selects the upstream CMake setting
`SNESRECOMP_AUDIO_TRACE_HISTORY=FULL`. The normal default remains SMALL.
At desktop shutdown, before the APU mutex is destroyed, a project-owned hook
uses the existing audio-trace API to snapshot the complete native DSP PCM.
This is **before device resampling and playback**, including samples that
would have been dropped by the output ring. Device underflows are recorded
separately. PCM captures are stereo, signed 16-bit, 32,040 Hz.

Native runs use normal pacing and SDL dummy video/audio. One run uses the
default 32,040-Hz device rate; a second changes only the isolated device rate
to 32,000 Hz. The resulting native PCM is byte-identical between those runs.
All eight sampled WRAM images and raw framebuffers also match the previous
optimized-renderer timing capture exactly, supporting noninterference of the
capture and pacing changes at those samples.

The first recording attempt retained only the last 65,536 sample frames
because a source-specific upstream SMALL setting overrode a target definition.
The complete-history guard rejected it (`start_sample != 0`); it is not used
as a full-length comparison. The final build uses the upstream CMake option
directly and captures every produced sample from index zero.

## Results

The repeated reference WAV is byte-identical to the original M1 reference WAV.

| Measurement | Snes9x reference | Native DSP capture |
| --- | ---: | ---: |
| Stereo sample frames | 3,254,101 | 3,259,546 |
| Duration at 32,040 Hz | 101.563702 s | 101.733645 s |
| RMS, integer PCM units | 1,193.90 | 1,180.26 |
| Absolute peak | 12,515 | 11,192 |
| Samples at an integer rail | 0 | 0 |
| First approximately 10-ms block with RMS > 32 | 4.144819 s | 4.174782 s |

The native recording is **0.169944 seconds longer**. The runtime's
`apu_frame_clock.h` budgets 17,088 SPC cycles, or 534 DSP sample frames, per
host frame. The reference frontend reports approximately 60.0988 frames/s;
the native frame clock uses a 60-Hz convention. These measured/code-level
differences are consistent with the length discrepancy. They do not fully
explain every cue offset or establish which behavior ZSNES 1.51 produces.

There is no PCM identity between native and reference. Searching +/-0.5 s
on approximately 10-ms RMS envelopes gives correlations of approximately
0.835–0.974 in nonsilent windows, with best local native delays around
30–70 ms. The 20–30 s window is silent in both captures and has no valid
correlation. Both captures have the same five long low-energy regions,
with shifted boundaries. Envelope similarity is useful timing evidence,
not proof of matching pitch, timbre, effects, or individual waveforms.

Device results distinguish output scheduling from DSP generation:

| Native dummy-device measurement | 32,040-Hz device | 32,000-Hz device |
| --- | ---: | ---: |
| Generated DSP sample frames | 3,259,546 | 3,259,546 |
| Output-ring dropped samples | 0 | 0 |
| Audible output-ring dropped samples | 0 | 0 |
| Underflow counter | 375 | 3 |
| Device-rate frames missing PCM | 164,802 | 1,599 |

At 32,000 Hz all three underflow counts occur within the first second,
before the first active music block; they do not increase during the rest
of the route. The retained native PCM is identical across device rates.
This supports a dummy-device callback/pacing explanation for the recurring
32,040-Hz underflows, rather than missing game-generated audio. It does not
qualify a physical sound device. Some generated audio remains queued when
the script quits; the WAV includes that tail.

## Status and next acceptance

- Passed: user listening smoke test, complete PCM capture, nonzero signal,
  no integer-rail samples, no DSP output-ring overflow drops, repeatable
  reference audio, and unchanged sampled gameplay state.
- Open: precise cross-core cue timing, waveform fidelity, recorded ZSNES
  comparison, physical-device scheduling, and sound effects outside this route.
- Known separate issues remain in [timing.md](timing.md), including the
  selected-state phase difference and file-menu background.

This is enough evidence to move the next gameplay acceptance step to a
reachable custom boss and its full attack cycle. Do not mark all audio
fidelity gates complete or integrate historical-version content yet.

## Reproduction

Use new capture names; the runner refuses existing directories.

```sh
python3 tools/m1.py build --audio
python3 tools/m1.py reference --capture audio-reference-new
python3 tools/m1.py native --audio --renderer optimized --capture audio-native-new
python3 tools/m1.py native --audio --renderer optimized \
  --audio-device-rate 32000 --capture audio-native-32000-new
python3 tools/compare_audio.py \
  local/captures/audio-reference-new/audio.wav \
  local/captures/audio-native-new/audio.wav
python3 -m unittest discover -s tests -v
```

The audio binary lives under `local/build/demo-1-1-audio/`. Captures retain
the source/ROM/route/binary receipts, complete WAV, final `audio-stats.json`,
periodic `audio-stats.txt`, timing observations, and scene snapshots. The
comparison tool rejects a native WAV whose adjacent stats report an incomplete
history. It requires matching sample rates and performs no implicit resampling.

Final local evidence:

- `local/captures/audio-reference`
- `local/captures/audio-native-full`
- `local/captures/audio-native-32000`
- `local/reports/audio-comparison.json`
- `local/reports/audio-device-rate-comparison.json`
- `local/reports/audio-instrumentation-state-comparison.json`

The four analyzer tests check known delay direction, silence without an
invented alignment, PCM measurements, and incomplete-history rejection.
All **16 project tests pass**.
