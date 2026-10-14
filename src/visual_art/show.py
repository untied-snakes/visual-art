"""The current visual, the shuffle and the crossfade. No window, no clock."""
import pygame

from visual_art.audio import AudioFrame
from visual_art.crossfade import Crossfade
from visual_art.setlist import Setlist
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
        setlist: Setlist | None = None,
    ) -> None:
        self.visuals = visuals
        self.width = width
        self.height = height
        self.seconds = seconds
        self.fade_seconds = fade
        # A setlist plays in order and only moves when told; otherwise shuffle.
        self.setlist = setlist
        self.order = setlist if setlist is not None else Shuffle(names, seed)
        self.current = self._make(self.order.next())
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
                self.fade.old.close()
                self.current = self.fade.new
                self.fade = None
        else:
            self.current.update(audio, dt)
            self.current.draw(surface)

    def skip(self) -> None:
        """Start a fade to the next visual now."""
        if len(self.order.names) > 1:
            self._fade_to(self.order.next())

    def back(self) -> None:
        """Fade back to the previous song's visual. Setlist only."""
        if self.setlist is not None and len(self.setlist.names) > 1:
            self._fade_to(self.setlist.previous())

    def jump(self, index: int) -> None:
        """Fade to song number index (0 = first). Setlist only."""
        if self.setlist is not None and index < len(self.setlist.names):
            self._fade_to(self.setlist.go_to(index))

    def _fade_to(self, name: str) -> None:
        if self.fade is not None:
            # Pressed again mid-fade: finish that fade at once and start the new one.
            self.fade.old.close()
            self.current = self.fade.new
        self.fade = Crossfade(self.current, self._make(name), self.fade_seconds)
        self.time_on_screen = 0.0

    def _make(self, name: str) -> Visual:
        # A fresh instance every time, so a visual always starts clean.
        return self.visuals[name](self.width, self.height)
