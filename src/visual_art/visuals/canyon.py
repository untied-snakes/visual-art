"""Looking up a slot canyon: curved bands of sandstone that slowly flow and bend.
The mids bend the rock more; the bass brightens the light falling from above.
Pictures in media/canyon/ are pressed into the rock as texture."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

BANDS = 26
POINTS = 90


class CanyonVisual(Visual):
    media_use = "texture on the rock walls"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.time = 0.0
        self.bend = 0.3
        self.light = 0.0
        self.ys = np.linspace(-0.1, 1.1, POINTS) * height
        self.sunbeam = palette.glow(int(height * 0.7), palette.SAND, 0.7)
        # Multiplied over the bands, so it only darkens: dark parts of the picture
        # become grooves in the rock, bright parts leave the rock as it is.
        self.media = Media("canyon", (int(width * 1.25), int(height * 1.25)), tint=[(110, 80, 80), palette.SAND, palette.BONE, (255, 255, 255)],
                           speed=0.5)

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt * (0.15 + 0.3 * audio.volume)
        self.bend += (0.3 + 0.9 * audio.mids - self.bend) * min(1.0, dt * 2)
        self.light += (audio.bass - self.light) * min(1.0, dt * 4)
        self.media.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.NIGHT)
        # Each band is the gap between two wavy vertical lines. Draw from the
        # outside in, so the walls close over each other towards the centre.
        lines = [self._wall_line(b) for b in range(BANDS + 1)]
        for b in range(BANDS):
            left = list(zip(lines[b], self.ys))
            right = list(zip(lines[b + 1], self.ys))
            color = palette.cycle(palette.STRATA, b / BANDS * 2 + self.time * 0.05)
            # Bands near the centre are lit; the outer walls fall into shadow.
            shade = abs(b / BANDS - 0.5) * 2
            color = palette.mix(color, palette.NIGHT, 0.15 + 0.7 * shade - 0.2 * self.light)
            pygame.draw.polygon(surface, color, left + right[::-1])

        picture = self.media.frame()
        if picture is not None:
            # The texture slides around with the flow of the rock.
            spare_x, spare_y = picture.get_width() - self.width, picture.get_height() - self.height
            x = -spare_x * (0.5 + 0.5 * math.sin(self.time * 0.9))
            y = -spare_y * (0.5 + 0.5 * math.cos(self.time * 0.7))
            surface.blit(picture, (x, y), special_flags=pygame.BLEND_MULT)

        beam = palette.dimmed(self.sunbeam, 0.2 + 0.8 * self.light)
        surface.blit(beam, beam.get_rect(center=(self.width // 2, 0)), special_flags=pygame.BLEND_ADD)

    def close(self) -> None:
        self.media.close()

    def _wall_line(self, b: int) -> np.ndarray:
        """x positions of the edge between band b-1 and band b, top to bottom."""
        across = b / BANDS  # 0 = left edge of screen, 1 = right
        # Squeeze the bands together towards the centre, like walls narrowing.
        x = 0.5 + np.sign(across - 0.5) * np.abs(across - 0.5) ** 1.4 * 1.3
        y = self.ys / self.height
        wobble = (
            np.sin(y * 5 + self.time * 2 + b * 0.3) * 0.05
            + np.sin(y * 11 - self.time * 1.3 + b * 0.7) * 0.02
        ) * self.bend * (1 - abs(across - 0.5))
        return (x + wobble) * self.width
