/* Real mixed-width leaf plus a synthetic byte-arithmetic variation. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"

#define CODE_BANK 0x13
#define CODE_PC 0xf1c2
#ifdef COORDINATE_OVERRIDE
#include "coordinate_guard_fixture.h"
#else
static uint8_t code[] = {
    0xbd,0x65,0x0e,0xeb,0xbd,0x35,0x0e,
#ifdef NARROW_FIXTURE
    0x38,0x38,
#else
    0xc2,0x20,
#endif
    0x38,0xf9,0x1a,0x00,0x99,0x00,0x00,
#ifdef NARROW_FIXTURE
    0x38,0x38,
#else
    0xe2,0x20,
#endif
    0x60,
};
#endif
#include "aot_bus_test_support.h"

RecompReturn Probe_M1X1(CpuState *cpu);
static uint16_t stop_pc=0x9234;
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0};
    cpu_mirrors_to_p(&g_cpu);
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc; in.e=g_cpu.emulation;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps<32); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in);
        assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles;
        g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge();
        g_cpu.coprocessor_master_cycles=g_cpu.master_cycles;
        snes_sync_master_clock(g_snes,g_cpu.master_cycles);
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in); cpu_p_to_mirrors(&g_cpu);
    return ((uint32_t)in.k<<16)|in.pc;
}
static unsigned current_x,current_y,current_db,current_dp,current_pb,current_flags;
static unsigned current_a,current_b;
static void initialize(void) {
    memset(ram,(current_a^current_b)&255,sizeof(ram));
    memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=current_a^0x8037; g_cpu.X=current_x; g_cpu.Y=current_y; g_cpu.S=0x1ed;
    g_cpu.D=current_dp; g_cpu.DB=current_db; g_cpu.PB=current_pb;
    g_cpu.P=0x30|current_flags; cpu_p_to_mirrors(&g_cpu);
    g_cpu.host_return_valid=2; g_cpu.ram=ram;
    unsigned base=current_db==0x7f?0x10000:0;
    ram[base+0xe65+current_x]=current_a>>8;
    ram[base+0xe35+current_x]=current_a&255;
    ram[base+0x1a+current_y]=current_b&255;
    ram[base+0x1b+current_y]=current_b>>8;
    ram[0x1ee]=0x33; ram[0x1ef]=0x92;
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
}
static void compare(const CpuState *expected,const uint8_t *expected_ram) {
    cpu_mirrors_to_p(&g_cpu);
    if(g_cpu.A!=expected->A || g_cpu.P!=expected->P ||
       g_cpu.cycles!=expected->cycles || g_cpu.master_cycles!=expected->master_cycles) {
        fprintf(stderr,"coordinate mismatch a=%04X b=%04X P=%02X X=%02X Y=%02X DB=%02X deadline=%llu: A=%04X/%04X P=%02X/%02X clocks=%llu/%llu cycles=%llu/%llu\n",
                current_a,current_b,current_flags,current_x,current_y,current_db,
                (unsigned long long)deadline,g_cpu.A,expected->A,g_cpu.P,expected->P,
                (unsigned long long)g_cpu.master_cycles,(unsigned long long)expected->master_cycles,
                (unsigned long long)g_cpu.cycles,(unsigned long long)expected->cycles);
        assert(0);
    }
    assert(g_cpu.X==expected->X && g_cpu.Y==expected->Y && g_cpu.S==expected->S);
    assert(g_cpu.D==expected->D && g_cpu.DB==expected->DB && g_cpu.PB==expected->PB);
    assert(g_cpu.m_flag==expected->m_flag && g_cpu.x_flag==expected->x_flag);
    assert(!memcmp(ram,expected_ram,sizeof(ram)) && !g_recomp_stack_top);
    assert(last_sync==g_cpu.master_cycles);
}
static unsigned check_case(void) {
    static uint8_t expected_ram[sizeof(ram)];
    static uint8_t final_ram[sizeof(ram)];
    uint64_t cutoff=deadline;
    initialize(); uint32_t pc=interpret((current_pb<<16)|CODE_PC);
    CpuState expected=g_cpu; memcpy(expected_ram,ram,sizeof(ram));
    CpuState final=expected;
    if((pc&0xffff)!=0x9234) {
        deadline=0; interpret(pc); final=g_cpu;
        memcpy(final_ram,ram,sizeof(ram));
    }
    deadline=cutoff;
    initialize(); Probe_M1X1(&g_cpu); compare(&expected,expected_ram);
    assert((pc==((current_pb<<16)|0x9234) && !yielded) || pc==yielded);
    if(yielded) {
        deadline=0; interpret(yielded);
        assert(g_cpu.S==0x1ef && g_cpu.m_flag==1);
        compare(&final,final_ram);
    } else if(!(current_flags&8)) {
#ifdef NARROW_FIXTURE
        assert(g_cpu.A==((current_a&0xff00)|((current_a-current_b)&255)));
        /* The synthetic trailing SECs overwrite C after byte subtraction. */
