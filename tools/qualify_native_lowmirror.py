#!/usr/bin/env python3
"""Qualify corrected mapped-code banks, official sprite95 and unchanged r14 routes."""
import argparse
import json
from pathlib import Path
import re

from native_sprite_gap import packs
from prepare_native_lowmirror import PLAN, load, review
from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_world1_next_course import require, word
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r15'
PARENT = 'demo11-native-product-r14'
TAGS = ('entry', 'mid', 'motion', 'after')
CASES = {'08b': ('native-lowmirror-08b.script', {0x32}, '9B'),
         '155': ('native-lowmirror-155-held.script', {0x31}, '9A'),
         '087': ('native-lowmirror-087.script', {0x1E, 0x1F, 0x20}, '96'),
         '086': ('native-lowmirror-086.script', {0x1C, 0x1D}, '95')}


def state(directory, tag, source=False):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    vram = (directory / (tag + '.vram.bin')).read_bytes()
    require(len(body) == 0x20000 and len(vram) == 0x10000 and
            len(saved) == (0x800 if source else 0x8000), 'incomplete/wrong-size state dump')
    rows = []
    for i in range(12):
        if body[0x14C8 + i] and body[0x1AB10 + i] & 8:
            rows.append(dict(slot=i, sprite=body[0x9E + i], custom=body[0x1AB9E + i],
                             status=body[0x14C8 + i], x=body[0xE4 + i] | body[0x14E0 + i] << 8,
                             y=body[0xD8 + i] | body[0x14D4 + i] << 8,
                             vx=body[0xB6 + i], vy=body[0xAA + i],
                             state1504=body[0x1504 + i], state151C=body[0x151C + i]))
    return body, dict(mode=body[0x100], room=word(body, 0x10B), lives=body[0xDBE],
                      player_x=word(body, 0x94), player_y=word(body, 0x96),
                      guest_frame=body[0x14], actors=rows,
                      wram_sha256=sha(body), sram_sha256=sha(saved), vram_sha256=sha(vram))


def rows(sample, ids):
    return [r for r in sample['actors'] if r['custom'] in ids]


def usage(directory, bank=None):
    matches = re.findall(r'\[native-seven\] bank=([0-9A-F]+) resolutions=(\d+) executed_page_instructions=(\d+)',
                         (directory / 'run.log').read_text())
    counts = {b: dict(resolutions=int(r), executed_page_instructions=int(e)) for b, r, e in matches}
    if bank:
        require(bank in counts and all(n > 0 for n in counts[bank].values()), 'module not exercised: ' + bank)
    return counts


