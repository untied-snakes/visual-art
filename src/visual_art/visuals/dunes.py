"""Layers of dunes and mesas at dusk, under stars and the odd shooting star.
The dunes heave with the music: far ridges with the highs, near ones with the bass.
The bass makes the last light on the horizon flare, loud passages make everything
drift faster, and sudden hits send a shooting star across the sky.
Pictures in media/dunes/ rise like mirages between the ridges and drift with them."""
import math

import numpy as np
import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.media import Media
from visual_art.visual import Visual

LAYERS = 5
STAR_COUNT = 220
# A mirage floats just in front of each of these ridges (0 = the farthest),
# so the ridges in front of it hide its lower edge.
MIRAGE_LAYERS = [0, 1, 2, 3]
RIDGE_COLORS = [palette.MAUVE, palette.DUSK, palette.INDIGO, (24, 14, 30), palette.NIGHT]


class DunesVisual(Visual):
    media_use = "mirages rising between the dunes"

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.rng = np.random.default_rng(7)
        self.sky = palette.vertical_gradient(width, height, list(reversed(palette.DUSK_SKY)))
        self.stars = np.column_stack([self.rng.uniform(0, width, STAR_COUNT), self.rng.uniform(0, height * 0.6, STAR_COUNT)])
        self.star_phase = self.rng.uniform(0, 2 * np.pi, STAR_COUNT)
        # Each layer is a ridge made of a few sine waves with random shapes.
        self.waves = self.rng.uniform(0.5, 1.0, (LAYERS, 3, 3))
        self.time = 0.0
        self.drift = 0.0          # how far the ridges have slid; runs faster when it's loud
        self.heave = np.zeros(LAYERS)  # how much the music is lifting each ridge
        self.glow = 0.0
        self.twinkle = 0.0
        self.loudness = 0.0       # slow average of the volume, to spot sudden hits
        self.meteor_wait = 0.0
        self.meteors = []         # [x, y, x speed, y speed, life left 1 -> 0]
        self.horizon_glow = palette.glow(int(width * 0.45), palette.CLAY, 0.8)
        self.xs = np.linspace(0, width, 160)

        self.mirages = []
        for n, layer in enumerate(MIRAGE_LAYERS):
            depth = layer / (LAYERS - 1)
            size = (int(height * (0.33 + 0.33 * depth) * 1.5), int(height * (0.33 + 0.33 * depth)))
            media = Media("dunes", size, start=n, seconds_each=25 + 7 * n, speed=0.5,
                          tint=[palette.NIGHT, palette.DUSK, palette.MAUVE, palette.CLAY, palette.OCHRE, palette.SAND],
                          tint_strength=0.85)
            # Spread them out across the screen to start with.
            self.mirages.append((layer, media, _soft_oval(size), n * 0.29 * (width + size[0])))

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt
        self.drift += dt * (1 + 3 * audio.volume)
        # Far ridges move with the highs, the middle with the mids, the near ones with the bass.
        # They rise quickly and settle slowly, like sand being lifted and falling back.
        target = np.array([audio.highs, audio.mids, audio.mids, audio.bass, audio.bass])
        rate = np.where(target > self.heave, 8.0, 1.5)
        self.heave += (target - self.heave) * np.minimum(1.0, dt * rate)
        self.glow += (audio.bass - self.glow) * min(1.0, dt * 6)
        self.twinkle += (audio.highs - self.twinkle) * min(1.0, dt * 6)

        # A sudden jump in loudness sends a shooting star.
        self.meteor_wait -= dt
        if audio.volume - self.loudness > 0.15 and self.meteor_wait <= 0:
            self.meteors.append([self.rng.uniform(self.width * 0.3, self.width * 1.1), self.rng.uniform(0, self.height * 0.25),
                                 self.rng.uniform(-900, -500), self.rng.uniform(150, 350), 1.0])
            self.meteor_wait = 0.6
        self.loudness += (audio.volume - self.loudness) * min(1.0, dt * 1.5)
        for meteor in self.meteors:
            meteor[0] += meteor[2] * dt
            meteor[1] += meteor[3] * dt
            meteor[4] -= dt * 1.4
        self.meteors = [m for m in self.meteors if m[4] > 0]

        for _, media, _, _ in self.mirages:
            media.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.sky, (0, 0))
        self._draw_stars(surface)
        self._draw_meteors(surface)

        horizon = self.height * 0.55
        glow = palette.dimmed(self.horizon_glow, 0.2 + 0.8 * self.glow)
        surface.blit(glow, glow.get_rect(center=(self.width // 2, int(horizon))), special_flags=pygame.BLEND_ADD)

        for layer in range(LAYERS):
            depth = layer / (LAYERS - 1)  # 0 = far away, 1 = close
            ys = self._ridge(layer, horizon)
            points = list(zip(self.xs, ys)) + [(self.width, self.height), (0, self.height)]
            color = palette.ramp(RIDGE_COLORS, depth)
            pygame.draw.polygon(surface, color, points)
            # A rim of last light along the far ridges, brighter as the music lifts them.
            if depth < 0.8:
                rim = palette.mix(palette.OCHRE, color, depth + 0.5 * (1 - self.heave[layer]) - 0.2 * self.glow)
                pygame.draw.lines(surface, rim, False, list(zip(self.xs, ys)), 2)
            for mirage in self.mirages:
                if mirage[0] == layer:
                    self._draw_mirage(surface, mirage, ys)

    def close(self) -> None:
        for _, media, _, _ in self.mirages:
            media.close()

    def _ridge(self, layer: int, horizon: float) -> np.ndarray:
        """Heights of one ridge across the screen."""
        depth = layer / (LAYERS - 1)
        base = horizon + depth * self.height * 0.32 - self.heave[layer] * (15 + 25 * depth)
        speed = 6 + 30 * depth  # closer layers drift faster (parallax)
        height = (20 + 50 * depth) * (1 + 1.5 * self.heave[layer])
        ys = np.full_like(self.xs, base)
        for frequency, amplitude, phase in self.waves[layer]:
            x = (self.xs + self.drift * speed) / self.width
            ys -= np.sin(x * frequency * (2 + 4 * depth) * np.pi + phase * 6) * amplitude * height
        return ys

    def _draw_mirage(self, surface: pygame.Surface, mirage, ridge: np.ndarray) -> None:
        layer, media, oval, start = mirage
        picture = media.frame()
        if picture is None:
            return
        depth = layer / (LAYERS - 1)
        w, h = oval.get_size()
        # Slide left with this ridge, a bit faster than it, and come back round.
        x = self.width - (start + self.drift * (20 + 50 * depth)) % (self.width + w)
        # Rest on the ridge, bob up and down slowly, and rise with the music.
        column = int(np.clip((x + w / 2) / self.width * (len(self.xs) - 1), 0, len(self.xs) - 1))
        bob = math.sin(self.time * 0.5 + layer * 1.7)
        y = ridge[column] - h * (0.55 + 0.12 * bob + 0.25 * self.heave[layer])
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(picture, (0, 0))
        sprite.blit(oval, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Far mirages are fainter, like they're seen through heat haze.
        sprite.set_alpha(int(min(255, 110 + 90 * depth + 60 * self.heave[layer])))
        surface.blit(sprite, (x, y))

    def _draw_stars(self, surface: pygame.Surface) -> None:
        brightness = 0.5 + 0.5 * np.sin(self.time * 1.5 + self.star_phase)
        brightness = brightness * (0.4 + 0.6 * self.twinkle)
        for (x, y), b in zip(self.stars, brightness):
            # Stars nearer the horizon are hidden by the last of the daylight.
            b *= 1 - y / (self.height * 0.6)
            pygame.draw.circle(surface, palette.mix(palette.INDIGO, palette.BONE, b), (int(x), int(y)), 1 + (b > 0.6))

    def _draw_meteors(self, surface: pygame.Surface) -> None:
        for x, y, vx, vy, life in self.meteors:
            tail = (x - vx * 0.15, y - vy * 0.15)
            pygame.draw.line(surface, palette.mix(palette.INDIGO, palette.SAND, life * 0.6), tail, (x, y), 2)
            pygame.draw.circle(surface, palette.mix(palette.INDIGO, palette.BONE, life), (int(x), int(y)), 2)


def _soft_oval(size: tuple[int, int]) -> pygame.Surface:
    """White, with alpha that fades out towards the edges of an oval. Multiply a picture
    by it (BLEND_RGBA_MULT) to give the picture soft, dissolving edges."""
    w, h = size
    x = (np.arange(w)[:, None] - w / 2) / (w / 2)
    y = (np.arange(h)[None, :] - h / 2) / (h / 2)
    alpha = (np.clip((1 - np.hypot(x, y)) / 0.6, 0, 1) ** 1.5 * 255).astype(np.uint8)
    oval = pygame.Surface(size, pygame.SRCALPHA)
    oval.fill((255, 255, 255, 255))
    pygame.surfarray.pixels_alpha(oval)[:] = alpha
    return oval
