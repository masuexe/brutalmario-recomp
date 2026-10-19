/* Three bounded M1/X1 leaves: real interpreter, byte writes and continuations. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"
#include "helper_fixture.h"
#define HELPER_TABLE_FIXTURE 1
#define NESTED_CALL_FIXTURE 1
static int unwind_parents;
typedef struct { uint32_t address; uint8_t value; } Write;
static Write writes[16];
static unsigned write_count;
static void RecordBusWrite(uint32_t address,uint8_t value) {
    assert(write_count<16); writes[write_count++]=(Write){address,value};
}
static uint8_t FixtureRead(uint8_t bank,uint16_t addr) {
    if((bank==0x15 || bank==0x95) && addr>=0xa045 && addr<0xa145)
        return table_bytes[addr-0xa045];
    return ((uint32_t)bank*19+addr*17+(addr>>8))&255;
}
#include "aot_bus_test_support.h"
RecompReturn Probe_M1X1(CpuState *cpu);
static unsigned low,high,index_x,dp,db,pb,flags;
static unsigned stop_pc=0x9234;
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0}; cpu_mirrors_to_p(&g_cpu);
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(deadline && g_cpu.master_cycles>=deadline)) {
        assert(++steps<32); transfers=0; bus_master=0;
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
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x30|flags;
    cpu_p_to_mirrors(&g_cpu); g_cpu.host_return_valid=2; g_cpu.ram=ram;
    /* Seed backing RAM directly, without issuing guest bus operations. */
#ifdef HELPER_RESTORE_POINTER
    ram[dp+0x6b]=low; ram[dp+0x6c]=high;
#elif defined(HELPER_ADVANCE_ROW)
    ram[dp+0x57]=low; ram[dp+0x6c]=high;
#else
    ram[dp+0x13]=low;
    unsigned base=db==0x7f?0x10000:0;
    ram[base+0xa045+index_x]=high;
#endif
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
    Write expected_writes[16],final_writes[16];
    uint64_t cutoff=deadline;
    initialize(); uint32_t pc=interpret((pb<<16)|CODE_PC);
    CpuState expected=g_cpu,final=g_cpu; unsigned count=write_count,final_count=count;
    memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_writes,writes,sizeof(writes));
    if((pc&65535)!=0x9234) {
        deadline=0; interpret(pc); final=g_cpu; final_count=write_count;
        memcpy(final_ram,ram,sizeof(ram)); memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff; initialize(); RecompReturn result=Probe_M1X1(&g_cpu);
    compare(&expected,expected_ram,expected_writes,count);
    assert(result==(yielded?(RecompReturn)RECOMP_RETURN_LLE_UNWIND_BASE:RECOMP_RETURN_NORMAL));
    assert((!yielded && (pc&65535)==0x9234) || yielded==pc);
    if(yielded) {
        deadline=0; interpret(yielded); compare(&final,final_ram,final_writes,final_count);
    }
    /* Independent binary result checks supplement the interpreter oracle. */
#ifdef HELPER_RESTORE_POINTER
    assert(ram[dp+4]==low && ram[dp+5]==high && g_cpu.A==(0xab00|high));
    assert(g_cpu.X==index_x && g_cpu.Y==0x73);
#elif defined(HELPER_ADVANCE_ROW)
    if(!(flags&8)) {
        unsigned next=(low+16)&255;
        assert(ram[dp+0x57]==next && g_cpu.Y==next);
        assert(g_cpu.A==(0xab00|(low>=240?((high+1)&255):next)));
        if(low>=240) assert(ram[dp+0x6c]==((high+1)&255) &&
            ram[dp+0x6f]==((high+1)&255) && ram[dp+5]==((high+1)&255));
        assert(g_cpu._flag_C==(low>=240 && high==255));
    }
#else
    if(!(flags&8) && (db==0x7e || db==0x7f)) {
        unsigned sum=low+high;
        assert(g_cpu.A==(0xab00|(sum&255)) && g_cpu._flag_C==(sum>255));
        assert(g_cpu._flag_V==((~(low^high)&(low^(sum&255))&128)!=0));
    }
#endif
    return 1;
}
int main(void) {
    unsigned cases=0;
    pb=CODE_BANK; db=0x7e; dp=0; index_x=0; deadline=0; refresh_at=100;
#ifdef HELPER_RESTORE_POINTER
    for(unsigned a=0;a<256;++a) for(unsigned b=0;b<16;++b) {
        low=a; high=(a*37+b*17)&255; flags=(b&1?0xc7:0)|((b&2)?8:0);
        index_x=(a+b)&255; cases+=check();
    }
#else
    /* Includes invalid BCD inputs and both carries for the two ADC leaves. */
    for(unsigned a=0;a<256;++a) for(unsigned b=0;b<256;++b)
    for(unsigned decimal=0;decimal<2;++decimal) {
        low=a; high=b; flags=0xc7|decimal*8; index_x=(a+b)&255;
        cases+=check();
    }
#endif
    const unsigned indices[]={0,1,0x10,0xba,0xbb,0xff};
    const unsigned dbs[]={0x15,0x95,0x7e,0x7f};
    const unsigned values[]={0,1,0x7f,0xef,0xf0,0xff};
    const unsigned dps[]={0,0x101,LAST_DP};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<4;++di) for(unsigned dpi=0;dpi<3;++dpi)
    for(unsigned xi=0;xi<6;++xi) for(unsigned decimal=0;decimal<2;++decimal) {
        pb=CODE_BANK+mirror*0x80; db=dbs[di]; dp=dps[dpi]; index_x=indices[xi];
        low=values[cases%6]; high=values[(cases/6)%6]; flags=0xc7|decimal*8;
        g_memsel=fast; deadline=0; cases+=check();
    }
    pb=CODE_BANK|0x80; db=0x7f; dp=0x101;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<6;++vi) for(unsigned cut=1;cut<=600;++cut) {
        low=values[vi]; high=values[(vi+3)%6]; flags=0xc7|decimal*8;
        index_x=indices[vi]; g_memsel=fast; deadline=cut; cases+=check();
    }
    /* Policy entry guard: no instruction or write occurs for unsafe DP. */
    deadline=0; dp=LAST_DP+1; initialize();
    static uint8_t memory[sizeof(ram)]; memcpy(memory,ram,sizeof(ram));
    Probe_M1X1(&g_cpu);
    assert(yielded==((pb<<16)|CODE_PC) && !g_cpu.master_cycles && !write_count);
    assert(!memcmp(memory,ram,sizeof(ram)) && !g_recomp_stack_top); ++cases;
#ifdef HELPER_FRAME_PHASE
    /* The fixed table operand stays in upper ROM even for a data bank with
       no low WRAM mirror. It must remain admitted, not spuriously yield. */
    dp=0x101; db=0x40; deadline=0; cases+=check();
#endif
    printf("Helper $%06X: %u state/write-order/clock/continuation cases passed\n",
           (CODE_BANK<<16)|CODE_PC,cases);
    return 0;
}
