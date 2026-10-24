#!/usr/bin/env python3
"""Qualify the Star World upper-right Plains Star routes on the Demo 1-1 line.

The tracked upper-right scripts cover the brick maze on the current head:
entry and ordinary controls, five real Dragon Coins with the real upward pipe and
goal tape plus save and console-reset reload, and a real fall/death/re-entry.
Reference and native runs must match fresh demoOnly1-line captures under the
same scripts.

The course music now uses the wiki-correct Plains Star slot 32. The level's
keyhole secret exit (P-Switch brick route) is not part of this check.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-upper-right'
ROUTES = {
    'entry': 'star-world-upper-right-entry.script',
    'coins-save': 'star-world-upper-right-coins-save.script',
    'death': 'star-world-upper-right-death.script',
}
HUB_FLAG = 0x1EA4
DRAGON_COIN_SAVED = 0x1F2F
PLAINS_SLOT = 0x32
LEGACY_SLOT = 0x5D
POSITION_TOLERANCE = {('entry', 'jump'): ('y', 16), ('entry', 'later'): ('y', 16)}
EXPECTED = {
    'entry': {
        'layout': dict(mode=0x12, room=0x002, x=0x0080, y=0x1080),
        'graphics': dict(mode=0x13, room=0x002),
        'active': dict(mode=0x14, room=0x002, x=0x0080, y=0x1080, lives=4),
        'standing': dict(mode=0x14, room=0x002, x=0x0080, y=0x1080),
        'walk': dict(mode=0x14, room=0x002, x=0x00B6, y=0x1080),
        'jump': dict(mode=0x14, room=0x002, x=0x00D2),
        'later': dict(mode=0x14, room=0x002, x=0x00D2),
    },
    'coins-save': {
        'active': dict(mode=0x14, room=0x002, lives=4),
        'coin1': dict(mode=0x14, room=0x002, x=0x01C0, y=0x0F90, lives=4),
        'coin2': dict(mode=0x14, room=0x002, x=0x0040, y=0x0F30),
        'coin3': dict(mode=0x14, room=0x002, x=0x00B0, y=0x0DE0),
        'coin4': dict(mode=0x14, room=0x002, x=0x0070, y=0x0D10),
        'coin5': dict(mode=0x14, room=0x002, x=0x00D0, y=0x0B70, lives=5, dk=0x20),
        'pipe_below': dict(mode=0x14, room=0x002, x=0x0108, y=0x0AB0, lives=5),
        'pipe_exit': dict(mode=0x14, room=0x048, x=0x0028, y=0x0140, lives=5),
        'saved_map': dict(mode=0x0E, room=0x048, flag=0x86, dk=0x20,
                          sram={2: 0x86, 0x1AF: 0x86}),
        'file_reload': dict(mode=0x0E, room=0x0C7, flag=0x86, dk=0x20,
                            sram={2: 0x86, 0x1AF: 0x86}),
        'reload_node': dict(mode=0x0E, room=0x0C7, flag=0x86, dk=0x20),
        'reload_reentry': dict(mode=0x14, room=0x002, x=0x0080, y=0x1080, flag=0x86, dk=0x20,
                               sram={2: 0x86}),
    },
    'death': {
        'active': dict(mode=0x14, room=0x002, lives=4),
        'death_return': dict(mode=0x0E, room=0x002, x=0x010E, y=0x012E, lives=3),
        'reentry': dict(mode=0x14, room=0x002, x=0x0080, y=0x1080, lives=3),
    },
}
ROUTE_SAMPLES = {'layout', 'graphics', 'active', 'standing', 'walk', 'jump', 'later',
                 'coin1', 'coin2', 'coin3', 'coin4', 'coin5', 'pipe_below', 'pipe_exit',
                 'saved_map', 'file_reload', 'reload_node', 'reload_reentry',
                 'death_return', 'reentry'}


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], flag=body[HUB_FLAG],
                dk=body[DRAGON_COIN_SAVED], sram={2: saved[2], 0x1AF: saved[0x1AF]})


def music_requests(capture_name):
    events = [json.loads(line) for line in
              (ROOT / 'local/captures' / capture_name / 'wram.jsonl').read_text().splitlines()]
    return [int(event['val'], 16) for event in events
            if event['f'] >= 2000 and event['adr'] == '0x01dfb'
            and int(event['val'], 16) not in (0, 0x20, 0x80)]


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-ur-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    states = {key: state(directory, key) for key in EXPECTED[route]}
    for key, expected in EXPECTED[route].items():
        for field, value in expected.items():
            if field == 'sram':
                for offset, byte in value.items():
                    require(states[key]['sram'][offset] == byte,
                            f'saved flag differs: {host}/{route}/{key}/sram[{offset}]')
                continue
            actual = states[key][field]
            tolerance = POSITION_TOLERANCE.get((route, key))
            if tolerance and tolerance[0] == field and abs(actual - value) <= tolerance[1]:
                continue
            require(actual == value,
                    f'route value differs: {host}/{route}/{key}/{field}: '
                    f'{actual!r} != {value!r}')
    if route == 'entry':
        layout = (directory / 'layout.wram.bin').read_bytes()
        active = (directory / 'active.wram.bin').read_bytes()
        changed = sum(1 for index in range(0xC800, 0xE000) if layout[index] != active[index])
        require(changed == 0, 'low Map16 buffer was corrupted: ' + host)
        if not native:
            sequence = music_requests(directory.name)
            require(PLAINS_SLOT in sequence, 'Plains Star slot 32 is not requested: ' + str(sequence))
            require(LEGACY_SLOT not in sequence, 'legacy slot 5D is still requested: ' + str(sequence))
    return name, receipt, states


def main():
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'head ROM identity differs')
    captures, results = {}, {}
    for route, script in ROUTES.items():
        name, receipt, states = check_route('reference', route, script, False)
        captures[name] = receipt
        results['reference_' + route] = states
    for route, script in ROUTES.items():
        name, receipt, states = check_route('native', route, script, True)
        captures[name] = receipt
        results['native_' + route] = states
        for key in states:
            for field in ('mode', 'room', 'x', 'y', 'lives', 'flag', 'dk'):
                reference = results['reference_' + route][key][field]
                actual = states[key][field]
                tolerance = POSITION_TOLERANCE.get((route, key))
                if tolerance and tolerance[0] == field and abs(actual - reference) <= tolerance[1]:
                    continue
                require(actual == reference, f'hosts differ: {route}/{key}/{field}')
    for route, script in ROUTES.items():
        name = 'd11-ur-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        donor = {key: state(directory, key) for key in EXPECTED[route]}
        for key in ROUTE_SAMPLES & set(EXPECTED[route]):
            reference = results['reference_' + route][key]
            for field in ('mode', 'room', 'x', 'y'):
                tolerance = POSITION_TOLERANCE.get((route, key))
                if tolerance and tolerance[0] == field and abs(donor[key][field] - reference[field]) <= tolerance[1]:
                    continue
                require(donor[key][field] == reference[field],
                        f'demoOnly1 parity differs: {route}/{key}/{field}')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(rom) and build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(rom), binary_sha256=build['binary_sha256'],
                  captures=captures, results=results,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Plains_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/'],
                  limits=['The scripts use labelled map/player/camera shortcuts and damage immunity; the coins, pipe, goal and deaths are real guest actions.',
                          'The Plains Star keyhole secret exit is not covered. The wiki route is: find the backward-animated brick near the top right, take its P-Switch, go to the bottom, press it to convert the bricks, and fall to the key and keyhole.',
                          'The course now requests the wiki-correct Plains Star slot 32 instead of the legacy 5D substitution; that change is the accepted BGM checkpoint.',
                          'An unassisted full traversal is not claimed.',
                          'The save flag constants are recipient-local. The demoOnly1 line uses the same normal-clear value on these scripts.'])
    output = ROOT / 'local/reports/demo11-star-upper-right-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Upper-right Plains Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
