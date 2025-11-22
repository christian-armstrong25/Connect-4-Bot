import time
from typing import Optional, Tuple

from utils.engine import GameBoard, Player
from utils.transposition_table import TranspositionTable
from utils.zobrist import get_hasher


def negamax(board: GameBoard, player: Player, depth: int, evaluator,
            alpha: float = float('-inf'), beta: float = float('inf'),
            deadline: Optional[float] = None,
            ply: int = 0,
            tt: Optional[TranspositionTable] = None,
            hash_value: Optional[int] = None) -> Tuple[int, Optional[int]]:
    if tt is None:
        tt = TranspositionTable()
    hasher = get_hasher()

    if hash_value is None:
        hash_value = hasher.compute_hash(board)

    # Check transposition table
    tt_result = tt.get(hash_value, depth, alpha, beta)
    if tt_result is not None:
        return tt_result

    # Get valid moves
    moves = board.get_valid_moves()
    if not moves:  # Draw
        return (0, None)

    if depth == 0: # Non-Terminal Leaf
        return (0, None)

    opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1

    max_score_when_not_winning = (GameBoard.MAX_MOVES - 1 - board.move_count) // 2
    if beta > max_score_when_not_winning:
        beta = max_score_when_not_winning
        if alpha >= beta:
            # Empty window - return first move with bound score
            return beta, moves[0] if moves else None

    # Order moves by transposition table scores for better pruning
    move_data = []
    for move in moves:
        row = _get_row_after_move(board, move)
        move_hash = hasher.update_hash(hash_value, move, row, player)
        opponent_score = tt.get_score(move_hash)
        move_data.append((move, move_hash,
                         opponent_score if opponent_score is not None else max_score_when_not_winning))
    move_data.sort(key=lambda x: x[2])

    # Initialize with worst score and first move (ensure we always return a move)
    best_score, best_move = -max_score_when_not_winning, move_data[0][0]

    for move, move_hash, _ in move_data:
        # Check deadline before recursive call
        if deadline and time.perf_counter() >= deadline:
            return best_score, best_move

        board.make_move(move, player)

        # Check for immediate win
        if board.check_win(player):
            # Win score = (MAX_MOVES + 1 - nbMoves()) / 2
            score = (GameBoard.MAX_MOVES + 1 - board.move_count) // 2
            board.undo_move(move)
            tt.store(hash_value, score, depth, move)
            return score, move

        # Recursive search
        score_result = negamax(board, opponent, depth - 1, evaluator,
                               -beta, -alpha, deadline, ply + 1, tt, move_hash)
        score = -score_result[0]
        board.undo_move(move)

        # Handle timeout from recursive call
        if score_result[1] is None and deadline and time.perf_counter() >= deadline:
            continue

        # Update best move
        if score > best_score:
            best_score, best_move = score, move

        alpha = max(alpha, score)
        if alpha >= beta:
            tt.store(hash_value, score, depth, best_move)
            return (score, best_move)

    tt.store(hash_value, best_score, depth, best_move)
    return best_score, best_move


def _get_row_after_move(board: GameBoard, col: int) -> int:
    col_base = col * (GameBoard.HEIGHT + 1)
    col_mask = board.mask & (((1 << (GameBoard.HEIGHT + 1)) - 1) << col_base)
    return col_mask.bit_count() if hasattr(int, 'bit_count') else bin(col_mask).count('1')
