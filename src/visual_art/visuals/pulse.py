"""A circle that swells with the bass and slowly shifts colour."""
import pygame

from visual_art.audio import AudioFrame
from visual_art.visual import Visual


class PulseVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self.radius = 0.0
        self.hue = 0.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        target = min(self.width, self.height) * (0.1 + 0.4 * audio.bass)
        # Ease toward the target so the pulse is smooth, not jittery.
        self.radius += (target - self.radius) * min(1.0, dt * 12)
        self.hue = (self.hue + dt * (20 + 200 * audio.highs)) % 360

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        color = pygame.Color(0)
        color.hsva = (self.hue, 80, 100, 100)
        center = (self.width // 2, self.height // 2)
        pygame.draw.circle(surface, color, center, int(self.radius))
