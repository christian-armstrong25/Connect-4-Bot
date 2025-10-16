#!/usr/bin/env python3
import time
from parser import BoardHasher, Bot, GameBoard, Player

import numpy as np

from evaluation import BoardEvaluator


class IterativeDeepeningBot(Bot):

    def __init__(self):
        self.evaluator = BoardEvaluator()

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        deadline = time.perf_counter() + (time_per_move / 1000)
        return self.iterative_deepening(board, player, deadline)

    def iterative_deepening(self, board: GameBoard, player: Player, deadline: float) -> int:
        best_move = None
        depth = 1

        while True:
            _, move = self.minimax(board, player, depth, deadline)
            if move is None:
                return best_move

            best_move = move
            depth += 1

    def minimax(self, board: GameBoard, player: Player, depth: int, deadline: float, alpha: float = float('-inf'), beta: float = float('inf')) -> tuple[float, int]:
        if depth == 0 or board.is_full() or time.perf_counter() >= deadline:
            return self.evaluator.evaluate_board(board, player), None

        scores = []
        moves = self._order_moves_center_out(board.get_valid_moves())

        if not moves:
            return self.evaluator.evaluate_board(board, player), None

        for move in moves:
            board.make_move(move, player)
            opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
            score = self.minimax(board, opponent, depth-1,
                                 deadline, alpha, beta)[0]
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
