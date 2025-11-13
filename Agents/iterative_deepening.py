"""
Iterative Deepening Bot Implementation

A bot that uses iterative deepening to gradually increase search depth until
time runs out. This ensures the bot always has a move ready and can use all
available time effectively.
"""

import time
from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class IterativeDeepeningBot(BaseNegamaxBot):
    # Set a small buffer to ensure we finish search before deadline
    TIME_BUFFER_MS = 0.15

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        deadline = time.perf_counter() + (time_per_move - self.TIME_BUFFER_MS) / 1000.0

        best_move: int = None
        depth = 1

        while True:
            # Search using best_move from previous iteration for move ordering
            _, move = self.negamax(
                board, player, depth,
                deadline=deadline,
                first_move=best_move
            )

            if move is None:
                return best_move

            best_move = move
            depth += 1