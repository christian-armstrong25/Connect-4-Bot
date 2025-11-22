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

### `solve_positions.py` - Position Solver (Self-Play)

Generates a database of precomputed optimal moves through self-play. The agent plays against itself, and only positions actually encountered during games are stored. As the search deepens over time, only positions searched to sufficient depth are cached.

**Usage:**

```bash
python solve_positions.py <time_seconds> [time_per_move_ms] [min_depth] [evaluator]
```

**Examples:**

```bash
python solve_positions.py 60                    # Run for 60 seconds with defaults
python solve_positions.py 120 150               # 120 seconds, 150ms per move
python solve_positions.py 60 100 2               # Minimum depth of 2 required
python solve_positions.py 60 100 0 old           # Use "old" evaluator
```

**Parameters:**

- `time_seconds` (required): How long to run self-play in seconds
- `time_per_move_ms` (default: 100): Time per move in milliseconds
  - Recommended: 100-200ms for good balance of depth and game diversity
- `min_depth` (default: 0): Minimum search depth to cache positions
  - Starts at this value and gradually increases over time
- `evaluator` (default: "new"): Which evaluator to use - "old" or "new"

**How it works:**

1. The agent plays games against itself using iterative deepening search
2. Only positions actually reached during games are tracked
3. Positions are extracted from the transposition table and cached
4. Minimum depth requirement gradually increases over time
5. Results are saved to `Board_Evals/precomputed_moves.py`

**Tips:**

- Start with 60-120 seconds for initial testing
- Use 150ms per move for optimal balance (depth 4-6, good game diversity)
- The system automatically merges with existing precomputed moves
- Longer runs will explore more positions and build a more comprehensive database

---

## Dependencies

Python 3.x (standard library only)
