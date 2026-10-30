#!/usr/bin/env python3
"""Check cumulative Seven child birth, font lifecycle, ending fixture and regressions."""
import argparse
import json
from pathlib import Path

from prepare_seven_product import ROOT, PLAN, load, review
from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_native_lowmirror import state, usage
from qualify_seven_child import FIELDS
from qualify_world1_next_course import require
from restore_star_world_1 import sha

TARGET = 'demo11-native-seven-product-v1'
PARENT = 'demo11-native-type3-c2-v2'
EXTRAS = {0x19B8: 1, 0x19D8: 1, 0xD7E2: 1}


def body(directory, tag):
    data = (directory / (tag+'.wram.bin')).read_bytes()
    require(len(data) == 0x20000, 'incomplete WRAM dump')
    return data


def room(data):
    return int.from_bytes(data[0x10B:0x10D], 'little')


def position(data):
    return [int.from_bytes(data[at:at+2], 'little') for at in (0x94, 0x96)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    admission = review()
    donor = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
    japanese = load(ROOT / 'config/native-content/seven-font-module.json')['font_adaptation']['decoded']
    english = load(ROOT / 'config/native-content/seven-ending-1up.json')['font_lifecycle']['recipient_font']['decoded']
    a, ar = native('seven-product-child-native-v1', 'seven-child-native-event.script', EXTRAS, target=TARGET)
    b, br = reference_capture('seven-product-child-source-v1', 'seven-child-donor-event.script', donor)
    used = usage(a, '90')
    children = []
    for tag in ('child_spawn', 'child32', 'child96'):
        x, y = body(a, tag), body(b, tag)
        require(x[0x100] == y[0x100] == 0x14 and room(x) == room(y) == 0xFF, 'child sample escaped fight')
        for i in (6, 7):
            require(x[0x1AB9E+i] == 0xE0 and y[0x1AB9E+i] == 0x6A and
                    x[0x1AB10+i] & 8 and y[0x1AB10+i] & 8, 'child namespace differs')
            fields = [x[at+i] for at in FIELDS]
            require(fields == [y[at+i] for at in FIELDS] and x[0x9E+i] == 0x6A and
                    x[0xC2+i] == 0x15 and x[0x14C8+i] == 8, 'child selected state differs')
            children.append(dict(tag=tag, slot=i, fields=fields))
        require(x[0xDDA] == 0xAC, 'modern fight request differs')
        for directory in (a, b):
            verify((directory / (tag+'.vram.bin')).read_bytes()[0x9000:0x9800], japanese, 'fight Japanese font')
    before, death, returned, course, reentry = [body(a, tag) for tag in
        ('child96', 'child_death', 'child_map', 'child_course_reentry', 'child_fight_reentry')]
    require(death[0x71] == 9 and room(death) == 0xFF and returned[0x100] == 0x0E and
            returned[0xDBE]+1 == before[0xDBE], 'real death/map/life loss differs')
    require(course[0x100] == 0x14 and room(course) == 5 and reentry[0x100] == 0x14 and
            room(reentry) == 0xFF and reentry[0xDBE] == returned[0xDBE] and reentry[0xC2+9] == 0,
            'course/fight re-entry differs')
    for tag in ('child_map', 'child_course_reentry'):
        verify((a / (tag+'.vram.bin')).read_bytes()[0x9000:0x9800], english, 'restored English font')
    verify((a / 'child_fight_reentry.vram.bin').read_bytes()[0x9000:0x9800], japanese, 're-entry Japanese font')

    fixture_extras = {**EXTRAS, 0x1531: 1, 0x1FF00: 2}
    c, cr = native('seven-product-ending-v1', 'seven-ending-native-fixture.script', fixture_extras, target=TARGET)
    d, dr = reference_capture('seven-product-ending-source-v1', 'seven-ending-donor-fixture.script', donor)
    walks = []
    for directory, expected in ((c, 0x17B), (d, 0x174)):
        queued, late = body(directory, 'ending_queued'), body(directory, 'ending_late')
        require(room(queued) == 0xFF and queued[0xCB] == 0x15 and late[0x100] == 0x14 and
                room(late) == expected and position(late) == [16, 352], 'ending fixture transition differs')
        dying, mapped = body(directory, 'test_right10'), body(directory, 'test_after_death')
        require(dying[0x71] == 9 and position(dying) == [744, 456] and mapped[0x100] == 0x0E and
                mapped[0xDBE]+1 == dying[0xDBE], 'ending pit/map/life loss differs')
    for i in range(1, 11):
        tag = f'test_right{i:02}'
        require(position(body(c, tag)) == position(body(d, tag)), 'ending walk position differs')
        walks.append(dict(tag=tag, position=position(body(c, tag))))
    for tag in ('ending_late', 'test_after_death'):
        verify((c / (tag+'.vram.bin')).read_bytes()[0x9000:0x9800], english, 'ending English font')

    e, er = native('seven-product-ending-mushroom-v1', 'seven-ending-mushroom-native.script', fixture_extras, target=TARGET)
    f, fr = reference_capture('seven-product-mushroom-source-v1', 'seven-ending-mushroom-donor.script', donor)
    mushroom = []
    for directory, expected in ((e, 0x17B), (f, 0x174)):
        start = body(directory, 'mushroom_before')
        require(start[0xDBE] == body(directory, 'ending_late')[0xDBE], 'early unexplained life award')
        spawn = life = None
        for i in range(1, 81):
            sample = body(directory, f'mushroom{i:03}')
            require(sample[0x100] == 0x14 and room(sample) == expected and
                    sample[0xDBE] in (start[0xDBE], start[0xDBE]+1), 'mushroom route/lives differ')
            if spawn is None and any(sample[0x9E+j] == 0x78 and sample[0x14C8+j] == 8 for j in range(12)):
                spawn = i
            if life is None and sample[0xDBE] == start[0xDBE]+1:
                life = i
        mapped = body(directory, 'mushroom_map')
        require(spawn is not None and life is not None and life > spawn and
                mapped[0x100] == 0x0E and mapped[0xDBE] == start[0xDBE], 'mushroom birth/award/pit consumption absent')
        mushroom.append(dict(spawn=spawn, life=life, lives=[start[0xDBE], start[0xDBE]+1, mapped[0xDBE]]))
    require(all(mushroom[0][key] == mushroom[1][key] for key in ('spawn', 'life')),
            'hidden mushroom event timing differs')

    regressions = {}
    for name, capture, baseline, script, extras in (
        ('purchase', 'seven-product-reg-purchase-v1', 'type3-c2-reg-purchase-v1', 'forest-a2-funded-purchase-save.script', {0x11809: 3}),
        ('C2', 'seven-product-reg-c2-v1', 'type3-c2-direction-final-v1', 'native-type3-c2-direction.script', {0x13: 2}),
        ('16B', 'seven-product-reg-16b-v1', 'type3-c2-all16b-final-v1', 'native-type3-all16b.script', {0x13: 2}),
        ('original6A', 'seven-product-existing-0e4-v1', 'seven-product-parent-0e4-v1', 'seven-child-existing-0e4.script', {})):
        extras = {**EXTRAS, **extras}
        g, gr = native(capture, script, extras, target=TARGET)
        h, hr = native(baseline, script, extras, target=PARENT)
        samples = {}
        for line in (ROOT / 'recomp/inputs' / script).read_text().splitlines():
            if not line.startswith('dump '):
                continue
            tag = line.split()[1]
            state(g, tag)
            state(h, tag)
            samples[tag] = {}
            for suffix in ('wram.bin', 'sram.bin', 'vram.bin'):
                left, right = (g / (tag+'.'+suffix)).read_bytes(), (h / (tag+'.'+suffix)).read_bytes()
                require(left == right, 'unchanged route differs: '+name+'/'+tag+'/'+suffix)
                samples[tag][suffix] = sha(left)
        regressions[name] = dict(native_receipt=gr, parent_receipt=hr, samples=samples)
    result = dict(target=TARGET, admission=admission, plan_sha256=sha(PLAN.read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()), child=dict(native_receipt=ar,
                  source_receipt=br, usage=used, pairs=children),
                  ending=dict(native_receipt=cr, source_receipt=dr, walk=walks),
                  mushroom=dict(native_receipt=er, source_receipt=fr, events=mushroom), regressions=regressions,
                  limits=['Child birth/death/re-entry scripts use map and pipe fixtures, without actor/HP/clear writes.',
                          'Ending/mushroom fixtures explicitly inject final tier and damage; no earned victory or saved-clear claim.',
                          'Child19 fields and font/event boundaries only; no whole source-engine, screenshot or audible equality.',
                          'Other95 rooms, C0/late-C1 phase and complete courses/boss victories remain open.'])
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()
