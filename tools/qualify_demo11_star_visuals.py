#!/usr/bin/env python3
"""Verify the scoped secret-room artwork, sky fuel HUD/flame and Santa recovery.

Map/player shortcuts, pipe-action and damage-immunity fixtures are explicit.
Slot matches use real timed jumps; Santa and reindeer are guest-generated.
The flame check samples sixteen consecutive frames, including both animations.
This is bounded qualification of the reported defects, not all-course acceptance.
"""
import json
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture, read_json, song
from qualify_demo11_star_sprites_safe import state
from qualify_world1_next_course import require, sha, word
from restore_star_world_1 import lorom, lz2, make_candidate, pointer_offset

ROOT = Path(ROOT)
HEAD = 'demo11-star-visuals-flame'
BASE = 'demo11-lower-inner-music'
INTERMEDIATE = 'demo11-star-visuals'


def image(target):
    cfg = read_json(ROOT / 'config/restorations' / (target + '.json'))
    rom = (ROOT / 'local/restoration' / target / 'rom.sfc').read_bytes()
    verify(rom, cfg['output'], target)
    return rom, cfg


def flames(body):
    tiles = []
    for i in range(64):
        x, y, tile, prop = body[0x300+i*4:0x304+i*4]
        if tile in (0x8C, 0x8E, 0xAC, 0xAE) and prop & 15 == 13 and y < 0xE0:
            tiles.append(dict(index=i, tile=tile, size=body[0x460+i] & 2, x=x, y=y))
    return tiles


