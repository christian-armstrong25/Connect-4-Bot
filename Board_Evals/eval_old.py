from connect4_engine import GameBoard, Player

class BoardEvaluator:
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
        if board.check_win(Player.PLAYER1):
            return self.WIN_SCORE
        if board.check_win(Player.PLAYER2):
            return -self.WIN_SCORE
        return self._evaluate_position(board)

    def _evaluate_position(self, board: GameBoard) -> float:
        p1_board, p2_board = board.boards
        playable_mask = self._get_playable_mask(p1_board, p2_board)
        p1_threats = self._count_threats(p1_board, p2_board, playable_mask)
        p2_threats = self._count_threats(p2_board, p1_board, playable_mask)
        return (p1_threats - p2_threats) * self.THREAT_SCORE

    def _get_playable_mask(self, p1_board: int, p2_board: int) -> int:
        mask = 0
        for col in range(7):
            for row in range(6):
                pos = row * 7 + col
                if not ((p1_board | p2_board) & (1 << pos)):
                    if row == 0 or ((p1_board | p2_board) & (1 << (pos - 7))):
                        mask |= 1 << pos
                    break
        return mask

    def _count_threats(self, player_board: int, opponent_board: int, playable_mask: int) -> int:
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
        return sum(1 for player_positions, gap_pos in self.PATTERNS
                   if self._matches_pattern(player_board, opponent_board, playable_mask,
                                            pos_func, player_positions, gap_pos))

    def _matches_pattern(self, player_board: int, opponent_board: int, playable_mask: int,
                         pos_func, player_positions: list, gap_position: int) -> bool:
        if any(not (player_board & (1 << pos_func(pos))) for pos in player_positions):
            return False
        gap_pos = pos_func(gap_position)
        return not ((player_board | opponent_board) & (1 << gap_pos))
