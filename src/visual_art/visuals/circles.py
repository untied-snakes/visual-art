"""Rings rippling out from the centre, like sound across a canyon floor.
The mids push the rings apart; the highs speed up the colour drift."""
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.visual import Visual

RING_COLORS = [palette.OCHRE, palette.CLAY, palette.RUST, palette.MAUVE, palette.DUSK, palette.TURQUOISE, palette.SAND]


class CirclesVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.radius = 0.0  # the rings flow outward from here
        self.hue = 0.0
        self.space = 20.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.hue = (self.hue + dt * (0.02 + 0.15 * audio.highs)) % 1.0
        target = 30 + audio.mids * 50
        self.space += (target - self.space) * min(1.0, dt * 3)
        self.radius = (self.radius + dt * (15 + 60 * audio.bass)) % self.space

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.NIGHT)  # always clear first
        center = (self.width // 2, self.height // 2)
        for i in range(30):
            color = palette.cycle(RING_COLORS, self.hue + i / 30)
            # Rings fade into the dark as they spread out.
            color = palette.mix(color, palette.NIGHT, i / 30)
            pygame.draw.circle(surface, color, center, int(self.radius + i * self.space), width=3)
