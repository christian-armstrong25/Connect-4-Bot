import time

from Board_Evals.eval_new import BoardEvaluator as NewEvaluator
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from engine import GameBoard, Player
from utils.negamax import negamax


class IterativeDeepeningBot:
    # Set a small buffer to ensure we stop search before deadline
    TIME_BUFFER_MS = 0.2
    # Center-first move ordering for Connect 4 (column 3 is center)
    CENTER_FIRST_ORDER = [3, 2, 4, 1, 5, 0, 6]

    def __init__(self, evaluator_name: str = "old"):
        evaluators = {"old": OldEvaluator,
                      "new": NewEvaluator}
        self.evaluator = evaluators[evaluator_name]()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        deadline = time.perf_counter() + (time_per_move - self.TIME_BUFFER_MS) / 1000.0
        best_move, move_order = None, []
        depth = 1

        while True:
            move_scores = []
            _, move = negamax(
                board, player, depth, self.evaluator,
                deadline=deadline,
                first_move=board.last_move,
                move_scores=move_scores,
                ordered_moves=move_order
            )

            if move is None:
                return best_move

            best_move = move
            depth += 1
            move_order = self._get_ordered_moves(board, move_scores)

    def _get_ordered_moves(self, board: GameBoard, move_scores: list) -> list:
        """Return valid moves ordered by scores from previous depth (highest first).
        Uses center-first ordering as a tiebreaker for moves with similar scores."""

        priority = {col: i for i, col in enumerate(self.CENTER_FIRST_ORDER)}
        return [m for _, m in sorted(move_scores, key=lambda sm: (-sm[0], priority.get(sm[1], 999)))]
