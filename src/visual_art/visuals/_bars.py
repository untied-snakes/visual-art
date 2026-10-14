"""Frequency bars across the bottom of the screen."""
import numpy as np
import pygame

from visual_art.audio import AudioFrame
from visual_art.visual import Visual

BAR_COUNT = 48


class BarsVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.heights = np.zeros(BAR_COUNT)

    def update(self, audio: AudioFrame, dt: float) -> None:
        # Group the spectrum into bars on a log scale, so bass isn't squashed into one bar.
        edges = np.geomspace(1, len(audio.spectrum), BAR_COUNT + 1).astype(int)
        levels = np.array([
            audio.spectrum[lo:max(hi, lo + 1)].mean() for lo, hi in zip(edges[:-1], edges[1:])
        ])
        target = np.clip(levels * 40, 0, 1)
        # Jump up instantly, fall back slowly.
        self.heights = np.maximum(target, self.heights - dt * 1.5)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 15))
        bar_width = self.width / BAR_COUNT
        for i, level in enumerate(self.heights):
            h = int(level * self.height * 0.9)
            color = pygame.Color(0)
            color.hsva = (200 + 140 * i / BAR_COUNT, 70, 100, 100)
            rect = pygame.Rect(int(i * bar_width) + 2, self.height - h, int(bar_width) - 4, h)
            pygame.draw.rect(surface, color, rect)
