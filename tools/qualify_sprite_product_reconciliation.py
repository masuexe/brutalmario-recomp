#!/usr/bin/env python3
"""Qualify three recovered cumulative sprite programs and retained native features."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from audit_native_sprite_placements import audit as placement_audit
from prepare_rom import verify
from prepare_sprite_product_reconciliation import PLAN, ROOT, TARGET, load, review
from qualify_forest_a2 import native
from qualify_forest_course_identity import sprite_list
from qualify_forest_shack import protected_stream, reference_capture
from qualify_native_lowmirror import state, usage
from qualify_seven_child import FIELDS
from qualify_sprite95_rooms import body, functional, script as room_script
from qualify_world1_next_course import require
from restore_star_world_1 import sha, write_verified

ARTIFACTS = ROOT / 'local/probes/sprite-product-v2'
ROOMS = {'25': 0x154, '33': 0x0FE, '94': 0x0EF}
TAGS = ('entered', 'held', 'f001', 'f016', 'f032', 'f064', 'f128', 'f256', 'f512')
PARENT = 'demo11-native-seven-product-v1'
REGRESSIONS = (
    ('trial5', 'sprite95-trial5-route-native-v2', '../../local/probes/sprite95-trial5-route-v2/native.script', {}),
    ('child', 'seven-product-child-native-v1', 'seven-child-native-event.script', {0xD7E2: 1}),
    ('purchase', 'seven-product-reg-purchase-v1', 'forest-a2-funded-purchase-save.script', {0x11809: 3}),
    ('c2', 'seven-product-reg-c2-v1', 'native-type3-c2-direction.script', {0x13: 2}),
    ('mushroom', 'seven-product-ending-mushroom-v1', 'seven-ending-mushroom-native.script',
     {0xD7E2: 1, 0x1531: 1, 0x1FF00: 2}),
)


def script(side, slot):
    text = room_script(side, 'idle-16c').split('dump entered\n')[0]
    room = ROOMS[slot]
    text = text.replace('poke 19b8 6c', f'poke 19b8 {room & 255:02x}').replace(
        'until 010b == 6c', f'until 010b == {room & 255:02x}')
    flag = (5 if side == 'native' else 1) if room >= 256 else 4
    text = re.sub(r'poke 19d8 [0-9a-f]+', f'poke 19d8 {flag:02x}', text)
    text = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))+'\n'
    text = ('# Diagnostic map/primary-room/pipe/immunity/player-position fixture.\n'
            '# No actor, HP, switch, progression, completion or save writes.\n'+text)
    xy = '2000a000' if slot == '25' else '80004001'
    text += f'dump entered\nforcepoke 1497 ff\npokefor 94 {xy} 1\ndump held\n'
    elapsed = 0
    for frame in (1, 16, 32, 64, 128, 256, 512):
        text += f'wait {frame-elapsed}\ndump f{frame:03}\n'
        elapsed = frame
    return text+'quit\n'


def actors(data, slot):
    return [(i, *(data[at+i] for at in FIELDS)) for i in range(12)
            if data[0x14C8+i] and data[0x1AB10+i] & 8 and data[0x1AB9E+i] == int(slot, 16)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for slot in ROOMS:
        for side in ('native', 'source'):
            write_verified(ARTIFACTS / f'{side}-{slot}.script', script(side, slot).encode())
    if args.prepare:
        print(ARTIFACTS, 'six immutable scripts; native scripts also drive parent controls')
        return
    require(args.output is not None and not args.output.exists(), 'supply a fresh report path')
    admission = review()
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, load(ROOT / 'config/restorations' / (TARGET+'.json'))['output'], 'native candidate')
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    programs = {}
    for slot, room in ROOMS.items():
        selected = admission['programs'][slot]
        verify((ROOT / 'local/restoration' / TARGET / selected['pack']['pack_file']).read_bytes(),
               selected['pack'], 'installed program')
        require(rom[selected['record_offset']:selected['record_offset']+16].hex() == selected['after'],
                'installed record differs')
        relative = '../../local/probes/sprite-product-v2/'
        a, ar = native(f'sprite-product-{slot}-native-v2', relative+f'native-{slot}.script',
                       {0x19B8: 1, 0x19D8: 1}, target=TARGET)
        b, br = reference_capture(f'sprite-product-{slot}-source-v2', relative+f'source-{slot}.script', donor)
        c, cr = native(f'sprite-product-{slot}-parent-v2', relative+f'native-{slot}.script',
                       {0x19B8: 1, 0x19D8: 1}, target=PARENT)
        snapshots = {}
        for tag in TAGS:
            x, y, z = body(a, tag), body(b, tag), body(c, tag)
            require(functional(x) == functional(y) and functional(x)['room'] == room and
                    x[0x100] == 0x14 and x[0x71] != 9, 'live room/player mismatch: '+slot+'/'+tag)
            require(actors(x, slot) == actors(y, slot) and len(actors(x, slot)) == (2 if slot == '94' else 1),
                    'selected actor state mismatch: '+slot+'/'+tag)
            require(not actors(z, slot), 'parent no longer demonstrates the missing custom program')
            snapshots[tag] = dict(functional=functional(x), actors=actors(x, slot),
                                  parent_functional=functional(z), parent_actors=actors(z, slot))
        if slot == '25':
            require(actors(body(a, 'entered'), slot)[0][6:8] == (240, 0) and
                    actors(body(a, 'f512'), slot)[0][6:8] == (111, 0), 'actual25 ascent absent')
        elif slot == '33':
            require(actors(body(a, 'entered'), slot)[0][4] == 208 and
                    actors(body(a, 'f256'), slot)[0][4] == 133 and
                    functional(body(a, 'f256'))['x'] > functional(body(a, 'held'))['x'],
                    'actual33 horizontal/player movement absent')
        else:
            ys = {rows['actors'][1][6]+256*rows['actors'][1][7] for rows in snapshots.values()}
            phases = {rows['actors'][1][2] for rows in snapshots.values()}
            require(len(ys) >= 5 and phases == {0, 1}, 'actual94 motion/state cycle absent')
        layouts = {}
        for table, label in ((0x05E000, 'foreground'), (0x05E600, 'background')):
            raw, pin = protected_stream(rom, table, room)
            require(raw == protected_stream(donor, table, room)[0], 'bounded room allocation differs')
            layouts[label] = pin
        placements = sprite_list(rom, room)
        require(placements == sprite_list(donor, room), 'sprite placements differ')
        layouts['sprites'] = dict(size=len(placements), sha256=sha(placements))
        programs[slot] = dict(native_receipt=ar, source_receipt=br, parent_receipt=cr,
                             samples=snapshots, layouts=layouts, module_usage=usage(a, selected['pack']['address'][:2]))
    regressions = {}
    for key, baseline, input_script, extras in REGRESSIONS:
        allowed = {0x19B8: 1, 0x19D8: 1, **extras}
        a, ar = native(f'sprite-product-reg-{key}-v1', input_script, allowed, target=TARGET)
        b, br = native(baseline, input_script, allowed, target=PARENT)
        tags = [line.split()[1] for line in (ROOT / 'recomp/inputs' / input_script).read_text().splitlines()
                if line.startswith('dump ')]
        overwritten = {tag: count for tag, count in Counter(tags).items() if count > 1}
        require(overwritten == ({'activated': 2} if key == 'trial5' else {}),
                'unexpected repeated dump tags')
        # The inherited trial5 fixture uses activated at both doors. Its file
        # contains the far-door sample only; do not count the overwritten hub.
        tags = list(dict.fromkeys(tags))
        snapshots = {}
        for tag in tags:
            state(a, tag)
            state(b, tag)
            snapshots[tag] = {}
            for suffix in ('wram.bin', 'sram.bin', 'vram.bin'):
                x, y = (a / (tag+'.'+suffix)).read_bytes(), (b / (tag+'.'+suffix)).read_bytes()
                require(x == y, 'retained feature regression differs: '+key+'/'+tag+'/'+suffix)
                snapshots[tag][suffix] = dict(size=len(x), sha256=sha(x))
        regressions[key] = dict(native_receipt=ar, parent_receipt=br, samples=snapshots,
                               overwritten_tags=overwritten)
    result = dict(target=TARGET, admission=admission, plan_sha256=sha(PLAN.read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()), programs=programs, regressions=regressions,
                  native_placement_census=placement_audit(TARGET),
                  limits=['Room/pipe/immunity/player-position fixtures qualify selected behavior, not ordinary full rooms, exits or earned boss wins.',
                          'All27 source pairs compare19 actor fields plus slot and functional player state. Parent controls demonstrate the prior absence.',
                          'Five complete-state parent regressions retain already-qualified features; no new source-engine, visible/audio or whole-game claim.',
                          'Inherited trial5 activated is emitted twice: only the final far-door file survives and is compared/counts once.',
                          'Ending mushroom regression uses the existing explicit final-tier/damage fixture; no earned Seven victory/save claim.'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
