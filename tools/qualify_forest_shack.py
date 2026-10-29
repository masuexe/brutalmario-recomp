#!/usr/bin/env python3
"""Qualify assisted shack switch, real Big Boo defeat, save and death boundaries."""
import argparse
import json
import re
from pathlib import Path

from prepare_rom import verify
from qualify_forest_course_identity import native_capture, sprite_list
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'demo11-native-product-r13'
NORMAL = ('node', 'active', 'room44', 'switch_before', 'switch_after', 'fight_ready',
          'on_throwblock', 'release', 'hit1', 'block2', 'hit2', 'block3', 'hit3',
          'clear_map', 'file_reload', 'onward')
DEATH = ('active', 'death_map', 'reentry')
BLOCKS = (0xE461, 0xE462, 0xE471, 0xE472, 0xE46D, 0xE46E, 0xE47D, 0xE47E)
PLANES = (0xC800, 0xE300, 0x1C800, 0x1E300)


def load(path):
    return json.loads(path.read_text())


def state(directory, tag):
    body = (directory / (tag + '.wram.bin')).read_bytes()
    saved = (directory / (tag + '.sram.bin')).read_bytes()
    vram = (directory / (tag + '.vram.bin')).read_bytes()
    require(len(body) == 0x20000 and len(saved) == 0x8000 and len(vram) == 0x10000,
            'incomplete dump: ' + str(directory / tag))
    actors = []
    for i in range(12):
        if body[0x14C8 + i]:
            actors.append(dict(slot=i, sprite=body[0x9E + i], status=body[0x14C8 + i],
                               x=body[0xE4 + i] | body[0x14E0 + i] << 8,
                               y=body[0xD8 + i] | body[0x14D4 + i] << 8))
    summary = dict(mode=body[0x100], room=word(body, 0x10B), lives=body[0xDBE],
                   player_x=word(body, 0x94), player_y=word(body, 0x96),
                   onoff=body[0x14AF], collision=body[0x5B], boss_phase=body[0xC2],
                   hits=body[0x1534], goal=body[0x1493], boss_clear=body[0x13C6],
                   flag=body[0x1EB7], save=[saved[0x15], saved[0x1C2]],
                   map=body[0x1F11], map_x=word(body, 0x1F17), map_y=word(body, 0x1F19),
                   blocks=[body[a] | body[a + 0x10000] << 8 for a in BLOCKS], actors=actors,
                   wram_sha256=sha(body), sram_sha256=sha(saved), vram_sha256=sha(vram))
    return body, summary


