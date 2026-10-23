#!/usr/bin/env python3
"""Qualify the Demo 1-1 base port of the room 106 graphics recovery.

Both Demo 1-1 and demoOnly1 lack extended graphics 1A2 while room 106 selects it,
so the terrain buffers load as unrelated data and Mario falls. This target ports the
same recovery onto the Demo 1-1 base in an isolated descendant.
"""
import hashlib, json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, lz2, pointer_offset
from qualify_world1_next_course import require, sha, word

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-room106.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-room106/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/demo11-base/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'demo 1-1 base')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')

    asset = cfg['assets'][0]
    decoded, compressed = lz2(donor, int(asset['source_address'], 16))
    verify(decoded, asset['decoded'], 'donor decoded graphics')
    verify(compressed, asset['compressed'], 'donor compressed graphics')
    slot = pointer_offset(int(asset['target_id'], 16))
    require(base[slot:slot + 3] == b'\xff' * 3, 'destination graphics slot was occupied')
    installed = int.from_bytes(candidate[slot:slot + 3], 'little')
    require(lz2(candidate, installed) == (decoded, compressed), 'relocated graphics differ')
    record = lorom(int(cfg['gfx_record']['address'], 16))
    require(base[record:record + 32].hex() == cfg['gfx_record']['before'], 'room record changed on the base')
    require(word(candidate, record + asset['record_offset']) == int(asset['target_id'], 16),
            'room does not select the relocated graphics')
    start, size = cfg['allocation']['offset'], cfg['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    count = len(compressed) - 1
    header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:start + len(header) + len(compressed)] == header + compressed,
            'protected graphics payload differs')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    allowed = (set(range(start, start + len(header) + len(compressed))) |
               set(range(slot, slot + 3)) |
               set(range(record + asset['record_offset'], record + asset['record_offset'] + 2)))
    require(changed <= allowed, 'unexpected changes outside the graphics regions')

    build = json.loads((ROOT / 'local/build/demo11-room106/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-room106/BrutalMarioDemo11Room106SNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    script = ROOT / 'recomp/inputs/world1-room106-entry.script'
    cells = 11 * 0x1b0
    donor_capture = ROOT / 'local/captures/world1-106-qualified-entry-cheap'
    captures, samples = {}, {}
    for host in ('reference', 'native'):
        directory = ROOT / 'local/captures' / ('d11-106-' + ('ref' if host == 'reference' else 'native'))
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        log = (directory / 'run.log').read_bytes()
        require(b'quit' in log and b'timed out' not in log, 'route incomplete: ' + host)
        captures[directory.name] = receipt
        samples[host] = {}
        for tag in ('settled', 'walk', 'jump', 'landed'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            source = (donor_capture / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'incomplete WRAM: {host}/{tag}')
            require(body[0x100] == 0x14 and word(body, 0x10b) == 0x106, f'wrong room: {host}/{tag}')
            for base_address in (0xc800, 0x1c800):
                require(body[base_address:base_address + cells] == source[base_address:base_address + cells],
                        f'Map16 buffer differs from donor: {host}/{tag}/{base_address:x}')
            samples[host][tag] = {'x': word(body, 0x94), 'y': word(body, 0x96)}

    report = {
        'scope': __doc__.strip(),
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'donor_rom_sha256': sha(donor),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': len(changed),
        'samples': samples,
        'captures': captures,
        'verified': ['destination graphics slot was empty on the base',
                     'room record selects the relocated graphics',
                     'relocated stream decompresses to the donor image',
                     'terrain equals the donor over 11 screens on both hosts',
                     'every changed byte lies in the allocation, slot or record word'],
        'limits': ['Entry and movement scope only; complete route, death and save',
                   'behaviour are not re-qualified on this base yet.',
                   'World 1 as a whole is not qualified on Demo 1-1.']}
    output = ROOT / 'local/reports/demo11-room106-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 room106 checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()