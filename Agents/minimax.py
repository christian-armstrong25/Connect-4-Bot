#!/usr/bin/env python3
"""Simple negamax bot with fixed depth."""

import time
from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class MinimaxBot(BaseNegamaxBot):
    """Negamax bot with fixed depth of 4."""

    def __init__(self, evaluator_name: str = "old"):
        super().__init__(evaluator_name)

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        return self.negamax(board, player, 4)[1]
