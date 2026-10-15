/* M1-only host instrumentation. No guest state changes. */
#include <stdio.h>
#include <stdlib.h>

/* Exported by the pinned SNESRecomp interp_bridge.c. These are different
 * units: body entries cannot be converted into a compiled-opcode fraction. */
extern unsigned long long g_interp_bridge_bounces;
extern unsigned long long g_interp_bridge_steps;

static void PrintM1Metrics(void)
{
    printf("[m1] aot_bridge_entries=%llu interpreted_opcodes=%llu\n",
           g_interp_bridge_bounces, g_interp_bridge_steps);
}

void M1MetricsRegister(void)
{
    atexit(PrintM1Metrics);
}
