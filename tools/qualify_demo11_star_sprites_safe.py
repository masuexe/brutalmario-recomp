#!/usr/bin/env python3
"""Qualify safe sprite allocations, seven node observations and two bounded routes.

The center node still enters room 000, so its entry is a diagnostic limitation.
The coaster route reaches a real tape clear and File A reload. The cap route
uses ordinary input after a map-coordinate shortcut, comparing player progress
with the previously qualified demoOnly1 forest head. Neither is a nine-course pass.
"""
import json
import math
import struct
import wave
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import check_allocation, lorom, make_candidate, sprite_rooms

ROOT = Path(ROOT)
HEAD = 'demo11-star-sprites-safe'
BINARY = 'BrutalMarioDemo11StarSpritesSafeSNESRecomp'


def read_json(path):
    return json.loads(path.read_text())


def capture(name, script, rom, build=None):
    directory = ROOT / 'local/captures' / name
    receipt = read_json(directory / 'receipt.json')
    require(receipt['rom_sha256'] == sha(rom), 'capture ROM differs: ' + name)
    require(receipt['route_sha256'] == sha((ROOT / 'recomp/inputs' / script).read_bytes()),
            'capture script differs: ' + name)
    binary = (ROOT / 'local/build' / HEAD / BINARY if build else
              ROOT / 'local/build/snesref/snesref')
    require(receipt['host_binary_sha256'] == sha(binary.read_bytes()),
            'capture host differs: ' + name)
    if build:
        require(build['rom_sha256'] == sha(rom), 'build ROM differs')
        require(build['binary_sha256'] == receipt['host_binary_sha256'], 'build binary differs')
    log = (directory / 'run.log').read_text()
    require(' quit' in log and 'timeout' not in log.lower() and 'assertion failed' not in log.lower(),
            'script did not complete cleanly: ' + name)
    return directory


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + str(directory / tag))
    info = read_json(directory / (tag + '.info.json'))
    frame = (directory / (tag + '.fb.bgrx')).read_bytes()
    require(len(frame) == info['fb_width'] * info['fb_height'] * 4,
            'incomplete framebuffer: ' + str(directory / tag))
    require((directory / (tag + '.sram.bin')).stat().st_size == 0x8000,
            'incomplete SRAM: ' + str(directory / tag))
    return body


