#!/usr/bin/env python3
"""Qualify the Demo 1-1 port of the shared extended graphics 12A.

Rooms 000, 007, 0CB, 100 and 116 select graphics 12A while the base lacks the
pointer table entry, so those rooms render from unrelated data. Only the graphics
pointer is written; no room record changes.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, pointer_offset
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
CLEAR_SCRIPT = 'recomp/inputs/world1-room138-clear-save.script'
ROUTE_SCRIPT = 'recomp/inputs/world1-next-course-entry.script'


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-room0cb-gfx.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-room0cb-gfx/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/demo11-room138-audio/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'room138 audio ancestor')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')

    asset = cfg['assets'][0]
    source = int.from_bytes(donor[pointer_offset(int(asset['source_id'], 16)):][:3], 'little')
    require(source == int(asset['source_address'], 16), 'donor graphics pointer changed')
    decoded, compressed = lz2(donor, source)
    verify(decoded, asset['decoded'], 'donor decoded graphics')
    verify(compressed, asset['compressed'], 'donor compressed graphics')
    slot = pointer_offset(0x12A)
    require(base[slot:slot + 3] == b'\xff' * 3, 'graphics slot was occupied on the base')
    installed = int.from_bytes(candidate[slot:slot + 3], 'little')
    require(lz2(candidate, installed) == (decoded, compressed), 'relocated graphics differ')

    selected = []
    for room in range(512):
        header = lorom(0x14AD08) + room * 32
        if int.from_bytes(candidate[header:header + 2], 'little') & 0x8000:
            words = [int.from_bytes(candidate[header + i:header + i + 2], 'little') for i in range(2, 20, 2)]
            if int(asset['target_id'], 16) in words:
                selected.append(room)
    require(selected == asset['rooms'], 'rooms selecting 12A changed: ' + str(selected))

    start, size = cfg['allocation']['offset'], cfg['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    count = len(compressed) - 1
    header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:start + len(header) + len(compressed)] == header + compressed,
            'protected graphics payload differs')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    allowed = set(range(start, start + len(header) + len(compressed))) | set(range(slot, slot + 3))
    require(changed <= allowed, 'unexpected changes outside the graphics region')

    build = json.loads((ROOT / 'local/build/demo11-room0cb-gfx/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-room0cb-gfx/BrutalMarioDemo11Room0CbGraphicsSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    def hashlib_sha(data):
        import hashlib
        return hashlib.sha256(data).hexdigest()

    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'base_rom_sha256': sha(base), 'donor_rom_sha256': sha(donor),
              'binary_sha256': build['binary_sha256'], 'changed_bytes': len(changed),
              'rooms_selecting_12a': selected, 'regressions': {}, 'captures': {}}

    checks = [('d11-0cb-reg-138-ref', CLEAR_SCRIPT, ('goal', 'completed_map')),
              ('d11-0cb-reg-010-ref', ROUTE_SCRIPT, ('ability_land',))]
    for name, script_path, tags in checks:
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'regression capture ROM differs: ' + name)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == hashlib_sha((ROOT / script_path).read_bytes()),
                'regression capture route differs: ' + name)
        report['captures'][name] = receipt
        report['regressions'][name] = {}
        ancestor = 'd11-138-clear-ref' if '138' in name else 'd11-010-route-ref'
        for tag in tags:
            body = (directory / (tag + '.wram.bin')).read_bytes()
            before = (ROOT / 'local/captures' / ancestor / (tag + '.wram.bin')).read_bytes()
            require(body[0x100:0x200] == before[0x100:0x200], f'game state changed in regression: {name}/{tag}')
            report['regressions'][name][tag] = {'mode': body[0x100], 'x': word(body, 0x94),
                                                'y': word(body, 0x96), 'goal': body[0x1493]}

    report['verified'] = ['graphics slot 12A was empty on the base and now points at the payload',
                           'relocated stream decompresses to the donor image',
                           'the rooms selecting 12A are exactly 000, 007, 0CB, 100, 116',
                           'changed bytes stay inside the allocation and the slot',
                           'room 138 clear/save and room 010 route regressions match the ancestor',
                           'game state (WRAM 0x100-0x1FF) is unchanged in both regressions']
    report['not_verified'] = ['Room 0CB entry is not established, so its rendered appearance is',
                              'not compared; the acceptance is structural plus regression.',
                              'Room 007 renders the shared graphics too but is not entered here.']
    report['limits'] = ['Linked dependency only; World 1 as a whole is not qualified on Demo 1-1.']
    output = ROOT / 'local/reports/demo11-room0cb-gfx-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 room0CB graphics checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()