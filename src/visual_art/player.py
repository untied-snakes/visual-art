"""The live window: keyboard, clock and live audio, driving a Show."""
import pygame

from visual_art.audio import AudioInput
from visual_art.show import Show
from visual_art.terminal import TerminalInput

# Foot pedals and page-turner remotes send arrow or Page Up/Down keys, so all of these work.
NEXT_KEYS = (pygame.K_SPACE, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_PAGEDOWN, pygame.K_n, pygame.K_RETURN)
BACK_KEYS = (pygame.K_LEFT, pygame.K_UP, pygame.K_PAGEUP, pygame.K_BACKSPACE)
# 1-9 then 0 jump straight to songs 1-10.
NUMBER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0)


class Player:
    def __init__(self, show: Show, audio: AudioInput, fullscreen: bool = True, display: int = 0, fps: int = 60) -> None:
        self.show = show
        self.audio = audio
        self.fullscreen = fullscreen
        self.display = display  # which screen: 0 = main, 1 = projector, ... (see `visual-art displays`)
        self.fps = fps
        self.terminal = TerminalInput()

    def run(self) -> None:
        pygame.display.set_caption("visual-art")
        screen = self._open_window()
        clock = pygame.time.Clock()
        self.audio.start()
        self._print_help()
        self.terminal.start()
        try:
            running = True
            while running:
                dt = clock.tick(self.fps) / 1000
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_q):
                            running = False
                        elif event.key in NEXT_KEYS:
                            self._next()
                        elif event.key in BACK_KEYS:
                            self._back()
                        elif event.key in NUMBER_KEYS:
                            self._jump(NUMBER_KEYS.index(event.key))
                        elif event.key == pygame.K_f:
                            self.fullscreen = not self.fullscreen
                            screen = self._open_window()
                for command in self.terminal.commands():
                    if command in ("", "n", "next"):
                        self._next()
                    elif command in ("b", "back", "p", "prev"):
                        self._back()
                    elif command.isdigit():
                        self._jump(int(command) - 1)
                    elif command in ("q", "quit"):
                        running = False
                    else:
                        print("  ? Enter = next, b = back, a number = that song, q = quit")
                self.show.step(self.audio.read(), dt, screen)
                pygame.display.flip()
        finally:
            self.audio.stop()
            pygame.quit()

    def _next(self) -> None:
        self.show.skip()
        self._print_now_playing()

    def _back(self) -> None:
        self.show.back()
        self._print_now_playing()

    def _jump(self, index: int) -> None:
        self.show.jump(index)
        self._print_now_playing()

    def _print_now_playing(self) -> None:
        if self.show.setlist is not None:
            print(f"  ▶ {self.show.setlist.label()}", flush=True)

    def _print_help(self) -> None:
        if self.show.setlist is None:
            print("  Space: next visual   F: fullscreen   Q/Esc: quit")
            return
        print("  In the window:  Space / → / PgDn = next song   ← / PgUp = back   1-9, 0 = song number")
        print("  In this terminal:  Enter = next   b = back   a number = that song   q = quit")
        print()
        for i, (name, title) in enumerate(self.show.setlist.songs):
            print(f"  {i + 1:2d}. {name:10s}  {title}")
        print()
        self._print_now_playing()

    def _open_window(self) -> pygame.Surface:
        # SCALED keeps the Show's size and stretches it to fit the screen,
        # adding black bars if the screen's shape is different.
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
        screen = pygame.display.set_mode((self.show.width, self.show.height), flags, display=self.display)
        pygame.mouse.set_visible(not self.fullscreen)
        return screen
