/* Compare actual generated C, paced bus helpers and interp816 execution.
 * The bus and scheduler are controlled; no game ROM is required. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"

RecompReturn Probe_M1X1(CpuState *cpu);
#define INDEXED_FIXTURE 1
#define CODE_BANK 4
#define CODE_PC 0xf87c
static uint8_t table[0x200];
static const uint8_t code[] = {0xbc,0xe5,0xd,0xb9,0x28,0xf8,0x85,0x0,0xac,0xd9,0x13,0xc0,0xa,0xd0,0x7,0xac,0xe8,0x1d,0xc0,0x1,0xd0,0x11,0xad,0xd6,0xd,0x4a,0x4a,0xa8,0xb9,0x11,0x1f,0xa8,0xb9,0x75,0xf8,0x25,0x0,0xf0,0x2,0xa9,0x1,0x60};
#include "aot_bus_test_support.h"

static void initialize(unsigned scenario, unsigned index, unsigned dp, unsigned pb, unsigned db) {
    memset(ram, 0, sizeof(ram)); memset(&g_cpu, 0, sizeof(g_cpu));
    memset(table, 0, sizeof(table));
    g_cpu.A=0xab80; g_cpu.X=index; g_cpu.Y=0x76; g_cpu.S=0x1ed;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x7d;
    g_cpu.m_flag=1; g_cpu.x_flag=1; g_cpu._flag_C=1;
    g_cpu._flag_I=1; g_cpu._flag_D=1; g_cpu._flag_V=1;
    g_cpu.host_return_valid=2; g_cpu.ram=ram;
    unsigned bank_offset = db == 0x7f ? 0x10000 : 0;
    unsigned lookup = (index & 1) ? 0xe0 : 0x10;
    ram[bank_offset+0xde5+index]=lookup;
    table[0x28+lookup]=scenario==3 ? 0 : 0x80;
    table[0x75+lookup]=0x80;
    if (db == 0x7e || db == 0x7f) {
        ram[bank_offset+0xf828+lookup]=table[0x28+lookup];
        ram[bank_offset+0xf875+lookup]=table[0x75+lookup];
    }
    ram[bank_offset+0x13d9]=scenario==0 ? 0 : 10;
    ram[bank_offset+0x1de8]=scenario==2 ? 0 : 1;
    ram[bank_offset+0xdd6]=scenario==4 ? 0xff : 0;
    ram[bank_offset+0x1f11]=lookup;
    ram[bank_offset+0x1f50]=0; /* scenario 4: zero-mask path */
    ram[0x1ee]=0x33; ram[0x1ef]=0x92;
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
}
static uint32_t interpret(uint32_t pc) {
    Interp816 in = {0};
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while (in.pc != 0x9234 && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps < 64); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in);
        assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles; g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge();
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in);
    return ((uint32_t)in.k<<16)|in.pc;
}

static void compare(const CpuState *state, const uint8_t *expected) {
    cpu_mirrors_to_p(&g_cpu);
    if(g_cpu.master_cycles!=state->master_cycles) {
        fprintf(stderr,"indexed clock mismatch: AOT=%llu interpreter=%llu\n",
                (unsigned long long)g_cpu.master_cycles,(unsigned long long)state->master_cycles);
        assert(0);
    }
    assert(g_cpu.A==state->A && g_cpu.X==state->X && g_cpu.Y==state->Y);
    assert(g_cpu.S==state->S && g_cpu.P==state->P && g_cpu.cycles==state->cycles);
    assert(!memcmp(ram,expected,sizeof(ram)) && g_recomp_stack_top==0);
    assert(last_sync==g_cpu.master_cycles);
}
int main(void) {
    static uint8_t expected[sizeof(ram)];
    unsigned cases=0;
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned dbi=0;dbi<4;++dbi) for(unsigned dp=0;dp<=0x101;dp+=0x101)
    for(unsigned index=0;index<=0xff;index+=0x33) for(unsigned scenario=0;scenario<5;++scenario) {
        unsigned dbs[]={0,0x80,0x7e,0x7f}; unsigned db=dbs[dbi],pb=4+mirror*0x80;
        deadline=0; refresh_at=0; g_memsel=fast;
        initialize(scenario,index,dp,pb,db); interpret((pb<<16)|CODE_PC);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        initialize(scenario,index,dp,pb,db);
        assert(Probe_M1X1(&g_cpu)==RECOMP_RETURN_NORMAL && !yielded);
        compare(&state,expected); ++cases;
    }
    /* Every clock cutoff, including refresh stalls, agrees at live op boundaries. */
    for(unsigned scenario=0;scenario<5;++scenario) for(unsigned cut=1;cut<=510;++cut) {
        deadline=cut; refresh_at=100; g_memsel=0;
        initialize(scenario,0xff,0x101,4,0); uint32_t pc=interpret(0x04f87c);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        initialize(scenario,0xff,0x101,4,0); Probe_M1X1(&g_cpu);
        compare(&state,expected);
        assert((pc==0x049234 && !yielded) || yielded==pc);
        if(yielded) { deadline=0; assert(interpret(yielded)==0x049234); }
        assert(g_cpu.S==0x1ef); ++cases;
    }
    /* Data banks outside stable WRAM/ROM must yield before the first access. */
    deadline=0; refresh_at=0;
    initialize(0,0,0,4,0x40); Probe_M1X1(&g_cpu);
    assert(yielded==0x04f87c && g_cpu.master_cycles==0 && g_cpu.S==0x1ed);
    /* Stable-memory guard endpoints, including a multi-byte boundary. */
    extern bool M1AotBusAddressSupported(uint32_t, unsigned);
    assert(M1AotBusAddressSupported(0x001fff,1));
    assert(!M1AotBusAddressSupported(0x001fff,2));
    assert(!M1AotBusAddressSupported(0x002100,1));
    assert(M1AotBusAddressSupported(0x7e2100,1));
    printf("indexed instruction bus: %u interpreter differential cases passed\n",cases);
    return 0;
}
