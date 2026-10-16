/* Compare actual generated C, paced bus helpers and interp816 execution.
 * The bus and scheduler are controlled; no game ROM is required. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"

RecompReturn Probe_M1X0(CpuState *cpu);
#define CODE_BANK 0
#define CODE_PC 0xb983
static const uint8_t code[] = {0xa7,0x8a,0xa6,0x8a,0xe8,0xd0,0x05,0xa2,0x00,0x80,0xe6,0x8c,0x86,0x8a,0x60};
#include "aot_bus_test_support.h"

static void initialize(unsigned pointer, unsigned dp, unsigned pb, unsigned flags) {
    memset(ram, 0, sizeof(ram)); memset(&g_cpu, 0, sizeof(g_cpu));
    g_cpu.A=0xab00; g_cpu.X=1234; g_cpu.Y=5678; g_cpu.S=0x1ed;
    g_cpu.D=dp; g_cpu.DB=0x7e; g_cpu.PB=pb; g_cpu.P=flags|0x20;
    g_cpu.m_flag=1; g_cpu._flag_C=!!(flags&1); g_cpu._flag_I=!!(flags&4);
    g_cpu._flag_D=!!(flags&8); g_cpu._flag_V=!!(flags&64);
    g_cpu.host_return_valid=2; g_cpu.ram=ram;
    ram[dp+0x8a]=pointer; ram[dp+0x8b]=pointer>>8; ram[dp+0x8c]=pointer>>16;
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
        assert(++steps < 20); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in);
        assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles; g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge();
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in);
    return ((uint32_t)in.k<<16)|in.pc;
}
int main(void) {
    static uint8_t expected[sizeof(ram)];
    for (unsigned fast=0;fast<2;++fast) for(unsigned pb=0;pb<=0x80;pb+=0x80)
    for(unsigned wrap=0;wrap<2;++wrap) for(unsigned dp=0;dp<=0x101;dp+=0x101)
    for(unsigned flags=0;flags<=0x4d;flags+=0x4d) for(unsigned memory=0;memory<3;++memory) {
        g_memsel=fast; unsigned pointer=(fast?0x808000:0x128000)+(wrap?0x7fff:0x123);
        if(memory==1) pointer=wrap?0xffffff:0xff8123;
        if(memory==2) pointer=wrap?0x7effff:0x7e8123;
        deadline=0; refresh_at=0; initialize(pointer,dp,pb,flags);
        interpret(((uint32_t)pb<<16)|0xb983);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        if (!fast && !pb && !dp && !flags && !memory) assert(state.master_cycles == (wrap ? 246 : 190));
        initialize(pointer,dp,pb,flags);
        assert(Probe_M1X0(&g_cpu)==RECOMP_RETURN_NORMAL);
        assert(g_cpu.A==state.A && g_cpu.X==state.X && g_cpu.Y==state.Y && g_cpu.S==state.S);
        cpu_mirrors_to_p(&g_cpu);
        assert(g_cpu.P==state.P && g_cpu.cycles==state.cycles);
        if(g_cpu.master_cycles!=state.master_cycles) {
            fprintf(stderr,"clock mismatch: AOT=%llu interpreter=%llu\n",
                    (unsigned long long)g_cpu.master_cycles,(unsigned long long)state.master_cycles);
            return 1;
        }
        assert(!memcmp(ram,expected,sizeof(ram)) && g_recomp_stack_top==0);
        assert(last_sync==g_cpu.master_cycles);
    }
    /* Every clock cutoff yields at the same opcode boundary with live state. */
    for(unsigned wrap=0;wrap<2;++wrap) for(unsigned cut=1;cut<=310;++cut) {
        deadline=cut; g_memsel=0; refresh_at=100;
        initialize(wrap?0x12ffff:0x128123,0,0,0x4d); uint32_t pc=interpret(0xb983);
        CpuState state=g_cpu; memcpy(expected,ram,sizeof(ram));
        initialize(wrap?0x12ffff:0x128123,0,0,0x4d); Probe_M1X0(&g_cpu);
        cpu_mirrors_to_p(&g_cpu);
        assert(g_cpu.A==state.A && g_cpu.X==state.X && g_cpu.S==state.S && g_cpu.P==state.P);
        assert(g_cpu.cycles==state.cycles && g_cpu.master_cycles==state.master_cycles);
        assert(!memcmp(ram,expected,sizeof(ram)) && g_recomp_stack_top==0);
        assert((pc==0x9234 && !yielded) || yielded==pc);
        if (yielded) { deadline=0; assert(interpret(yielded)==0x9234); }
        assert(g_cpu.master_cycles==(wrap?286:230) && g_cpu.S==0x1ef);
    }
    deadline=0; refresh_at=0;
    for(unsigned scenario=0;scenario<4;++scenario) {
        initialize(0x128123,0,0,0); unsigned before=0;
        if(scenario==0) g_cpu.emulation=1;
        if(scenario==1) g_cpu.D=0x2000;
        if(scenario==2) g_cpu.S=0x2000;
        if(scenario==3) { ram[0x8a]=0x40;ram[0x8b]=0x21;ram[0x8c]=0; }
        before=g_cpu.S;
        Probe_M1X0(&g_cpu);
        assert(yielded==0xb983 && g_cpu.master_cycles==0 && g_cpu.S==before);
    }
    puts("instruction bus: generated C matches interpreter state, memory, cycles and deadlines");
    return 0;
}
