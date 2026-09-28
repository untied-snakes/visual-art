"""The base class every visual extends."""
import pygame

from visual_art.audio import AudioFrame


class Visual:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def update(self, audio: AudioFrame, dt: float) -> None:
        """Change state. dt = seconds since last frame."""

    def draw(self, surface: pygame.Surface) -> None:
        """Paint the whole surface. Must fill the background first."""
        raise NotImplementedError
