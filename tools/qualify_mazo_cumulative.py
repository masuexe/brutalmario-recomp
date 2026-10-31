#!/usr/bin/env python3
"""Reconcile cumulative Mazo graphics with inherited programs and native regressions."""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

from native_sprite_gap import identity, packs
from prepare_mazo_gfx282 import (CUMULATIVE_PARENT as PARENT, CUMULATIVE_TARGET as TARGET,
                                CUMULATIVE_SHA, CUMULATIVE_CONFIG_SHA, MAZO_SHA, PACK_ADDRESS, ROOT)
from qualify_mazo_second import capture, dodge, graphics, read, require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset
from runtime_patches import patch_plan

REGRESSIONS = {
    '25': 'sprite25-room154-native.script',
    '33': 'sprite33-room0fe-native.script',
    '94': 'sprite94-room0ef-native.script',
    '175': 'native-modern-175.script',
    '178': 'native-modern-178.script',
    '97': 'native-modern-97-route.script',
    'c0': 'native-type3-shooters-c0-dense.script',
    'c1': 'native-type3-shooters-c1-dense.script',
    'c2': 'native-type3-c2-direction.script',
    'child': 'seven-child-native-event.script',
    'purchase': 'forest-a2-funded-purchase-save.script',
}


def review(cfg=None):
    require(sha((ROOT/'config/restorations'/(PARENT+'.json')).read_bytes()) == CUMULATIVE_CONFIG_SHA,
            'cumulative parent configuration pin')
    parent = read(ROOT/'config/restorations'/(PARENT+'.json'))
    cfg = cfg if cfg is not None else read(ROOT/'config/restorations'/(TARGET+'.json'))
    old = (ROOT/'local/restoration'/PARENT/'rom.sfc').read_bytes()
    new = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    source = (ROOT/'local/content-versions/mazo/rom.sfc').read_bytes()
    require(sha(old) == parent['output']['sha256'] == CUMULATIVE_SHA, 'cumulative parent pin')
    require(sha(source) == MAZO_SHA, 'official mazo pin')
    decoded, stream = lz2(source, graphics_pointer(source, 0x282), limit=0x10000)
    require(len(decoded) == 4096 and len(stream) == 3344, 'bounded donor graphics')
    off = pointer_offset(0x282)
    patch = dict(offset=off, before='ffffff', after='0080d2',
                 role='Extended graphics 282 requested by the room 151 boss 9C')
    pack = dict(variable='BM_MAZO_GFX282_PACK', pack_file='gfx282.bin', address='D28000',
                size=len(stream), sha256=sha(stream), executable=False,
                source='local/native-modules/mazo-gfx282-v1')
    expected = copy.deepcopy(parent)
    expected.update(id=TARGET, parent_restoration=PARENT, parent_output=parent['output'],
                    scope='Retain modern-sprites-v2 and mount official mazo GFX0282; experimental, no earned clear/save acceptance.')
    expected['native_sprite_gap']['extra_packs'].append(pack)
    expected['native_sprite_gap']['extra_patches'].append(patch)
    out = bytearray(old)
    require(out[off:off+3] == bytes.fromhex('ffffff'), 'pointer preimage')
    out[off:off+3] = PACK_ADDRESS.to_bytes(3, 'little')
    expected['output']['sha256'] = sha(out)
    require(cfg == expected, 'config changed beyond graphics and lineage; inherited recipes/hooks differ')
    require(new == out, 'ROM differs beyond the three pointer bytes')
    before, after = packs(PARENT), packs(TARGET)
    require(len(before) == 57 and after[:-1] == before and len(after) == 58, 'selected inherited programs/packs differ')
    require(all(int(p['address'], 16) >> 16 != 0xd2 for p in before), 'D2 bank collision')
    for item in after:
        data = (ROOT/'local/restoration'/TARGET/item['pack_file']).read_bytes()
        require(len(data) == item['size'] and sha(data) == item['sha256'], 'installed pack pin: '+item['variable'])
    require((ROOT/'local/restoration'/TARGET/'gfx282.bin').read_bytes() == stream, 'source stream differs')
    a, b = identity(PARENT), identity(TARGET)
    for feature, target in ((a, PARENT), (b, TARGET)):
        feature['files'].pop('config/restorations/'+target+'.json')
        feature.pop('generated_header_sha256')
        feature.pop('packs')
    require(a == b, 'inherited source programs or native runtime hooks differ')
    return dict(parent=PARENT, parent_rom_sha256=sha(old), rom_sha256=sha(new),
                retained_recipes=len(cfg['native_sprite_gap']['manifests']), retained_packs=len(before),
                retained_patches=len(parent['native_sprite_gap']['extra_patches']),
                inherited_native_adaptations=cfg['native_adaptations'],
                added_pack=pack, pointer_patch=patch, inherited_files=b['files'])


