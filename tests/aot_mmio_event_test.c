/* Restricted palette event timing, retaining the old event-clock negative
 * control. Its guard bypass never enters a game binary or target policy. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"

#define MMIO_EVENT_FIXTURE 1
#ifdef PALETTE_LOOP_FIXTURE
#include "palette_loop_fixture.h"
static uint8_t FixtureRead(uint8_t, uint16_t);
static void FixtureInitialize(unsigned);
#else
#define CODE_BANK 0x0d
#define CODE_PC 0xa6ba
static const uint8_t code[] = {
    0xa9,0x23,0x8d,0x21,0x21, /* index */
    0xa9,0x34,0x8d,0x22,0x21, /* color low */
    0xa9,0x12,0x8d,0x22,0x21, /* color high */
    0x60,
};
#endif
typedef struct Event { uint32_t address; uint8_t value; uint64_t master; } Event;
static Event events[768];
static unsigned event_count;
static void RecordMmioEvent(CpuState *, uint32_t, uint8_t);
#include "aot_bus_test_support.h"

static void RecordMmioEvent(CpuState *cpu, uint32_t address, uint8_t value) {
    assert(event_count < sizeof(events)/sizeof(events[0]));
    assert((address & 0xffff) == 0x2121 || (address & 0xffff) == 0x2122);
    /* This is the clock passed to WriteReg's snes_sync_master_clock. */
    events[event_count++] = (Event){address,value,cpu->master_cycles};
}

/* Actual pinned bridge write/timing bodies are extracted by the Python test.
 * The PPU-only fixture must never reach these unrelated APU paths. */
static uint64_t s_interp_bus_master, g_interp_bridge_write_epoch;
static unsigned long long g_interp_bridge_steps;
static unsigned s_interp_bus_cycles;
static int s_interp_bus_timing_active;
static void bridge_apu_flush(CpuState *cpu) { (void)cpu; assert(0); }
static void RtlApuLock(void) { assert(0); }
static void RtlApuUnlock(void) { assert(0); }
static void rtl_sync_apu_to_cpu_locked(void) { assert(0); }
#include "bridge_write.inc"

extern bool M1ProductionBusWriteSupported(uint32_t, unsigned);
static int bypass_guard;
bool M1AotBusWriteSupported(uint32_t address, unsigned width) {
    if (M1ProductionBusWriteSupported(address,width)) return true;
    unsigned bank=address>>16, reg=address&0xffff;
    return bypass_guard && width==1 && (bank<0x40 || (bank>=0x80 && bank<0xc0)) &&
           (reg==0x2121 || reg==0x2122);
}
RecompReturn Probe_M1X1(CpuState *);
RecompReturn LegacyProbe_M1X1(CpuState *);

void LegacyPaletteWrite8(CpuState *cpu,uint8_t bank,uint16_t reg,
                         uint8_t value,uint32_t fetch_master) {
    cpu->cycles+=4;
    cpu->master_cycles+=fetch_master;
    cpu_write8_paced(cpu,bank,reg,value);
}

