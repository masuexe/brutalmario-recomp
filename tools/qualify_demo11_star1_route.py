#!/usr/bin/env python3
"""Qualify the Star World lower-left course route on the Demo 1-1 line.

The course's graphics recovery was already qualified. This check exercises the
existing route scripts on the current head: entry, ordinary movement, a real
fall/death/re-entry, the real normal goal plus save and console-reset reload,
and the real keyhole secret exit with its World 1 Warp Star. The scripts poke
map coordinates, player coordinates and damage immunity as labelled fixtures;
they do not edit destinations, completion flags, events, Dragon Coin bits or SRAM.
Reference and native runs must match fresh demoOnly1-line captures under the
same scripts.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
HEAD = 'demo11-node-music'
DONOR = 'star-world-1'
SCRIPTS = {
    'entry': 'star-world-1-entry.script',
    'goal': 'star-world-1-goal.script',
    'save': 'star-world-1-save.script',
    'secret': 'star-world-1-secret.script',
    'side-exit': 'star-world-1-side-exit.script',
}
DUMPS = {
    'entry': ('loaded', 'initialized', 'standing', 'run', 'jump', 'falling',
              'death_return', 'reentry'),
    'goal': ('active', 'goal_room', 'clear', 'normal_clear_map',
             'normal_cleared_node', 'normal_reentry'),
    'save': ('goal_room', 'clear', 'normal_clear_map', 'file_reload', 'reload_node',
             'reload_reentry'),
    'secret': ('active', 'next', 'bottom', 'key_pickup', 'secret_map', 'secret_star',
               'destination'),
    'side-exit': ('loaded', 'initialized', 'active', 'next', 'room51', 'side_exit'),
}
POSITION_TOLERANCE = {
    ('entry', 'jump'): (6, 10),
    ('entry', 'falling'): (6, 12),
    ('secret', 'next'): (2, 8),
}
KEY_FLAG = 0x1EA7
SRAM_FLAGS = (5, 0x1B2)
NORMAL_FLAG = 0x89
SECRET_FLAG = 0x8B
EXPECTED = {
    'entry': {
        'loaded': dict(mode=0x12, room=0x005, lives=4),
        'initialized': dict(mode=0x13, room=0x005),
        'standing': dict(mode=0x14, room=0x005, x=16, y=352, lives=4),
        'run': dict(mode=0x14, room=0x005),
        'jump': dict(mode=0x14, room=0x005),
        'falling': dict(mode=0x14, room=0x005),
        'death_return': dict(mode=0x0E, room=0x005, lives=3, flag=0x09),
        'reentry': dict(mode=0x14, room=0x005, lives=3),
    },
    'goal': {
        'active': dict(mode=0x14, room=0x005, lives=4),
        'goal_room': dict(mode=0x14, room=0x048, x=40, y=320),
        'clear': dict(mode=0x14, room=0x048),
        'normal_clear_map': dict(mode=0x0E, flag=NORMAL_FLAG, map=6, mapx=344, mapy=424),
        'normal_cleared_node': dict(mode=0x0E, mapx=296, mapy=488),
        'normal_reentry': dict(mode=0x14, room=0x005, flag=NORMAL_FLAG),
    },
    'save': {
        'goal_room': dict(mode=0x14, room=0x048),
        'clear': dict(mode=0x14, room=0x048),
        'normal_clear_map': dict(mode=0x0E, flag=NORMAL_FLAG, mapx=344, mapy=424),
        'file_reload': dict(mode=0x0E, flag=NORMAL_FLAG, lives=4),
        'reload_node': dict(mode=0x0E, mapx=296, mapy=488),
        'reload_reentry': dict(mode=0x14, room=0x005, flag=NORMAL_FLAG),
    },
    'secret': {
        'active': dict(mode=0x14, room=0x005, lives=4),
        'next': dict(mode=0x14, room=0x054),
        'bottom': dict(mode=0x14, room=0x054),
        'key_pickup': dict(mode=0x14, room=0x054, key=1, lives=4),
        'secret_map': dict(mode=0x0E, flag=SECRET_FLAG, sram=[SECRET_FLAG, SECRET_FLAG]),
        'secret_star': dict(mode=0x0E, map=6, mapx=296, mapy=488),
        'destination': dict(mode=0x0E, map=0, mapx=104, mapy=440),
    },
    'side-exit': {
        'loaded': dict(mode=0x12, room=0x005),
        'initialized': dict(mode=0x13, room=0x005),
        'active': dict(mode=0x14, room=0x005, x=16, y=352),
        'next': dict(mode=0x14, room=0x048, x=40, y=320),
        'room51': dict(mode=0x14, room=0x051, x=120, y=320),
        'side_exit': dict(mode=0x0E, room=0x051, map=0, mapx=72, mapy=408),
    },
}


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    require(len(body) == 0x20000, 'incomplete WRAM: ' + tag)
    word = lambda address: int.from_bytes(body[address:address + 2], 'little')
    return dict(mode=body[0x100], room=word(0x10B), x=word(0x94), y=word(0x96),
                lives=body[0x0DBE], flag=body[KEY_FLAG], key=body[0x1470],
                sram=[saved[SRAM_FLAGS[0]], saved[SRAM_FLAGS[1]]],
                map=body[0x1F11], mapx=word(0x1F17), mapy=word(0x1F19))


def check_route(host, route, script, native):
    name = 'd11-star1-route-' + route + '-' + ('native' if native else 'ref')
    directory, receipt = capture(name, HEAD, script, native)
    states = {tag: state(directory, tag) for tag in DUMPS[route]}
    for tag, expected in EXPECTED[route].items():
        body = states[tag]
        for key, value in expected.items():
            require(body[key] == value,
                    f'route value differs: {host}/{route}/{tag}/{key}: {body[key]!r} != {value!r}')
    if route == 'entry':
        require(states['loaded']['x'] == 16 and states['loaded']['y'] == 352,
                'entrance spawn differs: ' + host)
        require(states['standing']['x'] == 16 and states['standing']['y'] == 352,
                'standing surface differs: ' + host)
        require(states['run']['x'] > 0x100, 'ordinary run did not cross the floor: ' + host)
        require(states['jump']['y'] < 0x140 and states['jump']['x'] > 0x100,
                'ordinary jump differs: ' + host)
        require(states['falling']['y'] > 0x200, 'ordinary fall did not happen: ' + host)
    if route == 'goal':
        require(states['clear']['x'] >= 0x1C0, 'goal tape was not reached: ' + host)
        require(states['normal_clear_map']['sram'] == [NORMAL_FLAG, NORMAL_FLAG],
                'normal clear was not saved: ' + host)
        require(states['normal_reentry']['sram'] == [NORMAL_FLAG, NORMAL_FLAG],
                'normal re-entry lost the clear: ' + host)
    if route == 'save':
        require(states['file_reload']['sram'] == [NORMAL_FLAG, NORMAL_FLAG],
                'console reset reload lost the clear: ' + host)
        require(states['reload_reentry']['sram'] == [NORMAL_FLAG, NORMAL_FLAG],
                're-entry after reload lost the clear: ' + host)
    if route == 'secret':
        require(states['bottom']['y'] > 0x300, 'secret room descent differs: ' + host)
        require(states['secret_map']['sram'] == [SECRET_FLAG, SECRET_FLAG],
                'secret clear was not saved: ' + host)
    return name, receipt, states


def compare_donor(reference, donor):
    for route in SCRIPTS:
        for tag in DUMPS[route]:
            expected, actual = donor[route][tag], reference[route][tag]
            tolerance = POSITION_TOLERANCE.get((route, tag), (0, 0))
            for key, value in expected.items():
                if key in ('x', 'y') and tolerance != (0, 0):
                    index = 0 if key == 'x' else 1
                    if abs(actual[key] - value) <= tolerance[index]:
                        continue
                if actual[key] != value:
                    raise ValueError('route differs from demoOnly1 line: %s/%s/%s' % (route, tag, key))


def main():
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'head ROM identity differs')
    captures, reference, native_states, donor = {}, {}, {}, {}
    for route, script in SCRIPTS.items():
        name, receipt, states = check_route('reference', route, script, False)
        captures[name] = receipt
        reference[route] = states
    for route, script in SCRIPTS.items():
        name, receipt, states = check_route('native', route, script, True)
        captures[name] = receipt
        native_states[route] = states
    for route, script in SCRIPTS.items():
        name = 'd11-star1-only1-' + route + '-ref'
        directory, receipt = capture(name, DONOR, script, False)
        captures[name] = receipt
        donor[route] = {tag: state(directory, tag) for tag in DUMPS[route]}
    compare_donor(reference, donor)

    report = dict(scope=__doc__.strip(), head=HEAD, donor_target=DONOR,
                  rom_sha256=sha(rom),
                  captures=captures,
                  results=dict(reference=reference, native=native_states, donor=donor),
                  limits=['The scripts use labelled map/player coordinate shortcuts and damage immunity; the goal and keyhole interactions are real guest actions.',
                          'This is the same bounded boundary the demoOnly1 line accepted: no unassisted full traversal, no Dragon Coin persistence claim and no audio claim.',
                          'The course graphics recovery remains pinned by the earlier Star1 graphics qualifier.'])
    output = ROOT / 'local/reports/demo11-star1-route.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Lower-left route checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
