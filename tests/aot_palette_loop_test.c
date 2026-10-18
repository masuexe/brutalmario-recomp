/* Real ROM leaves on a controlled bus, including full palette event streams. */
#define PALETTE_LOOP_FIXTURE 1
#include "aot_mmio_event_test.c"

static unsigned pattern;
static uint8_t FixtureRead(uint8_t bank,uint16_t addr) {
    (void)bank;
    if(addr>=TABLE_BASE && addr<TABLE_BASE+sizeof(table_bytes)) {
        uint8_t value=table_bytes[addr-TABLE_BASE];
        if(addr>=INDEX_BASE && addr<=INDEX_BASE+COLOR_COUNT)
            return pattern==1?0:value;
        return pattern==2?(value^0xa5):value;
    }
    return 0;
}
static void FixtureInitialize(unsigned db) {
    ram[0xdde]=0x9b; /* live final LDX in the second leaf */
    if(db==0x7e || db==0x7f) {
        unsigned base=db==0x7f?0x10000:0;
        ram[base+0xdde]=0x9b;
        for(unsigned i=0;i<sizeof(table_bytes);++i)
            ram[base+TABLE_BASE+i]=FixtureRead(db,TABLE_BASE+i);
    }
}
int main(void) {
    static uint8_t expected_ram[sizeof(ram)];
    Event expected_events[768];
    unsigned cases=0;
    unsigned dbs[]={0,0x3f,0x80,0xbf,0x7e,0x7f};
    for(unsigned fast=0;fast<2;++fast) for(unsigned mirror=0;mirror<2;++mirror)
    for(unsigned di=0;di<6;++di) for(pattern=0;pattern<3;++pattern)
    for(unsigned dp=0;dp<=0x101;dp+=0x101) {
        unsigned pb=CODE_BANK+mirror*0x80,db=dbs[di];
        g_memsel=fast; deadline=0; refresh_at=100;
        initialize(pb,db,1320); g_cpu.D=dp;
        interpret((pb<<16)|CODE_PC); CpuState expected=g_cpu;
        unsigned count=event_count;
        memcpy(expected_events,events,sizeof(events)); memcpy(expected_ram,ram,sizeof(ram));
        assert(count==((pattern==1 || db==0x7e || db==0x7f)?0:3*COLOR_COUNT));
        initialize(pb,db,1320); g_cpu.D=dp;
        Probe_M1X1(&g_cpu); assert(!yielded);
        compare_state(expected,expected_ram); compare_events(expected_events,count,0);
        ++cases;
    }
    /* Every master-clock cutoff through the entire observed loop, with
     * refresh, must preserve events and the exact continuation instruction. */
    pattern=0; g_memsel=1; deadline=0; refresh_at=100;
    initialize(CODE_BANK|0x80,0,0); interpret(((CODE_BANK|0x80)<<16)|CODE_PC);
    unsigned limit=g_cpu.master_cycles+1;
    for(unsigned cut=1;cut<=limit;++cut) {
        deadline=cut;
        initialize(CODE_BANK|0x80,0,0);
        uint32_t pc=interpret(((CODE_BANK|0x80)<<16)|CODE_PC);
        CpuState expected=g_cpu; unsigned count=event_count;
        memcpy(expected_events,events,sizeof(events)); memcpy(expected_ram,ram,sizeof(ram));
        initialize(CODE_BANK|0x80,0,0); Probe_M1X1(&g_cpu);
        compare_state(expected,expected_ram); compare_events(expected_events,count,0);
        assert((pc==(((CODE_BANK|0x80)<<16)|0x9234) && !yielded) || pc==yielded);
        ++cases;
    }
    printf("Palette loop $%02X%04X: %u exact-state/event cases; %u colors; full-loop cutoffs=%u\n",
           CODE_BANK,CODE_PC,cases,COLOR_COUNT,limit);
    return 0;
}
