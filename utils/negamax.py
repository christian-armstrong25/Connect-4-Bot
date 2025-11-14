import time
from typing import Optional, Tuple

from connect4_engine import GameBoard, Player


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            first_move: Optional[int] = None) -> Tuple[float, Optional[int]]:
    if depth == 0:
        score = evaluator.evaluate_board(board)
        return (-score if player == Player.PLAYER2 else score, None)

    best_score, best_move = float('-inf'), None
    moves = board.get_valid_moves()

    # Principal Variation (PV) move ordering: try the best move from previous
    # iteration first, as it's likely to be good in this iteration too
    # Create a new list to avoid modifying the cached list
    if first_move is not None and first_move in moves:
        moves = [first_move] + [m for m in moves if m != first_move]

    for move in moves:
        if deadline and time.perf_counter() >= deadline:
            return float('-inf'), None  # Signal timeout

        # Make move and search recursively
        board.make_move(move, player)

        # Check if this move wins immediately
        if board.check_win(player):
            board.undo_move(move, player)
            return float('inf'), move

        opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1
        score = -negamax(board, opponent, depth - 1, evaluator,
                         -beta, -alpha, deadline)[0]
        board.undo_move(move, player)

        # Update best move
        if score > best_score:
            best_score, best_move = score, move

        # alpha-beta pruning
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Prune remaining moves

    return best_score, best_move
