"""
Utility functions for Connect 4 AI bots.

This module provides shared algorithms and utilities used by different bot implementations.
"""

import time
from typing import Optional, Tuple

from connect4_engine import GameBoard, Player


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            first_move: Optional[int] = None) -> Tuple[float, Optional[int]]:
    """
    Negamax algorithm with alpha-beta pruning.

    Negamax is a variant of minimax that uses the mathematical property that
    max(a, b) = -min(-a, -b) to simplify the code.

    Args:
        board: The current game board state
        player: The player whose turn it is
        depth: Maximum depth to search
        evaluator: Board evaluator instance with evaluate_board method
        alpha: Best score the maximizing player can guarantee
        beta: Best score the minimizing player can guarantee
        deadline: Optional deadline (perf_counter time) to stop searching
        first_move: Optional move to try first (for move ordering)

    Returns:
        Tuple of (score, best_move). Returns (-inf, None) on timeout.
    """
    if depth == 0 or board.is_full():
        score = evaluator.evaluate_board(board)
        # Negate score for Player 2 (since evaluator returns from P1's perspective)
        return (-score if player == Player.PLAYER2 else score, None)

    moves = board.get_valid_moves()

    # Principal Variation (PV) move ordering: try the best move from previous
    # iteration first, as it's likely to be good in this iteration too
    # Create a new list to avoid modifying the cached list
    if first_move is not None and first_move in moves:
        moves = [first_move] + [m for m in moves if m != first_move]

    best_score = float('-inf')
    best_move: Optional[int] = moves[0]  # Default to first move
    opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1

    for move in moves:
        if deadline and time.perf_counter() >= deadline:
            return float('-inf'), None  # Signal timeout

        # Make move and search recursively
        board.make_move(move, player)
        score = -negamax(board, opponent, depth - 1, evaluator,
                         -beta, -alpha, deadline, None)[0]
        board.undo_move(move, player)

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = move

        # Update alpha (best score we can guarantee)
        alpha = max(alpha, score)

        # Beta cutoff: opponent won't allow us to reach this branch
        # (they have a better option elsewhere)
        if alpha >= beta:
            break  # Prune remaining moves

    return best_score, best_move
