#!/usr/bin/env python3
"""Reproduce assisted trial5 switch/Koopa/shell interactions against official7hero."""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_native_lowmirror import usage
from qualify_seven_child import FIELDS
from qualify_sprite95_rooms import ROOT, TARGET, body, functional, script as room_script
from qualify_world1_next_course import require
from restore_star_world_1 import sha, write_verified

ARTIFACTS = ROOT / 'local/probes/sprite95-trial5-v1'
EVENTS = ((160, 112, 1), (192, 232, 2), (224, 208, 1), (240, 264, 3),
          (256, 304, 1), (272, 264, 3), (288, 304, 1), (304, 328, 2),
          (324, 328, 2), (340, 328, 2), (368, 400, 1), (400, 456, 3),
          (412, 424, 2), (432, 496, 1))


def script(side):
    text = room_script(side, 'door-5').split('dump trial\n')[0]+'dump trial\n'
    text += ('# Assisted standing positions; ordinary jumps hit the numbered switches.\n'
             'press b 8\ndump jump8\nwait 24\ndump land1\n'
             'pokefor 94 28005000 2\npress b 8\ndump jump2\nwait 24\ndump land2\n'
             'pokefor 94 48005000 2\npress b 8\ndump jump3\nwait 24\ndump land3\n'
             '# Source bridge tiles396/397/398 use bits1/2/4;39A/39B/39C invert bits1/2/4.\n')
    for number, (x, mario, _) in enumerate(EVENTS):
        if number == 12:
            text += '# Open the raised switch2 barrier before the Koopa reaches it.\n'
        xy = mario.to_bytes(2, 'little').hex()+'5000'
        text += (f'pokefor 94 {xy} 2\nuntil 00ec == {x & 255:02x} 500\n'
                 f'dump event{number:02}_before\npress b 8\ndump event{number:02}_hit\n'
                 f'pokefor 94 {xy} 4\ndump event{number:02}_after\n')
    text += ('wait 64\ndump approaching_shell\nwait 64\ndump shell_entry\n'
             'wait 64\ndump shell_later\n'
             '# Assisted drop position; real collision must produce stomp/pickup.\n'
             'poke 94 18027000\npress y 8\ndump stomp8\n'
             '# Separate side approach after real stomp; no shell writes.\n'
             'pokefor 94 04029000 2\npress right+y 20\ndump carried_or_release\n'
             'wait 16\ndump released\n'
             '# Explicit above-roof position/scroll fixture bypasses platform traversal.\n')
    for x in range(672, 977, 8):
        text += 'poke 94 '+x.to_bytes(2, 'little').hex()+'0000\n'
    return text+('pokefor 94 d0036000 30\ndump final_door_before\npress up 2\n'
                 'dump final_door_activated\nwait 160\ndump final_return\n'
                 'wait 160\ndump final_return_later\nquit\n')


def normal_actors(data, fields=FIELDS):
    return [(i, *(data[f+i] for f in fields)) for i in range(12)
            if data[0x14C8+i] and not data[0x1AB10+i] & 8]


