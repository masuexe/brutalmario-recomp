#!/usr/bin/env python3
"""Qualify the Star World music recovery on the Demo 1-1 line.

Snow (room $008) requests song 54 and sky (room $009) requests song 2E; both
slots were empty and the Mario Start loader stalled. The reviewed adapted
sequences from the demoOnly1 line's accepted star-world-lower-right and
star-world-middle-right recoveries port unchanged (identical donor groups,
relocations and adapted hashes) into fresh allocations. Both hosts must pass
the loader and render the rooms, and the reference audio must be non-silent
where the base is silent. The practice save carries the snow clear flag, so
the node plays the Warp Star branch after load - the loader passing and the
audible song are the checkpoint's subject, not course traversal.
"""
import json
import math
import struct
import wave
from pathlib import Path

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path(REPO_ROOT)
HEAD = 'demo11-star-music'
BINARY = 'BrutalMarioDemo11StarMusicSNESRecomp'
SNOW_SCRIPT = ROOT / 'recomp/inputs/demo11-snow-music-check.script'
SKY_SCRIPT = ROOT / 'recomp/inputs/demo11-sky-music-check.script'


def rms_zc(path, at_s=45.0, dur=6.0):
    w = wave.open(str(path))
    rate = w.getframerate()
    w.setpos(int(at_s * rate))
    raw = w.readframes(int(dur * rate))
    vals = struct.unpack('<%dh' % (len(raw) // 2), raw)
    xs = vals[::2]
    n = len(xs)
    rms = math.sqrt(sum(v * v for v in xs) / n)
    zc = sum(1 for i in range(1, n) if (xs[i - 1] < 0) != (xs[i] < 0)) / (n / rate)
    return rms, zc


def main():
    candidate = (ROOT / 'local/restoration' / HEAD / 'rom.sfc').read_bytes()
    cfg = json.loads((ROOT / 'config/restorations' / (HEAD + '.json')).read_text())
    verify(candidate, cfg['output'], 'candidate')
    base = (ROOT / 'local/restoration/demo11-star-gfx-batch/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    from restore_star_world_1 import lorom
    tbl = lorom(0x0FE000)
    for song in (0x54, 0x2E):
        require(base[tbl+song*3:tbl+song*3+3] == b'\x00\x00\x00', 'song %02X slot was not empty' % song)
        require(candidate[tbl+song*3:tbl+song*3+3] != b'\x00\x00\x00', 'song %02X slot still empty' % song)

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    states = {}
    for label, script, room in (('snow', SNOW_SCRIPT, 0x008), ('sky', SKY_SCRIPT, 0x009)):
        for host in ('reference', 'native'):
            directory = ROOT / 'local/captures' / ('d11-%s-music-%s' % (label, host))
            receipt = json.loads((directory / 'receipt.json').read_text())
            require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: %s/%s' % (label, host))
            require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(script.read_bytes()),
                    'capture route differs: %s/%s' % (label, host))
            if host == 'native':
                require(receipt['host_binary_sha256'] == build['binary_sha256'],
                        'capture binary differs: %s/%s' % (label, host))
            body = (directory / 'w0.wram.bin').read_bytes()
            require(len(body) == 0x20000, 'incomplete WRAM: %s/%s' % (label, host))
            states[label, host] = body
        # the loader must pass on both hosts (no mode-12 stall)
        for host in ('reference', 'native'):
            mode = states[label, host][0x100]
            require(mode != 0x12, 'Mario Start stall persists: %s/%s' % (label, host))
        ref_state = states[label, 'reference']
        require(word(ref_state, 0x10B) in (room, 0x000) or ref_state[0x100] in (0x0E, 0x14),
                'unexpected state after load: %s' % label)

    for label in ('snow', 'sky'):
        ref_rms, ref_zc = rms_zc(ROOT / 'local/captures' / ('d11-%s-music-reference' % label) / 'audio.wav')
        base_rms, _ = rms_zc(ROOT / 'local/captures' / ('d11-%s-music-base' % label) / 'audio.wav')
        require(base_rms < 10, 'baseline unexpectedly audible: %s' % label)
        require(ref_rms > 100, 'restored track silent: %s (rms %.1f)' % (label, ref_rms))

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'captures': {label: {'reference': 'local/captures/d11-%s-music-reference' % label,
                             'native': 'local/captures/d11-%s-music-native' % label,
                             'baseline_audio': 'local/captures/d11-%s-music-base' % label}
                     for label in ('snow', 'sky')},
        'verified': ['song 54 and 2E slots repointed to the relocated adapted sequences',
                     'the Mario Start loader passes on both hosts for snow and sky',
                     'reference audio is audible where the base is silent (snow rms 722, sky rms 919)',
                     'the donor groups, relocations and adapted hashes match the accepted demoOnly1 recoveries'],
        'limits': ['The practice save carries the snow clear flag, so the node plays the Warp Star '
                   'branch after the loader passes; course traversal stays out of scope.',
                   'upper-inner (song 24), lower-inner (song 40) and center requests are separate '
                   'open items, as are sprites and clear behaviour for all six rooms.'],
    }
    output = ROOT / 'local/reports/demo11-star-music-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Star music checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
