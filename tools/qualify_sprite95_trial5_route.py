#!/usr/bin/env python3
"""Qualify the ordinary carry/jump/vine/door segment after explicit trial5 fixtures."""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_native_lowmirror import usage
from qualify_seven_child import FIELDS
from qualify_sprite95_rooms import ROOT, TARGET, actors, body, functional
from qualify_sprite95_trial5 import EVENTS, actor, normal_actors, script as assisted_script
from qualify_world1_next_course import require
from restore_star_world_1 import sha, write_verified

ARTIFACTS = ROOT / 'local/probes/sprite95-trial5-route-v2'
ROUTE = ('escaped_away', 'upper_before', 'upper_jump', 'upper_after', 'ledge_before',
         'brake', 'stop', 'creep', 'pit', 'vine_grab', 'vine_down', 'door_ready',
         'activated', 'returned', 'returned_later')


def script(side):
    text = assisted_script(side).split('# Separate side approach', 1)[0]
    text = text.replace('forcepoke 1497 ff\n', '').replace(
        '# Diagnostic primary-room/pipe/immunity/player-position fixture.',
        '# Diagnostic primary-room/pipe/player-position fixture; no damage-immunity writes.')
    return text+('''# Assisted position keeps Mario clear while the Koopa escapes to the left.
poke 94 58025000
wait 32
dump escaped_away
pokefor 94 04029000 2
# Final player-position write above. Ordinary input from here through the real return.
press right+y 150
dump upper_before
press right+y+b 24
dump upper_jump
press right+y 16
dump upper_after
press right+y 10
dump ledge_before
press left+y 6
dump brake
wait 16
dump stop
press right 6
dump creep
wait 8
dump pit
press up+right 16
dump vine_grab
press down 34
dump vine_down
press right 32
dump door_ready
press up 2
dump activated
wait 160
dump returned
wait 160
dump returned_later
quit
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for side in ('native', 'source'):
        write_verified(ARTIFACTS / (side+'.script'), script(side).encode())
    if args.prepare:
        print(ARTIFACTS, 'two immutable scripts')
        return
    require(args.output is not None and not args.output.exists(), 'supply a fresh report path')
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    verify(donor, json.loads((ROOT / 'config/7hero-donor.json').read_text())['output'], 'official7hero')
    relative = '../../local/probes/sprite95-trial5-route-v2/'
    a, ar = native('sprite95-trial5-route-native-v2', relative+'native.script',
                   {0x19B8: 1, 0x19D8: 1}, target=TARGET)
    b, br = reference_capture('sprite95-trial5-route-source-v2', relative+'source.script', donor)
    samples = {}

    def pair(tag, flags=None, fields=None):
        x, y = body(a, tag), body(b, tag)
        require(x[0x1497] == y[0x1497] == x[0x19] == y[0x19] == 0,
                'damage immunity or power-up active: '+tag)
        require(functional(x) == functional(y), 'functional mismatch: '+tag)
        require(x[0x1420:0x1423] == y[0x1420:0x1423], 'coin state differs: '+tag)
        if flags is not None:
            require(functional(x)['room'] == 0x172 and x[0x100] == 0x14 and
                    x[0x71] == x[0x1493] == x[0x1420] == x[0x1422] == 0 and
                    x[0x14AF] == flags and x[0x1FEAF] == 16, 'trial state differs: '+tag)
        if fields:
            require(normal_actors(x, fields) == normal_actors(y, fields), 'normal actor mismatch: '+tag)
        require(x[0x74] == y[0x74] and x[0x1470] == y[0x1470], 'climb/carry differs: '+tag)
        samples[tag] = dict(functional=functional(x), native_actors=normal_actors(x),
                            source_actors=normal_actors(y), compared_normal_fields=list(fields or ()),
                            climb=x[0x74], carry=x[0x1470], coins=[x[0x1420], x[0x1422]])
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
        require(actor(before, 8) == dict(id=0, status=8, x=x, y=160), 'Koopa event not reached')
        flags ^= 1 << (switch-1)
        pair(f'event{number:02}_hit', flags, fields)
        after = pair(f'event{number:02}_after', flags, fields)
        require(actor(after, 8) == dict(id=0, status=8, x=x+7, y=160), 'bridge crossing failed')
    for tag in ('approaching_shell', 'shell_entry', 'shell_later', 'stomp8'):
        pair(tag, 1, FIELDS)
    require(actor(body(a, 'shell_entry'), 9) == dict(id=4, status=8, x=499, y=160) and
            body(a, 'shell_entry')[0x14C8+8] == 0, 'real shell entry absent')
    require(actor(body(a, 'stomp8'), 9) == dict(id=4, status=9, x=537, y=160), 'real stomp absent')
    for tag in ROUTE:
        pair(tag, 1 if tag not in ('activated', 'returned', 'returned_later') else None, FIELDS)
    require(actor(body(a, 'escaped_away'), 8) == dict(id=0, status=8, x=471, y=160),
            'escaped Koopa history differs')
    require(body(a, 'upper_before')[0x1470] == 1, 'ordinary shell pickup/carry absent')
    require(int.from_bytes(body(a, 'upper_jump')[0x96:0x98], 'little') >= 0xFF00,
            'ordinary upper jump did not reach the expected window')
    vine = body(a, 'vine_grab')
    require(vine[0x74] != 0 and any(row[1] == 0x79 for row in normal_actors(vine)),
            'actual vine/climb interaction absent')
    ready = body(a, 'door_ready')
    require(ready[0x77] & 4 and (functional(ready)['x'], functional(ready)['y']) == (969, 96) and
            any(row[3] == 0x10 and row[4]+256*row[5] == 976 for row in actors(ready)),
            'actual final door not reached on foot')
    activated = body(a, 'activated')
    require(activated[0x71] == 6 and activated[0x14AF] == activated[0x1FEAF] == 16,
            'ordinary Up did not activate the saved-switch return')
    for tag in ('returned', 'returned_later'):
        data = body(a, tag)
        require(functional(data) == dict(mode=0x14, room=0x16E, action=0, x=208, y=688,
                                         flags=16, saved_switch=0, goal=0) and
                data[0x1420] == data[0x1422] == 1, 'real return/Dragon Coin absent')
    for directory in (a, b):
        initial = body(directory, 'trial')
        for tag in samples:
            current = body(directory, tag)
            require(current[0xDBE] == initial[0xDBE] and
                    current[0x1F2F:0x1F3B] == initial[0x1F2F:0x1F3B],
                    'unexpected life or saved five-coin flag change')
    report = dict(target=TARGET, checker_sha256=sha(Path(__file__).read_bytes()), samples=samples,
                  native_receipt=ar, source_receipt=br, module_usage=usage(a, 'A3'),
                  limits=['Room/pipe/hub/numbered-switch/stomp/escape/side-approach position fixtures remain; no immunity/actor/HP/velocity/switch/progress/completion/save writes.',
                          'After the final side-approach position, ordinary input carries/releases the shell, jumps via the upper corridor, climbs the generated vine and enters the real far door.',
                          'No unassisted whole trial, five-coin/save, audio/rendering or whole-engine parity claim.',
                          'First nine bridge events compare17 fields; later bridge/shell/route samples compare19 including animation.'])
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
