# Hearts AI

A Hearts card game implementation with AI players and game visualization.

## Project Structure

- `game-core/`: Core game logic implemented in Rust
  - Game rules and mechanics
  - Player strategies
  - Card and deck management
- `cli/`: Command-line interface in Rust
  - Game generation
  - Training data generation
  - Statistics reporting
- `ui/`: Game visualization in Python
  - Interactive game replay
  - Card animations
  - Player statistics display

## Features

- Multiple AI strategies:
  - Random: Makes random valid moves
  - Aggressive: Tries to play high cards
  - Avoid Points: Tries to minimize points taken
- Game visualization:
  - Real-time card animations
  - Player scores and statistics
  - Interactive game replay
- Game statistics:
  - Win rates per strategy
  - Average scores
  - Total wins

## Getting Started

### Prerequisites

- Rust (for game core and CLI)
- Python 3.x (for visualization)
- Required Python packages:
  ```
  pip install -r ui/requirements.txt
  ```

### Running the Game

1. Generate game results:
   ```bash
   cd cli
   cargo run -- generate-games -n <number_of_games>
   ```

2. View game visualization:
   ```bash
   cd ui
   python game_visualizer.py ../cli/data/game_results_*.json
   ```

### Visualization Controls

- **Space**: Toggle auto-play mode
- **Left/Right**: Previous/Next card
- **Shift+Left/Right**: Previous/Next trick
- Right key automatically moves to next trick when at end of current trick
- Close window to quit

## Game Rules

Hearts is played with 4 players and a standard 52-card deck. The goal is to avoid taking points:
- Each heart card (♥) is worth 1 point
- Queen of spades (♠Q) is worth 13 points
- Lowest score wins

## Development

### Adding New Strategies

1. Create a new strategy in `game-core/src/strategy.rs`
2. Implement the `Strategy` trait
3. Add the strategy to the player initialization in `game-core/src/game.rs`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
