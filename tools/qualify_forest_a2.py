#!/usr/bin/env python3
"""Check restored A2 menus, real purchase/save, return, gate104 and unchanged normal route."""
import argparse
import json
from pathlib import Path
import re

from native_sprite_gap import packs
from prepare_forest_a2 import build, load, RECIPE
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_forest_course_identity import native_capture
from qualify_forest_hollow import NORMAL, assert_route as assert_hollow, state as hollow_state
from qualify_forest_shack import reference_capture, state as base_state
from qualify_world1_next_course import require
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r14'
PARENT = 'demo11-native-product-r13'
MENU = ('greeting', 'menu_first', 'menu_second', 'menu_third', 'menu_fourth',
        'menu_bottom', 'menu_top', 'denied', 'menu_restored')
PURCHASE = ('funded', 'purchased', 'owned_menu', 'duplicate')


def native(name, script, extras=None, target=None):
    target = target or TARGET
    if not extras:
        return native_capture(name, target, script)
    directory, receipt = capture(name, target, script, native=True)
    build_receipt = load(ROOT / 'local/build' / target / 'm1-build.json')
    for key in ('native_content', 'runtime_patches', 'analysis'):
        require(receipt[key] == build_receipt[key], 'native build identity differs')
    source = (ROOT / 'recomp/inputs' / script).read_bytes()
    require((directory / 'input.script').read_bytes() == b'turbo on\n' + source,
            'executed script differs')
    require('BRK' not in (directory / 'run.log').read_text(), 'native BRK')
    allowed = {0x1F11: 2, 0x1F17: 8, 0x1F1F: 8, 0x100: 1, 0x94: 4,
               0x1497: 1, 0x88: 2, 0x71: 1}
    allowed.update(extras)
    for line in source.decode().splitlines():
        fields = line.split()
        if fields and fields[0] in ('poke', 'forcepoke', 'pokefor'):
            require(len(bytes.fromhex(fields[2])) == allowed.get(int(fields[1], 16)),
                    'fixture writes outside declared scope')
    return directory, receipt


def module_usage(directory, used):
    rows = re.findall(r'\[native-seven\] bank=([0-9A-F]+) resolutions=(\d+) executed_page_instructions=(\d+)',
                      (directory / 'run.log').read_text())
    a2 = [(int(reads), int(executed)) for bank, reads, executed in rows if bank == '9D']
    require(len(a2) == 1 and (all(v > 0 for v in a2[0]) if used else a2[0] == (0, 0)),
            'A2 execution evidence differs')
    require(all(int(reads) == int(executed) == 0 for bank, reads, executed in rows if bank != '9D'),
            'unexpected external module dependency')
    return dict(resolutions=a2[0][0], executed_page_instructions=a2[0][1])


def shop(directory, tag):
    body, summary = base_state(directory, tag)
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    actors = [dict(actor, custom=body[0x1AB9E + actor['slot']], extra=body[0x1AB10 + actor['slot']])
              for actor in summary['actors']]
    result = {k: summary[k] for k in ('mode', 'room', 'lives', 'player_x', 'player_y', 'goal')}
    result.update(actors=actors, menu=list(body[0x1FC00:0x1FC03]),
                  money=int.from_bytes(body[0x11809:0x1180C], 'little'),
                  ownership=list(body[0x11810:0x1181A]), phase=body[0x150D], variant=body[0x1531],
                  flag=body[0x1EE5], save=[saved[0x43], saved[0x1F0]],
                  saved_money=int.from_bytes(saved[0x809:0x80C], 'little'), saved_owned=saved[0x811],
                  text_sha256=sha(body[0xAD00:0xAE80]), sram_sha256=sha(saved),
                  wram_sha256=sha(body), vram_sha256=summary['vram_sha256'])
    return body, result


def assert_shop(s, tag, funded=False):
    require(s['mode'] == 0x14 and s['room'] == 0x182 and s['lives'] == 4 and s['goal'] == 0,
            'shop room/life/goal differs: ' + tag)
    require(len(s['actors']) == 1 and s['actors'][0]['custom'] == 0xA2 and
            s['actors'][0]['status'] == 8 and s['actors'][0]['extra'] == 9 and s['variant'] == 1,
            'live hollow A2 absent: ' + tag)
    require(s['phase'] == (1 if tag == 'greeting' else 3 if tag == 'purchased' else 2),
            'wrong menu phase: ' + tag)
    selected = dict(menu_second=1, menu_third=2, menu_fourth=3, menu_bottom=3).get(tag, 0)
    require(s['menu'][2] == selected, 'wrong/clamped selector: ' + tag)
    expected_money = 2222 if tag == 'funded' else 1111 if funded else 0
    expected_owned = 1 if funded and tag != 'funded' else 0
    require(s['money'] == expected_money and s['ownership'] == [0, expected_owned] + [0] * 8,
            'purchase/currency state differs: ' + tag)


