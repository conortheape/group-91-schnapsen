import random
from typing import Optional
from schnapsen.game import Bot, PlayerPerspective, Move


class StrategyBot2(Bot):
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(self.seed)

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        pass

    def __repr__(self) -> str:
        return f"StrategyBot2(seed={self.seed})"