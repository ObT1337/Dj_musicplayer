#! python3
import os
import unittest

from audio_track import TrackCollection
from PyQt6.QtWidgets import QApplication
from settings import IOSettings, UISettings
from ui import UI

TEST_PLAYLIST = os.path.join(IOSettings.wd, "static", "tracks", "playlists", "test.m3u")

TEST_APPLE_XML = os.path.join(IOSettings.wd, "target", "export", "test_apple.xml")


class TestUI(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.settings = UISettings()
        self.ui = UI(self.settings)

    # @unittest.skip
    def test_load_playlist(self):
        self.ui.open_playlist_from_file(TEST_PLAYLIST)
        self.app.exec()

    def test_export_to_apple_music_app(self):
        self.ui.open_playlist_from_file(TEST_PLAYLIST)
        self.ui.collection.export_to_apple_music(TEST_APPLE_XML)

    def tearDown(self):
        self.ui.close()
        del self.ui
        del self.settings
        del self.app


if __name__ == "__main__":
    unittest.main(verbosity=2)
