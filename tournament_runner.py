"""
Tournament Runner

A simple script to run a game between two AI agents for testing and comparison.
Displays the game progress and determines the winner.
"""

import time
from Agents.iterative_deepening import IterativeDeepeningBot
from Agents.minimax import MinimaxBot
from connect4_engine import GameBoard, Player


def main(time_limit_ms: int = 25) -> str:
    # Set up agents for each player
    # Player 1 uses "old" evaluator, Player 2 uses "new" evaluator
    agents = {
        Player.PLAYER1: IterativeDeepeningBot("old"),
        Player.PLAYER2: IterativeDeepeningBot("new")
    }

    board = GameBoard()
    current_player = Player.PLAYER1

    # Maximum 42 moves in Connect 4 (6 rows * 7 columns)
    for move_count in range(1, 43):
        agent = agents[current_player]
        player_name = "X (old)" if current_player == Player.PLAYER1 else "O (new)"

        # Calculate move and measure time
        start_time = time.perf_counter()
        move = agent.calculate_move(board, current_player, time_limit_ms)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Check for timeout
        if elapsed_ms > time_limit_ms:
            print(f"⏰ {player_name} timed out after {elapsed_ms:.0f}ms")
            return "timeout"

        # Validate move
        if move is None or not board.make_move(move, current_player):
            print(f"❌ Invalid move from {agent.__class__.__name__}")
            return "error"

        # Display move and board
        print(f"Move {move_count}: {player_name} -> Column {move}\n{board}")

        # Check win
        if board.check_win(current_player):
            print(f"🏆 {player_name} wins!")
            return player_name

        # Check draw
        if board.is_full():
            print("🤝 Draw!")
            return "draw"

        # Switch players
        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1

    # Should never reach here, but return draw as fallback
    return "draw"


if __name__ == "__main__":
    main()
