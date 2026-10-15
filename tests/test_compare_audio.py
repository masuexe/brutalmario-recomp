"""Check audio measurement and lag direction with synthetic PCM."""
import math
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from compare_audio import align, load


class AudioComparisonTests(unittest.TestCase):
    def test_incomplete_native_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'audio-stats.json').write_text(json.dumps({'wav_result': 0, 'start_sample': 32000}))
            with self.assertRaisesRegex(ValueError, 'incomplete native audio history'):
                load(path / 'audio.wav')

    def test_known_envelope_delay(self):
        reference = [abs(math.sin(i * .31) * math.cos(i * .071)) for i in range(500)]
        native = [0] * 7 + reference
        result = align(reference, native, 20, 480, 20)
        self.assertEqual(result['lag_blocks'], 7)
        self.assertAlmostEqual(result['correlation'], 1)

    def test_silence_has_no_invented_alignment(self):
        self.assertIsNone(align([0] * 100, [0] * 100, 0, 100, 10))

    def test_pcm_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.wav'
            with wave.open(str(path), 'wb') as wav:
                wav.setparams((2, 2, 32000, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(3200 * 4) + struct.pack('<hh', 1000, -1000) * 3200)
            info, envelope = load(path)
            self.assertEqual(info['sample_frames'], 6400)
            self.assertEqual(info['peak'], 1000)
            self.assertEqual(info['rail_samples'], 0)
            self.assertEqual(info['first_active_seconds_rms_gt_32'], .1)
            self.assertEqual(info['silent_runs_at_least_100ms_rms_le_1'], [[0, .1]])
            self.assertEqual(len(envelope), 20)
