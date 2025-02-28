# Hearts Game Visualizer

A Python-based visualization tool for Hearts card game replays. This program reads game data from a JSON file and provides an interactive visualization of the game, allowing you to step through tricks and see the cards being played.

## Requirements

- Python 3.7+
- Pygame 2.5.2

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create an `assets/cards` directory and add card images (optional):
   - Images should be named in the format: `{rank}_{suit}.png`
   - Example: `A_hearts.png`, `10_diamonds.png`, etc.
   - If images are not present, cards will be rendered with text

## Usage

Run the visualizer with a game JSON file:

```bash
python game_visualizer.py ../hearts-game/game_results.json
```

## Controls

- **Space**: Show next card (automatically moves to next trick when current trick is finished)
- **Left Arrow**: Go to previous trick
- **Right Arrow**: Go to next trick
- **Esc**: Quit the visualizer

## Game Display

- Players are positioned around the table (South, West, North, East)
- Cards are shown one at a time as you press space
- Cards are animated from player positions to the center
- Game and trick information is displayed at the top
- Control information is shown at the bottom
