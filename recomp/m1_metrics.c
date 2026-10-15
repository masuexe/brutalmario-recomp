/* M1-only host instrumentation. No guest state changes. */
#include <stdio.h>
#include <stdlib.h>
#include "cpu_state.h"
#include "snes/snes.h"
#include "audio_trace.h"
#include "snes/interp_bridge.h"
#include "common_rtl.h"

extern Snes *g_snes;

/* Desktop shutdown invokes this before destroying the APU mutex. The
 * existing API takes a coherent PCM snapshot while holding that mutex. */
void M1AudioShutdown(void)
{
    const char *dump = getenv("M1_APU_DUMP");
    if (dump && *dump && g_snes && g_snes->apu) {
        unsigned char ram[65536];
        RtlApuLock();
        memcpy(ram, g_snes->apu->ram, sizeof(ram));
        RtlApuUnlock();
        FILE *out = fopen(dump, "wb");
        if (!out) { perror("M1_APU_DUMP"); exit(1); }
        if (fwrite(ram, 1, sizeof(ram), out) != sizeof(ram) || fclose(out)) {
            fprintf(stderr, "M1_APU_DUMP: write failed\n"); exit(1);
        }
    }
    const char *wav = getenv("M1_AUDIO_WAV");
    const char *report = getenv("M1_AUDIO_REPORT");
    if (!wav || !*wav) return;
    uint64_t start = 0, count = 0;
    AudioTraceStats stats;
    audio_trace_get_stats(&stats);
    int result = audio_trace_dump_wav(wav, 0, 0, &start, &count);
    if (report && *report) {
        FILE *out = fopen(report, "w");
        if (!out) { perror("M1_AUDIO_REPORT"); exit(1); }
        fprintf(out,
                "{\"wav_result\":%d,\"start_sample\":%llu,\"sample_frames\":%llu,"
                "\"produced\":%llu,\"consumed\":%llu,\"dropped\":%llu,"
                "\"dropped_audible\":%llu,\"output_underflows\":%llu,"
                "\"output_missing_frames\":%llu,\"output_priming\":%llu,"
                "\"produced_cpu\":%llu,\"produced_audio\":%llu}\n",
                result, (unsigned long long)start, (unsigned long long)count,
                (unsigned long long)stats.produced, (unsigned long long)stats.consumed,
                (unsigned long long)stats.dropped, (unsigned long long)stats.dropped_audible,
                (unsigned long long)stats.output_underflows,
                (unsigned long long)stats.output_missing_frames,
                (unsigned long long)stats.output_priming,
                (unsigned long long)stats.produced_cpu, (unsigned long long)stats.produced_audio);
        if (fclose(out)) { perror("M1_AUDIO_REPORT close"); exit(1); }
    }
    if (result || start != 0 || count == 0) {
        fprintf(stderr, "[m1] incomplete audio capture: result=%d start=%llu count=%llu\n",
                result, (unsigned long long)start, (unsigned long long)count);
        exit(1);
    }
}

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
            fprintf(trace, "frame,phase,cpu_clock,beam_clock,vpos,hpos,counter13,counter14,mode,nmi_enabled,resume_pc,stack,irq_enabled,irq_pending,irq_masked,spc_pc,apu_in,apu_out,apu_clock\n");
        }
    }
    if (!trace || !g_snes) return;
    if (phase[0] == 'b') ++frame;
    Apu *apu = g_snes->apu;
    unsigned in = 0, out = 0;
    RtlApuLock();
    if (apu) for (unsigned i = 0; i < 4; ++i) {
        in |= (unsigned)apu->inPorts[i] << (8 * i);
        out |= (unsigned)apu->outPorts[i] << (8 * i);
    }
    unsigned spc_pc = apu && apu->spc ? apu->spc->pc : 0;
    unsigned long long apu_clock = apu ? apu->portClock : 0;
    RtlApuUnlock();
    fprintf(trace, "%u,%s,%llu,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%llu\n",
            frame, phase, (unsigned long long)g_cpu.master_cycles,
            (unsigned long long)g_snes->beamMasterLast,
            g_snes->vPos, g_snes->hPos, g_ram[0x13], g_ram[0x14],
            g_ram[0x100], g_snes->nmiEnabled, interp_bridge_lle_resume_pc(),
            g_cpu.S, g_snes->hIrqEnabled || g_snes->vIrqEnabled,
            g_snes->inIrq, g_cpu._flag_I, spc_pc, in, out, apu_clock);
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
#if defined(M1_SEPARATE_ECHO_DEFAULT) && M1_SEPARATE_ECHO_DEFAULT
    /* Target-specific compatibility also applies when launching the binary
     * directly. An explicit 0 remains available for hardware diagnostics. */
    if (!getenv("SNESRECOMP_SEPARATE_ECHO")) {
#ifdef _WIN32
        _putenv_s("SNESRECOMP_SEPARATE_ECHO", "1");
#else
        setenv("SNESRECOMP_SEPARATE_ECHO", "1", 0);
#endif
    }
#endif
    atexit(PrintM1Metrics);
}
