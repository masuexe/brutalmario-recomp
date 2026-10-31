#!/usr/bin/env python3
"""Qualify Mazo primary entry and assisted goal/save ownership at the real node."""
import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

from native_sprite_gap import packs
from prepare_mazo_primary_entry import ROOT, TARGET, PARENT, CONTROL, build
from qualify_mazo_cumulative import regression_capture
from qualify_world1_next_course import require, sha, word
from qualify_mazo_messages import room_capture, pixels, tiles
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom

SCRIPT = 'mazo-node-save-boundary.script'
REGRESSIONS = {'126': 'room126-node-clear-save-reload.script',
               'child': 'seven-child-native-event.script',
               'purchase': 'forest-a2-funded-purchase-save.script'}
STACK_RESIDUE = {0x1ba, 0x1bb, 0x1bc, 0x1bd, 0x1be, 0x1bf, 0x1c0, 0x1c1,
                 0x1c2, 0x1c3, 0x1c4, 0x1c5, 0x1c6, 0x1c7, 0x1c8, 0x1c9, 0x1ca, 0x1cb,
                 0x1d2, 0x1d3, 0x1d4, 0x1d6, 0x1d7, 0x1d9, 0x1db, 0x1dd, 0x1de, 0x1df, 0x1f8}


def compare_wram(x, y, cpu_x, cpu_y):
    require(cpu_x == cpu_y, 'regression CPU differs')
    require(len(x) == len(y) == 0x20000, 'regression WRAM size')
    delta = [i for i in range(len(x)) if x[i] != y[i]]
    sp = int(cpu_x[3], 16)
    node_difference = (x[0x100] == y[0x100] == 0x0e and
                       x[0x1f11] == y[0x1f11] == 0 and
                       x[0xd1f0] == 0x30 and y[0xd1f0] == 0xb4)
    require(all(i in STACK_RESIDUE and i < sp or (i == 0xd1f0 and node_difference) for i in delta),
            'regression active WRAM differs')
    return delta


def decompression_phase(x, y, cpu_x, cpu_y, timing_x, timing_y):
    """Replay INX/BNE/STX8A/RTS across the observed decompressor cut point."""
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    require(rom[lorom(0x00b983):lorom(0x00b992)].hex() == 'a78aa68ae8d005a20080e68c868a60' and
            rom[lorom(0x00b930):lorom(0x00b936)].hex() == '2083b99700c8',
            'decompression input helper changed')
    require(int(timing_x['resume_pc']) == 0xb933 and int(timing_y['resume_pc']) == 0xb987,
            'different active instruction boundary')
    require(0 <= int(timing_x['cpu_clock']) - int(timing_y['cpu_clock']) <= 128 and
            timing_x['vpos'] == timing_y['vpos'], 'unbounded decompressor timing difference')
    old = [int(v, 16) for v in cpu_y]
    require(old[6] == 0 and old[7] & 0x30 == 0x20 and old[1] < 0xffff,
            'unexpected decompressor CPU mode')
    require(word(y, old[3] + 1) == 0xb932, 'return address does not lead to B933')
    require(word(y, 0x8a) == old[1] and y[0x8c] == x[0x8c] == 0xa6,
            'input source pointer differs')
    source = next(p for p in packs(TARGET) if int(p['address'], 16) >> 16 == 0xa6)
    payload = (ROOT / 'local/restoration' / TARGET / source['pack_file']).read_bytes()
    offset = old[1] - (int(source['address'], 16) & 65535)
    require(0 <= offset < len(payload) and payload[offset] == old[0] & 255,
            'already fetched input byte differs')
    old[1] += 1  # INX; BNE is taken.
    old[7] = (old[7] & ~0x82) | (0x80 if old[1] & 0x8000 else 0)
    normalized = bytearray(y)
    normalized[0x8a:0x8c] = old[1].to_bytes(2, 'little')  # STX8A.
    old[3] += 2  # RTS consumes B932 and resumes B933; no gameplay state write.
    cpu = [f'{v:0{len(template)}x}' for v, template in zip(old, cpu_y)]
    delta = compare_wram(x, bytes(normalized), cpu_x, cpu)
    return dict(candidate_pc='00B933', control_pc='00B987', replay='INX/BNE/STX8A/RTS',
                clocks=[int(timing_x['cpu_clock']), int(timing_y['cpu_clock'])],
                source_pointer=[word(x, 0x8a), word(y, 0x8a)], normalized_cpu=cpu,
                inactive_stack_differences=delta)


