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
    ('whole-line byte audit', 'audit_demo11_line'),
    ('reachability audit', 'audit_demo11_reachability'),
    ('World 1-1 goal/clear', 'qualify_demo11_world1_1'),
    ('sprite ports 8D/0B', 'qualify_demo11_sprites'),
    ('World 1 route repair', 'qualify_demo11_world1_route'),
    ('room106 music fix', 'qualify_demo11_room106_music'),
    ('castle sprite 06', 'qualify_demo11_castle_sprite06'),
    ('Star1 graphics', 'qualify_demo11_star1_gfx'),
    ('Star batch graphics', 'qualify_demo11_star_gfx_batch'),
    ('Star music 54/2E', 'qualify_demo11_star_music'),
    ('historical Star entry samples', 'qualify_demo11_star_sprites'),
    ('safe Star sprites and routes', 'qualify_demo11_star_sprites_safe'),
    ('lower-inner cap expiry/music', 'qualify_demo11_lower_inner_music'),
    ('Star palette, fuel, flame, Santa', 'qualify_demo11_star_visuals'),
    ('center warp-star route/display', 'qualify_demo11_center_route'),
    ('Forest Star course port', 'qualify_demo11_star_forest'),
    ('node-scoped music dispatch', 'qualify_demo11_node_music'),
]


def main():
    results = []
    for label, module_name in CHECKS:
        try:
            module = __import__(module_name)
            sys.stdout.flush()
            status = module.main()
            if status:
                raise RuntimeError(f'check returned {status}')
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
