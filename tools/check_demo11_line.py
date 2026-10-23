#!/usr/bin/env python3
"""Run every Demo 1-1 line acceptance check in one pass.

Each check is an independent qualifier that pins its own ROM, build, captures and
report. This driver only sequences them and summarises pass/fail, so a rebase or a
future session can re-establish the whole line's status with one command.
"""
import sys
import traceback

CHECKS = [
    ('room106 graphics', 'qualify_demo11_room106'),
    ('room010 graphics (construction)', 'qualify_demo11_room010_gfx'),
    ('room010 music', 'qualify_demo11_room010_music'),
    ('room138 audio', 'qualify_demo11_room138_audio'),
    ('room0CB graphics', 'qualify_demo11_room0cb_gfx'),
    ('World 1 route parity', 'qualify_demo11_world1_routes'),
    ('engine flows', 'qualify_demo11_engine_flows'),
]


def main():
    results = []
    for label, module_name in CHECKS:
        try:
            module = __import__(module_name)
            sys.stdout.flush()
            module.main()
            results.append((label, 'pass', ''))
        except Exception as error:  # noqa: BLE001 - the driver reports every failure
            detail = traceback.format_exc(limit=2).strip().splitlines()[-1]
            results.append((label, 'FAIL', f'{error} | {detail}' if str(error) else detail))
    width = max(len(label) for label, _, _ in results)
    failed = 0
    print()
    print('Demo 1-1 line acceptance')
    print('-' * (width + 30))
    for label, status, detail in results:
        print(f'{label:<{width}}  {status}' + (f'  ({detail})' if detail else ''))
        failed += status != 'pass'
    print('-' * (width + 30))
    print(f'{len(results) - failed}/{len(results)} checks passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())