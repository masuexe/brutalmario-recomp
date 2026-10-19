# demoOnly1 audio synchronization after practice startup

The user reported growing A/V delay followed by intermittent sound and video
when launching `python3 tools/play_demo_only1.py --select-level` with the
all-completion practice option enabled. The selected destination and physical
audio-device logs were not supplied. The automated practice reproduction uses
Athletic Special, all-completion enabled, followed by 7,200 normally paced
frames (about two minutes). It uses isolated config/save directories.

The user subsequently reported that picture and sound still stuttered; the
previous automated results did not establish a fix for that real-device
failure. The later device-backpressure investigation below addresses an
additional blocking path found in the actual desktop report.

## Causes and changes

Practice scripts accelerate the initial menu and map navigation with
`turbo on`, then hand control back with `turbo off`. The desktop host did not
call the runtime's existing `RtlAudioSetFastForward` API. Thus acceleration
filled the 8,192-sample DSP ring, while its stale audio was never explicitly
removed at handoff. A script also changed turbo after the host had already
calculated its pacing mode for that iteration.

The desktop patch now notifies the runtime on every frame, including its
existing recovery interval. It clears the host mixer block (and SDL3 stream)
and resets the pacing deadline when returning to normal speed. Script changes
take effect on the same iteration. The existing runtime trims obsolete PCM
to its 2,136-native-sample cushion and applies its continuity ramp. Guest CPU,
APU, ROM, and completion-cheat logic are unchanged. Shutdown logs now include
produced/consumed/discarded samples, underflows, and remaining queue length.

A separate scheduling error compounded the issue under intermittent load:
`host_clock.c` scheduled the next simulation at `now + one frame` whenever
work finished late. Repeated misses therefore discarded guest time and added
an idle frame after already overdue work. The clock now retains the original
phase for delays within four frame periods, allowing short bursts to catch
up. Longer suspensions abandon old debt at `now`; they do not enqueue seconds
of catch-up or impose another idle frame. The explicit loader debt override
and guest elapsed-period accounting remain supported.

## Verification

The pinned overrides are the extended
`patches/runtime/0006-allow-startup-without-audio.patch` and the new
`patches/runtime/0007-fix-host-clock-catchup.patch`.

- The repeated-turbo integration regression requires two handoffs, checks
  actual guest-frame progress, observes stale-PCM discards, and verifies a
  queue below the host high-water mark after recovery.
- The deterministic clock regression models ten minutes of intermittent
  scheduling jitter, a long suspension, explicit loader debt, and sustained
  overload. It fails against the pinned original clock and passes with the
  override.
- In the practice reproduction, the host retired 6,056 stale sample frames at
  handoff. During the following two minutes it recorded zero output
  underflows and zero missing output frames. DSP overflow drops accumulated
  only during acceleration, then remained constant; they are distinct from
  the deliberate handoff discard.
- A separate display-jitter comparison injects a 40 ms delay into every 20th
  `SDL_RenderPresent`, using the same dummy audio/video backends and 32,000 Hz
  device setting for both binaries. This isolates late-frame recovery from
  guest logic and audio-device differences. Both runs executed 2,400 frames:

  | Measurement | Previous host | Fixed host |
  | --- | ---: | ---: |
  | Wall time | 43.599 s | 40.395 s |
  | Underflows after the first second | 202 | 0 |
  | Missing output frames at last periodic sample | 92,324 | 2,132 |
  | Output-ring overflow drops | 0 | 0 |

  The fixed host's four initial underflows / 2,132 missing frames all belong
  to startup priming and do not grow during the jitter test. Periodic counters
  describe the final one-second sample, rather than an invented exact exit
  snapshot for the old binary. The final build passes all 47 project tests.

The dummy device validates queue delivery and scheduling, not a physical
sound card or subjective listening. There remains a deliberate scheduling
cushion of at least approximately 67 ms plus the device buffer. Larger output
blocks require a larger native cushion, as described in the RDP follow-up
below; this fix does not claim zero audio latency. Hosts too slow to sustain guest execution can still
stutter.

Local measurements:

- `local/diagnostics/audio-sync-practice-before/`
- `local/diagnostics/audio-sync-practice-after/`
- `local/diagnostics/audio-jitter/before40/`
- `local/diagnostics/audio-jitter/after40/`
- `local/reports/demo-only-1/audio-sync-tests.log`

Rebuild and check:

