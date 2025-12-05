"""Script to generate precomputed moves through self-play."""
import os
import sys
import time
from typing import Dict, Optional, Set, Tuple

from tqdm import tqdm

import utils.zobrist
from Agents.ids import IterativeDeepeningBot
from utils.engine import GameBoard, Player
from utils.transposition_table import TranspositionTable
from utils.zobrist import get_hasher

# Reset to ensure fixed seed
utils.zobrist._hasher = None
hasher = get_hasher()


def play_self_play_game(agent, board: GameBoard, time_per_move: int,
                        visited_positions: Set[int]) -> Tuple[str, int]:
    """
    Play a single self-play game and track visited positions.
    Returns (result, num_moves).
    """
    board.reconstruct_from_moves([])
    current_player = Player.PLAYER1
    move_count = 0

    while move_count < GameBoard.MAX_MOVES:
        # Track position before move
        position_hash = hasher.compute_hash(board)
        visited_positions.add(position_hash)

        # Get move from agent (populates TT with positions it explores)
        move = agent.calculate_move(board, current_player, time_per_move)
        if move is None or not board.make_move(move, current_player):
            return "error", move_count

        move_count += 1

        # Track position after move
        position_hash_after = hasher.compute_hash(board)
        visited_positions.add(position_hash_after)

        if board.check_win(current_player):
            return "win", move_count
        if board.is_full():
            return "draw", move_count

        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1

    return "draw", move_count


def extract_positions_from_tt(tt: TranspositionTable, visited_positions: Set[int],
                              precomputed_moves: Dict[int, Tuple[int, int, int]],
                              min_depth: int = 0) -> int:
    """
    Extract positions from transposition table that were actually visited.

    Args:
        tt: Transposition table to extract from
        visited_positions: Set of position hashes that were actually visited
        precomputed_moves: Dictionary to add positions to
        min_depth: Minimum depth to consider (only store positions searched to at least this depth)

    Returns:
        Number of new positions added
    """
    new_count = 0
    updated_count = 0

    for position_hash in visited_positions:
        entry = tt.table.get(position_hash)
        if entry is None:
            continue

        score, depth, move = entry

        if depth >= min_depth and move is not None:
            existing = precomputed_moves.get(position_hash)
            if existing is None:
                # New position
                precomputed_moves[position_hash] = (score, move, depth)
                new_count += 1
            else:
                # Position exists - update if new depth is greater
                existing_score, existing_move, existing_depth = existing
                if depth > existing_depth:
                    precomputed_moves[position_hash] = (score, move, depth)
                    updated_count += 1

    return new_count + updated_count


