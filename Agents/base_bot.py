#!/usr/bin/env python3
"""Ultra-optimized base bot with shared negamax logic."""

import time
from connect4_engine import Bot, GameBoard, Player


class BaseNegamaxBot(Bot):

    def __init__(self, evaluator_name: str = "old"):
        from Board_Evals.eval_factory import create_evaluator
        self.evaluator = create_evaluator(evaluator_name)

    def negamax(self, board: GameBoard, player: Player, depth: int,
                alpha: float = float('-inf'), beta: float = float('inf'),
                deadline: float = None) -> tuple[float, int]:

        # Terminal conditions
        if depth == 0 or board.is_full() or (deadline and time.perf_counter() >= deadline):
            # In negamax, evaluation should be from current player's perspective
            score = self.evaluator.evaluate_board(board, player)
            # If it's PLAYER2's turn, negate the score since evaluation is from PLAYER1's perspective
            if player == Player.PLAYER2:
                score = -score
            return score, None

        moves = board.get_valid_moves()
        if not moves:
            return 0, None

        best_score = float('-inf')
        best_move = moves[0]

        for move in moves:
            # Make move
            board.make_move(move, player)

            # Recursive call - negamax always maximizes from current player's perspective
            opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
            score = -self.negamax(
                board, opponent, depth - 1, -beta, -alpha, deadline)[0]

            # Undo move
            board.undo_move(move, player)

            # Update best move (always maximizing in negamax)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

            # Alpha-beta pruning
            if alpha >= beta:
                break

        return best_score, best_move