def admission():
    recipe, parent, rom, raw = build()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    installed = ROOT / 'local/restoration' / TARGET
    require((installed / 'rom.sfc').read_bytes() == rom, 'installed ROM differs')
    require(packs(TARGET)[:-1] == packs(PARENT), 'inherited selected programs differ')
    for item in packs(TARGET):
        body = (installed / item['pack_file']).read_bytes()
        require(len(body) == item['size'] and sha(body) == item['sha256'], 'installed pack differs')
    before, after = parent['native_sprite_gap'], cfg['native_sprite_gap']
    require(after['manifests'] == before['manifests'] and
            after['extra_packs'][:-1] == before['extra_packs'] and
            after['extra_patches'][:-1] == before['extra_patches'], 'inherited recipe/patch override')
    require(cfg['native_adaptations'][:-1] == parent['native_adaptations'], 'inherited native adaptation lost')
    changed = {'id', 'scope', 'parent_restoration', 'parent_output', 'output',
               'native_sprite_gap', 'native_adaptations'}
    require(set(cfg) == set(parent) and all(cfg[k] == parent[k] for k in cfg if k not in changed),
            'unrelated target setting changed')
    return dict(rom_sha256=sha(rom), code_sha256=sha(raw),
                retained_recipes=len(after['manifests']), retained_packs=len(packs(PARENT)),
                retained_patches=len(before['extra_patches']))


def regressions(prefix, keys=None):
    result = {}
    for key, script in REGRESSIONS.items():
        if keys is not None and key not in keys:
            continue
        a, tags = regression_capture(f'{prefix}-{key}-candidate', TARGET, script)
        b, old = regression_capture(f'{prefix}-{key}-control', CONTROL, script)
        require(tags == old, 'regression sample list differs')
        traces = [{int(v[0]): v[2:] for line in (p / 'state-trace.txt').read_text().splitlines()
                   if (v := line.split(',')) and len(v) == 10} for p in (a, b)]
        timing = [{int(row['frame']): row for row in csv.DictReader((p / 'timing.csv').read_text().splitlines())
                   if row['phase'] == 'run'} for p in (a, b)]
        rows = {}
        for tag in tags:
            frames = [json.loads((p / (tag + '.info.json')).read_text())['frame'] for p in (a, b)]
            cpu = [trace[frame] for trace, frame in zip(traces, frames)]
            require(frames[0] == frames[1], 'regression frame differs')
            x, y = [(p / (tag + '.wram.bin')).read_bytes() for p in (a, b)]
            phase = None
            if cpu[0] != cpu[1]:
                require(key == 'child' and tag == 'fight180', 'unexpected CPU phase difference')
                phase = decompression_phase(x, y, *cpu, timing[0][frames[0]], timing[1][frames[1]])
                delta = phase['inactive_stack_differences']
            else:
                delta = compare_wram(x, y, *cpu)
            for suffix, size in [('sram.bin', 0x8000), ('vram.bin', 0x10000), ('fb.bgrx', 256*224*4)]:
                left, right = [(p / (tag + '.' + suffix)).read_bytes() for p in (a, b)]
                require(len(left) == size and left == right, 'regression save/render differs: ' + key + '/' + tag)
            rows[tag] = dict(frame=frames[0], cpu=cpu[0], wram_differences=delta,
                             wram_sha256=[sha(x), sha(y)], decompression_phase=phase)
        result[key] = dict(candidate=a.name, control=b.name, samples=rows)
    return result


