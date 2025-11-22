import time

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
        best_move = None
        depth = 1

        while True:
            _, move = negamax(board, player, depth,
                              self.evaluator, deadline=deadline, tt=self.tt)

            if move is None:
                return best_move

            best_move = move
            depth += 1
