"""Script to solve positions using minimax at max depth to populate precomputed_moves."""
import sys
import os
from typing import Dict, Optional, Tuple, Set
from utils.engine import GameBoard, Player
from utils.zobrist import get_hasher
from utils.negamax import negamax
from utils.transposition_table import TranspositionTable
from Board_Evals.eval_new import BoardEvaluator
import utils.zobrist
from tqdm import tqdm

# Constants
CENTER_FIRST_MOVES = [3, 2, 4, 1, 5, 0, 6]  # Center columns first
MAX_BEST_MOVES = 2  # Limit to top 2-3 moves based on evaluation

# Reset to ensure fixed seed
utils.zobrist._hasher = None
hasher = get_hasher()

# Global progress bar
pbar = None


def solve_position(board: GameBoard, current_player: Player, max_depth: int,
                   tt: TranspositionTable, position_hash: int,
                   evaluator=None) -> Optional[Tuple[int, int, int]]:
    """
    Solve a position using minimax at max depth.
    Note: negamax already checks the transposition table, so no need to check here.
    Returns (score, move, depth) if successful.
    """
    score, best_move = negamax(
        board, current_player, max_depth, evaluator,
        float('-inf'), float('inf'), deadline=None, ply=0, tt=tt,
        hash_value=position_hash
    )
    if best_move is None:
        return None
    # Get the depth from the TT entry (the entry was stored by negamax)
    stored_depth = tt.get_depth(position_hash)
    if stored_depth is None:
        # Shouldn't happen, but use max_depth as fallback
        stored_depth = max_depth
    return (score, best_move, stored_depth)


def select_moves_to_explore(board: GameBoard, player: Player, valid_moves: list,
                            best_move: Optional[int], evaluator, tt: TranspositionTable,
                            position_hash: int) -> list:
    """Select top 2-3 moves to explore based on evaluator score and transposition table."""
    if not valid_moves:
        return []

    valid_set = set(valid_moves)
    move_scores = []

    # Score each move from current player's perspective
    for move in valid_moves:
        if not board.can_play(move):
            continue

        # Check transposition table for this position after the move
        row = _get_row_after_move(board, move)
        move_hash = hasher.update_hash(position_hash, move, row, player)
        tt_score = tt.get_score(move_hash)

        if tt_score is not None:
            # TT score is from opponent's perspective (after move, opponent is next to play)
            # Negate to get score from current player's perspective
            score = -tt_score
            move_scores.append((move, score))
        else:
            # Use evaluator to score position after move
            board.make_move(move, player)
            eval_score = evaluator.evaluate_board(board)
            # Evaluator returns from P1's perspective, adjust for current player
            score = -eval_score if player == Player.PLAYER2 else eval_score
            board.undo_move(move)
            move_scores.append((move, score))

    # Sort by score (descending - best moves first)
    move_scores.sort(key=lambda x: x[1], reverse=True)

    # Select top MAX_BEST_MOVES moves
    moves_to_explore = [move for move, _ in move_scores[:MAX_BEST_MOVES]]

    # Always include best_move if available and not already included
    if best_move is not None and best_move in valid_set and best_move not in moves_to_explore:
        moves_to_explore.insert(0, best_move)
        # Keep only top MAX_BEST_MOVES
        moves_to_explore = moves_to_explore[:MAX_BEST_MOVES]

    return moves_to_explore


def _get_row_after_move(board: GameBoard, col: int) -> int:
    """Get the row index after making a move in the given column."""
    col_base = col * (GameBoard.HEIGHT + 1)
    col_mask = board.mask & (((1 << (GameBoard.HEIGHT + 1)) - 1) << col_base)
    return col_mask.bit_count() if hasattr(int, 'bit_count') else bin(col_mask).count('1')


