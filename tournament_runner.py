#!/usr/bin/env python3
"""Ultra-simplified tournament runner for Connect 4 agents."""

import argparse
import sys
import os
from connect4_engine import GameBoard, Player

sys.path.append(os.path.dirname(__file__))


def parse_player_spec(player_spec: str) -> tuple:
    """Parse player specification like 'MinimaxBot:old' into (agent, evaluator)."""
    if ':' in player_spec:
        agent, evaluator = player_spec.split(':', 1)
        return agent.strip(), evaluator.strip()
    else:
        return player_spec.strip(), "old"


def run_game(player1_spec: str, player2_spec: str, time_limit_ms: int = 25, verbose: bool = True) -> str:
    """Run a single game between two bots."""
    # Parse player specifications
    player1_type, eval1 = parse_player_spec(player1_spec)
    player2_type, eval2 = parse_player_spec(player2_spec)

    # Create agents
    if player1_type == "MinimaxBot":
        from Agents.minimax import MinimaxBot
        agent1 = MinimaxBot(eval1)
    elif player1_type == "IterativeDeepeningBot":
        from Agents.iterative_deepening import IterativeDeepeningBot
        agent1 = IterativeDeepeningBot(eval1)
    else:
        raise ValueError(f"Unknown agent: {player1_type}")

    if player2_type == "MinimaxBot":
        from Agents.minimax import MinimaxBot
        agent2 = MinimaxBot(eval2)
    elif player2_type == "IterativeDeepeningBot":
        from Agents.iterative_deepening import IterativeDeepeningBot
        agent2 = IterativeDeepeningBot(eval2)
    else:
        raise ValueError(f"Unknown agent: {player2_type}")

    # Initialize game
    board = GameBoard()
    current_player = Player.PLAYER1
    move_count = 0

    if verbose:
        print(f"\n🎮 {player1_spec} vs {player2_spec}")

    while move_count < 42:
        # Get current agent
        agent = agent1 if current_player == Player.PLAYER1 else agent2

        # Calculate move
        move = agent.calculate_move(board, current_player, time_limit_ms)

        if move is None or not board.make_move(move, current_player):
            if verbose:
                print(f"❌ Invalid move from {agent.__class__.__name__}")
            return "error"

        move_count += 1

        if verbose:
            player_name = player1_spec if current_player == Player.PLAYER1 else player2_spec
            print(f"Move {move_count}: {player_name} -> Column {move}")
            print(f"{board}")

        # Check win
        if board.check_win(current_player):
            winner = player1_spec if current_player == Player.PLAYER1 else player2_spec
            if verbose:
                print(f"🏆 {winner} wins!")
            return winner

        # Check draw
        if board.is_full():
            if verbose:
                print("🤝 Draw!")
            return "draw"

        # Switch players
        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1

    return "draw"


def run_tournament(player1: str, player2: str, games: int = 1, time_limit_ms: int = 25, verbose: bool = True):
    """Run a tournament between two players."""
    wins = {player1: 0, player2: 0, "draw": 0, "error": 0}

    if verbose:
        print(
            f"\n🏆 Tournament: {player1} vs {player2} ({games} games, {time_limit_ms}ms per move)")

    for game_num in range(1, games + 1):
        # Alternate first move
        if game_num % 2 == 0:
            result = run_game(player2, player1, time_limit_ms, verbose)
            if result == player1:
                result = player2
            elif result == player2:
                result = player1
        else:
            result = run_game(player1, player2, time_limit_ms, verbose)

        wins[result] += 1

        if verbose:
            print(f"Game {game_num}: {result}")

    # Print results
    print(f"\n📊 Final Results:")
    print(f"{player1}: {wins[player1]} wins")
    print(f"{player2}: {wins[player2]} wins")
    print(f"Draws: {wins['draw']}")
    print(f"Errors: {wins['error']}")

    if wins[player1] > wins[player2]:
        print(f"🏆 {player1} wins the tournament!")
    elif wins[player2] > wins[player1]:
        print(f"🏆 {player2} wins the tournament!")
    else:
        print("🤝 Tournament is a tie!")


def main():
    parser = argparse.ArgumentParser(description="Connect 4 Tournament Runner")
    parser.add_argument("--player1", "-p1", required=True,
                        help="Player 1 specification (format: 'BotType:evaluator', e.g., 'MinimaxBot:old')")
    parser.add_argument("--player2", "-p2", required=True,
                        help="Player 2 specification (format: 'BotType:evaluator', e.g., 'IterativeDeepeningBot:new')")
    parser.add_argument("--games", "-g", type=int,
                        default=1, help="Number of games")
    parser.add_argument("--time", "-t", type=int, default=25,
                        help="Time limit per move in milliseconds (default: 25)")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    run_tournament(args.player1, args.player2,
                   args.games, args.time, not args.quiet)


if __name__ == "__main__":
    main()
