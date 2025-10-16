#!/usr/bin/env python3
"""
Connect 4 Protocol Parser - handles all message parsing and game state.
"""

import random
import sys
import struct
from enum import IntEnum
from typing import NamedTuple, List, Optional


class Player(IntEnum):
    """Player enumeration as specified in the protocol."""
    PLAYER1 = ord('1')  # ASCII '1'
    PLAYER2 = ord('2')  # ASCII '2'


class MessageType(IntEnum):
    """Message type enumeration as specified in the protocol."""
    START_GAME = 0
    MAKE_MOVE = 1


class MessageHeader(NamedTuple):
    """Message header structure."""
    type: MessageType
    message_length: int


class GameStart(NamedTuple):
    """GameStart message structure."""
    header: MessageHeader
    your_player: Player
    time_per_move: int
    num_moves_made: int
    moves_made: List[int]


class MakeMove(NamedTuple):
    """MakeMove message structure."""
    header: MessageHeader
    column: int


class GameBoard:
    """Handles Connect 4 game board logic."""

    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.board = None
        self.move_history = []  # Track moves for undo
        self.initialize_board()

    def initialize_board(self):
        """Initialize empty board."""
        self.board = [[' ' for _ in range(self.cols)]
                      for _ in range(self.rows)]

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

    def make_move(self, column, player):
        """Make a move on the board."""
        if not (0 <= column < self.cols):
            return False

        for row in range(self.rows - 1, -1, -1):
            if self.board[row][column] == ' ':
                self.board[row][column] = chr(player)
                self.move_history.append((row, column))  # Track the move
                return True
        return False

    def is_valid_move(self, column):
        """Check if a move is valid."""
        return 0 <= column < self.cols and self.board[0][column] == ' '

    def get_valid_moves(self):
        """Get list of valid columns."""
        return [col for col in range(self.cols) if self.is_valid_move(col)]

    def reconstruct_from_moves(self, moves):
        """Reconstruct board state from list of moves."""
        self.initialize_board()

        for i, move in enumerate(moves):
            current_player = Player.PLAYER1 if i % 2 == 0 else Player.PLAYER2
            if not self.make_move(move, current_player):
                print(f"Warning: Could not place move {move} - column full")

    def check_win(self, player):
        """Check if player has won (4 in a row)."""
        symbol = chr(player)

        # Check horizontal
        for row in range(self.rows):
            for col in range(self.cols - 3):
                if all(self.board[row][col+i] == symbol for i in range(4)):
                    return True

        # Check vertical
        for row in range(self.rows - 3):
            for col in range(self.cols):
                if all(self.board[row+i][col] == symbol for i in range(4)):
                    return True

        # Check diagonal (top-left to bottom-right)
        for row in range(self.rows - 3):
            for col in range(self.cols - 3):
                if all(self.board[row+i][col+i] == symbol for i in range(4)):
                    return True

        # Check diagonal (top-right to bottom-left)
        for row in range(self.rows - 3):
            for col in range(3, self.cols):
                if all(self.board[row+i][col-i] == symbol for i in range(4)):
                    return True

        return False

    def is_full(self):
        """Check if board is full."""
        return all(self.board[0][col] != ' ' for col in range(self.cols))

    def undo_last_move(self):
        """Undo the last move made."""
        if not self.move_history:
            return False

        row, column = self.move_history.pop()
        self.board[row][column] = ' '
        return True


class BoardHasher:
    """Zobrist hasher for Connect 4 boards."""

    def __init__(self, rows=6, cols=7):
        # 2 players, random 64-bit integers
        self.R = [[[random.getrandbits(64) for _ in range(2)]
                   for _ in range(cols)] for _ in range(rows)]

    def hash(self, board):
        """Return a 64-bit Zobrist hash of the board."""
        h = 0
        for r in range(board.rows):
            for c in range(board.cols):
                piece = board.board[r][c]
                if piece == '1':
                    h ^= self.R[r][c][0]
                elif piece == '2':
                    h ^= self.R[r][c][1]
        return h

class Bot:
    """Base class for Connect 4 bots. Override calculate_move() to implement your AI."""

    def calculate_move(self, board: GameBoard, your_player: Player, time_per_move: int) -> int:
        """
        Calculate the best move for your bot.

        Args:
            board: Current game board state
            your_player: Your player (Player.PLAYER1 or Player.PLAYER2)
            time_per_move: Time limit per move in milliseconds

        Returns:
            Column number (0-6) where you want to place your piece
        """
        raise NotImplementedError("Subclasses must implement calculate_move()")


