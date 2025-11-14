import struct
import sys
from enum import IntEnum
from typing import Any, List, Optional


class Player(IntEnum):
    PLAYER1 = 1  # ('X')
    PLAYER2 = 2  # ('O')


class GameBoard:
    """
    The board is represented as two 64-bit integers (bitboards), one for each player.
    Each bit represents a position on the 6x7 board, with bit 0 being the bottom-left
    corner and bits increasing left-to-right, then bottom-to-top.
    """
    # Valid board positions: bits 0-41 (42 bits total for 6x7 board)
    _VALID_MASK = (1 << 42) - 1
    # Horizontal: all rows (0-5), columns 0-3 (where 4-in-a-row can start)
    _HORIZONTAL_MASK = 0x78F1E3C78F & _VALID_MASK
    # Vertical: rows 0-2 (bits 0-20), all columns (where 4-in-a-row can start)
    _VERTICAL_MASK = 0x1FFFFF  # Bits 0-20 (rows 0-2), prevents row wrap
    # Diagonal down: rows 0-2, columns 0-3 (where 4-in-a-row can start)
    _DIAGONAL_DOWN_MASK = 0x3C78F & _VALID_MASK
    # Diagonal up: rows 0-2, columns 3-6 (where 4-in-a-row can start)
    _DIAGONAL_UP_MASK = 0x1E3C78 & _VALID_MASK

    def __init__(self):
        self.rows, self.cols = 6, 7
        self.heights = [0] * 7
        self.move_count = 0
        self.boards = [0, 0]  # [player1_bitboard, player2_bitboard]

    def __str__(self) -> str:
        """
        Create a human-readable string representation of the board.

        Returns:
            String showing the board with 'X' for Player 1, 'O' for Player 2,
            and '.' for empty spaces. Rows are displayed top to bottom.
        """
        # Pre-allocate list with known size (6 rows + separator + column numbers)
        result = [None] * (self.rows + 2)
        idx = 0

        # Iterate from top row to bottom row
        for row in range(self.rows - 1, -1, -1):
            line = ["|"]
            for col in range(self.cols):
                pos = row * 7 + col  # Calculate bit position
                bit = 1 << pos       # Create bit mask for this position
                if self.boards[0] & bit:
                    line.append(" X")  # Player 1
                elif self.boards[1] & bit:
                    line.append(" O")  # Player 2
                else:
                    line.append(" .")  # Empty
            line.append(" |")
            result[idx] = "".join(line)
            idx += 1

        # Add separator and column numbers
        result[idx] = "|---------------|"
        idx += 1
        result[idx] = "  0 1 2 3 4 5 6"
        return "\n".join(result)

    def make_move(self, column: int, player: Player) -> bool:
        # Check if move is valid
        if not (0 <= column < 7 and self.heights[column] < 6):
            return False

        # Calculate position in bitboard
        pos = self.heights[column] * 7 + column

        # Set bit for player bitboard
        self.boards[player - 1] |= 1 << pos

        # Update column height and move count
        self.heights[column] += 1
        self.move_count += 1

        return True

    def undo_move(self, column: int, player: Player) -> None:
        self.move_count -= 1
        self.heights[column] -= 1

        # Clear the bit for this player's board using bitwise AND with NOT
        pos = self.heights[column] * 7 + column
        self.boards[player - 1] &= ~(1 << pos)

    def is_full(self) -> bool:
        return self.move_count >= 42

    def check_win(self, player: Player) -> bool:
        # if no one has even played 4 pieces, there cannot be a 4 in a row
        if self.move_count < 7:
            return False

        board = self.boards[player - 1]

        # order matters, vertical wins are rare while diagonals are the most common

        # Check diagonal down (\): shift by 8 (move up-right: +1 row, +1 col)
        # Only check positions that can form valid diagonals (cols 0-3, rows 0-2)
        if board & (board >> 8) & (board >> 16) & (board >> 24) & self._DIAGONAL_DOWN_MASK:
            return True

        # Check diagonal up (/): shift by 6 (move up-left: +1 row, -1 col)
        # Only check positions that can form valid diagonals (cols 3-6, rows 0-2)
        if board & (board >> 6) & (board >> 12) & (board >> 18) & self._DIAGONAL_UP_MASK:
            return True

        # Check horizontal: shift by 1 (move right one column)
        # Check for 4 consecutive: board & (board>>1) & (board>>2) & (board>>3)
        if board & (board >> 1) & (board >> 2) & (board >> 3) & self._HORIZONTAL_MASK:
            return True

        # Check vertical: shift by 7 (move up one row)
        # Only check bottom 3 rows (rows 0-2) since that's where 4-in-a-row can start
        if board & (board >> 7) & (board >> 14) & (board >> 21) & self._VERTICAL_MASK:
            return True

        return False

    def reconstruct_from_moves(self, moves: List[int]) -> None:
        # Reset board to empty state
        self.boards = [0, 0]
        self.heights = [0] * 7
        self.move_count = 0

        # Apply each move, alternating players
        for i, move in enumerate(moves):
            current_player = Player.PLAYER1 if i % 2 == 0 else Player.PLAYER2
            self.make_move(move, current_player)


