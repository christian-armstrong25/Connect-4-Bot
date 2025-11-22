"""Transposition table for caching evaluated positions."""
from typing import Optional, Tuple


class TranspositionTable:
    def __init__(self):
        # hash -> (score, depth, best_move)
        self.table: dict[int, Tuple[float, int, Optional[int]]] = {}

    def get(self, hash_key: int, depth: int, alpha: float, beta: float) -> Optional[Tuple[float, Optional[int]]]:
        """Get transposition table entry if depth is sufficient or bounds are valid."""
        entry = self.table.get(hash_key)
        if entry is None:
            return None

        score, entry_depth, best_move = entry
        if entry_depth >= depth or score >= beta or score <= alpha:
            return (score, best_move)

        return None

    def get_best_move(self, hash_key: int) -> Optional[int]:
        """Get best move for move ordering, even if depth is insufficient."""
        entry = self.table.get(hash_key)
        return entry[2] if entry else None

    def get_score(self, hash_key: int) -> Optional[float]:
        """Get score for move ordering, even if depth is insufficient."""
        entry = self.table.get(hash_key)
        return entry[0] if entry else None

    def store(self, hash_key: int, score: float, depth: int, best_move: Optional[int] = None) -> None:
        """Store entry only if depth is greater than or equal to existing entry."""
        existing = self.table.get(hash_key)
        if existing is None or depth >= existing[1]:
            self.table[hash_key] = (score, depth, best_move)

    def clear(self) -> None:
        self.table.clear()
