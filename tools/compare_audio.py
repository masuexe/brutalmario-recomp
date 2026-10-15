#!/usr/bin/env python3
"""Measure stereo PCM16 WAVs and compare energy envelopes without dependencies.

Envelope correlation is a diagnostic of cue/timing similarity, not proof of
waveform equivalence or audible quality. Device output is a separate gate.
"""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import wave


def load(path):
    receipt = path.parent / 'audio-stats.json'
    if receipt.exists():
        stats = json.loads(receipt.read_text())
        if stats['wav_result'] != 0 or stats['start_sample'] != 0:
            raise ValueError(f'{path}: rejected incomplete native audio history')
    with wave.open(str(path), 'rb') as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2 or wav.getcomptype() != 'NONE':
            raise ValueError(f'{path}: requires uncompressed stereo PCM16')
        rate = wav.getframerate()
        frames = wav.getnframes()
        raw = wav.readframes(frames)
    if len(raw) != frames * 4:
        raise ValueError(f'{path}: truncated PCM')
    pcm = array('h', raw)
    if sys.byteorder != 'little':
        pcm.byteswap()
    block = round(rate / 100)  # approximately 10 ms; actual size is recorded
    envelopes = []
    silence_runs = []
    start_silent = None
    for start in range(0, frames, block):
        samples = pcm[2 * start:2 * min(frames, start + block)]
        rms = math.sqrt(sum(v * v for v in samples) / len(samples))
        envelopes.append(rms)
        if rms <= 1 and start_silent is None:
            start_silent = start
        if rms > 1 and start_silent is not None:
            if start - start_silent >= rate // 10:
                silence_runs.append([start_silent / rate, start / rate])
            start_silent = None
    if start_silent is not None and frames - start_silent >= rate // 10:
        silence_runs.append([start_silent / rate, frames / rate])
    active = [i for i, rms in enumerate(envelopes) if rms > 32]
    info = {'path': str(path), 'sample_rate': rate, 'channels': 2,
            'sample_frames': frames, 'seconds': frames / rate,
            'pcm_sha256': hashlib.sha256(raw).hexdigest(),
            'rms': math.sqrt(sum(v * v for v in pcm) / len(pcm)) if pcm else 0,
            'peak': max(map(abs, pcm), default=0),
            'rail_samples': sum(v in (-32768, 32767) for v in pcm),
            'nonzero_samples': sum(v != 0 for v in pcm),
            'first_active_seconds_rms_gt_32': active[0] * block / rate if active else None,
            'silent_runs_at_least_100ms_rms_le_1': silence_runs,
            'envelope_block_frames': block}
    return info, envelopes


def correlation(a, b):
    n = len(a)
    if n < 20:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va < 1 or vb < 1:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def align(a, b, first, last, max_lag):
    best = None
    for lag in range(-max_lag, max_lag + 1):
        lo = max(first, 0, -lag)
        hi = min(last, len(a), len(b) - lag)
        score = correlation(a[lo:hi], b[lo + lag:hi + lag])
        if score is not None and (best is None or score > best['correlation']):
            best = {'lag_blocks': lag, 'correlation': score, 'compared_blocks': hi - lo}
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('native', type=Path)
    args = parser.parse_args()
    reference, a = load(args.reference)
    native, b = load(args.native)
    if reference['sample_rate'] != native['sample_rate']:
        parser.error('sample rates differ; explicitly resample a copy before comparison')
    seconds_per_block = reference['envelope_block_frames'] / reference['sample_rate']
    limit = round(.5 / seconds_per_block)
    step = round(10 / seconds_per_block)
    windows = []
    for first in range(0, min(len(a), len(b)), step):
        last = min(first + step, len(a), len(b))
        best = align(a, b, first, last, limit)
        if best:
            best['native_lag_seconds'] = best['lag_blocks'] * seconds_per_block
        windows.append({'reference_start_seconds': first * seconds_per_block,
                        'reference_end_seconds': last * seconds_per_block,
                        'best_envelope_alignment': best})
    print(json.dumps({'scope': __doc__.strip(), 'reference': reference, 'native': native,
                      'duration_difference_seconds': native['seconds'] - reference['seconds'],
                      'search_radius_seconds': limit * seconds_per_block,
                      'windows': windows}, indent=2))


if __name__ == '__main__':
    main()
