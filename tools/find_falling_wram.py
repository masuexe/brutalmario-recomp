#!/usr/bin/env python3
"""Find addresses that fall monotonically in an attack capture.

The tool reads a sorted series of WRAM dumps and reports addresses whose value
never increases and drops by at least a threshold. A boss health counter is a
candidate. A timer also matches, so verify the result against a control.
"""
import argparse
from pathlib import Path


def scan(data, first=0x0800, last=0x2000, drop=2):
    found = []
    for address in range(first, last):
        values = [d[address] for d in data]
        if values[0] - values[-1] < drop:
            continue
        if all(b <= a for a, b in zip(values, values[1:])):
            found.append((values[0] - values[-1], address, values[0], values[-1]))
    found.sort(reverse=True)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--prefix', default='')
    parser.add_argument('--first', type=lambda v: int(v, 0), default=0x0800)
    parser.add_argument('--last', type=lambda v: int(v, 0), default=0x2000)
    parser.add_argument('--drop', type=int, default=2)
    args = parser.parse_args()
    files = sorted(p for p in args.capture.glob(args.prefix + '*.wram.bin'))
    if len(files) < 4:
        raise SystemExit('not enough dumps')
    found = scan([p.read_bytes() for p in files], args.first, args.last, args.drop)
    print('files', len(files), 'candidates', len(found))
    for amount, address, start, end in found[:20]:
        print(f'{address:04X} drop={amount} {start}->{end}')


if __name__ == '__main__':
    main()
