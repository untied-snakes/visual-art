"""A slow spiral galaxy turning over the desert.
The core glows with the bass; the arms turn faster when the band gets loud.
Pictures in media/cosmos/ become a dim nebula behind it, slowly drifting."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

STARS = 1400
ARMS = 3


class CosmosVisual(Visual):
    media_use = "nebula behind the galaxy, slowly drifting"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        rng = np.random.default_rng(11)
        # Each star sits at a distance from the centre, along one of the arms,
        # scattered a little so the arms look like clouds, not lines.
        self.distance = rng.uniform(0.03, 1, STARS) ** 1.2
        arm = rng.integers(0, ARMS, STARS)
        self.angle = arm * 2 * np.pi / ARMS + self.distance * 5.5 + rng.normal(0, 0.22, STARS) * (1.2 - self.distance)
        self.size = rng.uniform(1, 3.2, STARS)
        self.colors = [palette.ramp([palette.BONE, palette.SAND, palette.OCHRE, palette.MAUVE, palette.TURQUOISE], d)
                       for d in self.distance + rng.normal(0, 0.1, STARS)]
        self.rotation = 0.0
        self.core = 0.0
        self.shimmer = 0.0
        self.time = 0.0
        self.core_glow = palette.glow(int(height * 0.45), palette.OCHRE, 0.9)
        self.haze = palette.glow(int(width * 0.5), palette.DUSK, 0.6)
        # Recoloured dark, so the stars still stand out against it.
        self.media = Media("cosmos", (int(width * 1.3), int(height * 1.3)),
                           tint=[palette.NIGHT, palette.NIGHT, palette.NIGHT, palette.INDIGO, palette.DUSK], speed=0.5)

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt
        self.rotation += dt * (0.03 + 0.12 * audio.volume)
        self.core += (audio.bass - self.core) * min(1.0, dt * 4)
        self.shimmer += (audio.highs - self.shimmer) * min(1.0, dt * 8)
        self.media.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        picture = self.media.frame()
        if picture is None:
            surface.fill(palette.NIGHT)
        else:
            spare_x, spare_y = picture.get_width() - self.width, picture.get_height() - self.height
            # Wander around, and drift a little further while the band is loud.
            surface.blit(picture, (-spare_x * (0.5 + 0.5 * math.sin(self.rotation * 0.8 + self.time * 0.07)),
                                   -spare_y * (0.5 + 0.5 * math.cos(self.rotation * 0.6 + self.time * 0.05))))
        cx, cy = self.width / 2, self.height / 2
        surface.blit(self.haze, self.haze.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_ADD)

        # Inner stars orbit faster than outer ones, which slowly winds the arms.
        angle = self.angle + self.rotation * (1.5 - self.distance)
        radius = self.distance * self.height * 0.62
        xs = cx + np.cos(angle) * radius * 1.35  # tilted, so the disc looks oval
        ys = cy + np.sin(angle) * radius * 0.75
        twinkle = 0.55 + 0.45 * np.sin(self.time * 3 + self.angle * 40) * self.shimmer
        for x, y, size, color, t in zip(xs, ys, self.size, self.colors, twinkle):
            pygame.draw.circle(surface, palette.mix(palette.NIGHT, color, t), (int(x), int(y)), int(size))

        core = palette.dimmed(self.core_glow, 0.35 + 0.65 * self.core)
        surface.blit(core, core.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_ADD)

    def close(self) -> None:
        self.media.close()
