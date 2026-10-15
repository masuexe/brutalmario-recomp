#!/usr/bin/env python3
"""Compare mode-3 opcode traces; identified polling loops remain explicit.

Equal filtered instruction sequences are not full CPU or hardware equivalence.
The six polling PCs are specific to the pinned Demo 1-1 ROM.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

POLL = {0x806b: 'main_wait_load_flag', 0x806d: 'main_wait_branch',
        0x8082: 'cmp_apu_ready', 0x8085: 'apu_ready_branch',
        0x80aa: 'cmp_apu_ack', 0x80ad: 'apu_ack_branch'}


def analyze(path):
    with path.open() as source:
        rows = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(source)]
    if not rows or rows[0]['mode'] != 3 or rows[-1]['mode'] != 4:
        raise ValueError('trace must contain the whole mode-3 load and its mode-4 exit')
    instructions = [(r['pc'], r['m'], r['x']) for r in rows if r['pc'] not in POLL]
    counts = collections.Counter(r['pc'] for r in rows)
    ready = [r for r in rows if r['pc'] == 0x8085]
    return {
        'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'first': rows[0], 'last': rows[-1], 'opcodes': len(rows),
        'elapsed_master_clocks': rows[-1]['clock'] - rows[0]['clock'],
        'poll_opcodes': {name: counts[pc] for pc, name in POLL.items()},
        'ready_wait_first': ready[0] if ready else None,
        'ready_wait_last': ready[-1] if ready else None,
        'nonpoll_opcodes': len(instructions),
        'nonpoll_pc_mx_sha256': hashlib.sha256(json.dumps(instructions).encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('traces', type=Path, nargs='+')
    args = parser.parse_args()
    runs = [analyze(path) for path in args.traces]
    print(json.dumps({'scope': __doc__.strip(), 'runs': runs,
                      'identical_nonpoll_pc_mx_sequences': len({
                          (r['nonpoll_opcodes'], r['nonpoll_pc_mx_sha256']) for r in runs}) == 1},
                     indent=2))


if __name__ == '__main__':
    main()