def regression_capture(name, target, script):
    p = ROOT/'local/captures'/name
    r = read(p/'receipt.json')
    build = read(ROOT/'local/build'/target/'m1-build.json')
    cfg = read(ROOT/'config/restorations'/(target+'.json'))
    text = (ROOT/'recomp/inputs'/script).read_text()
    require(r['stage'] == 'native' and r['target'] == target, 'regression role')
    require(r['route_sha256'] == sha(text.encode()) and (p/'input.script').read_text() == 'turbo on\n'+text,
            'regression input pin')
    require(r['rom_sha256'] == build['rom_sha256'] == cfg['output']['sha256'] ==
            sha((ROOT/'local/restoration'/target/'rom.sfc').read_bytes()), 'regression ROM pin')
    require(r['host_binary_sha256'] == build['binary_sha256'] == sha((
        ROOT/'local/build'/target/RESTORATIONS[target]['binary']).read_bytes()), 'regression binary pin')
    require(r['native_content'] == build['native_content'] == identity(target), 'regression module pin')
    require(r['runtime_patches'] == build['runtime_patches'] == patch_plan() and
            r['analysis'] == build['analysis'], 'regression runtime pin')
    log = (p/'run.log').read_text()
    require('exit: script quit after' in log and 'timeout' not in log.lower() and 'BRK' not in log
            and 'assertion failed' not in log.lower(), 'regression incomplete: '+name)
    tags = [line.split()[1] for line in text.splitlines() if line.startswith('dump ')]
    require(len(tags) == len(set(tags)), 'duplicate regression dump tags')
    return p, tags


def regressions(prefix):
    results = {}
    for key, script in REGRESSIONS.items():
        a, tags = regression_capture(f'{prefix}-{key}-candidate', TARGET, script)
        b, old_tags = regression_capture(f'{prefix}-{key}-parent', PARENT, script)
        require(tags == old_tags, 'regression tags differ')
        samples = {}
        for tag in tags:
            samples[tag] = {}
            for suffix, size in (('wram.bin', 0x20000), ('sram.bin', 0x8000), ('vram.bin', 0x10000),
                                 ('fb.bgrx', 256*224*4)):
                x, y = (a/(tag+'.'+suffix)).read_bytes(), (b/(tag+'.'+suffix)).read_bytes()
                require(len(x) == size and x == y, f'retained regression differs: {key}/{tag}/{suffix}')
                samples[tag][suffix] = sha(x)
        results[key] = dict(script=script, samples=samples,
                            receipts=[sha((p/'receipt.json').read_bytes()) for p in (a, b)])
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-side', choices=['parent', 'candidate'])
    p.add_argument('--prefix', default='mazo-cumulative-reg-v1')
    p.add_argument('--capture', default='mazo-cumulative-highhops-v1')
    p.add_argument('--hops', type=int, default=240)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    admission = review()
    if args.run_side:
        target = PARENT if args.run_side == 'parent' else TARGET
        for key, script in REGRESSIONS.items():
            print('RUN', args.run_side, key, flush=True)
            subprocess.run([sys.executable, str(ROOT/'tools/m1.py'), 'native', '--target', target,
                            '--script', str(ROOT/'recomp/inputs'/script), '--capture',
                            f'{args.prefix}-{key}-{args.run_side}'], cwd=ROOT, check=True)
        return
    require(args.output is not None and not args.output.exists(), 'fresh report required')
    directory, receipt, data = capture(args.capture, False, 'highhop', args.hops, target=TARGET)
    source, sr, sd = capture('mazo-second-source-highhops-v2', True, 'highhop', 120)
    result = dict(admission=admission, native=dict(dodge=dodge(data), graphics=graphics(directory, data, False)),
                  source=dict(dodge=dodge(sd), graphics=graphics(source, sd, True)),
                  receipts=[sha((q/'receipt.json').read_bytes()) for q in (directory, source)],
                  regressions=regressions(args.prefix),
                  limits=['Map/pipe/immunity and first-boss placement fixtures; later normal jumps.',
                          'Whole-fight clear, saved completion, audible music and product promotion remain open.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('PASS: cumulative programs retained, complete GFX282 upload, and eleven unchanged native regressions')


if __name__ == '__main__':
    main()
