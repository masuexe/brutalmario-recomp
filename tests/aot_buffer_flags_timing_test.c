/* Buffer flags: lookup loop, sentinel predicate and mixed-width fallback. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"
#include "buffer_flags_fixture.h"
#define NESTED_CALL_FIXTURE 1
#define HELPER_TABLE_FIXTURE 1
static int unwind_parents;
typedef struct { uint32_t address; uint8_t value; } Write;
static Write writes[64];
static unsigned write_count;
static void RecordBusWrite(uint32_t address,uint8_t value) {
    assert(write_count<64); writes[write_count++]=(Write){address,value};
}
static uint8_t FixtureRead(uint8_t bank,uint16_t addr) {
    if((bank==4 || bank==0x84) && addr>=0x9078 && addr<0x9086)
        return table_bytes[addr-0x9078];
    if((bank==0x15 || bank==0x95) && addr>=0xa106 && addr<0xa110)
        return mask_bytes[addr-0xa106];
    return ((uint32_t)bank*19+addr*17+(addr>>8))&255;
}
#include "aot_bus_test_support.h"
RecompReturn Probe_M1X1(CpuState *cpu);
static unsigned low,high,index_x,dp,db,pb,flags,stack_s=0x1ed;
static unsigned kind,initial_bits,player,slot,mask_salt;
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
        assert(++steps<256); transfers=0; bus_master=0;
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
static void seed(uint32_t address,unsigned value,unsigned width) {
    for(unsigned i=0;i<width;++i) {
        int32_t off=cpu_wram_offset(address>>16,address);
        if(off>=0) ram[off]=value>>(i*8);
        ++address;
    }
}
static void initialize(void) {
    memset(ram,low^high,sizeof(ram)); memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=0xab37; g_cpu.X=index_x; g_cpu.Y=0x73; g_cpu.S=stack_s;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x30|flags;
    cpu_p_to_mirrors(&g_cpu); g_cpu.host_return_valid=2; g_cpu.ram=ram;
    ram[dp+7]=initial_bits; ram[dp+8]=low; ram[dp+9]=low>>8;
    seed(0x7ed000+low,high,2);
    seed((db<<16)|0xdb3,0x6600|player,2);
    seed((db<<16)|0xdd6,slot,1);
    seed((db<<16)|(0x1f11+player),0xab00|(kind==1),2);
    seed((db<<16)|(0x1f19+slot),0x178+(kind==2),2);
    seed((db<<16)|(0x1f17+slot),0x128+(kind==3),2);
    for(unsigned i=0;i<10;++i) seed((db<<16)|(0xa106+i),mask_bytes[i]^mask_salt,1);
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
    if(g_cpu.X!=expected->X || g_cpu.Y!=expected->Y || g_cpu.S!=expected->S)
        fprintf(stderr,"register mismatch low=%04x value=%04x kind=%u DB=%02x D=%04x S=%04x guard=%04x cutoff=%llu: X=%04x/%04x Y=%04x/%04x S=%04x/%04x\n",
            low,high,kind,db,dp,stack_s,guard_pc,(unsigned long long)deadline,
            g_cpu.X,expected->X,g_cpu.Y,expected->Y,g_cpu.S,expected->S);
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
    Write expected_writes[64],final_writes[64];
    uint64_t cutoff=deadline; unsigned guard=guard_pc;
    initialize(); uint32_t pc=interpret((pb<<16)|CODE_PC);
    CpuState expected=g_cpu,final=g_cpu; unsigned count=write_count,final_count=count;
    memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_writes,writes,sizeof(writes));
    if(!skip_continuation && (pc&65535)!=0x9234) {
        deadline=0; guard_pc=0; interpret(pc); final=g_cpu; final_count=write_count;
        memcpy(final_ram,ram,sizeof(ram)); memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff; guard_pc=guard; initialize(); RecompReturn result=Probe_M1X1(&g_cpu);
    compare(&expected,expected_ram,expected_writes,count);
    assert(result==(yielded?(RecompReturn)RECOMP_RETURN_LLE_UNWIND_BASE:RECOMP_RETURN_NORMAL));
    assert((!yielded && (pc&65535)==0x9234) || yielded==pc);
    if(yielded && !skip_continuation) {
        deadline=0; guard_pc=0; interpret(yielded); compare(&final,final_ram,final_writes,final_count);
    }
    guard_pc=guard;
    /* Independent binary result checks supplement the interpreter oracle. */
#ifndef RELOCATED_FIXTURE
    if(!skip_continuation && dp==0 && stack_s==0x1ed && db==0x7e &&
       !player && !slot) {
        int hit=-1;
        for(int i=9;i>=0;--i) {
            if(table_bytes[i]==255 ? kind==0 : table_bytes[i]==(high&255)) {
                hit=i; break;
            }
        }
        unsigned value=initial_bits;
        if(hit>=0) value|=mask_bytes[hit]^mask_salt;
        assert(ram[7]==value && ram[8]==(high&255) && ram[9]==(low>>8));
        assert(g_cpu.X==(hit<0?255:(unsigned)hit) && g_cpu.Y==0x73);
        assert(g_cpu.m_flag && g_cpu.x_flag);
    }
