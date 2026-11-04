#!/usr/bin/env python3
"""Qualify the seven reviewed sprite records that product r20 adds.

The checker reads the r20 image and its packs, recomputes the placement census
on r20 and on its r19 parent, and reads one native capture per room. It
requires the parent to hold no actor for the selected slot and the candidate to
hold the expected motion.

The room 174 fixture needs BM_SEVEN_RETURN=0. The Seven return hook moves that
room to the overworld before gameplay.
"""
import argparse
import json
from pathlib import Path

from audit_native_sprite_placements import audit as placement_audit
from prepare_rom import verify
from qualify_sprite95_rooms import body, functional
from qualify_world1_next_course import require
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
BASE = 'demo11-native-product-r19'
TARGET = 'demo11-native-product-r20'
EXPECTED_SLOTS = {'96': ['1F0'], 'A5': ['056', '102'], 'A6': ['00C'],
                  'E8': ['111', '119'], 'E9': ['1CF'], 'EA': ['1F3'],
                  'F5': ['1E2']}
MERGED = {'25', '33', '94', '97', '99', 'A1', 'C2'}
TAGS = ('entered', 'f001', 'f016', 'f032', 'f064', 'f128', 'f256', 'f512')


def actors(data, slot):
    """Return (slot, state, x, y) for one slot in a WRAM sample."""
    rows = []
    for index in range(12):
        if (data[0x14C8+index] and data[0x1AB10+index] & 8
                and data[0x1AB9E+index] == slot):
            rows.append(dict(slot=index, state=data[0x1504+index],
                             x=data[0xE4+index]+256*data[0x14E0+index],
                             y=data[0xD8+index]+256*data[0x14D4+index]))
    return rows


