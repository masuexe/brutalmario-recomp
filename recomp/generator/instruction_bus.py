"""Opt-in native M1/X0 leaf timing; reject instructions not yet modeled.

Fetches and internal cycles are charged here. Actual data/stack transfers
use the runtime's existing paced accessors. No ROM addresses are special.
"""
from snes_cycles import instr_static_cycles
from .project_aot_policy import INSTRUCTION_BUS_VARIANTS

# Architectural data transfers, excluding fetches. All modeled widths are fixed.
DATA_TRANSFERS = {0xa7: 4, 0xa6: 2, 0xe8: 0, 0xd0: 0,
                  0xa2: 0, 0xe6: 2, 0x86: 2, 0x60: 2}
DP_END = {0xa7: 2, 0xa6: 1, 0xe6: 0, 0x86: 1}


def selected(bank, start, m, x):
    return f'{bank:02X}{start:04X}:M{m}X{x}' in INSTRUCTION_BUS_VARIANTS


def validate(blocks):
    max_dp, pointers = 0, set()
    for pairs in blocks.values():
        for insn, _ in pairs:
            if (insn.opcode not in DATA_TRANSFERS or
                    insn.m_flag != 1 or insn.x_flag != 0):
                raise ValueError('instruction-bus timing requires a supported native M1/X0 leaf: '
                                 f'${insn.addr:06X} {insn.mnem}')
            if insn.opcode in DP_END:
                max_dp = max(max_dp, insn.operand + DP_END[insn.opcode])
            if insn.opcode == 0xa7:
                pointers.add(insn.operand)
    return max_dp, sorted(pointers)


def prefix(insn, target_expr):
    cycles = instr_static_cycles(insn.opcode, insn.m_flag, insn.x_flag)
    internal = cycles - insn.length - DATA_TRANSFERS[insn.opcode]
    if internal < 0:
        raise ValueError('instruction timing has more transfers than CPU cycles')
    fetches = [f'cpu_region_speed(((uint32)cpu->PB << 16) | 0x{(insn.addr + i) & 0xffff:04x}u)'
               for i in range(insn.length)]
    return [
        'M1AotBusBoundary(cpu);',
        'if (interp_bridge_lle_master_deadline_reached(cpu)) {',
        f'  return interp_bridge_lle_yield_unwind(cpu, {target_expr});',
        '}',
        f'cpu->cycles += {cycles};',
        'cpu->master_cycles += ' + ' + '.join(fetches + [str(internal * 6)]) + ';',
    ]


def pace(line):
    for name in ('cpu_read8', 'cpu_read16', 'cpu_write8', 'cpu_write16'):
        line = line.replace(name + '(', name + '_paced(')
    return line