```sh
python3 tools/m1.py build --target demo-only-1
python3 -m unittest discover -s tests -v
python3 tools/play_demo_only1.py --select-level
```

## Follow-up: blocked PulseAudio/RDP delivery

The actual latest practice report was found at
`local/play/demo-only-1/practice/session-qzildii9/last_run_report.json`.
It identifies X11, PulseAudio, the `RDP Sink` output, 32,000 Hz / 512 output
frames, and the World 1 castle practice destination with completion enabled.
Between its 10,800- and 14,400-frame heartbeats, 3,600 frames took 73.912 s.
The final DSP output queue was completely full at 8,192 frames. The earlier
dummy-device jitter checks did not model a blocked audio consumer.

`RtlApuUnlock` used to wait for the device whenever its queue exceeded 4,096
frames. A stalled consumer could therefore add a 250 ms timeout to a guest
frame. Its callback-based rearming allowed these waits to recur under
intermittent delivery. Thus a problem in output delivery also stalled video.

The host now releases the APU mutex without waiting for queue consumption.
After each normally paced guest frame it checks the output backlog. If it
exceeds the 4,096-frame latency bound, `RtlAudioTrimBacklog` retains the most
recent 2,136 frames and schedules a 128-output-frame continuity ramp from the
last delivered sample. It does not alter CPU, SPC, or DSP synthesis state.
These deliberate stale-output discards have their own `backlog_discarded` /
`backlog_events` counters, separate from true ring overflows and turbo cleanup.
This extends runtime patches 0004 and 0006, with updated pinned hashes.

A test-only SDL shim delays an audio callback for 500 ms every 30 callbacks,
after a short startup warm-up. Under this identical failing-device scenario:

| Measurement, 1,200 guest frames | Previous host | Fixed host |
| --- | ---: | ---: |
| Wall time | 30.717 s | 19.951 s |
| 99th-percentile guest-frame service | 253.066 ms | 2.956 ms |
| Maximum guest-frame service | 253.963 ms | 4.372 ms |
| Guest frames over 50 ms | 60 | 0 |
| DSP ring overflow drops | 137,529 | 0 |

The fixed host deliberately retired 305,961 stale output frames, because
this test's device is intentionally unavailable for roughly half the run.
This shows that a blocked consumer cannot throttle gameplay and that the
queue recovers to recent audio. It does **not** claim uninterrupted physical
sound while the output device itself is blocked. The new integration
regression fails the earlier host's repeated 250 ms guest-frame waits; a
separate C regression verifies the retained PCM window, unchanged DSP state,
continuity-ramp setup, and wrapping ring counters. All 49 project tests pass.

New practice launches automatically retain `audio-stats.txt` (once per
second) and `frame-timing.csv` (bounded in-memory capture written at exit)
inside their isolated session directory. Explicit diagnostic environment
settings remain honored. These files allow a further real-desktop report to
distinguish device delivery, CPU/PPU work, and presentation stalls.

Local evidence is under `local/diagnostics/audio-device-stall/`, including the
before/after binaries' logs, frame timings, and `comparison.json`. The test
shim is checked in as `tests/host_audio_stall.c`; it only loads into regression
runs through `LD_PRELOAD` and is not part of the game executable.

A further run replayed that actual World 1 castle / all-completion startup
script with the user's 960×720 renderer configuration, offscreen video and
dummy audio. After turbo handoff it completed 10,800 normally paced frames
(about three minutes), with zero underflows or missing output frames. Guest
service p99 was 3.183 ms, maximum 23.501 ms, with no guest frames over 50 ms.
Presentation p99 was 2.052 ms. The bounded queue performed 14 stale-backlog
recoveries; true ring drops remained constant after accelerated startup.
Evidence is in `local/diagnostics/audio-device-stall/practice-world1-long/`.
This uses the actual session's input/config but still does not substitute
for listening to its physical RDP output.

## Follow-up: RDP transport blocks and native device rate

After the user confirmed smooth video but continuing audio interruptions,
`session-n8lsog8l` showed normal consumption for about 70 seconds, followed by
a collapse to approximately one or two render calls per second. Guest
production continued at about 32,040 native samples/s. This is different from
an underrun in the emulated DSP: when the output callback stops arriving, its
underrun counter cannot describe the missing physical playback.

