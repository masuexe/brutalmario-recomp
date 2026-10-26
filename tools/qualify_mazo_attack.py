#!/usr/bin/env python3
"""Record the bounded mazo attack windows for rooms 151 and 190.

The fixtures use labelled pipe entry. The 151 window also forces a stationary
Mario after the room load. This check records actor states, motion and timing
differences. It does not prove player damage, a fight clear or a save state.
"""
import argparse
import json
from pathlib import Path

from native_mazo import ROOT, identity, packs
from qualify_native_content import SIZES
from restore_star_world_1 import sha, write_verified

C9 = 'demo11-native-mazo-9c'
C9_ROM = '7d690e9b35493ba49e7f98bb2d63d77ec79ac0c3a78181e4771eb1d6ce012396'
C9_SCRIPT_DONOR = 'recomp/inputs/mazo-9c-align-donor.script'
C9_SCRIPT_NATIVE = 'recomp/inputs/mazo-9c-align-native.script'
B9 = 'demo11-native-mazo-9b'
B9_ROM = '8ab6bd4f5cbfe149aeeb759818ff2eab4d8b6102da698ab86ef1a5e1d375b244'
B9_SCRIPT_DONOR = 'recomp/inputs/mazo-9b-donor-fixture.script'
B9_SCRIPT_NATIVE = 'recomp/inputs/mazo-9b-native-fixture.script'
DONOR_ROM = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'


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


def mario(data):
    return (data[0x94] | (data[0x95] << 8), data[0x96] | (data[0x97] << 8))


def signed(value):
    return value if value < 0x8000 else value-0x10000


def actors(data, custom):
    return {slot: (signed(data[0xe4+slot] | (data[0x14e0+slot] << 8)),
                   signed(data[0xd8+slot] | (data[0x14d4+slot] << 8)))
            for slot in range(12)
            if data[0x14c8+slot] == 8 and data[0x1ab10+slot] & 8
            and data[0x1ab9e+slot] == custom}


def donor_capture(directory, script):
    receipt = read(directory / 'receipt.json')
    require(receipt['rom_sha256'] == DONOR_ROM, 'mazo donor ROM differs')
    require(receipt['script_sha256'] == sha((ROOT / script).read_bytes()),
            'mazo donor script differs')
    require(receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled' and
            receipt['diagnostic_core_override'] is None, 'reference configuration differs')
    log = (directory / 'run.log').read_text()
    require(' quit' in log and '[wav closed:' in log, 'donor capture did not complete')
    return receipt


def native_capture(directory, target, script):
    receipt = read(directory / 'receipt.json')
    cfg = read(ROOT / 'config/restorations' / (target+'.json'))
    build = read(ROOT / 'local/build' / target / 'm1-build.json')
    require(receipt['target'] == target and receipt['stage'] == 'native', 'native role differs')
    require(receipt['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'],
            'native ROM differs')
    require(receipt['host_binary_sha256'] == build['binary_sha256'], 'binary differs')
    require(receipt['native_content'] == build['native_content'] == identity(target),
            'native module identity differs')
    require(receipt['analysis'] == build['analysis'] and
            receipt['runtime_patches'] == build['runtime_patches'], 'build identity differs')
    require(receipt['route_sha256'] == sha((ROOT / script).read_bytes()), 'route differs')
    require((directory / 'input.script').read_text() == 'turbo on\n'+(ROOT / script).read_text(),
            'executed input copy differs')
    log = (directory / 'run.log').read_text()
    require('exit: script quit after' in log and 'TIMEOUT' not in log, 'capture did not complete')
    return receipt, log


