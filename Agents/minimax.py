from Board_Evals.eval_new import BoardEvaluator as NewEvaluator
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from utils.engine import GameBoard, Player
from utils.negamax import negamax
from utils.transposition_table import TranspositionTable


class MinimaxBot:
    SEARCH_DEPTH = 4

    def __init__(self, evaluator_name: str = "old"):
        evaluators = {"old": OldEvaluator, "new": NewEvaluator}
        self.evaluator = evaluators[evaluator_name]()
        self.tt = TranspositionTable()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        _, move = negamax(board, player, self.SEARCH_DEPTH,
                          self.evaluator, tt=self.tt)
        return move