class MessageHandler:
    """Handles all protocol communication and game state management."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.game_board = GameBoard()
        self.your_player = None
        self.time_per_move = None

    def run(self):
        """Main loop - handles all messages from stdin and sends responses."""
        try:
            while True:
                message_data = self._read_message()
                if message_data is None:
                    break

                message = self._parse_message(message_data)
                self._handle_message(message)

        except KeyboardInterrupt:
            print("Bot interrupted by user", file=sys.stderr)
        except Exception as e:
            print(f"Bot error: {e}", file=sys.stderr)
            sys.exit(1)

    def _read_message(self) -> Optional[bytes]:
        """Read a complete message from stdin."""
        header_bytes = sys.stdin.buffer.read(3)
        if len(header_bytes) < 3:
            return None

        msg_type, msg_length = struct.unpack('<BH', header_bytes)
        remaining_bytes = sys.stdin.buffer.read(msg_length - 3)
        if len(remaining_bytes) < (msg_length - 3):
            return None

        return header_bytes + remaining_bytes

    def _parse_header(self, data: bytes) -> MessageHeader:
        """Parse message header from bytes."""
        msg_type, msg_length = struct.unpack('<BH', data[:3])
        return MessageHeader(
            type=MessageType(msg_type),
            message_length=msg_length
        )

    def _parse_game_start(self, data: bytes) -> GameStart:
        """Parse GameStart message from bytes."""
        header = self._parse_header(data[:3])

        offset = 3
        your_player = Player(data[offset])
        offset += 1

        time_per_move = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4

        num_moves_made = data[offset]
        offset += 1

        moves_made = list(data[offset:])

        return GameStart(
            header=header,
            your_player=your_player,
            time_per_move=time_per_move,
            num_moves_made=num_moves_made,
            moves_made=moves_made
        )

    def _parse_make_move(self, data: bytes) -> MakeMove:
        """Parse MakeMove message from bytes."""
        header = self._parse_header(data[:3])
        column = data[3]

        return MakeMove(
            header=header,
            column=column
        )

    def _parse_message(self, data: bytes):
        """Parse any message type based on the header."""
        header = self._parse_header(data)

        if header.type == MessageType.START_GAME:
            return self._parse_game_start(data)
        elif header.type == MessageType.MAKE_MOVE:
            return self._parse_make_move(data)
        else:
            raise ValueError(f"Unknown message type: {header.type}")

    def _handle_message(self, message):
        """Handle parsed messages."""
        if isinstance(message, GameStart):
            self._handle_game_start(message)
        elif isinstance(message, MakeMove):
            self._handle_make_move(message)

    def _handle_game_start(self, message: GameStart):
        """Handle game start message."""
        self.your_player = message.your_player
        self.time_per_move = message.time_per_move

        print(f"Game starting! I am Player {chr(self.your_player)}")

        if message.num_moves_made > 0:
            self.game_board.reconstruct_from_moves(message.moves_made)
        else:
            self.game_board.initialize_board()

        self.game_board.print_board()

    def _handle_make_move(self, message: MakeMove):
        """Handle opponent's move and respond with our move."""
        opponent = Player.PLAYER2 if self.your_player == Player.PLAYER1 else Player.PLAYER1

        print(f"Opponent moves to column {message.column}")

        if self.game_board.make_move(message.column, opponent):
            self.game_board.print_board()

        our_move = self.bot.calculate_move(
            self.game_board, self.your_player, self.time_per_move)

        if our_move is not None and self.game_board.is_valid_move(our_move):
            self.game_board.make_move(our_move, self.your_player)
            print(f"I play column {our_move}")
            self.game_board.print_board()
            self._send_move(our_move)
        else:
            print("Invalid move calculated! Game forfeited.")
            sys.exit(1)

    def _send_move(self, column: int):
        """Send a move response back to the engine."""
        header = struct.pack('<BH', MessageType.MAKE_MOVE, 4)
        column_byte = struct.pack('B', column)
        message = header + column_byte

        sys.stdout.buffer.write(message)
        sys.stdout.buffer.flush()


def run_bot(bot: Bot):
    """Run a bot with the message handler."""
    handler = MessageHandler(bot)
    handler.run()
