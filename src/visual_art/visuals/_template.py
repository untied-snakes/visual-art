"""
HOW TO MAKE A NEW VISUAL
  1. Copy this file:   cp _template.py my_thing.py
  2. Rename the class: TemplateVisual -> MyThingVisual
  3. Try it:           uv run visual-art play my_thing
It's automatically included in shuffle.

Audio values you can use in update():
  audio.volume  audio.bass  audio.mids  audio.highs   roughly 0 (silent) to 1 (loud)
  audio.spectrum   array of loudness per frequency, low -> high
  audio.samples    the raw waveform, floats -1..1
"""
import pygame

from visual_art.audio import AudioFrame
from visual_art.visual import Visual


class TemplateVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        # Set up anything you need to remember between frames.
        self.radius = 0.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        # React to the music. Multiply any movement by dt.
        self.radius = 50 + audio.bass * 400

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))  # always clear first
        center = (self.width // 2, self.height // 2)
        pygame.draw.circle(surface, (255, 255, 255), center, int(self.radius))
