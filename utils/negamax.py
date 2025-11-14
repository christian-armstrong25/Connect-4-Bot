import time
from typing import Optional, Tuple

from engine import GameBoard, Player

# Mate score constant - large enough that regular eval scores never reach it
MATE_SCORE = 1000


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            first_move: Optional[int] = None,
            ply: int = 0) -> Tuple[float, Optional[int]]:
    # Depth cutoff Check
    if depth == 0:
        score = evaluator.evaluate_board(board)
        return (-score if player == Player.PLAYER2 else score, None)

    # Move ordering: center columns first, with PV move prioritization
    moves = [3, 2, 4, 1, 5, 0, 6]
    if first_move is not None and first_move in moves and moves[0] != first_move:
        moves = [first_move] + [m for m in moves if m != first_move]

    best_score, best_move = float('-inf'), None
    for move in moves:
        # Time cutoff Check
        if deadline and time.perf_counter() >= deadline:
            return float('-inf'), None

        # Invalid move Check
        if not board.make_move(move, player):
            continue

        # Immediate win check
        if board.check_win(player):
            board.undo_move(move, player)
            return MATE_SCORE - ply, move

        # Recursive search
        opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
        score = -negamax(board, opponent, depth - 1, evaluator,
                         -beta, -alpha, deadline, best_move, ply + 1)[0]
        board.undo_move(move, player)

        # Update best move
        if score > best_score:
            best_score, best_move = score, move

        # alpha-beta pruning
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Beta cutoff

    return best_score, best_move
