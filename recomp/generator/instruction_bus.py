"""Opt-in native function timing; reject instructions not yet modeled.

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
                  0xbd: 1, 0x80: 0, 0xae: 1,
                  0xeb: 0, 0xc2: 0, 0xe2: 0, 0x38: 0, 0xf9: 1, 0x99: 1,
                  0x8a: 0, 0x18: 0, 0x69: 0, 0xaa: 0, 0xa0: 0,
                  0x20: 2, 0xfd: 1, 0xb0: 0, 0xc6: 2,
                  0x7d: 1, 0x09: 0, 0x5a: 1, 0x7a: 1, 0x98: 0, 0xc8: 0, 0x90: 0,
                  0x29: 0, 0x0a: 0, 0x65: 1, 0xda: 1, 0xfa: 1, 0xbf: 1}
DP_END = {0xa7: 2, 0xa6: 1, 0xe6: 0, 0x86: 1, 0x85: 0, 0x25: 0, 0xa5: 0,
          0xc6: 0, 0x65: 0}
ABS_READS = {0xbc: 'X', 0xb9: 'Y', 0xac: None, 0xad: None, 0xbd: 'X', 0xae: None,
             0xf9: 'Y', 0xfd: 'X', 0x7d: 'X'}
WRAM_WRITES = {0x8d, 0x9f, 0x99}


def transfers(insn):
    if insn.opcode in (0xa6, 0x86, 0xbc, 0xac, 0xae, 0xda, 0xfa):
        return 1 if insn.x_flag else 2
    if insn.opcode in (0xf9, 0x99, 0xa5, 0x85, 0x65, 0xbd, 0xbf):
        return 1 if insn.m_flag else 2
    return DATA_TRANSFERS[insn.opcode]


def selected(bank, start, m, x):
    return f'{bank:02X}{start:04X}:M{m}X{x}' in INSTRUCTION_BUS_VARIANTS


def validate(blocks):
    max_dp, pointers = 0, set()
    for pairs in blocks.values():
        for insn, _ in pairs:
            wide = insn.m_flag == 0 and (
                insn.opcode in (0x38, 0xf9, 0x99, 0xe2) or
                (insn.x_flag == 1 and insn.opcode in
                 (0xa5, 0x85, 0x65, 0x29, 0x0a, 0x18, 0x69, 0xf0, 0xbd, 0x60)) or
                insn.opcode in (0xc2, 0xc9, 0xb0, 0xda, 0xfa, 0xa6, 0xbf, 0x29, 0xf0))
            if (insn.opcode not in DATA_TRANSFERS or
                    (insn.m_flag != 1 and not wide) or insn.x_flag not in (0, 1) or
                    (insn.opcode in (0xc2, 0xe2) and not (
                        insn.operand == 0x20 or
                        (insn.operand == 0x30 and insn.m_flag == 0))) or
                    (insn.opcode in (0x5a, 0x7a) and insn.x_flag != 1)):
                raise ValueError('instruction-bus timing requires a supported native width/opcode combination: '
                                 f'${insn.addr:06X} {insn.mnem}')
            if insn.opcode == 0x20 and not selected(
                    insn.addr >> 16, insn.operand, insn.m_flag, insn.x_flag):
                raise ValueError('instruction-bus calls require a qualified callee: '
                                 f'${insn.addr:06X} -> ${insn.operand:04X}')
            if insn.opcode in DP_END:
                end = DP_END[insn.opcode]
                if insn.opcode in (0xa6, 0x86) and insn.x_flag:
                    end = 0
                if insn.opcode in (0xa5, 0x85, 0x65) and not insn.m_flag:
                    end = 1
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
    if insn.opcode == 0x5a:
        guard += ' || cpu->S > 0x1fffu'
    if insn.opcode == 0x7a:
        guard += ' || cpu->S >= 0x1fffu'
    if insn.opcode == 0xda:
        width = transfers(insn)
        guard += f' || cpu->S < {width - 1}u || cpu->S > 0x1fffu'
    if insn.opcode == 0xfa:
        guard += f' || cpu->S > {0x1fff - transfers(insn)}u'
    if insn.opcode == 0xbf:
        address = f'((0x{insn.operand:06x}u + cpu->X) & 0xffffffu)'
        width = transfers(insn)
        guard += f' || !M1AotBusAddressSupported({address}, {width}u)'
        if width == 2:
            guard += f' || (({address} & 0xffffu) == 0xffffu)'
    if insn.opcode == 0x20:
        # Both native JSR pushes must land in WRAM before entering a child.
        guard += ' || cpu->S == 0 || cpu->S > 0x1fffu'
    if insn.opcode in ABS_READS:
        index = ABS_READS[insn.opcode]
        address = f"(((uint32)cpu->DB << 16) + 0x{insn.operand:04x}u"
        address += f" + cpu->{index})" if index else ")"
        width = transfers(insn)
        guard += f" || !M1AotBusAddressSupported({address}, {width}u)"
        if width == 2:
            # Runtime word accessors wrap the high byte within its bank;
            # interp816 indexed words carry into the next bank. Defer that
            # unsupported endpoint before either byte is read.
            guard += f" || (({address} & 0xffffu) == 0xffffu)"
    palette = insn.opcode == 0x8d and insn.operand in (0x2121, 0x2122)
    if insn.opcode in WRAM_WRITES:
        if insn.opcode == 0x8d:
            address = f"(((uint32)cpu->DB << 16) | 0x{insn.operand:04x}u)"
        elif insn.opcode == 0x99:
            address = f"(((uint32)cpu->DB << 16) + 0x{insn.operand:04x}u + cpu->Y)"
        else:
            address = f"((0x{insn.operand:06x}u + cpu->X) & 0xffffffu)"
        checker = 'M1AotPaletteWriteSupported' if palette else 'M1AotBusWriteSupported'
        width = transfers(insn)
        guard += f" || !{checker}({address}, {width}u)"
        if width == 2:
            guard += f" || (({address} & 0xffffu) == 0xffffu)"
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
    # The upstream word-push emitter predecrements S, writes a little-endian
    # word, then decrements S again. Timed PHX must instead write high at
    # the original S before low at S-1. Restore S for that first byte so
    # the paced accesses also observe the architectural stack pointer.
    word_push = 'cpu_write16(cpu, 0x00, cpu->S, cpu->X);'
    if word_push in line:
        return line.replace(word_push,
            'cpu->S = (uint16)(cpu->S + 1); '
            'cpu_write8_paced(cpu, 0x00, cpu->S, (uint8)(cpu->X >> 8)); '
            'cpu->S = (uint16)(cpu->S - 1); '
            'cpu_write8_paced(cpu, 0x00, cpu->S, (uint8)cpu->X);')
    if re.search(r'\bcpu_write8\(cpu, cpu->DB, \(uint16\)\(0x212[12]\), ', line):
        return line.replace('cpu_write8(', 'M1AotPaletteWrite8(').replace(
            ');', ', _m1_palette_fetch_master);')
    for name in ('cpu_read8', 'cpu_read16', 'cpu_write8', 'cpu_write16'):
        line = line.replace(name + '(', name + '_paced(')
    return line
