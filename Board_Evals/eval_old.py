from connect4_engine import GameBoard, Player


class BoardEvaluator:
    # Pattern definitions: (player_positions, gap_position)
    PATTERNS = [
        ((1, 2, 3), 0),  # ' 111'
        ((0, 1, 2), 3),  # '111 '
        ((0, 2, 3), 1),  # '1 11'
        ((0, 1, 3), 2),  # '11 1'
    ]

    def evaluate_board(self, board: GameBoard) -> float:
        p1_board, p2_board = board.boards

        # Precompute occupied positions (used multiple times, so cache it)
        occupied = p1_board | p2_board

        # Count threats for both players
        p1_threats = self._count_threats(p1_board, occupied)
        p2_threats = self._count_threats(p2_board, occupied)
        return (p1_threats - p2_threats)

    def _count_threats(self, player_board: int, occupied: int) -> int:
        count = 0

        # Check horizontal threats (rows 1-5, columns 0-3)
        # We check 4 consecutive positions, so we can start from column 0-3
        for row in range(1, 6):  # Skip row 0 (bottom) - threats there aren't useful
            row_base = row * 7
            for col in range(4):  # Can fit 4 positions starting from col 0-3
                base_pos = row_base + col
                count += self._count_patterns_horizontal(
                    player_board, occupied, base_pos
                )

        # Check diagonal down threats (\): top-left to bottom-right
        # Need at least 3 rows and 4 columns to fit a diagonal pattern
        for row in range(3):  # Can fit 4 positions starting from rows 0-2
            for col in range(4):  # Can fit 4 positions starting from cols 0-3
                base_pos = row * 7 + col
                count += self._count_patterns_diagonal_down(
                    player_board, occupied, base_pos
                )

        # Check diagonal up threats (/): top-right to bottom-left
        # Need at least 3 rows, and columns must start from 3-6 (to fit pattern going left)
        for row in range(3):  # Can fit 4 positions starting from rows 0-2
            for col in range(3, 7):  # Can fit 4 positions starting from cols 3-6
                base_pos = row * 7 + col
                count += self._count_patterns_diagonal_up(
                    player_board, occupied, base_pos
                )

        return count

    def _count_patterns_horizontal(self, player_board: int, occupied: int, base_pos: int) -> int:
        """Count patterns in horizontal direction."""
        count = 0

        for player_positions, gap_pos in self.PATTERNS:
            # Build bitmask of all player piece positions for this pattern
            player_bits = 0
            for pos_offset in player_positions:
                player_bits |= 1 << (base_pos + pos_offset)

            # Get bit position of the gap
            gap_bit = 1 << (base_pos + gap_pos)

            # Check if pattern matches:
            # 1. All player positions have pieces (player_board & player_bits == player_bits)
            # 2. Gap position is empty (not in occupied)
            if (player_board & player_bits) == player_bits and not (occupied & gap_bit):
                count += 1

        return count

    def _count_patterns_diagonal_down(self, player_board: int, occupied: int, base_pos: int) -> int:
        """Count patterns in diagonal down direction (top-left to bottom-right)."""
        count = 0

        for player_positions, gap_pos in self.PATTERNS:
            # Build bitmask: each step moves 8 bits (1 row + 1 column)
            player_bits = 0
            for pos_offset in player_positions:
                player_bits |= 1 << (base_pos + pos_offset * 8)

            gap_bit = 1 << (base_pos + gap_pos * 8)

            # Check if pattern matches
            if (player_board & player_bits) == player_bits and not (occupied & gap_bit):
                count += 1

        return count

    def _count_patterns_diagonal_up(self, player_board: int, occupied: int, base_pos: int) -> int:
        """Count patterns in diagonal up direction (top-right to bottom-left)."""
        count = 0

        for player_positions, gap_pos in self.PATTERNS:
            # Build bitmask: each step moves 6 bits (1 row - 1 column)
            player_bits = 0
            for pos_offset in player_positions:
                player_bits |= 1 << (base_pos + pos_offset * 6)

            gap_bit = 1 << (base_pos + gap_pos * 6)

            # Check if pattern matches
            if (player_board & player_bits) == player_bits and not (occupied & gap_bit):
                count += 1

        return count