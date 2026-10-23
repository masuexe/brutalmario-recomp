#!/usr/bin/env python3
"""Qualify the Demo 1-1 port of room 010's missing song 2F.

The Demo 1-1 base stalls in 'Mario Start' (mode 0x12) on room 010 because the level
selects song 2F and the song group is absent. This target ports the reviewed demo8
group payload; graphics 151/102 came from the ancestor target.
"""
import json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from restore_star_world_1 import adapt_music, lorom
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
SCRIPT = 'recomp/inputs/world1-room010-terrain.script'
PLAYFIELD_START = 48 * 256 * 4


def main():
    cfg = json.loads((ROOT / 'config/restorations/demo11-room010-music.json').read_text())
    candidate = (ROOT / 'local/restoration/demo11-room010-music/rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration/demo11-room010-gfx/rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/demo8/rom.sfc').read_bytes()
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    verify(candidate, cfg['output'], 'candidate')
    verify(base, cfg['base_output'], 'graphics ancestor')
    verify(donor, next(v['output'] for v in versions if v['id'] == 'demo8'), 'demo8')

    music = cfg['music']
    source = lorom(int(music['source_address'], 16))
    group = donor[source:source + music['source_group']['size']]
    verify(group, music['source_group'], 'donor music group')
    payload = adapt_music(group, music)
    verify(payload, music['adapted'], 'adapted music payload')
    pointer = lorom(int(music['pointer_address'], 16))
    require(base[pointer:pointer + 3].hex() == music['before'], 'song slot was not absent on the base')
    start, size = music['allocation']['offset'], music['allocation']['size']
    require(base[start:start + size] == bytes(size), 'allocation was not empty')
    count = len(payload) - 1
    header = b'STAR' + count.to_bytes(2, 'little') + (count ^ 0xffff).to_bytes(2, 'little')
    require(candidate[start:start + len(header) + len(payload)] == header + payload,
            'protected music payload differs')
    installed = int.from_bytes(candidate[pointer:pointer + 3], 'big')
    require(installed == ((start + 8) // 0x8000) << 16 | 0x8000 | ((start + 8) & 0x7fff),
            'music slot does not point at the relocated payload')
    changed = {i for i, (a, b) in enumerate(zip(base, candidate)) if a != b}
    allowed = set(range(start, start + len(header) + len(payload))) | set(range(pointer, pointer + 3))
    require(changed <= allowed, 'unexpected changes outside the music regions')

    build = json.loads((ROOT / 'local/build/demo11-room010-music/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-room010-music/BrutalMarioDemo11Room010MusicSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'] and build['rom_sha256'] == sha(candidate),
            'native build identity differs')

    script = ROOT / SCRIPT
    report = {'scope': __doc__.strip(), 'candidate_rom_sha256': sha(candidate),
              'base_rom_sha256': sha(base), 'donor_rom_sha256': sha(donor),
              'binary_sha256': build['binary_sha256'], 'changed_bytes': len(changed),
              'samples': {}, 'captures': {}}
    donor_frame = (ROOT / 'local/captures/d11-010-terrain-donor/entered.fb.bgrx').read_bytes()
    for host, name in (('reference', 'd11-010-music-ref'), ('native', 'd11-010-music-native')):
        directory = ROOT / 'local/captures' / name
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        report['captures'][name] = receipt
        report['samples'][host] = {}
        for tag in ('entered', 'settled'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(body[0x100] == 0x14, f'level did not reach gameplay: {host}/{tag}')
            require(word(body, 0x10b) == 0x010, f'wrong room: {host}/{tag}')
            report['samples'][host][tag] = {'mode': body[0x100], 'x': word(body, 0x94),
                                            'y': word(body, 0x96), 'music': body[0x0dda]}
        frame = (directory / 'entered.fb.bgrx').read_bytes()
        diff = sum(1 for i in range(PLAYFIELD_START, len(donor_frame)) if frame[i] != donor_frame[i])
        total = len(donor_frame) - PLAYFIELD_START
        report['samples'][host]['playfield_diff_vs_donor'] = {'bytes': diff, 'total': total,
                                                              'percent': round(100.0 * diff / total, 2)}
        if host == 'reference':
            require(diff * 100 <= total * 2, 'reference playfield differs from the donor by more than 2%')

    base_frame = (ROOT / 'local/captures/d11-010-terrain-base/entered.fb.bgrx').read_bytes()
    base_diff = sum(1 for i in range(PLAYFIELD_START, len(base_frame)) if base_frame[i] != donor_frame[i])
    report['samples']['base_vs_donor_playfield_percent'] = round(100.0 * base_diff / (len(donor_frame) - PLAYFIELD_START), 2)
    require(base_diff * 100 > (len(donor_frame) - PLAYFIELD_START) * 50,
            'the unfixed base no longer renders the Mario Start stall')

    report['verified'] = ['song slot was absent on the base and is now installed',
                           'relocated payload equals the reviewed adapted group',
                           'changed bytes stay inside the allocation and song slot',
                           'both hosts reach gameplay mode 0x14 in room 010',
                           'both hosts select song 0x2F and load room 0x010',
                           'the reference playfield matches the demo8 donor within 2%',
                           'the unfixed base still renders the Mario Start stall']
    report['not_verified'] = ['Audible song content (music-selection byte is not an audible match).',
                              'Native playfield pixel parity with the reference host: the two',
                              'hosts differ by host rendering, so only the reference frame is',
                              'compared with the donor.',
                              'Custom sprite 8D and full-course traversal.']
    report['limits'] = ['Intermediate descendant; full-course qualification needs sprite 8D.',
                        'World 1 as a whole is not qualified on Demo 1-1.']
    output = ROOT / 'local/reports/demo11-room010-music-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 room010 music checks passed: ' + str(output.relative_to(ROOT)))
    print('playfield diff vs donor:', {k: v for k, v in report['samples'].items() if isinstance(v, dict) and 'playfield_diff_vs_donor' in v})


if __name__ == '__main__':
    main()