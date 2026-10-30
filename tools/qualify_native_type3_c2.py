#!/usr/bin/env python3
"""Qualify official C2 generation, normal094 entry and all six16B shooters."""
import argparse
import json
from pathlib import Path

from prepare_native_type3_c2 import ROOT, TARGET, review
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_native_lowmirror import state, usage
from qualify_world1_next_course import require
from restore_star_world_1 import sha


def tags(script):
    result = [line.split()[1] for line in (ROOT / 'recomp/inputs' / script).read_text().splitlines()
              if line.startswith('dump ')]
    require(len(result) == len(set(result)), 'duplicate dump labels')
    return result


def paired(name, script):
    a, ar = native('type3-c2-'+name+'-final-v1', 'native-type3-'+script+'.script',
                   {0x19B8: 1, 0x19D8: 1, 0x13: 2}, target=TARGET)
    donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    b, br = reference_capture('type3-c2-source-'+name+'-final-v1',
                              'source-type3-'+script+'.script', donor)
    return a, ar, b, br


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    admission = review()
    a, ar, b, br = paired('direction', 'c2-direction')
    samples = {}
    for tag in ('approach_left', 'fire_left', 'left_1', 'left_7', 'left_24',
                'approach_right', 'fire_right', 'right_1', 'right_7', 'right_24'):
        x, xs = state(a, tag)
        y, ys = state(b, tag, source=True)
        require(xs['mode'] == ys['mode'] == 0x14 and xs['room'] == ys['room'] == 0x170 and
                x[0x71] == y[0x71] == x[0x9D] == y[0x9D] == 0, 'not live unfrozen170: '+tag)
        p = [r for r in xs['actors'] if r['custom'] == 0x95]
        q = [r for r in ys['actors'] if r['custom'] == 0x95]
        require(p == q and all(r['state1504'] == 15 for r in p), 'C2 generated actors differ: '+tag)
        require(x[0x1783:0x178B] == bytes(7)+bytes([0xB2]) and
                y[0x1783:0x178B] == bytes(7)+bytes([0x83]) and
                x[0x178B:0x17B3] == y[0x178B:0x17B3], 'C2 shooter state differs: '+tag)
        for row in p:
            i = row['slot']
            require([x[addr+i] for addr in (0x1656, 0x1662, 0x166E, 0x167A, 0x15AC)] ==
                    [y[addr+i] for addr in (0x1656, 0x1662, 0x166E, 0x167A, 0x15AC)],
                    'C2 child properties differ')
        if tag == 'fire_left':
            require(len(p) == 1 and (p[0]['x'], p[0]['y'], p[0]['vx']) == (368, 319, 240), 'left launch differs')
        if tag == 'fire_right':
            require(any((r['x'], r['y'], r['vx']) == (400, 319, 16) for r in p), 'right launch absent')
        samples[tag] = dict(native=xs, source=ys, generated=p, timer=x[0x17B2])
    used = usage(a, '91')
    usage(a, 'A3')

    p, pr = native('type3-c2-normal-entry-v1', 'native-type3-c2-normal-entry.script', {0xD7E2: 1}, target=TARGET)
    normal = {}
    for tag in ('entry0', 'entry16', 'entry48', 'entry240', 'entry600'):
        body, sample = state(p, tag)
        require(sample['mode'] == 0x14 and sample['room'] == 0x170 and body[0x71] == 0,
                'normal094 entry not live170: '+tag)
        if tag in ('entry48', 'entry240', 'entry600'):
            require(any(r['custom'] == 0x95 and r['state1504'] == 15 for r in sample['actors']),
                    'actual C2 child absent on normal entry')
        normal[tag] = sample
    usage(p, '91')

    c, cr, d, dr = paired('all16b', 'all16b')
    all_samples = {}
    last_positions = None
    for tag in tags('native-type3-all16b.script'):
        if not (tag.startswith('x') or tag.startswith('last_') or tag == 'end'):
            continue
        x, xs = state(c, tag)
        y, ys = state(d, tag, source=True)
        require(xs['mode'] == ys['mode'] == 0x14 and xs['room'] == ys['room'] == 0x16B and
                x[0x71] == y[0x71] == 0, 'invalid16B loading sample: '+tag)
        normalized = bytes((v & 0xC0) | ({0x30: 1, 0x31: 2}.get(v & 0x3F, v & 0x3F))
                           for v in x[0x1783:0x178B])
        require(normalized == y[0x1783:0x178B] and x[0x178B:0x17AB] == y[0x178B:0x17AB],
                '16B shooter identity/position mismatch: '+tag)
        last_positions = sorted(x[0x179B+i] | x[0x17A3+i] << 8 for i in range(8) if x[0x1783+i])
        all_samples[tag] = dict(native=xs, source=ys, native_ids=list(x[0x1783:0x178B]),
                                source_ids=list(y[0x1783:0x178B]),
                                native_timers=list(x[0x17AB:0x17B3]), source_timers=list(y[0x17AB:0x17B3]))
    require(last_positions == [656, 1040, 1248, 1440, 1760, 3856], 'not all six shooter placements loaded')
    usage(c, '94')
    usage(c, '93')
    regressions = {}
    for name, baseline, script, extras in (
        ('purchase', 'type3-shooters-reg-purchase-v1', 'forest-a2-funded-purchase-save.script', {0x11809: 3}),
        ('16b', 'type3-shooters-native-final-v1', 'native-type3-shooters-16b.script', {0x13: 2})):
        extras = {0x19B8: 1, 0x19D8: 1, **extras}
        e, er = native('type3-c2-reg-'+name+'-v1', script, extras, target=TARGET)
        f, fr = native(baseline, script, extras, target='demo11-native-type3-shooters-v1')
        hashes = {}
        for tag in tags(script):
            hashes[tag] = {}
            for suffix in ('wram.bin', 'sram.bin', 'vram.bin'):
                left, right = (e / (tag+'.'+suffix)).read_bytes(), (f / (tag+'.'+suffix)).read_bytes()
                require(left == right, 'full unchanged regression differs: '+name+'/'+tag+'/'+suffix)
                hashes[tag][suffix] = sha(left)
        regressions[name] = dict(native_receipt=er, parent_receipt=fr, samples=hashes)
    result = dict(target=TARGET, admission=admission, checker_sha256=sha(Path(__file__).read_bytes()),
                  direction=dict(native_receipt=ar, source_receipt=br, samples=samples, usage=used),
                  normal_entry=dict(receipt=pr, samples=normal),
                  all16b=dict(native_receipt=cr, source_receipt=dr, samples=all_samples), regressions=regressions,
                  limits=['Explicit position/pipe/immunity/global13/14 fixtures; normal094 case uses map/node fixture only.',
                          '16B late window teleports2048->3600; not an unassisted course pass.',
                          'All six shooter IDs/positions match, including extra-bit C0, but C0 motion phase and late C1 trajectories remain open.',
                          'C2 selected actor fields and listed properties only; no whole-engine/image/audio parity.',
                          'E0 birth, other95 rooms, complete courses/boss victories and product promotion remain open.'])
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()
