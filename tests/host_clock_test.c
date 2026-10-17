/* Deterministic scheduling tests: jitter must not slow guest time. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "host_clock.h"

int main(void) {
  SnesHostClock clock;
  const double hz = SNES_HOST_NTSC_HZ;
  const double period = 1.0 / hz;
  snes_host_clock_reset(&clock, 0, hz, 60);
  double now = 0;
  /* A desktop occasionally dispatches a frame 15 ms late. With a 4 ms
   * frame cost that misses the next deadline, but the host has ample spare
   * capacity to catch up. Reanchoring to now+period loses time every time. */
  for (unsigned i = 0; i < 36000; ++i) {
    now = fmax(now, clock.next_simulation);
    if (i % 60 == 59) now += 0.015;
    now += 0.004;
    snes_host_clock_simulation_done(&clock, now, false, 1);
  }
  assert(fabs(clock.next_simulation - 36000 * period) < 1e-7);
  assert(clock.simulation_frames == 36000);

  /* A long suspension abandons old debt without adding a fresh empty
   * frame period; the next guest frame may start immediately. */
  now += 2;
  snes_host_clock_simulation_done(&clock, now, false, 1);
  assert(fabs(clock.next_simulation - now) < 1e-9);
  assert(snes_host_clock_simulation_due(&clock, now));

  /* The explicit loader/debt override still preserves the full timeline. */
  snes_host_clock_reset(&clock, 0, hz, 60);
  snes_host_clock_simulation_done(&clock, 2, true, 3.5);
  assert(fabs(clock.next_simulation - 3.5 * period) < 1e-9);

  /* Consistently expensive work is CPU limited, not cost+one extra frame. */
  snes_host_clock_reset(&clock, 0, hz, 60);
  now = 0;
  for (unsigned i = 0; i < 1000; ++i) {
    now = fmax(now, clock.next_simulation) + 0.020;
    snes_host_clock_simulation_done(&clock, now, false, 1);
    assert(clock.next_simulation <= now);
    assert(now - clock.next_simulation <= 4 * period + 1e-9);
  }
  assert(fabs(now - 20) < 1e-9);
  puts("host clock: jitter, bounded debt, loader override, sustained overload passed");
  return 0;
}
