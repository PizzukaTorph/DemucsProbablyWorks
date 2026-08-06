import unittest

from transcription.melodic import TranscriptionConfig, _merge_events, apply_preset


class TranscriptionCleaningTests(unittest.TestCase):
    def test_clean_preset_is_aggressive(self):
        config = apply_preset(TranscriptionConfig(instrument="bass", preset="clean"))
        self.assertEqual(config.min_note_ms, 140)
        self.assertEqual(config.merge_gap_ms, 90)
        self.assertEqual(config.pitch_tolerance, 1)
        self.assertGreaterEqual(config.voiced_probability, 0.75)

    def test_draft_preset_keeps_more_detail(self):
        config = apply_preset(TranscriptionConfig(instrument="guitar", preset="draft"))
        self.assertLess(config.min_note_ms, 100)
        self.assertEqual(config.pitch_tolerance, 0)

    def test_nearby_same_pitch_events_are_merged(self):
        config = apply_preset(TranscriptionConfig(instrument="bass", preset="clean"))
        events = [
            {"note": 40, "start": 0.0, "end": 0.5},
            {"note": 41, "start": 0.55, "end": 1.0},
            {"note": 43, "start": 1.2, "end": 1.5},
        ]
        merged = _merge_events(events, config)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["start"], 0.0)
        self.assertEqual(merged[0]["end"], 1.0)


if __name__ == "__main__":
    unittest.main()
