#!/usr/bin/env python3
"""Qualify assisted 9C orb contact, activation and expiry; not boss damage or clear."""
import argparse
import hashlib
import json
from pathlib import Path

from native_sprite_gap import identity
from restoration_targets import RESTORATIONS
from runtime_patches import patch_plan

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-mazo-gfx282-v1'
SOURCE = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'
TAGS = ['before_contact', 'contact0'] + [f'orb{i:02d}' for i in range(1, 97)]


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def sequence(directory):
    samples = []
    for tag in TAGS:
        path = directory / (tag + '.wram.bin')
        b = path.read_bytes()
        require(len(b) == 0x20000, f'{path}: WRAM size')
        require(len((directory / (tag + '.vram.bin')).read_bytes()) == 0x10000, 'VRAM size')
        require(b[0x100] == 0x14 and int.from_bytes(b[0x10b:0x10d], 'little') == 0x151,
                f'{tag}: room not live 151')
        slots = [i for i in range(12) if b[0x14c8+i] == 8 and b[0x1ab10+i] & 8
                 and b[0x1ab9e+i] == 0x9c and b[0x1504+i] == 5]
        require(len(slots) == 1, f'{tag}: expected one 9C variant 5')
        i = slots[0]
        samples.append(dict(tag=tag, phase=b[0xc2+i], timer=b[0x1570+i],
                            progress=b[0x1602+i], enabled=b[0x1fe00], reaction=b[0x1fe01],
                            freeze=b[0x13fd], lock=b[0x9d],
                            x=b[0xe4+i] | b[0x14e0+i] << 8,
                            y=b[0xd8+i] | b[0x14d4+i] << 8,
                            wram_sha256=digest(path)))
    first, contact = samples[:2]
    require((first['phase'], first['x'], first['y'], first['enabled']) == (0, 168, 272, 0),
            'orb not waiting at world 168/272')
    require(contact['phase'] == 1 and contact['timer'] == 1 and contact['x'] == 120,
            'real contact did not start sequence')
    require([samples[j]['phase'] for j in (2, 11, 15)] == [1, 2, 3], 'cutscene transitions')
    active = [s for s in samples if s['phase'] == 3 and s['enabled'] == 1]
    require(len(active) >= 50 and any(s['progress'] >= 240 for s in active), 'buff duration/progress')
    require(any(s['enabled'] == 0 and s['phase'] == 0 and s['progress'] == 255
                for s in samples[70:]), 'buff expiry and orb reset')
    require(samples[-1]['phase'] == 0 and samples[-1]['enabled'] == 0
            and (samples[-1]['x'], samples[-1]['y']) == (168, 272), 'orb did not respawn')
    return samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', default='mazo-orb-sequence-native-v2')
    parser.add_argument('--source', default='mazo-orb-sequence-source-v3')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report')
    native, source = [ROOT / 'local/captures' / name for name in (args.native, args.source)]
    nr, sr = [read(p / 'receipt.json') for p in (native, source)]
    build = read(ROOT / 'local/build' / TARGET / 'm1-build.json')
    cfg = read(ROOT / 'config/restorations' / (TARGET + '.json'))
    require(nr['stage'] == 'native' and nr['target'] == TARGET, 'native role')
    require(nr['rom_sha256'] == cfg['output']['sha256'] == build['rom_sha256'], 'native ROM')
    require(nr['host_binary_sha256'] == build['binary_sha256'] == digest(
        ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']), 'native binary')
    require(nr['native_content'] == build['native_content'] == identity(TARGET), 'packs/hooks')
    require(nr['runtime_patches'] == build['runtime_patches'] == patch_plan(), 'runtime')
    require(nr['analysis'] == build['analysis'], 'native analysis')
    require(sr['rom_sha256'] == SOURCE == digest(ROOT / 'local/content-versions/mazo/rom.sfc'), 'source ROM')
    require(sr['core_sha256'] == digest(ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so'),
            'source core binary')
    require(sr['frontend_sha256'] == digest(ROOT / 'local/build/snesref/snesref'), 'source frontend')
    require(sr['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'source core options')
    for directory, suffix in ((native, ''), (source, '-donor')):
        script = ROOT / f'recomp/inputs/mazo-9c-orb-sequence{suffix}.script'
        prefix = 'turbo on\n' if directory == native else ''
        require((directory / 'input.script').read_text() == prefix + script.read_text(), 'input identity')
        receipt = nr if directory == native else sr
        require(receipt['route_sha256' if directory == native else 'script_sha256'] == digest(script), 'script pin')
        log = (directory / 'run.log').read_text()
        require(('exit: script quit after' if directory == native else ' quit') in log
                and 'TIMEOUT' not in log and 'dump orb96' in log, 'incomplete capture')
    a, b = sequence(native), sequence(source)
    fields = ('phase', 'timer', 'progress', 'enabled', 'freeze', 'x', 'y')
    equal = sum(all(x[k] == y[k] for k in fields) for x, y in zip(a[:15], b[:15]))
    require(equal == 15, 'contact/cutscene source comparison')
    require(all(a[15][k] == b[15][k] for k in ('phase', 'timer', 'enabled', 'freeze', 'x', 'y')),
            'activation source comparison')
    require(abs(a[15]['progress'] - b[15]['progress']) <= 1, 'activation clock phase')
    report = dict(scope=__doc__, target=TARGET, rom_sha256=nr['rom_sha256'],
                  binary_sha256=nr['host_binary_sha256'], source_rom_sha256=SOURCE,
                  cutscene_pairs=equal, activation_progress_delta=a[15]['progress']-b[15]['progress'],
                  compared_fields=fields,
                  captures={str(p.relative_to(ROOT)): digest(p / 'receipt.json') for p in (native, source)},
                  samples={'native': a, 'source': b},
                  limitations=['Map/pipe entry, player placement and immunity fixtures.',
                               'Later reaction timing differs; no whole-fight parity, damage, music or clear acceptance.',
                               'Candidate descends from r14, not modern-sprites-v2.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: 98 samples per host; {equal} exact contact/cutscene pairs; expiry and respawn on both hosts')


if __name__ == '__main__':
    main()
