#!/usr/bin/env python3
"""Generate immutable Sprite95 fixtures and qualify current six-room/door behavior."""
import argparse
import json
from pathlib import Path

from audit_star_boss_donors import sprite_table
from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_course_identity import sprite_list
from qualify_forest_shack import protected_stream, reference_capture
from qualify_native_lowmirror import usage
from qualify_seven_child import FIELDS
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha, write_verified

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-seven-product-v1'
ARTIFACTS = ROOT / 'local/probes/sprite95-rooms-v1'
ROOMS = (0x16C, 0x16D, 0x16E, 0x16F, 0x172, 0x1CC)
CASES = {f'idle-{r:03x}': r for r in ROOMS}
CASES.update(hub=0x16E, **{f'door-{i}': 0x16E for i in range(1, 6)})
TAGS = ('entered', 'f001', 'f016', 'f032', 'f064', 'f128', 'f256')


def script(side, case):
    template = 'native-sprite95-16b-held.script' if side == 'native' else 'native-sprite95-source-held.script'
    text = (ROOT / 'recomp/inputs' / template).read_text().split('pokefor 94', 1)[0]
    # Keep exact boot/entry commands; replace misleading inherited comments.
    text = '\n'.join(line for line in text.splitlines() if not line.startswith('#'))+'\n'
    room = CASES[case]
    text = text.replace('poke 19b8 6b', f'poke 19b8 {room & 255:02x}').replace(
        'until 010b == 6b', f'until 010b == {room & 255:02x}')
    text = ('# Diagnostic primary-room/pipe/immunity/player-position fixture.\n'
            '# No actor, HP, progression, completion or save writes.\n'
            '# Door cases test ordinary Up after assisted loading, not trial completion.\n'+text)
    text += 'dump entered\nforcepoke 1497 ff\n'
    if case.startswith('idle-'):
        elapsed = 0
        for frame in (1, 16, 32, 64, 128, 256):
            text += f'wait {frame-elapsed}\ndump f{frame:03}\n'
            elapsed = frame
    else:
        for y in range(64, 545, 4):
            text += 'poke 94 7000'+y.to_bytes(2, 'little').hex()+'\n'
            if y in (256, 400, 480, 544):
                text += f'dump y{y}\n'
        text += 'pokefor 94 70001002 30\ndump doors\n'
        if case.startswith('door-'):
            x = (16, 64, 112, 160, 208)[int(case[-1])-1]
            text += (f'pokefor 94 {x.to_bytes(2, "little").hex()}1002 10\ndump before_up\n'
                     'press up 2\ndump activated\nwait 160\ndump trial\n'
                     'wait 160\ndump trial_later\n')
    return text+'quit\n'


def prepare():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        for side in ('native', 'source'):
            write_verified(ARTIFACTS / f'{side}-{case}.script', script(side, case).encode())


def capture(case, side, donor):
    path = ARTIFACTS / f'{side}-{case}.script'
    relative = '../../'+str(path.relative_to(ROOT))
    name = f'sprite95-rooms-{case}-{side}-v1'
    if side == 'native':
        return native(name, relative, {0x19B8: 1, 0x19D8: 1}, target=TARGET)
    return reference_capture(name, relative, donor)


def body(directory, tag):
    data = (directory / (tag+'.wram.bin')).read_bytes()
    require(len(data) == 0x20000 and (directory / (tag+'.vram.bin')).stat().st_size == 0x10000,
            'incomplete sample')
    return data


def actors(data, slots=True):
    rows = [(i, *(data[at+i] for at in FIELDS)) for i in range(12)
            if data[0x14C8+i] and data[0x1AB10+i] & 8 and data[0x1AB9E+i] == 0x95]
    return rows if slots else sorted(row[1:] for row in rows)


def placements(data):
    return sorted(data[i:i+3] for i in range(1, len(data)-1, 3))