#else
        unsigned result=(current_a-current_b)&0xffff;
        assert(g_cpu.A==result && g_cpu._flag_C==(current_a>=current_b));
        assert(g_cpu._flag_V==(((current_a^current_b)&(current_a^result)&0x8000)!=0));
#endif
    }
    return 1;
}
int main(void) {
    unsigned cases=0;
#ifdef COORDINATE_OVERRIDE
    static uint8_t expected_ram[sizeof(ram)];
    current_x=0; current_y=GUARD_Y; current_dp=0x101;
    current_a=0x8000; current_b=0x7fff;
    deadline=0; refresh_at=100;
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned di=0;di<sizeof(guard_dbs)/sizeof(guard_dbs[0]);++di) {
        current_pb=CODE_BANK+mirror*0x80; current_db=guard_dbs[di];
        current_flags=0xc7|decimal*8; g_memsel=fast;
        stop_pc=EXPECTED_GUARD_PC?EXPECTED_GUARD_PC:0x9234;
        initialize(); interpret((current_pb<<16)|CODE_PC);
        CpuState expected=g_cpu; memcpy(expected_ram,ram,sizeof(ram));
        initialize(); Probe_M1X1(&g_cpu); compare(&expected,expected_ram);
        assert(yielded==(EXPECTED_GUARD_PC?((current_pb<<16)|EXPECTED_GUARD_PC):0));
        if(EXPECTED_GUARD_PC==0xf1cc || EXPECTED_GUARD_PC==0xf1cf)
            assert(g_cpu.m_flag==0); /* preserve the live REP state on fallback */
        ++cases;
    }
    printf("Coordinate guarded endpoints: %u safe-fallback/last-safe cases passed\n",cases);
#else
    const unsigned values[]={0,1,0x0f,0x10,0xff,0x100,0x7fff,0x8000,0xffff,0x9999,0x0a0a,0xfaaf};
    const unsigned flags[]={0,0xc3,0x46,0xc7}, indices[]={0,1,0x9b,0xff};
    const unsigned dbs[]={0,0x3f,0x80,0xbf,0x7e,0x7f}, dps[]={0,0x101,0x1fff};
    current_pb=CODE_BANK; current_db=0; current_dp=0; current_x=current_y=0;
    deadline=0; refresh_at=0; g_memsel=0;
    for(unsigned ai=0;ai<12;++ai) for(unsigned bi=0;bi<12;++bi)
    for(unsigned decimal=0;decimal<2;++decimal) for(unsigned fi=0;fi<4;++fi) {
        current_a=values[ai]; current_b=values[bi]; current_flags=flags[fi]|decimal*8;
        cases+=check_case();
    }
    refresh_at=100;
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<6;++di) for(unsigned xi=0;xi<4;++xi)
    for(unsigned yi=0;yi<4;++yi) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned dpi=0;dpi<3;++dpi) {
        current_a=(cases*1777)^0xa55a; current_a&=0xffff;
        current_b=(cases*3217)^0x5aa5; current_b&=0xffff;
        current_flags=flags[cases%4]|decimal*8;
        current_pb=CODE_BANK+mirror*0x80; current_db=dbs[di]; current_dp=dps[dpi];
        current_x=indices[xi]; current_y=indices[yi]; g_memsel=fast;
        cases+=check_case();
    }
    current_pb=CODE_BANK|0x80; current_db=0; current_dp=0x101;
    current_x=current_y=0xff;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<12;++vi) for(unsigned cut=1;cut<=420;++cut) {
        current_a=values[vi]; current_b=values[(vi+5)%12];
        current_flags=flags[vi%4]|decimal*8; g_memsel=fast;
        deadline=cut; cases+=check_case();
    }
    printf("Coordinate %s: %u state/memory/flag/clock/deadline cases passed\n",
#ifdef NARROW_FIXTURE
           "synthetic M1",
#else
           "ROM M1-M0-M1",
#endif
           cases);
#endif
    return 0;
}