def generate_precomputed_moves_self_play(time_limit_seconds: float,
                                         time_per_move: int = 100,
                                         min_depth: int = 0,
                                         max_depth: int = 42,
                                         evaluator_name: str = "new",
                                         existing_moves: Optional[Dict[int,
                                                                       Tuple[int, int, int]]] = None,
                                         adaptive_time: bool = True,
                                         max_time_per_move: int = 10000) -> Dict[int, Tuple[int, int, int]]:
    """
    Generate precomputed moves through self-play.

    The agent plays against itself, and only positions actually encountered
    during games are stored. As search depth increases, only positions
    searched to sufficient depth are cached.

    Adaptive behavior is based on:
    - Connect 4 branching factor: ~7 moves per position
    - Time-depth relationship: Each depth level requires ~7x more time
    - Position discovery rate: Adjust based on actual new positions found

    Args:
        time_limit_seconds: How long to run self-play (in seconds)
        time_per_move: Initial time per move in milliseconds
        min_depth: Minimum search depth to cache positions
        max_depth: Maximum search depth to use
        evaluator_name: Which evaluator to use ("old" or "new")
        existing_moves: Existing precomputed moves to merge with
        adaptive_time: If True, adaptively adjust time and depth based on discovery rate
        max_time_per_move: Maximum time per move when using adaptive time

    Returns:
        Dictionary of precomputed moves
    """
    existing_moves = existing_moves or {}
    precomputed_moves = dict(existing_moves)

    # Create agent with shared transposition table
    agent = IterativeDeepeningBot(evaluator_name)
    tt = agent.tt  # Shared transposition table

    # Pre-load existing moves into TT
    for hash_val, (score, move, depth) in existing_moves.items():
        tt.store(hash_val, score, depth, move)

    hasher = get_hasher()
    visited_positions: Set[int] = set()

    start_time = time.perf_counter()
    game_count = 0
    total_moves = 0
    initial_position_count = len(precomputed_moves)

    # Adaptive parameters
    current_time_per_move = time_per_move
    current_min_depth = min_depth

    # Track discovery rate for adaptive adjustments
    # Connect 4 has ~7 moves per position on average (branching factor)
    BRANCHING_FACTOR = 7.0
    # Each depth level requires roughly BRANCHING_FACTOR more time
    DEPTH_TIME_MULTIPLIER = BRANCHING_FACTOR

    # Track recent discovery rate (positions per game over last N games)
    recent_discoveries = []  # List of (game_count, new_positions) tuples
    DISCOVERY_WINDOW = 10  # Look at last 10 games for rate calculation

    # Progress tracking
    pbar = tqdm(desc="Self-play", unit="games", dynamic_ncols=True)

    print(f"Starting self-play for {time_limit_seconds:.1f} seconds...")
    print(f"Time per move: {time_per_move}ms")
    print(f"Initial minimum depth to cache: {current_min_depth}")
    print(f"Maximum search depth: {max_depth}")

    while time.perf_counter() - start_time < time_limit_seconds:

        # Play a game
        board = GameBoard()
        _, moves = play_self_play_game(
            agent, board, current_time_per_move, visited_positions)

        game_count += 1
        total_moves += moves

        # Extract positions from TT that were visited and meet depth requirement
        positions_before = len(precomputed_moves)
        extract_positions_from_tt(
            tt, visited_positions, precomputed_moves,
            min_depth=current_min_depth
        )

        total_new_positions = len(precomputed_moves) - initial_position_count
        new_this_game = len(precomputed_moves) - positions_before

        # Track discovery rate
        recent_discoveries.append((game_count, new_this_game))
        if len(recent_discoveries) > DISCOVERY_WINDOW:
            recent_discoveries.pop(0)

        # Calculate average discovery rate over recent games
        recent_total = sum(pos for _, pos in recent_discoveries)
        discovery_rate = recent_total / \
            len(recent_discoveries) if recent_discoveries else 0

        # Adaptive adjustment based on discovery rate and TT analysis
        if adaptive_time and len(recent_discoveries) >= DISCOVERY_WINDOW:
            # Analyze TT to see what depth we're actually reaching
            tt_depths = [entry[1]
                         for entry in tt.table.values() if entry[1] is not None]
            if tt_depths:
                avg_tt_depth = sum(tt_depths) / len(tt_depths)
                max_tt_depth = max(tt_depths)
            else:
                avg_tt_depth = 0
                max_tt_depth = 0

            # If discovery rate is very low and we're searching deeper than we're caching
            if discovery_rate < 0.1 and max_tt_depth > current_min_depth + 2:
                # Increase min_depth to match what we're actually searching
                # This ensures we cache the positions we're already exploring
                if current_min_depth < max_tt_depth - 1:
                    current_min_depth = min(
                        current_min_depth + 1, max_tt_depth - 1, max_depth)
                    # Extract all positions from TT at new depth
                    all_tt_positions = set(tt.table.keys())
                    extract_positions_from_tt(
                        tt, all_tt_positions, precomputed_moves, min_depth=current_min_depth)
                    pbar.set_description(
                        f"Self-play (min_depth {current_min_depth})")

            # If discovery rate is zero and we're not searching much deeper than min_depth
            elif discovery_rate == 0 and max_tt_depth <= current_min_depth + 1:
                # Need to search deeper - increase time based on branching factor
                # To go one depth deeper, we need roughly BRANCHING_FACTOR more time
                if current_time_per_move < max_time_per_move:
                    # Calculate time needed for one more depth level
                    time_for_next_depth = int(
                        current_time_per_move * DEPTH_TIME_MULTIPLIER)
                    # But don't increase too aggressively - cap at 2x per adjustment
                    new_time = min(time_for_next_depth,
                                   current_time_per_move * 2, max_time_per_move)
                    if new_time > current_time_per_move:
                        current_time_per_move = new_time
                        # Extract all positions from TT when time increases
                        all_tt_positions = set(tt.table.keys())
                        extract_positions_from_tt(
                            tt, all_tt_positions, precomputed_moves, min_depth=current_min_depth)
                        pbar.set_description(
                            f"Self-play (time: {current_time_per_move}ms)")

            # Gradually increase min_depth over time to keep up with deeper searches
            # This is based on elapsed time, not discovery rate
            elapsed = time.perf_counter() - start_time
            target_min_depth = min_depth + \
                int((elapsed / time_limit_seconds) * (max_depth - min_depth))
            if target_min_depth > current_min_depth and current_min_depth < max_depth:
                current_min_depth = min(target_min_depth, max_depth)
                all_tt_positions = set(tt.table.keys())
                extract_positions_from_tt(
                    tt, all_tt_positions, precomputed_moves, min_depth=current_min_depth)
                pbar.set_description(
                    f"Self-play (min_depth {current_min_depth})")

        pbar.update(1)
        pbar.set_postfix({
            'games': game_count,
            'positions': len(precomputed_moves),
            'new': total_new_positions,
            'time_ms': current_time_per_move
        })

        visited_positions.clear()

    pbar.close()

    # Final pass: extract any remaining positions from TT that meet criteria
    print("\nPerforming final extraction from transposition table...")
    all_tt_positions = set(tt.table.keys())
    final_new = extract_positions_from_tt(tt, all_tt_positions, precomputed_moves,
                                          min_depth=current_min_depth)
    if final_new > 0:
        print(f"  Extracted {final_new} additional positions from TT")

    elapsed = time.perf_counter() - start_time

    print("=" * 70)
    print(f"Self-play Statistics:")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Games played: {game_count}")
    print(f"  Total moves: {total_moves}")
    print(
        f"  Average moves per game: {total_moves / game_count if game_count > 0 else 0:.1f}")
    print(f"  Pre-loaded positions: {len(existing_moves)}")
    print(
        f"  New positions cached: {len(precomputed_moves) - len(existing_moves)}")
    print(f"  Total positions: {len(precomputed_moves)}")
    print(f"  TT size: {len(tt.table)}")
    print(f"  Final minimum depth: {current_min_depth}")
    print(f"  Final time per move: {current_time_per_move}ms")
    print("=" * 70)

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


