#!/usr/bin/env python3
"""Qualify the room0CB extended graphics 12A recovery.

Rooms 000, 0CB, 100 and 116 select graphics 12A; the recipient slot is empty
while cheap_demo keeps a real stream. The shared donor stream is relocated and
only the pointer is written. Room 0CB's actual entry is NOT established, so this
checks the resource install and a room138 entry regression, not the hidden room's
appearance.
"""
import hashlib, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, pointer_offset
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config/restorations/world1-room0cb-gfx.json').read_text())
    candidate = (ROOT / 'local/restoration/world1-room0cb-gfx/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/world1-room138-sprite/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'world1-room138-sprite base')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')

    asset = cfg['assets'][0]
    gid = int(asset['target_id'], 16)
    slot = pointer_offset(gid)
    require(base[slot:slot + 3] == b'\xff' * 3, 'recipient graphics slot was not empty')
    rooms = []
    for room in range(512):
        header = lorom(0x14ad08) + room * 32
        if int.from_bytes(base[header:header + 2], 'little') & 0x8000:
            if gid in [int.from_bytes(base[header + i:header + i + 2], 'little')
                       for i in range(2, 20, 2)]:
                rooms.append(room)
    require(rooms == asset['rooms'], 'graphics room dependencies differ')
    donor_pointer = int.from_bytes(donor[slot:slot + 3], 'little')
    decoded, compressed = lz2(donor, donor_pointer)
    verify(decoded, asset['decoded'], 'donor decoded graphics')
    verify(compressed, asset['compressed'], 'donor compressed graphics')
    installed = int.from_bytes(candidate[slot:slot + 3], 'little')
    require(lz2(candidate, installed) == (decoded, compressed), 'relocated graphics differ')
    start, size = cfg['allocation']['offset'], cfg['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    count = len(compressed) - 1
    protected = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:start + len(protected) + len(compressed)] == protected + compressed,
            'protected graphics payload differs')
    changed = [i for i, (a, b) in enumerate(zip(base, candidate)) if a != b]
    allowed = set(range(start, start + len(protected) + len(compressed))) | set(range(slot, slot + 3))
    require(set(changed) <= allowed, 'unexpected changes outside the graphics regions')

    build = json.loads((ROOT / 'local/build/world1-room0cb-gfx/m1-build.json').read_text())
    binary = ROOT / 'local/build/world1-room0cb-gfx/BrutalMarioWorld1Room0CbGraphicsSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    script = ROOT / 'recomp/inputs/world1-room138-entry.script'
    captures, states = {}, {}
    for host in ('reference', 'native'):
        directory = ROOT / 'local/captures' / f'world1-0cb-regression-{host}'
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'regression capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                'regression capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'regression binary differs')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'regression route incomplete: ' + host)
        states[host] = {}
        for tag in ('settled', 'walk'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'incomplete WRAM: {host}/{tag}')
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x138, f'wrong room: {host}/{tag}')
            states[host][tag] = body
        captures[directory.name] = receipt
    donor_settled = (ROOT / 'local/captures/world1-138-qualified-cheap/settled.wram.bin').read_bytes()
    cells = 19 * 0x1b0
    for host in ('reference', 'native'):
        for tag in ('settled', 'walk'):
            for base_address in (0xc800, 0x1c800):
                require(states[host][tag][base_address:base_address + cells] ==
                        donor_settled[base_address:base_address + cells],
                        f'room138 terrain regressed: {host}/{tag}')

    report = {
        'scope': __doc__.strip(),
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'donor_rom_sha256': sha(donor),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(changed),
        'graphics': {'id': asset['target_id'], 'rooms': rooms,
                     'decoded_size': asset['decoded']['size'],
                     'compressed_size': asset['compressed']['size'],
                     'allocation_offset': start},
        'verified': ['donor graphics stream location matches the pinned pointer',
                     'relocated stream decompresses to the donor image',
                     'protected RATS payload installed',
                     'only the allocation and pointer slot changed',
                     'room138 entry terrain still matches the donor on both hosts'],
        'captures': captures,
        'limits': ['Room 0CB entry is not established; its rendered appearance is',
                   'therefore NOT verified, only the resource install.',
                   'Rooms 000, 100 and 116 select the same graphics and inherit the fix',
                   'without separate entry checks. Audible output is not claimed.']}
    output = ROOT / 'local/reports/world1-room0cb-gfx-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room0CB graphics checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()