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
#ifdef CLEAR_FIXTURE
#define CODE_BANK 0x16
#define CODE_PC 0x9f2b
static const uint8_t code[] = {0xad,0x11,0x1f,0xc9,0x06,0xf0,0x0b,0xa2,0x07,0xa9,0x00,0x9f,0xa0,0xff,0x7f,0xca,0x10,0xf7,0x60};
#else
#define CODE_BANK 0x0d
#define CODE_PC 0xa6ba
static const uint8_t code[] = {0xa5,0x04,0x85,0x6b,0x85,0x6e,0xa5,0x05,0x85,0x6c,0x85,0x6f,0xad,0x28,0x19,
#ifdef COPY_MMIO_FIXTURE
    0x8d,0x00,0x21,
#else
    0x8d,0xa1,0x1b,
#endif
    0x60};
#endif
#include "aot_bus_test_support.h"

static uint16_t stop_pc=0x9234;
static void initialize(unsigned value, unsigned index, unsigned dp, unsigned pb, unsigned db) {
    for(unsigned i=0;i<sizeof(ram);++i) ram[i]=(i*17+(i>>8)+value)&255;
    memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=0xab80; g_cpu.X=index; g_cpu.Y=0x76; g_cpu.S=0x1ed;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x7d;
    g_cpu.m_flag=1; g_cpu.x_flag=1; g_cpu._flag_C=1;
    g_cpu._flag_I=1; g_cpu._flag_D=1; g_cpu._flag_V=1;
    g_cpu.host_return_valid=2; g_cpu.ram=ram;
    unsigned offset = db==0x7f ? 0x10000 : 0;
    ram[offset+0x1f11]=value;
    ram[dp+4]=value; ram[dp+5]=value^0xff;
    ram[offset+0x1928]=value^0x5a;
    ram[0x1ee]=0x33; ram[0x1ef]=0x92;
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
}
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0};
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps<100); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in);
        assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles; g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge();
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in);
    return ((uint32_t)in.k<<16)|in.pc;
}
static void compare(const CpuState *state,const uint8_t *expected) {
    cpu_mirrors_to_p(&g_cpu);
    assert(g_cpu.A==state->A && g_cpu.X==state->X && g_cpu.Y==state->Y);
    assert(g_cpu.S==state->S && g_cpu.D==state->D && g_cpu.DB==state->DB);
    assert(g_cpu.P==state->P && g_cpu.cycles==state->cycles);
    if(g_cpu.master_cycles!=state->master_cycles) {
        fprintf(stderr,"WRAM clock mismatch: AOT=%llu interpreter=%llu\n",
                (unsigned long long)g_cpu.master_cycles,(unsigned long long)state->master_cycles);
        assert(0);
    }
    assert(!memcmp(ram,expected,sizeof(ram)) && g_recomp_stack_top==0);
    assert(last_sync==g_cpu.master_cycles);
}
int main(void) {
    static uint8_t expected[sizeof(ram)];
#ifdef COPY_MMIO_FIXTURE
    deadline=0; refresh_at=0; g_memsel=0; stop_pc=0xa6c9;
    initialize(0xa5,0xff,0x101,CODE_BANK,0);
    assert(interpret((CODE_BANK<<16)|CODE_PC)==0x0da6c9);
    CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
    initialize(0xa5,0xff,0x101,CODE_BANK,0);
    Probe_M1X1(&g_cpu); compare(&state,expected);
    assert(yielded==0x0da6c9 && g_cpu.S==0x1ed);
    puts("WRAM write guard: yields at MMIO store with live state and no write");
#else
    unsigned cases=0, values[]={0,1,6,0x80,0xff}, dps[]={0,0x101,0x1f90};
    unsigned dbs[]={0,0x80,0x7e,0x7f};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned dbi=0;dbi<4;++dbi) for(unsigned dpi=0;dpi<3;++dpi)
    for(unsigned vi=0;vi<5;++vi) for(unsigned index=0;index<=0xff;index+=0xff) {
        unsigned value=values[vi],dp=dps[dpi],pb=CODE_BANK+mirror*0x80,db=dbs[dbi];
        deadline=0; refresh_at=0; g_memsel=fast;
        initialize(value,index,dp,pb,db); interpret((pb<<16)|CODE_PC);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        initialize(value,index,dp,pb,db);
        assert(Probe_M1X1(&g_cpu)==RECOMP_RETURN_NORMAL && !yielded);
        compare(&state,expected);
#ifdef CLEAR_FIXTURE
        if(value!=6) {
            for(unsigned i=0;i<8;++i) assert(ram[0x1ffa0+i]==0);
            assert(g_cpu.X==0xff && (g_cpu.A&255)==0);
        } else assert(g_cpu.X==index && (g_cpu.A&255)==6);
#else
        assert(ram[dp+0x6b]==value && ram[dp+0x6e]==value);
        assert(ram[dp+0x6c]==(value^0xff) && ram[dp+0x6f]==(value^0xff));
        assert(ram[(db==0x7f?0x10000:0)+0x1ba1]==(value^0x5a));
#endif
        ++cases;
    }
    /* Cutoffs cover every loop iteration and either conditional path. */
    for(unsigned vi=0;vi<5;++vi) for(unsigned cut=1;cut<=1800;++cut) {
        deadline=cut; refresh_at=100; g_memsel=1;
        initialize(values[vi],0xff,0x101,CODE_BANK|0x80,0x7f);
        uint32_t pc=interpret(((CODE_BANK|0x80)<<16)|CODE_PC);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        initialize(values[vi],0xff,0x101,CODE_BANK|0x80,0x7f);
        Probe_M1X1(&g_cpu); compare(&state,expected);
        assert((pc==(((CODE_BANK|0x80)<<16)|0x9234) && !yielded) || yielded==pc);
        if(yielded) { deadline=0; assert(interpret(yielded)==(((CODE_BANK|0x80)<<16)|0x9234)); }
        assert(g_cpu.S==0x1ef); ++cases;
    }
    deadline=0; refresh_at=0; g_memsel=0;
    initialize(0,0,0,CODE_BANK,0x40);