def main():
    global TARGET
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=(TARGET, 'demo11-native-forest-a2-v3'), default=TARGET)
    parser.add_argument('--prefix', default='forest-a2-r14')
    parser.add_argument('--output', default='local/reports/forest-a2-r14-acceptance-v1.json')
    args = parser.parse_args()
    TARGET = args.target
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    recipe = load(RECIPE)
    payload, audit = build(recipe)
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    adaptation = cfg['native_adaptations'][-1]
    require(adaptation['recipe_sha256'] == sha(RECIPE.read_bytes()) and
            adaptation['preparer_sha256'] == sha((ROOT / adaptation['preparer']).read_bytes()),
            'candidate preparation identity differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    parent = (ROOT / 'local/restoration' / PARENT / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], 'candidate')
    verify(parent, recipe['parent']['output'], 'parent')
    expected = bytearray(parent)
    offset = recipe['record']['recipient_offset']
    expected[offset:offset + 16] = bytes.fromhex(recipe['record']['native_raw'])
    for field in recipe['return_adaptation']['fields']:
        expected[lorom(int(field['address'], 16))] = int(field['after'], 16)
    require(expected == rom, 'candidate changes outside A2 record and new return entrance')
    installed = ROOT / 'local/restoration' / TARGET / recipe['code']['pack_file']
    require(installed.read_bytes() == payload, 'installed A2 pack differs')
    old_packs = {p['address']: p for p in packs(PARENT)}
    new_packs = {p['address']: p for p in packs(TARGET)}
    require(set(new_packs) - set(old_packs) == {'9DD7B4'} and
            all(new_packs[k] == v for k, v in old_packs.items()), 'inherited pack mappings changed')
    source = (ROOT / 'local/content-versions/demo-only-1/rom.sfc').read_bytes()
    menu, mr = native(args.prefix + '-menu-v1', 'forest-a2-menu-return.script')
    purchase, pr = native(args.prefix + '-purchase-v1', 'forest-a2-funded-purchase-save.script', {0x11809: 3})
    source_menu, sr = reference_capture('forest-a2-source-menu-v2', 'forest-a2-source-menu.script', source)
    source_purchase, spr = reference_capture('forest-a2-source-purchase-v1', 'forest-a2-source-purchase.script', source)
    pairs = {}
    for route, tags, a, b in (('menu', MENU, menu, source_menu), ('purchase', PURCHASE, purchase, source_purchase)):
        pairs[route] = {}
        for tag in tags:
            x, s = shop(a, tag)
            y, t = shop(b, tag)
            assert_shop(s, tag, route == 'purchase')
            assert_shop(t, tag, route == 'purchase')
            for key in ('mode', 'room', 'lives', 'player_x', 'player_y', 'goal', 'menu', 'money', 'ownership', 'phase', 'variant'):
                require(s[key] == t[key], 'official source functional mismatch: ' + tag + '/' + key)
            require(x[0xAD00:0xAE80] == y[0xAD00:0xAE80], 'official message tile buffer differs: ' + tag)
            pairs[route][tag] = dict(native=s, source=t, exact_message_bytes=384,
                                     limits='NPC motion, full VRAM/framebuffer and whole-engine state are not compared.')
    require(shop(menu, 'menu_top')[0][0xAD00:0xAE80] != shop(menu, 'denied')[0][0xAD00:0xAE80],
            'insufficient-funds response absent')
    require(shop(purchase, 'owned_menu')[0][0xAD00:0xAE80] != shop(purchase, 'duplicate')[0][0xAD00:0xAE80],
            'already-owned response absent')
    returns = {}
    for tag in ('returned', 'returned_stable', 'reentry'):
        _, s = shop(menu, tag)
        require(s['mode'] == 0x14 and s['lives'] == 4 and s['flag'] == 0x0F and s['save'] == [15, 15]
                and s['money'] == 0 and not any(s['ownership']), 'return changed life/clear/inventory')
        if tag == 'reentry':
            require(s['room'] == 0x182 and len(s['actors']) == 1 and s['actors'][0]['custom'] == 0xA2,
                    'ordinary Up re-entry failed')
        else:
            require(s['room'] == 0x11F and (s['player_x'], s['player_y']) == (800, 352), 'unsafe return position')
        returns[tag] = s
    persistence = {}
    for tag in ('returned', 'touched', 'clear_map', 'file_reload', 'onward'):
        _, s = shop(purchase, tag)
        cleared = tag in ('clear_map', 'file_reload', 'onward')
        require(s['lives'] == 4 and s['ownership'] == [0, 1] + [0] * 8 and
                s['money'] == (1112 if cleared else 1111) and s['flag'] == (143 if cleared else 15) and
                s['save'] == [s['flag']] * 2, 'earned purchase/save boundary differs: ' + tag)
        if cleared:
            require(s['saved_money'] == 1112 and s['saved_owned'] == 1, 'purchase not actually present in SRAM')
        else:
            require(s['saved_money'] == s['saved_owned'] == 0, 'pre-clear save control differs')
        persistence[tag] = s
    require(persistence['returned']['room'] == 0x11F and persistence['touched']['room'] == 0x43 and
            persistence['touched']['goal'] == 0xE0 and persistence['onward']['room'] == 0x114,
            'purchase route did not use real normal goal/onward entry')
    normal, nr = native(args.prefix + '-normal-v1', 'forest-hollow-normal-save.script')
    old, old_receipt = native_capture('forest-r13-hollow-normal-v2', PARENT, 'forest-hollow-normal-save.script')
    normal_states = {tag: hollow_state(normal, tag) for tag in NORMAL}
    assert_hollow(normal_states, 'normal')
    regression = {}
    for tag in NORMAL:
        regression[tag] = {}
        for suffix in ('wram.bin', 'sram.bin', 'vram.bin'):
            a, b = (normal / (tag + '.' + suffix)).read_bytes(), (old / (tag + '.' + suffix)).read_bytes()
            require(a == b, 'unchanged normal route differs: ' + tag + '/' + suffix)
            regression[tag][suffix] = dict(size=len(a), sha256=sha(a))
    gate, gr = native(args.prefix + '-gate104-v1', 'forest-a2-gate104.script', {0x19B8: 1, 0x19D8: 1})
    source_gate, sgr = reference_capture('forest-a2-source-gate104-v1', 'forest-a2-source-gate104.script', source)
    old_gate, ogr = native('forest-a2-parent-gate104-v1', 'forest-a2-gate104.script', {0x19B8: 1, 0x19D8: 1}, PARENT)
    gates = {}
    for tag, room in (('gate104', 0x104), ('gate104_after', 0x180)):
        a, s = shop(gate, tag)
        b, t = shop(source_gate, tag)
        require(s['mode'] == t['mode'] == 0x14 and s['room'] == t['room'] == room and
                s['lives'] == t['lives'] == 4 and a[0x1EAF] == b[0x1EAF] == 15,
                'original gate automatic exit differs')
        if tag == 'gate104':
            require(s['actors'] == t['actors'] and len(s['actors']) == 1 and
                    s['actors'][0]['custom'] == 0xA2 and a[0x71] == b[0x71] == 6,
                    'original gate A2/automatic pipe action absent')
        else:
            require((s['player_x'], s['player_y']) == (t['player_x'], t['player_y']) == (128, 352),
                    'gate destination player position differs')
        gates[tag] = dict(native=s, source=t,
                          limits='Gate entry has a 3-pixel player-Y phase difference; moving destination actors and full engine state are not compared.')
    require(shop(old_gate, 'gate104_after')[1]['room'] == 0x104, 'parent gate no longer reproduces missing actor')
    usage = {key: module_usage(path, used) for key, path, used in
             (('menu', menu, True), ('purchase', purchase, True), ('gate104', gate, True), ('normal', normal, False))}
    report = dict(target=TARGET, rom_sha256=sha(rom), parent=PARENT, audit=audit,
                  checker_sha256=sha(Path(__file__).read_bytes()), recipe_sha256=sha(RECIPE.read_bytes()),
                  receipts=dict(menu=mr, purchase=pr, normal=nr, old_normal=old_receipt,
                                gate=gr, old_gate=ogr, source_menu=sr, source_purchase=spr, source_gate=sgr),
                  source_pairs=pairs, returns=returns, persistence=persistence,
                  unchanged_normal=regression, gate104=gates, module_usage=usage,
                  limits=['Map/position/pipe/immunity and source destination/translevel fixtures are explicit.',
                          'Purchase funds2222 are a fixture; no ownership/completion/save bytes are written.',
                          'One real1111-price purchase and duplicate/insufficient controls; other purchases and ability effects remain open.',
                          'Original source return is incomplete; new secondary1FF is an explicit recipient adaptation.',
                          'No same-image source parity, full traversal, full visible/font or audio acceptance.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(output, sha(output.read_bytes()))


if __name__ == '__main__':
    main()
