"""Pictures and videos for a visual, from media/<visual name>/.

Drop .jpg/.png/.mp4/.mov files into, say, media/dunes/ and the dunes visual shows
them. With an empty or missing folder the visual looks the way it always has.
Several files take turns, crossfading every `seconds_each` seconds. Videos loop.

Files load and decode on background threads, so a big photo or a video never
makes the live picture stutter. Visuals just call update(dt) and frame().
"""
import logging
import queue
import threading
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pygame

from visual_art import palette

# visual-art/media, next to src/ and setlist.txt.
MEDIA_FOLDER = Path(__file__).resolve().parents[2] / "media"
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tga"}
VIDEO_TYPES = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}

# Live, never wait: show what's ready and catch up. Rendering to MP4 sets this
# to False so every picture is loaded and every video frame is used, in order.
realtime = True

# imageio-ffmpeg warns every time a video's size differs from ours. We resize on
# purpose, so hide that warning; real errors still show up.
logging.getLogger("imageio_ffmpeg").setLevel(logging.ERROR)

# Pictures already loaded, so a visual coming back on screen doesn't load them again.
_cache: dict[tuple, pygame.Surface] = {}


def files_for(name: str) -> list[Path]:
    """The images and videos in media/<name>/, in name order."""
    folder = MEDIA_FOLDER / name
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_TYPES | VIDEO_TYPES)


class Media:
    def __init__(
        self,
        name: str,
        size: tuple[int, int],
        tint: list | None = None,
        tint_strength: float = 1.0,
        seconds_each: float = 30.0,
        fade: float = 3.0,
        speed: float = 1.0,
        start: int = 0,
    ) -> None:
        """name: the visual's name, which is also its folder in media/.
        size: every picture is cropped to fill exactly this size.
        tint: recolour pictures along these colours (dark -> bright) so they match the show.
        tint_strength: 1 = fully recoloured, 0 = original colours.
        speed: video playback speed; 0.5 is half speed.
        start: which file to begin with, so several Medias in one visual can show different files."""
        self.files = files_for(name)
        self.size = size
        self.tint = tint
        self.tint_strength = tint_strength
        self.seconds_each = seconds_each
        self.fade_seconds = fade
        self.speed = speed
        self.index = start % len(self.files) if self.files else 0
        self.source = self._open(self.index) if self.files else None
        self.previous = None  # the file fading out, while a new one fades in
        self.progress = 0.0
        self.time_on = 0.0
        self.blend = pygame.Surface(size)

    @property
    def has_files(self) -> bool:
        return bool(self.files)

    def update(self, dt: float) -> None:
        if self.source is None:
            return
        self.source.update(dt)
        self.time_on += dt
        if self.previous is not None:
            self.previous.update(dt)
            if self.source.frame() is not None:  # don't start fading until it has loaded
                self.progress += dt / self.fade_seconds
                if self.progress >= 1:
                    self.previous.close()
                    self.previous = None
        elif len(self.files) > 1 and self.time_on >= self.seconds_each:
            self.index = (self.index + 1) % len(self.files)
            self.previous, self.source = self.source, self._open(self.index)
            self.progress = 0.0
            self.time_on = 0.0

    def frame(self) -> pygame.Surface | None:
        """The picture to show now, exactly `size` big. None if nothing is loaded yet."""
        if self.source is None:
            return None
        new = self.source.frame()
        old = self.previous.frame() if self.previous is not None else None
        if old is None:
            return new
        if new is None:
            return old
        self.blend.blit(old, (0, 0))
        new.set_alpha(int(255 * min(self.progress, 1.0)))
        self.blend.blit(new, (0, 0))
        new.set_alpha(None)
        return self.blend

    def close(self) -> None:
        """Stop any video decoding. Called when the visual leaves the screen."""
        for source in (self.source, self.previous):
            if source is not None:
                source.close()

    def _open(self, index: int):
        path = self.files[index]
        if path.suffix.lower() in VIDEO_TYPES:
            return _Video(path, self.size, self.tint, self.tint_strength, self.speed)
        return _Picture(path, self.size, self.tint, self.tint_strength)


