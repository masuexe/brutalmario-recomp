#!/usr/bin/env python3
"""Check five reflected impacts, the scripted marker and second-boss arrival in Mazo 151."""
import argparse
import hashlib
import json
from pathlib import Path

from mazo_reflect_route import ROOT, route
from native_sprite_gap import identity
from qualify_mazo_orb_sequence import SOURCE, TARGET, require
from restoration_targets import RESTORATIONS
from runtime_patches import patch_plan

TAGS = ['contact0'] + [f'c{c:02d}f{i:02d}' for c in range(1, 13) for i in range(1, 33)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def states(directory):
    result = []
    for tag in TAGS:
        b = (directory / (tag + '.wram.bin')).read_bytes()
        require(len(b) == 0x20000, f'{tag}: WRAM size')
        require(len((directory / (tag + '.vram.bin')).read_bytes()) == 0x10000, f'{tag}: VRAM size')
        actors = [i for i in range(12) if b[0x14c8+i] == 8 and b[0x1ab10+i] & 8
                  and b[0x1ab9e+i] == 0x9c]
        result.append(dict(tag=tag, mode=b[0x100], room=int.from_bytes(b[0x10b:0x10d], 'little'),
                           count=b[0x1f400], enabled=b[0x1fe00], reaction=b[0x1fe01],
                           player_y=int.from_bytes(b[0x96:0x98], 'little'), action=b[0x71],
                           actors=[dict(slot=i, variant=b[0x1504+i], phase=b[0xc2+i],
                                        timer=b[0x15ac+i], x=b[0xe4+i] | b[0x14e0+i] << 8,
                                        y=b[0xd8+i] | b[0x14d4+i] << 8) for i in actors],
                           wram_sha256=sha(b)))
    require(result[0]['count'] == 0, 'route did not start with zero hits')
    arrival = next((i for i, s in enumerate(result) if any(a['variant'] == 1 for a in s['actors'])), None)
    require(arrival is not None, 'second boss not reached')
    live = result[:arrival+1]
    require(all(s['mode'] == 0x14 and s['room'] == 0x151 for s in live), 'death/room change before arrival')
    counts = [s['count'] for s in live]
    require(set(counts) == set(range(7)) and counts[-1] == 6, 'stage counter sequence missing')
    require(all(y-x in (0, 1) for x, y in zip(counts, counts[1:])), 'hit count skipped or reset')
    reflect = [(i, s) for i, s in enumerate(live) if s['enabled'] == 1 and any(
        a['variant'] == 9 and a['phase'] == 1 for a in s['actors'])]
    require(reflect and any(s['reaction'] for s in live), 'reflection reaction/return actors missing')
    first = next(i for i, s in enumerate(live) if s['count'] == 1)
    require(first > 0 and live[first-1]['enabled'] == 1 and any(
        a['variant'] == 9 and a['phase'] == 1 and a['y'] >= 0x130
        for a in live[first-1]['actors']), 'first hit lacks preceding active reflection')
    require(any(a['variant'] == 0 and a['phase'] == 7 for s in live for a in s['actors']),
            'stage transition sequence missing')
    events = []
    for before, after in zip(live, live[1:]):
        if before['count'] == after['count']:
            continue
        scripted = (before['count'], after['count']) == (3, 4)
        require(any(a['variant'] == (11 if scripted else 10) for a in after['actors']),
                'missing transition actor or impact effect')
        if not scripted:
            require(after['enabled'] == 1 and any(a['variant'] == 9 and a['phase'] == 1
                    and a['y'] >= 0x130 for a in after['actors']), 'impact lacks active return actor')
        events.append(dict(tag=after['tag'], count=after['count'],
                           kind='scripted-marker' if scripted else 'reflected-impact'))
    require(sum(e['kind'] == 'reflected-impact' for e in events) == 5, 'five impacts missing')
    require(any(s['action'] == 9 or s['mode'] == 0x0c for s in result[arrival+1:]),
            'expected later failed traversal is absent; reassess scope')
    return dict(arrival=live[-1]['tag'], events=events, samples=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', default='mazo-reflect-long-native-v1')
    parser.add_argument('--source', default='mazo-reflect-long-source-v1')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'use a fresh report')
    captures = [ROOT / 'local/captures' / p for p in (args.native, args.source)]
    nr, sr = [read(p / 'receipt.json') for p in captures]
    build = read(ROOT / 'local/build' / TARGET / 'm1-build.json')
    cfg = read(ROOT / 'config/restorations' / (TARGET + '.json'))
    require(nr['target'] == TARGET and nr['stage'] == 'native', 'native role')
    require(nr['rom_sha256'] == build['rom_sha256'] == cfg['output']['sha256'], 'native ROM')
    require(nr['host_binary_sha256'] == build['binary_sha256'] == sha((
        ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']).read_bytes()), 'native binary')
    require(nr['native_content'] == build['native_content'] == identity(TARGET), 'native modules')
    require(nr['runtime_patches'] == build['runtime_patches'] == patch_plan(), 'runtime')
    require(nr['analysis'] == build['analysis'], 'native analysis')
    require(sr['rom_sha256'] == SOURCE == sha((ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()),
            'official source ROM')
    require(sr['reference_core_options'] == 'snes9x_echo_buffer_hack=enabled', 'source options')
    for field, path in [('core_sha256', 'local/upstream/snes9x/libretro/snes9x_libretro.so'),
                        ('frontend_sha256', 'local/build/snesref/snesref')]:
        require(sr[field] == sha((ROOT / path).read_bytes()), field)
    for donor, (directory, receipt) in enumerate(zip(captures, (nr, sr))):
        script = route(bool(donor))
        require((directory / 'input.script').read_text() == ('' if donor else 'turbo on\n') + script,
                'generated route differs from executed script')
        require(receipt['script_sha256' if donor else 'route_sha256'] == sha(script.encode()), 'script digest')
        log = (directory / 'run.log').read_text()
        require((' quit' if donor else 'exit: script quit after') in log and 'TIMEOUT' not in log
                and 'dump c12f32' in log, 'capture incomplete')
    results = {host: states(p) for host, p in zip(('native', 'source'), captures)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(scope=__doc__, rom_sha256=nr['rom_sha256'],
        binary_sha256=nr['host_binary_sha256'], source_rom_sha256=SOURCE,
        receipts={str(p.relative_to(ROOT)): sha((p/'receipt.json').read_bytes()) for p in captures},
        results=results, limitations=['Immunity, entry and repeated player-position fixtures.',
        'Later reaction timing and random attack choices differ; no whole-fight parity.',
        'Both long probes later die. No full clear, saved exit or audible music acceptance.']), indent=2)+'\n')
    print('PASS: five reflected impacts, scripted marker and second-boss arrival per host; 385 samples each')


if __name__ == '__main__':
    main()
