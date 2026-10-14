"""A vision-quest mandala: rings of petals turning against each other around an eye.
The pupil opens with the bass; each ring breathes with its own part of the spectrum.
Pictures in media/vision/ become a slowly turning kaleidoscope behind it all."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

# Each ring: how many petals, how far out (fraction of screen height), turning speed.
RINGS = [
    (8, 0.16, 0.10),
    (12, 0.24, -0.07),
    (16, 0.32, 0.05),
    (24, 0.40, -0.035),
    (32, 0.48, 0.025),
]
RING_COLORS = [palette.OCHRE, palette.CLAY, palette.MAUVE, palette.TURQUOISE, palette.DUSK]
# The kaleidoscope is worked out small and stretched to the screen, which also softens it.
KALEIDOSCOPE_SIZE = (480, 270)
MIRRORS = 12  # how many times the picture repeats around the circle


class VisionVisual(Visual):
    media_use = "kaleidoscope behind the mandala"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.turn = 0.0
        self.levels = np.zeros(len(RINGS))
        self.pupil = 0.3
        self.aura = palette.glow(int(height * 0.6), palette.MAUVE, 0.5)
        self.media = Media("vision", KALEIDOSCOPE_SIZE,
                           tint=[palette.NIGHT, palette.INDIGO, palette.DUSK, palette.MAUVE, palette.CLAY, palette.OCHRE, palette.SAND],
                           tint_strength=0.7, speed=0.5)
        # Distance and angle of every kaleidoscope pixel from the centre, worked out once.
        w, h = KALEIDOSCOPE_SIZE
        x = np.arange(w)[:, None] - w / 2
        y = (np.arange(h)[None, :] - h / 2) * np.ones((w, 1))
        self.distance = np.hypot(x, y)
        self.angle = np.arctan2(y, x)
        self.spin = 0.0
        self.zoom = 1.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.turn += dt * (0.6 + 1.2 * audio.volume)
        # Split the spectrum into one slice per ring, bass in the middle.
        edges = np.geomspace(2, len(audio.spectrum), len(RINGS) + 1).astype(int)
        target = np.array([audio.spectrum[lo:hi].mean() for lo, hi in zip(edges[:-1], edges[1:])])
        target = np.clip(target * 60, 0, 1)
        self.levels += (target - self.levels) * min(1.0, dt * 4)
        self.pupil += (0.25 + 0.6 * audio.bass - self.pupil) * min(1.0, dt * 5)
        self.spin += dt * (0.04 + 0.15 * audio.volume)
        self.zoom += (0.7 + 0.5 * audio.bass - self.zoom) * min(1.0, dt * 2)
        self.media.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = self.width / 2, self.height / 2
        picture = self.media.frame()
        if picture is None:
            surface.fill(palette.NIGHT)
            surface.blit(self.aura, self.aura.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_ADD)
        else:
            surface.blit(pygame.transform.smoothscale(self._kaleidoscope(picture), (self.width, self.height)), (0, 0))
        unit = self.height

        # Outer rings first so the inner ones overlap them.
        for (petals, reach, speed), color, level in reversed(list(zip(RINGS, RING_COLORS, self.levels))):
            length = unit * (0.07 + 0.05 * level)
            for p in range(petals):
                a = p * 2 * math.pi / petals + self.turn * speed
                self._petal(surface, cx, cy, a, unit * reach - length * 0.5, length, color, level)

        # The eye in the middle.
        eye = unit * 0.11
        pygame.draw.circle(surface, palette.SAND, (int(cx), int(cy)), int(eye))
        pygame.draw.circle(surface, palette.TURQUOISE, (int(cx), int(cy)), int(eye * 0.75))
        pygame.draw.circle(surface, palette.NIGHT, (int(cx), int(cy)), int(eye * 0.75 * self.pupil))

    def close(self) -> None:
        self.media.close()

    def _kaleidoscope(self, picture: pygame.Surface) -> pygame.Surface:
        """Cut a wedge from the picture and mirror it around the circle, like a kaleidoscope."""
        w, h = KALEIDOSCOPE_SIZE
        wedge = 2 * np.pi / MIRRORS
        # Fold every angle into one wedge, flipping every other one so the edges meet.
        a = (self.angle + self.spin) % wedge
        a = np.abs(a - wedge / 2) + self.spin * 0.3  # the wedge also slides across the picture
        r = self.distance * self.zoom
        x = (w / 2 + r * np.cos(a)).astype(int)
        y = (h / 2 + r * np.sin(a)).astype(int)
        # Past the picture's edge, bounce back into it instead of wrapping (no seams).
        x, y = x % (2 * w), y % (2 * h)
        x = np.where(x < w, x, 2 * w - 1 - x)
        y = np.where(y < h, y, 2 * h - 1 - y)
        return pygame.surfarray.make_surface(pygame.surfarray.array3d(picture)[x, y])

    def _petal(self, surface, cx, cy, angle, start, length, color, level) -> None:
        """A pointed leaf shape pointing away from the centre."""
        width = length * 0.28
        ux, uy = math.cos(angle), math.sin(angle)  # outward
        px, py = -uy, ux                           # sideways
        base = (cx + ux * start, cy + uy * start)
        tip = (cx + ux * (start + length), cy + uy * (start + length))
        mid = start + length * 0.45
        left = (cx + ux * mid + px * width, cy + uy * mid + py * width)
        right = (cx + ux * mid - px * width, cy + uy * mid - py * width)
        fill = palette.mix(palette.mix(color, palette.NIGHT, 0.45), color, level)
        pygame.draw.polygon(surface, fill, [base, left, tip, right])
        pygame.draw.polygon(surface, palette.mix(fill, palette.BONE, 0.35), [base, left, tip, right], 2)
