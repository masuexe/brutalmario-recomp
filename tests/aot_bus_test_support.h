/* Controlled bus and scheduler shared by generated-leaf differential probes. */
CpuState g_cpu;
Snes machine, *g_snes = &machine;
const char *g_last_recomp_func;
int g_recomp_stack_top;
int snes_frame_counter;
uint16_t g_cpu_entry_s[128];
uint8_t g_memsel;
static uint8_t ram[0x20000];
static uint64_t deadline, last_sync;
static uint32_t yielded;
static int refresh_at, refreshed;
static unsigned transfers;
static uint64_t bus_master;

uint8_t cpu_read8(CpuState *cpu, uint8_t bank, uint16_t addr) {
    (void)cpu;
    int32_t offset = cpu_wram_offset(bank, addr);
    if (offset >= 0) return ram[offset];
    if ((bank == CODE_BANK || bank == (CODE_BANK | 0x80)) && addr >= CODE_PC && addr < CODE_PC + sizeof(code))
        return code[addr - CODE_PC];
#ifdef INDEXED_FIXTURE
    if ((bank == 0 || bank == 0x80) && addr >= 0xf800 && addr < 0xfa00)
        return table[addr - 0xf800];
#endif
    return ((uint32_t)bank * 19 + addr * 17 + (addr >> 8)) & 255;
}
uint16_t cpu_read16(CpuState *cpu, uint8_t bank, uint16_t addr) {
    return cpu_read8(cpu, bank, addr) | (cpu_read8(cpu, bank, addr + 1) << 8);
}
void cpu_write8(CpuState *cpu, uint8_t bank, uint16_t addr, uint8_t value) {
    (void)cpu; int32_t offset = cpu_wram_offset(bank, addr);
#ifdef MMIO_EVENT_FIXTURE
    if (offset < 0) {
        RecordMmioEvent(cpu, ((uint32_t)bank << 16) | addr, value);
        return;
    }
#endif
    assert(offset >= 0); ram[offset] = value;
}
void cpu_write16(CpuState *cpu, uint8_t bank, uint16_t addr, uint16_t value) {
    cpu_write8(cpu, bank, addr, value); cpu_write8(cpu, bank, addr + 1, value >> 8);
}
static uint8_t read_bus(void *ctx, uint32_t addr) {
    ++transfers; bus_master += cpu_region_speed(addr);
    return cpu_read8(ctx, addr >> 16, addr);
}
static void write_bus(void *ctx, uint32_t addr, uint8_t value) {
    ++transfers; bus_master += cpu_region_speed(addr);
    cpu_write8(ctx, addr >> 16, addr, value);
}
void snes_refresh_charge(void) {
    if (refresh_at && !refreshed && g_cpu.master_cycles >= (unsigned)refresh_at) {
        g_cpu.master_cycles += 40; refreshed = 1;
    }
}
void snes_sync_master_clock(Snes *s, uint64_t master) { (void)s; last_sync = master; }
void WatchdogCheck(void) { snes_refresh_charge(); }
void RecompStackPush(const char *name) { (void)name; ++g_recomp_stack_top; }
void RecompStackPop(void) { assert(g_recomp_stack_top > 0); --g_recomp_stack_top; }
void RecompStackPopYield(void) { RecompStackPop(); }
void cpu_dbg_funcname(const char *name) { (void)name; }
int cpu_take_tailcall_return_context(uint16_t *s, uint8_t *hrv) { (void)s; (void)hrv; return 0; }
int cpu_resolve_ancestor_skip(uint16_t s) { (void)s; return -1; }
int interp_bridge_lle_master_deadline_reached(const CpuState *cpu) {
    return deadline && cpu->master_cycles >= deadline;
}
RecompReturn interp_bridge_lle_yield_unwind(CpuState *cpu, uint32_t pc) {
    (void)cpu; yielded = pc; return RECOMP_RETURN_SKIP_1;
}
int interp_bridge_return_targets_owner(uint16_t a, uint16_t b) { (void)a; (void)b; return 0; }
int interp_bridge_has_direct_paired_bounce(void) { return 0; }
int cpu_dispatch_has_entry(CpuState *cpu, uint32_t pc) { (void)cpu; (void)pc; return 0; }
RecompReturn cpu_dispatch_pc_from(CpuState *cpu,uint32_t pc,uint16_t s,uint32_t site) {
    (void)cpu; (void)pc; (void)s; (void)site; assert(0); return 0;
}
RecompReturn interp_tier_dispatch_popped_return(CpuState *cpu,uint32_t pc,uint32_t site,uint16_t s) {
    (void)cpu; (void)pc; (void)s; (void)site; assert(0); return 0;
}
RecompReturn interp_tier_dispatch_rewritten_return(CpuState *cpu,uint32_t pc,uint32_t site) {
    (void)cpu; (void)pc; (void)site; assert(0); return 0;
}
void dbg_rts_trace(CpuState *cpu,uint32_t pc,uint16_t a,uint16_t b,uint32_t c,uint8_t d) {
    (void)cpu; (void)pc; (void)a; (void)b; (void)c; (void)d;
}

