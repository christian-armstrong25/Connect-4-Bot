import time
from typing import Optional

from Board_Evals.eval_new import BoardEvaluator as NewEvaluator
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from utils.engine import GameBoard, Player
from utils.negamax import negamax
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
        best_move, best_score = None, None

        # Calculate theoretical score bounds based on remaining moves
        remaining_moves = GameBoard.MAX_MOVES - board.move_count
        min_theoretical = -(GameBoard.MAX_MOVES - remaining_moves) // 2
        max_theoretical = (GameBoard.MAX_MOVES + 1 - remaining_moves) // 2

        for depth in range(1, remaining_moves + 1):
            if time.perf_counter() >= deadline:
                break

            alpha = min_theoretical - 1
            beta = max_theoretical + 1

            # Aspiration window: use previous iteration's best score as lower bound
            # This helps prune moves that can't improve on previous results
            if best_score is not None:
                alpha = max(alpha, best_score - 1)

            score, move = negamax(
                board, player, depth, self.evaluator,
                alpha, beta,
                deadline=deadline, tt=self.tt
            )

            if move is None:  # Timeout
                break

            best_move = move
            best_score = score

            # Return early if we found a forced win
            win_score_at_current = (GameBoard.MAX_MOVES + 1 - board.move_count) // 2
            if score >= win_score_at_current:
                return best_move

        return best_move
