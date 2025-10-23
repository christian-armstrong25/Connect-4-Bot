#!/usr/bin/env python3
"""
Bitboard-based evaluation strategy matching the original pattern logic.
"""

from connect4_engine import GameBoard, Player


class BoardEvaluator:
    """Bitboard-based evaluation strategy matching original patterns."""

    # Scoring constants
    WIN_SCORE = float('inf')
    THREAT_SCORE = 250

    # Pattern definitions: (player_positions, gap_position)
    PATTERNS = [
        ([1, 2, 3], 0),  # ' 111'
        ([0, 1, 2], 3),  # '111 '
        ([0, 2, 3], 1),  # '1 11'
        ([0, 1, 3], 2),  # '11 1'
    ]

    def evaluate_board(self, board: GameBoard, current_player=None) -> float:
        """Evaluate the current board state."""
        if board.check_win(Player.PLAYER1):
            return self.WIN_SCORE
        if board.check_win(Player.PLAYER2):
            return -self.WIN_SCORE

        return self._evaluate_position(board)

    def _evaluate_position(self, board: GameBoard) -> float:
        """Evaluate strategic position using bitboards."""
        p1_board, p2_board = board.boards
        playable_mask = self._get_playable_mask(p1_board, p2_board)

        p1_threats = self._count_threats(p1_board, p2_board, playable_mask)
        p2_threats = self._count_threats(p2_board, p1_board, playable_mask)

        return float((p1_threats - p2_threats) * self.THREAT_SCORE)

    def _get_playable_mask(self, p1_board: int, p2_board: int) -> int:
        """Get mask of playable positions (not blocked by gravity)."""
        mask = 0
        for col in range(7):
            for row in range(6):
                pos = row * 7 + col
                if not (p1_board & (1 << pos)) and not (p2_board & (1 << pos)):
                    if row == 0 or (p1_board & (1 << (pos - 7))) or (p2_board & (1 << (pos - 7))):
                        mask |= 1 << pos
                    break
        return mask

    def _count_threats(self, player_board: int, opponent_board: int, playable_mask: int) -> int:
        """Count all threat patterns for a player."""
        count = 0

        # Horizontal patterns
        for row in range(1, 6):
            for col in range(4):
                count += self._count_patterns_at_position(
                    player_board, opponent_board, playable_mask,
                    lambda pos: (row * 7) + col + pos, row, col
                )

        # Diagonal TL-BR patterns
        for row in range(3):
            for col in range(4):
                count += self._count_patterns_at_position(
                    player_board, opponent_board, playable_mask,
                    lambda pos: (row + pos) * 7 + col + pos, row, col
                )

        # Diagonal TR-BL patterns
        for row in range(3):
            for col in range(3, 7):
                count += self._count_patterns_at_position(
                    player_board, opponent_board, playable_mask,
                    lambda pos: (row + pos) * 7 + col - pos, row, col
                )

        return count

    def _count_patterns_at_position(self, player_board: int, opponent_board: int,
                                    playable_mask: int, pos_func, row: int, col: int) -> int:
        """Count patterns at a specific position using the given position function."""
        count = 0
        for player_positions, gap_pos in self.PATTERNS:
            if self._matches_pattern(player_board, opponent_board, playable_mask,
                                     pos_func, player_positions, gap_pos):
                count += 1
        return count

    def _matches_pattern(self, player_board: int, opponent_board: int, playable_mask: int,
                         pos_func, player_positions: list, gap_position: int) -> bool:
        """Check if a pattern matches at the given position."""
        # Check player has pieces in specified positions
        for pos in player_positions:
            check_pos = pos_func(pos)
            if not (player_board & (1 << check_pos)):
                return False

        # Check gap position is empty
        gap_pos = pos_func(gap_position)
        if (player_board & (1 << gap_pos)) or (opponent_board & (1 << gap_pos)):
            return False

        return True
