"""The sound as a mountain range. Every moment's spectrum becomes a ridge that
drifts back towards the horizon, so the last few seconds of music pile up as hills."""
from collections import deque

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.visual import Visual

RIDGES = 40
POINTS = 120
SECONDS_PER_RIDGE = 0.18


class RidgelineVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.ridges = deque([np.zeros(POINTS)] * RIDGES, maxlen=RIDGES)
        self.current = np.zeros(POINTS)
        self.timer = 0.0
        self.sky = palette.vertical_gradient(width, height, [palette.NIGHT, palette.INDIGO, palette.DUSK, palette.CLAY])
        self.xs = np.linspace(width * 0.1, width * 0.9, POINTS)

    def update(self, audio: AudioFrame, dt: float) -> None:
        # Group the spectrum into points, mirrored so the bass makes peaks in the middle.
        half = POINTS // 2
        edges = np.geomspace(2, len(audio.spectrum) / 2, half + 1).astype(int)
        levels = np.array([audio.spectrum[lo:max(hi, lo + 1)].mean() for lo, hi in zip(edges[:-1], edges[1:])])
        levels = np.clip(levels * 40, 0, 1)
        shape = np.concatenate([levels[::-1], levels])
        # Keep the loudest moment since the last ridge was laid down.
        self.current = np.maximum(self.current, shape)
        self.timer += dt
        if self.timer >= SECONDS_PER_RIDGE:
            self.timer -= SECONDS_PER_RIDGE
            self.ridges.appendleft(self.current)
            self.current = np.zeros(POINTS)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.sky, (0, 0))
        # Taper the ends of each ridge down to the ground.
        taper = np.sin(np.linspace(0, np.pi, POINTS)) ** 1.5
        # Oldest ridges at the back (high up the screen, small), newest at the front.
        for i in reversed(range(RIDGES)):
            depth = i / (RIDGES - 1)  # 0 = front, 1 = horizon
            base_y = self.height * (0.92 - 0.5 * depth ** 0.8)
            scale = 1 - 0.55 * depth
            xs = self.width / 2 + (self.xs - self.width / 2) * scale
            ys = base_y - self.ridges[i] * taper * self.height * 0.35 * scale
            points = list(zip(xs, ys))
            fill = palette.mix(palette.NIGHT, palette.INDIGO, depth * 0.8)
            line = palette.ramp([palette.SAND, palette.OCHRE, palette.CLAY, palette.MAUVE, palette.DUSK], depth)
            pygame.draw.polygon(surface, fill, points + [(xs[-1], base_y + 4), (xs[0], base_y + 4)])
            pygame.draw.lines(surface, line, False, points, 2)
