"""The live window: keyboard, clock and live audio, driving a Show."""
import pygame

from visual_art.audio import AudioInput
from visual_art.show import Show


class Player:
    def __init__(self, show: Show, audio: AudioInput, fullscreen: bool = True, display: int = 0, fps: int = 60) -> None:
        self.show = show
        self.audio = audio
        self.fullscreen = fullscreen
        self.display = display  # which screen: 0 = main, 1 = projector, ... (see `visual-art displays`)
        self.fps = fps

    def run(self) -> None:
        pygame.display.set_caption("visual-art")
        screen = self._open_window()
        clock = pygame.time.Clock()
        self.audio.start()
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
                        elif event.key == pygame.K_SPACE:
                            self.show.skip()
                        elif event.key == pygame.K_f:
                            self.fullscreen = not self.fullscreen
                            screen = self._open_window()
                self.show.step(self.audio.read(), dt, screen)
                pygame.display.flip()
        finally:
            self.audio.stop()
            pygame.quit()

    def _open_window(self) -> pygame.Surface:
        # SCALED keeps the Show's size and stretches it to fit the screen,
        # adding black bars if the screen's shape is different.
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
        screen = pygame.display.set_mode((self.show.width, self.show.height), flags, display=self.display)
        pygame.mouse.set_visible(not self.fullscreen)
        return screen
