"""Picks which visual comes next, like dealing from a shuffled deck."""
import random


class Shuffle:
    def __init__(self, names: list[str], seed=None) -> None:
        self.names = list(names)
        self.random = random.Random(seed)
        self.deck: list[str] = []
        self.last: str | None = None

    def next(self) -> str:
        if not self.deck:
            self.deck = self.names[:]
            self.random.shuffle(self.deck)
            # Never play the same visual twice in a row across a reshuffle.
            if len(self.deck) > 1 and self.deck[-1] == self.last:
                self.deck[0], self.deck[-1] = self.deck[-1], self.deck[0]
        self.last = self.deck.pop()
        return self.last
