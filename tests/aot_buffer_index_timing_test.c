/* M0/X1 buffer index: word transfers, live-address guards and resumptions. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"
#include "buffer_index_fixture.h"
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
static unsigned low,high,index_x,dp,db,pb,flags,layer;
static int guarded_read;
static unsigned stop_pc=0x9234;
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0}; cpu_mirrors_to_p(&g_cpu);
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(guarded_read && in.pc==0xa32d) && !(deadline && g_cpu.master_cycles>=deadline)) {
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
    g_cpu.A=0xab37; g_cpu.X=index_x; g_cpu.Y=0x73; g_cpu.S=0x1ed;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x10|flags;
    cpu_p_to_mirrors(&g_cpu); g_cpu.host_return_valid=2; g_cpu.ram=ram;
    ram[dp]=low; ram[dp+1]=low>>8;
    ram[dp+2]=high; ram[dp+3]=high>>8;
    unsigned address=TABLE_OPERAND+index_x;
    int32_t off=cpu_wram_offset(db,address);
    if(off>=0) ram[off]=layer;
    off=cpu_wram_offset(db+(address==65535), (address+1)&65535);
    if(off>=0) ram[off]=(layer^0x55)&255;
    ram[0x1ee]=0x33; ram[0x1ef]=0x92;
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
    for(unsigned i=0;i<count;++i)
        assert(writes[i].address==expected_writes[i].address && writes[i].value==expected_writes[i].value);
}
static unsigned check(void) {
    static uint8_t expected_ram[sizeof(ram)],final_ram[sizeof(ram)];
    Write expected_writes[32],final_writes[32];
    uint64_t cutoff=deadline; int guard=guarded_read;
    initialize(); uint32_t pc=interpret((pb<<16)|CODE_PC);
    CpuState expected=g_cpu,final=g_cpu; unsigned count=write_count,final_count=count;
    memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_writes,writes,sizeof(writes));
    if((pc&65535)!=0x9234) {
        deadline=0; guarded_read=0; interpret(pc); final=g_cpu; final_count=write_count;
        memcpy(final_ram,ram,sizeof(ram)); memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff; guarded_read=guard; initialize(); RecompReturn result=Probe_M0X1(&g_cpu);
    compare(&expected,expected_ram,expected_writes,count);
    assert(result==(yielded?(RecompReturn)RECOMP_RETURN_LLE_UNWIND_BASE:RECOMP_RETURN_NORMAL));
    assert((!yielded && (pc&65535)==0x9234) || yielded==pc);
    if(yielded) {
        deadline=0; guarded_read=0; interpret(yielded); compare(&final,final_ram,final_writes,final_count);
    }
    guarded_read=guard;
    /* Independent binary result checks supplement the interpreter oracle. */
#ifndef BANK_WRAP_FIXTURE
    if(!(flags&8) && (db==0x7e || db==0x7f) && dp<0x1000) {
        unsigned value=(low&15)+((low&16)<<4)+((high<<4)&255)+((high>>12)&1);
        if(high&16) value+=0x200;
        if(layer) value+=0x400;
        assert((ram[dp+4]|(ram[dp+5]<<8))==value);
        assert(g_cpu.A==(layer?value:0) && !g_cpu._flag_C);
        assert(!g_cpu.m_flag && g_cpu.x_flag);
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
#ifdef BANK_WRAP_FIXTURE
    /* Runtime word reads wrap within a bank, interpreter indexed reads carry.
       The AOT guard must yield before either byte at this endpoint. */
    low=0xffff; high=0x8123; layer=1; flags=0xc7; guarded_read=1;
    cases+=check();
#else
    /* Sweep every word in each coordinate, including invalid BCD, carry,
       sign and truncation edges; vary the other word independently. */
    for(unsigned a=0;a<65536;++a) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned axis=0;axis<2;++axis) {
        low=axis?(a*73+0x89ab)&65535:a;
        high=axis?a:(a*31+0xfedc)&65535;
        flags=(a&1?0xc7:0)|decimal*8; layer=(a&2)?0xff:0;
        cases+=check();
    }
    const unsigned indices[]={0,1,0xed,0xee,0xef,0xff};
    const unsigned dbs[]={0,0x80,0x7e,0x7f};
    const unsigned values[]={0,1,0x7fff,0x8000,0xffff,0x1010};
    const unsigned dps[]={0,0x101,0x1ffa};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<4;++di) for(unsigned dpi=0;dpi<3;++dpi)
    for(unsigned xi=0;xi<6;++xi) for(unsigned decimal=0;decimal<2;++decimal) {
        pb=CODE_BANK+mirror*0x80; db=dbs[di]; dp=dps[dpi]; index_x=indices[xi];
        low=values[cases%6]; high=values[(cases/6)%6]; layer=(cases&1)?1:0;
        flags=0xc7|decimal*8; g_memsel=fast; deadline=0;
        guarded_read=(di<2 && index_x>=0xee); cases+=check();
    }
    pb=CODE_BANK|0x80; db=0x7f; dp=0x101; guarded_read=0;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<6;++vi) for(unsigned cut=1;cut<=1200;++cut) {
        low=values[vi]; high=values[(vi+3)%6]; flags=0xc7|decimal*8;
        layer=(vi&1)?0:255; index_x=indices[vi]; g_memsel=fast; deadline=cut;
        cases+=check();
    }
    /* Unmapped low data banks hand back at the same live read boundary. */
    deadline=0; dp=0x101; db=0x40; index_x=0; guarded_read=1; cases+=check();
    guarded_read=0;
    entry_guard(0x1ffb,0x1ed,0); ++cases;
    entry_guard(0x101,0x1ffe,0); ++cases;
    entry_guard(0x101,0x1ed,1); ++cases;
#endif
    printf("Buffer index: %u state/write-order/clock/continuation cases passed\n",cases);
    return 0;
}
