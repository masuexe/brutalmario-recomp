#!/usr/bin/env python3
"""Qualify Mazo completion without clearing the recipient's unrelated course00D."""
import argparse
import copy
import json
from pathlib import Path

from mazo_integrated_ending_route import route
from native_sprite_gap import packs
from prepare_mazo_progress import ROOT, PARENT, TARGET, RECIPE, VARIABLE, build
from qualify_mazo_cumulative import regression_capture
from qualify_mazo_ending import sphere
from qualify_mazo_primary_entry import REGRESSIONS, message_lifecycle
from qualify_mazo_messages import room_capture, tiles
from qualify_mazo_second import dodge, graphics
from qualify_world1_next_course import require, sha, word

SCRIPT = 'mazo-progress-recipient-reentry.script'
FULL_SCRIPT = '../../local/probes/mazo-progress/integrated-ending-v2.script'


def admission():
    recipe, parent, rom, original, payload = build()
    cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
    expected = copy.deepcopy(parent)
    expected.update(id=TARGET, parent_restoration=PARENT, parent_output=parent['output'],
                    scope='Preserve recipient00D completion; retain actual Mazo30 sphere-save path; experimental.')
    selected = next(p for p in expected['native_sprite_gap']['extra_packs'] if p['variable'] == VARIABLE)
    selected.update(source='local/native-modules/mazo-progress-v1', sha256=sha(payload))
    expected['native_adaptations'].append(dict(kind='version-scoped-mazo-progress',
        recipe=str(RECIPE.relative_to(ROOT)), recipe_sha256=sha(RECIPE.read_bytes()),
        note='Only A189AE STA1EAF is replaced. Unrelated recipient00D stays intact; actual sphere saves Mazo30.'))
    require(cfg == expected, 'target differs beyond the reviewed pack override')
    require((ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes() == rom,
            'recipient ROM changed')
    old, new = packs(PARENT), packs(TARGET)
    require(len(old) == len(new) == 61, 'selected pack count changed')
    for before, after in zip(old, new):
        descriptor = dict(before)
        if before['variable'] == VARIABLE:
            descriptor['sha256'] = sha(payload)
        require(after == descriptor, 'unreviewed inherited pack override')
        data = (ROOT / 'local/restoration' / TARGET / after['pack_file']).read_bytes()
        require(len(data) == after['size'] and sha(data) == after['sha256'], 'installed pack differs')
    require([i for i in range(len(payload)) if original[i] != payload[i]] == [37, 38, 39],
            'native actor differs beyond one store instruction')
    return dict(parent=PARENT, rom_sha256=sha(rom), original_code_sha256=sha(original),
                adapted_code_sha256=sha(payload), packs=len(new),
                recipes=len(cfg['native_sprite_gap']['manifests']),
                patches=len(cfg['native_sprite_gap']['extra_patches']), recipe_sha256=sha(RECIPE.read_bytes()))


def capture(name, target, script):
    text = (ROOT / 'recomp/inputs' / script).read_text()
    allowed = {0x1f11: 2, 0x1f17: (4, 8), 0x1f1f: 8, 0x100: 1, 0x1497: 1,
               0x94: 4, 0x19b8: 1, 0x19d8: 1, 0x88: 2, 0x71: 1}
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] in ('poke', 'forcepoke', 'pokefor'):
            permitted = allowed.get(int(fields[1], 16), ())
            permitted = (permitted,) if isinstance(permitted, int) else permitted
            require(len(bytes.fromhex(fields[2])) in permitted, 'undeclared fixture write')
    p, tags = regression_capture(name, target, script)
    states = {}
    for tag in tags:
        w = (p / (tag + '.wram.bin')).read_bytes()
        s = (p / (tag + '.sram.bin')).read_bytes()
        require(len(w) == 0x20000 and len(s) == 0x8000, 'incomplete memory: ' + tag)
        require(len((p / (tag + '.vram.bin')).read_bytes()) == 0x10000 and
                len((p / (tag + '.fb.bgrx')).read_bytes()) == 256*224*4, 'incomplete render: ' + tag)
        states[tag] = (w, s)
    return p, states


