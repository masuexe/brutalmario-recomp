/* WRAM record writers: nested calls, decimal pointers and bounded fallbacks. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "cpu_state.h"
#include "common_cpu_infra.h"
#include "snes/snes.h"
#include "snes/interp816.h"
#include "records_fixture.h"
#define NESTED_CALL_FIXTURE 1
#define HELPER_TABLE_FIXTURE 1
static int unwind_parents;
typedef struct { uint32_t address; uint8_t value; } Write;
static Write writes[128];
static unsigned write_count;
static void RecordBusWrite(uint32_t address,uint8_t value) {
    assert(write_count<128); writes[write_count++]=(Write){address,value};
}
static uint8_t FixtureRead(uint8_t bank,uint16_t addr) {
    if((bank==0x15 || bank==0x95) && addr>=0xa197 && addr<0xa19f)
        return mask_bytes[addr-0xa197];
    return ((uint32_t)bank*19+addr*17+(addr>>8))&255;
}
#include "aot_bus_test_support.h"
RecompReturn Caller_M1X1(CpuState *);
RecompReturn Callee_M1X1(CpuState *);
RecompReturn bank_15_A25B_M1X1(CpuState *cpu) { return Callee_M1X1(cpu); }
RecompReturn bank_15_A25B_M0X0(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn bank_15_A25B_M0X1(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn bank_15_A25B_M1X0(CpuState *cpu) { (void)cpu; assert(0); return 0; }
RecompReturn interp_tier_run_call_frame(CpuState *cpu,uint32_t target,uint32_t site,
                                      uint8_t size,uint32_t *out) {
    (void)cpu; (void)target; (void)site; (void)size; (void)out; assert(0); return 0;
}
static unsigned pointer,status,selector,bit_flags,dp,db,pb,flags,stack_s=0x1ed;
static unsigned root_pc=0xa19f,forced_pc;
static int skip_case,skip_continuation;
static unsigned stop_pc=0x9234;
/* Independently stop the oracle before unsupported data accesses. The test
   bus has no MMIO/cartridge writes; a guard hands back ownership at this PC.
   Word-bank endpoints also differ between the two underlying accessors. */
