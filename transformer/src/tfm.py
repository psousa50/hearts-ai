import os
import sys
from typing import List

import matplotlib.pyplot as plt
import msgpack
import numpy as np
import seaborn as sns
import tensorflow as tf
from game_classes import Card, GameState
from game_state_extractor import extract_game_states
from gensim.models import KeyedVectors, Word2Vec
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity

# Define all 52 cards in the deck
suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

# Generate all card names
all_cards = [f"{rank} of {suit}" for suit in suits for rank in ranks]

card_to_idx = {card: i for i, card in enumerate(all_cards)}

# ---------------------------- 1. Generate Pretrained Embeddings ----------------------------


def train_word2vec(cards_sequences: List[List[Card]], outfile_path, vector_size=128):
    game_sequences = [
        [f"{card.suit}{card.rank}" for card in sequence] for sequence in cards_sequences
    ]
    embedding_model = Word2Vec(
        sentences=game_sequences,
        vector_size=vector_size,
        window=5,
        min_count=1,
        sg=1,
        workers=4,
    )
    embedding_model.wv.save_word2vec_format(outfile_path)


# ---------------------------- 2. Load Pretrained Embeddings ----------------------------


def load_pretrained_embeddings(embedding_file, all_cards, embedding_dim=128):
    embedding_model = KeyedVectors.load_word2vec_format(embedding_file, binary=False)
    card_to_idx = {card: i for i, card in enumerate(embedding_model.index_to_key)}

    num_cards = len(card_to_idx)
    embedding_matrix = np.zeros((num_cards, embedding_dim))

    for card, index in card_to_idx.items():
        embedding_matrix[index] = embedding_model[card]  # Assign vector

    return embedding_matrix


# ---------------------------- 3. Build Transformer Model ----------------------------


def build_model(
    num_cards=52,
    embedding_dim=128,
    num_layers=6,
    hidden_dim=512,
    num_heads=8,
    max_seq_length=52,
    pretrained_embeddings=None,
    trainable_embeddings=False,
):
    inputs = tf.keras.layers.Input(shape=(max_seq_length,))

    embedding_layer = tf.keras.layers.Embedding(
        input_dim=num_cards,
        output_dim=embedding_dim,
        weights=[pretrained_embeddings] if pretrained_embeddings is not None else None,
        trainable=trainable_embeddings,
    )(inputs)

    x = embedding_layer
    for _ in range(num_layers):
        x = tf.keras.layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=embedding_dim
        )(x, x)
        x = tf.keras.layers.LayerNormalization()(x)
        x = tf.keras.layers.Dense(hidden_dim, activation="relu")(x)

    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    outputs = tf.keras.layers.Dense(num_cards, activation="softmax")(x)

    model = tf.keras.models.Model(inputs, outputs)
    model.compile(
        optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
    )
    return model


# ---------------------------- 4. Train Model ----------------------------


def train_model(model, X_train, y_train, batch_size=512, epochs=10):
    return model.fit(
        X_train, y_train, batch_size=batch_size, epochs=epochs, validation_split=0.1
    )


# ---------------------------- 5. Fine-Tune Embeddings ----------------------------


def fine_tune_embeddings(
    model, X_train, y_train, fine_tune_epochs=5, learning_rate=1e-5
):
    model.layers[1].trainable = True  # Unfreeze embedding layer
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model.fit(
        X_train, y_train, batch_size=512, epochs=fine_tune_epochs, validation_split=0.1
    )


# ---------------------------- 1. Load Model for Prediction ----------------------------


def load_trained_model(model_path):
    return tf.keras.models.load_model(model_path)


# ---------------------------- 2. Predict the Next Card ----------------------------


def predict_next_card(model, played_cards, card_to_idx, idx_to_card, max_seq_length=52):
    tokenized_seq = [card_to_idx[card] for card in played_cards if card in card_to_idx]

    # Pad sequence
    while len(tokenized_seq) < max_seq_length:
        tokenized_seq.append(0)
    tokenized_seq = tokenized_seq[:max_seq_length]

    input_tensor = np.array([tokenized_seq])
    predictions = model.predict(input_tensor)

    predicted_card_idx = np.argmax(predictions)
    return idx_to_card[predicted_card_idx]