def receipt(name):
    p = ROOT / 'local/captures' / name / 'receipt.json'
    r = json.loads(p.read_text())
    return dict(capture=name, receipt_sha256=sha(p.read_bytes()), rom_sha256=r['rom_sha256'],
                binary_sha256=r['host_binary_sha256'], input_sha256=r['route_sha256'])


def message_at(directory, tag, room, source_version):
    source, _ = room_capture(f'mazo-messages-{room:03x}-source-v{source_version}', room, True)
    a = (directory / (tag + '.vram.bin')).read_bytes()
    b = (source / 'message.vram.bin').read_bytes()
    require(tiles(a) == tiles(b), 'integrated source message tiles differ')
    def crop(raw):
        require(len(raw) == 256*224*4, 'incomplete integrated message pixels')
        return bytes(raw[y*1024+x*4+c] >> 3 for y in range(48, 112)
                     for x in range(56, 200) for c in range(3))
    pixels = crop((directory / (tag + '.fb.bgrx')).read_bytes())
    require(pixels == crop((source / 'message.fb.bgrx').read_bytes()), 'integrated text pixels differ')
    return dict(source=source.name, source_receipt_sha256=sha((source / 'receipt.json').read_bytes()),
                tiles_sha256=sha(tiles(a)), pixels_sha256=sha(pixels))


def saved_goal(states):
    before = states['m2'][0]
    require(before[0x100] == 0x14 and word(before, 0x10b) == 0x190 and
            before[0x13bf] == 0x30 and before[0x1ed2] == 0 and before[0x1eaf] == 0x0f,
            'wrong actual-node entry baseline')
    require(states['walked'][0][0x1493] >= 0xe0, 'actual sphere goal missing')
    for tag, (w, _) in states.items():
        require(w[0x1eaf] == 0x0f and w[0x1f56] == 0x0f,
                'recipient00D or its WRAM backup changed: ' + tag)
    for tag in ('after_goal', 'file_reload'):
        w, s = states[tag]
        require(w[0x100] == 0x0e and w[0x1ed2] == w[0x1f79] == s[0x30] == s[0x1dd] == 0x80,
                'actual Mazo30 completion did not survive: ' + tag)
        require(s[0xd] == s[0x1ba] == 0x0f and w[0x1f2e] == 0,
                'foreign completion or observed event count differs')
    return dict(original_course=0x30, flag=0x80, save_offsets=[0x30, 0x1dd],
                recipient_course=0x0d, recipient_flag=0x0f, exit_count=0)


def boundary(name):
    p, states = capture(name, TARGET, SCRIPT)
    original = (ROOT / 'recomp/inputs/mazo-node-save-boundary-settled.script').read_text()
    require((ROOT / 'recomp/inputs' / SCRIPT).read_text().startswith(original[:-5]),
            'terminal fixture prefix differs from the qualified parent route')
    result = saved_goal(states)
    node = states['recipient_node'][0]
    require(node[0x100] == 0x0e and node[0xd72d] == 0x0d, 'wrong retained recipient node')
    for tag in ('recipient_course', 'recipient_later'):
        w, s = states[tag]
        require(w[0x100] == 0x14 and word(w, 0x10b) == 0x00d and w[0x13bf] == 0x0d,
                'recipient course is no longer enterable')
        require(w[0x1ed2] == s[0x30] == s[0x1dd] == 0x80, 'Mazo save lost after recipient re-entry')
    result.update(capture=name, message=message_lifecycle(p, states),
                  receipt_sha256=sha((p / 'receipt.json').read_bytes()))
    return result


