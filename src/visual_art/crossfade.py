"""Blends one visual into the next."""
import pygame

from visual_art.audio import AudioFrame
from visual_art.visual import Visual


class Crossfade:
    def __init__(self, old: Visual, new: Visual, seconds: float) -> None:
        self.old = old
        self.new = new
        self.seconds = seconds
        self.elapsed = 0.0

    @property
    def progress(self) -> float:
        if self.seconds <= 0:
            return 1.0
        return min(self.elapsed / self.seconds, 1.0)

    @property
    def done(self) -> bool:
        return self.progress >= 1.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.elapsed += dt
        self.old.update(audio, dt)
        self.new.update(audio, dt)

    def draw(self, screen: pygame.Surface, old_surface: pygame.Surface, new_surface: pygame.Surface) -> None:
        self.old.draw(old_surface)
        self.new.draw(new_surface)
        screen.blit(old_surface, (0, 0))
        new_surface.set_alpha(int(255 * self.progress))
        screen.blit(new_surface, (0, 0))
