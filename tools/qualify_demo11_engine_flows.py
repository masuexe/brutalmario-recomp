#!/usr/bin/env python3
"""Check the original engine flows still behave on the Demo 1-1 base.

Six routes exercise behaviour that is not restored content: boss death and damage
phases, repeated death, the shop, the boss door and the Lemmy mask room. They were
accepted on the demoOnly1 line, so they must be re-checked after the rebase.
Two scripts begin with the native-only 'turbo on' command; their reference replays
use the same tracked script with that line removed, and the receipts pin that exact
derivation.
"""
import hashlib, json
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-room0cb-gfx'
BINARY = 'BrutalMarioDemo11Room0CbGraphicsSNESRecomp'


def strip_native_commands(text):
    return ''.join(line for line in text.splitlines(keepends=True)
                   if not line.startswith('turbo '))


def final_state(jsonl):
    final, frames = {}, 0
    for line in jsonl.read_text().splitlines():
        item = json.loads(line)
        frames = max(frames, item['f'])
        final[int(item['adr'], 16)] = int(item['val'], 16)
    return frames, final


def sample(directory, tag):
    return (directory / (tag + '.wram.bin')).read_bytes()


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    require(sha((ROOT / 'local/build' / HEAD / BINARY).read_bytes()) == build['binary_sha256'],
            'native build identity differs')

    report = {'scope': __doc__.strip(), 'head': HEAD, 'candidate_rom_sha256': sha(candidate),
              'binary_sha256': build['binary_sha256'], 'routes': {}}

    def receipt_for(capture, tracked_script, stripped=False):
        directory = ROOT / 'local/captures' / capture
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + capture)
        expected = (ROOT / 'recomp/inputs' / tracked_script).read_text()
        if stripped:
            expected = strip_native_commands(expected)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) ==
                hashlib.sha256(expected.encode()).hexdigest(), 'capture route differs: ' + capture)
        return directory, receipt

    # Reference-host routes that run unchanged.
    directory, _ = receipt_for('d11-eng-boss-death', 'demo-only-1-boss-death.script')
    body = sample(directory, 'after-death')
    require(body[0x100] == 0x0E and word(body, 0x10b) == 0x100, 'boss death did not return to the map')
    report['routes']['boss-death'] = {'host': 'reference', 'after_death_mode': body[0x100]}

    directory, _ = receipt_for('d11-eng-boss-probe', 'demo-only-1-boss-probe.script')
    modes = {tag: sample(directory, tag)[0x100]
             for tag in ('boss-01', 'boss-02', 'boss-03', 'boss-04', 'boss-06')}
    require(modes['boss-01'] == 0x14 and modes['boss-03'] == 0x0B,
            'boss damage phases no longer reach the death sequence')
    require(modes['boss-04'] == 0x0C and modes['boss-06'] == 0x0D,
            'boss death sequence differs')
    report['routes']['boss-probe'] = {'host': 'reference', 'modes': modes}

    directory, _ = receipt_for('d11-eng-repeat-death', 'demo-only-1-repeat-death.script')
    coins = [sample(directory, 'death-%d' % i)[0xDBE] for i in (1, 2, 3)]
    require(coins == [3, 2, 1], 'repeated death coin sequence changed: ' + str(coins))
    report['routes']['repeat-death'] = {'host': 'reference', 'coins': coins}

    directory, _ = receipt_for('d11-eng-shop', 'demo-only-1-shop.script')
    bank = sample(directory, 'menu-first')
    require(bank[0x100] == 0x14 and word(bank, 0x10b) == 0x105, 'shop menu did not open in the course')
    require(sample(directory, 'menu-exit')[0x100] == 0x14, 'shop exit left gameplay')
    report['routes']['shop'] = {'host': 'reference', 'menu_mode': bank[0x100],
                                'menu_room': word(bank, 0x10b)}

    # Routes whose tracked script starts with the native-only turbo command.
    directory, _ = receipt_for('d11-engr-boss-door', 'demo-only-1-boss-door.script', stripped=True)
    frames, final = final_state(directory / 'wram.jsonl')
    mode = final.get(0x100, 0)
    room = final.get(0x10b, 0) | (final.get(0x10c, 0) << 8)
    require(frames > 0 and mode == 0x14 and room == 0x100,
            'boss door route no longer reaches the boss room')
    report['routes']['boss-door'] = {'host': 'reference', 'frames': frames, 'final_mode': mode,
                                     'final_room': room, 'note': 'turbo line removed for reference'}

    directory, _ = receipt_for('d11-engr-lemmy-mask', 'demo-only-1-lemmy-mask.script', stripped=True)
    next_idle = sample(directory, 'next-idle')
    require(next_idle[0x100] == 0x14 and word(next_idle, 0x10b) == 0x08C,
            'Lemmy mask route no longer reaches its room')
    report['routes']['lemmy-mask'] = {'host': 'reference', 'room': word(next_idle, 0x10b),
                                      'note': 'turbo line removed for reference'}

    report['verified'] = ['every capture is pinned to the head ROM and to the documented route',
                          'boss death returns to the map and the damage phases reach the death sequence',
                          'repeated death still loses coins 3/2/1',
                          'the shop opens and exits without leaving gameplay',
                          'the boss door route reaches the boss room 0x100 with mode 0x14',
                          'the Lemmy mask route reaches room 0x08C with mode 0x14']
    report['limits'] = ['Reference host only: these routes were accepted on the demoOnly1 line',
                        'and this rerun verifies they still behave on the new base; the native',
                        'replays of the two turbo routes are too slow to include here.',
                        'Not a content qualification of the restored resources.']
    output = ROOT / 'local/reports/demo11-engine-flows.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Demo11 engine flow checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()