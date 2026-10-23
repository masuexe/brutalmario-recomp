#!/usr/bin/env python3
"""Qualify the Demo 1-1 extended graphics import.

Resolves which extended graphics the Demo 1-1 versions of World 1-1 and the castle
select but demoOnly1 lacks, and installs those streams into empty recipient slots.
No recipient room references them yet, so this target cannot change gameplay; it is
a prerequisite for a later layout migration.
"""
import hashlib, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, pointer_offset
from qualify_world1_next_course import require, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-extra-graphics.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-extra-graphics/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/world1-room0cb-gfx/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/demo-1-1/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'room0cb graphics base')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'demo-1-1'), 'demo 1-1')

    changed, allowed, installed = set(), set(), []
    for asset in cfg['assets']:
        gid = int(asset['target_id'], 16)
        slot = pointer_offset(gid)
        require(base[slot:slot + 3] == b'\xff' * 3, 'recipient slot was not empty: %03X' % gid)
        rooms = []
        for room in range(512):
            header = lorom(0x14ad08) + room * 32
            if int.from_bytes(base[header:header + 2], 'little') & 0x8000:
                if gid in [int.from_bytes(base[header + i:header + i + 2], 'little')
                           for i in range(2, 20, 2)]:
                    rooms.append(room)
        require(rooms == asset['rooms'], 'room dependency differs: %03X' % gid)
        require(rooms == [], 'a recipient room already selects %03X' % gid)
        donor_pointer = int.from_bytes(donor[slot:slot + 3], 'little')
        require(donor_pointer == int(asset['source_address'], 16), 'donor pointer changed: %03X' % gid)
        decoded, compressed = lz2(donor, donor_pointer)
        verify(decoded, asset['decoded'], 'donor decoded graphics')
        verify(compressed, asset['compressed'], 'donor compressed graphics')
        pointer = int.from_bytes(candidate[slot:slot + 3], 'little')
        require(lz2(candidate, pointer) == (decoded, compressed), 'relocated graphics differ: %03X' % gid)
        installed.append({'id': '%03X' % gid, 'compressed': len(compressed),
                          'decoded': len(decoded), 'pointer': '%06X' % pointer})
        allowed |= set(range(slot, slot + 3))
    start = cfg['allocation']['offset']
    cursor = start
    for asset in cfg['assets']:
        compressed = lz2(donor, int(asset['source_address'], 16))[1]
        count = len(compressed) - 1
        block = (b'STAR' + count.to_bytes(2, 'little') +
                 (count ^ 0xffff).to_bytes(2, 'little') + compressed)
        require(candidate[cursor:cursor + len(block)] == block, 'protected payload differs')
        allowed |= set(range(cursor, cursor + len(block)))
        cursor += len(block)
    require(base[start:cursor] == bytes(cursor - start), 'allocation was not empty')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    require(changed <= allowed, 'unexpected changes outside the graphics regions')

    build = json.loads((ROOT / 'local/build/demo11-extra-graphics/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-extra-graphics/BrutalMarioDemo11ExtraGraphicsSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    report = {
        'scope': __doc__.strip(),
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'donor_rom_sha256': sha(donor),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(changed),
        'installed': installed,
        'verified': ['every recipient slot was empty before the import',
                     'no recipient room selects the imported ids',
                     'donor pointers and streams match their pins',
                     'relocated streams decompress to the donor images',
                     'protected RATS payloads installed in the reviewed allocation',
                     'every changed byte lies in the allocation or a pointer slot'],
        'limits': ['The import alone cannot change gameplay because nothing references',
                   'the new ids; consuming them requires a later layout migration.',
                   'No Demo 1-1 level layout, sprite, music or header data is imported.',
                   'Audible output is not claimed.']}
    output = ROOT / 'local/reports/demo11-extra-graphics-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 graphics checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()