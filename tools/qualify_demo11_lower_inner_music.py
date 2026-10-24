#!/usr/bin/env python3
"""Check the Demo 1-1 lower-inner cap-expiry freeze repair.

Fixture caps initialize in free slot 0 and collide with a positioned player;
subtype selection is explicit. All effect timers expire naturally. This is not
an ordinary route to the cap blocks, a full clear, or new listening acceptance.
"""
import json
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_star_sprites_safe import state
from qualify_world1_next_course import require, sha, word
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom, make_candidate

ROOT = Path(ROOT)
HEAD = 'demo11-lower-inner-music'
BASE = 'demo11-star-sprites-safe'
SCRIPT = 'demo11-star-lower-inner-music.script'


def read_json(path):
    return json.loads(path.read_text())


def capture(name, target, script, native=False):
    directory = ROOT / 'local/captures' / name
    receipt = read_json(directory / 'receipt.json')
    cfg = read_json(ROOT / 'config/restorations' / (target + '.json'))
    require(receipt['rom_sha256'] == cfg['output']['sha256'], 'capture ROM differs: ' + name)
    require(receipt['route_sha256'] == sha((ROOT / 'recomp/inputs' / script).read_bytes()),
            'capture route differs: ' + name)
    binary = (ROOT / 'local/build' / target / RESTORATIONS[target]['binary'] if native else
              ROOT / 'local/build/snesref/snesref')
    require(receipt['host_binary_sha256'] == sha(binary.read_bytes()), 'capture binary differs')
    if native:
        build = read_json(ROOT / 'local/build' / target / 'm1-build.json')
        require(build['rom_sha256'] == receipt['rom_sha256'] and
                build['binary_sha256'] == receipt['host_binary_sha256'], 'build receipt differs')
    log = (directory / 'run.log').read_text().lower()
    require(' quit' in log and 'timeout' not in log and 'assertion failed' not in log,
            'fixture did not finish cleanly: ' + name)
    return directory, receipt


def song(rom, number):
    pointer = lorom(0x0FE000) + number * 3
    offset = lorom(int.from_bytes(rom[pointer:pointer+3], 'big'))
    count = int.from_bytes(rom[offset:offset+2], 'little')
    require(rom[offset+2:offset+4] == bytes.fromhex('0054'), 'unexpected song upload base')
    return rom[offset:offset+count+8], rom[offset+4:offset+count+4]


