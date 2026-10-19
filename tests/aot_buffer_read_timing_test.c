/* Buffer read: M/X width changes, word stack order and guarded resumption. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"
#include "buffer_read_fixture.h"
#define NESTED_CALL_FIXTURE 1
static int unwind_parents;
typedef struct { uint32_t address; uint8_t value; } Write;
static Write writes[32];
static unsigned write_count;
static void RecordBusWrite(uint32_t address,uint8_t value) {
    assert(write_count<32); writes[write_count++]=(Write){address,value};
}
#include "aot_bus_test_support.h"
RecompReturn Probe_M0X1(CpuState *cpu);
static unsigned low,high,index_x,dp,db,pb,flags,stack_s=0x1ed;
static unsigned guard_pc;
static int skip_continuation;
static unsigned stop_pc=0x9234;
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0}; cpu_mirrors_to_p(&g_cpu);
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(guard_pc && in.pc==guard_pc) && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps<40); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in); assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles; g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge();
        g_cpu.coprocessor_master_cycles=g_cpu.master_cycles;
        snes_sync_master_clock(g_snes,g_cpu.master_cycles);
    }
    g_cpu.A=in.a; g_cpu.X=in.x; g_cpu.Y=in.y; g_cpu.S=in.sp;
    g_cpu.P=interp816_getFlags(&in); cpu_p_to_mirrors(&g_cpu);
    return ((uint32_t)in.k<<16)|in.pc;
}
static void initialize(void) {
    memset(ram,low^high,sizeof(ram)); memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=0xab37; g_cpu.X=index_x; g_cpu.Y=0x73; g_cpu.S=stack_s;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x10|flags;
    cpu_p_to_mirrors(&g_cpu); g_cpu.host_return_valid=2; g_cpu.ram=ram;
    ram[dp+4]=low; ram[dp+5]=low>>8;
    unsigned address=TABLE_BASE+low;
    int32_t off=cpu_wram_offset(address>>16,address);
    if(off>=0) ram[off]=high;
    ++address;
    off=cpu_wram_offset(address>>16,address);
    if(off>=0) ram[off]=high>>8;
    ram[(stack_s+1)&65535]=0x33; ram[(stack_s+2)&65535]=0x92;
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
    write_count=0; unwind_parents=0;
}
static void compare(const CpuState *expected,const uint8_t *memory,
                    const Write *expected_writes,unsigned count) {
    cpu_mirrors_to_p(&g_cpu);
    if(g_cpu.A!=expected->A || g_cpu.P!=expected->P ||
       g_cpu.cycles!=expected->cycles || g_cpu.master_cycles!=expected->master_cycles) {
        fprintf(stderr,"helper %06x lo=%02x hi=%02x X=%02x DB=%02x D=%04x P=%02x cutoff=%llu: A=%04x/%04x P=%02x/%02x clocks=%llu/%llu cycles=%llu/%llu\n",
            (CODE_BANK<<16)|CODE_PC,low,high,index_x,db,dp,flags,(unsigned long long)deadline,
            g_cpu.A,expected->A,g_cpu.P,expected->P,
            (unsigned long long)g_cpu.master_cycles,(unsigned long long)expected->master_cycles,
            (unsigned long long)g_cpu.cycles,(unsigned long long)expected->cycles);
        assert(0);
    }
    assert(g_cpu.X==expected->X && g_cpu.Y==expected->Y && g_cpu.S==expected->S);
    assert(g_cpu.D==expected->D && g_cpu.DB==expected->DB && g_cpu.PB==expected->PB);
    assert(g_cpu.m_flag==expected->m_flag && g_cpu.x_flag==expected->x_flag);
    assert(!memcmp(ram,memory,sizeof(ram)) && !g_recomp_stack_top);
    assert(write_count==count && last_sync==g_cpu.master_cycles);
    for(unsigned i=0;i<count;++i) {
        if(writes[i].address!=expected_writes[i].address || writes[i].value!=expected_writes[i].value)
            fprintf(stderr,"write %u: AOT %06x=%02x interp %06x=%02x\n",i,
                    writes[i].address,writes[i].value,expected_writes[i].address,expected_writes[i].value);
        assert(writes[i].address==expected_writes[i].address && writes[i].value==expected_writes[i].value);
    }
}
static unsigned check(void) {
    static uint8_t expected_ram[sizeof(ram)],final_ram[sizeof(ram)];
    Write expected_writes[32],final_writes[32];
    uint64_t cutoff=deadline; unsigned guard=guard_pc;
    initialize(); uint32_t pc=interpret((pb<<16)|CODE_PC);
    CpuState expected=g_cpu,final=g_cpu; unsigned count=write_count,final_count=count;
    memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_writes,writes,sizeof(writes));
    if(!skip_continuation && (pc&65535)!=0x9234) {
        deadline=0; guard_pc=0; interpret(pc); final=g_cpu; final_count=write_count;
        memcpy(final_ram,ram,sizeof(ram)); memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff; guard_pc=guard; initialize(); RecompReturn result=Probe_M0X1(&g_cpu);
    compare(&expected,expected_ram,expected_writes,count);
    assert(result==(yielded?(RecompReturn)RECOMP_RETURN_LLE_UNWIND_BASE:RECOMP_RETURN_NORMAL));
    assert((!yielded && (pc&65535)==0x9234) || yielded==pc);
    if(yielded && !skip_continuation) {
        deadline=0; guard_pc=0; interpret(yielded); compare(&final,final_ram,final_writes,final_count);
    }
    guard_pc=guard;
    /* Independent binary result checks supplement the interpreter oracle. */
