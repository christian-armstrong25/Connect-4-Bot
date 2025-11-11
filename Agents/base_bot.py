import time
from connect4_engine import Bot, GameBoard, Player
from Board_Evals.eval_old import BoardEvaluator as OldEvaluator
from Board_Evals.eval_new import BoardEvaluator as NewEvaluator


class BaseNegamaxBot(Bot):
    def __init__(self, evaluator_name: str = "old"):
        evaluators = {"old": OldEvaluator, "new": NewEvaluator}
        self.evaluator = evaluators[evaluator_name]()

    def negamax(self, board: GameBoard, player: Player, depth: int,
                alpha: float = float('-inf'), beta: float = float('inf'),
                deadline: float = None) -> tuple[float, int]:
        if depth == 0 or board.is_full() or (deadline and time.perf_counter() >= deadline):
            score = self.evaluator.evaluate_board(board, player)
            return (-score if player == Player.PLAYER2 else score, None)

        moves = board.get_valid_moves()
        if not moves:
            return 0, None

        best_score, best_move = float('-inf'), moves[0]
        opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1

        for move in moves:
            board.make_move(move, player)
            score = -self.negamax(board, opponent, depth -
                                  1, -beta, -alpha, deadline)[0]
            board.undo_move(move, player)

            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_move
