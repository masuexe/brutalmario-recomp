/* Host timing support for explicitly selected, instruction-paced ROM leaves. */
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"

bool M1AotBusContextSupported(CpuState *cpu, unsigned max_dp, int pointer) {
    /* Keep pointer and return-frame reads in WRAM; unusual contexts fall back
     * at entry rather than acquiring extra MMIO side effects for validation. */
    if (cpu->emulation || cpu->D > 0x1fff - max_dp || cpu->S > 0x1ffd)
        return false;
    if (pointer >= 0) {
        uint16_t dp = cpu->D + pointer;
        uint32_t address = cpu_read16(cpu, 0, dp) |
                           ((uint32_t)cpu_read8(cpu, 0, dp + 2) << 16);
        if (cpu_wram_offset(address >> 16, address) < 0 &&
            (address & 0xffff) < 0x8000)
            return false;
    }
    return true;
}

/* Guard each live indexed address before charging or accessing it. */
bool M1AotBusAddressSupported(uint32_t address, unsigned width) {
    for (unsigned i = 0; i < width; ++i) {
        uint32_t at = (address + i) & 0xffffff;
        if (cpu_wram_offset(at >> 16, at) < 0 && (at & 0xffff) < 0x8000)
            return false;
    }
    return true;
}

/* This extension qualifies WRAM stores only. MMIO and cartridge writes
 * retain interpreter ownership at the current instruction. */
bool M1AotBusWriteSupported(uint32_t address, unsigned width) {
    for (unsigned i = 0; i < width; ++i) {
        uint32_t at = (address + i) & 0xffffff;
        if (cpu_wram_offset(at >> 16, at) < 0) return false;
    }
    return true;
}

void M1AotBusBoundary(CpuState *cpu) {
    snes_refresh_charge();
    cpu->coprocessor_master_cycles = cpu->master_cycles;
    if (g_snes) snes_sync_master_clock(g_snes, cpu->master_cycles);
}
