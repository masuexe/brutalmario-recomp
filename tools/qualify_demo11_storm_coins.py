#!/usr/bin/env python3
"""Qualify assisted real Dragon Coin pickups and the HDMA VRAM fix in room 122."""
import hashlib
import json
from m1 import ROOT
from runtime_patches import patch_plan

ROM_SHA = '48891cf75b570e4118f8646f7f216d50505d047edc40341b3d0dccdc8cc3022c'
OLD_BINARY_SHA = 'd8879d7e5d41692d40f1a08b501fad7156469916142d78a62a8817924113a6cb'
SCRIPT = ROOT / 'recomp/inputs/demo11-storm-dragon-coins.script'
CAPTURES = ROOT / 'local/captures'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sample(directory, tag, kind, size):
    data = (directory / (tag + '.' + kind + '.bin')).read_bytes()
    require(len(data) == size, f'{directory.name}/{tag}: wrong {kind} size')
    return data


def capture(name, expected_binary=None):
    directory = CAPTURES / name
    receipt = json.loads((directory / 'receipt.json').read_text())
    require(receipt['rom_sha256'] == ROM_SHA, name + ': wrong ROM')
    require(receipt['route_sha256'] == sha(SCRIPT.read_bytes()), name + ': wrong script')
    if expected_binary:
        require(receipt['host_binary_sha256'] == expected_binary, name + ': wrong binary')
    log = (directory / 'run.log').read_text()
    require('script f=2898 quit' in log, name + ': route did not complete')
    return directory, receipt


def main():
    build = json.loads((ROOT / 'local/build/demo11-fix-batch-p/m1-build.json').read_text())
    binary = ROOT / 'local/build/demo11-fix-batch-p/BrutalMarioDemo11FixBatchPSNESRecomp'
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'build binary differs')
    require(build['runtime_patches'] == patch_plan(), 'rebuild with current runtime')
    require(build['rom_sha256'] == ROM_SHA, 'build ROM differs')
    reference, ref_receipt = capture('storm-coins-ref-r2')
    before, old_receipt = capture('storm-coins-before-r2', OLD_BINARY_SHA)
    report = {'scope': __doc__.strip(), 'rom_sha256': ROM_SHA,
              'script_sha256': sha(SCRIPT.read_bytes()), 'reference': ref_receipt,
              'before': old_receipt, 'fixed': {}}
    for host in ('native', 'optimized', 'interpreter'):
        directory, receipt = capture('storm-coins-fixed-' + host, build['binary_sha256'])
        require(receipt['runtime_patches'] == patch_plan(), host + ': wrong runtime')
        require(receipt['interpreter_only_requested'] == (host == 'interpreter'),
                host + ': incorrect interpreter policy')
        require(receipt['renderer_override'] == ('optimized' if host == 'optimized' else None),
                host + ': incorrect renderer')
        if host == 'interpreter':
            require('[m1] aot_bridge_entries=0 ' in (directory / 'run.log').read_text(),
                    'interpreter still ran AOT bodies')
        old_differences = []
        for i in range(1, 6):
            for tag in (f'coin{i}', f'held{i}'):
                left = sample(reference, tag, 'wram', 0x20000)
                right = sample(directory, tag, 'wram', 0x20000)
                for wram in (left, right):
                    require(wram[0x100] == 0x14 and wram[0x10b:0x10d] == b'\x22\x01',
                            host + '/' + tag + ': left room 122 gameplay')
                    require(wram[0x1420] == i and wram[0x1422] == i,
                            host + '/' + tag + ': missing real pickup')
                    if i < 5 or tag == 'held5':
                        require(wram[0xdbe] == (5 if i == 5 else 4),
                                host + '/' + tag + ': unexpected life counter')
                for start in (0xc800, 0x1c800):
                    require(left[start:start+0x3600] == right[start:start+0x3600],
                            host + '/' + tag + ': Map16 differs')
                a = sample(reference, tag, 'vram', 0x10000)[0x4000:0x8000]
                b = sample(directory, tag, 'vram', 0x10000)[0x4000:0x8000]
                require(a == b, host + '/' + tag + ': tilemap corruption')
            old = sample(before, f'held{i}', 'vram', 0x10000)[0x4000:0x8000]
            old_differences.append(sum(x != y for x, y in zip(a, old)))
        require(all(old_differences), 'negative control no longer reproduces corruption')
        for tag in ('title', 'files', 'intro'):
            require((directory / (tag + '.fb.bgrx')).read_bytes() ==
                    (before / (tag + '.fb.bgrx')).read_bytes(),
                    host + '/' + tag + ': unrelated startup picture changed')
        report['fixed'][host] = {'receipt': receipt, 'tilemap_differences': 0,
                                 'before_tilemap_differences': old_differences}
    animal = CAPTURES / 'storm-regression-animal-fire'
    receipt = json.loads((animal / 'receipt.json').read_text())
    require(receipt['rom_sha256'] == ROM_SHA and
            receipt['host_binary_sha256'] == build['binary_sha256'] and
            receipt['runtime_patches'] == patch_plan(), 'animal regression identity differs')
    require(receipt['route_sha256'] ==
            sha((ROOT / 'recomp/inputs/star-world-1-animal-fire.script').read_bytes()),
            'animal regression route differs')
    wram = sample(animal, 'sign', 'wram', 0x20000)
    vram = sample(animal, 'sign', 'vram', 0x10000)
    require(wram[0x100] == 0x14 and wram[0x10b:0x10d] == b'\x05\x00' and
            wram[0x14af] == 1, 'animal sign trigger did not execute')
    for word, source, size in ((0xe00, 0xb100, 0x80), (0xf00, 0xb300, 0x80),
                               (0xc00, 0xb180, 0x80), (0xd00, 0xb380, 0x80),
                               (0xa00, 0xb500, 0x100), (0xb00, 0xb700, 0x100)):
        require(vram[word*2:word*2+size] == wram[source:source+size],
                'legacy DMA upload differs at VRAM word ' + hex(word))
    require('script f=4439 quit' in (animal / 'run.log').read_text(),
            'animal regression did not finish')
    report['legacy_upload_regression'] = receipt
    output = ROOT / 'local/reports/demo11-storm-coins.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Storm Dragon Coins: five pickups, extra life, Map16/tilemap parity, '
          'both renderers, interpreter and old-build negative control passed')


if __name__ == '__main__':
    main()