def reference_capture(name, script, rom):
    directory = ROOT / 'local/captures' / name
    receipt = load(directory / 'receipt.json')
    source = (ROOT / 'recomp/inputs' / script).read_bytes()
    require(receipt['rom_sha256'] == sha(rom) and receipt['script_sha256'] == sha(source),
            'reference ROM or script differs')
    require((directory / 'input.script').read_bytes() == source, 'reference executed script differs')
    require(receipt['frontend_sha256'] == sha((ROOT / 'local/build/snesref/snesref').read_bytes()),
            'reference frontend differs')
    core = ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so'
    require(receipt['core_sha256'] == sha(core.read_bytes()) and
            receipt['diagnostic_core_override'] is None, 'reference core differs')
    require(receipt['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled',
            'reference options differ')
    log = (directory / 'run.log').read_text().lower()
    require(' quit' in log and 'timeout' not in log and 'assertion failed' not in log,
            'reference route did not finish')
    return directory, receipt


def protected_stream(rom, table, room):
    slot = lorom(table) + room * 3
    address = int.from_bytes(rom[slot:slot + 3], 'little')
    offset = lorom(address)
    header = rom[offset - 8:offset]
    require(header[:4] == b'STAR' and word(header, 4) ^ word(header, 6) == 0xFFFF,
            'room stream has no valid bounded RATS header')
    size = word(header, 4) + 1
    require(0 < size <= 0x8000 and offset + size <= len(rom), 'room stream bounds invalid')
    return rom[offset:offset + size], dict(address=f'{address:06X}', size=size,
                                         sha256=sha(rom[offset:offset + size]))


def normal_assertions(states):
    for tag, (_, s) in states.items():
        cleared = tag in ('clear_map', 'file_reload', 'onward')
        flag = 0x81 if cleared else 1
        require(s['lives'] == 4 and s['flag'] == flag and s['save'] == [flag, flag],
                'life/completion/save differs: ' + tag)
    expected_rooms = dict(active=0x15, room44=0x44, switch_before=0x44, switch_after=0x44,
                          **{tag: 0x46 for tag in NORMAL[5:13]}, onward=0x123)
    for tag, room in expected_rooms.items():
        require(states[tag][1]['mode'] == 0x14 and states[tag][1]['room'] == room,
                'wrong room: ' + tag)
    before, after = states['switch_before'][1], states['switch_after'][1]
    require(before['onoff'] == 0 and not before['collision'] & 0x80 and
            after['onoff'] == 1 and after['collision'] & 0x80, 'real switch/collision change absent')
    active = states['active'][0]
    room44 = states['room44'][0]
    require((active[0x19BA], active[0x19DA]) == (0x44, 4) and
            (room44[0x19B8], room44[0x19D8]) == (0x46, 4), 'existing room exits differ')
    ready = states['fight_ready'][1]
    require(ready['onoff'] == 1 and ready['collision'] & 0x80 and ready['hits'] == 0 and
            ready['boss_phase'] == 2 and ready['actors'][0]['sprite'] == 0xC5 and
            ready['actors'][0]['status'] == 8 and ready['blocks'] == [0x12E] * 8,
            'boss or original throw blocks not ready')
    consumed = ()
    for tag, count, phase, new_block in (('hit1', 1, 5, 1), ('hit2', 2, 5, 0), ('hit3', 3, 6, 3)):
        s = states[tag][1]
        consumed += (new_block,)
        require(s['hits'] == count and s['boss_phase'] == phase and s['onoff'] == 1,
                'real boss damage absent: ' + tag)
        require(s['blocks'] == [0x25 if i in consumed else 0x12E for i in range(8)],
                'block consumption differs: ' + tag)
    end = states['hit3'][1]
    require(end['boss_clear'] == 1 and end['goal'] > 0 and not end['actors'],
            'third hit did not defeat the boss')
    for tag in ('clear_map', 'file_reload'):
        s = states[tag][1]
        require(s['mode'] == 0x0E and s['map'] == 0 and (s['map_x'], s['map_y']) == (0x188, 0x178),
                'onward node not reached: ' + tag)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', default='forest-r13-shack')
    parser.add_argument('--output', default='local/reports/forest-shack-acceptance-v1.json')
    args = parser.parse_args()
    output = ROOT / args.output
    require(not output.exists(), 'use a fresh report path')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    verify(rom, load(ROOT / 'config/restorations' / (TARGET + '.json'))['output'], TARGET)
    versions = {v['id']: v for v in load(ROOT / 'config/content-versions.json')['versions']}
    sources = {}
    for version in ('demo-1-1', 'demo-only-1', '7hero', 'cheap-demo'):
        donor = (ROOT / 'local/content-versions' / version / 'rom.sfc').read_bytes()
        verify(donor, versions[version]['output'], version)
        rows = {}
        for room in (0x15, 0x44, 0x46):
            rows[f'{room:03X}'] = {}
            for table, label in ((0x05E000, 'layer1'), (0x05E600, 'layer2')):
                raw, pin = protected_stream(donor, table, room)
                require(raw == protected_stream(rom, table, room)[0], 'official room stream differs')
                rows[f'{room:03X}'][label] = pin
            sprites = sprite_list(donor, room)
            require(sprites == sprite_list(rom, room), 'official sprite list differs')
            rows[f'{room:03X}']['sprites'] = dict(size=len(sprites), sha256=sha(sprites))
        sources[version] = dict(rom_sha256=sha(donor), rooms=rows)
    results = {}
    for route, tags, script in (('normal', NORMAL, 'forest-shack-normal-save.script'),
                                 ('death', DEATH, 'forest-shack-death-reentry.script')):
        version = 'v2' if route == 'death' else 'v1'
        native, native_receipt = native_capture(args.prefix + '-' + route + '-' + version, TARGET, script)
        ref, ref_receipt = reference_capture(args.prefix + '-' + route + '-ref-' + version, script, rom)
        mounts = re.findall(r'\[native-seven\] bank=([0-9A-F]+) resolutions=(\d+) executed_page_instructions=(\d+)',
                            (native / 'run.log').read_text())
        require(mounts and all(int(reads) == int(executed) == 0 for _, reads, executed in mounts),
                'external packs used; this reference comparison needs a new dependency review')
        host_states = {host: {tag: state(directory, tag) for tag in tags}
                       for host, directory in (('native', native), ('reference', ref))}
        for host, states in host_states.items():
            if route == 'normal':
                normal_assertions(states)
            else:
                for tag, mode, lives in (('active', 0x14, 4), ('death_map', 0x0E, 3), ('reentry', 0x14, 3)):
                    s = states[tag][1]
                    require(s['mode'] == mode and s['room'] == 0x15 and s['lives'] == lives and
                            s['flag'] == 1 and s['save'] == [1, 1] and s['onoff'] == 0,
                            'real death/re-entry differs: ' + host + '/' + tag)
        comparisons = {}
        for tag in tags:
            a, x = host_states['native'][tag]
            b, y = host_states['reference'][tag]
            for key in ('mode', 'room', 'lives', 'onoff', 'collision', 'boss_phase', 'hits',
                        'goal', 'boss_clear', 'flag', 'save', 'map', 'map_x', 'map_y', 'blocks'):
                require(x[key] == y[key], 'semantic mismatch: ' + tag + '/' + key)
            require(x['player_x'] == y['player_x'] and x['player_y'] == y['player_y'], 'player differs')
            require(len(x['actors']) == len(y['actors']), 'actor count differs')
            for actor, other in zip(x['actors'], y['actors']):
                require(all(actor[k] == other[k] for k in ('slot', 'sprite', 'status')), 'actor differs')
                require(all(min((actor[k] - other[k]) & 0xFFFF,
                                (other[k] - actor[k]) & 0xFFFF) <= 1 for k in ('x', 'y')),
                        'actor position differs by more than one pixel')
            require(all(a[start:start + 0x1B00] == b[start:start + 0x1B00] for start in PLANES),
                    'Map16 plane mismatch: ' + tag)
            comparisons[tag] = dict(native=x, reference=y, exact_map16_bytes=4 * 0x1B00)
        results[route] = dict(native_receipt=native_receipt, reference_receipt=ref_receipt,
                              captures=dict(native=str(native.relative_to(ROOT)),
                                            reference=str(ref.relative_to(ROOT))),
                              unused_external_mounts=len(mounts), samples=comparisons)
    report = dict(target=TARGET, rom_sha256=sha(rom), checker_sha256=sha(Path(__file__).read_bytes()),
                  official_sources=sources, routes=results,
                  limits=['Position/pipe-action/immunity fixtures bypass the P-switch/shell puzzle traversal.',
                          'Death uses position below the floor, followed by actual guest death and life loss.',
                          'Same-image reference agreement applies only to these pack-independent routes.',
                          'Moving actor coordinates permit one pixel; full WRAM/framebuffer parity is not claimed.',
                          'No audio, secret-exit, Dragon Coin or new manual acceptance claim.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: real switch, three block impacts, Big Boo defeat/save/reload and death/re-entry; {output}')


if __name__ == '__main__':
    main()
