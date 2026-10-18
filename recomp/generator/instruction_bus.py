"""Opt-in native M1 leaf timing; reject instructions not yet modeled.

Fetches and internal cycles are charged here. Actual data/stack transfers
use the runtime's existing paced accessors. No ROM addresses are special.
"""
import re
from snes_cycles import instr_static_cycles
from .project_aot_policy import INSTRUCTION_BUS_VARIANTS

# Architectural transfers excluding fetches. Widths are resolved per instruction.
DATA_TRANSFERS = {0xa7: 4, 0xa6: 2, 0xe8: 0, 0xd0: 0,
                  0xa2: 0, 0xe6: 2, 0x86: 2, 0x60: 2,
                  0xbc: 1, 0xb9: 1, 0x85: 1, 0xac: 1, 0xc0: 0,
                  0xad: 1, 0x4a: 0, 0xa8: 0, 0x25: 1, 0xf0: 0, 0xa9: 0,
                  0xc9: 0, 0xca: 0, 0x10: 0, 0x9f: 1, 0xa5: 1, 0x8d: 1,
                  0xbd: 1, 0x80: 0, 0xae: 1}
DP_END = {0xa7: 2, 0xa6: 1, 0xe6: 0, 0x86: 1, 0x85: 0, 0x25: 0, 0xa5: 0}
ABS_READS = {0xbc: 'X', 0xb9: 'Y', 0xac: None, 0xad: None, 0xbd: 'X', 0xae: None}
WRAM_WRITES = {0x8d, 0x9f}


def transfers(insn):
    if insn.opcode in (0xa6, 0x86, 0xbc, 0xac, 0xae):
        return 1 if insn.x_flag else 2
    return DATA_TRANSFERS[insn.opcode]


def selected(bank, start, m, x):
    return f'{bank:02X}{start:04X}:M{m}X{x}' in INSTRUCTION_BUS_VARIANTS


def validate(blocks):
    max_dp, pointers = 0, set()
    for pairs in blocks.values():
        for insn, _ in pairs:
            if (insn.opcode not in DATA_TRANSFERS or
                    insn.m_flag != 1 or insn.x_flag not in (0, 1)):
                raise ValueError('instruction-bus timing requires a supported native M1 leaf: '
                                 f'${insn.addr:06X} {insn.mnem}')
            if insn.opcode in DP_END:
                end = DP_END[insn.opcode]
                if insn.opcode in (0xa6, 0x86) and insn.x_flag:
                    end = 0
                max_dp = max(max_dp, insn.operand + end)
            if insn.opcode == 0xa7:
                pointers.add(insn.operand)
    return max_dp, sorted(pointers)


def prefix(insn, target_expr):
    cycles = instr_static_cycles(insn.opcode, insn.m_flag, insn.x_flag)
    internal = cycles - insn.length - transfers(insn)
    if internal < 0:
        raise ValueError('instruction timing has more transfers than CPU cycles')
    fetches = [f'cpu_region_speed(((uint32)cpu->PB << 16) | 0x{(insn.addr + i) & 0xffff:04x}u)'
               for i in range(insn.length)]
    guard = "interp_bridge_lle_master_deadline_reached(cpu)"
    if insn.opcode in ABS_READS:
        index = ABS_READS[insn.opcode]
        address = f"(((uint32)cpu->DB << 16) + 0x{insn.operand:04x}u"
        address += f" + cpu->{index})" if index else ")"
        width = transfers(insn)
        guard += f" || !M1AotBusAddressSupported({address}, {width}u)"
    palette = insn.opcode == 0x8d and insn.operand in (0x2121, 0x2122)
    if insn.opcode in WRAM_WRITES:
        if insn.opcode == 0x8d:
            address = f"(((uint32)cpu->DB << 16) | 0x{insn.operand:04x}u)"
        else:
            address = f"((0x{insn.operand:06x}u + cpu->X) & 0xffffffu)"
        checker = 'M1AotPaletteWriteSupported' if palette else 'M1AotBusWriteSupported'
        guard += f" || !{checker}({address}, 1u)"
    return [
        'M1AotBusBoundary(cpu);',
        f'if ({guard}) {{',
        f'  return interp_bridge_lle_yield_unwind(cpu, {target_expr});',
        '}',
        *([f'_m1_palette_fetch_master = {" + ".join(fetches)};'] if palette else [
            f'cpu->cycles += {cycles};',
            'cpu->master_cycles += ' + ' + '.join(fetches + [str(internal * 6)]) + ';']),
    ]


def pace(line):
    if re.search(r'\bcpu_write8\(cpu, cpu->DB, \(uint16\)\(0x212[12]\), ', line):
        return line.replace('cpu_write8(', 'M1AotPaletteWrite8(').replace(
            ');', ', _m1_palette_fetch_master);')
    for name in ('cpu_read8', 'cpu_read16', 'cpu_write8', 'cpu_write16'):
        line = line.replace(name + '(', name + '_paced(')
    return line