def explore_positions(board: GameBoard, current_player: Player, depth: int,
                      max_explore_depth: int, max_search_depth: int,
                      precomputed_moves: Dict[int, Tuple[int, int, int]], explored: Set[int],
                      tt: TranspositionTable, stats: Dict[str, int],
                      evaluator=None) -> None:
    """Recursively explore positions and solve them using minimax."""
    global pbar

    if depth >= max_explore_depth:
        return

    if board.check_win(Player.PLAYER1) or board.check_win(Player.PLAYER2) or board.is_full():
        return

    position_hash = hasher.compute_hash(board)

    if position_hash in explored:
        stats['skipped_explored'] += 1
        return

    explored.add(position_hash)

    result = precomputed_moves.get(position_hash)
    if result is None:
        result = solve_position(
            board, current_player, max_search_depth, tt, position_hash, evaluator)
        if result is None:
            return
        score, best_move, stored_depth = result
        precomputed_moves[position_hash] = (score, best_move, stored_depth)
        stats['solved'] += 1
        if pbar is not None:
            pbar.update(1)
    else:
        _, best_move, _ = result
        stats['skipped_existing'] += 1

    valid_moves = board.get_valid_moves()
    moves_to_explore = select_moves_to_explore(
        board, current_player, valid_moves, best_move, evaluator, tt, position_hash)

    if not moves_to_explore:
        return

    opponent = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1
    for move in moves_to_explore:
        board.make_move(move, current_player)
        explore_positions(board, opponent, depth + 1, max_explore_depth,
                          max_search_depth, precomputed_moves, explored, tt, stats, evaluator)
        board.undo_move(move)


def solve_all_positions_efficiently(tt: TranspositionTable,
                                    precomputed_moves: Dict[int, Tuple[int, int, int]]) -> int:
    """Efficiently solve all positions by solving the starting position once."""
    board = GameBoard()
    position_hash = hasher.compute_hash(board)

    global pbar
    # Start with indeterminate progress bar for solving
    pbar = tqdm(desc="Solving game tree", unit="nodes", dynamic_ncols=True)

    # Solve starting position - fills TT with all positions
    negamax(
        board, Player.PLAYER1, GameBoard.MAX_MOVES,
        evaluator=None,
        alpha=float('-inf'),
        beta=float('inf'),
        deadline=None,
        ply=0,
        tt=tt,
        hash_value=position_hash
    )

    # Close the solving bar and create extraction bar
    pbar.close()

    # Extract all positions from TT
    pbar = tqdm(total=len(tt.table), desc="Extracting positions",
                unit="pos", dynamic_ncols=True)

    initial_size = len(precomputed_moves)
    for hash_value, (score, depth, move) in tt.table.items():
        if hash_value not in precomputed_moves and move is not None:
            precomputed_moves[hash_value] = (score, move, depth)
        pbar.update(1)

    pbar.close()
    return len(precomputed_moves) - initial_size


def count_positions_to_solve(board: GameBoard, current_player: Player, depth: int,
                             max_explore_depth: int, existing_moves: Dict[int, Tuple[int, int, int]],
                             explored: Set[int], evaluator, tt: TranspositionTable) -> int:
    """Count how many positions will actually be solved (excluding skipped/existing)."""
    if depth >= max_explore_depth:
        return 0

    if board.check_win(Player.PLAYER1) or board.check_win(Player.PLAYER2) or board.is_full():
        return 0

    position_hash = hasher.compute_hash(board)
    if position_hash in explored:
        return 0

    explored.add(position_hash)
    count = 1 if position_hash not in existing_moves else 0

    opponent = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1
    valid_moves = board.get_valid_moves()
    # Use same move selection logic as exploration
    moves_to_explore = select_moves_to_explore(
        board, current_player, valid_moves, None, evaluator, tt, position_hash)

    for move in moves_to_explore:
        board.make_move(move, current_player)
        count += count_positions_to_solve(board, opponent, depth + 1,
                                          max_explore_depth, existing_moves, explored, evaluator, tt)
        board.undo_move(move)

    return count


