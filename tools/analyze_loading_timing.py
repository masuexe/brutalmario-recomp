#!/usr/bin/env python3
"""Summarize pinned Demo 1-1 loading probes without asserting machine equivalence.

Groups describe modes $11/$12 and counters $13/$14 for this ROM only.
Instruction hashes contain PC/M/X, not registers, memory, pixels or audio.
The main-loop and two APU polling pairs are explicitly counted and excluded
from the filtered hashes; the custom counter/APU loops remain included.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import struct

POLL = {0x806b, 0x806d, 0x8082, 0x8085, 0x80aa, 0x80ad}
SELECTED = ('mode', 'counter13', 'counter14')
OBSERVED = ('frame', 'clock', 'pc', 'v', 'h', *SELECTED)


def group(row):
    if row['mode'] == 17:
        return 'mode17'
    if row['mode'] == 18:
        if row['counter13'] == 252:
            return 'mode18_before_counter13'
        return 'mode18_load' if row['counter14'] == 193 else 'mode18_finalize'
    return None


def analyze(path):
    groups = {}
    events = []
    counter_loop = []
    previous = None
    with path.open() as source:
        for raw in csv.DictReader(source):
            row = {k: int(v) for k, v in raw.items()}
            observation = {k: row[k] for k in OBSERVED}
            if previous and any(row[k] != previous[k] for k in SELECTED):
                events.append(observation | {'previous_pc': previous['pc']})
            previous = row
            if row['pc'] == 0xfc13c and row['mode'] == 18:
                counter_loop.append(observation)
            key = group(row)
            if key is None:
                continue
            item = groups.setdefault(key, {
                'first': observation, 'opcodes': 0, 'nonpoll_opcodes': 0,
                'pcs': collections.Counter(), 'hash': hashlib.sha256()})
            item['last'] = observation
            item['opcodes'] += 1
            item['pcs'][row['pc']] += 1
            if row['pc'] not in POLL:
                item['nonpoll_opcodes'] += 1
                item['hash'].update(struct.pack('<IBB', row['pc'], row['m'], row['x']))
    for item in groups.values():
        item['pc_mx_sha256_excluding_named_polls'] = item.pop('hash').hexdigest()
        item['poll_counts'] = {f'{pc:06x}': item['pcs'][pc] for pc in sorted(POLL)}
        item['elapsed_master_clocks'] = item['last']['clock'] - item['first']['clock']
        item.pop('pcs')
    return {
        'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'events': events, 'groups': groups,
        'mode18_counter_loop': {'iterations': len(counter_loop),
                                'first': counter_loop[0] if counter_loop else None,
                                'last': counter_loop[-1] if counter_loop else None}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('traces', type=Path, nargs='+')
    args = parser.parse_args()
    runs = [analyze(path) for path in args.traces]
    keys = set.intersection(*(set(r['groups']) for r in runs))
    matching = {key: len({(r['groups'][key]['nonpoll_opcodes'],
                          r['groups'][key]['pc_mx_sha256_excluding_named_polls'])
                         for r in runs}) == 1 for key in sorted(keys)}
    print(json.dumps({'scope': __doc__.strip(), 'runs': runs,
                      'all_runs_equal_filtered_pc_mx_by_group': matching}, indent=2))


if __name__ == '__main__':
    main()
