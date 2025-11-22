# Connect-4 Bot

A Connect-4 game engine with AI agents and position solving capabilities.

## Scripts

### `runner.py` - Game Runner

Runs games between AI agents to test and compare strategies.

**Usage:**

```bash
python runner.py [time_limit_ms] [num_games]
```

**Examples:**

```bash
python runner.py                    # Single game, 25ms time limit
python runner.py 50                 # Single game, 50ms time limit
python runner.py 30 100             # Tournament of 100 games, 30ms limit
```

- **Single game mode** (`num_games=1`): Shows detailed move-by-move gameplay
- **Tournament mode** (`num_games>1`): Shows win rates and statistics

Currently pits MinimaxBot with "old" vs "new" evaluation functions. Edit `agents` in `run_game()` to change players.

---

### `solve_positions.py` - Position Solver

Generates a database of precomputed optimal moves by solving positions with minimax.

**Usage:**

```bash
python solve_positions.py [max_explore_depth] [max_search_depth] [merge_mode]
```

**Examples:**

```bash
python solve_positions.py 8                    # Depth 8, full solve
python solve_positions.py 6 10                 # Depth 6, search depth 10
python solve_positions.py 8 None replace       # Replace existing moves
```

**Parameters:**

- `max_explore_depth` (default: 8): How deep to explore the game tree
- `max_search_depth` (default: None): Minimax search depth (None = full solve)
- `merge_mode` (default: "merge"): "merge" to add to existing, "replace" to start fresh

Results are saved to `Board_Evals/precomputed_moves.py`. Shows progress bar and ETA during execution.

**Tips:** Start with `max_explore_depth=6` for testing. Use merge mode to incrementally build the database.

---

## Dependencies

Python 3.x (standard library only)
