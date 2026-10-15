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

/* Optional interpreted-instruction probe for the first boot-load phase.
 * Use an interpreter-only run: compiled instructions do not call this hook.
 * The clock is the pre-op master clock, not an estimate from host frames. */
static FILE *s_boot_trace;
static void M1BootTrace(uint32_t pc, int m, int x)
{
    static unsigned previous_mode;
    if (g_ram[0x100] == 3 || previous_mode == 3) {
        RtlApuLock();
        Apu *apu = g_snes->apu;
        fprintf(s_boot_trace, "%d,%llu,%u,%u,%u,%u,%u,%d,%d,%llu,%u,%u,%u,%u,%u,%u\n",
                snes_frame_counter + 1, (unsigned long long)g_cpu.master_cycles,
                pc, g_snes->vPos, g_snes->hPos, g_ram[0x100],
                g_ram[0x13], m, x, (unsigned long long)apu->portClock,
                apu->spc->pc, apu->timer[0].cycles, apu->timer[0].divider,
                apu->timer[0].counter, apu->timer[0].target,
                apu->outPorts[0] | ((unsigned)apu->outPorts[1] << 8));
        RtlApuUnlock();
    }
    previous_mode = g_ram[0x100];
}
static void M1BootTraceClose(void)
{
    if (s_boot_trace && fclose(s_boot_trace)) {
        perror("M1_BOOT_TRACE close"); exit(1);
    }
}

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
    /* These NTSC targets use the beam driver as their authoritative clock.
     * Keep the upstream frame/HLE model available for explicit diagnostics. */
    if (!getenv("SNESRECOMP_APU_MASTER_CLOCK")) {
#ifdef _WIN32
        _putenv_s("SNESRECOMP_APU_MASTER_CLOCK", "1");
#else
        setenv("SNESRECOMP_APU_MASTER_CLOCK", "1", 0);
#endif
    }
    const char *boot_trace = getenv("M1_BOOT_TRACE");
    if (boot_trace && *boot_trace) {
        s_boot_trace = fopen(boot_trace, "w");
        if (!s_boot_trace) { perror("M1_BOOT_TRACE"); exit(1); }
        fprintf(s_boot_trace, "frame,clock,pc,v,h,mode,counter13,m,x,apu_clock,spc_pc,timer0_prescaler,timer0_divider,timer0_counter,timer0_target,apu_out01\n");
        g_interp_bridge_pc_hook = M1BootTrace;
        atexit(M1BootTraceClose);
    }
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
