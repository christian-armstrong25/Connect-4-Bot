#!/usr/bin/env python3
from parser import Bot, GameBoard, Player
import numpy as np
from evaluation import BoardEvaluator


class MinimaxBot(Bot):
    def __init__(self):
        self.evaluator = BoardEvaluator()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        return self.minimax(board, player, 6)[1]

    def minimax(self, board: GameBoard, player: Player, depth: int, alpha: float = float('-inf'), beta: float = float('inf')) -> tuple[float, int]:
        if depth == 0 or board.is_full():
            return self.evaluator.evaluate_board(board, player), None

        scores = []
        moves = self._order_moves_center_out(board.get_valid_moves())

        if not moves:
            return self.evaluator.evaluate_board(board, player), None

        for move in moves:
            board.make_move(move, player)
            opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
            score = self.minimax(board, opponent, depth-1,
                                 alpha, beta)[0]
            scores.append(score)
            board.undo_last_move()

            # Alpha-beta pruning
            if player == Player.PLAYER1:
                alpha = max(alpha, score)
            else:
                beta = min(beta, score)

            if beta <= alpha:
                break

        idx = np.argmax(
            scores) if player == Player.PLAYER1 else np.argmin(scores)

        return scores[idx], moves[idx]

    def _order_moves_center_out(self, moves):
        center_order = [3, 4, 2, 5, 1, 6, 0]
        return [col for col in center_order if col in moves]