def window_9c():
    donor = ROOT / 'local/captures/mazo-9c-align-v2-donor'
    native = ROOT / 'local/captures/mazo-9c-align-v2-native'
    donor_capture(donor, C9_SCRIPT_DONOR)
    _, log = native_capture(native, C9, C9_SCRIPT_NATIVE)
    require('[native-seven] rejected:' not in log, 'native startup was rejected')

    observed = {'samples': []}
    offset = None
    wave_samples = []
    for frame in range(60, 481, 30):
        tag = f'fight{frame:03d}'
        a, b = body(donor, tag), body(native, tag)
        require(a[0x100] == b[0x100] == 0x14, 'aligned room mode differs at '+tag)
        require(room(a) == room(b) == 0x151, 'aligned room number differs at '+tag)
        require(mario(a) == mario(b) == (512, 320), 'aligned Mario state differs at '+tag)
        donor_parts, native_parts = actors(a, 0x9c), actors(b, 0x9c)
        for slot in (7, 9):
            require(donor_parts.get(slot) == native_parts.get(slot),
                    'persistent 9C part differs at '+tag+f' slot {slot}')
        if 6 in donor_parts and 6 in native_parts and frame <= 180:
            wave_samples.append((frame, donor_parts[6][0], native_parts[6][0]))
            wave_offset = native_parts[6][0]-donor_parts[6][0]
            if offset is None:
                offset = wave_offset
            require(wave_offset == offset, 'wave offset differs at '+tag)
        observed['samples'].append({'sample': tag, 'donor_actors': sorted(donor_parts),
                                    'native_actors': sorted(native_parts),
                                    'donor_wave_x': donor_parts.get(6, (None,))[0] if 6 in donor_parts else None,
                                    'native_wave_x': native_parts.get(6, (None,))[0] if 6 in native_parts else None})
    require(len(wave_samples) >= 3, 'wave samples are missing')
    require(offset == 69, 'recorded wave offset differs')
    require([donor_x-native_x for _, donor_x, native_x in wave_samples] == [-69]*len(wave_samples),
            'wave slope differs')

    late_donor = {tag: sorted(actors(body(donor, tag), 0x9c)) for tag in ('fight360', 'fight420', 'fight480')}
    late_native = {tag: sorted(actors(body(native, tag), 0x9c)) for tag in ('fight360', 'fight420', 'fight480')}
    require(late_donor == {'fight360': [6, 7, 9], 'fight420': [6, 7, 9], 'fight480': [6, 7, 9]},
            'donor late attack window differs')
    require(late_native == {'fight360': [7, 9], 'fight420': [6, 7, 9], 'fight480': [4, 5, 6, 7, 9]},
            'native late attack window differs')
    observed['wave'] = {'offset': offset, 'samples': wave_samples}
    observed['late_donor'] = late_donor
    observed['late_native'] = late_native
    return observed


def window_9b():
    donor = ROOT / 'local/captures/mazo-9b-entry-v2-donor'
    native = ROOT / 'local/captures/mazo-9b-entry-v3-native'
    donor_capture(donor, B9_SCRIPT_DONOR)
    native_capture(native, B9, B9_SCRIPT_NATIVE)

    persistent = (6, 7, 9)
    for tag, expected in (('fight150', {6: (96, 208), 7: (120, 120), 9: (128, 8)}),
                          ('fight600', {6: (96, 208), 7: (120, 120), 9: (128, 8)})):
        for directory, label in ((donor, 'donor'), (native, 'native')):
            parts = actors(body(directory, tag), 0x9b)
            require({slot: parts.get(slot) for slot in persistent} == expected,
                    label+' persistent 9B part differs at '+tag)
    require(body(donor, 'fight1200')[0x100] == body(native, 'fight1200')[0x100] == 0x0e,
            '9B map return differs')
    transient = 0
    for frame in range(150, 601, 30):
        tag = f'fight{frame:03d}'
        a, b = actors(body(donor, tag), 0x9b), actors(body(native, tag), 0x9b)
        for slot in range(6):
            if (slot in a) != (slot in b) or (slot in a and a[slot] != b[slot]):
                transient += 1
    require(transient == 58, 'recorded transient 9B difference count differs')
    return {'persistent_positions': {str(slot): expected[slot] for slot in persistent},
            'map_return_mode': '0E', 'transient_differences': transient}


def qualify(args):
    cfg9 = read(ROOT / 'config/restorations' / (C9+'.json'))
    cfg9b = read(ROOT / 'config/restorations' / (B9+'.json'))
    require(cfg9['output']['sha256'] == C9_ROM and cfg9b['output']['sha256'] == B9_ROM,
            'mazo target identities differ')
    c9 = window_9c()
    b9 = window_9b()
    report = {'scope': __doc__.strip(),
              'targets': {C9: {'rom': C9_ROM, 'packs': packs(C9)},
                          B9: {'rom': B9_ROM, 'packs': packs(B9)}},
              'room_151': c9, 'room_190': b9,
              'evidence': [{'directory': str(path.relative_to(ROOT)),
                            'receipt_sha256': sha((path / 'receipt.json').read_bytes())}
                           for path in (ROOT / 'local/captures/mazo-9c-align-v2-donor',
                                        ROOT / 'local/captures/mazo-9c-align-v2-native',
                                        ROOT / 'local/captures/mazo-9b-entry-v2-donor',
                                        ROOT / 'local/captures/mazo-9b-entry-v3-native')],
              'deferred': ['A shared-helper review for the attack actors and the room exit timing.',
                           'A player-damage, fight-clear or saved-completion proof.',
                           'The B0 corridor level-data import.']}
    write_verified(ROOT / args.output, (json.dumps(report, indent=2)+'\n').encode())
    print(args.output, sha((ROOT / args.output).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='local/reports/native-mazo-attack-final.json')
    qualify(parser.parse_args())
