import time
from typing import Optional

from Board_Evals.eval_new import BoardEvaluator as NewEvaluator
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from utils.engine import GameBoard, Player
from utils.negamax import negamax, MATE_SCORE
from utils.transposition_table import TranspositionTable


class IterativeDeepeningBot:
    # Set a small buffer to ensure we stop search before deadline
    TIME_BUFFER_MS = 0.2

    def __init__(self, evaluator_name: str = "old"):
        evaluators = {"old": OldEvaluator, "new": NewEvaluator}
        self.evaluator = evaluators[evaluator_name]()
        self.tt = TranspositionTable()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        deadline = time.perf_counter() + (time_per_move - self.TIME_BUFFER_MS) / 1000.0
        remaining_moves = GameBoard.MAX_MOVES - board.move_count
        best_move = None

        # Iterative deepening: explore progressively deeper until time runs out
        for depth in range(1, remaining_moves + 1):
            if time.perf_counter() >= deadline:
                break

            score, move = negamax(
                board, player, depth, self.evaluator,
                float('-inf'), float('inf'),
                deadline=deadline, tt=self.tt
            )

            # If search timed out, return best move found so far
            if move is None:
                break

            best_move = move

            # Return early if we found a forced win (provably optimal)
            if score >= MATE_SCORE - depth:
                return best_move

        return best_move
