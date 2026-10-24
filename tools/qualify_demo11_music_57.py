#!/usr/bin/env python3
"""Qualify the Demo 1-1 song 0x57 restoration candidate.

The candidate descends from `demo11-star-bgm` and installs one adapted legacy
song into the null recipient slot 0x57. The song comes from the reviewed
cheap-demo four-song upload group at `$44:A008`, sequence slot 3.

This check verifies the candidate identity, the installed payload, the slot
pointer and the survey captures. Translevel 001 no longer stalls at Mario
Start; it reaches gameplay. The capture has no input, so the player later falls
and the level reloads. That fall is not a music defect and is not claimed as a
course completion. An audible match is not claimed here.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restoration_targets import RESTORATIONS
from restore_star_world_1 import adapt_music, lorom

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
TARGET = 'demo11-music-57'
LEVEL = '001'


def sample_state(capture_directory, tag):
    body = (capture_directory / (tag + '.wram.bin')).read_bytes()
    return dict(mode=body[0x100], room=word(body, 0x10b), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], translevel=body[0x13BF])


def main():
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    require(sha(head) == cfg['base_output']['sha256'], 'base ROM identity differs')
    require(sha(candidate) == cfg['output']['sha256'], 'candidate ROM identity differs')

    donor = (ROOT / 'local/content-versions' / cfg['donor'] / 'rom.sfc').read_bytes()
    music = cfg['music']
    source = lorom(int(music['source_address'], 16))
    group = donor[source:source + music['source_group']['size']]
    require(sha(group) == music['source_group']['sha256'], 'donor group identity differs')
    payload = adapt_music(group, music)
    require(sha(payload) == music['adapted']['sha256'], 'adapted payload differs')
    require(len(payload) == music['adapted']['size'], 'adapted payload size differs')

    start = cfg['allocation']['offset']
    count = len(payload) - 1
    require(head[start:start + cfg['allocation']['size']] == bytes(cfg['allocation']['size']),
            'allocation is not empty on the base')
    require(candidate[start:start + 8] == b'STAR' + count.to_bytes(2, 'little') +
            (count ^ 0xFFFF).to_bytes(2, 'little'), 'RATS header differs')
    require(candidate[start + 8:start + 8 + len(payload)] == payload, 'installed payload differs')
    pointer = lorom(int(music['pointer_address'], 16))
    require(head[pointer:pointer + 3] == bytes(3), 'recipient slot is not empty')
    address = ((start + 8) // 0x8000) << 16 | 0x8000 | ((start + 8) & 0x7FFF)
    require(candidate[pointer:pointer + 3] == address.to_bytes(3, 'big'), 'slot pointer differs')

    changed = {index for index, (a, b) in enumerate(zip(head, candidate)) if a != b}
    allowed = set(range(pointer, pointer + 3)) | set(range(start, start + 8 + len(payload)))
    require(not (changed - allowed), 'candidate changed an unexpected byte')

    head_capture = ROOT / 'local/captures' / ('d11-survey-' + LEVEL)
    reference = ROOT / 'local/captures' / ('d11-music57-survey-' + LEVEL)
    native = ROOT / 'local/captures' / ('d11-music57-native-' + LEVEL)
    head_state = sample_state(head_capture, 'entry600')
    require(head_state['mode'] == 0x12, 'head no longer stalls at Mario Start')
    reference_early = sample_state(reference, 'entry240')
    require(reference_early['mode'] == 0x14, 'candidate does not reach gameplay')
    require(reference_early['room'] == 1, 'candidate room differs')
    for directory in (reference, native):
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + directory.name)
    keys = ('mode', 'room', 'lives', 'translevel')
    for tag in ('entry240', 'entry600'):
        reference_state = sample_state(reference, tag)
        native_state = sample_state(native, tag)
        if tag == 'entry240':
            require(all(reference_state[key] == native_state[key] for key in keys),
                    'native and reference differ: ' + tag)
        else:
            require(reference_state == native_state, 'native and reference differ: ' + tag)

    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']
    require(build['rom_sha256'] == sha(candidate) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'native build identity differs')
    print('Song 0x57 restoration checks passed: ' + TARGET)


if __name__ == '__main__':
    main()
