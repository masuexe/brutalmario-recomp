#!/usr/bin/env python3
"""Compare exclusive interpreted work across full, matching native routes.

Body-entry counts and interpreted-opcode counts use different units. Their
ratio is not an AOT percentage. Reduced interpretation is not a speed claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

LEAVES = {
    # Address spans can overlap: report independently, never sum the leaf rows.
    'BuildCoordinatePairBank15': (0x15a023, 0x15a044, '15A023:M1X1'),
    'SubtractIndexedCoordinateWordBank15': (0x15a032, 0x15a044, '15A032:M1X1'),
    'AppendIndexedSpriteEntries': (0x13f13d, 0x13f192, '13F13D:M1X1'),
    'BuildIndexedSpriteEntries': (0x13f06f, 0x13f0c4, '13F06F:M1X1'),
    'BuildCoordinatePair': (0x13f1a7, 0x13f1d4, '13F1A7:M1X1'),
    'SubtractIndexedCoordinateWord': (0x13f1c2, 0x13f1d4, '13F1C2:M1X1'),
    'UploadIndexedPalette80': (0x169585, 0x16959e, '169585:M1X1'),
    'UploadIndexedPalette30': (0x13efb2, 0x13efce, '13EFB2:M1X1'),
    'ClearEightWramBytesUnlessSix': (0x169f2b, 0x169f3d, '169F2B:M1X1'),
    'CopyLevelBufferPointers': (0x0da6ba, 0x0da6cc, '0DA6BA:M1X1'),
    'CheckOverworldAccessMask': (0x04f87c, 0x04f8a5, '04F87C:M1X1'),
    'CopyEightWordsAndEightBytes': (0x0480b9, 0x0480df, '0480B9:M0X0'),
    'ReadByteAdvanceLoRomPointer': (0x00b983, 0x00b991, '00B983:M1X0'),
}


def analyze(directory):
    receipt = json.loads((directory / 'receipt.json').read_text())
    files = list((directory / 'coverage').glob('*/*.json'))
    if len(files) != 1:
        raise ValueError('requires one coverage checkpoint from an isolated session')
    raw = files[0].read_bytes()
    profile = json.loads(raw)
    if (profile.get('dropped_cost_samples') or profile.get('overflowed_tuples') or
            profile.get('journal_write_failures') or not profile.get('checkpoint_complete')):
        raise ValueError('incomplete or lossy coverage capture')
    manifest_raw = (directory / 'program-manifest.json').read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != profile['identity']['program_digest']:
        raise ValueError('manifest differs from captured program')
    manifest = json.loads(manifest_raw)
    cpu = [r for r in profile['costs'] if r.get('processor', 'snes_cpu') == 'snes_cpu']
    total = sum(r['interpreted_instructions'] for r in cpu)
    metrics = re.search(r'\[m1\] aot_bridge_entries=(\d+) interpreted_opcodes=(\d+)',
                        (directory / 'run.log').read_text())
    if not metrics or int(metrics[2]) != total:
        raise ValueError('coverage cost does not agree with exit opcode counter')
    leaves = {}
    for name, (lo, hi, key) in LEAVES.items():
        rows = [r for r in cpu if lo <= int(r['target_pc24'], 16) <= hi]
        leaves[name] = {
            'interpreted_instructions': sum(r['interpreted_instructions'] for r in rows),
            'interpreted_guest_cycles': sum(r['guest_cycles'] for r in rows),
            'analysis_disposition': manifest['nodes'].get(key, {}).get('disposition', 'absent'),
        }
    return {
        'capture': str(directory), 'rom_sha256': receipt['rom_sha256'],
        'route_sha256': receipt['route_sha256'],
        'host_binary_sha256': receipt['host_binary_sha256'],
        'runtime_patches': receipt['runtime_patches'],
        'coverage_sha256': hashlib.sha256(raw).hexdigest(),
        'program_digest': profile['identity']['program_digest'],
        'eligible_variants': sum(n['disposition'] == 'aot_eligible' for n in manifest['nodes'].values()),
        'compiled_body_entries': int(metrics[1]),
        'interpreted_instructions': total,
        'interpreted_guest_cycles': sum(r['guest_cycles'] for r in cpu),
        'main_wait_interpreted_instructions': sum(r['interpreted_instructions'] for r in cpu
                                                 if int(r['target_pc24'], 16) in (0x806b, 0x806d)),
        'leaves': leaves,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path, nargs='+')
    args = parser.parse_args()
    runs = [analyze(p) for p in args.captures]
    if len({(r['rom_sha256'], r['route_sha256'], json.dumps([(p['source'], p['source_sha256'], p['result_sha256'])
                                             for p in r['runtime_patches']], sort_keys=True))
            for r in runs}) != 1:
        parser.error('ROM, route or runtime patches differ')
    print(json.dumps({'scope': __doc__.strip(), 'runs': runs}, indent=2))


if __name__ == '__main__':
    main()
