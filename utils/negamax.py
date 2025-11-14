import time
from typing import List, Optional, Tuple

from engine import GameBoard, Player

# Mate score constant - large enough that regular eval scores never reach it
MATE_SCORE = 1000


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            first_move: Optional[int] = None,
            ply: int = 0,
            move_scores: Optional[List[Tuple[float, int]]] = None,
            ordered_moves: Optional[list] = None) -> Tuple[float, Optional[int]]:
    # Depth cutoff check
    if depth == 0:
        score = evaluator.evaluate_board(board)
        return (-score if player == Player.PLAYER2 else score, None)

    # Move ordering: use pre-ordered moves or default center-first ordering
    moves = ordered_moves if ordered_moves else _get_default_moves(first_move)

    best_score, best_move = float('-inf'), None
    for move in moves:
        # Time cutoff check
        if deadline and time.perf_counter() >= deadline:
            return float('-inf'), None

        # Invalid move check
        if not board.make_move(move, player):
            continue

        # Immediate win check
        if board.check_win(player):
            board.undo_move(move, player)
            return MATE_SCORE - ply, move

        # Recursive search
        opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
        score = -negamax(board, opponent, depth - 1, evaluator,
                         -beta, -alpha, deadline, best_move, ply + 1,
                         move_scores, None)[0]
        board.undo_move(move, player)

        # Store scores for move ordering
        if move_scores and ply == 0:
            move_scores.append((score, move))

        # Update best move
        if score > best_score:
            best_score, best_move = score, move

        # alpha-beta pruning
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Beta cutoff

    return best_score, best_move


def _get_default_moves(first_move: Optional[int] = None) -> list:
    """Return default move ordering (center-first) with optional PV move first."""
    moves = [3, 2, 4, 1, 5, 0, 6]
    if first_move is not None and first_move in moves[1:]:
        moves = [first_move] + [m for m in moves if m != first_move]
    return moves
