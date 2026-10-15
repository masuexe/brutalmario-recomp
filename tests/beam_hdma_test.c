/* ROM-free integration: real DMA + PPU journal, controlled CPU/beam.
 * Window state must survive channel disable, skipped/repeated scanout,
 * changing table memory, and a late CPU display-register write. */
#include <assert.h>
#include <stdio.h>
#include "beam_frame_driver.h"
#include "cpu_state.h"
#include "snes/dma.h"
#include "snes/sdd1.h"
#include "ppu_test_stubs.h"

#define FIELD 357368ull
#define EDGE (225ull * 1364)
CpuState g_cpu;
Ppu *g_ppu;
static Snes machine;
static Dma dma;
static Ppu ppu;
static uint8_t pixels[256 * 224 * 4];
static uint8_t table[] = {0x81, 0x00, 0xff, 0x00};
static unsigned table_reads, transfers, observed;
static uint64_t deadline;

uint8_t snes_read(Snes *snes, uint32_t addr) {
    (void)snes;
    if (addr >= 0x6000 && addr < 0x6004) {
        ++table_reads;
        return table[addr - 0x6000];
    }
    assert(addr == 0xfffc || addr == 0xfffd);
    return addr == 0xfffd ? 0x80 : 0;
}
void snes_write(Snes *snes, uint32_t addr, uint8_t value) {
    (void)snes; (void)addr; (void)value; assert(0);
}
uint8_t snes_readBBus(Snes *snes, uint8_t addr) {
    (void)snes; (void)addr; assert(0); return 0;
}
void snes_writeBBus(Snes *snes, uint8_t addr, uint8_t value) {
    assert(snes == &machine && (addr == 0x26 || addr == 0x27));
    ++transfers;
    ppu_write(g_ppu, addr, value);
}
bool sdd1_dma_active(Sdd1 *sdd1, int channel) {
    (void)sdd1; (void)channel; assert(0); return false;
}
uint8_t sdd1_dma_get_byte(Sdd1 *sdd1, int channel) {
    (void)sdd1; (void)channel; assert(0); return 0;
}
void sdd1_dma_init(Sdd1 *sdd1, int channel, uint32_t source, uint32_t size) {
    (void)sdd1; (void)channel; (void)source; (void)size; assert(0);
}

/* Controlled beam edges, using the actual HDMA transfer implementation. */
void snes_sync_master_clock(Snes *snes, uint64_t clock) {
    while (snes->beamMasterLast < clock) {
        uint64_t pos = snes->beamMasterLast;
        unsigned h = pos % 1364;
        uint64_t next = pos + (h < 1024 ? 1024 - h : 1364 - h);
        if (next > clock) next = clock;
        snes->beamMasterLast = next;
        snes->vPos = (next % FIELD) / 1364;
        snes->hPos = next % 1364;
        if (snes->hPos == 1024 && snes->vPos < 225 && !snes->hdmaBeamOff)
            dma_doHdma(snes->dma);
        if (snes->hPos == 0) {
            if (snes->vPos == 0 && !snes->hdmaBeamOff) dma_initHdma(snes->dma);
            if (next == 224ull * 1364) {
                ppu_write(g_ppu, 0x2c, 0x10);
                ppu_write(g_ppu, 0x2d, 0x04);
            }
            if (snes->vPos == 225) ppu_rasterFieldBoundary();
        }
    }
}
void snes_advance_master_cycles(Snes *snes, uint32_t clocks) {
    snes_sync_master_clock(snes, snes->beamMasterLast + clocks);
}
uint32_t snes_master_clocks_until_line(const Snes *snes, uint32_t line) {
    return (line * 1364ull + FIELD - snes->beamMasterLast % FIELD) % FIELD;
}
uint32_t snes_master_clocks_until_irq(const Snes *snes) { (void)snes; return 0; }
void snes_set_hdma_beam_enabled(Snes *snes, bool enabled) { snes->hdmaBeamOff = !enabled; }
void snes_set_raster_irq_beam_enabled(bool enabled) { (void)enabled; }
void snes_refresh_exempt(void) {}
void cart_sync_coprocessors(Cart *cart, uint64_t clock) { (void)cart; (void)clock; }
int cx4_irq_pending(const Cx4 *cx4) { (void)cx4; return 0; }
bool sa1_cpu_irq_pending(const Sa1 *sa1) { (void)sa1; return false; }
void ppudma_note_interrupt(int nmi) { (void)nmi; assert(0); }
void cpu_write8(CpuState *cpu, uint8 bank, uint16 addr, uint8 value) {
    (void)cpu; (void)bank; (void)addr; (void)value; assert(0);
}
void interp_bridge_set_master_deadline(uint64_t clock) { deadline = clock; }
uint32_t interp_bridge_lle_resume_pc(void) { return 0x8000; }
int interp_bridge_lle_took_wai(void) { return 0; }
int interp_bridge_run_until_quiescent(CpuState *cpu, uint32_t pc) {
    assert(pc == 0x8000);
    if (!cpu->master_cycles && !machine.hdmaBeamOff) dma_initHdma(&dma);
    cpu->master_cycles = deadline;
    snes_sync_master_clock(&machine, deadline);
    return 0;
}
static void observe(const Ppu *p, unsigned line, void *context) {
    (void)context;
    assert(line >= 1 && line <= 224);
    assert(p->window1left == 0 && p->window1right == 255);
    assert(p->screenEnabled[0] == 0x15); /* late write not yet visible */
    ++observed;
}

int main(void) {
    g_snes = &machine; g_ppu = &ppu;
    machine.ppu = &ppu; machine.dma = &dma; dma.snes = &machine;
    ppu.renderBuffer = pixels; ppu.renderPitch = 256 * 4;
    ppu_reset(&ppu);
    ppu_write(&ppu, 0x2c, 0x15);
    dma.channel[0].hdmaActive = true;
    dma.channel[0].mode = 1;
    dma.channel[0].bAdr = 0x26;
    dma.channel[0].aAdr = 0x6000;
    snes_beam_frame_driver_reset();
    snes_beam_frame_driver_run_frame();
    assert(machine.beamMasterLast == EDGE);
    assert(transfers == 2 && ppu.window1right == 255);
    assert(ppu.screenEnabled[0] == 0x10 && ppu.screenEnabled[1] == 4);
    unsigned reads = table_reads;
    /* Rendering must consume history, not the possibly changed DMA table. */
    table[1] = 0xff; table[2] = 0;
    snes_beam_frame_driver_draw_ppu_frame_observed(observe, NULL);
    snes_beam_frame_driver_draw_ppu_frame_observed(observe, NULL);
    assert(observed == 448 && table_reads == reads && transfers == 2);
    assert(ppu.window1right == 255 && ppu.screenEnabled[0] == 0x10);
    /* Disable HDMA; neither another field nor skipped scanout may lose it. */
    dma.channel[0].hdmaActive = false;
    ppu_rasterRecord(0x420c, machine.vPos, 0);
    for (int frame = 0; frame < 3; ++frame) {
        snes_beam_frame_driver_run_frame();
        assert(ppu.window1right == 255);
    }
    snes_beam_frame_driver_draw_ppu_frame();
    assert(ppu.window1right == 255 && table_reads == reads && transfers == 2);
    puts("HDMA persists after disable; scanout cannot repeat transfers or lose late CPU writes");
    return 0;
}
