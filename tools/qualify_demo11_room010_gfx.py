#!/usr/bin/env python3
"""Construction check for the Demo 1-1 port of room 010's missing graphics.

Room 010 selects extended graphics 151 (twice) and 102 while the base lacks both
pointer table entries. This target ports only those payloads.

Scope note: unlike room 106's recovery, this fix is NOT visible in the Map16 terrain
buffers - the base, this target and the donor all load the same tiles. The defect is
visual (rendered tileset), and the course additionally stalls in 'Mario Start' until
music 2F is restored, so observable qualification waits for the music descendant.
"""
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lz2, lorom, pointer_offset
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'recomp/inputs/world1-room010-terrain.script'


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-room010-gfx.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-room010-gfx/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/demo11-room106/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/demo8/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'demo 1-1 base line')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'demo8'), 'demo8')

    for asset in cfg['assets']:
        source = int.from_bytes(donor[pointer_offset(int(asset['source_id'], 16)):][:3], 'little')
        require(source == int(asset['source_address'], 16), 'donor pointer changed')
        decoded, compressed = lz2(donor, source)
        verify(decoded, asset['decoded'], 'donor decoded graphics')
        verify(compressed, asset['compressed'], 'donor compressed graphics')
        slot = pointer_offset(int(asset['target_id'], 16))
        require(base[slot:slot + 3] == b'\xff' * 3, 'destination graphics slot was occupied')
        installed = int.from_bytes(candidate[slot:slot + 3], 'little')
        require(lz2(candidate, installed) == (decoded, compressed), 'relocated graphics differ')
        for record_address in asset['record_addresses']:
            record = lorom(int(record_address, 16))
            require(word(candidate, record + asset['record_offset']) == int(asset['target_id'], 16),
                    'record does not select the relocated graphics')
    for record in [{'address': cfg['gfx_record']['address'], 'before': cfg['gfx_record']['before']}] + cfg['additional_gfx_records']:
        offset = lorom(int(record['address'], 16))
        require(base[offset:offset + 32].hex() == record['before'], 'room record changed on the base')
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        before = bytes.fromhex(patch['before'])
        require(base[offset:offset + len(before)] == before, 'patch site differs on the base')
        require(candidate[offset:offset + len(before)] == bytes.fromhex(patch['after']), 'patch not applied')

    start, size = cfg['allocation']['offset'], cfg['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    allowed = set(range(start, start + size))
    for asset in cfg['assets']:
        slot = pointer_offset(int(asset['target_id'], 16))
        allowed |= set(range(slot, slot + 3))
        for record_address in asset['record_addresses']:
            record = lorom(int(record_address, 16))
            allowed |= set(range(record + asset['record_offset'], record + asset['record_offset'] + 2))
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        allowed |= set(range(offset, offset + len(bytes.fromhex(patch['before']))))
    require(changed <= allowed, 'unexpected changes outside the graphics regions')

    build = json.loads((ROOT / 'local/build/demo11-room010-gfx/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-room010-gfx/BrutalMarioDemo11Room010GraphicsSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    script = ROOT / SCRIPT
    facts = {}
    for host, name in (('base', 'd11-010-terrain-base'),
                       ('reference', 'd11-010-terrain-ref'),
                       ('native', 'd11-010-terrain-native'),
                       ('donor', 'd11-010-terrain-donor')):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                'capture route differs: ' + host)
        body = (directory / 'entered.wram.bin').read_bytes()
        require(word(body, 0x10b) == 0x010, 'capture is another room: ' + host)
        facts[host] = {'mode': body[0x100], 'x': word(body, 0x94), 'y': word(body, 0x96)}
        if host in ('reference', 'native'):
            require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
    require(facts['reference']['mode'] == facts['base']['mode'] == 0x12,
            'graphics-only target unexpectedly changed the level mode')
    require(facts['donor'] == {'mode': 0x14, 'x': 0x10, 'y': 0x160},
            'donor capture no longer reaches gameplay')

    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'base_rom_sha256': sha(base), 'donor_rom_sha256': sha(donor),
              'binary_sha256': build['binary_sha256'], 'changed_bytes': len(changed),
              'capture_facts': facts,
              'verified': ['both destination graphics slots were empty on the base',
                           'every room record selects the relocated stream',
                           'relocated streams decompress to the donor images',
                           'changed bytes stay inside the allocation, slots, records and patch site',
                           'the graphics-only target does not change the level mode,',
                           'while the donor capture does reach gameplay'],
              'not_verified': ['Rendered tileset on the Demo 1-1 base (Map16 buffers are',
                               'insensitive to these graphics and the course stalls in',
                               'Mario Start until music 2F is restored).'],
              'limits': ['Intermediate descendant; not a course qualification.',
                         'Music 2F and custom sprite 8D are still missing.',
                         'World 1 as a whole is not qualified on Demo 1-1.']}
    output = ROOT / 'local/reports/demo11-room010-gfx-construction.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 room010 graphics construction checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()