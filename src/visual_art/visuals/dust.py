"""Dust drifting through the last light, leaving soft trails.
Bass hits send gusts of wind through it; the highs make the motes glint."""
import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.visual import Visual

MOTES = 900


class DustVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.rng = np.random.default_rng(3)
        self.positions = self.rng.uniform((0, 0), (width, height), (MOTES, 2))
        self.sizes = self.rng.uniform(1, 3.5, MOTES)
        self.colors = [palette.ramp([palette.CLAY, palette.OCHRE, palette.SAND, palette.BONE], t)
                       for t in self.rng.uniform(0, 1, MOTES)]
        self.time = 0.0
        self.gust = 0.0
        self.glint = 0.0
        self.sky = palette.vertical_gradient(width, height, [palette.NIGHT, palette.INDIGO, palette.DUSK, palette.MAUVE])
        # The motes draw onto this and it fades a little each frame, which leaves trails.
        self.trails = pygame.Surface((width, height))
        self.trails.fill((0, 0, 0))

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt
        # Gusts come in fast and die away slowly.
        self.gust = max(audio.bass, self.gust - dt * 0.4)
        self.glint += (audio.highs - self.glint) * min(1.0, dt * 8)

        x, y = self.positions[:, 0], self.positions[:, 1]
        # A gentle swirling breeze that changes over time, plus the gust.
        angle = np.sin(x * 0.003 + self.time * 0.2) + np.cos(y * 0.004 - self.time * 0.15)
        speed = (15 + 160 * self.gust) * (0.5 + self.sizes / 3.5)
        self.positions[:, 0] += (np.cos(angle) * speed + 25 * self.gust * 3) * dt
        self.positions[:, 1] += np.sin(angle) * speed * 0.5 * dt
        self.positions %= (self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.sky, (0, 0))
        self.trails.fill((6, 6, 6), special_flags=pygame.BLEND_SUB)
        brightness = 0.35 + 0.65 * self.glint
        for (x, y), size, color in zip(self.positions, self.sizes, self.colors):
            dim = palette.mix((0, 0, 0), color, brightness * size / 3.5)
            pygame.draw.circle(self.trails, dim, (int(x), int(y)), int(size))
        surface.blit(self.trails, (0, 0), special_flags=pygame.BLEND_ADD)
