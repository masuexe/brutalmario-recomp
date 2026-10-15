/* M1-only host instrumentation. No guest state changes. */
#include <stdio.h>
#include <stdlib.h>
#include "cpu_state.h"
#include "snes/snes.h"

extern CpuState g_cpu;
extern Snes *g_snes;
extern unsigned char g_ram[0x20000];

/* Optional host observations. No guest memory or clock writes. */
void M1TimingSample(const char *phase)
{
    static FILE *trace;
    static int initialized;
    static unsigned frame;
    if (!initialized) {
        const char *path = getenv("M1_TIMING_TRACE");
        initialized = 1;
        if (path && *path) {
            trace = fopen(path, "w");
            if (!trace) { perror("M1_TIMING_TRACE"); exit(1); }
            fprintf(trace, "frame,phase,cpu_clock,beam_clock,vpos,hpos,counter13,counter14,mode,nmi_enabled\n");
        }
    }
    if (!trace || !g_snes) return;
    if (phase[0] == 'b') ++frame;
    fprintf(trace, "%u,%s,%llu,%llu,%u,%u,%u,%u,%u,%u\n",
            frame, phase, (unsigned long long)g_cpu.master_cycles,
            (unsigned long long)g_snes->beamMasterLast,
            g_snes->vPos, g_snes->hPos, g_ram[0x13], g_ram[0x14],
            g_ram[0x100], g_snes->nmiEnabled);
}

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