Read-only queries of the actual PulseAudio server identified an s16 stereo
44,100-Hz RDP sink. With the game's 32,000-Hz / 512-frame request, PulseAudio
used server-side `ffmpeg` resampling and a 4 ms requested sink latency. The
same collapse was reproduced against the real output device. A control that
only increased the block to 2,048 frames ran 150 normally paced seconds
without the consumption collapse, but retained internal underruns because
the original fixed native cushion was almost the size of a whole request.

For the SDL2 PulseAudio backend, the desktop host now queries the default
output's metadata. If its description contains `RDP`, it requests that
sink's native rate (within the supported range) and a minimum 2,048-frame
block. It leaves the stored config preference unchanged. The internal native
prefill is the greater of 2,136 samples and two complete device requests plus
two interpolation samples; the high-water mark includes an additional device request and guest block
so normal callback-sized bursts do not trigger unnecessary PCM discards.
The runtime uses this same target for priming, occupancy control and
fast-forward recovery. Thus enlarging the backend block cannot silently
leave a smaller, incompatible native queue. The DSP ring still bounds the
cushion, and device handling cannot block the video thread.

On this RDP device that negotiates 44,100 Hz / 2,048 output frames, a native
prefill of 2,978 samples (about 93 ms), and high-water mark 5,000. PulseAudio
reports no server resampling and an 11.610 ms requested sink latency. These
are observed negotiated parameters, not a change to the guest APU clock.
`SNESRECOMP_RDP_AUDIO=0` disables this device-specific adjustment for controlled
comparisons. Other output backends keep their configured output parameters;
the internal target can still grow to accommodate a larger requested block.

