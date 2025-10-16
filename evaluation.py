#!/usr/bin/env python3
"""Board evaluation logic for Connect 4."""

from parser import GameBoard, Player
from typing import Optional

import numpy as np


class BoardEvaluator:
    """Handles evaluation of Connect 4 board positions."""

    # Scoring constants
    WIN_SCORE = float('inf')
    IMMEDIATE_THREAT_SCORE = 1_000
    BLOCK_THREAT_SCORE = 10_000
    FALLBACK_THREAT_SCORE = 250
    BUILD_THREAT_SCORE = 50
    FALLBACK_GAP_SCORE = 150
    FALLBACK_BUILD_SCORE = 5
    THREE_IN_ROW_SCORE = 20
    TWO_IN_ROW_SCORE = 2

    def evaluate_board(self, board: GameBoard, current_player: Optional[Player] = None) -> float:
        """Evaluate the current board state only.

        Args:
            board: The Connect 4 game board to evaluate
            current_player: The player whose turn it is (unused in simplified version)

        Returns:
            Score from Player 1's perspective (positive = good for Player 1)
        """
        # Check if either player has already won
        if board.check_win(Player.PLAYER1):
            return self.WIN_SCORE
        if board.check_win(Player.PLAYER2):
            return -self.WIN_SCORE

        # No winner yet, evaluate strategic position
        return self._evaluate_strategic_position(board)

    def evaluate_rows(self, board: np.ndarray) -> float:
        return sum(self._estimate_row(row) for row in board)

    def _estimate_row(self, row: np.ndarray) -> float:
        """Evaluate a single row using pattern matching."""
        row_str = ''.join(row)
        score = 0.0

        # Define pattern groups with their scores
        patterns = [
            # Blocking opponent threats
            (['1222', '2122', '2212', '2221'], self.BLOCK_THREAT_SCORE),
            (['2111', '1211', '1121', '1112'], -self.BLOCK_THREAT_SCORE),

            # Non-playable gaps
            (['1 11', '11 1'], self.FALLBACK_GAP_SCORE),
            (['2 22', '22 2'], -self.FALLBACK_GAP_SCORE),

            # Non-playable immediate threats
            ([' 111', '111 ', ' 111 '], self.FALLBACK_THREAT_SCORE),
            ([' 222', '222 ', ' 222 '], -self.FALLBACK_THREAT_SCORE),

            # Building threats with playable space
            (['P11P', 'P11', '11P'], self.BUILD_THREAT_SCORE),
            (['P22P', 'P22', '22P'], -self.BUILD_THREAT_SCORE),

            # Non-playable building threats
            ([' 11 ', ' 11', '11 '], self.FALLBACK_BUILD_SCORE),
            ([' 22 ', ' 22', '22 '], -self.FALLBACK_BUILD_SCORE),
        ]

        # Check patterns
        for pattern_list, pattern_score in patterns:
            if any(pattern in row_str for pattern in pattern_list):
                score += pattern_score

        # Basic accumulative patterns
        score += row_str.count('111') * self.THREE_IN_ROW_SCORE
        score -= row_str.count('222') * self.THREE_IN_ROW_SCORE
        score += row_str.count('11') * self.TWO_IN_ROW_SCORE
        score -= row_str.count('22') * self.TWO_IN_ROW_SCORE

        return score

    def _add_playable_markers(self, board: np.ndarray) -> np.ndarray:
        """Add 'P' markers to empty spaces that are playable."""
        board_copy = board.copy()

        for col in range(board.shape[1]):
            for row in range(board.shape[0]):
                if board[row][col] == ' ':
                    board_copy[row][col] = 'P'
                    break

        return board_copy

    def _evaluate_center_control(self, board: np.ndarray) -> float:
        """Reward controlling center columns."""
        center_weights = [0, 2, 4, 6, 4, 2, 0]
        score = 0.0

        for col in range(7):
            weight = center_weights[col]
            for row in range(6):
                if board[row][col] == '1':
                    score += weight
                elif board[row][col] == '2':
                    score -= weight

        return score

    def _evaluate_strategic_position(self, board: GameBoard) -> float:
        """Evaluate strategic positioning based on current board state."""
        b = np.array(board.board)
        b_with_playable = self._add_playable_markers(b)
        score = 0.0

        # Evaluate all directions
        score += self.evaluate_rows(b_with_playable)  # Rows
        score += self.evaluate_rows(b_with_playable.T)  # Columns
        # Diagonals
        score += self.evaluate_rows(self.get_diagonals(b_with_playable))
        # Anti-diagonals
        score += self.evaluate_rows(
            self.get_diagonals(np.fliplr(b_with_playable)))

        # Add center control bonus
        score += self._evaluate_center_control(b)

        return score

    def get_diagonals(self, arr: np.ndarray) -> list:
        """Get diagonals from numpy array where 4 in a row is possible."""
        return [arr.diagonal(offset=k) for k in range(-arr.shape[0] + 4, arr.shape[1]-3)]
