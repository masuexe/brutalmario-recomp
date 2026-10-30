#!/usr/bin/env python3
"""Qualify the isolated C0/C1 shooter adapter, without promoting product r15."""
import argparse
import json
from pathlib import Path

from native_sprite_gap import packs
from prepare_native_lowmirror import load
from prepare_rom import verify
from qualify_forest_a2 import native
from qualify_forest_shack import reference_capture
from qualify_native_lowmirror import state, usage
from qualify_world1_next_course import require
from restore_star_world_1 import sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-type3-shooters-v1'
RECIPE = ROOT / 'config/native-content/type3-shooters-v1.json'


def children(body, phase):
    # Slot differences reflect independently occupied actors in the two engines.
    return sorted((body[0x14C8+i], body[0xE4+i] | body[0x14E0+i] << 8,
                   body[0xD8+i] | body[0x14D4+i] << 8, body[0xB6+i],
                   body[0xAA+i], body[0x151C+i]) for i in range(12)
                  if body[0x14C8+i] and body[0x1AB10+i] & 8 and
                  body[0x1AB9E+i] == 0x95 and body[0x1504+i] == phase)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    cfg, recipe = load(ROOT / 'config/restorations' / (TARGET+'.json')), load(RECIPE)
    parent = (ROOT / 'local/restoration/demo11-native-product-r15/rom.sfc').read_bytes()
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(parent, cfg['parent_output'], 'rejected parent identity')
    verify(rom, cfg['output'], 'isolated shooter descendant')
    expected = bytearray(parent)
    require(len(recipe['unapplied_rom_patches']) == 3, 'unexpected hook set')
    for patch in recipe['unapplied_rom_patches']:
        at, before, after = patch['offset'], bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
        require(expected[at:at+len(before)] == before and len(before) == len(after), 'hook preimage differs')
        expected[at:at+len(after)] = after
    require(expected == rom, 'changes outside the three bounded hooks')
    mappings = packs(TARGET)
    require(len(mappings) == 49, 'unexpected mapping set')
    old = packs('demo11-native-product-r15')
    require([p for p in mappings if p['pack_file'] != 'type3-shooters.bin'] == old,
            'existing pack descriptor changed')
    for pack in mappings:
        verify((ROOT / 'local/restoration' / TARGET / pack['pack_file']).read_bytes(), pack, 'native pack')
    code = bytes.fromhex(recipe['code']['raw_payload'])
    require(code == (ROOT / 'local/restoration' / TARGET / 'type3-shooters.bin').read_bytes(),
            'adapter differs from reviewed raw payload')

    a, ar = native('type3-shooters-native-final-v1', 'native-type3-shooters-16b.script',
                   {0x19B8: 1, 0x19D8: 1, 0x13: 2}, target=TARGET)
    source = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    b, br = reference_capture('type3-shooters-source-final-v1', 'source-type3-shooters-16b.script', source)
    used = {bank: usage(a, bank)[bank] for bank in ('92', '94', '93', 'A3')}
    tags = [line.split()[1] for line in (ROOT / 'recomp/inputs/native-type3-shooters-16b.script').read_text().splitlines()
            if line.startswith('dump scan_') or line.startswith('dump c0_') or line.startswith('dump c1_')]
    require(len(tags) == len(set(tags)), 'duplicate dump labels')
    samples, c1_pairs, c0_seen = {}, 0, False
    for tag in tags:
        x, xs = state(a, tag)
        y, ys = state(b, tag, source=True)
        require(xs['mode'] == ys['mode'] == 0x14 and xs['room'] == ys['room'] == 0x16B and
                x[0x71] == y[0x71] == x[0x9D] == y[0x9D] == 0, 'not live unfrozen16B: '+tag)
        native_ids, source_ids = x[0x1783:0x178B], y[0x1783:0x178B]
        require(bytes({0xB0: 0x81, 0xB1: 0x82}.get(v, v) for v in native_ids) == source_ids,
                'shooter identity mismatch: '+tag)
        require(x[0x178B:0x17AB] == y[0x178B:0x17AB], 'shooter positions differ: '+tag)
        timers = list(zip(x[0x17AB:0x17B3], y[0x17AB:0x17B3]))
        # Record differences explicitly; these fixed-time windows do not prove
        # cycle-exact C0 motion, and no tolerance is applied to child positions.
        p2, q2 = children(x, 2), children(y, 2)
        if p2 and q2:
            require(all(row[1] == 656 for row in p2+q2), 'C0 launch column differs')
            c0_seen = True
        p3, q3 = children(x, 3), children(y, 3)
        if tag.startswith('c1_'):
            require(p3 == q3 and p3, 'C1 normalized selected actor mismatch: '+tag)
            c1_pairs += 1
        samples[tag] = dict(native=xs, source=ys, native_shooters=list(native_ids),
                            source_shooters=list(source_ids), timers=timers,
                            native_phase2=p2, source_phase2=q2, phase3=p3)
    require(c0_seen and c1_pairs == 20, 'actual generated actors not covered')

    regressions = {}
    for name, baseline, script, extras in (
        ('normal', 'forest-a2-r14-normal-v1', 'forest-hollow-normal-save.script', {}),
        ('purchase', 'forest-a2-r14-purchase-v1', 'forest-a2-funded-purchase-save.script', {0x11809: 3}),
        ('seven-any', 'type3-shooters-parent-seven-any-v1', 'native-type3-seven-window.script', {0xD7E2: 1})):
        extras = {0x19B8: 1, 0x19D8: 1, **extras}
        p, pr = native('type3-shooters-reg-'+name+'-v1', script, extras, target=TARGET)
        q, qr = native(baseline, script, extras, target='demo11-native-product-r14')
        results = {}
        for line in (ROOT / 'recomp/inputs' / script).read_text().splitlines():
            if not line.startswith('dump '):
                continue
            tag = line.split()[1]
            w, _ = state(p, tag)
            z, _ = state(q, tag)
            differences = [i for i, (v, u) in enumerate(zip(w, z)) if v != u]
            # These bytes are below the active SP at every retained dump.
            # Do not call this a full byte-identical WRAM comparison.
            require(all(0x1BC <= i <= 0x1DE for i in differences), 'game-state regression: '+name+'/'+tag)
            for directory in (p, q):
                info = load(directory / (tag+'.info.json'))
                trace = [row.split(',') for row in (directory / 'state-trace.txt').read_text().splitlines()]
                stack = [int(row[5], 16) for row in trace if int(row[0]) == info['frame']]
                require(stack and all(i < sp for i in differences for sp in stack), 'excluded bytes overlap active stack')
            for suffix in ('sram.bin', 'vram.bin'):
                require((p / (tag+'.'+suffix)).read_bytes() == (q / (tag+'.'+suffix)).read_bytes(),
                        'saved/render state regression: '+name+'/'+tag)
            results[tag] = dict(inactive_stack_differences=differences, wram_sha256=sha(w))
        regressions[name] = dict(native_receipt=pr, parent_receipt=qr, samples=results)
    report = dict(target=TARGET, status='bounded-experimental-checkpoint; r14 remains accepted product',
                  rom_sha256=sha(rom), recipe_sha256=sha(RECIPE.read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()),
                  native_receipt=ar, source_receipt=br, module_usage=used,
                  shooter_samples=samples, c1_exact_normalized_pairs=c1_pairs, regressions=regressions,
                  limits=['Position, pipe, immunity and global13/14 fixtures; no actor, shooter timer, clear or save writes.',
                          'C0 actual loading, countdown and phase2 generation only; source/native motion phase differs.',
                          'One C0 and two C1 shooter instances loaded; remaining room16B windows and C2 are open.',
                          'C1 comparison ignores slots and compares status/XY/velocity/151C for phase3 custom95 only.',
                          'Regressions exclude explicitly recorded inactive stack residue01BC..01DE; SRAM/VRAM exact.',
                          'Old fixed-slot Seven E0 wait times out; current Seven window matches r14 but does not qualify E0 birth.',
                          'No full course, complete boss victory, full physics/timing, audio or visual acceptance.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()