#ifdef CLEAR_FIXTURE
    Probe_M1X1(&g_cpu);
    assert(yielded==((CODE_BANK<<16)|CODE_PC) && g_cpu.master_cycles==0);
#else
    stop_pc=0xa6c6;
    interpret((CODE_BANK<<16)|CODE_PC); CpuState state=g_cpu;
    memcpy(expected,ram,sizeof(ram)); initialize(0,0,0,CODE_BANK,0x40);
    Probe_M1X1(&g_cpu); compare(&state,expected);
    assert(yielded==0x0da6c6);
    /* One byte beyond the last safe DP placement must fall back at entry. */
    initialize(0xa5,0,0x1f91,CODE_BANK,0);
    memcpy(expected,ram,sizeof(ram)); Probe_M1X1(&g_cpu);
    assert(yielded==0x0da6ba && g_cpu.master_cycles==0 && g_cpu.S==0x1ed);
    assert(!memcmp(ram,expected,sizeof(ram)) && g_recomp_stack_top==0);
#endif
    extern bool M1AotBusWriteSupported(uint32_t,unsigned);
    assert(M1AotBusWriteSupported(0x7fffff,1));
    assert(M1AotBusWriteSupported(0x7fffff,2)); /* $80:0000 is WRAM mirror */
    assert(!M1AotBusWriteSupported(0x801fff,2));
    assert(!M1AotBusWriteSupported(0x002121,1));
    assert(!M1AotBusWriteSupported(0x008000,1));
    assert(!M1AotBusWriteSupported(0x002000,1));
    assert(M1AotBusWriteSupported(0x7e2121,1));
    printf("WRAM instruction bus: %u interpreter differential cases passed\n",cases);
#endif
    return 0;
}
