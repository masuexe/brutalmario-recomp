#!/usr/bin/env python3
"""Check the exact map-node scope of the Demo 1-1 BGM dispatch.

The accepted demo11-room106-music patch compared only the 8-bit low byte of the
persistent map-node X word ($1F17). The Star World middle-left node (X=$0158)
therefore also selected slot 0x33 and hid the forest donor track 0x5D. This
descendant target relocates the dispatch to a private shim that compares the
full word against #$0058. The room106 node keeps slot 0x33; every other node
passes its original $0DDA request. Both hosts are checked.
"""
import json

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, make_candidate

ROOT = Path = __import__('pathlib').Path(ROOT)
HEAD = 'demo11-node-music'
BASE = 'demo11-star-forest'
FOREST_SCRIPT = 'star-world-forest-entry.script'
BOTH_SCRIPT = 'demo11-room106-music-both.script'
PATCH = '00972B'
PATCH_BEFORE = 'ac171fc058d006a933eaeaeaea'
SHIM = bytes.fromhex('c220ad171fc95800e220f007adda0d5c389700a9335c389700')
SHIM_ADDRESS = 0x49EA00
FOREST_TRACK = 0x5D
ROOM106_TRACK = 0x33
ROOM120_TRACK = 0x49
APPLICATION_BASE = 0x5400


def read_json(path):
    return json.loads(path.read_text())


def song(rom, number):
    pointer = lorom(0x0FE000) + number * 3
    address = int.from_bytes(rom[pointer:pointer + 3], 'big')
    if address == 0:
        return None
    offset = lorom(address)
    count = int.from_bytes(rom[offset:offset + 2], 'little')
    if rom[offset + 2:offset + 4] != APPLICATION_BASE.to_bytes(2, 'little'):
        return None
    return rom[offset + 4:offset + 4 + count]


def music_requests(capture):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2300 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def summary(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94), y=word(body, 0x96),
                water=body[0x85], music=body[0x0DDA])


def verify_recipe():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    final = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = read_json(ROOT / 'config/restorations' / (HEAD + '.json'))
    verify(base, cfg['base_output'], 'intact parent')
    verify(final, cfg['output'], HEAD)
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    pins = {version['id']: version['output'] for version in versions}
    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    verify(donor, pins[cfg['donor']], cfg['donor'])
    replay, _ = make_candidate(base, donor, cfg)
    require(replay == final, 'recipe does not reproduce the candidate')
    changed = {i for i, (a, b) in enumerate(zip(base, final)) if a != b}
    require(changed <= allowed_regions(cfg), 'unexpected byte outside the reviewed regions')
    require(len(changed) == 38, 'change is not the reviewed patch plus shim: %d' % len(changed))

    patch = lorom(int(PATCH, 16))
    require(base[patch:patch + 13].hex() == PATCH_BEFORE, 'parent dispatch bytes differ')
    require(final[patch:patch + 13].hex() ==
            '5c08ea49' + 'ea' * 9, 'relocated dispatch jump differs')
    header = lorom(SHIM_ADDRESS)
    require(final[header:header + 4] == b'STAR', 'shim block header missing')
    count = int.from_bytes(final[header + 4:header + 6], 'little')
    require(count == len(SHIM) - 1 and
            int.from_bytes(final[header + 6:header + 8], 'little') == count ^ 0xFFFF,
            'shim block header fields differ')
    require(base[header:header + 8 + len(SHIM)] == bytes(8 + len(SHIM)),
            'parent shim range is not empty')
    require(final[header + 8:header + 8 + len(SHIM)] == SHIM, 'shim payload differs')
    return base, final, cfg


def check_forest_host(host, native):
    directory, receipt = capture('d11-node-music-forest-' + host, HEAD, FOREST_SCRIPT, native)
    states = {tag: summary(directory, tag) for tag in
              ('entry180', 'entry600', 'entry1200', 'movement')}
    for tag in ('entry180', 'entry600', 'entry1200'):
        body = states[tag]
        require(body['mode'] == 0x14 and body['room'] == 3 and body['x'] == 112 and
                body['y'] == 352 and body['water'] == 0, 'forest entry changed: ' + host + '/' + tag)
        require(body['music'] == FOREST_TRACK, 'forest node did not select the donor track: ' + host)
    require(states['movement']['x'] == 137 and abs(states['movement']['y'] - 337) <= 2,
            'forest movement changed: ' + host)
    if native:
        aram = (directory / 'apu-ram.bin').read_bytes()
        body = song(final_rom, FOREST_TRACK)
        require(body and aram[APPLICATION_BASE:APPLICATION_BASE + len(body)] == body,
                'native does not play the restored forest track: ' + host)
    else:
        requests = music_requests(directory.name)
        require(requests and requests[-1] == FOREST_TRACK and ROOM106_TRACK not in requests,
                'reference music requests differ: ' + str(requests))
    return directory.name, receipt, states


def check_both_host(host, native):
    directory, receipt = capture('d11-node-music-both-' + host, HEAD, BOTH_SCRIPT, native)
    room106, room120 = summary(directory, 'room106_settled'), summary(directory, 'room120_settled')
    require(room106['mode'] == 0x14 and room106['room'] == 0x0106 and
            room106['music'] == ROOM106_TRACK, 'room106 node lost slot 0x33: ' + host)
    require(room120['mode'] == 0x14 and room120['room'] == 0x0120 and
            room120['music'] == ROOM120_TRACK, 'room120 node lost slot 0x49: ' + host)
    return directory.name, receipt, dict(room106=room106, room120=room120)


def main():
    global final_rom
    base, final, cfg = verify_recipe()
    final_rom = final
    captures, results = {}, {}
    for host, native in (('ref', False), ('native', True)):
        name, receipt, states = check_forest_host(host, native)
        captures[name] = receipt
        results['forest_' + host] = states
        name, receipt, states = check_both_host(host, native)
        captures[name] = receipt
        results['both_' + host] = states

    previous = ROOT / 'local/captures/d11-forest-entry-ref'
    for tag in ('entry180', 'entry1200'):
        old = summary(previous, tag)
        new = results['forest_ref'][tag]
        require(old['music'] == ROOM106_TRACK, 'previous forest capture did not show the leak')
        skipped = {key for key in old if key != 'music' and old[key] != new[key]}
        require(not skipped, 'forest state changed outside music: ' + str(skipped))

    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11NodeMusicSNESRecomp'
    build = read_json(ROOT / 'local/build' / HEAD / 'm1-build.json')
    require(build['rom_sha256'] == sha(final) and build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')

    report = dict(scope=__doc__.strip(), target=HEAD, base_target=BASE,
                  rom_sha256=sha(final), base_sha256=sha(base), binary_sha256=build['binary_sha256'],
                  changed_bytes_from_base=38,
                  dispatch=dict(patch=PATCH, before=PATCH_BEFORE,
                                after=final[lorom(int(PATCH, 16)):lorom(int(PATCH, 16)) + 13].hex(),
                                shim_address='%06X' % SHIM_ADDRESS, shim=SHIM.hex()),
                  captures=captures, results=results,
                  limits=['The test enters nodes through explicit map teleports; it qualifies the dispatch boundary, not ordinary overworld travel.',
                          'The room106 slot 0x33 choice remains the user-auditioned decision recorded in the room106 music report.',
                          'Other courses keep their existing requests; this check covers the forest node and the two room106/room120 nodes.'])
    output = ROOT / 'local/reports/demo11-node-music.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Node-scoped music dispatch checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
