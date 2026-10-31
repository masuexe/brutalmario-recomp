#!/usr/bin/env python3
"""Qualify assisted Mazo cutscene, ordinary goal and bounded persistence evidence."""
import argparse
import json
from pathlib import Path

from mazo_ending_route import ending_route
from prepare_mazo_gfx282 import CUMULATIVE_TARGET as TARGET, ROOT
from qualify_mazo_second import capture, dodge, graphics, require, sha
from restore_star_world_1 import graphics_pointer, lz2


def sphere(b):
    return any(b[0x14c8+i] and not b[0x1ab10+i] & 8 and b[0x9e+i] == 0x4a for i in range(12))


def boundary(data, donor):
    before = data['contact0']
    first = data['scene001']
    require(not before[0x1eaf] & 0x80 and first[0x1f413] == 3, 'invalid pre-ending baseline')
    require(first[0x100] == 0x14 and first[0x71] == 11, 'scripted cutscene missing')
    progress = []
    for tag, b in data.items():
        if not tag.startswith('scene'):
            continue
        for i in range(12):
            if b[0x14c8+i] and b[0x1ab10+i] & 8 and b[0x1ab9e+i] == 0x9c and b[0x1504+i] == 2:
                progress.append(b[0x1570+i])
    require(len(set(progress)) >= 60 and max(progress) == 0x58 and
            progress == sorted(progress), 'cutscene timer did not reach scripted room transfer')
    room = next(((t, b) for t, b in data.items() if t.startswith('scene') and b[0x100] == 0x14
                 and int.from_bytes(b[0x10b:0x10d], 'little') == 0x192), None)
    require(room is not None, 'no live ending room192')
    end, dismissed, walked, after, reload = [data[t] for t in
        ('scene160', 'dismissed', 'walked', 'after_goal', 'file_reload')]
    require(all(int.from_bytes(b[0x10b:0x10d], 'little') == 0x192 and b[0x71] != 9
                for b in (end, dismissed, walked)), 'ending goal room/player differs')
    require(end[0x100] == 0x14 and end[0x1426] == 1 and sphere(end), 'ending message/goal sphere missing')
    require(end[0x1eaf] == before[0x1eaf] | 0x80, 'guest corridor flag did not preserve low bits')
    require(dismissed[0x1426] == 0 and dismissed[0x100] == 0x14 and sphere(dismissed), 'normal message dismissal failed')
    require(0xe0 <= walked[0x1493] <= 0xff and not sphere(walked) and
            120 <= int.from_bytes(walked[0x94:0x96], 'little') <= 136, 'ordinary sphere touch missing')
    require(after[0x100] == 0x0e and after[0x1493] == 0 and after[0x1eaf] & 0x80,
            'goal did not return to map')
    if donor:
        require(after[0x1f2e] == before[0x1f2e]+1 and not reload[0x1eaf] & 0x80,
                'source goal/reset observation differs')
    else:
        require(after[0x1f2e] == before[0x1f2e] and reload[0x1eaf] & 0x80 and reload[0x100] == 0x0e,
                'native practice-count/persistence observation differs')
    return dict(first_live_192=room[0], cutscene_timer_values=len(set(progress)),
                initial_flag=before[0x1eaf], ending_flag=end[0x1eaf], reload_flag=reload[0x1eaf],
                goal_timer=walked[0x1493], goal_x=int.from_bytes(walked[0x94:0x96], 'little'),
                exit_count_before=before[0x1f2e], exit_count_after=after[0x1f2e],
                reset_mode=reload[0x100], practice_translevel=before[0x13bf])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', default='mazo-ending-cumulative-v2')
    p.add_argument('--source', default='mazo-ending-source-v2')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    require(not args.output.exists(), 'fresh report required')
    source_rom = (ROOT/'local/content-versions/mazo/rom.sfc').read_bytes()
    font, _ = lz2(source_rom, graphics_pointer(source_rom, 0x2a), limit=0x10000)
    result = {}
    for donor, host, name in ((False, 'native', args.native), (True, 'source', args.source)):
        directory, r, data = capture(name, donor, 'highhop', 120 if donor else 240,
                                      target=TARGET, expected_script=ending_route(donor))
        for tag in [f'scene{i:03d}' for i in range(1, 161)]+['dismissed', 'walked', 'after_goal', 'file_reload']:
            b = (directory/(tag+'.wram.bin')).read_bytes()
            require(len(b) == 0x20000 and len((directory/(tag+'.vram.bin')).read_bytes()) == 0x10000,
                    'ending dump size: '+tag)
            require(len((directory/(tag+'.sram.bin')).read_bytes()) == (0x800 if donor else 0x8000),
                    'ending SRAM size: '+tag)
            data[tag] = b
        info = boundary(data, donor)
        saved = {tag: (directory/(tag+'.sram.bin')).read_bytes() for tag in
                 ('contact0', 'scene160', 'after_goal', 'file_reload')}
        if donor:
            require(saved['scene160'] == saved['after_goal'] == saved['file_reload'],
                    'source SRAM observation differs')
        else:
            expected = data['scene160'][0x1eaf]
            require(all(saved[t][0xd] == saved[t][0x1ba] == expected for t in ('after_goal', 'file_reload')),
                    'native flag missing from both guest save copies')
        vram = (directory/'scene160.vram.bin').read_bytes()
        tiles = [int.from_bytes(vram[i:i+2], 'little') & 0x3ff
                 for i in range(0xa000+9*64+7*2, 0xa000+9*64+25*2, 2)]
        result[host] = dict(boundary=info, dodge=dodge(data), graphics=graphics(directory, data, donor),
                            receipt_sha256=sha((directory/'receipt.json').read_bytes()),
                            sram_sha256={t: sha(b) for t, b in saved.items()},
                            changed_save_bytes=sum(a != b for a, b in zip(saved['scene160'], saved['after_goal'])),
                            message_diagnostic=dict(font_matches_source=vram[0x9000:0x9800] == font,
                                                    row9_tiles=tiles),
                            samples={t: sha(b) for t, b in data.items() if t.startswith('scene')})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(target=TARGET, results=result,
        limits=['Entry/first-boss position/immunity fixtures; no boss or completion writes.',
                'Guest cutscene transfers into192, guest B0/A9 sets1EAF bit80, normal B/right touches sphere.',
                'Native practice translevel75 does not increment the exit count; source30 increments it.',
                'Native guest flag persists in both save copies/reload; ordinary Mazo world/save identity remains open.',
                'Japanese message rendering differs; native row is blank and font is absent.',
                'No unassisted full level, correct whole-world progression or audible music acceptance.']), indent=2)+'\n')
    print('PASS: real cutscene transfer, message dismissal, sphere goal and bounded native flag persistence')


if __name__ == '__main__':
    main()
