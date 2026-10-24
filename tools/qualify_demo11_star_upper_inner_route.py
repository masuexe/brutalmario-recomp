#!/usr/bin/env python3
"""Qualify the Star World upper-inner Cave Star routes on the Demo 1-1 line.

The tracked upper-inner scripts cover the DKC2-style roller-coaster course on
the current head: entry and the coaster progress, the real coaster finish
with the normal-clear save and File A reload, and a real pit/death/re-entry.
Reference and native runs must match fresh demoOnly1-line captures under the
same scripts.

The wiki describes the Cave Star as a Skull Cart race against Koopas: the
normal exit reaches the end of the track, and the secret branch needs 1st
place in the race counter. The secret branch is not covered by this check.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-upper-inner'
ROUTES = {
    'entry': 'star-world-upper-inner-entry.script',
    'goal': 'star-world-upper-inner-goal.script',
    'death': 'star-world-upper-inner-death.script',
}
HUB_FLAG = 0x1EA9
GOAL_ACTIVE = 0x13CE
SRAM_FLAG = 7
SRAM_FLAG_MIRROR = 0x1B4
CAVE_SLOT = 0x51
PRE_ENTRY = {'title', 'files', 'intro', 'selected', 'map'}
ROUTE_SAMPLES = {
    'entry': {'active', 'entry180', 'entry600'},
    'goal': {'ow1', 'ow2', 'file_reload'},
    'death': {'layout', 'graphics', 'active', 'death_return', 'reentry'},
}


def blob(capture_name, tag, suffix='wram.bin'):
    return (ROOT / 'local/captures' / capture_name / (tag + '.' + suffix)).read_bytes()


def state(capture_name, tag):
    body = blob(capture_name, tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], flag=body[HUB_FLAG],
                coins=body[0x0DBF], xhigh=body[0x95], goal=body[GOAL_ACTIVE])


def music_requests(capture_name):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture_name / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2000 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-ui-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    require(receipt['rom_sha256'] == sha(head_rom), 'capture ROM differs: ' + name)
    if route == 'entry':
        active = state(name, 'active')
        require(active['mode'] == 0x14 and active['room'] == 0x007 and active['lives'] == 4,
                'entry state differs: ' + host)
        require(state(name, 'entry180')['xhigh'] == 1,
                'coaster progress did not reach X high 1: ' + host)
        require(state(name, 'entry600')['xhigh'] == 3,
                'coaster progress did not reach X high 3: ' + host)
        if not native:
            sequence = music_requests(name)
            require(CAVE_SLOT in sequence, 'Cave Star slot 51 is not requested: ' + str(sequence))
    if route == 'goal':
        ow1 = state(name, 'ow1')
        require(ow1['mode'] == 0x0D and ow1['room'] == 0x007 and ow1['goal'] == 1,
                'coaster finish transition differs: ' + host)
        ow2 = state(name, 'ow2')
        require(ow2['mode'] == 0x0E and ow2['flag'] == 0x81,
                'normal clear state differs: ' + host)
        reloaded = state(name, 'file_reload')
        require(reloaded['mode'] == 0x0E and reloaded['flag'] == 0x81,
                'File A reload differs: ' + host)
        for sample in ('ow2', 'file_reload'):
            saved = blob(name, sample, 'sram.bin')
            require(saved[SRAM_FLAG] == 0x81 and saved[SRAM_FLAG_MIRROR] == 0x81,
                    'saved SRAM flag differs: ' + host + '/' + sample)
    if route == 'death':
        layout = blob(name, 'layout')
        graphics = blob(name, 'graphics')
        active = blob(name, 'active')
        require(layout[0xC800:0x10000] == graphics[0xC800:0x10000],
                'low Map16 changed during graphics load: ' + host)
        require(graphics[0xC800:0x10000] == active[0xC800:0x10000],
                'low Map16 changed after activation: ' + host)
        require(state(name, 'active')['room'] == 0x007 and state(name, 'active')['lives'] == 4,
                'death route entry differs: ' + host)
        returned = state(name, 'death_return')
        require(returned['mode'] == 0x0E and returned['room'] == 0x007 and
                returned['lives'] == 3, 'death return differs: ' + host)
        reentry = state(name, 'reentry')
        require(reentry['mode'] == 0x14 and reentry['room'] == 0x007 and
                reentry['lives'] == 3, 'death re-entry differs: ' + host)
    return name, receipt


def compare_route(a, b, route, strict):
    for sample in ROUTE_SAMPLES[route]:
        left, right = state(a, sample), state(b, sample)
        for field, value in left.items():
            other = right[field]
            if strict:
                require(value == other,
                        f'sample differs: {route}/{sample}/{field}: {value} != {other}')
            elif field in ('mode', 'room', 'xhigh', 'flag', 'goal', 'lives'):
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
        compare_route(native_name, name, route, strict=(route != 'entry'))
    for route, script in ROUTES.items():
        name = 'd11-ui-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        compare_route(name, 'd11-ui-' + route + '-ref', route, strict=True)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(head_rom) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(head_rom), binary_sha256=build['binary_sha256'],
                  captures=captures,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Cave_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/',
                                'docs/walkthrough-reference.md'],
                  limits=['The scripts use labelled map/player shortcuts, player-X waits and, in the goal script, two phase counters to align both hosts; the coaster ride, finish, save, reload and deaths are real guest actions.',
                          'The normal clear is qualified. The secret branch is not covered; the Japanese wiki route requires defeating every Koopa so the goal block turns off, and the race-counter storage was not identified in this checkpoint.',
                          'The entry coaster positions differ by one frame between hosts (entry180 has a one-pixel offset; entry600 has a different coaster height). The check compares mode, room and player X high byte, not the exact coaster pixel.',
                          'An unassisted full traversal is not claimed. The save flag and SRAM constants are recipient-local.'])
    output = ROOT / 'local/reports/demo11-star-upper-inner-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Upper-inner Cave Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
