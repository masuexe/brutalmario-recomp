#!/usr/bin/env python3
"""Qualify the room106 music fix on the Demo 1-1 line.

The level-default BGM dispatch checks the persistent map-node X coordinate
($1F17) and requests native slot 0x33 only for the room106 node (0x58).
The user auditioned d11-song33 as the correct room106 music and confirmed
the neighbouring room120 course (node 0x88) must keep its original 0x49
request. Thirteen equal-width bytes only. Both hosts must select 0x33 on
the room106 node and 0x49 on the room120 node.
"""
import json
import math
import struct
import wave

from m1 import ROOT as REPO_ROOT
from prepare_rom import verify
from qualify_world1_next_course import require, sha, word

ROOT = Path = REPO_ROOT
HEAD = 'demo11-room106-music'
BINARY = 'BrutalMarioDemo11Room106MusicSNESRecomp'
BOTH_SCRIPT = ROOT / 'recomp/inputs/demo11-room106-music-both.script'
SOLO_SCRIPT = ROOT / 'recomp/inputs/demo11-room106-music-verify.script'
AUDITION = ROOT / 'local/probes/world1-survey/106-music-diagnostic/audition/d11-song33.wav'


def feats(path, at_s=55.0, dur=6.0):
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
    base = (ROOT / 'local/restoration/demo11-world1-route/rom.sfc').read_bytes()
    require(sha(base) == cfg['base_output']['sha256'], 'base identity differs')
    diffs = [i for i in range(len(base)) if base[i] != candidate[i]]
    require(diffs == list(range(0x172B, 0x1738)), 'candidate differs from the reviewed dispatch patch')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    states = {}
    for host in ('reference', 'native'):
        directory = ROOT / 'local/captures' / ('d11-music-both-' + ('ref' if host == 'reference' else 'native'))
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(BOTH_SCRIPT.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        for tag in ('room106_settled', 'room120_settled'):
            body = (directory / (tag + '.wram.bin')).read_bytes()
            require(len(body) == 0x20000, 'incomplete WRAM: ' + host + '/' + tag)
            states[host, tag] = body
        require(states[host, 'room106_settled'][0x100] == 0x14 and
                states[host, 'room106_settled'][0x0DDA] == 0x33 and
                (states[host, 'room106_settled'][0x10B] | states[host, 'room106_settled'][0x10C] << 8) == 0x0106,
                'room106 node does not request slot 33: ' + host)
        require(states[host, 'room120_settled'][0x100] == 0x14 and
                states[host, 'room120_settled'][0x0DDA] == 0x49 and
                (states[host, 'room120_settled'][0x10B] | states[host, 'room120_settled'][0x10C] << 8) == 0x0120,
                'room120 node lost its original 0x49 request: ' + host)

    solo_receipt = json.loads((ROOT / 'local/captures/d11-106only-ref/receipt.json').read_text())
    require(solo_receipt['rom_sha256'] == sha(candidate), 'solo capture ROM differs')
    require(solo_receipt.get('route_sha256', solo_receipt.get('script_sha256')) == sha(SOLO_SCRIPT.read_bytes()),
            'solo capture route differs')
    ref_audio = feats(ROOT / 'local/captures/d11-106only-ref/audio.wav', at_s=45.0)
    audition = feats(AUDITION, at_s=45.0)
    require(abs(ref_audio[0] - audition[0]) / audition[0] < 0.05 and
            abs(ref_audio[1] - audition[1]) / audition[1] < 0.10,
            'reference audio differs from the auditioned track: %s vs %s' % (ref_audio, audition))
    apu = (ROOT / 'local/captures/d11-music-both-native/apu-ram.bin').read_bytes()
    chans = [struct.unpack_from('<H', apu, a)[0] for a in (0x30, 0x32, 0x34, 0x36, 0x3A, 0x3C)]
    require(all(c == 0 or 0x5400 <= c < 0x5800 for c in chans), 'native is not playing an uploaded track')

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': {'0x172B-0x1737': 'node-bound dispatch (LDY $1F17/CPY #$58/BNE/LDA #$33)'},
        'captures': {'reference': 'local/captures/d11-music-both-ref',
                     'reference_audio': 'local/captures/d11-106only-ref',
                     'native': 'local/captures/d11-music-both-native'},
        'verified': ['both hosts request native slot 0x33 on the room106 node (0x58,0x1D8; internal room $0106)',
                     'both hosts keep the original 0x49 request on the room120 node (0x88,0x1F8; internal room $0120)',
                     'reference audio reproduces the user-auditioned d11-song33 track',
                     'native ARAM shows an uploaded track playing',
                     'exactly the reviewed thirteen bytes differ from the accepted route head'],
        'limits': ['The final acceptance is the user listening to the native build; '
                   'the audition decision (song 33) is user-provided.',
                   'Other courses keep their existing music; only the room106 default request changes.'],
    }
    output = ROOT / 'local/reports/demo11-room106-music-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room106 music checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