def generate_precomputed_moves(max_explore_depth: int = 8,
                               max_search_depth: Optional[int] = None,
                               existing_moves: Optional[Dict[int, Tuple[int, int, int]]] = None) -> Dict[int, Tuple[int, int, int]]:
    """Generate precomputed moves database by solving positions with minimax."""
    max_search_depth = max_search_depth or GameBoard.MAX_MOVES
    existing_moves = existing_moves or {}

    tt = TranspositionTable()
    for hash_val, (score, move, depth) in existing_moves.items():
        tt.store(hash_val, score, depth, move)

    precomputed_moves = dict(existing_moves)
    stats = {'solved': 0, 'skipped_existing': 0, 'skipped_explored': 0}

    solving_to_max_depth = max_search_depth >= GameBoard.MAX_MOVES

    if solving_to_max_depth:
        print("Using efficient full-solve mode (solving to max depth)...")
        if existing_moves:
            print(f"Pre-loaded {len(existing_moves)} existing positions")

        stats['solved'] = solve_all_positions_efficiently(
            tt, precomputed_moves)

        print("=" * 70)
        print(f"Statistics:")
        print(f"  Pre-loaded: {len(existing_moves)}")
        print(f"  Newly solved: {stats['solved']}")
        print(f"  Total positions: {len(precomputed_moves)}")
        print(f"  TT size: {len(tt.table)}")
    else:
        print(f"Using exploration mode...")
        print(
            f"Solving positions up to exploration depth {max_explore_depth}...")
        print(f"Using minimax search depth: {max_search_depth}")
        if existing_moves:
            print(f"Pre-loaded {len(existing_moves)} existing positions")

        evaluator = BoardEvaluator()

        print("Counting positions to solve...")
        board = GameBoard()
        count_explored = set()
        tt_count = TranspositionTable()  # Use fresh TT for counting
        for hash_val, (score, move, depth) in existing_moves.items():
            tt_count.store(hash_val, score, depth, move)
        total_to_solve = count_positions_to_solve(board, Player.PLAYER1, 0,
                                                  max_explore_depth, existing_moves, count_explored, evaluator, tt_count)

        global pbar
        pbar = tqdm(total=total_to_solve, desc="Solving",
                    unit="pos", dynamic_ncols=True)

        explored = set()
        explore_positions(board, Player.PLAYER1, 0, max_explore_depth,
                          max_search_depth, precomputed_moves, explored, tt, stats, evaluator)

        pbar.close()

        print("=" * 70)
        print(f"Statistics:")
        print(f"  Newly solved: {stats['solved']}")
        print(f"  Skipped (existing): {stats['skipped_existing']}")
        print(f"  Skipped (already explored): {stats['skipped_explored']}")
        print(f"  Total positions: {len(precomputed_moves)}")
        print(f"  TT size: {len(tt.table)}")

    return precomputed_moves


def load_existing_moves() -> Dict[int, Tuple[int, int, int]]:
    """Load existing precomputed moves from file. Format: (score, move, depth)."""
    try:
        from Board_Evals.precomputed_moves import PRECOMPUTED_MOVES
        return dict(PRECOMPUTED_MOVES)
    except (ImportError, AttributeError):
        return {}


def write_precomputed_moves(precomputed_moves: Dict[int, Tuple[int, int, int]],
                            file_path: str = "Board_Evals/precomputed_moves.py") -> None:
    """Write precomputed moves with scores and depth to the file. Format: (score, move, depth)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, file_path)

    with open(full_path, 'w') as f:
        f.write(
            '"""Precomputed moves: zobrist hashes mapped to (score, move, depth) tuples for board positions."""\n\n')
        f.write('PRECOMPUTED_MOVES = {\n')
        for hash_val, (score, move, depth) in sorted(precomputed_moves.items()):
            f.write(f'    {hash_val}: ({score}, {move}, {depth}),\n')
        f.write('}\n')

    print(f"\n✓ Written {len(precomputed_moves)} positions to {file_path}")


def main():
    """Main entry point."""
    max_explore_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    max_search_depth = int(sys.argv[2]) if len(
        sys.argv) > 2 else GameBoard.MAX_MOVES
    merge_existing = sys.argv[3].lower(
    ) != 'replace' if len(sys.argv) > 3 else True

    existing_moves = {}
    if merge_existing:
        existing_moves = load_existing_moves()
        if existing_moves:
            print(f"Loaded {len(existing_moves)} existing precomputed moves")

    precomputed_moves = generate_precomputed_moves(
        max_explore_depth=max_explore_depth,
        max_search_depth=max_search_depth,
        existing_moves=existing_moves if merge_existing else {}
    )

    new_count = len(precomputed_moves) - len(existing_moves)
    if existing_moves and new_count > 0:
        print(f"\nSummary: {new_count} new positions added")

    write_precomputed_moves(precomputed_moves)


if __name__ == "__main__":
    main()
