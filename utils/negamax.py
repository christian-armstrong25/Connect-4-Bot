import time
from typing import Optional, Tuple

from engine import GameBoard, Player


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            first_move: Optional[int] = None) -> Tuple[float, Optional[int]]:
    if depth == 0:
        score = evaluator.evaluate_board(board)
        return (-score if player == Player.PLAYER2 else score, None)

    # Column order prioritizing center columns
    moves = [3, 2, 4, 1, 5, 0, 6]
    # Principal Variation (PV) move ordering
    if first_move is not None and first_move in moves and moves[0] != first_move:
        moves = [first_move] + [m for m in moves if m != first_move]

    best_score, best_move = float('-inf'), None
    for move in moves:
        if deadline and time.perf_counter() >= deadline:
            return float('-inf'), None

        # if move is not valid, continue
        if not board.make_move(move, player):
            continue

        # Stop search if move wins
        if board.check_win(player):
            board.undo_move(move, player)
            return float('inf'), move

        # Recursively search
        opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
        score = -negamax(board, opponent, depth - 1, evaluator,
                         -beta, -alpha, deadline, best_move)[0]
        board.undo_move(move, player)

        # Update best move
        if score > best_score:
            best_score, best_move = score, move

        # alpha-beta pruning
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Prune remaining moves

    return best_score, best_move