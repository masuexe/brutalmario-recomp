#!/usr/bin/env python3
"""Qualify room BC/CC HP uploads, real damage, and ordinary/fuel HUD controls.

Map, player, room-exit and vanilla Koopa spawn fixtures are explicit in inputs.
No HP, HUD, completion or SRAM values are injected. This is not a boss clear.
"""
import json
import re
from pathlib import Path

from audit_demo11_line import allowed_regions
from m1 import ROOT
from prepare_rom import verify
from qualify_demo11_lower_inner_music import capture
from qualify_world1_next_course import require, sha, word
from restoration_targets import RESTORATIONS
from restore_star_world_1 import lorom, make_candidate

ROOT = Path(ROOT)
TARGET = 'demo11-hp-bars'
BASE = 'demo11-boss-room-music-a9'
CORE_SHA = '39aff6a57c370035486e1b5ca3d33b99ac31ed5e809a883984bce9be51aecf7c'
SCRIPTS = {'bc': 'demo11-hp-boss-bc.script', 'cc': 'demo11-hp-mario-cc.script'}


def load(path):
    return json.loads(path.read_text())


def state(directory, tag):
    wram = (directory / (tag + '.wram.bin')).read_bytes()
    vram = (directory / (tag + '.vram.bin')).read_bytes()
    require(len(wram) == 0x20000 and len(vram) == 0x10000, 'incomplete dump: ' + str(directory))
    return wram, vram


def uploaded(directory, tag, room):
    wram, vram = state(directory, tag)
    require(wram[0x100] == 0x14 and word(wram, 0x10B) == room, 'wrong room/mode: ' + str(directory))
    require(wram[0x1FFDF] == 1, 'legacy HUD flag absent')
    require(vram[0xA050:0xA070:2] == wram[0x1FFE0:0x1FFF0], 'HP buffer is not displayed')
    return wram, vram


def donor_capture(room, donor_pin):
    name = 'hp-' + room + '-cheap-ref-r2'
    directory = ROOT / 'local/captures' / name
    receipt = load(directory / 'receipt.json')
    script = 'demo11-hp-boss-bc-donor.script' if room == 'bc' else SCRIPTS[room]
    require(receipt['rom_sha256'] == donor_pin['sha256'], 'donor capture ROM differs')
    require(receipt['script_sha256'] == sha((ROOT / 'recomp/inputs' / script).read_bytes()), 'donor route differs')
    require(receipt['core_sha256'] == CORE_SHA, 'donor core differs')
    require(receipt['frontend_sha256'] == sha((ROOT / 'local/build/snesref/snesref').read_bytes()),
            'donor frontend differs')
    log = (directory / 'run.log').read_text().lower()
    require(' quit' in log and 'timeout' not in log and 'assertion failed' not in log, 'donor did not finish')
    return directory, receipt


