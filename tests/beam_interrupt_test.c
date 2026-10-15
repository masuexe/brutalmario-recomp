/* ROM-free scheduler contract: a long handler keeps its real stack frame
 * while spanning host calls. The bridge and beam are controlled doubles. */
#include <assert.h>
#include <stdio.h>
#include "beam_frame_driver.h"
#include "cpu_state.h"
#include "snes/snes.h"

#define FIELD 357368ull
#define EDGE (225ull * 1364)
#define MAIN 0x008000u
#define HANDLER 0x009000u
#define CONTINUE 0x009010u

CpuState g_cpu;
static Snes machine;
Snes *g_snes = &machine;
Ppu *g_ppu;
static uint8_t ram[65536];
static uint64_t deadline, work;
static uint32_t resume;
static int completed, deliveries;

void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 value) {
    (void)cpu; assert(bank == 0); ram[addr] = value;
}
uint8_t snes_read(Snes *snes, uint32_t addr) {
    (void)snes;
    return (addr == 0xfffc || addr == 0xffea || addr == 0xffee) ? 0 :
           (addr == 0xfffd ? 0x80 : 0x90);
}
void snes_sync_master_clock(Snes *snes, uint64_t clock) {
    snes->beamMasterLast = clock;
    snes->vPos = (clock % FIELD) / 1364;
    snes->hPos = clock % 1364;
}
void snes_advance_master_cycles(Snes *snes, uint32_t clocks) {
    snes_sync_master_clock(snes, snes->beamMasterLast + clocks);
}
uint32_t snes_master_clocks_until_line(const Snes *snes, uint32_t line) {
    uint64_t phase = snes->beamMasterLast % FIELD;
    return (line * 1364ull + FIELD - phase) % FIELD;
}
uint32_t snes_master_clocks_until_irq(const Snes *snes) { (void)snes; return 0; }
void snes_set_hdma_beam_enabled(Snes *snes, bool enabled) { (void)snes; (void)enabled; }
void snes_set_raster_irq_beam_enabled(bool enabled) { (void)enabled; }
void snes_refresh_exempt(void) {}
void cart_sync_coprocessors(Cart *cart, uint64_t clock) { (void)cart; (void)clock; }
int cx4_irq_pending(const Cx4 *cx4) { (void)cx4; return 0; }
bool sa1_cpu_irq_pending(const Sa1 *sa1) { (void)sa1; return false; }
bool ppu_checkOverscan(Ppu *ppu) { (void)ppu; return false; }
void ppu_handleVblank(Ppu *ppu) { (void)ppu; }
void ppu_rasterBegin(Ppu *ppu) { (void)ppu; }
void ppudma_note_interrupt(int nmi) { assert(nmi); ++deliveries; }
void interp_bridge_set_master_deadline(uint64_t clock) { deadline = clock; }
uint32_t interp_bridge_lle_resume_pc(void) { return resume; }
int interp_bridge_lle_took_wai(void) { return 0; }

static void run(CpuState *cpu, uint32_t pc, bool bounded) {
    if (pc == HANDLER) {
        assert(cpu->S == 0x1fb);
        machine.nmiEnabled = false; /* Guest disables NMI during its upload. */
        work = 3 * FIELD + 1234;
    }
    if (pc == HANDLER || pc == CONTINUE) {
        uint64_t budget = bounded ? deadline - cpu->master_cycles : work;
        uint64_t used = work < budget ? work : budget;
        cpu->master_cycles += used;
        work -= used;
        if (work) {
            assert(cpu->S == 0x1fb);
            resume = CONTINUE;
        } else {
            /* Architectural native RTI: restore P, PC and PB. */
            cpu->P = ram[++cpu->S];
            uint32_t restored = ram[++cpu->S];
            restored |= (uint32_t)ram[++cpu->S] << 8;
            restored |= (uint32_t)ram[++cpu->S] << 16;
            assert(restored == MAIN && cpu->S == 0x1ff);
            resume = restored;
            ++completed;
        }
    } else { assert(pc == MAIN); resume = MAIN; }
    if (bounded && cpu->master_cycles < deadline) cpu->master_cycles = deadline;
    snes_sync_master_clock(&machine, cpu->master_cycles);
}
int interp_bridge_run_until_quiescent(CpuState *cpu, uint32_t pc) {
    run(cpu, pc, true); return 1;
}
int interp_bridge_run_interrupt(CpuState *cpu, uint32_t pc) {
    ppudma_note_interrupt(machine.inNmi);
    run(cpu, pc, false); return 1;
}

int main(void) {
    g_cpu.S = 0x1ff;
    snes_beam_frame_driver_reset();
    snes_beam_frame_driver_run_frame();
    assert(g_cpu.master_cycles == EDGE);
    machine.nmiEnabled = true;
    for (int frame = 1; frame <= 4; ++frame) {
        snes_beam_frame_driver_run_frame();
        assert(g_cpu.master_cycles == EDGE + frame * FIELD);
        assert(machine.vPos == 225 && machine.hPos == 0);
        assert(deliveries == 1);
        assert(completed == (frame == 4));
        assert(g_cpu.S == (frame == 4 ? 0x1ff : 0x1fb));
    }
    puts("long interrupt preserves field boundaries, continuation and stack");
    return 0;
}
