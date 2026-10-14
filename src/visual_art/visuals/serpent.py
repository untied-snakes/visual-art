"""Two banded snakes winding around each other across the dark sand.
They move faster when the band gets louder, and swell with the bass."""
import math

import pygame

from visual_art import palette
from visual_art.audio import AudioFrame
from visual_art.visual import Visual

SEGMENTS = 110
# Each snake: its band colours, and an offset so the two take different paths.
SNAKES = [
    ([palette.RUST, palette.SAND, palette.NIGHT, palette.SAND], 0.0),
    ([palette.TURQUOISE, palette.BONE, palette.DUSK, palette.BONE], 2.4),
]


class SerpentVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.time = 0.0
        self.slither = 0.0
        self.thickness = 1.0
        # The snakes leave faint tracks in the sand that slowly fade.
        self.tracks = pygame.Surface((width, height))
        self.tracks.fill((0, 0, 0))
        self.floor = palette.vertical_gradient(width, height, [palette.NIGHT, (26, 16, 30), (44, 26, 34)])

    def update(self, audio: AudioFrame, dt: float) -> None:
        self.time += dt * (0.25 + 0.5 * audio.volume)
        self.slither += dt * (2 + 4 * audio.mids)
        self.thickness += (1 + 1.2 * audio.bass - self.thickness) * min(1.0, dt * 5)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.floor, (0, 0))
        self.tracks.fill((2, 2, 2), special_flags=pygame.BLEND_SUB)
        for colors, offset in SNAKES:
            head = self._body_point(0, offset)
            pygame.draw.circle(self.tracks, (60, 36, 30), (int(head[0]), int(head[1])), 6)
        surface.blit(self.tracks, (0, 0), special_flags=pygame.BLEND_ADD)

        for colors, offset in SNAKES:
            self._draw_snake(surface, colors, offset)

    def _path(self, t: float, offset: float) -> tuple[float, float]:
        """Where a snake's head is at time t: a slow wandering loop."""
        w, h = self.width, self.height
        x = w / 2 + w * 0.32 * math.sin(t * 0.7 + offset) + w * 0.08 * math.sin(t * 1.9 + offset * 2)
        y = h / 2 + h * 0.30 * math.sin(t * 0.9 + offset * 1.3) + h * 0.08 * math.cos(t * 2.3 + offset)
        return x, y

    def _body_point(self, i: int, offset: float) -> tuple[float, float]:
        """Segment i follows the path the head took a moment ago, swaying side to side."""
        x, y = self._path(self.time - i * 0.03, offset)
        nx, ny = self._path(self.time - i * 0.03 - 0.01, offset)
        dx, dy = x - nx, y - ny
        length = math.hypot(dx, dy) or 1.0
        sway = math.sin(i * 0.25 - self.slither) * 18 * (i / SEGMENTS)
        return x - dy / length * sway, y + dx / length * sway

    def _draw_snake(self, surface: pygame.Surface, colors: list, offset: float) -> None:
        points = [self._body_point(i, offset) for i in range(SEGMENTS)]
        radii = [(6 + 26 * (1 - i / SEGMENTS) ** 0.6) * self.thickness for i in range(SEGMENTS)]
        # A dark outline under the whole body first, then the bands on top,
        # tail first so the head ends up on top.
        for (x, y), radius in zip(points, radii):
            pygame.draw.circle(surface, palette.NIGHT, (int(x), int(y)), int(radius) + 3)
        for i in reversed(range(SEGMENTS)):
            x, y = points[i]
            pygame.draw.circle(surface, colors[(i // 8) % len(colors)], (int(x), int(y)), int(radii[i]))
        # Two eyes on the head, set either side of the direction it's moving.
        (hx, hy), (nx, ny) = points[0], points[3]
        dx, dy = hx - nx, hy - ny
        length = math.hypot(dx, dy) or 1.0
        dx, dy = dx / length, dy / length
        size = 30 * self.thickness
        for side in (-1, 1):
            ex = hx + dx * size * 0.4 - dy * side * size * 0.45
            ey = hy + dy * size * 0.4 + dx * side * size * 0.45
            pygame.draw.circle(surface, palette.OCHRE, (int(ex), int(ey)), max(3, int(size * 0.18)))
            pygame.draw.circle(surface, palette.NIGHT, (int(ex), int(ey)), max(1, int(size * 0.07)))
