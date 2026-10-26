#!/usr/bin/env python3
"""Check the bounded mazo 9B entry and preserved native routes.

The recipient already supplies room 190 level data and its sprite list. This
check covers the installed 9B record, the A2 module view and the room 190 entry
window. It does not prove attack damage, a fight clear, a saved completion or
the B0 corridor module. The transient intro actors differ between hosts; the
three persistent 9B parts and the settled state match.
"""
import argparse
import json
from pathlib import Path
import re

from native_mazo import ROOT, identity, packs
from prepare_rom import verify
from qualify_native_content import SIZES
from qualify_native_seven import native_capture as validate_capture
from restore_star_world_1 import sha, write_verified

TARGET = 'demo11-native-mazo-9b'
BASE = 'demo11-native-sprite9e'
DONOR = 'local/captures/mazo-9b-entry-v2-donor'
DONOR_ROM = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'
DONOR_SCRIPT = 'recomp/inputs/mazo-9b-donor-fixture.script'
NATIVE_SCRIPT = 'recomp/inputs/mazo-9b-native-fixture.script'
PERSISTENT = (6, 7, 9)
SUFFIXES = {**SIZES, 'apu.tsv': None, 'ppuw.tsv': None, 'regs.json': None, 'dma.tsv': None}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_text())


def body(directory, tag):
    data = (directory / (tag+'.wram.bin')).read_bytes()
    require(len(data) == 0x20000, 'WRAM size differs')
    require(len((directory / (tag+'.vram.bin')).read_bytes()) == 0x10000, 'VRAM size differs')
    return data


def room(data):
    return int.from_bytes(data[0x10b:0x10d], 'little')


def parts(data):
    slots = [slot for slot in range(12) if data[0x14c8+slot] == 8
             and data[0x1ab10+slot] & 8 and data[0x1ab9e+slot] == 0x9b]
    positions = {slot: (data[0xe4+slot] | (data[0x14e0+slot] << 8),
                        data[0xd8+slot] | (data[0x14d4+slot] << 8)) for slot in slots}
    return slots, positions


def donor_capture():
    directory = ROOT / DONOR
    receipt = read(directory / 'receipt.json')
    require(receipt['rom_sha256'] == DONOR_ROM, 'mazo donor ROM differs')
    require(receipt['script_sha256'] == sha((ROOT / DONOR_SCRIPT).read_bytes()),
            'mazo donor script differs')
    require(receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled' and
            receipt['diagnostic_core_override'] is None, 'reference configuration differs')
    log = (directory / 'run.log').read_text()
    require(' quit' in log and '[wav closed:' in log, 'donor capture did not complete')
    return receipt