def actor(data, slot):
    return dict(id=data[0x9E+slot], status=data[0x14C8+slot],
                x=data[0xE4+slot]+256*data[0x14E0+slot],
                y=data[0xD8+slot]+256*data[0x14D4+slot])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for side in ('native', 'source'):
        write_verified(ARTIFACTS / f'{side}-return-v3.script', script(side).encode())
    if args.prepare:
        print(ARTIFACTS, 'two immutable scripts')
        return
    require(args.output is not None and not args.output.exists(), 'supply a fresh report path')
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    verify(donor, json.loads((ROOT / 'config/7hero-donor.json').read_text())['output'], 'official7hero')
    relative = '../../local/probes/sprite95-trial5-v1/'
    a, ar = native('sprite95-trial5-return-native-v3', relative+'native-return-v3.script',
                   {0x19B8: 1, 0x19D8: 1}, target=TARGET)
    b, br = reference_capture('sprite95-trial5-return-source-v3', relative+'source-return-v3.script', donor)
    samples = {}

    def pair(tag, flags=None, fields=None):
        x, y = body(a, tag), body(b, tag)
        require(functional(x) == functional(y), 'functional mismatch: '+tag)
        if flags is not None:
            require(x[0x100] == 0x14 and int.from_bytes(x[0x10B:0x10D], 'little') == 0x172 and
                    x[0x71] == x[0x1493] == 0 and x[0x14AF] == flags and x[0x1FEAF] == 16,
                    'trial state/earned switch differs: '+tag)
            require(x[0x1420] == x[0x1422] == 0, 'coin already present before return: '+tag)
        if fields:
            require(normal_actors(x, fields) == normal_actors(y, fields), 'normal actor mismatch: '+tag)
        samples[tag] = dict(functional=functional(x), native_actors=normal_actors(x),
                            source_actors=normal_actors(y), compared_normal_fields=list(fields or ()),
                            carrying=x[0x1470], dragon_coins=[x[0x1420], x[0x1422]],
                            native_lives=x[0xDBE], source_lives=y[0xDBE])
        require(x[0x1420:0x1423] == y[0x1420:0x1423], 'coin state differs: '+tag)
        return x

    pair('trial', 0)
    for tag, flags in (('jump8', 1), ('land1', 1), ('jump2', 3), ('land2', 3),
                       ('jump3', 7), ('land3', 7)):
        pair(tag, flags)
    flags = 7
    motion = tuple(f for f in FIELDS if f not in (0x1570, 0x1602))
    for number, (x, _, switch) in enumerate(EVENTS):
        fields = FIELDS if number >= 9 else motion
        before = pair(f'event{number:02}_before', flags, fields)
        require(actor(before, 8) == dict(id=0, status=8, x=x, y=160), 'live Koopa event not reached')
        flags ^= 1 << (switch-1)
        pair(f'event{number:02}_hit', flags, fields)
        after = pair(f'event{number:02}_after', flags, fields)
        require(actor(after, 8) == dict(id=0, status=8, x=x+7, y=160), 'bridge crossing failed')
    for tag in ('approaching_shell', 'shell_entry', 'shell_later', 'stomp8', 'carried_or_release', 'released'):
        pair(tag, 1, FIELDS)
    for tag, xpos in (('shell_entry', 499), ('shell_later', 531)):
        data = body(a, tag)
        require(data[0x14C8+8] == 0 and actor(data, 9) == dict(id=4, status=8, x=xpos, y=160),
                'Koopa did not actually enter the waiting shell')
    require(actor(body(a, 'stomp8'), 9) == dict(id=4, status=9, x=537, y=160), 'real stomp absent')
    grabbed = body(a, 'carried_or_release')
    released = body(a, 'released')
    require(grabbed[0x1470] == body(b, 'carried_or_release')[0x1470] == 1 and
            grabbed[0x14C8+9] == 10 and released[0x1470] == body(b, 'released')[0x1470] == 0 and
            released[0x14C8+9] == 10 and actor(released, 9)['x'] > actor(grabbed, 9)['x'],
            'actual pickup/release evidence absent')
    for tag in ('final_door_before', 'final_door_activated', 'final_return', 'final_return_later'):
        data = pair(tag)
        if tag == 'final_door_before':
            require(data[0x71] == 0 and data[0x77] & 4 and functional(data)['room'] == 0x172 and
                    any(data[0x14C8+i] == 8 and data[0x1AB10+i] & 8 and data[0x1AB9E+i] == 0x95 and
                        actor(data, i)['x'] == 976 and actor(data, i)['y'] == 112 for i in range(12)),
                    'far door not live/grounded')
        elif tag == 'final_door_activated':
            require(data[0x71] == 6 and data[0x14AF] == data[0x1FEAF] == 16,
                    'ordinary Up did not restore the saved switch and activate the real door')
        else:
            require(functional(data) == dict(mode=0x14, room=0x16E, action=0, x=208, y=688,
                                             flags=16, saved_switch=0, goal=0) and
                    data[0x1420] == data[0x1422] == 1, 'return/real Dragon Coin absent')
        for directory in (a, b):
            initial, current = body(directory, 'trial'), body(directory, tag)
            require(current[0xDBE] == initial[0xDBE] and
                    current[0x1F2F:0x1F3B] == initial[0x1F2F:0x1F3B],
                    'unexpected life or saved five-coin flag change')
    report = dict(target=TARGET, native_receipt=ar, source_receipt=br, samples=samples,
                  checker_sha256=sha(Path(__file__).read_bytes()), module_usage=usage(a, 'A3'),
                  limits=['Map/room/pipe/immunity/player-position fixtures; no actor/HP/switch/progress/completion/save writes.',
                          'Early Koopa animation counter1570 and frame1602 differ; first nine bridge events compare17 fields, later events/shell compare19.',
                          'The input format inserts an idle frame after press: pickup is observed at1470=1 with shell already released tostatus10; no heldstatus11 sample claimed.',
                          'Above-roof far-corridor fixture bypasses remaining platform traversal; real Up return/one Dragon Coin only, no ordinary full trial clear, five-coin completion, save or audible/visible parity claim.'])
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
