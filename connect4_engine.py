#!/usr/bin/env python3
"""Connect 4 Engine with bitboard representation."""

import struct
import sys
from enum import IntEnum
from typing import List


class Player(IntEnum):
    PLAYER1 = 1
    PLAYER2 = 2


class GameBoard:
    """Connect 4 game board using bitboards."""

    def __init__(self):
        self.rows, self.cols = 6, 7
        self.boards = [0, 0]  # [player1, player2]
        self.heights = [0] * 7  # Column heights for fast move validation
        self.move_count = 0

        # Precomputed masks for win detection
        self._win_masks = self._compute_win_masks()

    def __str__(self):
        """String representation of the board."""
        result = []
        for row in range(self.rows - 1, -1, -1):
            line = "|"
            for col in range(self.cols):
                pos = row * 7 + col
                if self.boards[0] & (1 << pos):
                    line += " X"
                elif self.boards[1] & (1 << pos):
                    line += " O"
                else:
                    line += " ."
            line += " |"
            result.append(line)
        result.append("|---------------|")
        result.append("  0 1 2 3 4 5 6")
        return "\n".join(result)

    def _compute_win_masks(self) -> List[int]:
        """Precompute all possible 4-in-a-row patterns."""
        masks = []
        patterns = [(0, 6, 0, 4, 0, 1), (0, 3, 0, 7, 1, 0),
                    (0, 3, 0, 4, 1, 1), (0, 3, 3, 7, 1, -1)]

        for row_start, row_end, col_start, col_end, row_delta, col_delta in patterns:
            for row in range(row_start, row_end):
                for col in range(col_start, col_end):
                    mask = 0
                    for i in range(4):
                        mask |= 1 << ((row + i * row_delta) *
                                      7 + col + i * col_delta)
                    masks.append(mask)
        return masks

    def make_move(self, column: int, player: Player) -> bool:
        """Make a move on the board."""
        if not self.is_valid_move(column):
            return False

        pos = self.heights[column] * 7 + column
        self.boards[player - 1] |= 1 << pos
        self.heights[column] += 1
        self.move_count += 1
        return True

    def is_valid_move(self, column: int) -> bool:
        """Check if a move is valid."""
        return 0 <= column < 7 and self.heights[column] < 6

    def get_valid_moves(self) -> List[int]:
        """Get valid columns ordered by center preference."""
        return [col for col in [3, 2, 4, 1, 5, 0, 6] if self.heights[col] < 6]

    def check_win(self, player: Player) -> bool:
        """Check if player has won."""
        board = self.boards[player - 1]
        return any((board & mask) == mask for mask in self._win_masks)

    def is_full(self) -> bool:
        """Check if board is full."""
        return self.move_count >= 42

    def undo_move(self, column: int, player: Player):
        """Undo a move."""
        self.heights[column] -= 1
        pos = self.heights[column] * 7 + column
        self.boards[player - 1] &= ~(1 << pos)
        self.move_count -= 1

    def reconstruct_from_moves(self, moves: List[int]):
        """Reconstruct board state from list of moves."""
        self.boards = [0, 0]
        self.heights = [0] * 7
        self.move_count = 0

        for i, move in enumerate(moves):
            current_player = Player.PLAYER1 if i % 2 == 0 else Player.PLAYER2
            self.make_move(move, current_player)


class Bot:
    """Base class for Connect 4 bots."""

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        raise NotImplementedError("Subclasses must implement calculate_move()")


class SimpleEngine:
    """Connect 4 engine."""

    def __init__(self, agent_class_name: str, evaluator_name: str = "old"):
        self.board = GameBoard()
        self.my_player = None
        self.time_per_move = 5000
        self.agent = self._create_agent(agent_class_name, evaluator_name)

    def _create_agent(self, agent_class_name: str, evaluator_name: str):
        """Create agent with evaluator selection."""
        from Agents.iterative_deepening import IterativeDeepeningBot
        from Agents.minimax import MinimaxBot
        agents = {"MinimaxBot": MinimaxBot,
                  "IterativeDeepeningBot": IterativeDeepeningBot}
        if agent_class_name not in agents:
            raise ValueError(f"Unknown agent class: {agent_class_name}")
        return agents[agent_class_name](evaluator_name)

    def _send_move(self, column: int):
        """Send move response."""
        header = struct.pack('<BH', 1, 4)
        column_byte = struct.pack('B', column)
        sys.stdout.buffer.write(header + column_byte)
        sys.stdout.buffer.flush()

    def _handle_game_start(self, data: bytes):
        """Handle game start message."""
        self.my_player = Player.PLAYER1 if data[3] == ord(
            '1') else Player.PLAYER2
        self.time_per_move = struct.unpack('<I', data[4:8])[0]
        num_moves = data[8]
        moves = list(data[9:9+num_moves]) if num_moves > 0 else []

        self.board = GameBoard()
        if moves:
            self.board.reconstruct_from_moves(moves)
        if self.my_player == Player.PLAYER1:
            self._make_and_send_move()

    def _handle_make_move(self, data: bytes):
        """Handle opponent's move and respond."""
        opponent = Player.PLAYER2 if self.my_player == Player.PLAYER1 else Player.PLAYER1
        self.board.make_move(data[3], opponent)
        self._make_and_send_move()

    def _make_and_send_move(self):
        """Make a move and send it."""
        move = self.agent.calculate_move(
            self.board, self.my_player, self.time_per_move)
        if move is None or not self.board.make_move(move, self.my_player):
            sys.exit(1)
        self._send_move(move)

    def run(self):
        """Main engine loop."""
        try:
            handlers = {0: self._handle_game_start, 1: self._handle_make_move}
            while True:
                header_data = sys.stdin.buffer.read(3)
                if len(header_data) < 3:
                    break
                msg_type, msg_length = struct.unpack('<BH', header_data)
                remaining_data = sys.stdin.buffer.read(msg_length - 3)
                if len(remaining_data) < (msg_length - 3):
                    break
                if msg_type not in handlers:
                    break
                handlers[msg_type](header_data + remaining_data)
        except (KeyboardInterrupt, Exception):
            sys.exit(1)


def main():
    if not (2 <= len(sys.argv) <= 3):
        print(
            "Usage: python3 connect4_engine.py <agent_class_name> [evaluator_name]")
        print("Available agents: MinimaxBot, IterativeDeepeningBot")
        print("Available evaluators: old, new")
        sys.exit(1)
    try:
        SimpleEngine(sys.argv[1], sys.argv[2] if len(
            sys.argv) == 3 else "old").run()
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