def rows(directory, tag, slot):
    data = body(ROOT / 'local/captures' / directory, tag)
    return functional(data), actors(data, int(slot, 16))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report path')
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    base_cfg = json.loads((ROOT / 'config/restorations' / (BASE + '.json')).read_text())
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'sprite merge candidate')
    verify(base, base_cfg['output'], 'sprite merge parent')

    candidate = placement_audit(TARGET)
    parent = placement_audit(BASE)
    require(candidate['rom_sha256'] == cfg['output']['sha256'], 'census candidate differs')
    require(candidate['placeholder_slots'] == EXPECTED_SLOTS, 'candidate placeholder set differs')
    require(set(parent['placeholder_slots']) - set(candidate['placeholder_slots']) == MERGED,
            'merge delta differs')
    require(set(parent['placeholder_slots']) == MERGED | set(EXPECTED_SLOTS),
            'parent placeholder set differs')

    evidence = {}
    for room, slot, candidate_capture, parent_capture, tags in (
            ('154', '25', 'product-r20-room154-native-v1', 'product-r19-room154-control-v1',
             ('r1', 'r2', 'r3')),
            ('0EF', '94', 'product-r20-room0EF-native-v1', 'product-r19-room0EF-control-v1',
             ('r1', 'r2', 'r3')),
            ('0FE', '33', 'product-r20-room0FE-native-v1', 'product-r19-room0FE-control-v1',
             ('r1', 'r2', 'r3')),
            ('174', '99', 'product-r20-room174-native-v2', 'product-r19-room174-control-v2', TAGS),
            ('175', '99', 'product-r20-room175-native-v1', 'product-r19-room175-control-v1',
             ('entered', 'f256')),
            ('175', 'A1', 'product-r20-room175-native-v1', 'product-r19-room175-control-v1',
             ('entered', 'f256')),
            ('176', 'A1', 'product-r20-room176-native-v1', 'product-r19-room176-control-v1', TAGS),
            ('178', 'A1', 'product-r20-room178-native-v1', 'product-r19-room178-control-v1', TAGS),
            ('1EF', '97', 'product-r20-route1EF-native-v1', 'product-r19-route1EF-control-v1',
             ('entered', 'f032', 'f256'))):
        record = dict(room=room, slot=slot, candidate=candidate_capture,
                      parent=parent_capture, samples={})
        for tag in tags:
            cstate, crows = rows(candidate_capture, tag, slot)
            pstate, prows = rows(parent_capture, tag, slot)
            require(cstate['room'] == int(room, 16), 'candidate room differs: '+room+'/'+tag)
            if crows:
                require(cstate['mode'] in (0x13, 0x14), 'candidate is not in a room: '+room+'/'+tag)
            require(not prows, 'parent now holds the custom actor: '+room+'/'+tag)
            record['samples'][tag] = dict(state=cstate, candidate=crows, parent=prows)
        require(record['samples'][tags[0]]['candidate'], 'candidate has no actor: '+room)
        evidence[room+'/'+slot] = record

    first = evidence['154/25']
    ys = [first['samples'][tag]['candidate'][0]['y'] for tag in ('r1', 'r2', 'r3')]
    require(ys == sorted(ys, reverse=True) and ys[0] > ys[-1], 'sprite 25 does not rise')
    second = evidence['0EF/94']
    require(len(second['samples']['r1']['candidate']) == 2, 'sprite 94 actor count differs')
    require({row['y'] for row in second['samples']['r1']['candidate']} == {224} and
            max(row['y'] for row in second['samples']['r2']['candidate']) == 320,
            'sprite 94 Y motion differs')
    xs = [evidence['0FE/33']['samples'][tag]['candidate'][0]['x'] for tag in ('r1', 'r2', 'r3')]
    require(xs[0] == 208 and xs[-1] == 133, 'sprite 33 X motion differs')
    require([row['x'] for row in evidence['175/99']['samples']['entered']['candidate']] ==
            [290, 207, 143], 'sprite 99 positions differ')
    require([(row['x'], row['y']) for row in evidence['176/A1']['samples']['entered']['candidate']] ==
            [(64, 256)] and
            [row['x'] for row in evidence['176/A1']['samples']['f256']['candidate']] == [369] and
            not evidence['176/A1']['samples']['f512']['candidate'], 'A1 room 176 motion differs')
    require([row['y'] for row in evidence['178/A1']['samples']['f128']['candidate']] == [146] and
            [row['y'] for row in evidence['178/A1']['samples']['f256']['candidate']] == [271],
            'A1 room 178 motion differs')
    require([(row['x'], row['y']) for row in evidence['1EF/97']['samples']['f256']['candidate']] ==
            [(192, 368)], 'sprite 97 position differs')

    c2_state, c2_rows = rows('product-r20-room170-native-v1', 'r2', '95')
    _p2_state, p2_rows = rows('product-r19-room170-control-v2', 'r2', '95')
    generated = [row for row in c2_rows if row['state'] == 0x0F]
    require(c2_state['room'] == 0x170 and len(generated) == 2, 'C2 generated actor count differs')
    require(not p2_rows, 'parent now generates C2 actors')

    report = dict(target=TARGET, parent=BASE,
                  rom_sha256=candidate['rom_sha256'], parent_rom_sha256=parent['rom_sha256'],
                  packs=len(candidate['packs']),
                  candidate_placeholders=candidate['placeholder_slots'],
                  parent_placeholders=parent['placeholder_slots'],
                  merged_slots=sorted(MERGED), c2_generated=generated,
                  samples={key: dict(room=value['room'], slot=value['slot'],
                                     candidate=value['candidate'], parent=value['parent'],
                                     states={tag: value['samples'][tag]['state'] for tag in value['samples']},
                                     actors={tag: value['samples'][tag]['candidate'] for tag in value['samples']})
                           for key, value in evidence.items()},
                  checker_sha256=sha(Path(__file__).read_bytes()),
                  scope=__doc__.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps({'report': str(args.output), 'rom_sha256': candidate['rom_sha256'],
                      'merged': sorted(MERGED),
                      'remaining_placeholders': sorted(EXPECTED_SLOTS)}, indent=2))


if __name__ == '__main__':
    main()