class SimpleEngine:
    """
    Connect 4 game engine that handles communication protocol and game flow.

    The engine communicates via binary protocol over stdin/stdout:
    - Message type 0: Game start (includes initial moves if any)
    - Message type 1: Opponent move notification

    The engine responds by sending the chosen move as a binary message.
    """

    def __init__(self, agent_class_name: str, evaluator_name: str = "old"):
        """
        Initialize the game engine with an AI agent.

        Args:
            agent_class_name: Name of the agent class ("MinimaxBot" or "IterativeDeepeningBot")
            evaluator_name: Name of the board evaluator ("old" or "new")
        """
        self.board = GameBoard()
        self.my_player: Optional[Player] = None
        self.time_per_move = 10
        self.agent = self._create_agent(agent_class_name, evaluator_name)

    def _create_agent(self, agent_class_name: str, evaluator_name: str) -> Any:
        """
        Create and return an AI agent instance.

        Args:
            agent_class_name: Name of the agent class to instantiate
            evaluator_name: Name of the board evaluator to use

        Returns:
            AI agent instance of the requested type

        Raises:
            ValueError: If agent_class_name is not recognized
        """
        from Agents.ids import IterativeDeepeningBot
        from Agents.minimax import MinimaxBot

        agents = {
            "MinimaxBot": MinimaxBot,
            "IterativeDeepeningBot": IterativeDeepeningBot
        }

        if agent_class_name not in agents:
            raise ValueError(f"Unknown agent class: {agent_class_name}")

        return agents[agent_class_name](evaluator_name)

    def _send_move(self, column: int) -> None:
        """
        Send a move response via binary protocol to stdout.

        Protocol format:
        - Header: 1 byte message type (1 = move), 2 bytes message length (little-endian)
        - Body: 1 byte column index (0-6)
        """
        header = struct.pack('<BH', 1, 4)  # Message type 1, length 4 bytes
        column_byte = struct.pack('B', column)  # Column as unsigned byte
        sys.stdout.buffer.write(header + column_byte)
        sys.stdout.buffer.flush()

    def _handle_game_start(self, data: bytes) -> None:
        """
        Handle game start message (message type 0).

        Message format:
        - Bytes 0-2: Header (already parsed)
        - Byte 3: Player number ('1' or '2')
        - Bytes 4-7: Time per move in milliseconds (unsigned int, little-endian)
        - Byte 8: Number of initial moves
        - Bytes 9+: Initial moves (column indices)
        """
        # Extract player number (byte 3)
        self.my_player = Player.PLAYER1 if data[3] == ord(
            '1') else Player.PLAYER2

        # Extract time limit (bytes 4-7, unsigned int)
        self.time_per_move = struct.unpack('<I', data[4:8])[0]

        # Extract initial moves if any
        num_moves = data[8]
        moves = list(data[9:9+num_moves]) if num_moves > 0 else []

        # Reconstruct board from initial moves
        if moves:
            self.board.reconstruct_from_moves(moves)
        else:
            # Reset board to empty state if no moves
            self.board.boards = [0, 0]
            self.board.heights = [0] * 7
            self.board.move_count = 0

        # If we're player 1, we move first
        if self.my_player == Player.PLAYER1:
            self._make_and_send_move()

    def _handle_make_move(self, data: bytes) -> None:
        """
        Handle opponent move notification (message type 1).

        Message format:
        - Bytes 0-2: Header (already parsed)
        - Byte 3: Column index of opponent's move
        """
        # Determine opponent and apply their move
        opponent = Player.PLAYER2 if self.my_player == Player.PLAYER1 else Player.PLAYER1
        opponent_column = data[3]
        self.board.make_move(opponent_column, opponent)

        # Calculate and send our response move
        self._make_and_send_move()

    def _make_and_send_move(self) -> None:
        """
        Calculate the best move using the AI agent and send it.

        Exits with error code 1 if move calculation fails or move is invalid.
        """
        move = self.agent.calculate_move(
            self.board, self.my_player, self.time_per_move
        )

        # Validate move
        if move is None or not self.board.make_move(move, self.my_player):
            sys.exit(1)

        self._send_move(move)

    def run(self) -> None:
        """
        Main engine loop that processes incoming messages.

        Continuously reads binary messages from stdin and handles them:
        - Message type 0: Game start
        - Message type 1: Opponent move

        Exits on EOF, invalid message, or exception.
        """
        try:
            handlers = {
                0: self._handle_game_start,
                1: self._handle_make_move
            }

            while True:
                # Read message header (3 bytes: 1 byte type + 2 bytes length)
                header_data = sys.stdin.buffer.read(3)
                if len(header_data) < 3:
                    break  # EOF or incomplete message

                # Parse header
                msg_type, msg_length = struct.unpack('<BH', header_data)

                # Read remaining message body
                remaining_data = sys.stdin.buffer.read(msg_length - 3)
                if len(remaining_data) < (msg_length - 3):
                    break  # Incomplete message

                # Route to appropriate handler
                if msg_type not in handlers:
                    break  # Unknown message type

                handlers[msg_type](header_data + remaining_data)

        except (KeyboardInterrupt, Exception):
            sys.exit(1)


def main() -> None:
    """
    Main entry point for the Connect 4 engine.

    Command line usage:
        python3 connect4_engine.py <agent_class_name> [evaluator_name]

    Arguments:
        agent_class_name: Name of the AI agent to use
                         Options: "MinimaxBot", "IterativeDeepeningBot"
        evaluator_name: Name of the board evaluator (optional, default: "old")
                       Options: "old", "new"

    Example:
        python3 connect4_engine.py IterativeDeepeningBot new
    """
    if not (2 <= len(sys.argv) <= 3):
        print(
            "Usage: python3 connect4_engine.py <agent_class_name> [evaluator_name]")
        print("Available agents: MinimaxBot, IterativeDeepeningBot")
        print("Available evaluators: old, new")
        sys.exit(1)

    try:
        agent_name = sys.argv[1]
        evaluator_name = sys.argv[2] if len(sys.argv) == 3 else "old"
        engine = SimpleEngine(agent_name, evaluator_name)
        engine.run()
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
