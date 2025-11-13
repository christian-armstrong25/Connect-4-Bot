"""
Minimax Bot Implementation

A simple bot that uses fixed-depth minimax search (via negamax) to find the best move.
This bot searches to a fixed depth of 4, regardless of time available.
"""

import time
from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class MinimaxBot(BaseNegamaxBot):
    SEARCH_DEPTH = 4

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        _, move = self.negamax(
            board, player, self.SEARCH_DEPTH)

        return move
