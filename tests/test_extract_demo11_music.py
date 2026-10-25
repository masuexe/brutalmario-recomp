"""Bounded checks for the Demo 1-1 music extraction tool."""
from array import array
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import extract_demo11_music as music


def silent(seconds, rate=music.REFERENCE_RATE):
    return array('h', [0]) * (int(seconds * rate) * 2)


class MusicTableTests(unittest.TestCase):
    def test_table_reader_returns_the_pinned_upload_block(self):
        rom = bytearray(0x90000)
        table = music.lorom(music.TABLE_ADDR)
        rom[table + 0x10 * 3:table + 0x10 * 3 + 3] = (0x108000).to_bytes(3, 'big')
        block = music.lorom(0x108000)
        rom[block:block + 2] = (5).to_bytes(2, 'little')
        rom[block + 2:block + 4] = (0x5400).to_bytes(2, 'little')
        rom[block + 4:block + 9] = b'abcde'
        songs = music.read_table(bytes(rom))
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0]['slot'], 0x10)
        self.assertEqual(songs[0]['payload'], b'abcde')
        self.assertEqual(songs[0]['destination'], 0x5400)
        self.assertEqual(songs[0]['rom_address'], 0x108000)

    def test_table_reader_rejects_an_unexpected_destination(self):
        rom = bytearray(0x90000)
        table = music.lorom(music.TABLE_ADDR)
        rom[table:table + 3] = (0x108000).to_bytes(3, 'big')
        block = music.lorom(0x108000)
        rom[block:block + 2] = (4).to_bytes(2, 'little')
        rom[block + 2:block + 4] = (0x6800).to_bytes(2, 'little')
        rom[block + 4:block + 8] = b'abcd'
        with self.assertRaisesRegex(ValueError, 'unexpected upload block'):
            music.read_table(bytes(rom))

    def test_table_reader_skips_a_null_entry(self):
        self.assertEqual(music.read_table(bytes(0x90000)), [])

    def test_names_use_the_slot_id_when_the_title_is_unknown(self):
        self.assertEqual(music.song_name(0x01, None), 'song-01')
        self.assertEqual(music.song_name(0x52, {'title': 'Stickerbrush Symphony'}),
                         'song-52-stickerbrush-symphony')
        self.assertEqual(music.slug('Go! Go! Kids!'), 'go-go-kids')


class CutTests(unittest.TestCase):
    def test_cut_lands_in_verified_silence_before_the_song(self):
        samples = silent(40)
        loud_start = music.frame_to_sample(2200)
        for index in range(loud_start * 2, len(samples)):
            samples[index] = 2000 if index % 2 == 0 else -2000
        cut = music.find_cut(samples, music.REFERENCE_RATE, 2196)
        self.assertEqual(cut, music.frame_to_sample(2196 - music.PREROLL_FRAMES))
        self.assertLess(cut, loud_start)

    def test_cut_walks_back_when_the_candidate_is_not_silent(self):
        samples = silent(40)
        candidate = music.frame_to_sample(2196 - music.PREROLL_FRAMES)
        quiet = music.frame_to_sample(2160)
        for index in range(quiet * 2, candidate * 2):
            samples[index] = 1000
        cut = music.find_cut(samples, music.REFERENCE_RATE, 2196)
        self.assertIsNotNone(cut)
        self.assertLess(cut, quiet + 4 * 321)

    def test_cut_requires_a_request_frame(self):
        self.assertIsNone(music.find_cut(silent(10), music.REFERENCE_RATE, None))


class ContentTests(unittest.TestCase):
    def test_content_end_ignores_a_silent_tail(self):
        samples = silent(10)
        for index in range(0, int(1.0 * music.REFERENCE_RATE) * 2):
            samples[index] = 2500 if index % 2 == 0 else -2500
        end = music.content_end(samples, music.REFERENCE_RATE)
        self.assertAlmostEqual(end, 1.0, places=2)

    def test_analysis_reports_a_silent_buffer(self):
        stats = music.analyse(silent(5), music.REFERENCE_RATE)
        self.assertEqual(stats['rms'], 0.0)
        self.assertEqual(stats['silent_fraction'], 1.0)




class IndexTests(unittest.TestCase):
    def test_index_embeds_the_id_list_and_the_level_bytes(self):
        entry = {
            'slot': '52',
            'slot_value': 0x52,
            'title': 'Stickerbrush Symphony',
            'origin_game': 'Donkey Kong Country 2',
            'payload': {'size': 3020},
            'audio': {'file': 'wav/song-52-stickerbrush-symphony.wav',
                      'duration_seconds': 100.0},
        }
        with tempfile.TemporaryDirectory() as directory:
            music.write_index(Path(directory), [entry])
            html = (Path(directory) / 'index.html').read_text()
        self.assertIn('id="ids-hex"', html)
        self.assertIn('0x52', html)
        self.assertIn('level byte 0x53', html)
        self.assertIn('<audio', html)
        self.assertIn('Copy id list', html)
        self.assertIn('Level byte (id+1)', html)


if __name__ == '__main__':
    unittest.main()


class IdListTests(unittest.TestCase):
    def test_id_list_writes_the_hex_slot_and_the_level_byte(self):
        entry = {
            'slot': '52',
            'slot_value': 0x52,
            'title': 'Stickerbrush Symphony',
            'origin_game': 'Donkey Kong Country 2',
            'payload': {'size': 3020},
            'audio': {'file': 'wav/song-52-stickerbrush-symphony.wav'},
        }
        with tempfile.TemporaryDirectory() as directory:
            music.write_ids(Path(directory), [entry])
            text = (Path(directory) / 'music-ids.txt').read_text()
            table = (Path(directory) / 'music-ids.csv').read_text()
        self.assertIn('52  dec  82  level-byte 53', text)
        self.assertIn('52,82,53,3020', table)
        self.assertIn('Stickerbrush Symphony', table)
