"""Layers of dunes and mesas at dusk, under stars that flicker with the highs.
The bass makes the last light on the horizon glow brighter.
Pictures in media/dunes/ become the sky, recoloured to dusk and slowly drifting."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

LAYERS = 5
STAR_COUNT = 220


class DunesVisual(Visual):
    media_use = "sky behind the dunes, slowly drifting"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        rng = np.random.default_rng(7)
        self.sky = palette.vertical_gradient(width, height, list(reversed(palette.DUSK_SKY)))
        self.stars = np.column_stack([rng.uniform(0, width, STAR_COUNT), rng.uniform(0, height * 0.6, STAR_COUNT)])
        self.star_phase = rng.uniform(0, 2 * np.pi, STAR_COUNT)
        # Each layer is a ridge made of a few sine waves with random shapes.
        self.waves = rng.uniform(0.5, 1.0, (LAYERS, 3, 3))
        self.time = 0.0
        self.glow = 0.0
        self.twinkle = 0.0
        self.horizon_glow = palette.glow(int(width * 0.45), palette.CLAY, 0.6)
        self.xs = np.linspace(0, width, 160)
        # A little bigger than the screen, so there's room to drift.
        self.media = Media("dunes", (int(width * 1.1), int(height * 1.1)),
                           tint=[palette.NIGHT, palette.INDIGO, palette.DUSK, palette.MAUVE, palette.CLAY, palette.OCHRE],
                           tint_strength=0.9, speed=0.5)

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt
        self.glow += (audio.bass - self.glow) * min(1.0, dt * 3)
        self.twinkle += (audio.highs - self.twinkle) * min(1.0, dt * 6)
        self.media.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        picture = self.media.frame()
        if picture is None:
            surface.blit(self.sky, (0, 0))
        else:
            spare_x, spare_y = picture.get_width() - self.width, picture.get_height() - self.height
            drift_x = spare_x * (0.5 + 0.5 * math.sin(self.time * 0.03))
            drift_y = spare_y * (0.5 + 0.5 * math.cos(self.time * 0.04))
            surface.blit(picture, (-drift_x, -drift_y))
        self._draw_stars(surface)

        horizon = self.height * 0.55
        glow = palette.dimmed(self.horizon_glow, 0.3 + 0.7 * self.glow)
        surface.blit(glow, glow.get_rect(center=(self.width // 2, int(horizon))), special_flags=pygame.BLEND_ADD)

        for layer in range(LAYERS):
            depth = layer / (LAYERS - 1)  # 0 = far away, 1 = close
            base = horizon + depth * self.height * 0.32
            speed = 6 + 30 * depth  # closer layers drift faster (parallax)
            ys = np.full_like(self.xs, base)
            for frequency, amplitude, phase in self.waves[layer]:
                x = (self.xs + self.time * speed) / self.width
                ys -= np.sin(x * frequency * (2 + 4 * depth) * np.pi + phase * 6) * amplitude * (20 + 50 * depth)
            points = list(zip(self.xs, ys)) + [(self.width, self.height), (0, self.height)]
            color = palette.ramp([palette.MAUVE, palette.DUSK, palette.INDIGO, (24, 14, 30), palette.NIGHT], depth)
            pygame.draw.polygon(surface, color, points)
            # A thin rim of last light along the far ridges.
            if depth < 0.6:
                rim = palette.mix(palette.CLAY, color, depth + 0.3 * (1 - self.glow))
                pygame.draw.lines(surface, rim, False, list(zip(self.xs, ys)), 2)

    def close(self) -> None:
        self.media.close()

    def _draw_stars(self, surface: pygame.Surface) -> None:
        brightness = 0.5 + 0.5 * np.sin(self.time * 1.5 + self.star_phase)
        brightness = brightness * (0.4 + 0.6 * self.twinkle)
        for (x, y), b in zip(self.stars, brightness):
            # Stars nearer the horizon are hidden by the last of the daylight.
            b *= 1 - y / (self.height * 0.6)
            pygame.draw.circle(surface, palette.mix(palette.INDIGO, palette.BONE, b), (int(x), int(y)), 1 + (b > 0.6))
