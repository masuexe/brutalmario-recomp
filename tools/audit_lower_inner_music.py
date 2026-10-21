#!/usr/bin/env python3
"""Compare the lower-inner donor's bank-local cues with existing recipient songs.

Read-only structural evidence: compare reachable note, instrument and call graphs,
ignoring relocated pointers and unreachable padding. This is not a listening test.
Only the reviewed command subset is supported; unsupported songs are rejected.
"""
import argparse
import json
from pathlib import Path

from prepare_rom import verify
from restore_star_world_1 import lorom, sha

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = {0xda: 1, 0xdb: 1, 0xde: 1, 0xdf: 1, 0xe0: 1, 0xe2: 1,
              0xe7: 1, 0xe9: 3, 0xef: 3, 0xf0: 0, 0xf1: 3, 0xf2: 3}


def song_graph(data, base, sequence):
    def word(address):
        offset = address - base
        if not 0 <= offset <= len(data) - 2:
            raise ValueError('music pointer exceeds the uploaded image')
        return int.from_bytes(data[offset:offset+2], 'little')

    cache, active = {}, set()

    def track(address):
        if address in cache:
            return cache[address]
        if address in active:
            raise ValueError('recursive music call')
        active.add(address)
        cursor, result = address, []
        for _ in range(10000):
            if not base <= cursor < base + len(data):
                raise ValueError('music track exceeds the uploaded image')
            command = data[cursor-base]
            cursor += 1
            if command == 0:
                break
            arguments = []
            if command < 0x80:
                if cursor-base >= len(data):
                    raise ValueError('truncated duration')
                if data[cursor-base] < 0x80:
                    arguments = [data[cursor-base]]
                    cursor += 1
            elif command >= 0xda:
                if command not in PARAMETERS:
                    raise ValueError(f'unsupported music command {command:02X}')
                count = PARAMETERS[command]
                arguments = list(data[cursor-base:cursor-base+count])
                if len(arguments) != count:
                    raise ValueError('truncated music command')
                cursor += count
                if command == 0xe9:
                    arguments = [track(arguments[0] | arguments[1] << 8), arguments[2]]
            result.append([command, arguments])
        else:
            raise ValueError('music track exceeds the command budget')
        active.remove(address)
        cache[address] = result
        return result

    offset = sequence - base
    if data[offset+4:offset+8] != b'\xff\x00' + (sequence+2).to_bytes(2, 'little'):
        raise ValueError('unsupported intro/loop header')
    return [[track(pointer) if (pointer := word(pattern+i)) else None
             for i in range(0, 16, 2)]
            for pattern in (word(sequence), word(sequence+2))]


def audit():
    versions = json.loads((ROOT / 'config/content-versions.json').read_text())['versions']
    images = {}
    for key in ('cheap-demo', 'demo-only-1'):
        pin = next(item['output'] for item in versions if item['id'] == key)
        images[key] = (ROOT / 'local/content-versions' / key / 'rom.sfc').read_bytes()
        verify(images[key], pin, key)
    donor, recipient = images['cheap-demo'], images['demo-only-1']
    group = donor[lorom(0x3f8008):lorom(0x3f8008)+6136]
    verify(group, {'size': 6136, 'sha256':
                  'da36affbc31a2ddcdd647334f4413509d79bba3f801e22730997b741704d840f'},
           'room117 donor music bank')
    assert group[:4] == bytes.fromhex('f0170068') and group[-4:] == bytes(4)
    comparisons = []
    for cue, sequence, song_id in (('course', 0x6800, 0x60), ('cap', 0x6808, 0x79)):
        left = song_graph(group[4:-4], 0x6800, sequence)
        entry = lorom(0x0fe000) + song_id * 3
        address = int.from_bytes(recipient[entry:entry+3], 'big')
        offset = lorom(address)
        count = int.from_bytes(recipient[offset:offset+2], 'little')
        assert recipient[offset+2:offset+4] == bytes.fromhex('0054')
        right = song_graph(recipient[offset+4:offset+4+count], 0x5400, 0x5400)
        matches = [[part, channel] for part in range(2) for channel in range(8)
                   if left[part][channel] == right[part][channel]]
        assert len(matches) == (16 if cue == 'cap' else 12)
        comparisons.append({
            'cue': cue, 'donor_sequence': f'{sequence:04X}',
            'recipient_song': f'{song_id:02X}', 'recipient_pointer': f'{address:06X}',
            'identical_reachable_graph': left == right,
            'matching_part_channels': matches, 'total_part_channels': 16,
            'donor_graph_sha256': sha(json.dumps(left, separators=(',', ':')).encode()),
            'recipient_graph_sha256': sha(json.dumps(right, separators=(',', ':')).encode()),
        })
    return {'scope': __doc__.strip(), 'inputs': {key: sha(value) for key, value in images.items()},
            'donor_group': {'address': '3F8008', 'size': len(group), 'sha256': sha(group)},
            'comparisons': comparisons,
            'limits': 'Course song60 is a revised arrangement, not byte-identical donor audio. '
                      'No global music-id mapping or complete supported-command coverage is claimed.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'local/reports/lower-inner-music-identity.json')
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    for item in report['comparisons']:
        print(f"{item['cue']}: recipient ${item['recipient_song']}, "
              f"{len(item['matching_part_channels'])}/16 matching part/channels; "
              f"exact graph={item['identical_reachable_graph']}")


if __name__ == '__main__':
    main()