def mazo_capture(directory, script):
    receipt = read(directory / 'receipt.json')
    cfg = read(ROOT / 'config/restorations' / (TARGET+'.json'))
    build = read(ROOT / 'local/build' / TARGET / 'm1-build.json')
    require(receipt['target'] == TARGET and receipt['stage'] == 'native', 'native role differs')
    require(receipt['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'],
            'native ROM differs')
    require(receipt['host_binary_sha256'] == build['binary_sha256'], 'binary differs')
    require(receipt['native_content'] == build['native_content'] == identity(TARGET),
            'native module identity differs')
    require(receipt['analysis'] == build['analysis'] and
            receipt['runtime_patches'] == build['runtime_patches'], 'build identity differs')
    require(receipt['route_sha256'] == sha((ROOT / script).read_bytes()), 'route differs')
    require((directory / 'input.script').read_text() == 'turbo on\n'+(ROOT / script).read_text(),
            'executed input copy differs')
    log = (directory / 'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'capture did not complete')
    return receipt, log


def entry():
    donor = donor_capture()
    native = ROOT / 'local/captures/mazo-9b-entry-v3-native'
    receipt, log = mazo_capture(native, NATIVE_SCRIPT)
    require(receipt['native_content'] == identity(TARGET) and
            identity(TARGET)['kind'] == 'immutable-mazo-entry', 'mazo module identity differs')
    require('[native-seven] rejected:' not in log, 'native startup was rejected')
    count = re.search(r'\[native-seven\] bank=A2 resolutions=(\d+) '
                      r'executed_page_instructions=(\d+)', log)
    require(count and int(count.group(1)) > 0 and int(count.group(2)) > 0,
            'the A2 module view did not execute')

    approach = body(native, 'approach146')
    require(approach[0x100] == 0x14 and room(approach) == 0x146, 'native approach differs')

    donor_150 = body(ROOT / DONOR, 'fight150')
    native_150 = body(native, 'fight150')
    for host, data in (('donor', donor_150), ('native', native_150)):
        require(data[0x100] == 0x14 and room(data) == 0x190, host+' room 190 entry differs')
    donor_slots, donor_positions = parts(donor_150)
    native_slots, native_positions = parts(native_150)
    require(set(PERSISTENT) <= set(donor_slots) and set(PERSISTENT) <= set(native_slots),
            'persistent 9B part is absent')
    require({slot: donor_positions[slot] for slot in PERSISTENT} ==
            {slot: native_positions[slot] for slot in PERSISTENT},
            'persistent 9B part position differs')

    donor_600 = body(ROOT / DONOR, 'fight600')
    native_600 = body(native, 'fight600')
    require(donor_600[0x100] == 0x14 and native_600[0x100] == 0x14, 'settled mode differs')
    donor_settled, donor_settled_positions = parts(donor_600)
    native_settled, native_settled_positions = parts(native_600)
    require(donor_settled == native_settled == list(PERSISTENT), 'settled part set differs')
    require(donor_settled_positions == native_settled_positions,
            'settled part position differs')

    donor_late = body(ROOT / DONOR, 'fight1200')
    native_late = body(native, 'fight1200')
    require(donor_late[0x100] == native_late[0x100] == 0x0e, 'map return differs')

    transient_differences = []
    for frame in range(150, 601, 30):
        tag = f'fight{frame:03d}'
        d_slots, d_pos = parts(body(ROOT / DONOR, tag))
        n_slots, n_pos = parts(body(native, tag))
        for slot in range(6):
            if (slot in d_pos) != (slot in n_pos) or (slot in d_pos and d_pos[slot] != n_pos[slot]):
                transient_differences.append({'sample': tag, 'slot': slot,
                                              'donor': list(d_pos.get(slot, ())) or None,
                                              'native': list(n_pos.get(slot, ())) or None})
    require(transient_differences, 'recorded transient intro difference is absent')

    return {'donor_receipt_sha256': sha((ROOT / DONOR / 'receipt.json').read_bytes()),
            'donor_script_sha256': donor['script_sha256'],
            'donor_rom_sha256': donor['rom_sha256'],
            'native_receipt_sha256': sha((native / 'receipt.json').read_bytes()),
            'native_script_sha256': sha((ROOT / NATIVE_SCRIPT).read_bytes()),
            'native_a2_resolutions': int(count.group(1)),
            'native_a2_executed_page_instructions': int(count.group(2)),
            'persistent_slots': list(PERSISTENT),
            'persistent_positions': {str(slot): donor_positions[slot] for slot in PERSISTENT},
            'settled_positions': {str(slot): donor_settled_positions[slot] for slot in PERSISTENT},
            'transient_differences': transient_differences,
            'map_return_modes': [f'{donor_late[0x100]:02X}', f'{native_late[0x100]:02X}']}


def regressions(prefix, parent_prefix):
    routes = [('star1', 'recomp/inputs/demo11-star1-entry.script'),
              ('boss', 'recomp/inputs/demo11-hp-boss-bc.script'),
              ('lifts', 'recomp/inputs/native-sprite9e-room146.script')]
    routes += [(name, 'recomp/inputs/seven-child-existing-'+name+'.script')
               for name in ('0d8', '0e2', '0e3', '0e4')]
    comparisons = []
    for name, script in routes:
        old = ROOT / 'local/captures' / (parent_prefix+'-'+name)
        new = ROOT / 'local/captures' / (prefix+'-'+name)
        validate_capture(old, BASE, script)
        mazo_capture(new, script)
        tags = sorted(path.name.removesuffix('.wram.bin') for path in old.glob('*.wram.bin'))
        require(tags == sorted(path.name.removesuffix('.wram.bin') for path in new.glob('*.wram.bin')),
                'regression dump set differs')
        for tag in tags:
            for suffix, size in SUFFIXES.items():
                filename = tag+'.'+suffix
                a, b = (old / filename).read_bytes(), (new / filename).read_bytes()
                require(a and a == b and (size is None or len(a) == size),
                        'regression differs: '+name+'/'+filename)
                comparisons.append({'route': name, 'file': filename, 'sha256': sha(a)})
    return comparisons


def qualify(args):
    cfg = read(ROOT / 'config/restorations' / (TARGET+'.json'))
    module = read(ROOT / 'config/native-content/mazo-9b-module.json')
    verify((ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes(), cfg['output'],
           'mazo native ROM')
    entry_facts = entry()
    comparisons = regressions(args.prefix, args.parent_prefix)
    report = {'scope': __doc__.strip(), 'target': TARGET, 'rom': cfg['output'],
              'module': {'recipe_sha256': sha((ROOT / 'config/native-content/mazo-9b-module.json').read_bytes()),
                         'adapted_code_sha256': module['code']['adapted_sha256'],
                         'record': module['record'],
                         'packs': packs(TARGET)},
              'donor': {'manifest_sha256': sha((ROOT / 'config/mazo-donor.json').read_bytes()),
                        'rom_sha256': DONOR_ROM},
              'entry': entry_facts, 'regressions': comparisons,
              'scope_note': 'The entry window ends at the first map return. No attack damage, '
                            'fight clear, saved completion or B0 corridor is qualified.',
              'deferred': ['Full mazo 9B attack and damage behavior.',
                           'Transient intro actor trajectories and shared-helper closure.',
                           'B0 corridor namespace conflict with ForestStar.']}
    write_verified(ROOT / args.output, (json.dumps(report, indent=2)+'\n').encode())
    print(args.output, sha((ROOT / args.output).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='mazo-9b-regression-v2')
    parser.add_argument('--parent-prefix', default='mazo-9c-parent')
    parser.add_argument('--output', default='local/reports/native-mazo-9b-final.json')
    qualify(parser.parse_args())
