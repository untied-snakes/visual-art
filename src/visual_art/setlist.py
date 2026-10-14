"""Plays visuals in a fixed order, one per song. It only moves when told to."""
from pathlib import Path


class Setlist:
    def __init__(self, songs: list[tuple[str, str]]) -> None:
        self.songs = songs  # [(visual name, song title), ...]
        self.names = [name for name, _ in songs]
        self.index = -1  # nothing playing yet; next() starts on the first song

    def next(self) -> str:
        self.index = (self.index + 1) % len(self.songs)
        return self.names[self.index]

    def previous(self) -> str:
        self.index = (self.index - 1) % len(self.songs)
        return self.names[self.index]

    def go_to(self, index: int) -> str:
        self.index = index % len(self.songs)
        return self.names[self.index]

    def label(self) -> str:
        """What's on screen, for the terminal, e.g. '3/10  canyon  Song Three'."""
        name, title = self.songs[self.index]
        return f"{self.index + 1}/{len(self.songs)}  {name:10s}  {title}"


def read_setlist(path: Path) -> list[tuple[str, str]]:
    """Read a setlist file: one song per line, the visual name then an optional title.
    Blank lines and lines starting with # are skipped."""
    songs = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, title = line.partition(" ")
        songs.append((name, title.strip()))
    return songs
