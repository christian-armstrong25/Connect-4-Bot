"""
Iterative Deepening Bot Implementation

A bot that uses iterative deepening to gradually increase search depth until
time runs out. This ensures the bot always has a move ready and can use all
available time effectively.
"""

import time
from typing import Optional
from connect4_engine import GameBoard, Player
from Board_Evals.eval_new import BoardEvaluator as NewEvaluator
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from utils.negamax import negamax


class IterativeDeepeningBot:
    # Set a small buffer to ensure we finish search before deadline
    TIME_BUFFER_MS = 0.25

    def __init__(self, evaluator_name: str = "old"):
        evaluators = {"old": OldEvaluator,
                      "new": NewEvaluator}
        self.evaluator = evaluators[evaluator_name]()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        deadline = time.perf_counter() + (time_per_move - self.TIME_BUFFER_MS) / 1000.0

        best_move = None
        depth = 1

        while True:
            # Search using best_move from previous iteration for move ordering
            _, move = negamax(
                board, player, depth, self.evaluator,
                deadline=deadline,
                first_move=best_move
            )

            if move is None:
                return best_move

            best_move = move
            depth += 1