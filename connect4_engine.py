#!/usr/bin/env python3
"""
Simplified Connect 4 Engine - combines parser and agent engine functionality.
Usage: python3 simple_engine.py <agent_class_name>
Example: python3 simple_engine.py MinimaxBot
"""

import sys
import struct
import os
from typing import List, Optional
from enum import IntEnum

# Add current directory to path for local imports
sys.path.append(os.path.dirname(__file__))


class Player(IntEnum):
    """Player enumeration."""
    PLAYER1 = ord('1')
    PLAYER2 = ord('2')


class GameBoard:
    """Optimized Connect 4 game board."""

    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.board = [[' ' for _ in range(self.cols)]
                      for _ in range(self.rows)]
        self.move_history = []
        # Track column heights for faster move validation
        self.column_heights = [0] * self.cols

    def make_move(self, column: int, player: Player) -> bool:
        """Make a move on the board."""
        if not (0 <= column < self.cols) or self.column_heights[column] >= self.rows:
            return False

        row = self.rows - 1 - self.column_heights[column]
        self.board[row][column] = chr(player)
        self.column_heights[column] += 1
        self.move_history.append((row, column))
        return True

    def is_valid_move(self, column: int) -> bool:
        """Check if a move is valid."""
        return 0 <= column < self.cols and self.column_heights[column] < self.rows

    def get_valid_moves(self) -> List[int]:
        """Get list of valid columns."""
        return [col for col in range(self.cols) if self.column_heights[col] < self.rows]

    def reconstruct_from_moves(self, moves: List[int]):
        """Reconstruct board state from list of moves."""
        self.board = [[' ' for _ in range(self.cols)]
                      for _ in range(self.rows)]
        self.move_history = []
        self.column_heights = [0] * self.cols

        for i, move in enumerate(moves):
            current_player = Player.PLAYER1 if i % 2 == 0 else Player.PLAYER2
            self.make_move(move, current_player)

    def check_win(self, player: Player) -> bool:
        """Check if player has won (4 in a row)."""
        symbol = chr(player)

        # Check horizontal
        for row in range(self.rows):
            for col in range(self.cols - 3):
                if (self.board[row][col] == symbol and
                    self.board[row][col+1] == symbol and
                    self.board[row][col+2] == symbol and
                        self.board[row][col+3] == symbol):
                    return True

        # Check vertical
        for row in range(self.rows - 3):
            for col in range(self.cols):
                if (self.board[row][col] == symbol and
                    self.board[row+1][col] == symbol and
                    self.board[row+2][col] == symbol and
                        self.board[row+3][col] == symbol):
                    return True

        # Check diagonal (top-left to bottom-right)
        for row in range(self.rows - 3):
            for col in range(self.cols - 3):
                if (self.board[row][col] == symbol and
                    self.board[row+1][col+1] == symbol and
                    self.board[row+2][col+2] == symbol and
                        self.board[row+3][col+3] == symbol):
                    return True

        # Check diagonal (top-right to bottom-left)
        for row in range(self.rows - 3):
            for col in range(3, self.cols):
                if (self.board[row][col] == symbol and
                    self.board[row+1][col-1] == symbol and
                    self.board[row+2][col-2] == symbol and
                        self.board[row+3][col-3] == symbol):
                    return True

        return False

    def is_full(self) -> bool:
        """Check if board is full."""
        return all(height >= self.rows for height in self.column_heights)

    def undo_last_move(self) -> bool:
        """Undo the last move made."""
        if not self.move_history:
            return False

        row, column = self.move_history.pop()
        self.board[row][column] = ' '
        self.column_heights[column] -= 1
        return True

    def print_board(self):
        """Print the Connect 4 board."""
        for row in range(self.rows):
            print("|", end="")
            for col in range(self.cols):
                piece = self.board[row][col]
                if piece == ' ':
                    print(" .", end="")
                elif piece == '1':
                    print(" X", end="")
                elif piece == '2':
                    print(" O", end="")
                else:
                    print(f" {piece}", end="")
            print(" |")
        print("|---------------|")
        print("  0 1 2 3 4 5 6")


