"""The base class every visual extends."""
import pygame

from visual_art.audio import AudioFrame


class Visual:
    # If this visual uses pictures from media/<name>/, say how, e.g. "background".
    # `visual-art list` shows it.
    media_use: str | None = None

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def update(self, audio: AudioFrame, dt: float) -> None:
        """Change state. dt = seconds since last frame."""

    def draw(self, surface: pygame.Surface) -> None:
        """Paint the whole surface. Must fill the background first."""
        raise NotImplementedError

    def close(self) -> None:
        """Called when the visual leaves the screen. Stop anything running in the background."""
