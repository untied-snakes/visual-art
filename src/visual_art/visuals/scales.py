"""Lizard skin: a field of scales that light up as the sound ripples across.
Each column of scales follows its own slice of the spectrum, bass on the left.
Pictures in media/scales/ turn the skin into a mosaic that the music lights up."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

SCALE_SIZE = 46  # pixels from a scale's centre to its corner
SKIN = [palette.DUSK, palette.RUST, palette.CLAY, palette.OCHRE, palette.SAND]
MOSAIC_SHRINK = 8  # the picture is loaded at 1/8 size; each scale takes one pixel's colour


class ScalesVisual(Visual):
    media_use = "mosaic of the picture, lit by the music"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        # Centres of a hexagon grid that covers the screen.
        step_x = SCALE_SIZE * math.sqrt(3)
        step_y = SCALE_SIZE * 1.5
        self.cells = []
        for row in range(int(height / step_y) + 2):
            for col in range(int(width / step_x) + 2):
                x = col * step_x + (step_x / 2 if row % 2 else 0)
                self.cells.append((x, row * step_y))
        self.columns = int(width / step_x) + 2
        self.hexagons = [self._hexagon(x, y, SCALE_SIZE - 3) for x, y in self.cells]
        self.levels = np.zeros(self.columns)
        self.time = 0.0
        self.pattern = 0.0
        # The picture is bigger than the screen so it can pan slowly under the scales.
        self.media = Media("scales", (width * 3 // 2 // MOSAIC_SHRINK, height * 3 // 2 // MOSAIC_SHRINK),
                           tint=SKIN, tint_strength=0.8)
        # Which pixel of the small picture each scale takes its colour from, before panning.
        self.sample_x = np.array([min(int(x / MOSAIC_SHRINK), width // MOSAIC_SHRINK - 1) for x, _ in self.cells])
        self.sample_y = np.array([min(int(y / MOSAIC_SHRINK), height // MOSAIC_SHRINK - 1) for _, y in self.cells])

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt
        self.pattern += dt * (0.1 + 0.4 * audio.mids)
        self.media.update(dt)
        edges = np.geomspace(2, len(audio.spectrum), self.columns + 1).astype(int)
        target = np.array([audio.spectrum[lo:max(hi, lo + 1)].mean() for lo, hi in zip(edges[:-1], edges[1:])])
        target = np.clip(target * 50, 0, 1)
        # Light up fast, fade slowly.
        self.levels = np.maximum(target, self.levels - dt * 0.8)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.NIGHT)
        step_x = SCALE_SIZE * math.sqrt(3)
        picture = self.media.frame()
        photo = None
        if picture is not None:
            spare_x = picture.get_width() - self.width // MOSAIC_SHRINK
            spare_y = picture.get_height() - self.height // MOSAIC_SHRINK
            pan_x = int(spare_x * (0.5 + 0.5 * math.sin(self.pattern * 0.7)))
            pan_y = int(spare_y * (0.5 + 0.5 * math.cos(self.pattern * 0.5)))
            photo = pygame.surfarray.array3d(picture)[self.sample_x + pan_x, self.sample_y + pan_y].tolist()
        for i, ((x, y), hexagon) in enumerate(zip(self.cells, self.hexagons)):
            column = min(int(x / step_x), self.columns - 1)
            # A slow ripple of colour runs across the skin like a lizard changing colour.
            ripple = 0.5 + 0.5 * math.sin(x * 0.004 + y * 0.006 - self.pattern * 3)
            bright = palette.ramp(SKIN[2:], ripple)
            base = palette.ramp(SKIN[:3], ripple)
            if photo is not None:
                bright = base = palette.mix(photo[i], bright, 0.25)
            color = palette.mix(palette.mix(base, palette.NIGHT, 0.5), bright, self.levels[column])
            pygame.draw.polygon(surface, color, hexagon)
            # A bright edge, like light catching the rim of each scale.
            pygame.draw.polygon(surface, palette.mix(color, palette.SAND, 0.25), hexagon, 2)

    def close(self) -> None:
        self.media.close()

    def _hexagon(self, x: float, y: float, size: float) -> list[tuple[float, float]]:
        return [(x + size * math.cos(math.pi / 3 * i + math.pi / 6),
                 y + size * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
