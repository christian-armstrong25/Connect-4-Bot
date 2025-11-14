import random
import time

from Agents.iterative_deepening import IterativeDeepeningBot
from Agents.minimax import MinimaxBot
from engine import GameBoard, Player


def run_game(time_limit_ms: int = 25, randomize_start: bool = False, verbose: bool = True) -> str:
    board = GameBoard()
    agents = {
        Player.PLAYER1: MinimaxBot("old"),
        Player.PLAYER2: IterativeDeepeningBot("new")
    }

    # Randomize starting player for fairness
    if randomize_start and random.random() < 0.5:
        current_player = Player.PLAYER2
        if verbose: print("🎲 Random start: O (new) goes first\n")
    else:
        current_player = Player.PLAYER1
        if verbose: print("🎲 Random start: X (old) goes first\n")

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
            if verbose: print(f"⏰ {player_name} timed out after {elapsed_ms:.2f}ms (limit: {time_limit_ms}ms)")
            return "timeout"

        # Validate move
        if move is None or not board.make_move(move, current_player):
            if verbose: print(f"❌ Invalid move from {player_name}: {move}")
            return "error"

        # Display move and board
        if verbose: print(f"Move {move_count}: {player_name} -> Column {move} ({elapsed_ms:.2f}ms)\n{board}\n")

        # Check win
        if board.check_win(current_player):
            if verbose: print(f"🏆 {player_name} wins!")
            return player_name

        # Check draw
        if board.is_full():
            if verbose: print("🤝 Draw!")
            return "draw"

        # Switch players
        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1

    # Should never reach here, but return draw as fallback
    return "draw"


def main(time_limit_ms: int = 25, num_games: int = 1):
    if num_games == 1:
        result = run_game(time_limit_ms, randomize_start=False, verbose=True)
    else:
        # Run multiple games and collect statistics
        results = {"X (old)": 0, "O (new)": 0, "draw": 0,
                   "timeout": 0, "error": 0}

        print(
            f"Running {num_games} games with {time_limit_ms}ms time limit...\n")

        for game_num in range(1, num_games + 1):
            result = run_game(
                time_limit_ms, randomize_start=True, verbose=False)
            results[result] = results.get(result, 0) + 1

            if game_num % 10 == 0 or game_num == num_games:
                print(f"Game {game_num}/{num_games} completed...")

        # Display statistics
        print(f"\n{'='*50}")
        print(
            f"Tournament Results ({num_games} games, {time_limit_ms}ms per move)")
        print(f"{'='*50}")
        print(
            f"X (old) wins:  {results['X (old)']:3d} ({100*results['X (old)']/num_games:.1f}%)")
        print(
            f"O (new) wins:  {results['O (new)']:3d} ({100*results['O (new)']/num_games:.1f}%)")
        print(
            f"Draws:         {results['draw']:3d} ({100*results['draw']/num_games:.1f}%)")
        if results['timeout'] > 0:
            print(
                f"Timeouts:      {results['timeout']:3d} ({100*results['timeout']/num_games:.1f}%)")
        if results['error'] > 0:
            print(
                f"Errors:        {results['error']:3d} ({100*results['error']/num_games:.1f}%)")
        print(f"{'='*50}")


if __name__ == "__main__":
    import sys

    # python tournament_runner.py [time_limit_ms] [num_games]
    time_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    num_games = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    main(time_limit, num_games)
