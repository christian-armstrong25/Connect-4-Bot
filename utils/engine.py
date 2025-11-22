import struct
import sys
from enum import IntEnum
from typing import Any, List, Optional


class Player(IntEnum):
    PLAYER1 = 1  # ('X')
    PLAYER2 = 2  # ('O')


class GameBoard:
    HEIGHT = 6
    WIDTH = 7
    MAX_MOVES = HEIGHT * WIDTH

    def __init__(self):
        self.move_count = 0
        self.position = 0  # Current player's pieces
        self.mask = 0      # All occupied cells
        self._current_player_in_position = Player.PLAYER1
        self.last_move: Optional[int] = None  # Last column played
        # Valid moves in center-first order: [3, 2, 4, 1, 5, 0, 6]
        self._valid_moves = [3, 2, 4, 1, 5, 0, 6]

    @staticmethod
    def _top_mask(col: int) -> int:
        return (1 << (GameBoard.HEIGHT - 1)) << col * (GameBoard.HEIGHT + 1)

    @staticmethod
    def _bottom_mask(col: int) -> int:
        return 1 << col * (GameBoard.HEIGHT + 1)

    def can_play(self, col: int) -> bool:
        return not (self.mask & self._top_mask(col))

    def get_valid_moves(self) -> List[int]:
        """Return cached valid moves in center-first order."""
        return self._valid_moves

    @property
    def boards(self):
        if self.move_count == 0:
            return [0, 0]
        if self._current_player_in_position == Player.PLAYER1:
            return [self.position, self.mask ^ self.position]
        return [self.mask ^ self.position, self.position]

    def __str__(self) -> str:
        """Return human-readable board representation."""
        p1_board, p2_board = self.boards
        result = []

        for row in range(self.HEIGHT - 1, -1, -1):
            line = ["|"]
            for col in range(self.WIDTH):
                pos = col * (self.HEIGHT + 1) + row
                bit = 1 << pos
                if p1_board & bit:
                    line.append(" X")
                elif p2_board & bit:
                    line.append(" O")
                else:
                    line.append(" .")
            line.append(" |")
            result.append("".join(line))

        result.append("|---------------|")
        result.append("  0 1 2 3 4 5 6")
        return "\n".join(result)

    def make_move(self, column: int, player: Player) -> bool:
        if not self.can_play(column):
            return False

        # Update mask to add piece at correct height
        new_mask = self.mask | (self.mask + self._bottom_mask(column))
        new_bit = new_mask & ~self.mask
        self.mask = new_mask

        # If different player, switch position first
        if self.move_count > 0 and self._current_player_in_position != player:
            self.position ^= self.mask
        # Add new piece to current player's position
        self.position |= new_bit

        self._current_player_in_position = player
        self.move_count += 1
        self.last_move = column

        # If column is now full, remove it from valid moves
        if not self.can_play(column) and column in self._valid_moves:
            self._valid_moves.remove(column)

        return True

    def undo_move(self, column: Optional[int] = None) -> None:
        self.move_count -= 1
        self.last_move = None

        # Find and remove the highest set bit in this column
        col_base = column * (self.HEIGHT + 1)
        col_mask = self.mask & ((1 << (self.HEIGHT + 1)) - 1) << col_base
        if col_mask:
            highest_bit = 1 << (col_mask.bit_length() - 1)
            self.mask &= ~highest_bit
            self.position &= ~highest_bit

        # Switch players back
        self.position ^= self.mask
        self._current_player_in_position = Player.PLAYER2 if self._current_player_in_position == Player.PLAYER1 else Player.PLAYER1

        # If column is now available, add it back to valid moves in center-first order
        if column is not None and self.can_play(column) and column not in self._valid_moves:
            CENTER_FIRST = [3, 2, 4, 1, 5, 0, 6]
            column_index = CENTER_FIRST.index(column)
            # Insert before the first move that comes after this column in center-first order
            for i, move in enumerate(self._valid_moves):
                if CENTER_FIRST.index(move) > column_index:
                    self._valid_moves.insert(i, column)
                    return
            # If no later move found, append to end
            self._valid_moves.append(column)

    def is_full(self) -> bool:
        return self.move_count >= self.MAX_MOVES

    def check_win(self, player: Player) -> bool:
        # if no one has even played 4 pieces, there cannot be a 4 in a row
        if self.move_count < 7:
            return False

        p1_board, p2_board = self.boards
        board = p1_board if player == Player.PLAYER1 else p2_board

        # Check diagonals first (most common wins)
        m = board & (board >> 6)
        if m & (m >> 12):
            return True

        m = board & (board >> 8)
        if m & (m >> 16):
            return True

        # Check horizontal
        m = board & (board >> 7)
        if m & (m >> 14):
            return True

        # Check vertical (least common)
        m = board & (board >> 1)
        return bool(m & (m >> 2))

    def reconstruct_from_moves(self, moves: List[int]) -> None:
        """Reset board and apply moves from the list."""
        self.position = 0
        self.mask = 0
        self.move_count = 0
        self._current_player_in_position = Player.PLAYER1
        self.last_move = None
        self._valid_moves = [3, 2, 4, 1, 5, 0, 6]

        for i, col in enumerate(moves):
            self.make_move(col, Player.PLAYER1 if i %
                           2 == 0 else Player.PLAYER2)


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
        """Create and return an AI agent instance."""
        from Agents.ids import IterativeDeepeningBot
        from Agents.minimax import MinimaxBot

        agents = {"MinimaxBot": MinimaxBot,
                  "IterativeDeepeningBot": IterativeDeepeningBot}
        if agent_class_name not in agents:
            raise ValueError(f"Unknown agent class: {agent_class_name}")
        return agents[agent_class_name](evaluator_name)

    def _send_move(self, column: int) -> None:
        """Send a move response via binary protocol to stdout."""
        sys.stdout.buffer.write(struct.pack('<BHB', 1, 4, column))
        sys.stdout.buffer.flush()

    def _handle_game_start(self, data: bytes) -> None:
        """Handle game start message (message type 0)."""
        self.my_player = Player.PLAYER1 if data[3] == ord(
            '1') else Player.PLAYER2
        self.time_per_move = struct.unpack('<I', data[4:8])[0]

        num_moves = data[8]
        moves = list(data[9:9+num_moves]) if num_moves > 0 else []
        self.board.reconstruct_from_moves(moves)

        if self.my_player == Player.PLAYER1:
            self._make_and_send_move()

    def _handle_make_move(self, data: bytes) -> None:
        """Handle opponent move notification (message type 1)."""
        opponent = Player.PLAYER2 if self.my_player == Player.PLAYER1 else Player.PLAYER1
        self.board.make_move(data[3], opponent)
        self._make_and_send_move()

    def _make_and_send_move(self) -> None:
        """Calculate the best move using the AI agent and send it."""
        move = self.agent.calculate_move(
            self.board, self.my_player, self.time_per_move)
        if move is None or not self.board.make_move(move, self.my_player):
            sys.exit(1)
        self._send_move(move)

    def run(self) -> None:
        """Main engine loop that processes incoming messages."""
        handlers = {0: self._handle_game_start, 1: self._handle_make_move}

        try:
            while True:
                header = sys.stdin.buffer.read(3)
                if len(header) < 3:
                    break

                msg_type, msg_length = struct.unpack('<BH', header)
                body = sys.stdin.buffer.read(msg_length - 3)
                if len(body) < (msg_length - 3) or msg_type not in handlers:
                    break

                handlers[msg_type](header + body)
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
