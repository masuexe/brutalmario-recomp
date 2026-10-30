#!/usr/bin/env python3
"""Append input commands to a running practice game.

The live console reads the cheat script by byte offset, so append complete lines
to the same file. This tool keeps the write small and flushed for the running
game.
"""
import argparse
from pathlib import Path


def append(play_dir, lines):
    path = play_dir / 'cheats.script'
    if not path.parent.is_dir():
        raise SystemExit('missing play directory: ' + str(path.parent))
    with path.open('a', encoding='utf-8') as handle:
        for line in lines:
            handle.write(line.rstrip() + '\n')
        handle.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--play-dir', type=Path, required=True)
    parser.add_argument('--file', type=Path, action='append')
    parser.add_argument('--line', action='append')
    args = parser.parse_args()
    lines = []
    for path in args.file or []:
        lines.extend(path.read_text().splitlines())
    lines.extend(args.line or [])
    if not lines:
        raise SystemExit('no lines to append')
    append(args.play_dir, lines)
    print('appended', len(lines), 'lines to', args.play_dir / 'cheats.script')


if __name__ == '__main__':
    main()
