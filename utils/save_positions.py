"""Utility to save positions from transposition tables to precomputed_moves.py"""
import os
from typing import Dict, Tuple

from Board_Evals.precomputed_moves import PRECOMPUTED_MOVES
from utils.transposition_table import TranspositionTable


def save_positions(*transposition_tables: TranspositionTable,
                   file_path: str = "Board_Evals/precomputed_moves.py") -> int:
    """Save all positions from transposition tables to file. Returns number of new positions."""
    # Merge all positions from all tables
    all_positions: Dict[int, Tuple[int, int, int]] = dict(PRECOMPUTED_MOVES)

    for tt in transposition_tables:
        for hash_val, (score, depth, move) in tt.table.items():
            if move is not None:
                existing = all_positions.get(hash_val)
                if existing is None or depth > existing[2]:
                    all_positions[hash_val] = (score, move, depth)

    # Write to file
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(script_dir, file_path)

    with open(full_path, 'w') as f:
        f.write('"""Precomputed moves: zobrist hashes mapped to (score, move, depth) tuples for board positions."""\n\n')
        f.write('PRECOMPUTED_MOVES = {\n')
        for hash_val, (score, move, depth) in sorted(all_positions.items()):
            f.write(f'    {hash_val}: ({score}, {move}, {depth}),\n')
        f.write('}\n')

    new_count = len(all_positions) - len(PRECOMPUTED_MOVES)

    # Print summary
    print(f"\n✓ Written {len(all_positions)} positions to {file_path}")
    if new_count > 0:
        print(f"  Added {new_count} new positions")

    # Reload module
    import importlib

    import Board_Evals.precomputed_moves
    importlib.reload(Board_Evals.precomputed_moves)

    return new_count
