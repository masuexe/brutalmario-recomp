#!/usr/bin/env python3
"""Qualify scoped Mazo messages, font lifecycle and retained cumulative behavior."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from mazo_ending_route import ending_route
from mazo_message_routes import route
from native_sprite_gap import identity, packs
from prepare_mazo_messages import PARENT, RECIPE, ROOT, TARGET, build
from qualify_mazo_cumulative import REGRESSIONS, regression_capture
from qualify_mazo_ending import boundary
from qualify_mazo_second import capture, dodge, graphics, read, require, sha


def admission():
    recipe, parent, expected, code, data = build()
    cfg = read(ROOT/'config/restorations'/(TARGET+'.json'))
    require(cfg['id'] == TARGET and cfg['parent_restoration'] == PARENT and
            cfg['parent_output'] == parent['output'], 'message candidate lineage')
    changed = {'id', 'scope', 'parent_restoration', 'parent_output', 'output', 'native_sprite_gap', 'native_adaptations'}
    require(set(cfg) == set(parent) and all(cfg[k] == parent[k] for k in cfg if k not in changed), 'inherited config changed')
    a, b = parent['native_sprite_gap'], cfg['native_sprite_gap']
    require(set(a) == set(b) and a['manifests'] == b['manifests'] and
            b['extra_packs'][:-2] == a['extra_packs'] and b['extra_patches'][:-2] == a['extra_patches'],
            'inherited recipes/packs/records changed')
    require(cfg['native_adaptations'][:-1] == parent['native_adaptations'] and
            cfg['native_adaptations'][-1]['recipe_sha256'] == sha(RECIPE.read_bytes()) and
            cfg['native_adaptations'][-1]['recipe'] == str(RECIPE.relative_to(ROOT)), 'native adaptation changed')
    for item, raw, address, executable in zip(b['extra_packs'][-2:], (code, data), ('89B000', 'D38000'), (True, False)):
        require((item['address'], item['size'], item['sha256'], item['executable']) ==
                (address, len(raw), sha(raw), executable), 'new pack differs')
    for item, pin in zip(b['extra_patches'][-2:], recipe['patches']):
        from restore_star_world_1 import lorom
        require(item == dict(offset=lorom(int(pin['address'], 16)), before=pin['before'],
                             after=pin['after'], role=pin['role']), 'message hook differs')
    actual = (ROOT/'local/restoration'/TARGET/'rom.sfc').read_bytes()
    require(actual == expected and cfg['output']['sha256'] == sha(expected), 'unexpected ROM changes')
    old_packs, new_packs = packs(PARENT), packs(TARGET)
    require(len(old_packs) == 58 and new_packs[:-2] == old_packs and len(new_packs) == 60, 'inherited program selection differs')
    for item in new_packs:
        raw = (ROOT/'local/restoration'/TARGET/item['pack_file']).read_bytes()
        require(len(raw) == item['size'] and sha(raw) == item['sha256'], 'installed pack differs: '+item['variable'])
    x, y = identity(PARENT), identity(TARGET)
    for target, value in ((PARENT, x), (TARGET, y)):
        value['files'].pop('config/restorations/'+target+'.json')
        value.pop('generated_header_sha256')
        value.pop('packs')
    require(x == y, 'inherited source/runtime hooks differ')
    return dict(parent=PARENT, rom_sha256=sha(actual), retained_recipes=len(a['manifests']),
                retained_packs=len(old_packs), retained_patches=len(a['extra_patches']),
                recipe_sha256=sha(RECIPE.read_bytes()), code_sha256=sha(code), data_sha256=sha(data))


def room_capture(name, room, donor):
    p = ROOT/'local/captures'/name
    text = route(room, donor)
    r = read(p/'receipt.json')
    if donor:
        source = ROOT/'local/content-versions/mazo/rom.sfc'
        require(r['rom_sha256'] == read(RECIPE)['sources']['mazo']['sha256'] == sha(source.read_bytes()), 'source ROM pin')
        require(r['script_sha256'] == sha(text.encode()) and (p/'input.script').read_text() == text, 'source route pin')
        require(r['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'source options')
        for key, path in [('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so'),
                          ('frontend_sha256', 'local/build/snesref/snesref')]:
            require(r[key] == sha((ROOT/path).read_bytes()), 'source '+key)
        log = (p/'run.log').read_text()
        require(' quit' in log and 'timeout' not in log.lower(), 'source incomplete')
    else:
        version = 3 if room == 0x191 else 2
        script = f'../../local/probes/mazo-messages/native{room:03x}-v{version}.script'
        require((ROOT/'recomp/inputs'/script).read_text() == text, 'generated native route differs')
        regression_capture(name, TARGET, script)
    tags = [line.split()[1] for line in text.splitlines() if line.startswith('dump ')]
    result = {}
    for tag in tags:
        b = (p/(tag+'.wram.bin')).read_bytes()
        require(len(b) == 0x20000 and len((p/(tag+'.vram.bin')).read_bytes()) == 0x10000 and
                len((p/(tag+'.sram.bin')).read_bytes()) == (0x800 if donor else 0x8000), 'room dump size')
        result[tag] = b
    return p, result


def tiles(vram):
    return b''.join(vram[0xa000+y*64+12:0xa000+y*64+52] for y in range(5, 15))


def pixels(directory):
    raw = (directory/'message.fb.bgrx').read_bytes()
    require(len(raw) == 256*224*4, 'framebuffer size')
    # Compare source RGB565 and native BGRX at their common 5-bit precision.
    return bytes(raw[y*1024+x*4+c] >> 3 for y in range(48, 112) for x in range(56, 200) for c in range(3))


def rooms():
    result = {}
    recipe = read(RECIPE)
    for room, source_version in ((0x191, 3), (0x192, 2)):
        a, data = room_capture(f'mazo-messages-v2-{room:03x}-native-v1', room, False)
        b, source = room_capture(f'mazo-messages-{room:03x}-source-v{source_version}', room, True)
        for samples in (data, source):
            state = samples['message']
            require(state[0x100] == 0x14 and int.from_bytes(state[0x10b:0x10d], 'little') == room and
                    state[0x1426] == (2 if room == 0x191 else 1), 'message request not live')
            require(samples['closed'][0x1426] == 0, 'message not closed')
            if room == 0x191:
                require(int.from_bytes(samples['following'][0x10b:0x10d], 'little') == 0x151 and
                        samples['following'][0x100] == 0x14, '191 guest transition absent')
            else:
                require(samples['walked'][0x1493] >= 0xe0 and samples['after_goal'][0x100] == 0x0e,
                        '192 ordinary sphere/map boundary absent')
        av, bv = [(p/'message.vram.bin').read_bytes() for p in (a, b)]
        require(sha(av[0x9000:0x9800]) == sha(bv[0x9000:0x9800]) == recipe['fonts']['japanese']['sha256'], 'Japanese font differs')
        require(tiles(av) == tiles(bv) and pixels(a) == pixels(b), 'source message glyphs/pixels differ')
        for tag in ('closed', 'following' if room == 0x191 else 'after_goal'):
            require(sha((a/(tag+'.vram.bin')).read_bytes()[0x9000:0x9800]) == recipe['fonts']['english']['sha256'],
                    'English font did not return: '+tag)
        log = (a/'run.log').read_text()
        usage = re.search(r'bank=89 resolutions=(\d+) executed_page_instructions=(\d+)', log)
        require(usage is not None and int(usage[2]) > 0, 'private message program not executed')
        result[f'{room:03x}'] = dict(native_receipt=sha((a/'receipt.json').read_bytes()),
            source_receipt=sha((b/'receipt.json').read_bytes()), tilemap_sha256=sha(tiles(av)),
            common_precision_pixels_sha256=sha(pixels(a)), executed_instructions=int(usage[2]),
            native_course_id=data['message'][0x13bf], source_course_id=source['message'][0x13bf])
    return result


def compare_wram(x, y, cpu_x, cpu_y):
    require(cpu_x == cpu_y, 'CPU register regression')
    differences = [i for i, (a, b) in enumerate(zip(x, y)) if a != b]
    require(set(differences) <= {0x1f8}, 'game-state WRAM regression')
    require(all(i < int(cpu_x[3], 16) for i in differences), 'difference overlaps active stack')
    return differences


def regressions(prefix, capture_names=None):
    capture_names = capture_names or {}
    require(not set(capture_names)-set(REGRESSIONS), 'unknown regression capture override')
    result = {}
    for key, script in REGRESSIONS.items():
        name = capture_names.get(key, f'{prefix}-{key}-candidate')
        require(re.fullmatch(r'[A-Za-z0-9_-]+', name), 'invalid regression capture name')
        a, tags = regression_capture(name, TARGET, script)
        b, old_tags = regression_capture(f'mazo-cumulative-reg-v1-{key}-candidate', PARENT, script)
        require(tags == old_tags, 'regression tags differ')
        traces = [{int(v[0]): v[2:] for line in (p/'state-trace.txt').read_text().splitlines()
                   if (v := line.split(','))} for p in (a, b)]
        samples = {}
        for tag in tags:
            frames = [read(p/(tag+'.info.json'))['frame'] for p in (a, b)]
            cpu = [trace[frame] for trace, frame in zip(traces, frames)]
            raw = [(p/(tag+'.wram.bin')).read_bytes() for p in (a, b)]
            require(all(len(w) == 0x20000 for w in raw), 'regression WRAM size')
            delta = compare_wram(*raw, *cpu)
            for suffix, size in (('sram.bin', 0x8000), ('vram.bin', 0x10000), ('fb.bgrx', 256*224*4)):
                x, y = [(p/(tag+'.'+suffix)).read_bytes() for p in (a, b)]
                require(len(x) == size and x == y, 'saved/render regression: '+key+'/'+tag+'/'+suffix)
            samples[tag] = dict(inactive_stack_differences=delta, cpu=cpu[0],
                                wram_sha256=[sha(w) for w in raw])
        result[key] = dict(candidate_capture=a.name, parent_capture=b.name, samples=samples,
                           receipts=[sha((p/'receipt.json').read_bytes()) for p in (a, b)])
    return result


def ending(name):
    p, _, data = capture(name, False, 'highhop', 240, target=TARGET, expected_script=ending_route())
    for tag in [f'scene{i:03d}' for i in range(1, 161)]+['dismissed', 'walked', 'after_goal', 'file_reload']:
        raw = (p/(tag+'.wram.bin')).read_bytes()
        require(len(raw) == 0x20000 and len((p/(tag+'.vram.bin')).read_bytes()) == 0x10000,
                'ending dump size')
        data[tag] = raw
    info = boundary(data, False)
    font = read(RECIPE)['fonts']
    for tag, name in [('scene160', 'japanese'), ('dismissed', 'english'), ('file_reload', 'english')]:
        require(sha((p/(tag+'.vram.bin')).read_bytes()[0x9000:0x9800]) == font[name]['sha256'], 'ending font lifecycle: '+tag)
    for tag in ('after_goal', 'file_reload'):
        raw = (p/(tag+'.sram.bin')).read_bytes()
        require(len(raw) == 0x8000 and raw[0xd] == raw[0x1ba] == data['scene160'][0x1eaf], 'ending save copies')
    return dict(boundary=info, dodge=dodge(data), graphics=graphics(p, data, False),
                receipt=sha((p/'receipt.json').read_bytes()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-regressions', action='store_true')
    p.add_argument('--prefix', default='mazo-messages-reg-v2')
    p.add_argument('--ending', default='mazo-messages-ending-native-v2')
    p.add_argument('--capture-map', type=Path, help='explicit fresh capture names for interrupted cases')
    p.add_argument('--cases', help='comma-separated regression cases to run; qualification still checks all eleven')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    reviewed = admission()
    if args.run_regressions:
        selected = args.cases.split(',') if args.cases else list(REGRESSIONS)
        require(set(selected) <= set(REGRESSIONS), 'unknown regression case')
        for key, script in REGRESSIONS.items():
            if key not in selected:
                continue
            subprocess.run([sys.executable, str(ROOT/'tools/m1.py'), 'native', '--target', TARGET,
                '--script', str(ROOT/'recomp/inputs'/script), '--capture', f'{args.prefix}-{key}-candidate'], cwd=ROOT, check=True)
        return
    require(args.output is not None and not args.output.exists(), 'fresh report required')
    result = dict(admission=reviewed, rooms=rooms(),
        regressions=regressions(args.prefix, read(args.capture_map) if args.capture_map else None), ending=ending(args.ending),
        checker_sha256=sha(Path(__file__).read_bytes()), limits=[
            'Room/pipe/immunity/contact-position and first-boss placement fixtures; no completion writes.',
            'WRAM exception only inactive1F8 below equal SP; all CPU registers equal. No full-WRAM parity claim.',
            'Ordinary Mazo world/save identity, room190 traversal, unassisted fight and audible music remain open.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('PASS: both source messages/pixels, English font lifecycle, full ending and eleven retained regressions')


if __name__ == '__main__':
    main()