def save_positions_from_transposition_tables(transposition_tables: list,
                                             visited_positions: Set[int],
                                             min_depth: int = 0,
                                             file_path: str = "Board_Evals/precomputed_moves.py",
                                             reload_module: bool = True) -> int:
    """
    Extract positions from one or more transposition tables and save to precomputed_moves.py.

    Args:
        transposition_tables: List of TranspositionTable instances to extract from
        visited_positions: Set of position hashes that were actually visited during the game
        min_depth: Minimum depth to consider (only store positions searched to at least this depth)
        file_path: Path to the precomputed_moves.py file
        reload_module: If True, reload the precomputed_moves module so new positions are available

    Returns:
        Number of new positions added
    """
    # Load existing precomputed moves
    existing_moves = load_existing_moves()
    precomputed_moves = dict(existing_moves)

    # Extract positions from all transposition tables
    for tt in transposition_tables:
        for position_hash in visited_positions:
            entry = tt.table.get(position_hash)
            if entry is None:
                continue

            score, depth, move = entry

            if depth >= min_depth and move is not None:
                existing = precomputed_moves.get(position_hash)
                if existing is None:
                    # New position
                    precomputed_moves[position_hash] = (score, move, depth)
                else:
                    # Position exists - update if new depth is greater
                    existing_score, existing_move, existing_depth = existing
                    if depth > existing_depth:
                        precomputed_moves[position_hash] = (score, move, depth)

    # Save to file
    new_count = len(precomputed_moves) - len(existing_moves)
    if new_count > 0 or len(precomputed_moves) != len(existing_moves):
        write_precomputed_moves(precomputed_moves, file_path)

        # Reload the module so new positions are available for future imports
        if reload_module:
            import importlib

            import Board_Evals.precomputed_moves
            importlib.reload(Board_Evals.precomputed_moves)

    return new_count


def main():
    """
    Main entry point for self-play position generation.

    Usage:
        python solve_positions.py <time_seconds> [time_per_move_ms] [min_depth] [evaluator] [max_time_per_move_ms]

    Arguments:
        time_seconds: How long to run self-play (in seconds)
        time_per_move_ms: Initial time per move in milliseconds (default: 100)
        min_depth: Minimum search depth to cache positions (default: 0)
        evaluator: Which evaluator to use - "old" or "new" (default: "new")
        max_time_per_move_ms: Maximum time per move for adaptive time (default: 10000 = 10 seconds)

    Examples:
        # Run for 60 seconds with defaults
        python solve_positions.py 60

        # Run for 120 seconds with 150ms per move
        python solve_positions.py 120 150

        # Run with minimum depth of 2
        python solve_positions.py 60 100 2

        # Run with old evaluator
        python solve_positions.py 60 100 0 old

        # Run with higher time limits for deeper search (30 seconds per move max)
        python solve_positions.py 300 1000 0 new 30000
    """
    time_limit = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    time_per_move = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    min_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    evaluator_name = sys.argv[4] if len(sys.argv) > 4 else "new"
    max_time_per_move = int(sys.argv[5]) if len(sys.argv) > 5 else 10000

    existing_moves = load_existing_moves()
    if existing_moves:
        print(f"Loaded {len(existing_moves)} existing precomputed moves")

    precomputed_moves = generate_precomputed_moves_self_play(
        time_limit_seconds=time_limit,
        time_per_move=time_per_move,
        min_depth=min_depth,
        max_depth=GameBoard.MAX_MOVES,
        evaluator_name=evaluator_name,
        existing_moves=existing_moves,
        adaptive_time=True,
        max_time_per_move=max_time_per_move
    )

    new_count = len(precomputed_moves) - len(existing_moves)
    if new_count > 0:
        print(f"\nSummary: {new_count} new positions added")

    write_precomputed_moves(precomputed_moves)


if __name__ == "__main__":
    main()
