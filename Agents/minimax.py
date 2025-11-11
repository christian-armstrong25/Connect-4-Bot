from connect4_engine import GameBoard, Player
from .base_bot import BaseNegamaxBot


class MinimaxBot(BaseNegamaxBot):
    def calculate_move(self, board: GameBoard, player: Player, time_per_move: int) -> int:
        return self.negamax(board, player, 4)[1]
