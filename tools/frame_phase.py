#!/usr/bin/env python3
"""Check a suspect scene for frame or animation phase differences.

The tool runs the same dense-frame script on the reference and native hosts. It
then compares every native dump with every reference dump and reports the best
alignment. A small residual at a non-zero offset means a phase difference. A
large residual at every offset means a real rendering difference.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE_DIR = ROOT / 'local/probes/demo11-course-survey'


def load(path):
    return json.loads(Path(path).read_text())


def scene(directory, tag):
    wram = (directory / (tag + '.wram.bin')).read_bytes()
    framebuffer = (directory / (tag + '.fb.bgrx')).read_bytes()
    return {'mode': wram[0x100],
            'player': (int.from_bytes(wram[0x94:0x96], 'little'),
                       int.from_bytes(wram[0x96:0x98], 'little')),
            'framebuffer': framebuffer}


def rgb5_difference(left, right, width=256, height=224):
    expected = width * height * 4
    if len(left) != expected or len(right) != expected:
        return expected
    return sum(any(left[i + k] >> 3 != right[i + k] >> 3 for k in range(3))
               for i in range(0, expected, 4))


def dense_script(translevel, frames, step):
    source = (PROBE_DIR / ('course-%s.script' % translevel)).read_text()
    head = source.split('dump entry240')[0]
    body = head
    for index in range(frames):
        body += 'wait %d\ndump d%02d\n' % (step, index)
    return body + 'quit\n'


def capture(host, target, script_path, name):
    directory = ROOT / 'local/captures' / name
    if directory.exists():
        import shutil
        shutil.rmtree(directory)
    result = subprocess.run([sys.executable, str(ROOT / 'tools/m1.py'), host,
                             '--target', target, '--script', str(script_path),
                             '--capture', name],
                            cwd=ROOT, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise SystemExit(host + ' capture failed: ' + result.stderr[-200:])
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--translevel', required=True)
    parser.add_argument('--target', default='demo11-fix-batch-p')
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--step', type=int, default=20)
    args = parser.parse_args()

    script_path = ROOT / 'local/probes' / ('phase-%s.script' % args.translevel)
    script_path.write_text(dense_script(args.translevel, args.frames, args.step))

    captures = {}
    for host, suffix in (('reference', 'ref'), ('native', 'nat')):
        name = 'phase-%s-%s' % (args.translevel, suffix)
        captures[host] = capture(host, args.target, script_path, name)

    reference = [scene(captures['reference'], 'd%02d' % index) for index in range(args.frames)]
    native = [scene(captures['native'], 'd%02d' % index) for index in range(args.frames)]

    matrix = []
    best = None
    for i, left in enumerate(native):
        row = []
        for j, right in enumerate(reference):
            value = rgb5_difference(left['framebuffer'], right['framebuffer'])
            row.append(value)
            if best is None or value < best[0]:
                best = (value, i, j)
        matrix.append(row)

    same_state = all(native[index]['player'] == reference[index]['player'] for index in range(args.frames))

    def row_differences(left, right, width=256):
        rows = []
        expected = width * 224 * 4
        if len(left) != expected or len(right) != expected:
            return [224]
        for y in range(224):
            changed = 0
            for i in range(y * width * 4, (y + 1) * width * 4, 4):
                if any(left[i + k] >> 3 != right[i + k] >> 3 for k in range(3)):
                    changed += 1
            if changed:
                rows.append(y)
        return rows

    odd_rows = []
    for index in range(args.frames):
        if matrix[index][index] > 200:
            odd_rows.extend(row_differences(native[index]['framebuffer'],
                                            reference[index]['framebuffer']))
    zero_offset_ok = sum(1 for index in range(args.frames) if matrix[index][index] <= 200)
    if zero_offset_ok == args.frames:
        verdict = 'identical'
    elif best[0] < 200 and best[2] != best[1]:
        verdict = 'phase'
    elif odd_rows and max(odd_rows) < 8:
        verdict = 'top-lines'
    else:
        verdict = 'rendering'
    result = {
        'translevel': args.translevel,
        'frames': args.frames,
        'step': args.step,
        'best_residual_pixels': best[0],
        'best_native_frame': best[1],
        'best_reference_frame': best[2],
        'offset': best[2] - best[1],
        'player_state_equal_at_same_index': same_state,
        'zero_offset_residuals': [matrix[index][index] for index in range(args.frames)],
        'matrix': matrix,
        'verdict': verdict,
    }
    output = ROOT / 'local/reports' / ('phase-%s.json' % args.translevel)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
                      ('translevel', 'best_residual_pixels', 'offset', 'verdict',
                       'player_state_equal_at_same_index')}, indent=2))
    print('report:', output.relative_to(ROOT))


if __name__ == '__main__':
    main()
