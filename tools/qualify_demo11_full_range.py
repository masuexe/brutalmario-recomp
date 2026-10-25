#!/usr/bin/env python3
"""Qualify the full-range Demo 1-1 course survey on the candidate chain end.

The qualifier reads the two survey reports for translevels 0x001-0x0C0 and
0x0C1-0x0FF. It checks the report identity, the result classes and the capture
receipts. The claim is bounded: every translevel loads; there is no Mario Start
stall. Entry and short gameplay are the claims.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-fix-batch-o2'
YOSHI_HOUSE = {'077', '07B'}


def load(path):
    return json.loads(Path(path).read_text())


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    require(sha(rom) == cfg['output']['sha256'], 'chain-end identity differs')

    reports = [
        load(ROOT / 'local/reports/demo11-course-survey-chain-o.json'),
        load(ROOT / 'local/reports/demo11-course-survey-tail.json'),
    ]
    entries = []
    for report, first, last, count in zip(reports, (0x001, 0x0C1), (0x0C0, 0x0FF),
                                          (192, 63)):
        require(report['target'] == TARGET, 'report target differs')
        require(report['first'] == f'{first:03X}' and report['last'] == f'{last:03X}',
                'report range differs')
        require(len(report['entries']) == count, 'report entry count differs')
        entries.extend(report['entries'])

    require(len(entries) == 255, 'full range does not cover 255 translevels')
    seen = set()
    playable = 0
    deaths = 0
    house = 0
    for entry in entries:
        translevel = entry['translevel']
        require(translevel not in seen, 'duplicate translevel: ' + translevel)
        seen.add(translevel)
        require(entry['rom_sha256'] == sha(rom), 'entry ROM differs: ' + translevel)
        receipt = load(ROOT / entry['capture'] / 'receipt.json')
        require(receipt['rom_sha256'] == sha(rom), 'capture ROM differs: ' + translevel)
        require(entry['result'] != 'mario-start-stall', 'stall found: ' + translevel)
        samples = entry['samples']
        if entry['result'] == 'playable':
            require(samples['entry240']['mode'] in ('13', '14'),
                    'no gameplay at entry 240: ' + translevel)
            require(samples['entry600']['mode'] == '14',
                    'playable claim without gameplay: ' + translevel)
            playable += 1
            continue
        if translevel in YOSHI_HOUSE:
            require(samples['entry240']['mode'] == '0E' and
                    samples['entry600']['mode'] == '0E',
                    'Yoshi house entry does not return to the map: ' + translevel)
            house += 1
            continue
        require(samples['entry240']['mode'] == '14',
                'no gameplay at entry 240: ' + translevel)
        require(samples['entry600']['lives_minus_one'] <
                samples['entry240']['lives_minus_one'],
                'unexplained non-playable entry: ' + translevel)
        deaths += 1

    require(playable == 207, 'playable count differs: ' + str(playable))
    require(deaths == 46, 'death count differs: ' + str(deaths))
    require(house == 2, 'map-return count differs: ' + str(house))
    print('Full-range survey checks passed: 255 translevels, 207 playable, '
          '46 no-input deaths, 2 map returns')


if __name__ == '__main__':
    main()
