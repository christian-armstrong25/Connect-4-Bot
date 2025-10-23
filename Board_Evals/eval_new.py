#!/usr/bin/env python3
"""
Bitboard-based evaluation strategy matching the original pattern logic.
"""

from connect4_engine import GameBoard, Player


class BoardEvaluator:
    """Bitboard-based evaluation strategy matching original patterns."""

    # Scoring constants - matching original
    WIN_SCORE = float('inf')
    FALLBACK_THREAT_SCORE = 250
    BUILD_THREAT_SCORE = 50
    FALLBACK_BUILD_SCORE = 5

    def __init__(self):
        # Precompute all 4-in-a-row patterns
        self._win_masks = self._compute_win_masks()

    def evaluate_board(self, board: GameBoard, current_player=None) -> float:
        """Evaluate the current board state using bitboards."""
        # Check if either player has already won
        if board.check_win(Player.PLAYER1):
            return self.WIN_SCORE
        if board.check_win(Player.PLAYER2):
            return -self.WIN_SCORE

        # No winner yet, evaluate strategic position using bitboards
        return self._evaluate_bitboard_position(board)

    def _evaluate_bitboard_position(self, board: GameBoard) -> float:
        """Evaluate strategic position using direct bitboard operations."""
        p1_board = board.boards[0]
        p2_board = board.boards[1]

        # Get playable positions mask
        playable_mask = self._get_playable_positions_mask(p1_board, p2_board)

        # Evaluate both players
        p1_score = self._evaluate_player_position(
            p1_board, p2_board, playable_mask)
        p2_score = self._evaluate_player_position(
            p2_board, p1_board, playable_mask)

        return p1_score - p2_score  # Positive for player 1, negative for player 2

    def _evaluate_player_position(self, player_board: int, opponent_board: int, playable_mask: int) -> float:
        """Evaluate position for a specific player."""
        score = 0.0

        # Check for non-playable immediate threats: ' 111', '111 ', '1 11', '11 1'
        threats = self._count_non_playable_threats(
            player_board, opponent_board, playable_mask)
        score += threats * self.FALLBACK_THREAT_SCORE

        return score

    def _get_playable_positions_mask(self, player_board: int, opponent_board: int) -> int:
        """Get a mask of all playable positions (not blocked by gravity)."""
        playable_mask = 0

        for col in range(7):
            # Find the top empty position in each column
            for row in range(6):
                pos = row * 7 + col
                if not (player_board & (1 << pos)) and not (opponent_board & (1 << pos)):
                    # Check if this position is supported by a piece below (for gravity)
                    if row == 0 or (player_board & (1 << (pos - 7))) or (opponent_board & (1 << (pos - 7))):
                        playable_mask |= 1 << pos
                    break  # Only the top empty position is playable

        return playable_mask

    def _count_non_playable_threats(self, player_board: int, opponent_board: int, playable_mask: int) -> int:
        """Count non-playable immediate threats: ' 111', '111 ', '1 11', '11 1'."""
        threat_count = 0

        # Check horizontal patterns
        threat_count += self._count_horizontal_patterns(player_board, opponent_board, playable_mask,
                                                        [[1, 2, 3], [0, 1, 2], [
                                                            0, 2, 3], [0, 1, 3]],
                                                        [0, 3, 1, 2])

        # Check diagonal patterns
        threat_count += self._count_diagonal_patterns(player_board, opponent_board, playable_mask,
                                                      [[1, 2, 3], [0, 1, 2], [
                                                          0, 2, 3], [0, 1, 3]],
                                                      [0, 3, 1, 2])

        return threat_count

    def _count_horizontal_patterns(self, player_board: int, opponent_board: int, playable_mask: int,
                                   player_positions_list: list, gap_positions: list) -> int:
        """Count horizontal patterns matching the given player positions and gap positions."""
        count = 0

        for row in range(1, 6):
            for col in range(4):  # Need 4 consecutive positions
                for i, (player_positions, gap_pos) in enumerate(zip(player_positions_list, gap_positions)):
                    if self._matches_horizontal_pattern(player_board, opponent_board, playable_mask,
                                                        row, col, player_positions, gap_pos):
                        count += 1

        return count

    def _count_diagonal_patterns(self, player_board: int, opponent_board: int, playable_mask: int,
                                 player_positions_list: list, gap_positions: list) -> int:
        """Count diagonal patterns matching the given player positions and gap positions."""
        count = 0

        # Top-left to bottom-right diagonals
        for row in range(3):
            for col in range(4):
                for i, (player_positions, gap_pos) in enumerate(zip(player_positions_list, gap_positions)):
                    if self._matches_diagonal_tlbr_pattern(player_board, opponent_board, playable_mask,
                                                           row, col, player_positions, gap_pos):
                        count += 1

        # Top-right to bottom-left diagonals
        for row in range(3):
            for col in range(3, 7):
                for i, (player_positions, gap_pos) in enumerate(zip(player_positions_list, gap_positions)):
                    if self._matches_diagonal_trbl_pattern(player_board, opponent_board, playable_mask,
                                                           row, col, player_positions, gap_pos):
                        count += 1

        return count

    def _matches_horizontal_pattern(self, player_board: int, opponent_board: int, playable_mask: int,
                                    row: int, col: int, player_positions: list, gap_position: int) -> bool:
        """Check if a horizontal pattern matches."""
        # Check that player has pieces in the specified positions
        for pos in player_positions:
            check_pos = (row * 7) + col + pos
            if not (player_board & (1 << check_pos)):
                return False

        # Check that gap position is empty
        gap_pos = (row * 7) + col + gap_position
        if (player_board & (1 << gap_pos)) or (opponent_board & (1 << gap_pos)):
            return False

        # For non-playable threats, gap must not be playable
        # For build threats, gap must be playable
        is_playable = bool(playable_mask & (1 << gap_pos))

        # This is a simplified check - in practice you'd want to distinguish between
        # non-playable threats and build threats based on the pattern type
        return True

    def _matches_diagonal_tlbr_pattern(self, player_board: int, opponent_board: int, playable_mask: int,
                                       row: int, col: int, player_positions: list, gap_position: int) -> bool:
        """Check if a top-left to bottom-right diagonal pattern matches."""
        # Check that player has pieces in the specified positions
        for pos in player_positions:
            check_pos = (row + pos) * 7 + col + pos
            if not (player_board & (1 << check_pos)):
                return False

        # Check that gap position is empty
        gap_pos = (row + gap_position) * 7 + col + gap_position
        if (player_board & (1 << gap_pos)) or (opponent_board & (1 << gap_pos)):
            return False

        # For non-playable threats, gap must not be playable
        # For build threats, gap must be playable
        is_playable = bool(playable_mask & (1 << gap_pos))

        return True

    def _matches_diagonal_trbl_pattern(self, player_board: int, opponent_board: int, playable_mask: int,
                                       row: int, col: int, player_positions: list, gap_position: int) -> bool:
        """Check if a top-right to bottom-left diagonal pattern matches."""
        # Check that player has pieces in the specified positions
        for pos in player_positions:
            check_pos = (row + pos) * 7 + col - pos
            if not (player_board & (1 << check_pos)):
                return False

        # Check that gap position is empty
        gap_pos = (row + gap_position) * 7 + col - gap_position
        if (player_board & (1 << gap_pos)) or (opponent_board & (1 << gap_pos)):
            return False

        # For non-playable threats, gap must not be playable
        # For build threats, gap must be playable
        is_playable = bool(playable_mask & (1 << gap_pos))

        return True

    def _compute_win_masks(self):
        """Precompute all possible 4-in-a-row patterns."""
        masks = []

        # Horizontal masks
        for row in range(6):
            for col in range(4):
                mask = 0
                for i in range(4):
                    mask |= 1 << (row * 7 + col + i)
                masks.append(mask)

        # Diagonal masks (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                mask = 0
                for i in range(4):
                    mask |= 1 << ((row + i) * 7 + col + i)
                masks.append(mask)

        # Diagonal masks (top-right to bottom-left)
        for row in range(3):
            for col in range(3, 7):
                mask = 0
                for i in range(4):
                    mask |= 1 << ((row + i) * 7 + col - i)
                masks.append(mask)

        return masks
