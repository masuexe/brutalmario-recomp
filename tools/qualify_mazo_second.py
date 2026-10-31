#!/usr/bin/env python3
"""Qualify the second-boss ground-check dodge and optional full GFX282 upload."""
import argparse
import hashlib
import json
from pathlib import Path

from mazo_second_route import second_route
from native_sprite_gap import identity
from qualify_mazo_orb_sequence import ROOT, SOURCE, TARGET, require
from restoration_targets import RESTORATIONS
from runtime_patches import patch_plan
from restore_star_world_1 import graphics_pointer, lz2


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def capture(name, donor, mode, hops=80, target=TARGET):
    p = ROOT / 'local/captures' / name
    r = read(p / 'receipt.json')
    script = second_route(donor, mode, hops)
    require((p/'input.script').read_text() == ('' if donor else 'turbo on\n') + script, 'executed input differs')
    require(r['script_sha256' if donor else 'route_sha256'] == sha(script.encode()), 'input digest')
    if donor:
        require(r['rom_sha256'] == SOURCE == sha((ROOT/'local/content-versions/mazo/rom.sfc').read_bytes()), 'source ROM')
        require(r['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'source options')
        for field, file in [('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so'),
                            ('frontend_sha256', 'local/build/snesref/snesref')]:
            require(r[field] == sha((ROOT/file).read_bytes()), field)
    else:
        b = read(ROOT/'local/build'/target/'m1-build.json')
        cfg = read(ROOT/'config/restorations'/(target+'.json'))
        require(r['stage'] == 'native' and r['target'] == target, 'native role')
        require(r['rom_sha256'] == b['rom_sha256'] == cfg['output']['sha256'], 'native ROM')
        require(r['host_binary_sha256'] == b['binary_sha256'] == sha((
            ROOT/'local/build'/target/RESTORATIONS[target]['binary']).read_bytes()), 'native binary')
        require(r['native_content'] == b['native_content'] == identity(target), 'native module identity')
        require(r['runtime_patches'] == b['runtime_patches'] == patch_plan(), 'native runtime')
        require(r['analysis'] == b['analysis'], 'native analysis')
    log = (p/'run.log').read_text()
    require((' quit' if donor else 'exit: script quit after') in log and 'TIMEOUT' not in log
            and 'timeout at' not in log.lower(), 'capture did not complete')
    tags = ['contact0'] + [f'c{c:02d}f{i:02d}' for c in range(1, (6 if donor else 5)+1) for i in range(1, 33)]
    if mode == 'idle':
        tags += ['last_orb_cycle'] + [f'late{i:03d}' for i in range(1, 251)]
    else:
        tags += ['ground_attack', 'before_jump', 'jump_check', 'survived_ground_attack']
        tags += ([f'follow{i:03d}' for i in range(1, 161)] if mode == 'jump' else
                 [f'highhop{i:03d}' for i in range(1, hops+1)])
    data = {}
    for tag in tags:
        b = (p/(tag+'.wram.bin')).read_bytes()
        require(len(b) == 0x20000 and len((p/(tag+'.vram.bin')).read_bytes()) == 0x10000, f'{tag}: dump size')
        data[tag] = b
    return p, r, data


def dodge(data):
    before, jump, after = [data[t] for t in ('before_jump', 'jump_check', 'survived_ground_attack')]
    for b in (before, jump, after):
        require(b[0x100] == 0x14 and int.from_bytes(b[0x10b:0x10d], 'little') == 0x151
                and b[0x1f400] == 6 and b[0x71] != 9, 'invalid second-boss dodge state')
        require(b[0x150d] == 1 and b[0x14d1] == 8 and b[0x1aba7] == 0x9c, 'main second boss missing')
    require(before[0xcb] == 8 and before[0x15b5] == 0xc0 and before[0x77] & 4, 'grounded attack baseline')
    require(jump[0xcb] == 8 and jump[0x15b5] < 0xb8 and not jump[0x77] & 4, 'jump did not cross ground check in air')
    require(int.from_bytes(jump[0x96:0x98], 'little') < 336, 'player did not jump')
    require(all(not (b[0x14c8+i] and b[0x1ab9e+i] == 0x9c and b[0x1504+i] == 13
                     and b[0x151c+i]) for b in (jump, after) for i in range(12)), 'fatal child generated during dodge')
    return dict(before_y=int.from_bytes(before[0x96:0x98], 'little'),
                jump_y=int.from_bytes(jump[0x96:0x98], 'little'), timer=jump[0x15b5])


def fatal_control(data):
    late = [(t, b) for t, b in data.items() if t.startswith('late')]
    actor = next(((t, b) for t, b in late if any(b[0x14c8+i] and b[0x1ab9e+i] == 0x9c
                  and b[0x1504+i] == 13 and b[0x151c+i] == 1 for i in range(12))), None)
    require(actor is not None, 'idle control lacks forced-fall child')
    death = next(((t, b) for t, b in late if t > actor[0] and b[0x71] == 9
                  and int.from_bytes(b[0x96:0x98], 'little') >= 512), None)
    require(death is not None, 'idle control lacks death below arena')
    return dict(child=actor[0], death=death[0], y=int.from_bytes(death[1][0x96:0x98], 'little'))


def graphics(p, data, donor):
    rom = (ROOT/'local/content-versions/mazo/rom.sfc').read_bytes()
    gfx, _ = lz2(rom, graphics_pointer(rom, 0x282), limit=0x10000)
    require(len(gfx) == 4096, 'donor GFX282 decode size')
    tags = []
    for tag, b in data.items():
        if not tag.startswith('highhop'):
            continue
        if (p/(tag+'.vram.bin')).read_bytes()[0xf000:0x10000] == gfx:
            require(b[0x100] == 0x14 and int.from_bytes(b[0x10b:0x10d], 'little') == 0x151
                    and b[0x1f413] == 3 and b[0x71] != 9, 'GFX282 not in live later sequence')
            require(any(b[0x14c8+i] and b[0x1ab9e+i] == 0x9c and b[0x1504+i] == 23 for i in range(12)),
                    'later variant23 missing')
            tags.append(tag)
    require(tags, 'no complete GFX282 upload')
    return dict(first=tags[0], last=tags[-1], samples=len(tags), vram_start='F000', decoded_sha256=sha(gfx))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-highhops', help='optional completed native resource capture')
    parser.add_argument('--native-hops', type=int, default=80)
    parser.add_argument('--source-highhops', help='optional completed official source resource capture')
    parser.add_argument('--source-hops', type=int, default=120)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report')
    result, receipts = {}, {}
    for donor, host in ((False, 'native'), (True, 'source')):
        for mode in ('idle', 'jump'):
            name = f'mazo-second-{host}-{mode}-v1'
            p, r, data = capture(name, donor, mode)
            result[name] = fatal_control(data) if mode == 'idle' else dodge(data)
            receipts[name] = sha((p/'receipt.json').read_bytes())
        name = args.source_highhops if donor else args.native_highhops
        if name:
            p, r, data = capture(name, donor, 'highhop', args.source_hops if donor else args.native_hops)
            result[name] = dict(dodge=dodge(data), graphics=graphics(p, data, donor))
            receipts[name] = sha((p/'receipt.json').read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(scope=__doc__, target=TARGET, results=result,
        receipts=receipts, limitations=['Entry, first-boss placement and permanent immunity fixtures.',
        'No position or boss-state writes after first-boss progression; jumps use normal input.',
        'No earned whole-fight clear, save, unassisted traversal or audible music acceptance.']), indent=2)+'\n')
    print('PASS: grounded death and normal jump dodge on both hosts; requested resource checks pass')


if __name__ == '__main__':
    main()
