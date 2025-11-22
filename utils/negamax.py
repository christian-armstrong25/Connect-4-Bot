import time
from typing import Optional, Tuple

from utils.engine import GameBoard, Player
from utils.transposition_table import TranspositionTable
from utils.zobrist import get_hasher

MATE_SCORE = 1000


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

    tt_result = tt.get(hash_value, depth, alpha, beta)
    if tt_result is not None:
        return tt_result

    # Get valid moves in center-first order, then order by transposition table scores
    moves = board.get_valid_moves()
    if not moves:  # check draw
        return (0, None)

    if depth == 0:
        score = evaluator.evaluate_board(board)
        score = -score if player == Player.PLAYER2 else score
        # Don't cache leaf node evaluations (cheap and numerous)
        return (score, None)

    # Pre-compute opponent to avoid repeated conditionals
    opponent = Player.PLAYER2 if player == Player.PLAYER1 else Player.PLAYER1

    # Order moves by transposition table scores
    move_data = []
    for move in moves:
        row = _get_row_after_move(board, move)
        move_hash = hasher.update_hash(hash_value, move, row, player)
        opponent_score = tt.get_score(move_hash) or MATE_SCORE
        move_data.append((move, move_hash, opponent_score))

    move_data.sort(key=lambda x: x[2])  # Sort by opponent score (ascending)

    best_score, best_move = -MATE_SCORE, None

    for move, move_hash, _ in move_data:
        # Check deadline before recursive call
        if deadline and time.perf_counter() >= deadline:
            return -MATE_SCORE, None

        board.make_move(move, player)
        if board.check_win(player):
            score = MATE_SCORE - ply
            board.undo_move(move)
            tt.store(hash_value, score, depth, move)
            return score, move

        score = -negamax(board, opponent, depth - 1, evaluator, -beta, -alpha,
                         deadline, ply + 1, tt, move_hash)[0]
        board.undo_move(move)

        # If recursive call timed out, propagate timeout
        # Uniquely identifies timout because opponent mate always has ply > 0
        if score == MATE_SCORE:
            return MATE_SCORE, None

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
