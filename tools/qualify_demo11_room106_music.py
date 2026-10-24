#!/usr/bin/env python3
"""Qualify the room106 music fix on the Demo 1-1 line.

The level-default music request (0x49) is bound to an override that requests
native slot 0x33 - the track the user identified as correct through the
audition library (d11-song33). Three equal-width bytes only; no data, table
or engine transplant. Both hosts must select 0x33 in room106 and reproduce
the audition track's audio features.
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
SCRIPT = ROOT / 'local/probes/world1-survey/106-aram-entry.script'
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
    require(diffs == [0x172C, 0x172D, 0x172E, 0x1737], 'candidate differs from the reviewed three patches')

    build = json.loads((ROOT / 'local/build' / HEAD / 'm1-build.json').read_text())
    binary = ROOT / 'local/build' / HEAD / BINARY
    require(sha(binary.read_bytes()) == build['binary_sha256'], 'native build identity differs')

    states = {}
    for host in ('reference', 'native'):
        directory = ROOT / 'local/captures' / ('d11-106music-' + ('ref' if host == 'reference' else 'native'))
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['rom_sha256'] == sha(candidate), 'capture ROM differs: ' + host)
        require(receipt.get('route_sha256', receipt.get('script_sha256')) == sha(SCRIPT.read_bytes()),
                'capture route differs: ' + host)
        if host == 'native':
            require(receipt['host_binary_sha256'] == build['binary_sha256'], 'capture binary differs')
        body = (directory / 'settled.wram.bin').read_bytes()
        require(len(body) == 0x20000, 'incomplete WRAM: ' + host)
        states[host] = body
        require(body[0x100] == 0x14 and body[0x0DDA] == 0x33,
                'room106 does not request slot 33: ' + host)
    require(states['reference'][0x0DDA] == states['native'][0x0DDA], 'host divergence in selection')

    ref_audio = feats(ROOT / 'local/captures/d11-106music-ref/audio.wav')
    audition = feats(AUDITION)
    require(abs(ref_audio[0] - audition[0]) < 1.0 and abs(ref_audio[1] - audition[1]) < 1.0,
            'reference audio differs from the auditioned track: %s vs %s' % (ref_audio, audition))
    apu = (ROOT / 'local/captures/d11-106music-native/apu-ram.bin').read_bytes()
    chans = [struct.unpack_from('<H', apu, a)[0] for a in (0x30, 0x32, 0x34, 0x36, 0x3A, 0x3C)]
    require(all(c == 0 or 0x5400 <= c < 0x5800 for c in chans), 'native is not playing an uploaded track')

    report = {
        'scope': __doc__.strip(),
        'head': HEAD,
        'candidate_rom_sha256': sha(candidate),
        'base_rom_sha256': sha(base),
        'binary_sha256': build['binary_sha256'],
        'changed_bytes': {'0x172C': '40->49', '0x172D/2E': 'eaea->f007', '0x1737': '16->33'},
        'captures': {'reference': 'local/captures/d11-106music-ref',
                     'native': 'local/captures/d11-106music-native'},
        'verified': ['both hosts request native slot 0x33 in room106',
                     'reference audio reproduces the user-auditioned d11-song33 track',
                     'native ARAM shows an uploaded track playing',
                     'exactly the three reviewed bytes differ from the accepted route head'],
        'limits': ['The final acceptance is the user listening to the native build; '
                   'the audition decision (song 33) is user-provided.',
                   'Other courses keep their existing music; only the room106 default request changes.'],
    }
    output = ROOT / 'local/reports/demo11-room106-music-qualification.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Room106 music checks passed: ' + str(output.relative_to(ROOT)))


if __name__ == '__main__':
    main()
