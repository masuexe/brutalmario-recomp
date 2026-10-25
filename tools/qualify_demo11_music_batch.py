#!/usr/bin/env python3
"""Qualify the Demo 1-1 music batch A and fix batch B candidates.

`demo11-music-batch-a` installs five legacy songs from cheap-demo with the
validated id mapping. `demo11-fix-batch-b` adds nine extended graphics from
7hero on top of it.

This check verifies both candidates, the installed songs and graphics, and the
reviewed captures. Three stalled translevels reach gameplay:

- `043` fixes with music only (song `44`);
- `01E` fixes with music only (song `21`);
- `038` needs the graphics batch too; on music only it reaches gameplay and
  then returns to the map.

Entry and short gameplay are the claims. Full traversals, audible match and
other levels are not claimed.
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
HEAD = 'demo11-star-bgm'
MUSIC = 'demo11-music-batch-a'
FIX = 'demo11-fix-batch-b'
BASE_TEXT = 'Brutal Mario Demo11 Course Gfx A'


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
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    music = (ROOT / 'local/restoration' / MUSIC / 'rom.sfc').read_bytes()
    fix = (ROOT / 'local/restoration' / FIX / 'rom.sfc').read_bytes()
    music_cfg = json.loads((ROOT / 'config/restorations' / (MUSIC + '.json')).read_text())
    fix_cfg = json.loads((ROOT / 'config/restorations' / (FIX + '.json')).read_text())
    require(sha(head) == music_cfg['base_output']['sha256'], 'music base differs')
    require(sha(music) == music_cfg['output']['sha256'], 'music candidate differs')
    require(sha(music) == fix_cfg['base_output']['sha256'], 'fix base differs')
    require(sha(fix) == fix_cfg['output']['sha256'], 'fix candidate differs')

    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    tool = load_tool()
    cheap_groups = groups(donor)
    for track in music_cfg['music_tracks']:
        song = int(track['id'], 16)
        index = (song - 0x20) // 4
        slot = (song - 0x20) % 4
        group = donor[cheap_groups[index]:cheap_groups[index] + 6136]
        config, payload = tool.walk(group, slot, int.from_bytes(group[2:4], 'little'))
        require(sha(payload) == track['adapted']['sha256'], 'payload differs: ' + track['id'])
        pointer = lorom(int(track['pointer_address'], 16))
        require(head[pointer:pointer + 3] == bytes(3), 'base slot not empty: ' + track['id'])
        address = int.from_bytes(music[pointer:pointer + 3], 'big')
        start = lorom(address)
        header = music[start - 8:start]
        require(header[:4] == b'STAR', 'missing RATS block: ' + track['id'])
        count = int.from_bytes(header[4:6], 'little')
        require(count == len(payload) - 1, 'music count differs: ' + track['id'])
        require(music[start:start + len(payload)] == payload, 'music payload differs: ' + track['id'])
        require(music[start + len(payload):start + len(payload) + 4] == bytes(4), 'music trailer differs')
        allocation = track['allocation']
        require(allocation['offset'] >= 0 and
                start - 8 >= allocation['offset'] and
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
        size = len(compressed)
        start = data - 8
        allocation = fix_cfg['allocation']
        require(allocation['offset'] <= start and
                start + 8 + size <= allocation['offset'] + allocation['size'],
                'gfx block outside its allocation')

    head_captures = {'01E': 'd11-retarget-survey2-01E', '038': 'd11-retarget-survey2-038',
                     '043': 'd11-retarget-survey2-043'}
    music_captures = {'01E': 'd11-musicb-survey-01E', '038': 'd11-musicb-survey-038',
                      '043': 'd11-musicb-survey-043'}
    fix_captures = {'01E': 'd11-fixb-survey-01E', '038': 'd11-fixb-survey-038',
                    '043': 'd11-fixb-survey-043'}

    def state(capture, tag):
        body = (ROOT / 'local/captures' / capture / (tag + '.wram.bin')).read_bytes()
        return body[0x100]

    for translevel, capture in head_captures.items():
        require(state(capture, 'entry600') == 0x12, 'head no longer stalls: ' + translevel)
    for translevel in ('01E', '043'):
        require(state(music_captures[translevel], 'entry600') == 0x14,
                'music batch does not fix: ' + translevel)
    require(state(music_captures['038'], 'entry600') == 0x0E,
            'music only capture for 038 changed as reviewed')
    for translevel, capture in fix_captures.items():
        require(state(capture, 'entry600') == 0x14, 'fix batch does not fix: ' + translevel)
        receipt = json.loads((ROOT / 'local/captures' / capture / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(fix), 'capture ROM differs: ' + translevel)
        native = 'd11-fixb-native-' + translevel
        for tag in ('entry240', 'entry600'):
            reference_state = capture_state(ROOT, capture, tag)
            native_state = capture_state(ROOT, native, tag)
            for key in ('mode', 'room', 'lives', 'translevel'):
                require(reference_state[key] == native_state[key],
                        'native and reference differ: ' + translevel + '/' + tag + '/' + key)
        native_receipt = json.loads((ROOT / 'local/captures' / native / 'receipt.json').read_text())
        require(native_receipt['rom_sha256'] == sha(fix), 'native capture ROM differs: ' + translevel)

    build_path = ROOT / 'local/build' / FIX / 'm1-build.json'
    if build_path.exists():
        build = json.loads(build_path.read_text())
        binary = ROOT / 'local/build' / FIX / RESTORATIONS[FIX]['binary']
        require(build['rom_sha256'] == sha(fix) and
                build['binary_sha256'] == sha(binary.read_bytes()),
                'native build identity differs')
    print('Music batch A and fix batch B checks passed')


if __name__ == '__main__':
    main()
