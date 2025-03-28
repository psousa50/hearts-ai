# Notes

## Training Data

The goal is to find "Good" sequences of games, i.e. a sequence of last cards played and a card to play next that was considered a good move.

One way of doing this:
- Simulate a game
- before each move, simulate a number of game for each valid move and choose the one with the best score
- the simulation should be start with the current game state and use random strategy for all players

Q.
- what if the best move is a lousy one?
- 