#endif
    return 1;
}
static void entry_guard(unsigned bad_dp,unsigned bad_s,unsigned emulation) {
    dp=bad_dp; initialize(); g_cpu.S=bad_s; g_cpu.emulation=emulation;
    static uint8_t memory[sizeof(ram)]; memcpy(memory,ram,sizeof(ram));
    CpuState before=g_cpu;
    Probe_M1X1(&g_cpu);
    assert(yielded==((pb<<16)|CODE_PC) && !g_cpu.master_cycles && !write_count);
    assert(!memcmp(memory,ram,sizeof(ram)) && !g_recomp_stack_top);
    assert(g_cpu.A==before.A && g_cpu.S==before.S && g_cpu.P==before.P);
}
int main(void) {
    unsigned cases=0;
    pb=CODE_BANK; db=0x7e; dp=0; index_x=0; deadline=0; refresh_at=100;
#ifdef RELOCATED_FIXTURE
    low=1; high=0; kind=0; flags=0xc7; guard_pc=COMPARE_GUARD; cases+=check();
    assert(yielded==(COMPARE_GUARD?((pb<<16)|COMPARE_GUARD):0));
#else
    for(unsigned a=0;a<65536;++a) {
        low=a; high=(a*73+0x89ab)&65535; index_x=a&255;
        initial_bits=a&255; mask_salt=(a>>8)&255; kind=a%4;
        flags=(a&1?0xc7:0)|(a&2?8:0); guard_pc=a==0x2fff?0xa114:0;
        cases+=check();
    }
    low=0x101; guard_pc=0;
    for(unsigned a=0;a<65536;++a) {
        high=a; kind=a%4; initial_bits=(a>>8)&255; mask_salt=a&255;
        flags=(a&1?0xc7:0)|(a&2?8:0); index_x=(a>>8)&255; cases+=check();
    }
    /* All low values, initial output masks and predicate outcomes. */
    low=0x123; mask_salt=0;
    for(unsigned value=0;value<256;++value) for(unsigned bits=0;bits<256;++bits)
    for(unsigned state=0;state<4;++state) {
        high=0x5500|value; initial_bits=bits; kind=state; flags=0xc7|(bits&1?8:0);
        cases+=check();
    }
    const unsigned dbs[]={0,0x80,0x15,0x95,0x7e,0x7f};
    const unsigned dps[]={0,0x101,0x1ff6};
    const unsigned stacks[]={1,0x1ed,0x1ffd};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<6;++di) for(unsigned dpi=0;dpi<3;++dpi)
    for(unsigned si=0;si<3;++si) for(unsigned state=0;state<4;++state) {
        /* Rewritten return frames are outside this leaf harness. */
        if(dps[dpi]+7<=stacks[si]+2 && dps[dpi]+8>=stacks[si]+1) continue;
        pb=CODE_BANK+mirror*0x80; db=dbs[di]; dp=dps[dpi]; stack_s=stacks[si];
        low=0x101; high=0; kind=state; initial_bits=0x55; mask_salt=0x81;
        index_x=0xff; flags=0xc7|(state&1?8:0); g_memsel=fast; deadline=0;
        cases+=check();
    }
    /* All four sentinel outcomes, ordinary matches and complete no-match. */
    const unsigned values[]={0x31,0x30,0xfe,0x35,0x37,0,0,0,0};
    const unsigned kinds[]={0,0,1,1,1,0,1,2,3};
    pb=CODE_BANK|0x80; db=0x7e; dp=0x101; stack_s=0x1ed;
    for(unsigned fast=0;fast<2;++fast) for(unsigned decimal=0;decimal<2;++decimal)
    for(unsigned vi=0;vi<9;++vi) for(unsigned cut=1;cut<=3500;++cut) {
        low=0x101; high=0xaa00|values[vi]; kind=kinds[vi]; initial_bits=0x55;
        flags=0xc7|decimal*8; index_x=(vi*37)&255; g_memsel=fast; deadline=cut;
        cases+=check();
    }
    /* Word endpoints and live-read guards after the sentinel saves X. */
    deadline=0; dp=0x101; low=0x2fff; high=0; kind=0;
    guard_pc=0xa114; cases+=check();
    low=1; db=0x40; guard_pc=0xa138; cases+=check();
    db=0; player=0xed; slot=0; guard_pc=0; cases+=check();
    player=0; slot=0xe5; cases+=check();
    player=0xee; slot=0; guard_pc=0xa13f; cases+=check();
    player=0; slot=0xe6; guard_pc=0xa14a; cases+=check();
    slot=0; stack_s=0; kind=1; guard_pc=0xa12e; cases+=check();
    kind=0; guard_pc=0xa12e; cases+=check();
    stack_s=0x1ed; guard_pc=0;
    entry_guard(0x1ff7,0x1ed,0); ++cases;
    entry_guard(0x101,0x1ffe,0); ++cases;
    entry_guard(0x101,0x1ed,1); ++cases;
#endif
    printf("Buffer flags: %u state/write-order/clock/continuation cases passed\n",cases);
    return 0;
}
