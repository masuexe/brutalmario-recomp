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

/* Only these two byte ports have qualified instruction-start event timing.
 * Preserve the WRAM guard for every other store and for non-system banks. */
bool M1AotPaletteWriteSupported(uint32_t address, unsigned width) {
    if (width != 1) return false;
    if (M1AotBusWriteSupported(address, width)) return true;
    unsigned bank = address >> 16, reg = address & 0xffff;
    return (bank < 0x40 || (bank >= 0x80 && bank < 0xc0)) &&
           (reg == 0x2121 || reg == 0x2122);
}

/* Native M1 STA abs: three fetches and one byte transfer, no internal cycles.
 * PPU effects see the same pre-op clock as bridge_bus_write; charge the full
 * instruction afterward without ever rewinding the CPU or beam clock.
 * A DB that resolves these operands to WRAM retains ordinary paced timing. */
void M1AotPaletteWrite8(CpuState *cpu, uint8_t bank, uint16_t reg,
                       uint8_t value, uint32_t fetch_master) {
    if (cpu_wram_offset(bank, reg) >= 0) {
        cpu->cycles += 4;
        cpu->master_cycles += fetch_master;
        cpu_write8_paced(cpu, bank, reg, value);
    } else {
        cpu_write8(cpu, bank, reg, value);
        cpu->cycles += 4;
        cpu->master_cycles += fetch_master + cpu_region_speed(((uint32_t)bank << 16) | reg);
    }
}

void M1AotBusBoundary(CpuState *cpu) {
    snes_refresh_charge();
    cpu->coprocessor_master_cycles = cpu->master_cycles;
    if (g_snes) snes_sync_master_clock(g_snes, cpu->master_cycles);
}
