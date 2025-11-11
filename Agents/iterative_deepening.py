#!/usr/bin/env python3
import time
from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class IterativeDeepeningBot(BaseNegamaxBot):
    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        buffer_ms = 4
        deadline = time.perf_counter() + (time_per_move - buffer_ms) / 1000.0
        best_move, depth = None, 1

        while True:
            _, move = self.negamax(board, player, depth, deadline=deadline)
            if move is None:
                return best_move
            best_move, depth = move, depth + 1
