#!/usr/bin/env python3
"""Qualify the mazo 1E5 resource and captured room 190 Mode 7 pixels."""
import argparse
import json
from pathlib import Path

from restore_star_world_1 import check_allocation, graphics_pointer, lorom, lz2, sha

ROOT = Path(__file__).resolve().parents[1]
DONOR_SHA = '94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1'
STREAM_SHA = '9beea9998d0fe150fc78018d305433b8a05e32181ad8f80ea1a4cdfb6728f7f3'


def qualify(candidate, interpreter, donor):
    base = (ROOT / 'local/restoration/demo11-native-product-r2/rom.sfc').read_bytes()
    rom = (ROOT / 'local/restoration/demo11-native-product-r3/rom.sfc').read_bytes()
    source = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
    for name, data in [('r2', base), ('r3', rom)]:
        cfg = json.loads((ROOT / f'config/restorations/demo11-native-product-{name}.json').read_text())
        assert sha(data) == cfg['output']['sha256'], name + ' ROM identity'
    assert sha(source) == DONOR_SHA
    assert graphics_pointer(base, 0x1e5) == 0xffffff
    assert graphics_pointer(source, 0x1e5) == 0x31eaec
    decoded, stream = lz2(source, 0x31eaec)
    assert len(stream) == 1545 and sha(stream) == STREAM_SHA
    assert len(decoded) == 4096
    check_allocation(base, 0x108008, len(stream))
    assert graphics_pointer(rom, 0x1e5) == 0x218008
    assert lz2(rom, 0x218008) == (decoded, stream)
    expected = bytearray(base)
    expected[0x108008:0x108008 + len(stream)] = stream
    pointer = lorom(0x148008) + (0x1e5 - 0x100) * 3
    expected[pointer:pointer+3] = bytes.fromhex('088021')
    assert rom == expected, 'changes outside the two reviewed windows'

    captures = {}
    identities = {}
    for name, prefix in [('native', candidate), ('interpreter', interpreter), ('donor', donor)]:
        ram = Path(str(prefix) + '.wram.bin').read_bytes()
        vram = Path(str(prefix) + '.vram.bin').read_bytes()
        assert len(ram) == 0x20000 and len(vram) == 0x10000
        assert ram[0x100] == 0x14 and ram[0x10b:0x10d] == b'\x90\x01', name + ' room/mode'
        receipt_file = prefix.parent / 'receipt.json'
        receipt = json.loads(receipt_file.read_text())
        assert receipt['rom_sha256'] == (DONOR_SHA if name == 'donor' else sha(rom))
        identities[name] = dict(receipt_sha256=sha(receipt_file.read_bytes()),
                                receipt=receipt,
                                vram_sha256=sha(vram),
                                frame=json.loads(Path(str(prefix) + '.info.json').read_text())['frame'])
        captures[name] = vram
    native, interp, reference = (captures[k] for k in ('native', 'interpreter', 'donor'))
    assert native[:0x8000:2] == reference[:0x8000:2], 'Mode 7 map'
    assert native[1:0x8000:2] == reference[1:0x8000:2], 'Mode 7 pixels'
    assert native == interp, 'interpreter VRAM'
    assert Path(str(candidate) + '.fb.bgrx').read_bytes() == Path(str(interpreter) + '.fb.bgrx').read_bytes()
    return dict(rom_sha256=sha(rom), stream_sha256=sha(stream),
                mode7_map_equal_bytes=16384, mode7_pixels_equal_bytes=16384,
                native_interpreter_vram_equal_bytes=65536,
                identities=identities,
                captures={k: str(v) for k, v in [('native', candidate), ('interpreter', interpreter), ('donor', donor)]},
                scope='Practice transfer; donor health-lock fixture. Graphics qualification, not an unassisted fight clear.')


def qualify_regression(base, candidate):
    """Compare five assisted room 191 samples on the same input script."""
    receipts = {str(path): json.loads((path / 'receipt.json').read_text())
                for path in (base, candidate)}
    assert receipts[str(base)]['route_sha256'] == receipts[str(candidate)]['route_sha256']
    count = 0
    for tag in ('w1', 'w2', 'w3', 'w4', 'w5'):
        ram = (base / (tag + '.wram.bin')).read_bytes()
        assert ram[0x100] == 0x14 and ram[0x10b:0x10d] == b'\x91\x01'
        for suffix in ('wram.bin', 'vram.bin', 'cgram.bin', 'oam.bin', 'fb.bgrx'):
            name = tag + '.' + suffix
            assert (base / name).read_bytes() == (candidate / name).read_bytes(), name
            count += 1
    return dict(equal_files=count, receipts=receipts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True, help='dump prefix, without suffix')
    parser.add_argument('--interpreter', type=Path, required=True)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--regression-base', type=Path, required=True)
    parser.add_argument('--regression-candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.native, args.interpreter, args.donor)
    result['room191_regression'] = qualify_regression(args.regression_base, args.regression_candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
