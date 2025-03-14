# Game Models

## The Game

It should contain all the information needed to run the game, including:

- The game id
- The players
- The current trick
- The hearts broken flag
- The current player
- The tricks

## GameResult

It should contain all the information needed to replay the game, including:

- The game id
- The players (name, initial hand, strategy, score)
- All the tricks
- The winner

### Trick

It should contain all the information about a trick, including:

- The cards played, in the players order
- The first player
- The winner
- The points got by the winner

### The current Trick

It should contain all the information about the current trick, including:

- The cards played, in the players order
- Non-played cards are represented by NONE (or similar))
- The first player

### Player

It should contain all the information about a player, including:

- The player name
- The player initial hand
- The player strategy
- The player score

The player index is the order of the player in the game, starting from 0.

## The AI Training Data

It should contain all the information needed to train the AI, including:

- The players and their scores
- The previous tricks
- The current trick cards
- The current player
- The player hand at the time of the play
- The played card



## The process:

### Generating the training data (Rust):

1. Generate a game
2. Create the training data from the game
3. Convert it to a compact form (?)
4. Save it to a file

### Training the AI (Python):

1. Load the compact training data from the file
2. Create a TrainingData object from the compact training data
3. Train the AI
4. Save the model


