#!/usr/bin/env python3
"""Board evaluation logic for Connect 4."""

from connect4_engine import GameBoard, Player
from typing import Optional

import numpy as np


class BoardEvaluator:
    """Handles evaluation of Connect 4 board positions."""

    # Scoring constants
    WIN_SCORE = float('inf')
    BLOCK_THREAT_SCORE = 10_000
    FALLBACK_THREAT_SCORE = 250
    BUILD_THREAT_SCORE = 50
    FALLBACK_BUILD_SCORE = 5

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
            # Non-playable immediate threats
            ([' 111', '111 ', '1 11', '11 1'], self.FALLBACK_THREAT_SCORE),
            ([' 222', '222 ', '2 22', '22 2'], -self.FALLBACK_THREAT_SCORE),

            # Building threats with playable space
            (['P11', '11P'], self.BUILD_THREAT_SCORE),
            (['P22', '22P'], -self.BUILD_THREAT_SCORE),

            # Non-playable building threats
            ([' 11', '11 '], self.FALLBACK_BUILD_SCORE),
            ([' 22', '22 '], -self.FALLBACK_BUILD_SCORE),
        ]

        # Check patterns
        for pattern_list, pattern_score in patterns:
            if any(pattern in row_str for pattern in pattern_list):
                score += pattern_score

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
        """Evaluate center control."""
        center_cols = [2, 3, 4]
        score = 0.0

        for col in center_cols:
            for row in range(board.shape[0]):
                if board[row][col] == '1':
                    score += 1
                elif board[row][col] == '2':
                    score -= 1

        return score

    def _evaluate_strategic_position(self, board: GameBoard) -> float:
        """Evaluate the strategic position of the board."""
        # Convert board to numpy array for easier manipulation
        board_array = np.array(board.board)

        # Add playable markers
        board_with_markers = self._add_playable_markers(board_array)

        # Evaluate rows
        row_score = self.evaluate_rows(board_with_markers)

        # Evaluate columns
        col_score = self.evaluate_rows(board_with_markers.T)

        # Evaluate diagonals
        diag_score = self._evaluate_diagonals(board_with_markers)

        # Evaluate center control
        center_score = self._evaluate_center_control(board_array)

        return row_score + col_score + diag_score + center_score

    def _evaluate_diagonals(self, board: np.ndarray) -> float:
        """Evaluate diagonal patterns."""
        score = 0.0
        rows, cols = board.shape

        # Check diagonals (top-left to bottom-right)
        for i in range(rows - 3):
            for j in range(cols - 3):
                diag = [board[i+k][j+k] for k in range(4)]
                score += self._estimate_row(np.array(diag))

        # Check diagonals (top-right to bottom-left)
        for i in range(rows - 3):
            for j in range(3, cols):
                diag = [board[i+k][j-k] for k in range(4)]
                score += self._estimate_row(np.array(diag))

        return score
