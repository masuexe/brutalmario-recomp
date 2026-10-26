#!/usr/bin/env python3
"""Check the bounded donor entry captures; no fight completion is implied."""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import sha, write_verified

ROOT = Path(__file__).resolve().parents[1]


def check_capture(directory, script, identity, expected):
    receipt_path = directory / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['rom_sha256'] != identity:
        raise ValueError('capture ROM identity differs')
    for path in (script, directory / 'input.script'):
        if sha(path.read_bytes()) != receipt['script_sha256']:
            raise ValueError('capture input script identity differs')
    for key, path in (
        ('frontend_sha256', ROOT / 'local/build/snesref/snesref'),
        ('core_sha256', ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so'),
    ):
        if sha(path.read_bytes()) != receipt[key]:
            raise ValueError('capture reference binary identity differs')
    if (receipt['diagnostic_core_override'] is not None or
            receipt['reference_core_options'] != 'snes9x_echo_buffer_hack=enabled'):
        raise ValueError('unexpected reference configuration')
    log = (directory / 'run.log').read_text()
    if ' quit' not in log or '[wav closed:' not in log:
        raise ValueError('capture lacks script completion')
    samples = {}
    for tag, mode, room, custom, minimum in expected:
        path = directory / (tag + '.wram.bin')
        wram = path.read_bytes()
        if len(wram) != 0x20000:
            raise ValueError('WRAM dump size differs')
        if len((directory / (tag + '.vram.bin')).read_bytes()) != 0x10000:
            raise ValueError('VRAM dump size differs')
        actual_room = int.from_bytes(wram[0x10b:0x10d], 'little')
        if (wram[0x100], actual_room) != (mode, room):
            raise ValueError(f'{tag}: wrong game mode/room')
        active = [slot for slot in range(12) if wram[0x14c8+slot] == 8 and
                  wram[0x1ab10+slot] & 8 and
                  wram[0x1ab9e+slot] == custom] if custom is not None else []
        if len(active) < minimum:
            raise ValueError(f'{tag}: expected custom actor is absent')
        samples[tag] = {'mode': f'{mode:02X}', 'room': f'{room:03X}',
                        'custom_slot': f'{custom:02X}' if custom is not None else None,
                        'active_slots': active, 'wram_sha256': sha(wram),
                        'vram_sha256': sha((directory / (tag + '.vram.bin')).read_bytes()),
                        'framebuffer_sha256': sha((directory / (tag + '.fb.bgrx')).read_bytes())}
    return {'capture': str(directory.relative_to(ROOT)),
            'receipt_sha256': sha(receipt_path.read_bytes()),
            'rom_sha256': identity, 'script_sha256': receipt['script_sha256'],
            'frontend_sha256': receipt['frontend_sha256'], 'core_sha256': receipt['core_sha256'],
            'samples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='boss-deps-final')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'local/reports/boss-donor-entry-reviewed.json')
    args = parser.parse_args()
    boss = json.loads((ROOT / 'config/boss-donor.json').read_text())
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    mazo = next(v for v in versions if v['id'] == 'mazo')
    results = []
    for identifier, metadata, script, expected in (
        ('boss', boss, 'seven', [('castle_entry', 0x14, 0x108, None, 0),
                                ('fight180', 0x14, 0xff, 0x2a, 2),
                                ('fight600', 0x14, 0xff, 0x2a, 2),
                                ('fight1200', 0x14, 0xff, 0x2a, 7)]),
        ('mazo', mazo, 'mazo151', [('castle_idle', 0x14, 0x190, 0x9b, 3),
                                 ('fight180', 0x14, 0x151, 0x9c, 2),
                                 ('fight600', 0x0d, 0x151, None, 0),
                                 ('fight1200', 0x0e, 0x151, None, 0)]),
    ):
        rom = ROOT / 'local/content-versions' / identifier / 'rom.sfc'
        verify(rom.read_bytes(), metadata['output'], identifier)
        directory = ROOT / 'local/captures' / f'{args.prefix}-{identifier}-fixture-v1'
        results.append(check_capture(directory,
            ROOT / 'recomp/inputs' / f'boss-dependency-{script}-entry.script',
            metadata['output']['sha256'], expected))
    report = {'scope': __doc__.strip(), 'tool_sha256': sha(Path(__file__).read_bytes()),
              'fixtures': 'Explicit pipe-action room transfer after original donor map entry; '
                          'no imported saves, invulnerability, forced movement or completion writes.',
              'limitations': 'Entry/intro and sampled actor presence only. '
                             'No complete fight, ending, saved clear, audible match or native integration.',
              'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_verified(args.output, (json.dumps(report, indent=2) + '\n').encode())
    print('8 donor samples passed;', args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
