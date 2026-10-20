#!/usr/bin/env python3
"""Prepare fresh Star World entrance probes and summarize bounded captures.

Donor probes explicitly select same-number room candidates, not natural donor
map destinations. Correspondence and complete playability require further checks.
"""
import argparse
import hashlib
import json
from pathlib import Path

from play_demo_only1 import ROOT, teleport_script
from prepare_rom import verify
from restore_star_world_1 import lorom, pointer_offset

NODES = (
    ('upper-left', 0x128, 0x168, 0x04, 0x004),
    ('upper-right', 0x1c8, 0x168, 0x02, 0x002),
    ('upper-inner', 0x178, 0x188, 0x07, 0x007),
    ('middle-left', 0x158, 0x1a8, 0x03, 0x003),
    ('center', 0x178, 0x1a8, 0x0a, 0x00a),
    ('middle-right', 0x198, 0x1a8, 0x09, 0x009),
    ('lower-inner', 0x178, 0x1c8, 0x3b, 0x117),
    ('lower-left', 0x128, 0x1e8, 0x05, 0x005),
    ('lower-right', 0x1c8, 0x1e8, 0x08, 0x008),
)


def donor_tile_address(x, y):
    # Map 6's observed 16-column page layout, verified at every selected node.
    return 0xd400 + (y >> 4) * 16 + ((x >> 4) & 15) + (x >> 8) * 0x200


def prepare(directory):
    startup = (ROOT / 'recomp/inputs/m1-route.script').read_text().split('dump map')[0]
    header = '# Bounded entrance survey: disposable uncleared save; map coordinate shortcut.\n'
    tail = 'press y 2\nwait 180\ndump entry180\nwait 420\ndump entry600\nquit\n'
    directory.mkdir(parents=True, exist_ok=True)
    for _, x, y, translevel, _ in NODES:
        key = f'{x:03x}-{y:03x}'
        transfer = teleport_script((6, x, y)) + 'dump selected\n'
        scripts = {
            key: header + startup + transfer + tail,
            'donor-' + key: (header + '# Same-number donor room candidate; not its natural map route.\n' +
                            startup + 'poke 0109 00\n' + transfer +
                            f'poke {donor_tile_address(x, y):x} {translevel:02x}\n' + tail),
        }
        for name, content in scripts.items():
            path = directory / (name + '.script')
            if path.exists() and path.read_text() != content:
                raise ValueError(f'refusing to overwrite a different script: {path}')
            path.write_text(content)
    print(f'Prepared 18 scripts in {directory}')


def graphics(rom, room):
    start = lorom(0x14ad08) + room * 32
    header = rom[start:start+32]
    ids = [int.from_bytes(header[i:i+2], 'little') for i in range(2, 20, 2)]
    missing = [f'{gfx:03X}' for gfx in ids if 0x100 <= gfx <= 0xfff and
               rom[pointer_offset(gfx):pointer_offset(gfx)+3] == b'\xff\xff\xff']
    return {'record': header.hex(), 'selected_ids': [f'{gfx:03X}' for gfx in ids],
            'missing_extended_ids': missing,
            'boundary': 'Only missing $100..$FFF pointers; other resources are not qualified.'}


def summarize(prefix, output):
    versions = {v['id']: v for v in json.loads((ROOT / 'config/content-versions.json').read_text())['versions']}
    roms = {}
    for version in ('demo-only-1', 'cheap-demo'):
        roms[version] = (ROOT / f'local/content-versions/{version}/rom.sfc').read_bytes()
        verify(roms[version], versions[version]['output'], version)
    result = {'scope': __doc__.strip(), 'wait_frames_after_entry': [180, 600], 'nodes': []}
    for name, x, y, translevel, room in NODES:
        key = f'{x:03x}-{y:03x}'
        node = {'name': name, 'map': 6, 'x': x, 'y': y, 'translevel': f'{translevel:02X}',
                'room': f'{room:03X}', 'captures': {},
                'graphics': {version: graphics(rom, room) for version, rom in roms.items()}}
        for host in ('original', 'native', 'donor'):
            directory = ROOT / f'local/captures/{prefix}-{host}-{key}'
            receipt = json.loads((directory / 'receipt.json').read_text())
            version = 'cheap-demo' if host == 'donor' else 'demo-only-1'
            if receipt['rom_sha256'] != hashlib.sha256(roms[version]).hexdigest():
                raise ValueError(f'capture ROM identity differs: {directory}')
            samples = {}
            for tag in ('selected', 'entry180', 'entry600'):
                b = (directory / f'{tag}.wram.bin').read_bytes()
                if len(b) != 0x20000:
                    raise ValueError(f'incomplete WRAM dump: {directory}/{tag}')
                samples[tag] = {
                    'mode': f'{b[0x100]:02X}', 'room': f'{int.from_bytes(b[0x10b:0x10d], "little"):03X}',
                    'translevel': f'{b[0x13bf]:02X}', 'player_x': int.from_bytes(b[0x94:0x96], 'little'),
                    'player_y': int.from_bytes(b[0x96:0x98], 'little'), 'lives_minus_one': b[0xdbe],
                }
                if tag == 'selected' and host != 'donor':
                    if (b[0x100] != 0x0e or b[0x1f11] != 6 or
                            int.from_bytes(b[0x1f17:0x1f19], 'little') != x or
                            int.from_bytes(b[0x1f19:0x1f1b], 'little') != y or
                            b[donor_tile_address(x, y)] != translevel or
                            b[0x1ea2+translevel] & 0x80):
                        raise ValueError(f'not the expected uncleared entrance: {directory}')
                if tag == 'entry180' and samples[tag]['room'] != f'{room:03X}':
                    raise ValueError(f'room mapping differs: {directory}')
            node['captures'][host] = {'path': str(directory.relative_to(ROOT)),
                                      'receipt': receipt, 'samples': samples}
        node['recipient_native_state_samples_match'] = all(
            node['captures']['original']['samples'][tag] == node['captures']['native']['samples'][tag]
            for tag in ('entry180', 'entry600'))
        node['recipient_native_entry_states_match'] = all(
            node['captures']['original']['samples'][tag][field] == node['captures']['native']['samples'][tag][field]
            for tag in ('entry180', 'entry600')
            for field in ('mode', 'room', 'translevel', 'lives_minus_one'))
        result['nodes'].append(node)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Recorded {len(result["nodes"])} entrances in {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'report'])
    parser.add_argument('--scripts', type=Path, default=ROOT / 'local/probes/star-hub-survey')
    parser.add_argument('--capture-prefix', default='hub')
    parser.add_argument('--output', type=Path, default=ROOT / 'local/reports/star-hub-survey.json')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.scripts)
    else:
        if not args.capture_prefix or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.capture_prefix):
            parser.error('capture prefix must contain only letters, digits, hyphens or underscores')
        summarize(args.capture_prefix, args.output)


if __name__ == '__main__':
    main()
