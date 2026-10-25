#!/usr/bin/env python3
"""Qualify the Demo 1-1 music batch C and fix batch D candidates.

`demo11-music-batch-c` installs songs 0x55, 0x56 and 0x57 from cheap-demo on
top of fix batch B. `demo11-fix-batch-d` adds five extended graphics from
7hero.

The reviewed captures fix four more stalled translevels:

- `04B` with music only (song `56`);
- `0A5` with music only (song `57`);
- `00E` with song `56` and graphics `11C`;
- `01F` with song `55` and graphics `1A7`;
- `06D` with graphics `203`-`205` (song `45` was already present).

Translevel `001` reaches gameplay and then returns to the map because the
scripts have no input. Entry and short gameplay are the claims.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha
from restoration_targets import RESTORATIONS
from restore_star_world_1 import graphics_pointer, lorom, lz2, pointer_offset

ROOT = Path(ROOT)
BASE = 'demo11-fix-batch-b'
MUSIC = 'demo11-music-batch-c'
FIX = 'demo11-fix-batch-d'
NEW_FIXED = ('00E', '01F', '04B', '06D', '0A5')


def load_tool():
    path = ROOT / 'tools/derive_legacy_song.py'
    spec = importlib.util.spec_from_file_location('derive_legacy_song', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def groups(rom):
    result = []
    start = 0
    while True:
        index = rom.find(bytes.fromhex('f0170068'), start)
        if index < 0:
            return result
        group = rom[index:index + 6136]
        if group[4 + 0x40:4 + 0x60] != bytes(32) or any(group[4:4 + 0x40]):
            result.append(index)
        start = index + 1


def capture_state(root, capture, tag):
    body = (root / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
    return {'mode': body[0x100], 'room': int.from_bytes(body[0x10B:0x10D], 'little'),
            'lives': body[0x0DBE], 'translevel': body[0x13BF]}


def main():
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    music = (ROOT / 'local/restoration' / MUSIC / 'rom.sfc').read_bytes()
    fix = (ROOT / 'local/restoration' / FIX / 'rom.sfc').read_bytes()
    music_cfg = json.loads((ROOT / 'config/restorations' / (MUSIC + '.json')).read_text())
    fix_cfg = json.loads((ROOT / 'config/restorations' / (FIX + '.json')).read_text())
    require(sha(base) == music_cfg['base_output']['sha256'], 'music base differs')
    require(sha(music) == music_cfg['output']['sha256'], 'music candidate differs')
    require(sha(music) == fix_cfg['base_output']['sha256'], 'fix base differs')
    require(sha(fix) == fix_cfg['output']['sha256'], 'fix candidate differs')

    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    tool = load_tool()
    cheap_groups = groups(donor)
    for track in music_cfg['music_tracks']:
        song = int(track['id'], 16)
        group = donor[cheap_groups[(song - 0x20) // 4]:][:6136]
        config, payload = tool.walk(group, (song - 0x20) % 4,
                                    int.from_bytes(group[2:4], 'little'))
        require(sha(payload) == track['adapted']['sha256'], 'payload differs: ' + track['id'])
        pointer = lorom(int(track['pointer_address'], 16))
        require(base[pointer:pointer + 3] == bytes(3), 'base slot not empty: ' + track['id'])
        address = int.from_bytes(music[pointer:pointer + 3], 'big')
        start = lorom(address)
        require(music[start - 8:start - 4] == b'STAR', 'missing RATS block: ' + track['id'])
        count = int.from_bytes(music[start - 4:start - 2], 'little')
        require(count == len(payload) - 1, 'music count differs: ' + track['id'])
        require(music[start:start + len(payload)] == payload, 'music payload differs: ' + track['id'])
        allocation = track['allocation']
        require(start - 8 >= allocation['offset'] and
                start + len(payload) + 4 <= allocation['offset'] + allocation['size'],
                'music block outside allocation')

    gfx_donor = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
    for asset in fix_cfg['assets']:
        source = graphics_pointer(gfx_donor, int(asset['source_id'], 16))
        decoded, compressed = lz2(gfx_donor, source)
        slot = pointer_offset(int(asset['target_id'], 16))
        require(music[slot:slot + 3] == b'\xff' * 3, 'gfx base slot not empty')
        address = int.from_bytes(fix[slot:slot + 3], 'little')
        data = lorom(address)
        header = fix[data - 8:data]
        require(header[:4] == b'STAR', 'gfx RATS block missing')
        check, installed = lz2(fix, address)
        require(check == decoded and installed == compressed, 'gfx data differs')
        allocation = fix_cfg['allocation']
        require(data - 8 >= allocation['offset'] and
                data + len(compressed) <= allocation['offset'] + allocation['size'],
                'gfx block outside allocation')

    head_captures = {tag: 'd11-retarget-survey2-' + tag
                     for tag in ('00E', '01F', '04B', '06D', '0A5')}
    for translevel, capture in head_captures.items():
        require(capture_state(ROOT, capture, 'entry600')['mode'] == 0x12,
                'head no longer stalls: ' + translevel)
    for translevel in ('04B', '0A5'):
        require(capture_state(ROOT, 'd11-musicc-survey-' + translevel, 'entry600')['mode'] == 0x14,
                'music batch does not fix: ' + translevel)
    for translevel in NEW_FIXED:
        capture = 'd11-fixd-survey-' + translevel
        state = capture_state(ROOT, capture, 'entry600')
        require(state['mode'] == 0x14, 'fix batch does not fix: ' + translevel)
        receipt = json.loads((ROOT / 'local/captures' / capture / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(fix), 'capture ROM differs: ' + translevel)
        native = 'd11-fixd-native-' + translevel
        native_path = ROOT / 'local/captures' / native / ('entry600.wram.bin')
        if native_path.exists():
            for tag in ('entry240', 'entry600'):
                reference_state = capture_state(ROOT, capture, tag)
                native_state = capture_state(ROOT, native, tag)
                for key in ('mode', 'room', 'lives', 'translevel'):
                    require(reference_state[key] == native_state[key],
                            'native and reference differ: ' + translevel + '/' + tag + '/' + key)
    require(capture_state(ROOT, 'd11-fixd-survey-001', 'entry240')['mode'] == 0x14,
            'translevel 001 does not reach gameplay')
    require(capture_state(ROOT, 'd11-fixd-survey-001', 'entry600')['mode'] == 0x0E,
            'translevel 001 no longer returns to the map as recorded')

    build_path = ROOT / 'local/build' / FIX / 'm1-build.json'
    if build_path.exists():
        build = json.loads(build_path.read_text())
        binary = ROOT / 'local/build' / FIX / RESTORATIONS[FIX]['binary']
        require(build['rom_sha256'] == sha(fix) and
                build['binary_sha256'] == sha(binary.read_bytes()),
                'native build identity differs')
    print('Music batch C and fix batch D checks passed')


if __name__ == '__main__':
    main()
