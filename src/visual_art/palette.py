"""Shared colours for the show: slow-burning cosmic desert psych.

Every visual picks from these so the whole set feels like one place:
a canyon at dusk, with the stars coming out.
"""
import numpy as np
import pygame

NIGHT = (10, 7, 18)         # the sky after the sun has gone
INDIGO = (34, 24, 58)
DUSK = (78, 40, 84)         # the purple band above the horizon
MAUVE = (140, 70, 100)
RUST = (176, 72, 40)
CLAY = (204, 104, 62)
OCHRE = (224, 154, 66)
SAND = (236, 206, 158)
SAGE = (128, 148, 112)
TURQUOISE = (64, 152, 150)
BONE = (246, 236, 216)      # starlight, bleached bone

# The sky from the horizon up.
DUSK_SKY = [OCHRE, CLAY, MAUVE, DUSK, INDIGO, NIGHT]
# Dark to bright, for things that glow.
EMBER = [NIGHT, DUSK, RUST, CLAY, OCHRE, SAND, BONE]
# Rock layers in a canyon wall.
STRATA = [RUST, CLAY, OCHRE, SAND, CLAY, MAUVE, RUST, DUSK]


def mix(a, b, t: float) -> tuple[int, int, int]:
    """Blend colour a into colour b. t=0 is a, t=1 is b."""
    t = min(max(t, 0.0), 1.0)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(colors: list, t: float) -> tuple[int, int, int]:
    """Pick a colour along a list of colours. t=0 is the first, t=1 the last."""
    t = min(max(t, 0.0), 1.0) * (len(colors) - 1)
    i = min(int(t), len(colors) - 2)
    return mix(colors[i], colors[i + 1], t - i)


def cycle(colors: list, t: float) -> tuple[int, int, int]:
    """Like ramp, but loops back to the first colour, so t can grow forever."""
    t = (t % 1.0) * len(colors)
    i = int(t) % len(colors)
    return mix(colors[i], colors[(i + 1) % len(colors)], t - int(t))


def vertical_gradient(width: int, height: int, colors: list) -> pygame.Surface:
    """A surface that fades through colors from top to bottom."""
    column = np.array([ramp(colors, y / max(height - 1, 1)) for y in range(height)], dtype=np.uint8)
    return pygame.surfarray.make_surface(np.broadcast_to(column, (width, height, 3)).copy())


def glow(radius: int, color, strength: float = 1.0) -> pygame.Surface:
    """A soft round light. Blit it with special_flags=pygame.BLEND_ADD."""
    size = radius * 2
    y, x = np.mgrid[0:size, 0:size]
    distance = np.hypot(x - radius + 0.5, y - radius + 0.5) / radius
    falloff = np.clip(1 - distance, 0, 1) ** 2 * strength
    pixels = np.clip(falloff[..., None] * np.array(color), 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(pixels)


def dimmed(surface: pygame.Surface, amount: float) -> pygame.Surface:
    """A darker copy of surface. amount=1 keeps it as is, 0 makes it black.
    Use this on glows: BLEND_ADD ignores set_alpha()."""
    v = int(255 * min(max(amount, 0.0), 1.0))
    copy = surface.copy()
    copy.fill((v, v, v), special_flags=pygame.BLEND_MULT)
    return copy
