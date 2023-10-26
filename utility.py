from concurrent.futures import ThreadPoolExecutor

from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError


def filter_files_by_genre(all_files):
    def has_no_genre(file):
        try:
            tags = EasyID3(file)
            if "genre" in tags:
                return len(tags["genre"]) == 0
            else:
                return True
        except ID3NoHeaderError:
            return True

    with ThreadPoolExecutor() as executor:
        filtered_files = list(executor.map(has_no_genre, all_files))

    return [file for file, include in zip(all_files, filtered_files) if include]


def openPlaylist(playlist):
    with open(playlist, "r") as f:
        return [line.strip() for line in f.readlines()]
