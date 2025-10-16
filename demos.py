#!/usr/bin/env python3
"""
Interactive demos for Connect 4 bot.
"""

import random
from parser import Bot, GameBoard, Player

from Agents.iterative_deepening import IterativeDeepeningBot
from Agents.minimax import MinimaxBot

TestBot = MinimaxBot


def get_human_move(game_board):
    """Get a valid move from the human player."""
    while True:
        try:
            move = input("Enter column (0-6): ").strip()
            if move.lower() in ['q', 'quit', 'exit']:
                return None

            col = int(move)
            if col < 0 or col > 6:
                print("Column must be between 0 and 6")
                continue

            if not game_board.is_valid_move(col):
                print("Column is full! Choose another column.")
                continue

            return col

        except ValueError:
            print("Please enter a valid number (0-6) or 'q' to quit")


def bot_vs_bot_game():
    """Run a game between two simple bots."""
    print("🤖 Bot vs Bot Game")
    print("=" * 50)

    bot1 = IterativeDeepeningBot()
    bot2 = MinimaxBot()
    game_board = GameBoard()

    print("Starting game...")
    game_board.print_board()

    current_player = Player.PLAYER1
    move_count = 0
    max_moves = 42

    while move_count < max_moves:
        if current_player == Player.PLAYER1:
            bot = bot1
            symbol = "X"
        else:
            bot = bot2
            symbol = "O"

        print(f"\nPlayer {symbol}'s turn...")

        move = bot.calculate_move(game_board, current_player, 1000)
        if move is None:
            print("No valid moves left - game over!")
            break

        game_board.make_move(move, current_player)
        print(f"Player {symbol} plays column {move}")
        game_board.print_board()

        if game_board.check_win(current_player):
            print(f"\n🎉 Player {symbol} wins!")
            break

        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1
        move_count += 1

    if move_count >= max_moves:
        print("\n🤝 Game ended in a draw!")

    print(f"\nTotal moves: {move_count}")


def human_vs_bot_game():
    """Run a game between human and bot."""
    print("👤 Human vs Bot Game")
    print("=" * 50)
    print("You are X, Bot is O")
    print("Enter column number (0-6) or 'q' to quit")

    bot = TestBot()
    game_board = GameBoard()

    print("\nStarting game...")
    game_board.print_board()

    current_player = Player.PLAYER1
    move_count = 0
    max_moves = 42

    while move_count < max_moves:
        if current_player == Player.PLAYER1:
            print(f"\n👤 Your turn (X)")
            move = get_human_move(game_board)

            if move is None:
                print("Game ended by player.")
                return

            game_board.make_move(move, current_player)
            print(f"You play column {move}")
            game_board.print_board()

        else:
            print(f"\n🤖 Bot's turn (O)")
            move = bot.calculate_move(game_board, current_player, 5000)

            if move is None:
                print("No valid moves left - game over!")
                break

            game_board.make_move(move, current_player)
            print(f"Bot plays column {move}")
            game_board.print_board()

        if game_board.check_win(current_player):
            if current_player == Player.PLAYER1:
                print("\n🎉 You win! Congratulations!")
            else:
                print("\n🤖 Bot wins! Better luck next time!")
            break

        current_player = Player.PLAYER2 if current_player == Player.PLAYER1 else Player.PLAYER1
        move_count += 1

    if move_count >= max_moves:
        print("\n🤝 Game ended in a draw!")


def main():
    """Main demo menu."""
    print("🎮 Connect 4 - Interactive Demos")
    print("=" * 50)

    while True:
        print("\n1. Bot vs Bot Game")
        print("2. Human vs Bot Game")
        print("3. Exit")
        print("-" * 30)

        try:
            choice = input("Select demo (1-3): ").strip()

            if choice == '1':
                bot_vs_bot_game()
            elif choice == '2':
                human_vs_bot_game()
            elif choice == '3':
                print("👋 Thanks for playing!")
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")

        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted by user.")
            break
        except Exception as e:
            print(f"💥 Demo error: {e}")
            break


if __name__ == "__main__":
    main()
