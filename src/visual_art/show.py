"""The current visual, the shuffle and the crossfade. No window, no clock."""
import pygame

from visual_art.audio import AudioFrame
from visual_art.crossfade import Crossfade
from visual_art.shuffle import Shuffle
from visual_art.visual import Visual


class Show:
    def __init__(
        self,
        visuals: dict[str, type[Visual]],
        width: int,
        height: int,
        names: list[str],
        seconds: float | None = None,
        fade: float = 4.0,
        seed=None,
    ) -> None:
        self.visuals = visuals
        self.width = width
        self.height = height
        self.seconds = seconds
        self.fade_seconds = fade
        self.shuffle = Shuffle(names, seed)
        self.current = self._make(self.shuffle.next())
        self.fade: Crossfade | None = None
        self.time_on_screen = 0.0
        # Off-screen surfaces the crossfade draws each visual onto.
        self.old_surface = pygame.Surface((width, height))
        self.new_surface = pygame.Surface((width, height))

    def step(self, audio: AudioFrame, dt: float, surface: pygame.Surface) -> None:
        self.time_on_screen += dt
        if self.seconds is not None and self.fade is None and self.time_on_screen >= self.seconds:
            self.skip()

        if self.fade is not None:
            self.fade.update(audio, dt)
            self.fade.draw(surface, self.old_surface, self.new_surface)
            if self.fade.done:
                self.current = self.fade.new
                self.fade = None
        else:
            self.current.update(audio, dt)
            self.current.draw(surface)

    def skip(self) -> None:
        """Start a fade to the next visual now."""
        if self.fade is not None or len(self.shuffle.names) < 2:
            return
        self.fade = Crossfade(self.current, self._make(self.shuffle.next()), self.fade_seconds)
        self.time_on_screen = 0.0

    def _make(self, name: str) -> Visual:
        # A fresh instance every time, so a visual always starts clean.
        return self.visuals[name](self.width, self.height)