static int unsafe_next(Interp816 *in) {
    if(in->pc<CODE_PC || in->pc>=CODE_PC+sizeof(code)) return 0;
    unsigned at=in->pc-CODE_PC,op=code[at];
    if(op==0x9f || op==0x8f) {
        uint32_t address=code[at+1]|(code[at+2]<<8)|(code[at+3]<<16);
        if(op==0x9f) address=(address+in->x)&0xffffff;
        unsigned width=in->mf?1:2;
        for(unsigned i=0;i<width;++i) {
            uint32_t byte=(address+i)&0xffffff;
            int32_t off=cpu_wram_offset(byte>>16,byte);
            if(off>=0 && off<65536 && off>=((int)stack_s-1) && off<=(int)stack_s+2) {
                skip_case=1; return 1; /* rewritten return frame outside scope */
            }
            if(off<0) return 1;
        }
        if(width==2 && (address&65535)==65535) return 1;
    }
    if(op==0xad || op==0x39) {
        uint32_t address=(in->db<<16)|(code[at+1]|(code[at+2]<<8));
        if(op==0x39) address+=in->y;
        if(cpu_wram_offset(address>>16,address)<0 && (address&65535)<0x8000) return 1;
    }
    return 0;
}
static uint32_t interpret(uint32_t pc) {
    Interp816 in={0}; cpu_mirrors_to_p(&g_cpu);
    in.mem=&g_cpu; in.read=read_bus; in.write=write_bus;
    in.a=g_cpu.A; in.x=g_cpu.X; in.y=g_cpu.Y; in.sp=g_cpu.S;
    in.dp=g_cpu.D; in.db=g_cpu.DB; in.k=g_cpu.PB; in.pc=pc; in.e=g_cpu.emulation;
    interp816_setFlags(&in,g_cpu.P);
    unsigned steps=0;
    while(in.pc!=stop_pc && !(forced_pc && in.pc==forced_pc) &&
          !(deadline && g_cpu.master_cycles>=deadline)) {
        if(unsafe_next(&in)) break;
        assert(++steps<160); transfers=0; bus_master=0;
        int cycles=interp816_runOpcode(&in); assert((unsigned)cycles>=transfers);
        g_cpu.cycles+=cycles; g_cpu.master_cycles+=bus_master+6*(cycles-transfers);
        snes_refresh_charge(); g_cpu.coprocessor_master_cycles=g_cpu.master_cycles;
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
    memset(ram,0xa7,sizeof(ram)); memset(&g_cpu,0,sizeof(g_cpu));
    g_cpu.A=0xab37; g_cpu.X=0xd3; g_cpu.Y=0x73; g_cpu.S=stack_s;
    g_cpu.D=dp; g_cpu.DB=db; g_cpu.PB=pb; g_cpu.P=0x30|flags;
    cpu_p_to_mirrors(&g_cpu); g_cpu.host_return_valid=2; g_cpu.ram=ram;
    seed((db<<16)|0x6b7,selector,1);
    for(unsigned i=0;i<8;++i) seed((db<<16)|(0xa197+i),mask_bytes[i],1);
    seed(0x7f1820+(selector>>3),bit_flags,1);
    seed(0x7fffdd,status,1); seed(0x7f837b,pointer,2);
    ram[(stack_s+1)&65535]=0x33; ram[(stack_s+2)&65535]=0x92;
    yielded=0; last_sync=0; refreshed=0; g_recomp_stack_top=0;
    write_count=0; unwind_parents=0; skip_case=0;
}
static void compare(const CpuState *expected,const uint8_t *memory,
                    const Write *expected_writes,unsigned count) {
    cpu_mirrors_to_p(&g_cpu);
    if(g_cpu.A!=expected->A || g_cpu.P!=expected->P ||
       g_cpu.cycles!=expected->cycles || g_cpu.master_cycles!=expected->master_cycles) {
        fprintf(stderr,"helper %06x lo=%02x hi=%02x X=%02x DB=%02x D=%04x P=%02x cutoff=%llu: A=%04x/%04x P=%02x/%02x clocks=%llu/%llu cycles=%llu/%llu\n",
            (CODE_BANK<<16)|CODE_PC,pointer,status,selector,db,dp,flags,(unsigned long long)deadline,
            g_cpu.A,expected->A,g_cpu.P,expected->P,
            (unsigned long long)g_cpu.master_cycles,(unsigned long long)expected->master_cycles,
            (unsigned long long)g_cpu.cycles,(unsigned long long)expected->cycles);
        assert(0);
    }
    if(g_cpu.X!=expected->X || g_cpu.Y!=expected->Y || g_cpu.S!=expected->S)
        fprintf(stderr,"register mismatch low=%04x value=%04x kind=%u DB=%02x D=%04x S=%04x guard=%04x cutoff=%llu: X=%04x/%04x Y=%04x/%04x S=%04x/%04x\n",
            pointer,status,bit_flags,db,dp,stack_s,forced_pc,(unsigned long long)deadline,
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
    Write expected_writes[128],final_writes[128];
    uint64_t cutoff=deadline; unsigned forced=forced_pc;
    initialize(); uint32_t pc=interpret((pb<<16)|root_pc);
    if(skip_case) return 0;
    CpuState expected=g_cpu,final=g_cpu; unsigned count=write_count,final_count=count;
    memcpy(expected_ram,ram,sizeof(ram)); memcpy(expected_writes,writes,sizeof(writes));
    uint32_t final_pc=pc;
    if(!skip_continuation && (pc&65535)!=stop_pc) {
        deadline=0; forced_pc=0; final_pc=interpret(pc);
        if(skip_case) { forced_pc=forced; deadline=cutoff; return 0; }
        final=g_cpu; final_count=write_count;
        memcpy(final_ram,ram,sizeof(ram)); memcpy(final_writes,writes,sizeof(writes));
    }
    deadline=cutoff; forced_pc=forced; initialize();
    RecompReturn result=root_pc==0xa19f?Caller_M1X1(&g_cpu):Callee_M1X1(&g_cpu);
    compare(&expected,expected_ram,expected_writes,count);
    assert(result==(yielded?(RecompReturn)(RECOMP_RETURN_LLE_UNWIND_BASE-unwind_parents):RECOMP_RETURN_NORMAL));
    assert((!yielded && (pc&65535)==stop_pc) || yielded==pc);
    if(yielded && !skip_continuation) {
        deadline=0; forced_pc=0; interpret(yielded); compare(&final,final_ram,final_writes,final_count);
    }
    forced_pc=forced;
    /* Independent binary record checks for bounded, non-aliasing contexts. */
    if(!(flags&8) && pointer<=0xd0 && status==0 && db==0x7e &&
       (final_pc&65535)==stop_pc) {
        int alternate=root_pc==0xa25b || (bit_flags&mask_bytes[selector&7]);
        assert(ram[0x1ffdd]==(alternate?0x33:0x22));
        assert((ram[0x1837b]|(ram[0x1837c]<<8))==pointer+24);
        const unsigned heads[]={0x7c50,0x7d50,0x9c50,0x9d50};
        const unsigned alternate_payloads[]={0x3838,0x3839,0x3848,0x3849};
        for(unsigned i=0;i<4;++i) {
            unsigned at=0x1837d+pointer+i*6;
            assert((ram[at]|(ram[at+1]<<8))==heads[i]);
            assert(ram[at+2]==0 && ram[at+3]==1);
            assert((ram[at+4]|(ram[at+5]<<8))==(alternate?alternate_payloads[i]:0x38fe));
        }
        assert(ram[0x18383+((pointer+18)&255)]==255);
        assert(g_cpu.X==((pointer+18)&255) && g_cpu.A==0x38ff);
    }
    return 1;
}
static unsigned entry_guard(unsigned bad_dp,unsigned bad_s,unsigned emulation) {
    dp=bad_dp; initialize(); g_cpu.S=bad_s; g_cpu.emulation=emulation;
    static uint8_t memory[sizeof(ram)]; memcpy(memory,ram,sizeof(ram));
    CpuState before=g_cpu;
    RecompReturn result=root_pc==0xa19f?Caller_M1X1(&g_cpu):Callee_M1X1(&g_cpu);
    assert(result==(RecompReturn)RECOMP_RETURN_LLE_UNWIND_BASE);
    assert(yielded==((pb<<16)|root_pc) && !g_cpu.master_cycles && !write_count);
    assert(!memcmp(memory,ram,sizeof(ram)) && !g_recomp_stack_top);
    assert(g_cpu.A==before.A && g_cpu.S==before.S && g_cpu.P==before.P);
    return 1;
}
int main(void) {
    unsigned cases=0;
    pb=CODE_BANK; db=0x7e; dp=0; deadline=0; refresh_at=100;
    for(unsigned leaf=0;leaf<2;++leaf) {
        root_pc=leaf?0xa25b:0xa19f; status=0; selector=0x37; bit_flags=0xff;
        for(unsigned value=0;value<65536;++value) for(unsigned decimal=0;decimal<2;++decimal) {
            pointer=value; flags=0xc7|decimal*8; deadline=0; cases+=check();
        }
    }
    root_pc=0xa19f; pointer=0x40;
    for(unsigned i=0;i<256;++i) for(unsigned bits=0;bits<256;++bits) {
        selector=i; bit_flags=bits; status=bits%3==0?0:bits%3==1?0x22:0x33;
        flags=0xc7|(i&1?8:0); deadline=0; cases+=check();
    }
    const unsigned dbs[]={0,0x80,0x15,0x95,0x7e,0x7f};
    const unsigned dps[]={0,0x101,0x1fff};
    const unsigned stacks[]={2,0x1ed,0x1ffd};
    for(unsigned leaf=0;leaf<2;++leaf) for(unsigned fast=0;fast<2;++fast)
    for(unsigned mirror=0;mirror<2;++mirror) for(unsigned di=0;di<6;++di)
    for(unsigned dpi=0;dpi<3;++dpi) for(unsigned si=0;si<3;++si)
    for(unsigned state=0;state<3;++state) {
        root_pc=leaf?0xa25b:0xa19f; pb=CODE_BANK+mirror*0x80;
        db=dbs[di]; dp=dps[dpi]; stack_s=stacks[si];
        pointer=0x40; status=state==0?0:state==1?0x22:0x33;
        selector=cases&255; bit_flags=cases&1?0xff:0; flags=0xc7|(state&1?8:0);
        g_memsel=fast; deadline=0; cases+=check();
    }
    /* Both writers, both status gates, parent/child cutoffs and pointer edges. */
    pb=CODE_BANK|0x80; db=0x7e; dp=0x101; stack_s=0x1ed; selector=0;
    const unsigned ptrs[]={0,0xd0,0x7c60,0xffff,0x7c81,0x9999};
    for(unsigned path=0;path<6;++path) for(unsigned fast=0;fast<2;++fast)
    for(unsigned decimal=0;decimal<2;++decimal) for(unsigned cut=1;cut<=4000;++cut) {
        root_pc=path>=4?0xa25b:0xa19f; bit_flags=path&1?0xff:0;
        status=path==0?0x22:path==1?0x33:path==4?0x33:0;
        pointer=ptrs[path]; flags=0xc7|decimal*8; g_memsel=fast; deadline=cut;
        cases+=check();
    }
    deadline=0; pointer=0; status=0; root_pc=0xa19f; bit_flags=0xff;
    const unsigned stacks_guard[]={0,1};
    for(unsigned i=0;i<2;++i) {
        stack_s=stacks_guard[i]; forced_pc=i?0xa25b:0xa1b5;
        skip_continuation=i==0; cases+=check();
    }
    skip_continuation=0; forced_pc=0; stack_s=0x1ed; db=0x40; cases+=check();
    for(unsigned leaf=0;leaf<2;++leaf) {
        root_pc=leaf?0xa25b:0xa19f; db=0x7e;
        cases+=entry_guard(0x2000,0x1ed,0);
        cases+=entry_guard(0,0x1ffe,0);
        cases+=entry_guard(0,0x1ed,1);
    }
    printf("Record writers: %u state/write-order/clock/continuation cases passed\n",cases);
    return 0;
}
