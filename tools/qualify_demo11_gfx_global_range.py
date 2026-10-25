#!/usr/bin/env python3
"""Qualify the full-range survey on the global graphics chain.

The chain adds 53 extended graphics IDs and makes 18 more translevels playable.
The claim is bounded: all 255 translevels load, no stall remains, 233 stay in
gameplay. Translevel 069 changed its idle behaviour; the user must confirm it.
"""
import json
from pathlib import Path

from m1 import ROOT
from qualify_world1_next_course import require, sha

ROOT = Path(ROOT)
TARGET = 'demo11-gfx-global13'
REPORTS = ['demo11-course-survey-gg-chain.json', 'demo11-course-survey-gg-tail.json']
RANGES = [('001', '0C0', 192), ('0C1', '0FF', 63)]
EXPECTED = {'playable': 233, 'mode-0E': 14, 'mode-0C': 4, 'mode-0D': 2,
            'mode-17': 1, 'mode-0B': 1}
GAINED = {'023', '02D', '05E', '063', '065', '06A', '06B', '06E', '071', '072',
          '075', '076', '07A', '07E', '082', '083', '092', '093'}
BEHAVIOUR_CHANGE = {'069'}
YOSHI_HOUSE = {'077', '07B'}


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
    require(GAINED <= playable, 'a graphics-restored level regressed')
    require(BEHAVIOUR_CHANGE.isdisjoint(playable),
            'the documented behaviour change did not happen')
    house = {entry['translevel'] for entry in entries
             if (entry.get('samples', {}).get('entry600') or {}).get('room') == '0C5'}
    require(house == YOSHI_HOUSE, 'Yoshi House returns differ: ' + repr(house))
    for entry in entries:
        receipt = load(ROOT / 'local/captures' / Path(entry['capture']).name / 'receipt.json')
        require(receipt['rom_sha256'] == cfg['output']['sha256'],
                'capture ROM differs: ' + entry['translevel'])
    print('Global graphics survey passed: 255 loads, zero stalls, 233 playable')


if __name__ == '__main__':
    main()