def main():
    cfg = load(ROOT / 'config/restorations' / (TARGET + '.json'))
    base_cfg = load(ROOT / 'config/restorations' / (BASE + '.json'))
    require(cfg['base_restoration'] == BASE and cfg['base_output'] == base_cfg['output'], 'parent differs')
    rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
    base = (ROOT / 'local/restoration' / BASE / 'rom.sfc').read_bytes()
    donor = (ROOT / 'local/content-versions/cheap-demo/rom.sfc').read_bytes()
    donor_pin = next(v['output'] for v in load(ROOT / 'config/content-versions.json')['versions']
                     if v['id'] == 'cheap-demo')
    verify(donor, donor_pin, 'official cheap-demo')
    verify(rom, cfg['output'], TARGET)
    verify(base, cfg['base_output'], BASE)
    require(make_candidate(base, donor, cfg)[0] == rom, 'recipe does not reproduce ROM')
    changed = {i for i, (a, b) in enumerate(zip(base, rom)) if a != b}
    require(changed <= allowed_regions(cfg) and len(changed) == 84, 'unexpected patch footprint')
    source = cfg['source_dma']
    require(source['version'] == 'cheap-demo', 'DMA source version differs')
    start = lorom(int(source['address'], 16))
    dma = donor[start:start + source['size']]
    verify(dma, source, 'official donor DMA sequence')
    require(dma.replace(bytes.fromhex('e230'), bytes.fromhex('e220')) in
            bytes.fromhex(cfg['raw_blocks'][0]['bytes']), 'DMA adaptation differs')
    for address, length in ((0x108294, 0x48), (0x3EA000, 77), (0x318522, 16), (0x2C8BA0, 0x106)):
        start = lorom(address)
        require(rom[start:start + length] == base[start:start + length], 'existing HUD/HP/boss code changed')
    require(sha((ROOT / 'local/upstream/snes9x/libretro/snes9x_libretro.so').read_bytes()) == CORE_SHA,
            'reference core binary differs')
    build = load(ROOT / 'local/build' / TARGET / 'm1-build.json')
    require(build['rom_sha256'] == cfg['output']['sha256'] and build['binary_sha256'] ==
            sha((ROOT / 'local/build' / TARGET / RESTORATIONS[TARGET]['binary']).read_bytes()), 'build differs')

    receipts = {}
    for room, number in (('bc', 0xBC), ('cc', 0xCC)):
        old, receipt = capture('hp-' + room + '-base-ref-r3', BASE, SCRIPTS[room])
        receipts[old.name] = receipt
        old_wram, old_vram = state(old, 'active')
        require(word(old_wram, 0x10B) == number and old_wram[0x1FFDF] == 1, 'negative control lacks HP data')
        require(old_vram[0xA050:0xA070:2] != old_wram[0x1FFE0:0x1FFF0], 'negative control no longer fails')
        if room == 'bc':
            require(any(old_wram[0x14C8+i] == 8 and old_wram[0x1AB9E+i] == 0x2B for i in range(12)),
                    'boss absent from negative control')
        original, receipt = donor_capture(room, donor_pin)
        receipts[original.name] = receipt
        donor_wram, donor_vram = uploaded(original, 'active', number)
        require(donor_wram[0x1FFE0:0x1FFE5] == old_wram[0x1FFE0:0x1FFE5], 'donor label differs')
        reference = None
        old_native, receipt = capture('hp-' + room + '-base-native-r3', BASE, SCRIPTS[room], True)
        receipts[old_native.name] = receipt
        for host in (('ref', 'native', 'interpreter', 'optimized') if room == 'bc' else ('ref', 'native', 'interpreter')):
            directory, receipt = capture('hp-' + room + '-fixed-' + host + '-r2', TARGET,
                                         SCRIPTS[room], host != 'ref')
            receipts[directory.name] = receipt
            if host == 'interpreter':
                require(receipt['interpreter_only_requested'], 'interpreter capture not requested')
                log = (directory / 'run.log').read_text()
                require(re.search(r'aot_bridge_entries=0\b', log), 'interpreter capture used AOT')
            wram, vram = uploaded(directory, 'active', number)
            require(wram[0x1FFE0:0x1FFF0] == old_wram[0x1FFE0:0x1FFF0], 'fix changed HP data')
            if reference is None:
                reference = directory
            tags = ('active', 'later') if room == 'bc' else ('active', 'later', 'contact', 'settled')
            for tag in tags:
                w, v = uploaded(directory, tag, number)
                rw, rv = state(reference, tag)
                require(w[0x1FFDF:0x1FFF0] == rw[0x1FFDF:0x1FFF0] and
                        v[0xA050:0xA070] == rv[0xA050:0xA070], 'native/reference HP display differs')
                # Compare the actual 2bpp glyphs and their palette with the original donor.
                for tile in set(w[0x1FFE0:0x1FFF0]):
                    offset = 0x8000 + tile * 16
                    require(v[offset:offset+16] == donor_vram[offset:offset+16], 'HP glyph differs')
                require(w[0x731:0x739] == donor_wram[0x731:0x739], 'HP palette differs')
            for tag in ('title', 'files', 'intro'):
                require((directory / (tag + '.fb.bgrx')).read_bytes() ==
                        ((old if host == 'ref' else old_native) / (tag + '.fb.bgrx')).read_bytes(), 'startup picture changed')
            if room == 'cc':
                before, _ = state(directory, 'later')
                hit, _ = state(directory, 'contact')
                after, _ = state(directory, 'settled')
                require(before[0x19] == 2 and hit[0x19] == 0 and after[0x19] == 2, 'guest damage path absent')
                require(before[0x1420] == 1 and after[0x1420] == 2 and
                        before[0x1FFE0:0x1FFF0] != after[0x1FFE0:0x1FFF0], 'HP did not deplete')
                for tag in ('corridor', 'returned'):
                    w, v = state(directory, tag)
                    _, control = state(old, tag)
                    require(word(w, 0x10B) == 0x15F and w[0x1FFDF] == 0, 'ordinary-room control missing')
                    require(v[0xA000:0xA800] == control[0xA000:0xA800], 'ordinary HUD changed or retained HP cells')

    for host in ('ref', 'native'):
        fixed, receipt = capture('hp-fuel-fixed-' + host + '-r1', TARGET, 'demo11-sky-fuel.script', host == 'native')
        receipts[fixed.name] = receipt
        old, receipt = capture('hp-fuel-base-ref-r1', BASE, 'demo11-sky-fuel.script')
        receipts[old.name] = receipt
        first, _ = state(fixed, 'active')
        used, vram = uploaded(fixed, 'fuel_used', 9)
        require(used[0x1FFE0:0x1FFE4] == bytes.fromhex('0f1e0e15'), 'FUEL label missing')
        require(first[0x1FFE4:0x1FFF0] != used[0x1FFE4:0x1FFF0], 'fuel did not deplete')
        for tag in ('active', 'fuel_used'):
            w, v = state(fixed, tag)
            ow, ov = state(old, tag)
            require(w[0x1FFE0:0x1FFF0] == ow[0x1FFE0:0x1FFF0] and
                    v[0xA050:0xA070] == ov[0xA050:0xA070], 'accepted fuel display changed')
    report = dict(target=TARGET, rom_sha256=cfg['output']['sha256'], binary_sha256=build['binary_sha256'],
                  reference_core_sha256=CORE_SHA, changed_bytes=len(changed), captures=receipts,
                  scope='HP uploads and fixture damage only; no unassisted traversal or boss clear')
    (ROOT / 'local/reports/demo11-hp-bars-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print('HP bar checks passed: BC boss, CC Mario/damage, both hosts, interpreter, ordinary HUD and fuel')


if __name__ == '__main__':
    main()