def main():
    cfg = read_json(ROOT / 'config/restorations' / (HEAD + '.json'))
    rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], HEAD)
    verify(base, cfg['base_output'], BASE)
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'donor')
    rebuilt, _ = make_candidate(base, donor, cfg)
    require(rebuilt == rom, 'recipe does not reproduce the candidate')
    changes = {i for i, (a, b) in enumerate(zip(base, rom)) if a != b}
    expected = {lorom(a) for a in (0x3AB524, 0x3A8085, 0x3A80C6, 0x3A8104,
                                  0x3A83A5, 0x3A8429, 0x3A8469)}
    require(changes == expected and changes <= allowed_regions(cfg), 'change is not exactly seven selection bytes')

    accepted_cfg = read_json(ROOT / 'config/restorations/star-world-lower-inner.json')
    accepted = (ROOT / 'local/restoration/star-world-lower-inner/rom.sfc').read_bytes()
    verify(accepted, accepted_cfg['output'], 'accepted demoOnly1 music target')
    songs = {}
    for number in (0x60, 0x79):
        upload, body = song(rom, number)
        require(upload == song(base, number)[0] == song(accepted, number)[0],
                'song differs from user-confirmed demoOnly1 payload: %02X' % number)
        songs['%02X' % number] = dict(upload_sha256=sha(upload), body_size=len(body))

    baseline, fixed = {}, {}
    for host, suffix in (('reference', 'ref'), ('native', 'native')):
        native = host == 'native'
        directory, receipt = capture('d11-cap-freeze-base-' + suffix, BASE,
                                     'demo11-star-cap-expiry-freeze.script', native)
        active = state(directory, 'invisible_active')
        expired = state(directory, 'invisible_expired')
        later = state(directory, 'invisible_resumed')
        require(active[0x1FFD0] > 0x10, 'baseline cap was not active')
        require(expired[0x1DFB] == 0x21 and expired[0x1FFD0] == 0x10,
                'baseline did not reach the bad expiry request')
        require(expired == later, 'baseline WRAM no longer demonstrates the freeze')
        a = read_json(directory / 'invisible_expired.info.json')['frame']
        b = read_json(directory / 'invisible_resumed.info.json')['frame']
        require(b - a >= 180, 'baseline freeze observation too short')
        baseline[host] = dict(receipt=receipt, frozen_wram_sha256=sha(expired), observation_frames=b-a)

        directory, receipt = capture('d11-cap-music-fixed-' + suffix, HEAD, SCRIPT, native)
        course = state(directory, 'course_music')
        require(course[0x0DDA] == 0x60, 'course selection incorrect')
        effects = {}
        for index, name in enumerate(('invisible', 'metal', 'wing')):
            initialized = state(directory, name + '_initialized')
            active = state(directory, name + '_active')
            expired = state(directory, name + '_expired')
            resumed = state(directory, name + '_resumed')
            require(initialized[0x1504] == index and initialized[0x14C8] == 8,
                    'test cap not initialized: ' + name)
            require(initialized[0x1FFD0:0x1FFD3] == bytes(3), 'fixture starts with active effects')
            require(active[0x1FFD0+index] > 0x10 and
                    all(active[0x1FFD0+i] == 0 for i in range(3) if i != index),
                    'wrong active cap effect: ' + name)
            for body in (active, expired, resumed):
                require(body[0x100] == 0x14 and word(body, 0x10B) == 0x117 and
                        body[0x0DDA] == 0x60 and body[0x1DFB] == 0 and body[0x0DBE] == 4,
                        'level/music/life state incorrect: ' + host + '/' + name)
            require(expired[0x1FFD0:0x1FFD3] == resumed[0x1FFD0:0x1FFD3] == bytes(3),
                    'effect did not expire naturally')
            require(expired != resumed and expired[0x14] != resumed[0x14],
                    'guest no longer advances after expiry')
            effects[name] = dict(active_timer=active[0x1FFD0+index], expired_timers=[0, 0, 0],
                                 frame_counter_after=[expired[0x14], resumed[0x14]])
        fixed[host] = dict(receipt=receipt, effects=effects)

        route, route_receipt = capture('d11-cap-music-route-' + suffix, HEAD,
                                       'star-world-lower-inner-route.script', native)
        old_route, _ = capture('d11-safe-li-route-' + suffix, BASE,
                               'star-world-lower-inner-route.script', native)
        for tag in ('y19', 'y25', 'checkpoint', 'jump', 'landed', 'onward'):
            body, old = state(route, tag), state(old_route, tag)
            require(body[0x100] == 0x14 and word(body, 0x10B) == 0x117 and
                    all(abs(word(body, a) - word(old, a)) <= 8 for a in (0x94, 0x96)),
                    'warp-star regression diverges: ' + host + '/' + tag)
        require(word(state(route, 'onward'), 0x94) >= 0xD00, 'warp-star progression missing')
        fixed[host]['route_receipt'] = route_receipt

    directory = ROOT / 'local/captures/d11-cap-music-fixed-ref'
    events = [json.loads(line) for line in (directory / 'wram.jsonl').read_text().splitlines()]
    selected = [e for e in events if e['adr'] == '0x01dfb' and e['val'] in ('0x60', '0x79')]
    require([e['val'] for e in selected] == ['0x60', '0x79', '0x60', '0x79', '0x60', '0x79', '0x60'],
            'course/pickup/expiry request sequence differs')
    aram_checks = []
    for name, script, number in (('d11-cap-music-active-native', 'demo11-star-cap-active.script', 0x79),
                                ('d11-cap-music-fixed-native', SCRIPT, 0x60)):
        directory, receipt = capture(name, HEAD, script, True)
        aram = (directory / 'apu-ram.bin').read_bytes()
        body = song(rom, number)[1]
        require(len(aram) == 65536 and aram[0x5400:0x5400+len(body)] == body,
                'actual SPC song payload differs: ' + name)
        aram_checks.append(dict(capture=name, receipt=receipt, song='%02X' % number,
                                matched_bytes=len(body), aram_sha256=sha(aram)))

    report = dict(scope=__doc__.strip(), target=HEAD, rom_sha256=sha(rom), base_sha256=sha(base),
                  changed_bytes=len(changes), songs=songs, baseline=baseline, fixed=fixed,
                  reference_music_requests=selected, actual_native_aram=aram_checks,
                  limits=['Initialized-cap collision fixtures qualify pickup and natural expiry, not traversal to cap blocks.',
                          'Warp-star regression is a segment, not a full 100-coin clear.',
                          'No new listening acceptance claimed; song payloads match the previously accepted correction exactly.',
                          'Center entry and other restoration work remain open.'])
    output = ROOT / 'local/reports/demo11-lower-inner-music.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Lower-inner cap-expiry/music checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
