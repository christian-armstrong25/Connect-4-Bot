#!/usr/bin/env python3
"""Iterative deepening negamax bot with time management."""

import time
from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class IterativeDeepeningBot(BaseNegamaxBot):
    """Iterative deepening bot that uses available time efficiently."""

    def __init__(self, evaluator_name: str = "old"):
        super().__init__(evaluator_name)

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        buffer_ms = 0
        deadline = time.perf_counter() + ((time_per_move - buffer_ms) / 1000.0)
        return self.iterative_deepening(board, player, deadline)

    def iterative_deepening(self, board: GameBoard, player: Player, deadline: float) -> int:
        """Iteratively increase depth until time runs out."""
        best_move = None
        depth = 1

        while True:
            _, move = self.negamax(board, player, depth, deadline=deadline)
            if move is None:
                return best_move

            best_move = move
            depth += 1