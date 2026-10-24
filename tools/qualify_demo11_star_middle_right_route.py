#!/usr/bin/env python3
"""Qualify the Star World middle-right Sky Star routes on the Demo 1-1 line.

The tracked middle-right scripts cover the vertical rocket course on the
current head: entry and ordinary controls with the rocket fuel load, the real
rocket finish and top door with the normal-clear save and File A reload, and a
real fall/death/re-entry. Reference and native runs must match fresh
demoOnly1-line captures under the same scripts.

The user verified the secret exit in play. This check qualifies only the
normal exit and does not repeat the secret route search.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-middle-right'
ROUTES = {
    'entry': 'star-world-middle-right-entry.script',
    'goal': 'star-world-middle-right-goal.script',
    'death': 'star-world-middle-right-death.script',
}
HUB_FLAG = 0x1EAB
FUEL = 0x1594
GOAL_ACTIVE = 0x13CE
SRAM_FLAG = 9
SRAM_FLAG_MIRROR = 0x1B6
SKY_SLOT = 0x58
PRE_ENTRY = {'title', 'files', 'intro', 'selected', 'map'}
ROUTE_SAMPLES = {
    'entry': {'layout', 'graphics', 'active', 'standing', 'walk', 'jump', 'later'},
    'goal': {'active', 'finish', 'door', 'blocks', 'landed', 'overworld', 'file_reload'},
    'death': {'active', 'death_return', 'reentry', 'reentry_later'},
}


def blob(capture_name, tag, suffix='wram.bin'):
    return (ROOT / 'local/captures' / capture_name / (tag + '.' + suffix)).read_bytes()


def state(capture_name, tag):
    body = blob(capture_name, tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], flag=body[HUB_FLAG],
                coins=body[0x0DBF], fuel=body[FUEL], ending=body[GOAL_ACTIVE])


def music_requests(capture_name):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture_name / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2000 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-mr-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    require(receipt['rom_sha256'] == sha(head_rom), 'capture ROM differs: ' + name)
    if route == 'entry':
        require(blob(name, 'layout')[0xC800:0x10000] == blob(name, 'graphics')[0xC800:0x10000],
                'low Map16 buffer was corrupted: ' + host)
        active = state(name, 'active')
        require(active['mode'] == 0x14 and active['room'] == 0x009 and
                active['lives'] == 4 and active['fuel'] == 0x0B,
                'entry state differs: ' + host)
        require(state(name, 'standing')['room'] == 0x009 and
                state(name, 'standing')['x'] == 0x070,
                'standing sample differs: ' + host)
        require(state(name, 'walk')['x'] > state(name, 'standing')['x'],
                'ordinary movement changed nothing: ' + host)
        require(state(name, 'jump')['fuel'] == 0x0A,
                'rocket fuel load was not consumed: ' + host)
        if not native:
            sequence = music_requests(name)
            require(SKY_SLOT in sequence, 'Sky Star slot 58 is not requested: ' + str(sequence))
    if route == 'goal':
        finish = state(name, 'finish')
        require(finish['mode'] == 0x14 and finish['room'] == 0x009 and
                finish['coins'] == 4 and finish['fuel'] == 0,
                'rocket finish differs: ' + host)
        require(state(name, 'door')['room'] == 0x09B and
                state(name, 'blocks')['room'] == 0x09B and
                state(name, 'landed')['room'] == 0x09B,
                'goal room samples differ: ' + host)
        overworld = state(name, 'overworld')
        require(overworld['mode'] == 0x0E and overworld['room'] == 0x09B and
                overworld['flag'] == 0x8C and overworld['ending'] == 1,
                'normal clear state differs: ' + host)
        reloaded = state(name, 'file_reload')
        require(reloaded['mode'] == 0x0E and reloaded['flag'] == 0x8C,
                'File A reload differs: ' + host)
        for sample in ('overworld', 'file_reload'):
            saved = blob(name, sample, 'sram.bin')
            require(saved[SRAM_FLAG] == 0x8C and saved[SRAM_FLAG_MIRROR] == 0x8C,
                    'saved SRAM flag differs: ' + host + '/' + sample)
    if route == 'death':
        require(state(name, 'active')['room'] == 0x009 and state(name, 'active')['lives'] == 4,
                'death route entry differs: ' + host)
        returned = state(name, 'death_return')
        require(returned['mode'] == 0x0E and returned['room'] == 0x009 and
                returned['lives'] == 3, 'death return differs: ' + host)
        reentry = state(name, 'reentry')
        require(reentry['mode'] == 0x14 and reentry['room'] == 0x009 and
                reentry['lives'] == 3 and reentry['fuel'] == 0x0B,
                'death re-entry differs: ' + host)
    return name, receipt


def compare_route(a, b, route):
    for sample in ROUTE_SAMPLES[route]:
        left, right = state(a, sample), state(b, sample)
        require(left == right, f'sample differs: {route}/{sample}: {left} != {right}')


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
        compare_route(native_name, name, route)
    for route, script in ROUTES.items():
        name = 'd11-mr-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        compare_route(name, 'd11-mr-' + route + '-ref', route)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(head_rom) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(head_rom), binary_sha256=build['binary_sha256'],
                  captures=captures,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Sky_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/',
                                'docs/walkthrough-reference.md',
                                'docs/demo11-sky-secret.md'],
                  limits=['The scripts use labelled map shortcuts, scripted rides and the existing top-door input sequence; the rocket ride, finish, door, save, reload and death are real guest actions.',
                          'The normal exit is qualified. The secret exit was verified by the user in play and is not retried here.',
                          'An unassisted full traversal and listening acceptance are not claimed.',
                          'The save flag and SRAM constants are recipient-local. The demoOnly1 line matches them on these scripts.'])
    output = ROOT / 'local/reports/demo11-star-middle-right-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Middle-right Sky Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