#ifndef RELOCATED_FIXTURE
    if(!skip_continuation && stack_s>1 && dp<0x1000 &&
       !((dp+4<=stack_s+2) && (dp+5>=stack_s+1))) {
        if(low<0x800) {
            unsigned value=high&255;
            assert(g_cpu.A==value);
            assert(g_cpu._flag_C==(value==0 || value>=0x87));
        } else {
            assert(g_cpu.A==low && g_cpu._flag_C);
            assert(!write_count);
        }
        assert(g_cpu.m_flag && g_cpu.x_flag && g_cpu.X==index_x);
    }
#endif
    return 1;
}
static void entry_guard(unsigned bad_dp,unsigned bad_s,unsigned emulation) {
    dp=bad_dp; initialize(); g_cpu.S=bad_s; g_cpu.emulation=emulation;
    static uint8_t memory[sizeof(ram)]; memcpy(memory,ram,sizeof(ram));
    CpuState before=g_cpu;
    Probe_M0X1(&g_cpu);
    assert(yielded==((pb<<16)|CODE_PC) && !g_cpu.master_cycles && !write_count);
    assert(!memcmp(memory,ram,sizeof(ram)) && !g_recomp_stack_top);
    assert(g_cpu.A==before.A && g_cpu.S==before.S && g_cpu.P==before.P);
}
int main(void) {
    unsigned cases=0;
    pb=CODE_BANK; db=0x7e; dp=0; index_x=0; deadline=0; refresh_at=100;
#ifdef RELOCATED_FIXTURE
    /* Check the last safe word, the forbidden endpoint and indexed bank
       carry; unsafe reads yield with X still on the guest stack. */
    const unsigned offsets[]={0,1,2,0x7ff};
    for(unsigned i=0;i<4;++i) {
        low=offsets[i]; high=0x8642; flags=0xc7; index_x=i*37;
        int blocked=TABLE_BASE==0x1ffe ? low!=0 : low==1;
        guard_pc=blocked?0xa0ef:0; cases+=check();
        assert(yielded==(blocked?((pb<<16)|0xa0ef):0));
    }
#else
    /* Exhaust every input index, every table word and the complete byte
       predicate for every accepted index. Decimal never alters CMP. */
    for(unsigned a=0;a<65536;++a) for(unsigned decimal=0;decimal<2;++decimal) {
        low=a; high=(a*73+0x89ab)&65535; index_x=a&255;
        flags=(a&1?0xc7:0)|decimal*8; cases+=check();
    }
    low=0x7ff;
    for(unsigned a=0;a<65536;++a) {
        high=a; flags=(a&1?0xc7:0)|(a&2?8:0); index_x=(a>>8)&255;
        cases+=check();
    }
    for(unsigned a=0;a<0x800;++a) for(unsigned b=0;b<256;++b) {
        low=a; high=(b<<8)|b; flags=(b&1?0xc7:0)|(a&1?8:0);
        index_x=(a+b)&255; cases+=check();
    }
    const unsigned indices[]={0,1,0x7ff,0x800,0x8000,0xffff};
    const unsigned values[]={0,1,0x86,0x87,0xff,0xff00};
    const unsigned dbs[]={0,0x40,0x7e,0x7f};
    const unsigned dps[]={0,0x101,0x1ffa};
    const unsigned stacks[]={2,0x1ed,0x1ffd};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<4;++di) for(unsigned dpi=0;dpi<3;++dpi)
    for(unsigned si=0;si<3;++si) for(unsigned vi=0;vi<6;++vi) {
        pb=CODE_BANK+mirror*0x80; db=dbs[di]; dp=dps[dpi]; stack_s=stacks[si];
        low=indices[vi]; high=values[vi]; index_x=values[(vi+1)%6]&255;
        flags=(vi&1?0xc7:0)|(vi&2?8:0); g_memsel=fast; deadline=0; cases+=check();
    }
    pb=CODE_BANK|0x80; db=0x40; dp=0x101; stack_s=0x1ed;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<6;++vi) for(unsigned cut=1;cut<=800;++cut) {
        low=vi<4?indices[vi]:1; high=values[vi]; flags=0xc7|decimal*8;
        index_x=(vi*37)&255; g_memsel=fast; deadline=cut; cases+=check();
    }
    deadline=0; low=1; high=0x8601; stack_s=0; guard_pc=0xa0ec;
    skip_continuation=1; cases+=check(); assert(yielded==((pb<<16)|0xa0ec));
    stack_s=1; guard_pc=0xa0f3; skip_continuation=0;
    cases+=check(); assert(yielded==((pb<<16)|0xa0f3));
    guard_pc=0; stack_s=0x1ed;
    entry_guard(0x1ffb,0x1ed,0); ++cases;
    entry_guard(0x101,0x1ffe,0); ++cases;
    entry_guard(0x101,0x1ed,1); ++cases;
#endif
    printf("Buffer read: %u state/write-order/clock/continuation cases passed\n",cases);
    return 0;
}
