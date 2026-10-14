"""Reads commands typed into the terminal while the window is open.

input() blocks, so it runs on its own thread and only drops each line into a
queue. The Player picks them up on the main thread, between frames.
"""
import queue
import threading


class TerminalInput:
    def __init__(self) -> None:
        self.lines: queue.Queue[str] = queue.Queue()

    def start(self) -> None:
        # daemon=True: don't keep the program alive waiting for a line on quit.
        threading.Thread(target=self._read, daemon=True).start()

    def commands(self) -> list[str]:
        """Every line typed since the last call, lowercased and stripped."""
        found = []
        while not self.lines.empty():
            found.append(self.lines.get().strip().lower())
        return found

    def _read(self) -> None:
        while True:
            try:
                self.lines.put(input())
            except EOFError:
                return