static uint8_t interpreter_read(void *ctx, uint32_t address) {
    bridge_timing_bus(address);
    return cpu_read8(ctx,address>>16,address);
}
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0};
    in.mem=&g_cpu; in.read=interpreter_read; in.write=bridge_bus_write;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=0x9234 && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps<5000);
        s_interp_bus_cycles=0; s_interp_bus_master=0; s_interp_bus_timing_active=1;
        int cycles=interp816_runOpcode(&in);
        s_interp_bus_timing_active=0;
        assert((unsigned)cycles>=s_interp_bus_cycles);
        bridge_finish_opcode(&g_cpu,cycles);
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in);
    return ((uint32_t)in.k<<16)|in.pc;
}
static void initialize(unsigned pb,unsigned db,uint64_t origin) {
    memset(&g_cpu,0,sizeof(g_cpu)); memset(ram,0,sizeof(ram));
    memset(events,0,sizeof(events)); event_count=0;
    g_cpu.A=0xab00; g_cpu.X=0x27; g_cpu.Y=0x56; g_cpu.S=0x1ed;
    g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x34;
    g_cpu.m_flag=1; g_cpu.x_flag=1; g_cpu._flag_I=1;
    g_cpu.master_cycles=origin; g_cpu.ram=ram; g_cpu.host_return_valid=2;
    ram[0x1ee]=0x33; ram[0x1ef]=0x92;
#ifdef PALETTE_LOOP_FIXTURE
    FixtureInitialize(db);
#endif
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
}
static void compare_state(CpuState expected, const uint8_t *expected_ram) {
    cpu_mirrors_to_p(&g_cpu);
    assert(g_cpu.A==expected.A && g_cpu.X==expected.X && g_cpu.Y==expected.Y);
    assert(g_cpu.P==expected.P && g_cpu.S==expected.S && g_cpu.D==expected.D);
    assert(g_cpu.DB==expected.DB && g_cpu.PB==expected.PB);
    assert(g_cpu.cycles==expected.cycles && g_cpu.master_cycles==expected.master_cycles);
    assert(!memcmp(ram,expected_ram,sizeof(ram)) && !g_recomp_stack_top);
    assert(last_sync==g_cpu.master_cycles);
}
static void compare_events(const Event *expected,unsigned count,unsigned delta) {
    assert(event_count==count);
    for(unsigned i=0;i<count;++i) {
        assert(events[i].address==expected[i].address && events[i].value==expected[i].value);
        assert(events[i].master==expected[i].master+delta);
    }
}
#ifndef PALETTE_LOOP_FIXTURE
int main(void) {
    unsigned cases=0, crossings=0;
    static uint8_t expected_ram[sizeof(ram)];
    const unsigned origins[]={0,1300,1320,1340,1360,2720};
    const unsigned dbs[]={0,0x3f,0x80,0xbf};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<4;++di) for(unsigned oi=0;oi<6;++oi)
    for(unsigned refresh=0;refresh<2;++refresh) {
        unsigned pb=CODE_BANK+mirror*0x80, db=dbs[di], origin=origins[oi];
        unsigned delta=(fast && mirror)?24:30;
        g_memsel=fast; deadline=0; refresh_at=refresh?origin+45:0;
        initialize(pb,db,origin); interpret((pb<<16)|CODE_PC);
        CpuState expected=g_cpu; Event expected_events[3];
        memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_events,events,sizeof(expected_events));
        assert(event_count==3);

        bypass_guard=0; initialize(pb,db,origin); LegacyProbe_M1X1(&g_cpu);
        assert(yielded==((pb<<16)|(CODE_PC+2)) && !event_count);
        /* Interpreter continuation preserves event clocks as well as state. */
        interpret(yielded); compare_state(expected,expected_ram);
        compare_events(expected_events,3,0);

        bypass_guard=1; initialize(pb,db,origin); LegacyProbe_M1X1(&g_cpu);
        assert(!yielded); compare_state(expected,expected_ram);
        compare_events(expected_events,3,delta);
        for(unsigned i=0;i<3;++i)
            crossings+=(events[i].master/1364 != expected_events[i].master/1364);
        if(!fast && !mirror && !di && !oi && !refresh) {
            for(unsigned i=0;i<3;++i)
                printf("write $%06X=%02X interpreter=%llu candidate_AOT=%llu delta=%u\n",
                       events[i].address,events[i].value,
                       (unsigned long long)expected_events[i].master,
                       (unsigned long long)events[i].master,delta);
            printf("equal final master clock=%llu\n",(unsigned long long)g_cpu.master_cycles);
        }
        bypass_guard=0; initialize(pb,db,origin); Probe_M1X1(&g_cpu);
        assert(!yielded); compare_state(expected,expected_ram);
        compare_events(expected_events,3,0);
        ++cases;
    }
    /* Cut every instruction, including between successive CGRAM port writes. */
    for(unsigned cut=1;cut<=220;++cut) {
        g_memsel=0; deadline=cut; refresh_at=45;
        initialize(CODE_BANK,0,0); uint32_t pc=interpret((CODE_BANK<<16)|CODE_PC);
        CpuState expected=g_cpu; Event expected_events[3]; unsigned count=event_count;
        memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_events,events,sizeof(expected_events));
        bypass_guard=1; initialize(CODE_BANK,0,0); LegacyProbe_M1X1(&g_cpu);
        compare_state(expected,expected_ram); compare_events(expected_events,count,30);
        assert((pc==((CODE_BANK<<16)|0x9234) && !yielded) || pc==yielded);
        bypass_guard=0; initialize(CODE_BANK,0,0); Probe_M1X1(&g_cpu);
        compare_state(expected,expected_ram); compare_events(expected_events,count,0);
        assert((pc==((CODE_BANK<<16)|0x9234) && !yielded) || pc==yielded);
        ++cases;
    }
    assert(crossings>0);
    assert(!M1ProductionBusWriteSupported(0x002121,1));
    assert(!M1ProductionBusWriteSupported(0xbf2122,1));
    extern bool M1AotPaletteWriteSupported(uint32_t,unsigned);
    assert(M1AotPaletteWriteSupported(0x002121,1));
    assert(M1AotPaletteWriteSupported(0xbf2122,1));
    assert(M1AotPaletteWriteSupported(0x7e2121,1)); /* WRAM */
    assert(!M1AotPaletteWriteSupported(0x002121,2));
    assert(!M1AotPaletteWriteSupported(0x002120,1));
    assert(!M1AotPaletteWriteSupported(0x002123,1));
    assert(!M1AotPaletteWriteSupported(0x402122,1));
    assert(!M1AotPaletteWriteSupported(0xc02122,1));
    printf("Palette event qualification: %u exact-event cases; legacy negative control retains %u scanline crossings\n",
           cases,crossings);
    return 0;
}
#endif