def main():
    base, _ = image(BASE)
    intermediate, resources = image(INTERMEDIATE)
    final, finish = image(HEAD)
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    versions = read_json(ROOT / 'config/content-versions.json')['versions']
    verify(donor, next(v['output'] for v in versions if v['id'] == 'cheap-demo'), 'donor')
    for parent, child, cfg in ((base, intermediate, resources), (intermediate, final, finish)):
        verify(parent, cfg['base_output'], 'parent')
        replay, _ = make_candidate(parent, donor, cfg)
        require(replay == child, 'recipe does not reproduce child')
        require({i for i, (a, b) in enumerate(zip(parent, child)) if a != b} <= allowed_regions(cfg),
                'unexpected change outside reviewed regions')
    require(sum(a != b for a, b in zip(intermediate, final)) == 4, 'flame patch is not four bytes')
    require(final[lorom(0x38B5E0):][:4] == bytes.fromhex('eaeaeaea'), 'flame OAM gap remains')
    require(final[lorom(0x008DE1):][:4] == bytes.fromhex('2208a03e'), 'scoped fuel hook absent')
    require(final[lorom(0x108294):][:0x48] == base[lorom(0x108294):][:0x48],
            'original recipient status-bar routine changed')

    image('star-world-forest')
    palette_source = int.from_bytes(base[lorom(0x0EF600 + 0x54*3):][:3], 'little')
    require(final[lorom(palette_source):][:514] == base[lorom(palette_source):][:514],
            'palette data changed instead of artwork')
    palette_pointer = pointer_offset(0xFF8)
    gfx, _ = lz2(final, int.from_bytes(final[palette_pointer:palette_pointer+3], 'little'))
    verify(gfx, resources['assets'][0]['decoded'], 'secret-room artwork')
    require(word(final, lorom(0x14B788) + 4) == 0xFF8, 'private graphics selection missing')
    donor_capture, _ = capture('d11-visual-only1-secret-ref', 'star-world-forest',
                               'demo11-star1-secret-palette.script')
    old_state = state(donor_capture, 'bottom')
    old_vram = (donor_capture / 'bottom.vram.bin').read_bytes()

    captures, results = {}, {}
    for host, suffix in (('reference', 'ref'), ('native', 'native')):
        native = host == 'native'
        secret_name = 'd11-visual-secret-native' if native else 'd11-visual-secret-final-ref'
        directory, receipt = capture(secret_name, HEAD, 'demo11-star1-secret-palette.script', native)
        body = state(directory, 'bottom')
        require(body[0x100] == 0x14 and word(body, 0x10B) == 0x54, 'secret pipe destination missing')
        require(body[0x701:0x903] == old_state[0x701:0x903], 'secret-room palette differs')
        vram = (directory / 'bottom.vram.bin').read_bytes()
        require(vram[0x2000:0x3000] == old_vram[0x2000:0x3000] == gfx,
                'displayed secret-room artwork differs from qualified predecessor')
        captures[secret_name] = receipt

        directory, receipt = capture('d11-visual-fuel-' + suffix, HEAD, 'demo11-sky-fuel.script', native)
        initial, used = state(directory, 'active'), state(directory, 'fuel_used')
        require(used[0x100] == 0x14 and word(used, 0x10B) == 9, 'fuel route lost sky course')
        slot = next((j for j in range(12) if used[0x14C8+j] == 8 and used[0x1AB9E+j] == 0x28), None)
        require(slot is not None, 'rocket missing')
        require(used[0x1594+slot] < initial[0x1594+slot], 'actual riding did not consume fuel')
        vram = (directory / 'fuel_used.vram.bin').read_bytes()
        require(used[0x1FFE0:0x1FFE4] == bytes.fromhex('0f1e0e15'), 'FUEL label missing')
        require(vram[0xA050:0xA070:2] == used[0x1FFE0:0x1FFF0], 'fuel cells not uploaded to visible tilemap')
        require(initial[0x1FFE4:0x1FFF0] != used[0x1FFE4:0x1FFF0], 'gauge did not track depletion')
        results[host] = dict(fuel_before=initial[0x1594+slot], fuel_after=used[0x1594+slot])
        captures[directory.name] = receipt

        directory, receipt = capture('d11-visual-flame-' + suffix, HEAD, 'demo11-sky-flame.script', native)
        animations = set()
        for i in range(16):
            body = state(directory, 'flame%02d' % i)
            tiles = flames(body)
            require(len(tiles) == 2 and all(t['size'] == 2 for t in tiles),
                    'tail flame still has an 8x8/missing tile')
            require(tiles[1]['index'] == tiles[0]['index'] + 1, 'flame OAM gap remains')
            require(tiles[1]['y'] == tiles[0]['y'] + 16 and tiles[0]['x'] == tiles[1]['x'],
                    'flame geometry changed')
            animations.add(tuple(t['tile'] for t in tiles))
        require(animations == {(0x8C, 0xAC), (0x8E, 0xAE)}, 'both animation frames not exercised')
        results[host]['flame_animations'] = sorted(animations)
        captures[directory.name] = receipt

        directory, receipt = capture('d11-visual-sky-goal-' + suffix, HEAD,
                                     'star-world-middle-right-goal.script', native)
        require(word(state(directory, 'door'), 0x10B) == 0x9B, 'sky top door missing')
        cleared, reloaded = state(directory, 'overworld'), state(directory, 'file_reload')
        require(cleared[0x100] == reloaded[0x100] == 0x0E and cleared[0x13CE] == 1 and
                cleared[0x1EAB] == reloaded[0x1EAB] == 0x8C, 'sky clear/reload failed')
        for tag in ('overworld', 'file_reload'):
            saved = (directory / (tag + '.sram.bin')).read_bytes()
            require(saved[9] == saved[0x1B6] == 0x8C, 'sky SRAM copies differ')
        captures[directory.name] = receipt

        directory, receipt = capture('d11-visual-santa-arrival-' + suffix, HEAD,
                                     'demo11-snow-santa-arrival.script', native)
        witnesses = []
        for i in range(24):
            body = state(directory, 'santa%02d' % i)
            types = {body[0x1504+j] for j in range(12)
                     if body[0x14C8+j] == 8 and body[0x1AB9E+j] == 9 and
                     body[0x1AB10+j] & 4 and word(body, 0x10B) == 0x26}
            if {0, 2} <= types:
                witnesses.append(i)
        require(witnesses, 'real slot match did not generate Santa and reindeer')
        results[host]['santa_arrival_samples'] = witnesses
        captures[directory.name] = receipt
        directory, receipt = capture('d11-visual-santa-secret-' + suffix, HEAD,
                                     'star-world-lower-right-secret.script', native)
        body = state(directory, 'secret_map')
        require(body[0x100] == 0x0E and body[0x1EAA] == 0x8B and body[0x13CE] == 1,
                'Santa reward/keyhole clear failed')
        captures[directory.name] = receipt

        directory, receipt = capture('d11-visual-cap-regression-' + suffix, HEAD,
                                     'demo11-star-lower-inner-music.script', native)
        for name in ('invisible', 'metal', 'wing'):
            active = state(directory, name + '_active')
            expired, resumed = state(directory, name + '_expired'), state(directory, name + '_resumed')
            require(any(active[0x1FFD0:0x1FFD3]), 'cap regression did not activate effect')
            require(expired[0x1FFD0:0x1FFD3] == resumed[0x1FFD0:0x1FFD3] == bytes(3),
                    'cap expiry regression failed')
            require(resumed[0x100] == 0x14 and word(resumed, 0x10B) == 0x117 and
                    resumed[0x0DDA] == 0x60 and resumed[0x1DFB] == 0 and
                    expired[0x14] != resumed[0x14], 'cap expiry froze after the NMI change')
        if native:
            aram = (directory / 'apu-ram.bin').read_bytes()
            song60 = song(final, 0x60)[1]
            require(aram[0x5400:0x5400+len(song60)] == song60, 'cap expiry loaded wrong music')
        captures[directory.name] = receipt

    baseline, receipt = capture('d11-visual-base-flame-ref', BASE, 'demo11-sky-flame.script')
    tiles = flames(state(baseline, 'flame00'))
    require(len(tiles) == 2 and [t['size'] for t in tiles] == [2, 0],
            'baseline no longer reproduces the cropped flame')
    captures[baseline.name] = receipt
    report = dict(scope=__doc__.strip(), target=HEAD, rom_sha256=sha(final),
                  base_sha256=sha(base), intermediate_sha256=sha(intermediate),
                  changed_bytes_from_base=sum(a != b for a, b in zip(base, final)),
                  captures=captures, results=results,
                  limits=['Secret-room comparison covers graphics and palette through an assisted pipe-action route.',
                          'Fuel/flame samples and the actual-input sky normal-clear route are checked; the sky secret exit remains open.',
                          'Santa probes use position/immunity fixtures and real timed slot matches; no reward, actor or completion state is fabricated.',
                          'The fuel hook is scoped to active room009; recipient behavior outside it is retained and cap expiry is rerun.',
                          'Center entry and broader restoration scope remain open.'])
    output = ROOT / 'local/reports/demo11-star-visuals.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star visual recovery checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
