"""Bounded checks for the level music retarget recipe helpers.

The tests use synthetic level blocks.  They check the music object pattern,
the site choice rule and the first-fit allocator.  They do not claim an audible
match or a playable course.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_music_retarget as retarget


class MusicObjectTests(unittest.TestCase):
    def test_music_object_masks_ignore_screen_and_height_bits(self):
        block = bytes.fromhex('406025')
        self.assertEqual(retarget.music_objects(block),
                         [{'index': 0, 'param': 0x25}])

    def test_other_object_numbers_are_not_music(self):
        # 0x40 0x50 is object 0x25 and 0x60 0x60 is object 0x36.
        block = bytes.fromhex('405025606025')
        self.assertEqual(retarget.music_objects(block), [])

    def test_screen_and_height_bits_stay_inside_the_mask(self):
        block = bytes.fromhex('7f6005')
        self.assertEqual(retarget.music_objects(block), [])

    def test_truncated_tail_is_skipped(self):
        block = bytes.fromhex('4060')
        self.assertEqual(retarget.music_objects(block), [])


class SiteChoiceTests(unittest.TestCase):
    def test_single_object_is_always_chosen(self):
        objects = [{'index': 7, 'param': 0x10}]
        self.assertEqual(retarget.choose_site({'wrong': '0f'}, objects), objects[0])

    def test_parameter_form_matches_the_song_number_plus_one(self):
        objects = [{'index': 1, 'param': 0x24}, {'index': 9, 'param': 0x51}]
        self.assertEqual(retarget.choose_site({'wrong': '23'}, objects)['index'], 1)

    def test_raw_parameter_form_is_accepted(self):
        objects = [{'index': 1, 'param': 0x24}, {'index': 9, 'param': 0x51}]
        self.assertEqual(retarget.choose_site({'wrong': '51'}, objects)['index'], 9)

    def test_two_matches_are_rejected(self):
        objects = [{'index': 1, 'param': 0x24}, {'index': 9, 'param': 0x24}]
        self.assertIsNone(retarget.choose_site({'wrong': '23'}, objects))

    def test_unknown_song_is_rejected(self):
        objects = [{'index': 1, 'param': 0x24}, {'index': 9, 'param': 0x51}]
        self.assertIsNone(retarget.choose_site({'wrong': '77'}, objects))

    def test_entry_without_a_wrong_id_is_rejected(self):
        objects = [{'index': 1, 'param': 0x24}, {'index': 9, 'param': 0x51}]
        self.assertIsNone(retarget.choose_site({}, objects))


class AllocationTests(unittest.TestCase):
    def test_first_fit_keeps_every_range_inside_its_segment(self):
        segments = [(0x1000, 300), (0x9000, 600)]
        ranges = retarget.allocate(segments, [200, 400, 90])
        # First fit: the third range returns to the first segment remainder.
        self.assertEqual(ranges, [(0x1000, 200), (0x9000, 400), (0x10c8, 90)])
        for start, size in ranges:
            self.assertEqual(start // 0x8000, (start + size - 1) // 0x8000)

    def test_a_size_that_fits_no_segment_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no free within-bank range'):
            retarget.allocate([(0x1000, 100)], [500])

    def test_free_segments_skip_protected_rats_blocks(self):
        rom = bytearray(0x10000)
        count = 40
        rom[0x1000:0x1008] = (b'STAR' + count.to_bytes(2, 'little') +
                              (count ^ 0xffff).to_bytes(2, 'little'))
        rom[0x1008:0x1008 + count + 1] = bytes(count + 1)
        segments = retarget.free_segments(bytes(rom), 1000)
        protected = (0x1000, 0x1008 + count + 1)
        for start, length in segments:
            self.assertFalse(start < protected[1] and protected[0] < start + length,
                             'a free range overlaps the protected block')
        self.assertTrue(segments)
        self.assertFalse(any(0x1000 <= start < protected[1] for start, _ in segments))

    def test_free_segments_stop_at_a_bank_boundary(self):
        # A zero run that crosses 0x8000 must become two ranges.
        rom = bytearray(b'\x01' * 0x10000)
        rom[0x7f00:0x8000] = bytes(0x100)
        rom[0x8000:0x9000] = bytes(0x1000)
        segments = retarget.free_segments(bytes(rom), 0x100)
        self.assertEqual(segments, [(0x7f00, 0x100), (0x8000, 0x1000)])


class SongPointerTests(unittest.TestCase):
    def test_a_low_bank_keeps_the_plain_form(self):
        track = {'allocation': {'offset': 0x10640D}}
        self.assertEqual(retarget.song_pointer(track), bytes.fromhex('20e415'))

    def test_bank_7e_and_7f_use_the_mirror(self):
        # Banks 0x7E and 0x7F are WRAM, so the table entry must use the mirror.
        self.assertEqual(retarget.song_pointer({'allocation': {'offset': 0x3F62F7}}),
                         bytes.fromhex('fee2ff'))
        self.assertEqual(retarget.song_pointer({'allocation': {'offset': 0x3FF018}}),
                         bytes.fromhex('fff020'))

    def test_the_pointer_addresses_the_payload(self):
        for offset in (0x10640D, 0x3F62F7, 0x3FF018, 0x27B448):
            entry = retarget.song_pointer({'allocation': {'offset': offset}})
            self.assertEqual(retarget.lorom(int.from_bytes(entry, 'big')), offset + 8)


class RecordTableTests(unittest.TestCase):
    def test_a_record_without_the_selection_flag_is_free(self):
        rom = bytearray(b'\x01' * 0x400000)
        table = retarget.lorom(retarget.RECORD_TABLE)
        for index in range(512):
            offset = table + index * 32
            rom[offset:offset + 2] = (0x8100).to_bytes(2, 'little')
        offset = table + 0x24 * 32
        rom[offset:offset + 2] = (0x0100).to_bytes(2, 'little')
        room, found = retarget.free_graphics_record(bytes(rom))
        self.assertEqual((room, found), (0x24, offset))

    def test_a_selected_record_is_not_free(self):
        rom = bytearray(0x400000)
        table = retarget.lorom(retarget.RECORD_TABLE)
        for index in range(512):
            offset = table + index * 32
            rom[offset:offset + 2] = (0x8100).to_bytes(2, 'little')
        with self.assertRaisesRegex(ValueError, 'no free room graphics record'):
            retarget.free_graphics_record(bytes(rom))


if __name__ == '__main__':
    unittest.main()
