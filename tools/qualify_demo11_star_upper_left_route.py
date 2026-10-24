#!/usr/bin/env python3
"""Qualify the Star World upper-left Bay Star routes on the Demo 1-1 line.

The tracked upper-left scripts cover the vertical water cave on the current
head: entry and ordinary controls, real swimming and a water-level switch,
five real DK coins with the screen-8 pipe and the real goal tape, the alternate
pipe side exit, and a real fall/death/re-entry. Reference and native runs must
match fresh demoOnly1-line captures under the same scripts.

The bay keyhole secret exit is not part of this check. The wiki route is
recorded in the report limits.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
DONOR = 'star-world-upper-left'
ROUTES = {
    'entry': 'star-world-upper-left-entry.script',
    'water': 'star-world-upper-left-water.script',
    'coins-save': 'star-world-upper-left-coins-save.script',
    'side-exit': 'star-world-upper-left-side-exit.script',
    'death': 'star-world-upper-left-death.script',
}
WATER_TARGET = 0x1FFD0
HUB_FLAG = 0x1EA6
HUB_SECOND = 0x1EA9
DK_SAVED = 0x1F2F
EXPECTED = {
    'entry': {
        'selected': dict(mode=0x0E, room=0x0C5),
        'layout': dict(mode=0x12, room=0x004, x=0x01A0, y=0x0CB0),
        'graphics': dict(mode=0x13, room=0x004),
        'active': dict(mode=0x14, room=0x004, x=0x01A0, y=0x0CB0, lives=4),
        'standing': dict(mode=0x14, room=0x004, x=0x01A0, y=0x0CB0),
        'jump': dict(mode=0x14, room=0x004, x=0x0163),
        'move': dict(mode=0x14, room=0x004, x=0x0149),
        'later': dict(mode=0x14, room=0x004, x=0x0148),
    },
    'water': {
        'standing': dict(mode=0x14, room=0x004, x=0x01A0, y=0x0CB0, water=0x0CB0),
        'swim': dict(mode=0x14, room=0x004, x=0x01A0, y=0x0CA4, water=0x0CB0),
        'water_switch': dict(mode=0x14, room=0x004, x=0x0020, y=0x0CB0, water=0x0C90),
        'water_settled': dict(mode=0x14, room=0x004, x=0x0020, y=0x0CB0, water=0x0C90),
    },
    'coins-save': {
        'coin1': dict(mode=0x14, room=0x004, x=0x0180, y=0x0BBF, lives=4),
        'coin2': dict(mode=0x14, room=0x004, x=0x0020, y=0x0B85),
        'coin3': dict(mode=0x14, room=0x004, x=0x0010, y=0x0B68),
        'coin4': dict(mode=0x14, room=0x004, x=0x0040, y=0x0B4A),
        'coin5': dict(mode=0x14, room=0x004, x=0x01D0, y=0x0B20, lives=5, dk=0x08),
        'pipe_ready': dict(mode=0x14, room=0x004, x=0x0190, y=0x08A9),
        'goal_room': dict(mode=0x14, room=0x048, x=0x0028, y=0x0140, lives=5),
        'saved_map': dict(mode=0x0E, room=0x048, flag=0x85, second=0x03, dk=0x08,
                          sram={4: 0x85, 7: 0x03}),
        'file_reload': dict(mode=0x0E, room=0x0C7, flag=0x85, second=0x03, dk=0x08,
                            sram={4: 0x85, 7: 0x03}),
        'reload_node': dict(mode=0x0E, room=0x0C7, flag=0x85, second=0x03, dk=0x08),
        'reload_reentry': dict(mode=0x14, room=0x004, flag=0x85, second=0x03, dk=0x08,
                               sram={4: 0x85}),
    },
    'side-exit': {
        'active': dict(mode=0x14, room=0x004),
        'goal_room': dict(mode=0x14, room=0x048, x=0x0028, y=0x0140),
        'side_room': dict(mode=0x14, room=0x051, x=0x0078, y=0x0140),
        'side_exit': dict(mode=0x0E, room=0x051, x=0x000D, y=0x011E, lives=4),
    },
    'death': {
        'active': dict(mode=0x14, room=0x004, lives=4),
        'death_return': dict(mode=0x0E, room=0x004, x=0x010E, y=0x012E, lives=3),
        'reentry': dict(mode=0x14, room=0x004, x=0x01A0, y=0x0CB0, lives=3),
    },
}


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + tag)
    return dict(mode=body[0x100], room=word(body, 0x10B), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], flag=body[HUB_FLAG],
                second=body[HUB_SECOND], dk=body[DK_SAVED],
                water=word(body, WATER_TARGET), sram={4: saved[4], 7: saved[7]})


def check_route(host, route, script, native):
    tag = 'native' if native else 'ref'
    name = 'd11-ul-' + route + '-' + tag
    directory, receipt = capture(name, HEAD, script, native)
    states = {key: state(directory, key) for key in EXPECTED[route]}
    for key, expected in EXPECTED[route].items():
        for field, value in expected.items():
            if field == 'sram':
                for offset, byte in value.items():
                    require(states[key]['sram'][offset] == byte,
                            f'saved flag differs: {host}/{route}/{key}/sram[{offset}]')
                continue
            require(states[key][field] == value,
                    f'route value differs: {host}/{route}/{key}/{field}: '
                    f'{states[key][field]!r} != {value!r}')
    if route == 'entry':
        require(states['move']['x'] < states['standing']['x'], 'ordinary left input moved the player: ' + host)
        layout = (directory / 'layout.wram.bin').read_bytes()
        active = (directory / 'active.wram.bin').read_bytes()
        changed = sum(1 for index in range(0xC800, 0xE000) if layout[index] != active[index])
        require(changed == 0, 'low Map16 buffer was corrupted: ' + host)
    if route == 'water':
        require(states['swim']['y'] < states['standing']['y'], 'B presses did not swim upward: ' + host)
    return name, receipt, states


def main():
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'head ROM identity differs')
    captures, results, donor = {}, {}, {}
    for route, script in ROUTES.items():
        name, receipt, states = check_route('reference', route, script, False)
        captures[name] = receipt
        results['reference_' + route] = states
    for route, script in ROUTES.items():
        name, receipt, states = check_route('native', route, script, True)
        captures[name] = receipt
        results['native_' + route] = states
        for key in states:
            for field in ('mode', 'room', 'x', 'y', 'lives', 'flag', 'second', 'dk', 'water'):
                require(states[key][field] == results['reference_' + route][key][field],
                        f'hosts differ: {route}/{key}/{field}')
    for route, script in ROUTES.items():
        name = 'd11-ul-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        donor[route] = {key: state(directory, key) for key in EXPECTED[route]}
        for key in EXPECTED[route]:
            if key == 'selected':
                continue
            for field in ('mode', 'room', 'x', 'y'):
                require(donor[route][key][field] == results['reference_' + route][key][field],
                        f'demoOnly1 parity differs: {route}/{key}/{field}')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(rom) and build['binary_sha256'] == sha(binary.read_bytes()),
            'native build identity differs')

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(rom), binary_sha256=build['binary_sha256'],
                  captures=captures, results=results,
                  wiki_sources=['https://brutalmario.fandom.com/wiki/Bay_Star',
                                'https://brutalmario.fandom.com/wiki/Music',
                                'https://wikiwiki.jp/kitikumario/'],
                  limits=['The scripts use labelled map/player coordinate shortcuts and damage immunity; the coins, water switch, pipes, goal and deaths are real guest actions.',
                          'The bay keyhole secret exit is not covered. The wiki route is: touch the top switch, let the water rise, lower it two levels, then take the key to the keyhole.',
                          'An unassisted full ascent is not claimed.',
                          'The save flag constants are recipient-local. The demoOnly1 line uses the same normal-clear value on these scripts.'])
    output = ROOT / 'local/reports/demo11-star-upper-left-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Upper-left Bay Star route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
