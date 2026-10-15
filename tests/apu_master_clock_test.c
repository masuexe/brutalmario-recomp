/* Exercise the actual patched runtime's clock selection and boundary sync.
 * Unrelated runtime sections are discarded by the linker. */
#include <assert.h>
#include <math.h>
#include M1_RUNTIME_SOURCE

CpuState g_cpu;
Snes *g_snes;
int snes_frame_counter;
static Snes machine;
static Apu apu;
static uint64_t observed;
void RtlApuLock(void) {}
void RtlApuUnlock(void) {}

bool apu_runToGuestCycle(Apu *a, uint64_t target, uint32_t limit) {
    assert(a == &apu && limit > 0);
    observed = target; a->portClock = target; return true;
}
void audio_trace_set_producer(int producer) { (void)producer; }
void audio_trace_on_guest_sync(int boundary, uint64_t cycles) {
    assert(boundary == 1); (void)cycles;
}
uint64_t snesrecomp_host_now_ns(void) { return 0; }

int main(int argc, char **argv) {
    assert(argc == 2);
    bool master = argv[1][0] == '1';
    setenv("SNESRECOMP_APU_MASTER_CLOCK", argv[1], 1);
    g_snes = &machine; machine.apu = &apu;
    RtlEnableExtendedFrameTiming();
    /* First call ends at V=225, not at a full 262-line field. */
    g_cpu.master_cycles = 225ull * 1364;
    rtl_apu_clock_begin(&g_apu_frame_clock, 0);
    uint64_t before = rtl_apu_guest_cycle();
    rtl_sync_apu_frame_boundary();
    if (master) {
        assert(before == 14650 && observed == before);
        assert(RtlLastFramePeriods() < 0.86);
    } else {
        assert(before == 14674 && observed == 17088); /* legacy default */
        assert(RtlLastFramePeriods() == 1.0);
    }
    /* Repeated host boundaries must not add rounding/minimum drift. */
    for (unsigned field = 1; field <= 1000; ++field) {
        rtl_apu_clock_begin(&g_apu_frame_clock, g_cpu.master_cycles);
        g_cpu.master_cycles += 357368;
        uint64_t expected = master ? g_cpu.master_cycles * 15664ull / 328125ull
                                   : g_apu_frame_clock.start_guest + 17088;
        assert(rtl_apu_guest_cycle() == expected);
        rtl_sync_apu_frame_boundary();
        assert(observed == expected);
        assert(fabs(RtlLastFramePeriods() - 1.0) < 0.00006);
    }
    if (master) {
        /* A loader spanning three fields advances exactly its elapsed clocks. */
        rtl_apu_clock_begin(&g_apu_frame_clock, g_cpu.master_cycles);
        g_cpu.master_cycles += 3 * 357368 + 1234;
        rtl_sync_apu_frame_boundary();
        assert(observed == g_cpu.master_cycles * 15664ull / 328125ull);
        assert(RtlLastFramePeriods() > 3.0);
        /* No 64-bit intermediate overflow at the maximum master timestamp. */
        assert(rtl_apu_master_cycle(UINT64_MAX) ==
               (uint64_t)(((__uint128_t)UINT64_MAX * 15664) / 328125));
    }
    return 0;
}