class Bot:
    """Base class for Connect 4 bots."""

    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        """Calculate the best move for your bot."""
        raise NotImplementedError("Subclasses must implement calculate_move()")


class SimpleEngine:
    """Simplified engine that handles everything."""

    def __init__(self, agent_class_name: str):
        self.board = GameBoard()
        self.my_player = None
        self.time_per_move = 5000
        self.agent = self._create_agent(agent_class_name)

    def _create_agent(self, agent_class_name: str):
        """Dynamically create the specified agent."""
        if agent_class_name == "MinimaxBot":
            from Agents.minimax import MinimaxBot
            return MinimaxBot()
        elif agent_class_name == "IterativeDeepeningBot":
            from Agents.iterative_deepening import IterativeDeepeningBot
            return IterativeDeepeningBot()
        else:
            raise ValueError(f"Unknown agent class: {agent_class_name}")

    def _send_move(self, column: int):
        """Send a move response back to the engine."""
        header = struct.pack('<BH', 1, 4)  # MAKE_MOVE type, length 4
        column_byte = struct.pack('B', column)
        message = header + column_byte

        sys.stdout.buffer.write(message)
        sys.stdout.buffer.flush()

    def _handle_game_start(self, data: bytes):
        """Handle game start message."""
        # Skip header (3 bytes)
        offset = 3
        self.my_player = Player(data[offset])
        offset += 1

        self.time_per_move = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4

        num_moves = data[offset]
        offset += 1

        moves = list(data[offset:])

        print(f"Game starting! I am Player {chr(self.my_player)}")

        if num_moves > 0:
            self.board.reconstruct_from_moves(moves)
        else:
            self.board = GameBoard()

        self.board.print_board()

        # If I'm Player 1, make the first move immediately
        if self.my_player == Player.PLAYER1:
            our_move = self.agent.calculate_move(
                self.board, self.my_player, self.time_per_move)
            if our_move is not None and self.board.is_valid_move(our_move):
                self.board.make_move(our_move, self.my_player)
                print(f"I play column {our_move}")
                self.board.print_board()
                self._send_move(our_move)
            else:
                print("Invalid move calculated! Game forfeited.")
                sys.exit(1)

    def _handle_make_move(self, data: bytes):
        """Handle opponent's move and respond with our move."""
        opponent_move = data[3]  # Skip header, get column
        opponent = Player.PLAYER2 if self.my_player == Player.PLAYER1 else Player.PLAYER1

        print(f"Opponent moves to column {opponent_move}")

        if self.board.make_move(opponent_move, opponent):
            self.board.print_board()

        our_move = self.agent.calculate_move(
            self.board, self.my_player, self.time_per_move)

        if our_move is not None and self.board.is_valid_move(our_move):
            self.board.make_move(our_move, self.my_player)
            print(f"I play column {our_move}")
            self.board.print_board()
            self._send_move(our_move)
        else:
            print("Invalid move calculated! Game forfeited.")
            sys.exit(1)

    def run(self):
        """Main engine loop."""
        try:
            while True:
                # Read message header
                header_data = sys.stdin.buffer.read(3)
                if len(header_data) < 3:
                    break

                msg_type, msg_length = struct.unpack('<BH', header_data)

                # Read remaining message data
                remaining_data = sys.stdin.buffer.read(msg_length - 3)
                if len(remaining_data) < (msg_length - 3):
                    break

                full_message = header_data + remaining_data

                if msg_type == 0:  # GAME_START
                    self._handle_game_start(full_message)
                elif msg_type == 1:  # MAKE_MOVE
                    self._handle_make_move(full_message)
                else:
                    print(f"Unknown message type: {msg_type}", file=sys.stderr)
                    break

        except KeyboardInterrupt:
            print("Bot interrupted by user", file=sys.stderr)
        except Exception as e:
            print(f"Bot error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 connect4_engine.py <agent_class_name>")
        print("Available agents: MinimaxBot, IterativeDeepeningBot")
        sys.exit(1)

    agent_class_name = sys.argv[1]

    try:
        engine = SimpleEngine(agent_class_name)
        engine.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
