/* Real nested caller: complete state, ordered writes and deadline continuation. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"

#ifdef BANK15_FIXTURE
#define CODE_BANK 0x15
#define CODE_PC 0xa023
#define CALLEE_PC 0xa032
#define JSR_PC 0xa02a
#define LAST_DP 0x1fff
#define bank_13_F1C2_M1X1 bank_15_A032_M1X1
#define bank_13_F1C2_M0X0 bank_15_A032_M0X0
#define bank_13_F1C2_M0X1 bank_15_A032_M0X1
#define bank_13_F1C2_M1X0 bank_15_A032_M1X0
#else
#define CODE_BANK 0x13
#define CODE_PC 0xf1a7
#define CALLEE_PC 0xf1c2
#define JSR_PC 0xf1ae
#define LAST_DP 0x1ffc
#endif
#define NESTED_CALL_FIXTURE 1
static const uint8_t code[] = {
0x8a,0x18,0x69,0x10,0xaa,0xa0,0x02,0x20,
#ifdef BANK15_FIXTURE
0x32,0xa0,0xae,0xde,0x0d,0xa0,0x00,
#else
0xc2,0xf1,0xae,0xde,0x0d,
0xa5,0x02,0x38,0xfd,0x55,0x0e,0x85,0x02,0xb0,0x02,0xc6,0x03,0xa0,0x00,
#endif
0xbd,0x65,0x0e,0xeb,0xbd,0x35,0x0e,0xc2,0x20,0x38,0xf9,0x1a,0x00,
0x99,0x00,0x00,0xe2,0x20,0x60};
static int unwind_parents;
typedef struct { uint32_t address; uint8_t value; } Write;
static Write writes[32];
static unsigned write_count;
static void RecordBusWrite(uint32_t address, uint8_t value) {
    assert(write_count < 32);
    writes[write_count++] = (Write){address,value};
}
#include "aot_bus_test_support.h"
RecompReturn Caller_M1X1(CpuState *cpu);
RecompReturn Callee_M1X1(CpuState *cpu);
RecompReturn bank_13_F1C2_M1X1(CpuState *cpu) { return Callee_M1X1(cpu); }
RecompReturn bank_13_F1C2_M0X0(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn bank_13_F1C2_M0X1(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn bank_13_F1C2_M1X0(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn interp_tier_run_call_frame(CpuState *cpu,uint32_t target,uint32_t site,
                                      uint8_t size,uint32_t *out) {
    (void)cpu; (void)target; (void)site; (void)size; (void)out; assert(0); return 0;
}
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
        assert(++steps<64); transfers=0; bus_master=0;
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
static unsigned current_a,current_b,current_s=0x1ed;
static void initialize(void) {
    memset(ram,(current_a^current_b)&255,sizeof(ram));
    memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=current_a^0x8037; g_cpu.X=current_x; g_cpu.Y=current_y; g_cpu.S=current_s;
    g_cpu.D=current_dp; g_cpu.DB=current_db; g_cpu.PB=current_pb;
    g_cpu.P=0x30|current_flags; cpu_p_to_mirrors(&g_cpu);
    g_cpu.host_return_valid=2; g_cpu.ram=ram;
    unsigned base=current_db==0x7f?0x10000:0;
    for (unsigned i=0;i<256;++i) {
        ram[base+0xe65+i]=(current_a+i)>>8;
        ram[base+0xe35+i]=(current_a+i)&255;
        ram[base+0xe55+i]=current_b&255;
    }
    ram[base+0xdde]=current_y;
    ram[base+0xe65+current_x]=current_a>>8;
    ram[base+0xe35+current_x]=current_a&255;
    ram[base+0x1a+current_y]=current_b&255;
    ram[base+0x1b+current_y]=current_b>>8;
    ram[base+0x1a]=current_b; ram[base+0x1b]=current_b>>8;
    ram[base+0x1c]=current_b; ram[base+0x1d]=current_b>>8;
    write_count=0; unwind_parents=0;
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
    Write expected_writes[32], final_writes[32];
    unsigned expected_count=write_count, final_count=write_count;
    memcpy(expected_writes,writes,sizeof(writes));
    CpuState final=expected;
    if((pc&0xffff)!=0x9234) {
        deadline=0; interpret(pc); final=g_cpu;
        memcpy(final_ram,ram,sizeof(ram));
        final_count=write_count; memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff;
    initialize(); RecompReturn result=Caller_M1X1(&g_cpu); compare(&expected,expected_ram);
    assert(write_count==expected_count);
    for(unsigned i=0;i<write_count;++i)
        assert(writes[i].address==expected_writes[i].address && writes[i].value==expected_writes[i].value);
    assert(result==(yielded ? (RecompReturn)(RECOMP_RETURN_LLE_UNWIND_BASE-unwind_parents) : RECOMP_RETURN_NORMAL));
    assert((pc==((current_pb<<16)|0x9234) && !yielded) || pc==yielded);
    if(yielded) {
        deadline=0; interpret(yielded);
        assert(g_cpu.S==0x1ef && g_cpu.m_flag==1);
        compare(&final,final_ram);
        assert(write_count==final_count);
        for(unsigned i=0;i<write_count;++i)
            assert(writes[i].address==final_writes[i].address && writes[i].value==final_writes[i].value);
    }
    return 1;
}
int main(void) {
    unsigned cases=0;
    const unsigned indices[]={0,1,0xef,0xf0,0xff};
    const unsigned dbs[]={0,0x3f,0x80,0xbf,0x7e,0x7f};
    const unsigned dps[]={0,0x101,LAST_DP};
    const unsigned values[]={0,1,0x7fff,0x8000,0xffff,0x9999};
    refresh_at=100;
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<6;++di) for(unsigned xi=0;xi<5;++xi)
    for(unsigned yi=0;yi<5;++yi) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned dpi=0;dpi<3;++dpi) {
        current_a=values[cases%6]; current_b=values[(cases/6)%6];
        current_flags=0xc7|decimal*8;
        current_pb=CODE_BANK+mirror*0x80; current_db=dbs[di]; current_dp=dps[dpi];
        current_x=indices[xi]; current_y=indices[yi]; g_memsel=fast;
        deadline=0; cases+=check_case();
    }
    current_pb=CODE_BANK|0x80; current_db=0; current_dp=0x101;
    current_x=0xff; current_y=0xf0;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<6;++vi) for(unsigned cut=1;cut<=1000;++cut) {
        current_a=values[vi]; current_b=values[(vi+3)%6];
        current_flags=0xc7|decimal*8; g_memsel=fast;
        deadline=cut; cases+=check_case();
    }
    /* Compare precise fallback boundaries with the interpreter stopped before
       the unsafe operation, including an already-pushed child frame. */
    const unsigned stacks[]={0,1,0x1ed,0x1ed};
    const unsigned guard_pc[]={JSR_PC,CALLEE_PC,CALLEE_PC,CODE_PC};
    static uint8_t expected_ram[sizeof(ram)];
    for(unsigned i=0;i<4;++i) {
        current_s=stacks[i]; current_db=i==2?0x40:0;
        current_dp=i==3?LAST_DP+1:0; deadline=0;
        stop_pc=guard_pc[i]; initialize(); interpret((current_pb<<16)|CODE_PC);
        CpuState expected=g_cpu; memcpy(expected_ram,ram,sizeof(ram));
        Write expected_writes[32]; unsigned expected_count=write_count;
        memcpy(expected_writes,writes,sizeof(writes));
        initialize(); RecompReturn result=Caller_M1X1(&g_cpu);
        compare(&expected,expected_ram);
        assert(yielded==((current_pb<<16)|stop_pc));
        assert(result==(RecompReturn)(RECOMP_RETURN_LLE_UNWIND_BASE-unwind_parents));
        assert(write_count==expected_count);
        for(unsigned j=0;j<write_count;++j)
            assert(writes[j].address==expected_writes[j].address && writes[j].value==expected_writes[j].value);
        ++cases;
    }
    printf("Nested coordinate caller: %u state/write-order/clock/continuation cases passed\n",cases);
    return 0;
}
