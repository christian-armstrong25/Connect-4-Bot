# Connect 4 Bot

## 🚀 Quick Start

### Run Demos

```bash
python demos.py
```

### Run Tests

```bash
python tests.py
```

## 🎮 Game Board API

```python
board.get_valid_moves()           # [0,1,2,3,4,5,6] - valid columns
board.is_valid_move(col)          # True/False - check if column valid
board.make_move(col, player)      # True/False - make move
board.check_win(player)           # True/False - check if player won
board.is_full()                   # True/False - check if board full
board.print_board()               # Pretty print board
```