The upstream behavior was checked in the pinned
[SDL 2.30 PulseAudio backend](https://github.com/libsdl-org/SDL/blob/release-2.30.0/src/audio/pulseaudio/SDL_pulseaudio.c)
and the installed version of
[WSLg's RDP sink module](https://github.com/microsoft/PulseAudio-mirror/blob/c33051f2296af748ac5cd13e51abfac4d129e4c7/src/modules/rdp/module-rdp-sink.c).
SDL derives the PulseAudio buffer request from its output block, and the RDP
module uses requested sink latency to size its transport chunks. This
supports the parameter choice; it does not establish every underlying RDP
failure mechanism.

New regressions verify RDP metadata detection, actual device rate/block
negotiation, the explicit opt-out, bounded native targets, and turbo cleanup
using the negotiated cushion. All 50 project tests pass. Real-device captures
and comparisons are retained under `local/diagnostics/rdp-audio/`.

The full RDP profile first completed 180 normally paced seconds with no
underflows or missing output frames. A final pass added a complete device
request of headroom above the queue target, avoiding false stale-queue
recovery at ordinary callback boundaries. This final binary then ran another
120 normally paced seconds on the real RDP device. There were no backlog
discards and no new underruns after startup (the three initial startup
underflows totaled 2,205 output frames before interactive handoff). The user
confirmed hearing the test with no interruptions; sound then stopped when
the scripted test exited normally. Both runs include accelerated menu/map
startup in addition to their stated normally paced durations.

For the final run, a five-second PulseAudio recording was restricted to the
game's specific sink-input ID. It contained 221,184 stereo frames, RMS 653,
peak 3,116, and no exact stereo-silence runs, confirming that the test fed
actual nonzero game audio rather than an empty stream. The final comparison
is in `local/diagnostics/rdp-audio/comparison.json`; the final run and filtered
monitor capture are under `native44100-headroom/`. All 50 project tests and
the final eight host integration checks pass, and the build receipt matches
the executable used by `tools/play_demo_only1.py`.

## Follow-up: failure after six minutes and Windows native output

The user subsequently observed audio stuttering about 5 minutes 50 seconds
after startup. The earlier two- and three-minute RDP runs therefore did not
establish long-term stability. In `session-5yesgjmq`, guest audio production
remained normal while callback consumption collapsed near 360 seconds.
Changing only PulseAudio's requested latency to 40 ms also failed in a longer
real-device run and is not enabled by the project.

These observations point to the WSLg/RDP output path, not a demonstrated
hardware fault. The exact transport failure is unresolved; the project's
choice of backend and buffering still determines whether it encounters that
path. Increasing its buffers alone is insufficient.

On WSL with the WSLg PulseAudio server, `tools/play_demo_only1.py` now selects
project-local Windows native output automatically. `tools/windows_audio.py`
starts `recomp/windows_audio.ps1` through the installed Windows PowerShell.
The helper uses Windows' built-in `waveOut` API on the default Windows output
device, at 44,100 Hz, signed 16-bit stereo. It needs no additional packages
and changes no services, device preferences, volume settings, or registry
values. Explicit `SDL_AUDIODRIVER` choices and `EnableAudio=0` remain honored.

The Linux host leaves SDL's dummy device paused and sends PCM from a separate
audio thread into a pipe. The helper queues three 512-frame buffers
(about 35 ms maximum device queue); it grants another completion credit only
after Windows marks a submitted buffer played. Credits are the sole output
clock and bound queued PCM even if WSL interoperability buffers the pipe
ahead. The thread waits for a credit before taking PCM from the guest ring.
Waiting happens outside the APU mutex, so a slow output device cannot throttle
video. The existing bounded native queue retains recent audio after a long
output stall. Polling allows shutdown to interrupt a missing completion
without waiting for the helper to time out.

An initial native-output candidate completed ten minutes without the sustained
consumption collapse; the user confirmed hearing uninterrupted sound past
the previous failure point. It nevertheless recorded 18 post-startup
underruns (11,044 missing output frames, about 250 ms in total). That candidate
used SDL's dummy callback timer in addition to device completion credits.
The final implementation removes this extra timer. SDL's timer behavior can
be checked in its [audio thread implementation](https://github.com/libsdl-org/SDL/blob/release-2.30.0/src/audio/SDL_audio.c).
This is a project-side scheduling correction, not evidence of faulty hardware.

The completion-only candidate also completed ten minutes, but the user heard
one very short interruption, consistent with its remaining underrun counters.
A further measurement identified a clock mismatch: over the same observation
interval, Windows QPC advanced 13.0997378 s and Linux `MONOTONIC_RAW` advanced
13.099725883 s, while corrected Linux `MONOTONIC` advanced 13.288067367 s.
The approximately 1.4% frequency difference exceeds the native resampler's
0.5% drift allowance. Raw-versus-corrected differences also varied over time.
Increasing queue capacity alone cannot correct this changing clock mismatch.

Linux output backends retain the corrected clock that matches their audio
scheduling. After successfully creating Windows native output, the host now
uses `MONOTONIC_RAW` for frame pacing, matching the measured Windows playback
clock. It selects the clock before initializing frame deadlines and retains
that choice through shutdown, including if the helper subsequently fails.
This changes neither the guest CPU/APU clock ratio nor system clock settings.

The Windows path also uses six guest audio blocks of native prefill: 3,204
samples (100 ms), 33 ms above the original minimum. Its high-water mark of
4,854 samples leaves room for a full three-completion burst plus a guest
block. The helper's own queue remains three 512-frame blocks. This modest
latency tradeoff gives the WSL/Windows handoff additional scheduling margin.
Other backends retain their existing prefill calculations.

If Windows output cannot initialize, the launcher falls back to SDL. If the
helper exits during play, its completion channel closes and gameplay
continues without sound. The helper reports a device error after five seconds
without a buffer completion. `windows-audio.log` in the current session/build
directory records the negotiated format, submitted samples, and Windows
device position once per second. It closes when the game exits; sound ending
at that point is expected.

Use the same launch command:

```sh
python3 tools/play_demo_only1.py --select-level
```

For a controlled comparison using the SDL/WSLg path:

```sh
SNESRECOMP_WINDOWS_AUDIO=0 python3 tools/play_demo_only1.py --select-level
```

New regressions run the real built host with a simulated slow Windows
consumer, with a consumer that exits after startup, and with an invalid
helper handshake. They check guest-frame completion, correct pipe format,
clean process shutdown, and fallback. Launcher checks also verify automatic
selection, disabled audio, and fallback. All 54 project tests pass. These pipe
tests complement the real Windows device run; they cannot establish physical
sound quality by themselves.

### Final real-device verification

The final clock-matched binary completed the actual all-completion / World 1
castle practice startup and 36,000 normally paced frames, then exited normally
after 38,616 total frames. Windows native playback ran for 606.821 seconds,
exceeding the reported 5 minute 50 second failure point. The test used the
user's 960×720 configuration with offscreen video and test volume 15; sound
was delivered to the real Windows output device.

After the first 15 seconds there were zero additional underruns, missing
output frames, or ring drops. The three initial underruns totaled 2,205 output
frames before interactive handoff. There were no stale-backlog discards or
recovery events at all. Windows' reported submitted queue stayed within the
three-buffer bound (observed maximum 1,512 frames). Normal guest service p99
was 3.118 ms and maximum 5.083 ms. The complete 54-test suite also passed while
this final real-device run was playing.

Evidence is retained under
`local/diagnostics/rdp-audio/windows-native/raw-clock-long10m/`, with host
output in `raw-clock-long-host.log` and a machine-readable summary in
`final-verification.json` alongside that directory. Read-only clock probes
are retained as `clock-comparison.txt` and `windows-clock-comparison.txt` in
the same parent directory. The runtime patches reconstruct their pinned
results cleanly and the build receipt matches the tested executable.

This establishes stable playback for this ten-minute reproduction. Longer
interactive sessions and perceptual A/V alignment remain separate checks;
the earlier short runs were insufficient to establish either.
## Follow-up: demo-1-1 direct launch bypassed the native output path

The user reported that the 63-variant demo-1-1 candidate again showed A/V
desync shortly after startup and audio stuttering after the window lost
focus, while gameplay and graphics were correct.

`local/build/demo-1-1/last_run_report.json` from that session records
`audio output[0]: RDP Sink`, `RDP audio compatibility: rate=44100
samples=2048`, and no `frame clock: MONOTONIC_RAW` breadcrumb. The
executable therefore ran on SDL's WSLg PulseAudio path. That is expected:
`tools/play_demo_only1.py` is the only launcher that starts the Windows
waveform helper, and the demo-1-1 instructions tell the user to run
`local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` directly. The binary
contains both fixes, but the fixes engage only when the host receives
`SNESRECOMP_WINDOWS_AUDIO_FD` / `_ACK_FD`. This is a launcher gap, not a
regression in the audio code.

`tools/play_demo_1_1.py` now applies the same verified path to demo-1-1:
receipt and ROM verification, the executable-relative config, and
`windows_audio.run` with an `--no-windows-audio` opt-out for controlled
comparison. `tests/test_play_demo_1_1.py` covers native launch, forced SDL,
disabled audio, unavailable helper, and stale-receipt rejection.

### Measured difference on this machine

Both paths ran the same executable and config with offscreen video, reading
the per-second audio counters:

| Path | Duration | Produced | Consumed | Result |
| --- | ---: | ---: | ---: | --- |
| SDL / WSLg RDP sink | 178 s | 32,040/s | 18,190/s | consumption collapsed to ~1.6k/s at t≈98 s |
| Windows native pipe | 237 s | 31,710/s | 31,673/s | stable, no new underruns after startup |

The RDP collapse reproduces the documented transport failure. Its consumption
rate fell by more than an order of magnitude within one second while guest
production stayed at 32,040/s, which is the signature of a blocked output
consumer rather than a DSP underrun.

`MONOTONIC` and `MONOTONIC_RAW` were also measured on this host: over ten
seconds they differed by about 0.7%, exceeding the audio servo's ±0.5%
range. The Windows path selects `MONOTONIC_RAW`, so the frame clock and the
output clock agree. On the RDP path the corrected clock is used, so a drift
the servo cannot absorb accumulates as A/V offset. That is consistent with
desync appearing early and worsening.

### Focus loss

No focus-loss handling exists in the host: the runtime has no
`SDL_WINDOWEVENT` case at all, so losing focus changes neither simulation
nor audio. The observed post-focus stutter is therefore not a code path that
pauses and resumes audio. It is more likely explained by the RDP transport
itself being throttled while the window is unfocused, which this project
cannot fix. The Windows native path does not depend on that transport.

These measurements establish which path this host's RDP sink fails on. They
do not establish that the RDP transport can be made reliable from inside the
emulator, and they are not a substitute for listening.

Launch the candidate with:

```sh
python3 tools/play_demo_1_1.py
```

For a controlled comparison on the old path:

```sh
python3 tools/play_demo_1_1.py --no-windows-audio
```


### User acceptance of the demo-1-1 launcher follow-up

The user subsequently reported that the demo-1-1 audio stutter issue was fixed
and the resulting build tested without issues. This closes the pending audible
checkpoint for the current 63-variant build within that reported session.
Exact duration, individual perceptual checks and the launch command were not
separately supplied. The recommended interactive entry remains
`python3 tools/play_demo_1_1.py`; direct executable launch does not select the
Windows-native path automatically. The launcher's five unit tests also pass.
