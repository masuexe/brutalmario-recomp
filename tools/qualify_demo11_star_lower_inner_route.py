#!/usr/bin/env python3
"""Qualify the Star World lower-inner Valley Star routes on the Demo 1-1 line.

The tracked lower-inner scripts cover the cap course on the current head: a
real-input traversal past the former wall and through the warp-star chain, the
real 100-coin controller ending with its save and reload, and a real
pit/death/re-entry. Reference and native runs must match fresh demoOnly1-line
captures under the same scripts.

The wiki describes the Valley Star as a Super Mario 64 cap course whose secret
key exit follows a 100-coin collection. The coin route uses Start pauses and
player placement fixtures; the pickups, rollover, extra life, ending, save and
reload are guest actions.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-lower-inner'
ROUTES = {
    'route': 'star-world-lower-inner-route.script',
    'goal': 'star-world-lower-inner-goal.script',
    'death': 'star-world-lower-inner-death.script',
}
COINS = 0x0DBF
HUB_FLAG = 0x1EDD
GOAL_TIMER = 0x1493
GOAL_ACTIVE = 0x13CE
ENDING = 0x141C
SRAM_FLAGS = (0x3B, 0x1E8)
PRE_ENTRY = {'title', 'files', 'intro', 'selected', 'map'}
POSITION_TOLERANCE = {('route', sample): 4 for sample in
                      ('checkpoint', 'jump', 'landed', 'onward', 'y19', 'y25')}
ROUTE_SAMPLES = {
    'route': {'checkpoint', 'jump', 'landed', 'onward', 'y19', 'y25'},
    'goal': {'before_coins', 'coin010', 'coin020', 'coin030', 'coin040', 'coin050',
             'coin060', 'coin070', 'coin080', 'coin090', 'coin097', 'coin098',
             'coin099', 'hundred_coins', 'goal_animation', 'overworld', 'file_reload'},
    'death': {'active', 'death_return', 'reentry'},
}


def blob(capture_name, tag, suffix='wram.bin'):
    return (ROOT / 'local/captures' / capture_name / (tag + '.' + suffix)).read_bytes()


def state(capture_name, tag):
    body = blob(capture_name, tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], coins=body[COINS],
                flag=body[HUB_FLAG], timer=word(body, GOAL_TIMER),
                goal=body[GOAL_ACTIVE], ending=body[ENDING])


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-li-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    require(receipt['rom_sha256'] == sha(head_rom), 'capture ROM differs: ' + name)
    if route == 'route':
        for sample in ROUTE_SAMPLES['route']:
            body = state(name, sample)
            require(body['mode'] == 0x14 and body['room'] == 0x117 and body['lives'] == 4,
                    'traversal sample differs: ' + host + '/' + sample)
            require(body['coins'] == 4, 'starting coin count differs: ' + host + '/' + sample)
        onward = state(name, 'onward')
        require(onward['x'] > 0x0D00 and onward['y'] <= 0x0120,
                'the traversal did not pass the former wall: ' + host)
    if route == 'goal':
        before = state(name, 'before_coins')
        require(before['mode'] == 0x14 and before['room'] == 0x117 and
                before['coins'] == 0 and before['lives'] == 4,
                'pre-pickup state differs: ' + host)
        require(state(name, 'coin090')['coins'] >= 0x50,
                'late coin sample is too low: ' + host)
        require(state(name, 'coin098')['coins'] == 99, '99-coin sample differs: ' + host)
        hundred = state(name, 'coin099')
        require(hundred['coins'] == 0 and hundred['lives'] == 5,
                '100-coin rollover or extra life differs: ' + host)
        require(state(name, 'hundred_coins')['lives'] == 5,
                'extra life was not retained: ' + host)
        animation = state(name, 'goal_animation')
        require(animation['timer'] > 0 and animation['ending'] == 1,
                'the 100-coin ending did not start: ' + host)
        overworld = state(name, 'overworld')
        require(overworld['mode'] == 0x0E and overworld['flag'] == 0x8F and
                overworld['goal'] == 1 and overworld['lives'] == 5,
                'overworld return differs: ' + host)
        reloaded = state(name, 'file_reload')
        require(reloaded['mode'] == 0x0E and reloaded['flag'] == 0x8F,
                'File A reload differs: ' + host)
        for sample in ('overworld', 'file_reload'):
            saved = blob(name, sample, 'sram.bin')
            require(saved[SRAM_FLAGS[0]] == 0x8F and saved[SRAM_FLAGS[1]] == 0x8F,
                    'saved SRAM flag differs: ' + host + '/' + sample)
    if route == 'death':
        require(state(name, 'active')['room'] == 0x117 and state(name, 'active')['lives'] == 4,
                'death route entry differs: ' + host)
        returned = state(name, 'death_return')
        require(returned['mode'] == 0x0E and returned['room'] == 0x117 and
                returned['lives'] == 3, 'death return differs: ' + host)
        reentry = state(name, 'reentry')
        require(reentry['mode'] == 0x14 and reentry['room'] == 0x117 and
                reentry['lives'] == 3, 'death re-entry differs: ' + host)
    return name, receipt


def compare_samples(a, b, route):
    for sample in ROUTE_SAMPLES[route]:
        left, right = state(a, sample), state(b, sample)
        for field, value in left.items():
            other = right[field]
            tolerance = POSITION_TOLERANCE.get((route, sample), 0) if field in ('x', 'y') else 0
            if tolerance and abs(value - other) <= tolerance:
                continue
            require(value == other,
                    f'sample differs: {route}/{sample}/{field}: {value} != {other}')


def main():
    global head_rom
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    head_rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    require(sha(head_rom) == cfg['output']['sha256'], 'head ROM identity differs')
    captures = {}
    for route, script in ROUTES.items():
        name, receipt = check_route('reference', route, script, False)
        captures[name] = receipt
        native_name, receipt = check_route('native', route, script, True)
        captures[native_name] = receipt
        compare_samples(native_name, name, route)
    for route, script in ROUTES.items():
        name = 'd11-li-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        compare_samples(name, 'd11-li-' + route + '-ref', route)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(head_rom) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(head_rom), binary_sha256=build['binary_sha256'],
                  captures=captures,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Valley_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/',
                                'docs/walkthrough-reference.md'],
                  limits=['The route and coin scripts use labelled map/player/camera shortcuts, Start pauses and damage immunity; the coin pickups, rollover, extra life, ending, save, key exit and deaths are real guest actions.',
                          'An unassisted 100-coin route and DK coverage are not claimed.',
                          'The cap music checks remain pinned by tools/qualify_demo11_lower_inner_music.py.',
                          'The save flag and SRAM constants are recipient-local. The demoOnly1 line matches them on these scripts.'])
    output = ROOT / 'local/reports/demo11-star-lower-inner-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Lower-inner Valley Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