def functional(data):
    return dict(mode=data[0x100], room=int.from_bytes(data[0x10B:0x10D], 'little'), action=data[0x71],
                x=int.from_bytes(data[0x94:0x96], 'little'), y=int.from_bytes(data[0x96:0x98], 'little'),
                flags=data[0x14AF], saved_switch=data[0x1FEAF], goal=data[0x1493])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    prepare()
    if args.prepare:
        print(ARTIFACTS, len(CASES)*2, 'immutable scripts')
        return
    require(args.output is not None and not args.output.exists(), 'supply a fresh output path')
    recipe = json.loads((ROOT / 'config/native-content/sprite95-boss-module.json').read_text())
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET+'.json')).read_text())
    verify(rom, cfg['output'], 'current native candidate')
    source = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    source_versions = {}
    for version in ('boss', '7hero'):
        donor = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        pin = json.loads((ROOT / 'config' / (version+'-donor.json')).read_text())
        verify(donor, pin['output'], 'official '+version)
        at = lorom(sprite_table(donor)[2])+0x95*16
        require(donor[at:at+16].hex() == recipe['record']['raw'], 'official95 record differs')
        offset = lorom(0x20E40B)
        verify(donor[offset:offset+5144], recipe['code'], 'official95 protected program')
        source_versions[version] = sha(donor)
    verify((ROOT / 'local/restoration' / TARGET / 'sprite95-code.bin').read_bytes(), recipe['code'], 'native95 program')
    offset = lorom(sprite_table(rom)[2])+0x95*16
    require(rom[offset:offset+16].hex() == recipe['record']['native_raw'], 'native95 mapping differs')
    layouts = {}
    for room in ROOMS:
        layouts[f'{room:03X}'] = {}
        placed, source_placed = sprite_list(rom, room), sprite_list(source, room)
        require(placed[0] == source_placed[0] and placements(placed) == placements(source_placed),
                'sprite placement/header differs')
        require(placed == source_placed or room == 0x16E, 'unexpected sprite-list reordering')
        layouts[f'{room:03X}']['sprites'] = dict(native_sha256=sha(placed), source_sha256=sha(source_placed),
                                               size=len(placed), exact_order=placed == source_placed,
                                               placement_multiset_equal=True)
        for table, label in ((0x05E000, 'foreground'), (0x05E600, 'background')):
            if room == 0x1CC and label == 'background':
                # No immediate STAR allocation at this pointer: do not use an
                # unbounded object scan or claim complete L2 identity.
                layouts[f'{room:03X}'][label] = 'No bounded STAR identity claimed.'
                continue
            raw, pin = protected_stream(rom, table, room)
            require(raw == protected_stream(source, table, room)[0], 'room allocation differs')
            layouts[f'{room:03X}'][label] = pin
    results = {}
    for case, room in CASES.items():
        a, ar = capture(case, 'native', source)
        b, br = capture(case, 'source', source)
        snapshots = {}
        if case.startswith('idle-'):
            for tag in TAGS:
                x, y = body(a, tag), body(b, tag)
                require(functional(x) == functional(y) and functional(x)['room'] == room and
                        x[0x100] == 0x14 and x[0x71] == 0, 'live room state differs: '+case+'/'+tag)
                require(actors(x) == actors(y), '95 selected state differs: '+case+'/'+tag)
                require(bool(actors(x)) == (room != 0x16E), 'unexpected idle95 coverage')
                snapshots[tag] = dict(functional=functional(x), actors=actors(x), layer2_y=int.from_bytes(x[0x1468:0x146A], 'little'))
                if room == 0x16F:
                    require(x[0x1468:0x146A] == y[0x1468:0x146A], 'layer2 motion differs')
            if room == 0x16C:
                require(any(row[3] == 6 for row in actors(body(a, 'f128'))), 'actual phase6 child absent')
            if room == 0x16F:
                require(len({s['layer2_y'] for s in snapshots.values()}) >= 5, 'layer2 did not move/cycle')
        else:
            for tag in ('y400', 'y480', 'y544', 'doors'):
                x, y = body(a, tag), body(b, tag)
                require(functional(x) == functional(y) and x[0x100] == 0x14 and x[0x71] == 0 and
                        actors(x, False) == actors(y, False) and actors(x), 'hub loading/state mismatch')
                snapshots[tag] = dict(functional=functional(x), actors=actors(x, False))
            require(len(actors(body(a, 'doors'))) == 6, 'five doors plus return not materialized')
            if case.startswith('door-'):
                number = int(case[-1])
                destination = (0x150, 0x16F, 0x170, 0x171, 0x172)[number-1]
                for tag in ('before_up', 'activated', 'trial', 'trial_later'):
                    x, y = body(a, tag), body(b, tag)
                    require(functional(x) == functional(y), 'actual door function differs: '+case+'/'+tag)
                    observed = functional(x)
                    if tag == 'before_up':
                        require(observed['room'] == 0x16E and observed['flags'] == 0 and x[0x77] & 4, 'door fixture not grounded/unvisited')
                    elif tag == 'activated':
                        require(observed['action'] == 6 and observed['flags'] == 1 << (number-1), 'game did not activate/mark selected door')
                    else:
                        require(observed['room'] == destination and observed['mode'] == 0x14 and observed['action'] == 0,
                                'trial entry not live')
                        require(observed['flags'] == (0 if number == 5 else 1 << (number-1)) and
                                observed['saved_switch'] == (16 if number == 5 else 0), 'trial switch save differs')
                    snapshots[tag] = dict(functional=observed, native_actors=actors(x), source_actors=actors(y))
        executed = usage(a, 'A3' if case != 'idle-16e' else None)
        results[case] = dict(native_receipt=ar, source_receipt=br, samples=snapshots, module_usage=executed)
    report = dict(target=TARGET, rom_sha256=sha(rom), generator_checker_sha256=sha(Path(__file__).read_bytes()),
                  source_versions=source_versions, layouts=layouts, cases=results,
                  limits=['Explicit map/primary-room/pipe/immunity/held/gradual player-position fixtures; no actor, HP, progression, completion or save writes.',
                          'Five-door entries and source switch preservation only; no trial clears or Dragon Coin completion.',
                          'Idle1CC phaseD state is covered; attempted grounded/airborne Up fixtures did not activate it in either host.',
                          '172 beginning-door activation restores switch16 but loops into172 in both hosts; not a trial exit.',
                          '16E sprite-list placements match as a multiset but order differs; hub actor slots are normalized, not equated.',
                          '1CC background has no bounded identity here. Other actor families, full visible/audio/physics parity and whole courses remain open.'])
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(args.output, sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
