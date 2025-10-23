#!/usr/bin/env python3
"""Ultra-optimized base bot with shared minimax logic."""

import time
from connect4_engine import Bot, GameBoard, Player


class BaseMinimaxBot(Bot):

    def __init__(self, evaluator_name: str = "old"):
        from Board_Evals.eval_factory import create_evaluator
        self.evaluator = create_evaluator(evaluator_name)

    def minimax(self, board: GameBoard, player: Player, depth: int,
                alpha: float = float('-inf'), beta: float = float('inf'),
                deadline: float = None) -> tuple[float, int]:

        # Terminal conditions
        if depth == 0 or board.is_full() or (deadline and time.perf_counter() >= deadline):
            return self.evaluator.evaluate_board(board, player), None

        moves = board.get_valid_moves()
        if not moves:
            return 0, None

        best_score = float(
            '-inf') if player == Player.PLAYER1 else float('inf')
        best_move = moves[0]

        for move in moves:
            # Make move
            board.make_move(move, player)

            # Recursive call
            opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
            score, _ = self.minimax(
                board, opponent, depth - 1, alpha, beta, deadline)

            # Undo move
            board.undo_move(move, player)

            # Update best move
            if player == Player.PLAYER1:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)

            # Alpha-beta pruning
            if beta <= alpha:
                break

        return best_score, best_move