# ---------------------------- 3. Visualize Embeddings ----------------------------


def visualize_embeddings(embedding_matrix, card_labels):
    # Define colors for each suit
    suit_colors = {
        "Hearts": "red",
        "Diamonds": "blue",
        "Clubs": "green",
        "Spades": "purple",
    }

    # Extract suit for each card
    suits = [label.split(" of ")[1] for label in card_labels]

    # First reduce dimensions using PCA (stabilizes t-SNE)
    pca = PCA(n_components=30, random_state=42)  # Reduce dimensions to 30
    reduced_embeddings_pca = pca.fit_transform(embedding_matrix)

    # Now run t-SNE on PCA output
    tsne = TSNE(
        n_components=2, perplexity=5, random_state=42, init="pca"
    )  # Use PCA initialization
    reduced_embeddings = tsne.fit_transform(reduced_embeddings_pca)

    # Create scatter plot with suit-based colors
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        x=reduced_embeddings[:, 0],
        y=reduced_embeddings[:, 1],
        hue=suits,
        palette=suit_colors,
        legend="full",
    )

    # Annotate each point with card labels
    for i, label in enumerate(card_labels):
        plt.annotate(
            label,
            (reduced_embeddings[i, 0], reduced_embeddings[i, 1]),
            fontsize=8,
            alpha=0.75,
        )

    plt.title("Card Embeddings Visualization with t-SNE (Suits in Different Colors)")
    plt.legend(title="Suit")
    plt.show()


# ---------------------------- 4. Example Usage ----------------------------


def example():
    model = load_trained_model("hearts_model.h5")

    # Example card mappings
    card_to_idx = {card: i for i, card in enumerate(all_cards)}
    idx_to_card = {i: card for card, i in card_to_idx.items()}

    # Predict the next card given played cards
    played_cards = ["10 of Hearts", "3 of Hearts", "8 of Hearts"]
    predicted_card = predict_next_card(model, played_cards, card_to_idx, idx_to_card)
    print("Predicted Next Card:", predicted_card)

    # Load embeddings and visualize
    embedding_matrix = load_pretrained_embeddings("card_embeddings.txt", all_cards)
    visualize_embeddings(embedding_matrix, all_cards)


def extract_card_sequence_from_game_state(game_state: GameState):
    return [
        card for trick in game_state.previous_tricks for card in trick.cards
    ] + game_state.current_trick.ordered_cards()


def train_embeddings(train_data_path, embeddings_path):
    print("\nTraining word2vec embeddings...", flush=True)
    with open(train_data_path, "rb") as f:
        raw_data = msgpack.unpackb(f.read(), raw=False)

    game_states = extract_game_states(raw_data)
    cards = [
        extract_card_sequence_from_game_state(game_state) for game_state in game_states
    ]

    train_word2vec(cards, embeddings_path)


def load_and_visualize_embeddings(embeddings_path):
    print("\nLoading embeddings...", flush=True)
    embedding_matrix = load_pretrained_embeddings(embeddings_path, all_cards)

    if np.isnan(embedding_matrix).any():
        print("⚠️ Warning: NaN values detected in the embedding matrix!")

    if np.all(embedding_matrix == 0, axis=1).any():
        print(
            "⚠️ Warning: Some embeddings are all zeros. Assigning random small values."
        )
        embedding_matrix += np.random.normal(0, 1e-6, embedding_matrix.shape)

    visualize_embeddings(embedding_matrix, all_cards)
    visualize_similarities(embedding_matrix)


def visualize_similarities(embedding_matrix):
    # Compute cosine similarity between each pair of cards
    similarity_matrix = cosine_similarity(embedding_matrix)

    # Create a heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        similarity_matrix,
        xticklabels=all_cards,
        yticklabels=all_cards,
        cmap="coolwarm",
        annot=False,
    )

    # 🔹 Improve layout
    plt.title("Pairwise Card Similarities (Cosine Similarity)")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # 🔹 Show the heatmap
    plt.show()


if __name__ == "__main__":
    os.makedirs("embeddings", exist_ok=True)

    train_data_path = sys.argv[1]

    embeddings_path = f"embeddings/card_embeddings_{sys.argv[2]}.txt"

    train_embeddings(train_data_path, embeddings_path)
    load_and_visualize_embeddings(embeddings_path)
