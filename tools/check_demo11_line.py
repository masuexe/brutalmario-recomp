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
    ('lower-left course route', 'qualify_demo11_star1_route'),
    ('Star World course BGM', 'qualify_demo11_star_bgm'),
    ('upper-left Bay Star route', 'qualify_demo11_star_upper_left_route'),
    ('upper-right Plains Star route', 'qualify_demo11_star_upper_right_route'),
    ('lower-right Snow Star route', 'qualify_demo11_star_lower_right_route'),
    ('lower-inner Valley Star route', 'qualify_demo11_star_lower_inner_route'),
    ('upper-inner Cave Star route', 'qualify_demo11_star_upper_inner_route'),
    ('middle-right Sky Star route', 'qualify_demo11_star_middle_right_route'),
    ('course music retarget', 'qualify_demo11_course_music_retarget'),
    ('song 0x57 restoration', 'qualify_demo11_music_57'),
    ('course graphics A', 'qualify_demo11_course_gfx_a'),
    ('music batch A / fix batch B', 'qualify_demo11_music_batch'),
    ('music batch C / fix batch D', 'qualify_demo11_music_batch_cd'),
    ('graphics fix batches E / F', 'qualify_demo11_gfx_batches_ef'),
    ('music batch G', 'qualify_demo11_music_batch_g'),
    ('graphics fix batches H / I', 'qualify_demo11_gfx_batches_hi'),
    ('music batch J / graphics K1-M', 'qualify_demo11_batches_jklm'),
    ('music batch N / graphics O1-O2', 'qualify_demo11_batches_no'),
    ('full-range course survey', 'qualify_demo11_full_range'),
    ('graphics batch P', 'qualify_demo11_batch_p'),
    ('storm Dragon Coin VRAM', 'qualify_demo11_storm_coins'),
    ('world graphics batches', 'qualify_demo11_gfx_worlds'),
    ('world graphics full survey', 'qualify_demo11_gfx_full_range'),
    ('custom sprites World 2-4', 'qualify_demo11_sprites_w234'),
    ('sprite window relocations', 'qualify_demo11_sprite_windows'),
    ('final custom sprite', 'qualify_demo11_sprite_final'),
    ('space budget', 'check_space_budget'),
    ('final sprite full survey', 'qualify_demo11_sprite_final_range'),
    ('global graphics batches', 'qualify_demo11_gfx_global'),
    ('global graphics full survey', 'qualify_demo11_gfx_global_range'),
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
