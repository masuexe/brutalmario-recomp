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
C9_SCRIPT_DONOR = 'recomp/inputs/mazo-9c-align-fine-donor.script'
C9_SCRIPT_NATIVE = 'recomp/inputs/mazo-9c-align-fine-native.script'
LOAD_SCRIPT_DONOR = 'recomp/inputs/mazo-9c-load-donor.script'
LOAD_SCRIPT_NATIVE = 'recomp/inputs/mazo-9c-load-native.script'
LATE_SCRIPT_DONOR = 'recomp/inputs/mazo-9c-late-donor.script'
LATE_SCRIPT_NATIVE = 'recomp/inputs/mazo-9c-late-native.script'
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


def wave_x(data):
    if data[0x14c8+6] == 8 and data[0x1ab10+6] & 8 and data[0x1ab9e+6] == 0x9c:
        return signed(data[0xe4+6] | (data[0x14e0+6] << 8))
    return None


def onset(directory):
    gameplay = room_first = wave = wave_x = None
    for frame in range(1, 221):
        data = body(directory, f't{frame:03d}')
        if room_first is None and room(data) == 0x151:
            room_first = frame
        if gameplay is None and data[0x100] == 0x14:
            gameplay = frame
        value = wave_x_of(data)
        if wave is None and value is not None:
            wave, wave_x = frame, value
    return {'room_first': room_first, 'gameplay': gameplay, 'wave': wave, 'wave_x': wave_x}


def wave_x_of(data):
    if data[0x14c8+6] == 8 and data[0x1ab10+6] & 8 and data[0x1ab9e+6] == 0x9c:
        return signed(data[0xe4+6] | (data[0x14e0+6] << 8))
    return None


def load_timing():
    donor = ROOT / 'local/captures/mazo-9c-load-v2-donor'
    native = ROOT / 'local/captures/mazo-9c-load-v2-native'
    donor_capture(donor, LOAD_SCRIPT_DONOR)
    native_capture(native, C9, LOAD_SCRIPT_NATIVE)
    d, n = onset(donor), onset(native)
    require(d == {'room_first': 31, 'gameplay': 141, 'wave': 193, 'wave_x': 285},
            'donor load timing differs')
    require(n == {'room_first': 39, 'gameplay': 161, 'wave': 216, 'wave_x': 285},
            'native load timing differs')
    require(n['room_first']-d['room_first'] == 8, 'recorded room onset delta differs')
    require(n['gameplay']-d['gameplay'] == 20, 'recorded gameplay onset delta differs')
    require(n['wave']-d['wave'] == 23, 'recorded wave onset delta differs')
    require(n['wave']-n['gameplay'] == 55 and d['wave']-d['gameplay'] == 52,
            'recorded wave delay differs')
    return {'donor': d, 'native': n,
            'deltas': {'room_first': 8, 'gameplay': 20, 'wave': 23},
            'wave_delay_after_gameplay': {'donor': 52, 'native': 55},
            'scope': 'The wave onset follows the host load and gameplay onset. Most of the '
                     '23-frame offset follows the 20-frame gameplay onset delta. A three-frame '
                     'residual stays open.'}


def window_9c_late():
    donor = ROOT / 'local/captures/mazo-9c-late-v1-donor'
    native = ROOT / 'local/captures/mazo-9c-late-v1-native'
    donor_capture(donor, LATE_SCRIPT_DONOR)
    native_capture(native, C9, LATE_SCRIPT_NATIVE)

    tags = ['late400']+[f'late{frame:03d}' for frame in range(405, 661, 5)]
    donor_rows, native_rows = {}, {}
    for tag in tags:
        a, b = body(donor, tag), body(native, tag)
        require(a[0x100] == b[0x100] == 0x14, 'later window mode differs at '+tag)
        donor_rows[tag], native_rows[tag] = actors(a, 0x9c), actors(b, 0x9c)

    for tag in tags:
        parts = donor_rows[tag]
        require(parts.get(6) == (144, 320), 'donor later slot 6 differs at '+tag)
        require(all(body(donor, tag)[0xb6+slot] == 0 for slot in parts),
                'donor later actor has speed at '+tag)
    require(donor_rows['late400'] == {6: (144, 320), 7: (168, 272), 9: (144, 320)},
            'donor later start set differs')
    require(native_rows['late400'] == {7: (168, 272), 9: (144, 320)},
            'native later start set differs')

    def x_at(tag, slot):
        return native_rows[tag].get(slot, (None, None))[0]

    require(x_at('late410', 6) == 268 and x_at('late480', 6) == -12,
            'native slot 6 later motion differs')
    require(x_at('late445', 5) == 256 and x_at('late470', 5) == 156,
            'native slot 5 later motion differs')
    require(x_at('late475', 4) == 264 and x_at('late540', 4) == 4,
            'native slot 4 later motion differs')
    speeds = {body(native, tag)[0xb6+slot] for tag in tags for slot in (4, 5, 6)
              if slot in native_rows[tag]}
    require(speeds == {192}, 'native later wave speed differs')
    return {'donor': 'One stationary slot 6 part at (144,320) with zero speed through the window. '
                     'Slots 7 and 9 stay fixed.',
            'native': 'Repeating left-moving waves in slots 6, 5 and 4 with speed 192. '
                      'Slot 6: X 268 at late410 and -12 at late480. Slot 5: X 256 at late445. '
                      'Slot 4: X 264 at late475.',
            'donor_rows': {tag: {str(k): list(v) for k, v in donor_rows[tag].items()}
                           for tag in ('late400', 'late480', 'late600', 'late660')},
            'native_rows': {tag: {str(k): list(v) for k, v in native_rows[tag].items()}
                            for tag in ('late410', 'late480', 'late540', 'late600')}}