def capture(name, target, current):
    p = ROOT / 'local/captures' / name
    r = json.loads((p / 'receipt.json').read_text())
    script = 'mazo-node-save-boundary-settled.script' if current else SCRIPT
    if current:
        regression_capture(name, target, script)
    else:
        # The preserved control predates the source edit. Pin its frozen build
        # receipt and binary; do not relabel it as current-source parity.
        b = json.loads((ROOT / 'local/build' / target / 'm1-build.json').read_text())
        require(r['target'] == target and r['stage'] == 'native', 'historical control role')
        for key in ('rom_sha256', 'native_content', 'runtime_patches', 'analysis'):
            require(r[key] == b[key], 'historical control build receipt differs: ' + key)
        require(r['host_binary_sha256'] == b['binary_sha256'] == sha((ROOT / 'local/build' /
                target / RESTORATIONS[target]['binary']).read_bytes()), 'historical binary differs')
        require(r['rom_sha256'] == sha((ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()),
                'historical ROM differs')
        source = (ROOT / 'recomp/inputs' / script).read_bytes()
        require(r['route_sha256'] == sha(source) and
                (p / 'input.script').read_bytes() == b'turbo on\n' + source, 'historical input differs')
        log = (p / 'run.log').read_text()
        require('exit: script quit after' in log and 'timeout' not in log.lower() and
                'assertion failed' not in log.lower() and 'BRK' not in log, 'historical control incomplete')
    tags = [s.split()[1] for s in (ROOT / 'recomp/inputs' / script).read_text().splitlines()
            if s.startswith('dump ')]
    states, samples = {}, {}
    for tag in tags:
        w = (p / (tag + '.wram.bin')).read_bytes()
        s = (p / (tag + '.sram.bin')).read_bytes()
        require(len(w) == 0x20000 and len(s) == 0x8000, 'incomplete memory: ' + tag)
        states[tag] = (w, s)
        samples[tag] = dict(mode=w[0x100], room=word(w, 0x10b), translevel=w[0x13bf],
                            goal=w[0x1493], exits=w[0x1f2e], event=w[0x1dea], node=w[0xd1f0],
                            course30=w[0x1ed2], legacy0d=w[0x1eaf],
                            extended_b4=w[0x1f56], save30=[s[0x30], s[0x1dd]],
                            wram_sha256=sha(w), sram_sha256=sha(s))
    return p, r, states, samples


def boundary(states, fixed):
    node = states['m1'][0]
    require(node[0x100] == 0x0e and node[0x1f11] == 0 and
            word(node, 0x1f17) == 256 and word(node, 0x1f19) == 240,
            'wrong actual map node')
    selector = 0x30 if fixed else 0xb4
    require(node[0xd1f0] == selector, 'wrong node assignment')
    entry = states['m2'][0]
    require(entry[0x100] == 0x14 and word(entry, 0x10b) == 0x190 and
            entry[0x13bf] == selector and entry[0x1dea] == 0xff,
            'primary entry, event or saved course context differs')
    w = states['walked'][0]
    require(w[0x100] == 0x14 and word(w, 0x10b) == 0x192 and
            0 < w[0x1493] <= 0xf0, 'real sphere goal absent')
    require(states['closed'][0][0x1426] == 0, 'message not dismissed')
    require(node[0x1ed2] == 0 and node[0x1f2e] == 0, 'already completed control')
    for tag in ('after_goal', 'file_reload'):
        w, s = states[tag]
        require(w[0x100] == 0x0e and w[0x1f2e] == 0, 'map or observed exit count differs')
        require(w[0x1ed2] == s[0x30] == s[0x1dd] == (0x80 if fixed else 0),
                'original course completion or save copy missing: ' + tag)
        require(w[0x1eaf] == 0x8f and s[0xd] == s[0x1ba] == 0x8f,
                'original B0 legacy flag behavior changed')
        # 1F56 also belongs to the backup WRAM flag block (1F49+0D).
        require(w[0x1f56] == 0x8f, 'legacy flag backup differs')


def message_lifecycle(directory, states):
    source, _ = room_capture('mazo-messages-192-source-v2', 0x192, True)
    recipe = json.loads((ROOT / 'config/native-content/mazo-messages-v2.json').read_text())
    require(states['message'][0][0x1426] == 1, 'guest message request absent')
    actual = (directory / 'message.vram.bin').read_bytes()
    reference = (source / 'message.vram.bin').read_bytes()
    require(len(actual) == len(reference) == 0x10000 and
            sha(actual[0x9000:0x9800]) == recipe['fonts']['japanese']['sha256'], 'Japanese font differs')
    require(tiles(actual) == tiles(reference) and pixels(directory) == pixels(source),
            'current ending message differs from official source')
    for tag in ('closed', 'after_goal', 'file_reload'):
        raw = (directory / (tag + '.vram.bin')).read_bytes()
        require(sha(raw[0x9000:0x9800]) == recipe['fonts']['english']['sha256'], 'font restore differs')
    return dict(source_capture=source.name, source_receipt_sha256=sha((source / 'receipt.json').read_bytes()),
                tilemap_sha256=sha(tiles(actual)), text_pixels_sha256=sha(pixels(directory)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', default='mazo-node-save-boundary-control-v1')
    p.add_argument('--historical-control', default='mazo-node-save-boundary-v1')
    p.add_argument('--candidate', default='mazo-node-save-boundary-v5')
    p.add_argument('--run-regressions', choices=['candidate', 'control'])
    p.add_argument('--prefix', default='mazo-primary-reg-v1')
    p.add_argument('--output')
    a = p.parse_args()
    if a.run_regressions:
        target = TARGET if a.run_regressions == 'candidate' else CONTROL
        for key, script in REGRESSIONS.items():
            subprocess.run([sys.executable, str(ROOT / 'tools/m1.py'), 'native', '--target', target,
                            '--script', str(ROOT / 'recomp/inputs' / script), '--capture',
                            f'{a.prefix}-{key}-{a.run_regressions}'], cwd=ROOT, check=True)
        return
    require(a.output is not None, 'output required')
    output = ROOT / a.output
    require(not output.exists(), 'use a fresh report path')
    review = admission()
    results = {}
    for label, name, target, fixed in [
            ('historical_control', a.historical_control, 'demo11-native-product-r14', False),
            ('control', a.control, CONTROL, False), ('candidate', a.candidate, TARGET, True)]:
        directory, receipt, states, rows = capture(name, target, target != 'demo11-native-product-r14')
        boundary(states, fixed)
        if fixed:
            log = (directory / 'run.log').read_text()
            matches = re.findall(r'bank=88 resolutions=\d+ executed_page_instructions=(\d+)', log)
            require(matches and int(matches[-1]) > 0, 'primary adapter never executed')
            review['executed_primary_instructions'] = int(matches[-1])
            review['message_lifecycle'] = message_lifecycle(directory, states)
        results[label] = dict(
            capture=name, receipt_sha256=sha((directory / 'receipt.json').read_bytes()),
            rom_sha256=receipt['rom_sha256'], binary_sha256=receipt['host_binary_sha256'], samples=rows)
    report = dict(target=TARGET, checker_sha256=sha(Path(__file__).read_bytes()),
                  admission=review, regressions=regressions(a.prefix), **results,
                  limits=['Map placement and room190-to192 pipe-action fixtures.',
                          'No ordinary room190 traversal, earned fight or complete world acceptance.',
                          'B0 still sets legacy course0D; its recipient meaning remains open.',
                          'Control and candidate have different ROMs and program packs.',
                          'Three regressions allow bounded inactive stack residue, intended map-node byte and one proven decompressor phase.',
                          'The native exit count remains0; official-source count reconciliation stays open.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: node30, primary190, real sphere goal, course30/save copies and File A reload')


if __name__ == '__main__':
    main()
