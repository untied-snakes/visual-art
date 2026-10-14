"""A low sun that swells with the bass and slowly burns through dusk colours.
Pictures in media/pulse/ show inside the sun, recoloured to match it."""
import math

import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

SUN_COLORS = [palette.OCHRE, palette.CLAY, palette.RUST, palette.MAUVE, palette.CLAY]


class PulseVisual(Visual):
    media_use = "picture inside the sun"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.radius = 0.0
        self.hue = 0.0  # how far along SUN_COLORS we are; loops
        self.time = 0.0
        self.sky = palette.vertical_gradient(width, height, [palette.NIGHT, palette.INDIGO, palette.DUSK])
        self.halo = palette.glow(int(min(width, height) * 0.6), palette.CLAY, 0.8)
        # Bigger than the sun ever gets, so the picture can drift around inside it.
        self.media = Media("pulse", (1000, 1000), tint=[palette.RUST, palette.CLAY, palette.OCHRE, palette.SAND, palette.BONE],
                           tint_strength=0.85, speed=0.5)

    def update(self, audio: AudioFrame, dt: float) -> None:
        target = min(self.width, self.height) * (0.12 + 0.3 * audio.bass)
        # Ease toward the target so the pulse is smooth, not jittery.
        self.radius += (target - self.radius) * min(1.0, dt * 4)
        self.hue = (self.hue + dt * (0.01 + 0.08 * audio.highs)) % 1.0
        self.media.update(dt)
        self.time += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.sky, (0, 0))
        center = (self.width // 2, int(self.height * 0.55))
        # The halo grows a little with the sun.
        size = int(self.halo.get_width() * (0.7 + self.radius / self.height))
        halo = pygame.transform.smoothscale(self.halo, (size, size))
        surface.blit(halo, halo.get_rect(center=center), special_flags=pygame.BLEND_ADD)
        color = palette.cycle(SUN_COLORS, self.hue)
        pygame.draw.circle(surface, color, center, int(self.radius))
        inner = int(self.radius * 0.8)
        picture = self.media.frame()
        if picture is None or inner < 2:
            pygame.draw.circle(surface, palette.mix(color, palette.SAND, 0.5), center, inner)
        else:
            surface.blit(self._disc(picture, inner), (center[0] - inner, center[1] - inner))

    def close(self) -> None:
        self.media.close()

    def _disc(self, picture: pygame.Surface, radius: int) -> pygame.Surface:
        """The picture, shrunk to the sun's size and cut into a circle."""
        size = radius * 2
        # Show a window of the picture that wanders across it.
        window = int(picture.get_width() * 0.6)
        spare = picture.get_width() - window
        left = int(spare * (0.5 + 0.5 * math.sin(self.time * 0.15)))
        top = int(spare * (0.5 + 0.5 * math.cos(self.time * 0.11)))
        crop = picture.subsurface((left, top, window, window))
        disc = pygame.Surface((size, size), pygame.SRCALPHA)
        disc.blit(pygame.transform.smoothscale(crop, (size, size)), (0, 0))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        disc.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return disc
