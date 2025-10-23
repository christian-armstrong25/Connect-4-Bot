#!/usr/bin/env python3
"""Base class for Connect 4 bots with shared minimax logic."""

import time
from connect4_engine import Bot, GameBoard, Player
from evaluation import BoardEvaluator


class BaseMinimaxBot(Bot):
    """Base class for minimax-based bots with shared logic."""

    def __init__(self):
        self.evaluator = BoardEvaluator()

    def minimax(self, board: GameBoard, player: Player, depth: int,
                alpha: float = float('-inf'), beta: float = float('inf'),
                deadline: float = None) -> tuple[float, int]:
        """Minimax algorithm with alpha-beta pruning."""
        # Check time limit if provided
        if deadline and time.perf_counter() >= deadline:
            return self.evaluator.evaluate_board(board, player), None

        if depth == 0 or board.is_full():
            return self.evaluator.evaluate_board(board, player), None

        moves = self._order_moves_center_out(board.get_valid_moves())
        if not moves:
            return self.evaluator.evaluate_board(board, player), None

        scores = []
        for move in moves:
            board.make_move(move, player)
            opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
            score = self.minimax(board, opponent, depth -
                                 1, alpha, beta, deadline)[0]
            scores.append(score)
            board.undo_last_move()

            # Alpha-beta pruning
            if player == Player.PLAYER1:
                alpha = max(alpha, score)
            else:
                beta = min(beta, score)

            if beta <= alpha:
                break

        # Find best move
        if player == Player.PLAYER1:
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
        else:
            best_idx = min(range(len(scores)), key=lambda i: scores[i])

        return scores[best_idx], moves[best_idx]

    def _order_moves_center_out(self, moves):
        """Order moves with center columns first for better pruning."""
        center_order = [3, 4, 2, 5, 1, 6, 0]
        return [col for col in center_order if col in moves]
