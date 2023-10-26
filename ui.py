import copy
import glob
import logging
import os
import platform
import traceback

import utility
from audio_track import AudioTrack, TrackCollection
from logger import Logger
from mutagen.easyid3 import EasyID3
from PyQt6.QtCore import QDir, QSize, Qt, QTime, QTimer, QUrl
from PyQt6.QtGui import QAction, QFont, QIcon, QKeySequence, QMovie, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from settings import LoggerSettings, UISettings
from widgets import LimitedGridLayout, RemovableButton, TabWidget, TrackTable

log = Logger("UI", LoggerSettings.log_level)


class UI(QMainWindow):
    def __init__(
        self,
        ui_settings: UISettings,
    ) -> None:
        super().__init__()
        self.ui_settings = ui_settings

        self.setWindowTitle("Music Player")
        self.showFullScreen()

        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setPosition(0)

        # Define Theme
        self.setPalette(QApplication.style().standardPalette())

        # Timer for updating time labels every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_labels)
        self.collection = TrackCollection()
        self.focused_collection = self.collection
        self.current_track = None
        self.widget_init()
        self.init_menubar()

        self.show()

    def widget_init(self):
        # Create Buttons
        self.load_button = QPushButton("Load tracks from directory")
        self.show_file = QPushButton()
        if platform.system() == "Darwin":
            self.show_file.setText("Show file in Finder")
        elif platform.system() == "Windows":
            self.show_file.setText("Show file in Explorer")
        else:
            self.show_file.setText("Show file in File Manager")

        # Create Tag labels
        self.track_label = QLabel("Track Name")
        self.bpm_label = QLabel("BPM")
        self.genre_label = QLabel("Genre")
        self.date_label = QLabel("Date")
        self.path_label = QLabel("Path")

        # Track_table
        self.track_table = TrackTable(parent_window=self)

        ###### Utility Widget
        self.utilities_one = TabWidget()
        self.utilities_two = TabWidget()

        # Genre Buttons
        self.genre_buttons_mode = "set"
        self.genre_buttons_tab = QVBoxLayout()
        self.genre_buttons = LimitedGridLayout(max_columns=5)
        plus_button = QPushButton("Add Genre Button +")
        plus_button.clicked.connect(self.create_genre_button)
        self.genre_buttons_tab.addWidget(plus_button)
        self.genre_buttons_tab.addStretch(1)
        self.genre_buttons_tab.addLayout(self.genre_buttons)
        self.utilities_one.add_tab("Genres", self.genre_buttons_tab)

        # Playlist Buttons
        self.playlist_buttons_tab = QVBoxLayout()
        self.playlist_buttons = LimitedGridLayout(max_columns=5)
        plus_button = QPushButton("New Playlist +")
        plus_button.clicked.connect(self.create_playlist)
        self.playlist_buttons_tab.addWidget(plus_button)
        self.playlist_buttons_tab.addStretch(1)
        self.playlist_buttons_tab.addLayout(self.playlist_buttons)
        self.utilities_one.add_tab("Playlists", self.playlist_buttons_tab)

        # Media buttons
        self.play_button = QPushButton(">")
        self.pause_button = QPushButton("||")
        self.stop_button = QPushButton("[]")
        self.back_button = QPushButton("<<")
        self.forward_button = QPushButton(">>")

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setValue(0)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.media_player.audioOutput().setVolume(50)

        # Add labels for time display
        self.time_elapsed_label = QLabel("00:00")
        self.time_remaining_label = QLabel("00:00")

        # Add label for Volume display
        self.volume_label = QLabel("50%")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.path_label)
        layout.addWidget(self.show_file)
        layout.addWidget(self.track_label)
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(self.bpm_label)
        tags_layout.addWidget(self.genre_label)
        tags_layout.addWidget(self.date_label)
        table_util_layout = QHBoxLayout()
        util_layout = QVBoxLayout()
        util_layout.addWidget(self.utilities_one)
        util_layout.addWidget(self.utilities_two)
        table_util_layout.addWidget(self.track_table)
        table_util_layout.addLayout(util_layout)

        bwd_fwd = QHBoxLayout()
        bwd_fwd.addWidget(self.back_button)
        bwd_fwd.addWidget(self.forward_button)

        media_buttons = QHBoxLayout()
        media_buttons.addWidget(self.play_button)
        media_buttons.addWidget(self.pause_button)
        media_buttons.addWidget(self.stop_button)
        media_buttons.addWidget(self.time_elapsed_label)
        media_buttons.addWidget(self.seek_slider)
        media_buttons.addWidget(self.time_remaining_label)
        media_buttons.addWidget(self.volume_slider)
        media_buttons.addWidget(self.volume_label)

        layout.addLayout(tags_layout)
        layout.addLayout(table_util_layout)
        layout.addLayout(bwd_fwd)
        layout.addLayout(media_buttons)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect buttons
        self.load_button.clicked.connect(self.navigate_directory_with_no_genre_tracks)
        self.show_file.clicked.connect(self.show_file_in_explorer)
        self.back_button.clicked.connect(self.back)
        self.forward_button.clicked.connect(self.forward)
        self.play_button.clicked.connect(self.play)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)

        # Connect volume slider
        self.volume_slider.valueChanged.connect(self.change_volume)

        # Connect seek slider
        self.seek_slider.valueChanged.connect(self.set_position)

        # Connect media player positionChanged signal
        self.media_player.positionChanged.connect(self.update_time_labels)

        self.media_player.sourceChanged.connect(self.update_track)

        # File path of the current track
        self.current_track = ""
        self.current_tags = None
        self.current_index = None

        # Create a list to hold the button texts
        self.saved_button_texts = set()
        self.num_dyn_buttons = 0
        # Create and add dynamic buttons to the grid layout
        self.button_dict = {}  # Dictionary to store button instances

        # Read the saved button texts from the file
        self.load_saved_button_texts()

    def show_file_in_explorer(self):
        if not self.current_track:
            return
        if platform.system() == "Darwin":
            os.system(f"open -R '{self.current_track}'")
        elif platform.system() == "Windows":
            os.system(f"explorer '/select,{self.current_track}'")
        else:
            os.system(f"xdg-open '{self.current_track}'")

    def dynamic_buttons(
        self,
        window_title: str = "Enter Button Text",
        window_label: str = "Button Text:",
    ):
        # Ask the user for the button text
        button_text, ok = QInputDialog.getText(self, window_title, window_label)

        # If the user clicked "OK" and entered some text, create a new button
        if ok and button_text:
            if button_text in self.saved_button_texts:
                QMessageBox.warning(
                    self, "Duplicate Button", "This button already exists!"
                )
                return
            self.add_dynamic_button(button_text)
            self.saved_button_texts.add(button_text)
            # Save the updated list of button texts to the file
            self.save_button_texts()

    def create_genre_button(self):
        self.dynamic_buttons("Enter Genre", "Genre:")

    def add_dynamic_button(self, button_text):
        new_button = RemovableButton(button_text, self.genre_buttons)
        # Connect the new button's clicked signal to a slot
        new_button.clicked(lambda: self.on_genre_button_click(new_button))
        new_button.on_remove(lambda: self.on_genre_button_remove_click(new_button))
        # new_button.remove_button.clicked.connect(lambda: self.remove_dynamic_button(new_button))

    def init_saved_buttons(self):
        for button_text in self.saved_button_texts:
            self.add_dynamic_button(button_text)

    def on_genre_button_click(self, button):
        button_text = button.text
        if self.current_track and self.current_tags:
            if "genre" in self.current_tags and len(self.current_tags["genre"]) > 0:
                genre = list(self.current_tags["genre"][0].split(" / "))
                if button_text in genre:
                    genre.remove(button_text)
                else:
                    genre += [button_text]
            else:
                genre = [button_text]
            genre = " / ".join(genre)
            self.current_tags.update({"genre": genre})
            self.genre_label.setText(f"Genre: {genre}")
            self.current_tags.save()

    def on_genre_button_remove_click(self, button):
        button_text = button.text
        self.saved_button_texts.remove(button_text)
        self.save_button_texts()
        self.genre_buttons.clear_layout()
        self.init_saved_buttons()

    def load_saved_button_texts(self):
        try:
            with open("saved_buttons.txt", "r") as file:
                self.saved_button_texts = set((line.strip() for line in file))
                self.init_saved_buttons()
        except FileNotFoundError:
            # If the file is not found, create an empty tuple
            self.saved_button_texts = set()

    def save_button_texts(self):
        with open("saved_buttons.txt", "w") as file:
            file.write("\n".join(self.saved_button_texts))

    def play(self):
        if self.current_track:
            self.media_player.play()
            # Start the timer to update time labels every second
            self.timer.start(1000)

    def back(self):
        if self.current_track is not None and self.current_index is not None:
            if self.current_index == 0:
                self.load_track(len(self.focused_collection) - 1)
            else:
                self.load_track(self.current_index - 1)

    def forward(self):
        if self.current_track is not None and self.current_index is not None:
            if self.current_index < len(self.focused_collection) - 1:
                self.load_track(self.current_index + 1)
            else:
                self.load_track(0)

    def pause(self):
        self.media_player.pause()
        self.timer.stop()

    def stop(self):
        self.timer.stop()
        self.media_player.stop()

    def change_volume(self, value):
        self.media_player.audioOutput().setVolume(value)

        self.volume_label.setText(str(value) + "%")

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_time_labels(self):
        if self.media_player.duration() > 0:
            total_duration = self.media_player.duration()
            current_position = self.media_player.position()

            elapsed_time = QTime(0, 0).addMSecs(current_position).toString("mm:ss")
            self.time_elapsed_label.setText(elapsed_time)

            remaining_time = (
                QTime(0, 0)
                .addMSecs(total_duration - current_position)
                .toString("mm:ss")
            )
            self.time_remaining_label.setText(remaining_time)

            # Update seek slider position
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(current_position)
            self.seek_slider.blockSignals(False)

    def update_track(self):
        self.update_time_labels()
        self.seek_slider.setRange(0, self.media_player.duration())
        self.media_player.setPosition(0)
        self.seek_slider.setValue(0)

        current_track = self.current_track
        track_name = f"{current_track.artist} - {current_track.title}"
        self.track_label.setText(f"Track: {track_name}")

        self.bpm_label.setText(f"BPM: {current_track.bpm}")

        self.genre_label.setText(f"Genre: {current_track.genre}")

        self.date_label.setText(f"Date: {current_track.date}")

    def open_files_from_directory(self):
        all_files = self.get_files_from_directory()
        if not all_files:
            return
        self.open_tracks(TrackCollection(all_files))

    def get_files_from_directory(self):
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", options=options
        )
        if not directory:
            return

        all_files = glob.glob(os.path.join(directory, "**"), recursive=True)
        all_files = [
            os.path.abspath(file)
            for file in all_files
            if os.path.isfile(file) and file.endswith((".mp3", ".wav"))
        ]
        return all_files

    def navigate_directory_with_no_genre_tracks(self):
        all_files = self.open_files_from_directory()
        if not all_files:
            return

        self.open_tracks(TrackCollection(utility.filter_files_by_genre(all_files)))

    def select_file_in_file_dialog(self, file_filter: str = "All Files (*.*)"):
        """Allows the user to navigate to a file on the system. Currently the file_filter is not implemented and will be ignored.

        Args:
            file_filter (str, optional): Limits the selection of files to certain file types. Defaults to None and is currently ignored as not implemented

        Returns:
            Tuple[str,str]: Returns a tuple of the selected file.
        """
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly
        file_dialog = QFileDialog(self, options=options)
        selected_file, _ = file_dialog.getOpenFileName(
            self, "Select File", filter=file_filter
        )
        return selected_file

    def select_playlist_in_file_dialog(self):
        file_filter = "Playlist (*.m3u)"
        selected_playlist = self.select_file_in_file_dialog(file_filter)
        if not selected_playlist:
            return
        selected_playlist
        log.debug(f"Selected playlist: {selected_playlist}")
        return selected_playlist

    def load_files_from_playlist(self, playlist_file: str):
        with open(playlist_file, "r") as file:
            all_files = [
                os.path.abspath(line.strip())
                for line in file
                if not line.startswith("#")
            ]
        print(all_files)
        return all_files

    def open_playlist_from_file_dialog(self):
        selected_playlist = self.select_playlist_in_file_dialog()
        if not selected_playlist:
            return
        self.open_playlist_from_file(selected_playlist)

    def open_playlist_from_file(self, playlist):
        self.open_tracks(TrackCollection(self.load_files_from_playlist(playlist)))

    def open_tracks(self, tracks: TrackCollection):
        self.collection += tracks
        self.focused_collection = tracks
        self.load_track(0, tracks)

    def load_track(self, identifier, tracks: None | TrackCollection = None):
        if tracks:
            self.selected_tracks = tracks
            if isinstance(identifier, str):
                identifier, _ = self.selected_tracks.get_track_by_path(identifier)
            self.re_init_track_table(tracks, identifier)
        if isinstance(identifier, int):
            track = self.collection[identifier]
            index = identifier
        else:
            index, track = self.collection.get_track_by_path(identifier)

        self.path_label.setText(f"Path: {track.path}")
        was_playing = self.media_player.isPlaying()
        self.current_index = index
        self.current_track = track
        log.debug(f"Loading track: {track.full_name}")
        self.media_player.setSource(QUrl.fromLocalFile(track.path))

        log.debug(f"Loaded track: {track.full_name}")
        if was_playing:
            self.play()

    def keyPressEvent(self, event):
        key_sequence = event.key()
        if event.key() == Qt.Key.Key_Q:
            self.close()  # Close the window when Q key is pressed
        if event.key() == Qt.Key.Key_E:
            next_step = {
                -1: lambda: None,
                0: self.start,
            }
            next_step[self.window_state]()
        if event.key() == Qt.Key.Key_Space or key_sequence == Qt.Key.Key_MediaNext:
            if self.media_player.isPlaying():
                self.pause()
            else:
                self.play()
        if event.key() == Qt.Key.Key_MediaNext or key_sequence == Qt.Key.Key_Right:
            self.forward()
        if event.key() == Qt.Key.Key_MediaPrevious or key_sequence == Qt.Key.Key_Left:
            self.back()
        if (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_O
        ):
            self.navigate_directory()

    def export_to_file_dialog(self):
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.ReadOnly
        return QFileDialog.getSaveFileName(self, "Select target", options=options)

    def export_collection_to_apple_music_dialog(self, path):
        path = self.export_to_file_dialog()
        self.collection.export_to_apple_music(path)

    def init_menubar(self):
        open_playlist = QAction("&From Playlist", self)
        open_playlist.setStatusTip("Opens a playlist file")
        open_playlist.triggered.connect(self.open_playlist_from_file)

        open_files_from_dir = QAction("&From Directory", self)
        open_files_from_dir.setStatusTip("Opens a all files from a certain Directory")
        open_files_from_dir.triggered.connect(self.open_files_from_directory)

        export_to_itunes = QAction("&Export to iTunes", self)
        export_to_itunes.setStatusTip("Exports the current track collection to Itunes")
        export_to_itunes.triggered.connect(self.export_collection_to_apple_music_dialog)

        menu = self.menuBar()
        self.file_menu = menu.addMenu("&File")
        self.open_menu = self.file_menu.addMenu("&Open")
        self.open_menu.addAction(open_playlist)
        self.open_menu.addAction(open_files_from_dir)

        self.export_menu = self.file_menu.addMenu("&Export")
        self.export_menu.addAction(export_to_itunes)

    def re_init_track_table(self, tracks: TrackCollection, index=0):
        self.track_table.clearContents()
        self.track_table.all_tracks = tracks
        self.track_table.selected_track = tracks[index]
        self.track_table.update_table(tracks)

    def create_playlist(self):
        playlist_name, ok = QInputDialog.getText(
            self, "Enter Playlist Name", "Playlist Name:"
        )
        if ok and playlist_name:
            self.collection.playlists[playlist_name] = TrackCollection(
                name=playlist_name, parent=self.collection
            )
