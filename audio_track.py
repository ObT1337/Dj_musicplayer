import xml.etree.ElementTree as ET

from mutagen.easyid3 import EasyID3


class AudioTrack(EasyID3):
    def __init__(self, path=None):
        super().__init__(path)
        self.path = path
        self.title = f"{','.join(self.get('title',[]))}"
        self.artist = f"{','.join(self.get('artist',[]))}"
        self.album = f"{','.join(self.get('album',[]))}"
        self.date = f"{','.join(self.get('date',[]))}"
        self.genre = f"{','.join(self.get('genre',[]))}"
        self.bpm = f"{','.join(self.get('bpm',[]))}"
        self.full_name = f"{self.artist} - {self.title}"

    def get_all_values(self):
        return [
            self.path,
            self.title,
            self.artist,
            self.album,
            self.date,
            self.genre,
            self.bpm,
        ]

    def to_dict(self):
        return {
            "path": self.path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "date": self.date,
            "genre": self.genre,
            "bpm": self.bpm,
        }

    def translate_to_apple_music(self):
        res = {}
        for key, value in self.to_dict().items():
            if key == "path":
                key = "Location"
                # value = value.replace(" ", "%20")
                value = f"file://{value}"
                # print(value)
            elif key == "title":
                key = "Name"
            elif key == "artist":
                key = "Artist"
            elif key == "album":
                key = "Album"
            elif key == "date":
                key = "Year"
            elif key == "genre":
                key = "Genre"
            elif key == "bpm":
                key = "BPM"
            res[key] = value
        return res


class TrackCollection:
    def __init__(
        self, tracks: list[AudioTrack] | list[str] = [], name="collection", parent=False
    ) -> None:
        self.name = name
        self.tracks = []
        for track in tracks:
            if isinstance(track, str):
                track = AudioTrack(track)
            elif not isinstance(track, AudioTrack):
                raise TypeError(
                    "Tracks in the attribute 'tracks' have to be of type AudioTrack or str"
                )
            self.tracks.append(track)
        self.by_path: dict[str:AudioTrack] = dict()
        self.by_title: dict[str : list[AudioTrack]] = dict()
        self.by_artist: dict[str : list[AudioTrack]] = dict()
        self.by_album: dict[str : list[AudioTrack]] = dict()
        self.by_date: dict[str : list[AudioTrack]] = dict()
        self.by_genre: dict[str : list[AudioTrack]] = dict()
        self.by_bpm: dict[int : list[AudioTrack]] = dict()
        if not parent:
            self.playlists: list[TrackCollection] = dict()

    def __len__(self):
        return len(self.tracks)

    def __getitem__(self, index):
        return self.tracks[index]

    def __str__(self) -> str:
        return "\n".join([track.full_name for track in self.tracks])

    def __add__(self, other):
        for track in other.tracks:
            if track not in self.tracks:
                self.add_track(track)
        return self

    def add_playlist(self, other):
        self.playlists[other.name] = other
        self += other

    def export_to_apple_music(self, filename):
        # Create the root element of the XML document
        root = ET.Element("plist")
        root.set("version", "1.0")
        root_dict = ET.SubElement(root, "dict")

        tracks_element = ET.SubElement(root_dict, "key")
        tracks_element.text = "Tracks"
        tracks_dict = ET.SubElement(root_dict, "dict")

        # Add each track to the track array as a dict
        for i, track in enumerate(self.tracks):
            track_id = ET.SubElement(tracks_dict, "key")
            track_id.text = str(i)

            track_dict = ET.SubElement(tracks_dict, "dict")
            track: AudioTrack
            a_track = track.translate_to_apple_music()
            a_track["Track ID"] = str(i)
            for key, value in a_track.items():
                if value is None or value == "":
                    continue
                key_element = ET.SubElement(track_dict, "key")
                key_element.text = key
                value: str
                if value.isnumeric():
                    value_element = ET.SubElement(track_dict, "integer")
                else:
                    value_element = ET.SubElement(track_dict, "string")
                value_element.text = value

        # Write the XML document to a file
        tree = ET.ElementTree(root)
        tree.write(filename, xml_declaration=True, encoding="utf-8")

    def add_track(self, track: AudioTrack):
        if track.path in self.by_path:
            return
        self.by_path[track.path] = track
        self.tracks.append(track)
        for i, data in enumerate(
            zip(
                [*track.get_all_values()],
                [
                    1,
                    self.by_title,
                    self.by_artist,
                    self.by_album,
                    self.by_date,
                    self.by_genre,
                    self.by_bpm,
                ],
            ),
        ):
            if i == 0:
                continue
            key, _dict = data
            if key not in _dict:
                _dict[key] = []
            _dict[key].append(track)

    def remove_track(self, track):
        if track.path not in self.by_path:
            return
        if track not in self.tracks:
            return
        self.tracks.remove(track)
        for key, _dict in zip(
            [*track.get_all_values()],
            [
                [],
                self.by_title,
                self.by_artist,
                self.by_album,
                self.by_date,
                self.by_genre,
                self.by_bpm,
            ],
        ):
            if track in dict[key]:
                _dict[key].remove(track)

    def init_dicts(self):
        for track in self.tracks:
            if track.path not in self.by_path:
                self.by_path[track.path] = track
            if track.title not in self.by_title:
                self.by_title[track.title] = []
            if track.artist not in self.by_album:
                self.by_artist[track.artist] = []
            if track.album not in self.by_album:
                self.by_album[track.album] = []
            if track.date not in self.by_date:
                self.by_date[track.date] = []
            if track.genre not in self.by_genre:
                self.by_genre[track.genre] = []
            if track.bpm not in self.by_bpm:
                self.by_bpm[track.bpm] = []
            for key, _dict in zip(
                [*track.get_all_values()],
                [
                    [],
                    self.by_title,
                    self.by_artist,
                    self.by_album,
                    self.by_date,
                    self.by_genre,
                    self.by_bpm,
                ],
            ):
                _dict[key].append(track)

    def get_track_by_path(self, path: str) -> tuple[int, AudioTrack]:
        track = self.by_path[path]
        i = self.tracks.index(track)
        return i, track

    def get_tracks_by_title(self, title: str) -> list[AudioTrack]:
        return self.by_title[title]

    def get_tracks_by_artist(self, artists: str) -> list[AudioTrack]:
        return self.by_artist[artists]

    def get_tracks_by_album(self, album: str) -> list[AudioTrack]:
        return self.by_album[album]

    def get_tracks_by_date(self, date: str) -> list[AudioTrack]:
        return self.by_date[date]

    def get_tracks_by_genre(self, genre: str) -> list[AudioTrack]:
        return self.by_genre[genre]

    def get_tracks_by_bpm(self, bpm: int) -> list[AudioTrack]:
        return self.by_bpm[bpm]