def window_9c():
    donor = ROOT / 'local/captures/mazo-9c-align-fine-v2-donor'
    native = ROOT / 'local/captures/mazo-9c-align-fine-v2-native'
    donor_capture(donor, C9_SCRIPT_DONOR)
    _, log = native_capture(native, C9, C9_SCRIPT_NATIVE)
    require('[native-seven] rejected:' not in log, 'native startup was rejected')

    observed = {'samples': []}
    for frame in range(60, 201, 5):
        tag = f'fight{frame:03d}'
        a, b = body(donor, tag), body(native, tag)
        if a[0x100] != 0x14 or b[0x100] != 0x14:
            observed['samples'].append({'sample': tag, 'mode': [f'{a[0x100]:02X}', f'{b[0x100]:02X}']})
            continue
        require(room(a) == room(b) == 0x151, 'aligned room number differs at '+tag)
        require(mario(a) == mario(b) == (512, 320), 'aligned Mario state differs at '+tag)
        donor_parts, native_parts = actors(a, 0x9c), actors(b, 0x9c)
        for slot in (7, 9):
            require(donor_parts.get(slot) == native_parts.get(slot),
                    'persistent 9C part differs at '+tag+f' slot {slot}')
        observed['samples'].append({'sample': tag, 'donor_wave_x': wave_x(a),
                                    'native_wave_x': wave_x(b)})

    require(body(donor, 'fight120')[0x100] == body(native, 'fight120')[0x100] == 0x14,
            'aligned gameplay mode is absent at fight120')
    # The first wave moves -3 pixels per frame in both hosts. The intercept
    # x+3*t records the wave phase. A 69-pixel difference equals 23 frames.
    frames = list(range(125, 201, 5)) + [240]
    donor_phase = {wave_x(body(donor, f'fight{frame:03d}'))+3*frame
                   for frame in frames
                   if wave_x(body(donor, f'fight{frame:03d}')) is not None}
    frames = list(range(145, 201, 5)) + [240]
    native_phase = {wave_x(body(native, f'fight{frame:03d}'))+3*frame
                    for frame in frames
                    if wave_x(body(native, f'fight{frame:03d}')) is not None}
    require(donor_phase == {651}, 'donor first wave phase differs')
    require(native_phase == {720}, 'native first wave phase differs')
    require(wave_x(body(donor, 'fight125')) == 276 and wave_x(body(native, 'fight145')) == 285,
            'first wave entry sample differs')
    require(wave_x(body(donor, 'fight240')) == -69 and wave_x(body(native, 'fight240')) == 0,
            'first wave exit sample differs')
    require((720-651) // 3 == 23, 'recorded wave phase offset differs')

    later = {}
    for label, directory in (('donor', donor), ('native', native)):
        later[label] = {tag: wave_x(body(directory, tag))
                        for tag in ('fight420', 'fight450', 'fight480', 'fight540', 'fight600')}
    require(later['donor'] == {'fight420': 144, 'fight450': 144, 'fight480': 144,
                               'fight540': 144, 'fight600': 144},
            'donor later attack cycle differs')
    require(later['native'] == {'fight420': None, 'fight450': None, 'fight480': 208,
                                'fight540': -32, 'fight600': 112},
            'native later attack cycle differs')

    observed['first_wave'] = {'donor_phase': 651, 'native_phase': 720,
                              'speed_pixels_per_frame': 3, 'phase_offset_frames': 23,
                              'donor_first_sample': 125, 'native_first_sample': 145}
    observed['later_cycles'] = later
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
    load = load_timing()
    late = window_9c_late()
    report = {'scope': __doc__.strip(),
              'targets': {C9: {'rom': C9_ROM, 'packs': packs(C9)},
                          B9: {'rom': B9_ROM, 'packs': packs(B9)}},
              'room_151': c9, 'load_timing': load, 'room_151_late': late,
              'room_190': b9,
              'evidence': [{'directory': str(path.relative_to(ROOT)),
                            'receipt_sha256': sha((path / 'receipt.json').read_bytes())}
                           for path in (ROOT / 'local/captures/mazo-9c-align-fine-v2-donor',
                                        ROOT / 'local/captures/mazo-9c-align-fine-v2-native',
                                        ROOT / 'local/captures/mazo-9c-load-v2-donor',
                                        ROOT / 'local/captures/mazo-9c-load-v2-native',
                                        ROOT / 'local/captures/mazo-9c-late-v1-donor',
                                        ROOT / 'local/captures/mazo-9c-late-v1-native',
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
