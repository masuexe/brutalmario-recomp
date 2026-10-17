# demoOnly1 audio synchronization after practice startup

The user reported growing A/V delay followed by intermittent sound and video
when launching `python3 tools/play_demo_only1.py --select-level` with the
all-completion practice option enabled. The selected destination and physical
audio-device logs were not supplied. The automated practice reproduction uses
Athletic Special, all-completion enabled, followed by 7,200 normally paced
frames (about two minutes). It uses isolated config/save directories.

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
cushion of approximately 67 ms plus the device buffer; this fix does not claim
zero audio latency. Hosts too slow to sustain guest execution can still
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