class _Picture:
    def __init__(self, path: Path, size, tint, tint_strength) -> None:
        self.path = path
        self.key = (path, size, tuple(tint or ()), tint_strength)
        self.size = size
        self.tint = tint
        self.tint_strength = tint_strength
        self.surface = _cache.get(self.key)
        if self.surface is None:
            if realtime:
                threading.Thread(target=self._load, daemon=True).start()
            else:
                self._load()

    def _load(self) -> None:
        try:
            image = pygame.image.load(self.path)
        except (pygame.error, OSError) as error:
            print(f"  ! couldn't load {self.path.name}: {error}")
            return
        pixels = _tinted(_cover(image, self.size), self.tint, self.tint_strength)
        surface = pygame.surfarray.make_surface(pixels)
        _cache[self.key] = surface
        self.surface = surface

    def update(self, dt: float) -> None:
        pass

    def frame(self) -> pygame.Surface | None:
        return self.surface

    def close(self) -> None:
        pass


class _Video:
    def __init__(self, path: Path, size, tint, tint_strength, speed) -> None:
        self.path = path
        self.size = size
        self.tint = tint
        self.tint_strength = tint_strength
        self.speed = speed
        self.fps = 30.0  # replaced by the real rate once the file is open
        self.clock = 0.0
        self.surface = None
        # The decoder thread keeps a few frames ready here.
        self.frames: queue.Queue[pygame.Surface] = queue.Queue(maxsize=4)
        self.stopped = threading.Event()
        threading.Thread(target=self._decode, daemon=True).start()

    def update(self, dt: float) -> None:
        self.clock += dt * self.speed
        if self.surface is None:
            self._take_frame()
        while self.clock >= 1 / self.fps:
            self.clock -= 1 / self.fps
            if not self._take_frame():
                self.clock = 0.0  # decoder is behind; hold this frame
                break

    def frame(self) -> pygame.Surface | None:
        return self.surface

    def close(self) -> None:
        self.stopped.set()

    def _take_frame(self) -> bool:
        try:
            self.surface = self.frames.get(block=not realtime, timeout=None if realtime else 10)
            return True
        except queue.Empty:
            return False

    def _decode(self) -> None:
        width, height = self.size
        # ffmpeg scales and crops to our size, so Python only ever sees small frames.
        crop = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        while not self.stopped.is_set():  # once per loop of the video
            reader = imageio_ffmpeg.read_frames(str(self.path), output_params=["-an", "-vf", crop])
            try:
                self.fps = next(reader).get("fps") or 30.0
                for raw in reader:
                    pixels = np.frombuffer(raw, np.uint8).reshape(height, width, 3).swapaxes(0, 1)
                    surface = pygame.surfarray.make_surface(_tinted(pixels, self.tint, self.tint_strength))
                    while not self.stopped.is_set():
                        try:
                            self.frames.put(surface, timeout=0.2)
                            break
                        except queue.Full:
                            pass
                    if self.stopped.is_set():
                        break
            except Exception as error:
                print(f"  ! couldn't play {self.path.name}: {error}")
                return
            finally:
                reader.close()  # stops ffmpeg


def _cover(image: pygame.Surface, size: tuple[int, int]) -> np.ndarray:
    """Scale image to fill size completely, cropping the edges that stick out.
    Returns pixels as a (width, height, 3) array."""
    # Copy onto a plain 32-bit surface first: smoothscale can't handle paletted PNGs.
    plain = pygame.Surface(image.get_size(), 0, 32)
    plain.blit(image, (0, 0))
    width, height = size
    scale = max(width / plain.get_width(), height / plain.get_height())
    scaled_size = (max(width, round(plain.get_width() * scale)), max(height, round(plain.get_height() * scale)))
    scaled = pygame.transform.smoothscale(plain, scaled_size)
    left = (scaled_size[0] - width) // 2
    top = (scaled_size[1] - height) // 2
    return pygame.surfarray.array3d(scaled)[left:left + width, top:top + height]


def _tinted(pixels: np.ndarray, tint: list | None, strength: float) -> np.ndarray:
    """Recolour by brightness: the darkest parts become tint[0], the brightest tint[-1]."""
    if not tint or strength <= 0:
        return pixels
    wide = pixels.astype(np.uint16)  # room for the sums below without overflowing
    brightness = (wide[..., 0] * 77 + wide[..., 1] * 150 + wide[..., 2] * 29) >> 8
    lookup = np.array([palette.ramp(tint, i / 255) for i in range(256)], dtype=np.uint8)
    toned = lookup[brightness]
    if strength >= 1:
        return toned
    return (pixels * (1 - strength) + toned * strength).astype(np.uint8)