def integrated(name):
    require((ROOT / 'recomp/inputs' / FULL_SCRIPT).read_text() == route(), 'generated integrated input differs')
    p, states = capture(name, TARGET, FULL_SCRIPT)
    result = saved_goal(states)
    data = {tag: row[0] for tag, row in states.items()}
    require(data['message191'][0x1426] == 2 and word(data['message191'], 0x10b) == 0x191,
            '191 guest message not reached')
    require(data['fight_entry'][0x100] == 0x14 and word(data['fight_entry'], 0x10b) == 0x151 and
            data['fight_entry'][0x13bf] == 0x30, '191 did not lead to the actual-context fight')
    require(set(range(7)) <= {b[0x1f400] for tag, b in data.items() if tag.startswith('c')},
            'reflected-hit/scripted-marker progression incomplete')
    require(all(data[f'c{cycle:02d}f32'][0x1f400] < 6 for cycle in (1, 2)),
            'a contact placement continued after reflection marker6')
    timer = []
    for tag, w in data.items():
        if tag.startswith(('highhop', 'scene')):
            for i in range(12):
                if w[0x14c8+i] and w[0x1ab10+i] & 8 and w[0x1ab9e+i] == 0x9c and w[0x1504+i] == 2:
                    timer.append(w[0x1570+i])
    require(len(set(timer)) >= 60 and max(timer) == 0x58 and timer == sorted(timer),
            'scripted cutscene did not complete')
    end, closed, touched = [data[t] for t in ('scene160', 'dismissed', 'walked')]
    require(end[0x1426] == 1 and sphere(end) and word(end, 0x10b) == 0x192,
            'scripted transfer did not reach message/sphere')
    require(closed[0x1426] == 0 and sphere(closed) and not sphere(touched),
            'ordinary dismissal and sphere touch absent')
    fonts = json.loads((ROOT / 'config/native-content/mazo-messages-v2.json').read_text())['fonts']
    for tag, language in [('scene160', 'japanese'), ('dismissed', 'english'), ('file_reload', 'english')]:
        raw = (p / (tag + '.vram.bin')).read_bytes()
        require(sha(raw[0x9000:0x9800]) == fonts[language]['sha256'], 'fight font lifecycle differs')
    result.update(capture=name, dodge=dodge(data), graphics=graphics(p, data, False),
                  cutscene_timer_values=len(set(timer)),
                  messages={'191': message_at(p, 'message191', 0x191, 3),
                            '192': message_at(p, 'scene160', 0x192, 2)},
                  receipt_sha256=sha((p / 'receipt.json').read_bytes()))
    return result


def regressions(prefix):
    result = {}
    for key, script in REGRESSIONS.items():
        a, tags = regression_capture(f'{prefix}-{key}', TARGET, script)
        b, old_tags = regression_capture(f'mazo-primary-reg-v1-{key}-candidate', PARENT, script)
        require(tags == old_tags, 'inherited regression sample list differs')
        traces = [{int(v[0]): v[2:] for line in (p / 'state-trace.txt').read_text().splitlines()
                   if (v := line.split(','))} for p in (a, b)]
        samples = {}
        for tag in tags:
            samples[tag] = {}
            frames = [json.loads((p / (tag + '.info.json')).read_text())['frame'] for p in (a, b)]
            require(frames[0] == frames[1] and traces[0][frames[0]] == traces[1][frames[1]],
                    'inherited CPU/frame regression: ' + key + '/' + tag)
            for suffix, size in [('wram.bin', 0x20000), ('sram.bin', 0x8000),
                                 ('vram.bin', 0x10000), ('fb.bgrx', 256*224*4)]:
                x, y = [(p / (tag + '.' + suffix)).read_bytes() for p in (a, b)]
                require(len(x) == size and x == y, 'inherited state regression: ' + key + '/' + tag + '/' + suffix)
                samples[tag][suffix] = sha(x)
        result[key] = dict(capture=a.name, parent=b.name, samples=samples,
                           receipts=[receipt(p.name) for p in (a, b)])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boundary', default='mazo-progress-boundary-v1')
    p.add_argument('--integrated', default='mazo-progress-integrated-ending-v2')
    p.add_argument('--prefix', default='mazo-progress-reg-v1')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'use a fresh report path')
    result = dict(admission=admission(), boundary=boundary(a.boundary), integrated=integrated(a.integrated),
                  regressions=regressions(a.prefix), checker_sha256=sha(Path(__file__).read_bytes()),
                  receipts=[receipt(a.boundary), receipt(a.integrated)],
                  limits=['Map, room190 pipe,191 obstacle and first-boss contact positions plus permanent immunity are fixtures.',
                          'No boss HP, phase, completion, event or save writes in the input.',
                          'Recipient eventFF/exit count0, unassisted traversal and earned fight acceptance remain open.',
                          'Existing saved00D bits are preserved; no retroactive save changes.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: actual-node assisted fight/ending and Mazo30 save; recipient00D stays intact')


if __name__ == '__main__':
    main()
