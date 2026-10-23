#!/usr/bin/env python3
"""Qualify the Demo 1-1 port of room 138's audio dependency.

Room 138's header requests global song 21, which both builds lack, so the level
stalls in 'Mario Start'. This target imports donor private song 7E, retargets the
header byte from 21 to 7E and lets private 7E inherit sample bank 2.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from restore_star_world_1 import adapt_music, lorom
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
ENTRY_SCRIPT = 'recomp/inputs/world1-room138-entry.script'
CLEAR_SCRIPT = 'recomp/inputs/world1-room138-clear-save.script'


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-room138-audio.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-room138-audio/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/demo11-room010-music/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'audio ancestor')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'cheap_demo')

    music = cfg['music']
    source = lorom(int(music['source_address'], 16))
    group = donor[source:source + music['source_group']['size']]
    verify(group, music['source_group'], 'donor music group')
    payload = adapt_music(group, music)
    verify(payload, music['adapted'], 'adapted music payload')
    pointer = lorom(int(music['pointer_address'], 16))
    require(base[pointer:pointer + 3].hex() == music['before'], 'private song slot was not absent on the base')
    start, size = music['allocation']['offset'], music['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    count = len(payload) - 1
    header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:start + len(header) + len(payload)] == header + payload,
            'protected music payload differs')
    installed = int.from_bytes(candidate[pointer:pointer + 3], 'big')
    require(installed == ((start + 8) // 0x8000) << 16 | 0x8000 | ((start + 8) & 0x7fff),
            'song slot does not point at the relocated payload')
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        before = bytes.fromhex(patch['before'])
        require(base[offset:offset + len(before)] == before, 'patch site differs on the base')
        require(candidate[offset:offset + len(before)] == bytes.fromhex(patch['after']), 'patch not applied')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    allowed = set(range(start, start + len(header) + len(payload))) | set(range(pointer, pointer + 3))
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        allowed |= set(range(offset, offset + 1))
    require(changed <= allowed, 'unexpected changes outside the music regions')

    build = json.loads((ROOT / 'local/build/demo11-room138-audio/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-room138-audio/BrutalMarioDemo11Room138AudioSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    entry_script = (ROOT / ENTRY_SCRIPT).read_bytes()
    clear_script = (ROOT / CLEAR_SCRIPT).read_bytes()
    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'base_rom_sha256': sha(base), 'donor_rom_sha256': sha(donor),
              'binary_sha256': build['binary_sha256'], 'changed_bytes': len(changed),
              'entry': {}, 'clear_route': {}, 'captures': {}}

    def receipt(name, script_bytes, candidate_rom):
        directory = ROOT / 'local/captures' / name
        data = json.loads((directory / 'receipt.json').read_text())
        require(data.get('route_sha256', data.get('script_sha256')) == hashlib_sha(script_bytes),
                'capture route differs: ' + name)
        if candidate_rom:
            require(data['rom_sha256'] == candidate_rom, 'capture ROM differs: ' + name)
        report['captures'][name] = data
        return directory

    def hashlib_sha(data):
        import hashlib
        return hashlib.sha256(data).hexdigest()

    for name, rom_sha in (('d11-138-clear-ref', sha(candidate)), ('d11-138-clear-native', sha(candidate))):
        directory = receipt(name, clear_script, rom_sha)
        if name.endswith('native'):
            require(report['captures'][name]['host_binary_sha256'] == build['binary_sha256'],
                    'clear-route capture binary differs')
        samples = {}
        for tag in ('entry180', 'goal', 'completed_map', 'castle_entry', 'reload_course', 'settled'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, f'incomplete WRAM: {name}/{tag}')
            samples[tag] = {'mode': body[0x100], 'room': word(body, 0x10b), 'x': word(body, 0x94),
                            'y': word(body, 0x96), 'goal': body[0x1493]}
        require(samples['entry180']['mode'] == 0x14 and samples['entry180']['room'] == 0x138,
                'entry did not reach room 138 gameplay: ' + name)
        require(samples['goal']['goal'] == 0xF0, 'goal tape not touched: ' + name)
        require(samples['completed_map']['mode'] == 0x0E, 'no map return after the goal: ' + name)
        require(samples['castle_entry']['room'] == 0x10E, 'castle route changed: ' + name)
        report['clear_route'][name] = samples

    base_directory = ROOT / 'local/captures/d11-138-demo11-base'
    base_receipt = json.loads((base_directory / 'receipt.json').read_text())
    require(base_receipt.get('route_sha256', base_receipt.get('script_sha256')) == hashlib_sha(entry_script),
            'base entry capture route differs')
    base_body = (base_directory / 'entry180.wram.bin').read_bytes()
    report['base_stall'] = {'mode': base_body[0x100], 'room': word(base_body, 0x10b),
                            'music': base_body[0x0dda]}
    require(report['base_stall']['mode'] == 0x12 and report['base_stall']['music'] == 0x21,
            'unfixed base no longer shows the room138 music stall')

    for name in ('d11-138-demo11-room138-audio',):
        directory = receipt(name, entry_script, sha(candidate))
        body = (directory / 'entry600.wram.bin').read_bytes()
        report['entry'][name] = {'mode': body[0x100], 'room': word(body, 0x10b), 'music': body[0x0dda]}
        require(body[0x100] == 0x14 and word(body, 0x10b) == 0x138 and body[0x0dda] == 0x7E,
                'ported target did not reach room138 with private song 7E')

    report['verified'] = ['private song 7E slot was absent on the base and is now installed',
                           'relocated payload equals the reviewed adapted group',
                           'both reviewed patches applied at their pinned sites',
                           'changed bytes stay inside the allocation, song slot and patches',
                           'the unfixed base still stalls in mode 0x12 requesting song 0x21',
                           'the ported target reaches gameplay with private song 0x7E',
                           'the clear/save route passes on reference and native: goal 0xF0,',
                           'map return, castle node, course reload and settled state']
    report['not_verified'] = ['Audible song content.',
                              'Custom sprite 0B is not ported: Demo 1-1 spawns its own 0x0B',
                              'sprite (status 0x08 during the route) and the course clears, so',
                              'only a user playtest can judge its visual fidelity.']
    report['limits'] = ['Room 138 scope only; World 1 as a whole is not qualified on Demo 1-1.']
    output = ROOT / 'local/reports/demo11-room138-audio-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 room138 audio checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()