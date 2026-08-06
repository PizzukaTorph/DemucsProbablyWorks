import importlib.util
import unittest
from pathlib import Path


WATCHER_PATH = Path(__file__).resolve().parents[1] / "demucs" / "watcher.py"
spec = importlib.util.spec_from_file_location("project_demucs_watcher", WATCHER_PATH)
watcher = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(watcher)


class SupportedAudioFileTests(unittest.TestCase):
    def test_accepts_supported_audio_extensions_case_insensitively(self):
        for filename in (
            "song.wav",
            "song.MP3",
            "song.flac",
            "song.ogg",
            "song.m4a",
            "song.aac",
        ):
            with self.subTest(filename=filename):
                self.assertTrue(watcher.is_supported_audio_file(filename))

    def test_rejects_hidden_files(self):
        for filename in (".gitkeep", ".DS_Store", ".hidden.mp3"):
            with self.subTest(filename=filename):
                self.assertFalse(watcher.is_supported_audio_file(filename))

    def test_rejects_non_audio_and_temporary_files(self):
        for filename in (
            "status.json",
            "notes.txt",
            "song.mp3.tmp",
            "song.wav.partial",
            "README",
        ):
            with self.subTest(filename=filename):
                self.assertFalse(watcher.is_supported_audio_file(filename))


if __name__ == "__main__":
    unittest.main()
