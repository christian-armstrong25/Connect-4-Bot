"""Zobrist hashing for Connect 4 board positions."""
import random
from typing import Optional

from engine import GameBoard, Player


class ZobristHasher:
    def __init__(self, seed: Optional[int] = None):
        rng = random.Random(seed)
        # Flattened table: [player][col][row] -> table[(player-1)*stride + col*HEIGHT + row]
        self.table = [rng.getrandbits(64) for _ in range(
            2 * GameBoard.WIDTH * GameBoard.HEIGHT)]
        self.player_to_move_hash = rng.getrandbits(64)
        self.table_stride = GameBoard.WIDTH * GameBoard.HEIGHT

    def compute_hash(self, board: GameBoard) -> int:
        """Compute hash by XORing table entries for all pieces on the board."""
        hash_value = 0
        p1_board, p2_board = board.boards

        for col in range(GameBoard.WIDTH):
            for row in range(GameBoard.HEIGHT):
                pos = col * (GameBoard.HEIGHT + 1) + row
                bit = 1 << pos
                table_idx = col * GameBoard.HEIGHT + row

                if p1_board & bit:
                    hash_value ^= self.table[table_idx]
                elif p2_board & bit:
                    hash_value ^= self.table[self.table_stride + table_idx]

        if board.move_count % 2 == 1:
            hash_value ^= self.player_to_move_hash

        return hash_value

    def update_hash(self, hash_value: int, col: int, row: int, player: Player) -> int:
        """Update hash incrementally for a move: XOR piece position and switch player."""
        table_idx = (player - 1) * self.table_stride + \
            col * GameBoard.HEIGHT + row
        return hash_value ^ self.table[table_idx] ^ self.player_to_move_hash


_hasher: Optional[ZobristHasher] = None


def get_hasher(seed: Optional[int] = None) -> ZobristHasher:
    global _hasher
    if _hasher is None:
        _hasher = ZobristHasher(seed)
    return _hasher
