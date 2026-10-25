#!/usr/bin/env python3
"""Qualify the full-range survey on the boss room chain.

The boss chain fills the remaining subroom graphics and ports custom sprite 2B.
The outer translevel behavior must stay identical to the room 49 chain. Two
translevels change because their previously missing custom sprites now run:
070 (boss room chain 14C -> 14D) and 062 (a moving object now acts).
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-gfx-boss76'
PREVIOUS = 'demo11-sprite-room49'
REPORTS = ['demo11-course-survey-b76-chain.json', 'demo11-course-survey-b76-tail.json']
PREVIOUS_REPORTS = ['demo11-course-survey-r49-chain.json', 'demo11-course-survey-r49-tail.json']
EXPECTED = {'playable': 231, 'mode-0E': 14, 'mode-0C': 5, 'mode-0D': 2,
            'mode-17': 1, 'mode-13': 1, 'mode-0B': 1}


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'chain-end identity differs')
    entries = []
    for name in REPORTS:
        report = load(ROOT / 'local/reports' / name)
        require(report['target'] == TARGET, 'report target differs')
        entries.extend(report['entries'])
    require(len(entries) == 255, 'survey does not cover 255 translevels')
    counts = {}
    for entry in entries:
        counts[entry['result']] = counts.get(entry['result'], 0) + 1
    require(counts == EXPECTED, 'class counts differ: ' + repr(counts))
    require('mario-start-stall' not in counts, 'a Mario Start stall remains')
    for entry in entries:
        receipt = load(ROOT / 'local/captures' / Path(entry['capture']).name / 'receipt.json')
        require(receipt['rom_sha256'] == cfg['output']['sha256'],
                'capture ROM differs: ' + entry['translevel'])
    previous = []
    for name in PREVIOUS_REPORTS:
        previous.extend(load(ROOT / 'local/reports' / name)['entries'])
    new_by = {entry['translevel']: entry['result'] for entry in entries}
    old_by = {entry['translevel']: entry['result'] for entry in previous}
    diffs = [(tag, old_by.get(tag), new_by.get(tag)) for tag in sorted(set(old_by) | set(new_by))
             if old_by.get(tag) != new_by.get(tag)]
    require(not diffs, 'outer translevel behavior changed: ' + repr(diffs))

    serious = ROOT / 'local/captures' / 'long-070'
    body = (serious / 'f35.wram.bin').read_bytes()
    require(body[0x100] == 0x14, 'boss room chain does not reach gameplay')
    require(int.from_bytes(body[0x10B:0x10D], 'little') == 0x14D,
            'boss room chain does not reach room 14D')
    changed = ROOT / 'local/captures' / 'long-062'
    body = (changed / 'f35.wram.bin').read_bytes()
    require(body[0x100] == 0x0E, 'level 062 does not return to the map after the death')
    print('Boss chain survey passed: 255 loads, 231 playable, two documented sprite changes')


if __name__ == '__main__':
    main()
