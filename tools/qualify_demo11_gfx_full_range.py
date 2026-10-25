#!/usr/bin/env python3
"""Qualify the full-range course survey on the world graphics chain end.

The claim is bounded: every translevel loads and no Mario Start stall exists.
The script also checks the class counts, the newly playable entries and the
capture receipts.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-gfx-world8c'
REPORTS = ['demo11-course-survey-gfx-chain.json', 'demo11-course-survey-gfx-tail.json']
RANGES = [('001', '0C0', 192), ('0C1', '0FF', 63)]
NEWLY_PLAYABLE = {'047', '041', '037', '016', '031', '022', '020', '04C'}
YOSHI_HOUSE = {'077', '07B'}
EXPECTED = {'playable': 218, 'mode-0E': 28, 'mode-0D': 4, 'mode-0C': 2,
            'mode-0B': 2, 'mode-17': 1}


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'chain-end identity differs')
    entries = []
    for name, (first, last, count) in zip(REPORTS, RANGES):
        report = load(ROOT / 'local/reports' / name)
        require(report['target'] == TARGET, 'report target differs')
        require(report['first'] == first and report['last'] == last, 'report range differs')
        require(len(report['entries']) == count, 'report entry count differs')
        entries.extend(report['entries'])
    require(len(entries) == 255, 'survey does not cover 255 translevels')
    counts = {}
    for entry in entries:
        counts[entry['result']] = counts.get(entry['result'], 0) + 1
    require(counts == EXPECTED, 'class counts differ: ' + repr(counts))
    require(counts.get('mario-start-stall', 0) == 0, 'a Mario Start stall remains')
    playable = {entry['translevel'] for entry in entries if entry['result'] == 'playable'}
    require(NEWLY_PLAYABLE <= playable, 'a newly playable translevel regressed')
    house = {entry['translevel'] for entry in entries
             if (entry.get('samples', {}).get('entry600') or {}).get('room') == '0C5'}
    require(house == YOSHI_HOUSE, 'Yoshi House returns differ: ' + repr(house))
    for entry in entries:
        if entry['result'] == 'missing':
            raise SystemExit('missing capture: ' + entry['translevel'])
        receipt = load(ROOT / 'local/captures' / Path(entry['capture']).name / 'receipt.json')
        require(receipt['rom_sha256'] == cfg['output']['sha256'],
                'capture ROM differs: ' + entry['translevel'])
    print('Full-range survey on the world graphics chain passed: '
          '255 loads, zero stalls, 218 playable')


if __name__ == '__main__':
    main()
