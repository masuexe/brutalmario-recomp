#!/usr/bin/env python3
"""Qualify the Demo 1-1 course-music retarget candidate.

The candidate descends from `demo11-star-bgm` and changes the course music byte
of 17 stalled levels from legacy-family song ids to the verified new-family
equivalents in `config/music-mapping.json`. It installs no new song data.

This check verifies the candidate identity, the pinned patch sites, and the
survey captures. Seven of the retargeted translevels reach gameplay on the
candidate while the head captures stall at Mario Start. The other retargeted
levels still need follow-up work.
"""
import hashlib
import json
from pathlib import Path

from m1 import ROOT
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restoration_targets import RESTORATIONS

ROOT = Path(ROOT)
HEAD = 'demo11-star-bgm'
TARGET = 'demo11-course-music-retarget'
FIXED = ('015', '021', '03C', '048', '04E', '054', '056')
ALL_PATCHED = ('00D', '015', '01A', '021', '02C', '034', '03C', '048', '04D',
               '04E', '052', '054', '055', '056', '062', '06F', '070')


def main():
    head = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    candidate = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / TARGET / '..' / (TARGET + '.json')).resolve().read_text())
    require(sha(candidate) == cfg['output']['sha256'], 'candidate ROM identity differs')
    require(sha(head) == cfg['base_output']['sha256'], 'base ROM identity differs')
    changed = [index for index, (a, b) in enumerate(zip(head, candidate)) if a != b]
    require(len(changed) == len(cfg['code_patches']), 'unexpected changed byte count')
    for patch in cfg['code_patches']:
        offset = lorom(int(patch['address'], 16))
        require(head[offset] == int(patch['before'], 16), 'patch site moved: ' + patch['address'])
        require(candidate[offset] == int(patch['after'], 16), 'patch value differs: ' + patch['address'])

    for translevel in ALL_PATCHED:
        head_dir = ROOT / 'local/captures' / ('d11-survey-' + translevel)
        candidate_dir = ROOT / 'local/captures' / ('d11-retarget-survey-' + translevel)
        require((candidate_dir / 'entry600.wram.bin').exists(), 'missing candidate capture: ' + translevel)
        require((head_dir / 'entry600.wram.bin').exists(), 'missing head capture: ' + translevel)
    for translevel in FIXED:
        head_state = (ROOT / 'local/captures' / ('d11-survey-' + translevel) / 'entry600.wram.bin').read_bytes()
        candidate_state = (ROOT / 'local/captures' / ('d11-retarget-survey-' + translevel) / 'entry600.wram.bin').read_bytes()
        require(head_state[0x100] == 0x12, 'head no longer stalls: ' + translevel)
        require(candidate_state[0x100] == 0x14, 'candidate does not reach gameplay: ' + translevel)
        require(word(candidate_state, 0x10b) == word(head_state, 0x10b),
                'candidate room differs: ' + translevel)

    for translevel in FIXED:
        reference = ROOT / 'local/captures' / ('d11-retarget-survey-' + translevel)
        native = ROOT / 'local/captures' / ('d11-retarget-native-' + translevel)
        for sample in ('entry240', 'entry600'):
            require((native / (sample + '.wram.bin')).exists(),
                    'missing native sample: ' + translevel + '/' + sample)
            require(sample_state(native, sample) == sample_state(reference, sample),
                    'native and reference differ: ' + translevel + '/' + sample)
        for directory in (reference, native):
            receipt = json.loads((directory / 'receipt.json').read_text())
            require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + directory.name)

    registry = RESTORATIONS[TARGET]
    build = json.loads((ROOT / 'local/build' / TARGET / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / TARGET / registry['binary']
    require(build['rom_sha256'] == sha(candidate) and
            build['binary_sha256'] == sha(binary.read_bytes()),
            'candidate build identity differs')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / 'BrutalMarioDemo11StarWorldBgmSNESRecomp'
    require(build['rom_sha256'] == sha(head) and
            build['binary_sha256'] == sha(binary.read_bytes()), 'head build identity differs')
    print('Course music retarget checks passed: ' + TARGET)


def sample_state(capture_directory, tag):
    body = (capture_directory / (tag + '.wram.bin')).read_bytes()
    return dict(mode=body[0x100], room=word(body, 0x10b), x=word(body, 0x94),
                y=word(body, 0x96), lives=body[0x0DBE], translevel=body[0x13BF])


def lorom(address):
    bank = (address >> 16) & 0xFF
    offset = (bank & 0x7F) * 0x8000 + (address & 0x7FFF)
    return offset


if __name__ == '__main__':
    main()
