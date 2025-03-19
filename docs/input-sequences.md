# 🚀 King Card Game: Key Insights from Our Discussion

## 1️⃣ Choosing the Input Sequence for Model Training
- **Two main approaches:**
  - **Trick-Based Order**: Keep the order in which cards were played (P3 → P1 → P4 → P2).
  - **Fixed Player Order**: Always structure moves in (P1 → P2 → P3 → P4) order.
- **Best Approach** ✅:  
  - **Use Trick-Based Order + Player Encoding** → This keeps natural game dynamics and allows the model to learn player strategies.

## 2️⃣ Using Embeddings in the Transformer Model
- **Why Use Embeddings?**
  - Converts categorical inputs (**players, cards**) into dense vectors.
  - Helps the model learn **relationships between different cards and players**.
- **Key Changes in Model:**
  - **Player Embeddings**: Each player (0-3) gets an **8D vector**.
  - **Card Embeddings**: Each card (0-51) gets a **16D vector**.
  - **Concatenation Layer**: Merges both embeddings before passing to the Transformer.

## 3️⃣ Should We Predict the Next Player?
- **No need to predict the next player** because:
  - The game **rules already determine the turn order**.
  - The model should **only predict the next card**.

## 4️⃣ Identifying Good Players in a Specific Game
- **Hearts Scoring Rules**:  
  - **Lower scores = better performance**.
  - Total scores **always sum to 26**.
- **Methods to Identify "Good" Players:**
  - **Top 50% Selection**: Selects the best 2 out of 4 players per game.
  - **Fixed Threshold (Best Score + X points)**: Includes all players within a reasonable range of the best score.
  - **Percentile-Based Selection (Top 25%)** ✅: Dynamically adjusts the threshold based on the game's score distribution.

## 5️⃣ Understanding the 25th Percentile (Q1)
- **Definition**: The **25th percentile (Q1)** is the score below which **25% of players fall**.
- **Calculation Example in a Hearts Game**:
  - Given scores: `[3, 7, 10, 6]`
  - **Sorted**: `[3, 6, 7, 10]`
  - **Q1 Calculation**:
    \[
    Q1 = 3 + 0.25 \times (6 - 3) = 5.25
    \]
  - **Interpretation**: Players scoring **≤ 5.25** are in the **top 25%**.