def capture_native(name, script, target=TARGET, funded=False):
    extras = {0x19B8: 1, 0x19D8: 1}
    if script == 'native-lowmirror-087.script':
        extras[0x13] = 2
    if funded:
        extras[0x11809] = 3
    return native(name, script, extras, target=target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='local/reports/native-lowmirror-r15-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    plan = load(PLAN)
    require(plan['candidate'] == TARGET and plan['parent'] == PARENT, 'wrong reviewed target')
    admission = review(plan)
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'native candidate')
    mappings = packs(TARGET)
    require(len(mappings) == 48 and all(int(p['address'], 16) >> 16 & 0x7F < 0x40
                                     for p in mappings if p['executable']),
            'an executable mapping lacks low WRAM/IO mirrors')
    for p in mappings:
        verify((ROOT / 'local/restoration' / TARGET / p['pack_file']).read_bytes(), p, 'native pack')
    preparation_path = ROOT / 'local/restoration' / TARGET / 'lowmirror-review.json'
    preparation = load(preparation_path)
    require(preparation['plan'] == plan and preparation['review'] == admission and
            all(sha((ROOT / path).read_bytes()) == digest for path, digest in preparation['files'].items()),
            'preparation receipt no longer matches its actual sources')
    cheap = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    verify(cheap, load(ROOT / 'config/cheap-demo-donor.json')['output'], 'official cheap_demo')
    cases = {}
    for room, (script, ids, bank) in CASES.items():
        version = 'v2' if room == '087' else 'v1'
        a, ar = capture_native(f'low-r15-{room}-native-{version}', script)
        b, br = reference_capture(f'low-r15-{room}-cheap-{version}', script, cheap)
        pairs = {}
        for tag in TAGS:
            x, s = state(a, tag)
            y, t = state(b, tag, True)
            require(s['mode'] == t['mode'] == 0x14 and s['room'] == t['room'] == int(room, 16) and
                    s['lives'] == t['lives'] == 4, 'wrong live room/life: ' + room + '/' + tag)
            require((s['player_x'], s['player_y']) == (t['player_x'], t['player_y']),
                    'player position mismatch: ' + room + '/' + tag)
            require(rows(s, ids) == rows(t, ids), 'selected actor state mismatch: ' + room + '/' + tag)
            pairs[tag] = dict(native=s, source=t, compared_custom_ids=[f'{i:02X}' for i in sorted(ids)])
        require(pairs['entry']['native']['guest_frame'] != pairs['after']['native']['guest_frame'],
                'native simulation did not advance')
        require(rows(pairs['entry']['native'], ids), 'required actor never materialized')
        cases[room] = dict(native_receipt=ar, source_receipt=br, samples=pairs, usage=usage(a, bank),
                           clock_fixture='Global13/14 reset to zero after entry.' if room == '087' else None)
    controls = {}
    for room in ('08b', '155'):
        script, ids, _ = CASES[room]
        directory, receipt = capture_native(f'low-r14-{room}-native-v1', script, PARENT)
        samples = {tag: state(directory, tag)[1] for tag in TAGS}
        require(all(s['mode'] == 0x14 and s['room'] == int(room, 16) and s['lives'] == 4
                    for s in samples.values()), 'parent control did not remain active')
        if room == '08b':
            require(all(len(rows(s, ids)) == 1 for s in samples.values()) and
                    len(rows(cases[room]['samples']['motion']['native'], ids)) == 2,
                    'parent child-generation defect no longer reproduced')
        else:
            require(all([(r['x'], r['y']) for r in rows(s, ids)] == [(544, 320)]
                        for s in samples.values()), 'parent stationary-actor control differs')
            require(rows(cases[room]['samples']['entry']['native'], ids)[0]['x'] != 544 and
                    not rows(cases[room]['samples']['after']['native'], ids),
                    'corrected actor did not move and leave the sample window')
        controls[room] = dict(receipt=receipt, samples=samples, usage=usage(directory))
    seven = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    verify(seven, load(ROOT / 'config/7hero-donor.json')['output'], 'official equivalent behavior source')
    a, ar = capture_native('low-r15-95-native-v1', 'native-sprite95-16b-held.script')
    b, br = reference_capture('low-r15-95-7hero-v1', 'native-sprite95-source-held.script', seven)
    old95, old95_receipt = capture_native('low-r14-95-native-v1', 'native-sprite95-16b-held.script', PARENT)
    sprite95 = {}
    for tag in TAGS:
        _, s = state(a, tag)
        _, t = state(b, tag, True)
        _, p = state(old95, tag)
        require(s['mode'] == t['mode'] == p['mode'] == 0x14 and s['room'] == t['room'] == p['room'] == 0x16B,
                'sprite95 room not active')
        require(s['lives'] == p['lives'] == 4 and t['lives'] == 19 and
                len(rows(s, {0x95})) == len(rows(t, {0x95})) == 1 and
                rows(s, {0x95}) == rows(t, {0x95}) and not rows(p, {0x95}),
                'new/source95 behavior or parent missing-record control differs')
        sprite95[tag] = dict(native=s, source=t, parent=p,
                            limits='Only sprite95 is compared; the source entry context/life pool and actor8C behavior differ.')
    sprite95_result = dict(native_receipt=ar, source_receipt=br, parent_receipt=old95_receipt,
                           samples=sprite95, usage=usage(a, 'A3'))
    regressions = {}
    for route, script, baseline in (
            ('normal', 'forest-hollow-normal-save.script', 'forest-a2-r14-normal-v1'),
            ('menu', 'forest-a2-menu-return.script', 'forest-a2-r14-menu-v1'),
            ('purchase', 'forest-a2-funded-purchase-save.script', 'forest-a2-r14-purchase-v1')):
        a, ar = capture_native('low-r15-reg-' + route + '-v1', script, funded=route == 'purchase')
        b, br = capture_native(baseline, script, PARENT, funded=route == 'purchase')
        tags = [line.split()[1] for line in (ROOT / 'recomp/inputs' / script).read_text().splitlines()
                if line.startswith('dump ')]
        samples = {}
        for tag in tags:
            samples[tag] = {}
            for suffix in ('wram.bin', 'sram.bin', 'vram.bin'):
                x, y = (a / (tag + '.' + suffix)).read_bytes(), (b / (tag + '.' + suffix)).read_bytes()
                require(x == y, 'unchanged r14 route differs: ' + route + '/' + tag + '/' + suffix)
                samples[tag][suffix] = dict(size=len(x), sha256=sha(x))
        require(all(v['resolutions'] == v['executed_page_instructions'] == 0
                    for bank, v in usage(a).items() if bank != '9D'), 'regression route uses a changed module')
        regressions[route] = dict(native_receipt=ar, parent_receipt=br, samples=samples, usage=usage(a))
    report = dict(target=TARGET, rom_sha256=sha(rom), parent=PARENT,
                  checker_sha256=sha(Path(__file__).read_bytes()), plan_sha256=sha(PLAN.read_bytes()),
                  preparation_sha256=sha(preparation_path.read_bytes()), admission=admission,
                  source_actor_cases=cases, parent_defect_controls=controls, sprite95=sprite95_result,
                  unchanged_r14_routes=regressions,
                  limits=['Position/primary-destination/pipe/immunity and held-position fixtures are explicit; no actor or clear writes.',
                          'Selected actor identity/status/XY/velocity and1504/151C tables only; no full source-engine or animation parity.',
                          'Room087 uses an explicit global13/14 phase fixture. The unphased late-fall sample has a9-pixel Y difference; full physics/timing parity is not qualified.',
                          'Slot95 is restored for seven placed rooms; new functional capture covers16B only.',
                          'C0/C1 compatible mapping is static admission; probes did not execute those callback views.',
                          'Diagnostic0A2 entry stalls before module execution,15D fixture does not instantiate2D, and160/05B trajectories differ; no runtime acceptance for those paths.',
                          'C2, complete courses/bosses, source8C differences, other95 rooms and visible/audio acceptance remain open.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()