def main():
    cfg = read_json(ROOT / 'config/restorations' / (HEAD + '.json'))
    rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / cfg['base_restoration'] / 'rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'donor')
    verify(rom, cfg['output'], HEAD)
    verify(base, cfg['base_output'], 'intact parent')
    replay, _ = make_candidate(base, donor, cfg)
    require(replay == rom, 'recipe does not reproduce the ROM')
    changed = {i for i, (a, b) in enumerate(zip(base, rom)) if a != b}
    require(changed <= allowed_regions(cfg), 'unexpected byte changes')
    ports = {}
    for sprite in cfg['custom_sprites']:
        source = int(sprite['source_address'], 16)
        dest = int(sprite['destination_address'], 16)
        size = sprite['block']['size']
        check_allocation(base, lorom(dest), size)
        require(source & 0xffff == dest & 0xffff, 'low address changed')
        verify(rom[lorom(dest):lorom(dest)+size], sprite['block'], 'sprite block')
        require(sprite_rooms(base, int(sprite['id'], 16)) == sprite['rooms'],
                'placement dependencies differ')
        record = rom[lorom(int(sprite['destination_record_address'], 16)):][:16]
        expected = bytearray.fromhex(sprite['source_record'])
        for i in (8, 11):
            address = int.from_bytes(record[i:i+3], 'little')
            require(dest + 8 <= address < dest + size, 'entry outside block')
            expected[i+2] = dest >> 16
        require(record == expected, 'installed record differs')
        ports[sprite['id']] = dict(destination=sprite['destination_address'],
                                   rooms=sprite['rooms'])

    # Reproduce the superseded artifact for forensic comparisons, without endorsing it.
    old_cfg = read_json(ROOT / 'config/restorations/demo11-star-sprites.json')
    old = (ROOT / 'local/restoration/demo11-star-sprites/rom.sfc').read_bytes()
    historical, _ = make_candidate(base, donor, old_cfg)
    require(historical == old, 'historical recipe is not reproducible')
    occupied, displaced = [], []
    for sprite in old_cfg['sprite_ports']:
        at = lorom(int(sprite['destination_address'], 16))
        if any(base[at:at+sprite['block']['size']]):
            occupied.append(sprite['sid'])
        rec = bytes.fromhex(sprite['installed_record'])
        dest = int(sprite['destination_address'], 16)
        if any(not dest+8 <= int.from_bytes(rec[i:i+3], 'little') < dest+sprite['block']['size']
               for i in (8, 11)):
            displaced.append(sprite['sid'])
    require(len(occupied) == 7 and displaced == ['24', '37', '30'],
            'historical defect diagnosis changed')

    build = read_json(ROOT / 'local/build' / HEAD / 'm1-build.json')
    nodes = {'cave': (0x004, 0x22), 'snow': (0x008, 0x07),
             'sky': (0x009, 0x28), 'coaster': (0x007, 0x36),
             'caps': (0x117, 0x70), 'upperright': (0x002, 0x77),
             'center': (0x000, 0x00)}
    captures = {}
    for host, suffix in (('reference', 'ref'), ('native', 'native')):
        directory = capture('d11-safe-entries-' + suffix, 'demo11-star-sprites-entry.script',
                            rom, build if host == 'native' else None)
        captures[host] = str(directory.relative_to(ROOT))
        for label, (room, number) in nodes.items():
            for tag in ('entry', 'later'):
                body = state(directory, label + '_' + tag)
                require(body[0x100] == 0x14 and word(body, 0x10B) == room,
                        'wrong node state: %s/%s/%s' % (host, label, tag))
                if label != 'center':
                    require(any(body[0x9E+j] == number and body[0x14C8+j] == 8
                                for j in range(12)), 'expected sprite absent: ' + label)
        goal = capture('d11-safe-ui-goal-' + suffix, 'star-world-upper-inner-goal.script',
                       rom, build if host == 'native' else None)
        cleared = state(goal, 'ow2')
        reloaded = state(goal, 'file_reload')
        require(cleared[0x100] == 0x0E and cleared[0x13CE] == 1 and cleared[0x1EA9] == 0x81,
                'coaster clear missing: ' + host)
        require(reloaded[0x100] == 0x0E and reloaded[0x1EA9] == 0x81,
                'coaster File A reload missing: ' + host)
        for tag in ('ow2', 'file_reload'):
            sram = (goal / (tag + '.sram.bin')).read_bytes()
            require(sram[7] == sram[0x1B4] == 0x81, 'coaster SRAM copies differ')

    predecessor_cfg = read_json(ROOT / 'config/restorations/star-world-forest.json')
    predecessor = (ROOT / 'local/restoration/star-world-forest/rom.sfc').read_bytes()
    verify(predecessor, predecessor_cfg['output'], 'demoOnly1 comparison')
    route = 'star-world-lower-inner-route.script'
    comparison = capture('d11-safe-li-only1-ref', route, predecessor)
    progression = {}
    for host, suffix in (('reference', 'ref'), ('native', 'native')):
        directory = capture('d11-safe-li-route-' + suffix, route, rom,
                            build if host == 'native' else None)
        progression[host] = {}
        for tag in ('y19', 'y25', 'checkpoint', 'jump', 'landed', 'onward'):
            body, expected = state(directory, tag), state(comparison, tag)
            require(body[0x100] == 0x14 and word(body, 0x10B) == 0x117, 'cap route lost level')
            require(all(abs(word(body, a) - word(expected, a)) <= 8 for a in (0x94, 0x96)),
                    'cap route player differs from qualified predecessor: ' + host + '/' + tag)
            progression[host][tag] = [word(body, a) for a in (0x94, 0x96)]
        require(progression[host]['onward'][0] >= 0xD00, 'warp-star progression missing')

    # Confirm that the center-node mapping defect predates this sprite replacement.
    for name, identity in (('d11-safe-center-base-ref', base), ('d11-safe-center-v2-ref', rom)):
        directory = capture(name, 'demo11-star-center-sprites.script', identity)
        require(word(state(directory, 'entered'), 0x10B) == 0,
                'center node mapping changed; revisit the diagnostic')

    ref = ROOT / captures['reference']
    info = read_json(ref / 'upperright_entry.info.json')
    with wave.open(str(ref / 'audio.wav')) as audio:
        audio.setpos(round(info['frame'] / 60.0988118623 * audio.getframerate()))
        raw = audio.readframes(audio.getframerate())
        samples = struct.unpack('<%dh' % (len(raw) // 2), raw)
    rms = math.sqrt(sum(v*v for v in samples) / len(samples))
    require(rms > 100, 'upper-right reference audio is silent')
    report = dict(head=HEAD, rom_sha256=sha(rom), base_sha256=sha(base),
                  binary_sha256=build['binary_sha256'], ports=ports,
                  changed_bytes=len(changed), captures=captures,
                  historical_occupied_blocks=occupied, historical_displaced_entries=displaced,
                  lower_inner_progression=progression, upperright_reference_pcm_rms=rms,
                  verified=['All eleven blocks use checked empty, RATS-safe same-low-address ranges.',
                            'Both entry pointers in every record lie inside its pinned block.',
                            'Six real course entries and the center-node defect repeat on both hosts.',
                            'The coaster reaches a real tape clear, both SRAM copies and File A reload.',
                            'Lower-inner actual-input warp-star progression agrees within 8 px with the demoOnly1 predecessor.',
                            'The historical artifact and the safe head both reproduce exactly.'],
                  limits=['Center node enters room 000 on the intact parent and both safe hosts; no center Boss entry/clear claimed.',
                          'Per-sprite interaction coverage is incomplete, including center sprite 24 and later snow/sky actors.',
                          'Lower-inner full clear, caps, DK, death/re-entry and music correspondence remain open.',
                          'PCM energy is not human listening acceptance; framebuffer equality is not claimed.',
                          'Other course traversals and original World 1 routes have not been rerun on this head.'])
    output = ROOT / 'local/reports/demo11-star-sprites-safe.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Safe Star sprite checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
