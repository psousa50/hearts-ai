import datetime
import os
from typing import List

import numpy as np
import tensorflow as tf
from game_classes import GameState
from gensim.models import KeyedVectors
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.layers import (
    Add,
    Dense,
    Dropout,
    Embedding,
    GlobalAveragePooling1D,
    Input,
    LayerNormalization,
    MultiHeadAttention,
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from transformer_encoding import (
    INPUT_SEQUENCE_LENGTH,
    build_input_sequence,
    build_train_data,
    decode_card,
)

NUM_CARDS = 52
EMBED_DIM = 16
NUM_HEADS = 4
FEED_FORWARD_DIM = 64


class HeartsTransformerModel:
    def __init__(self, pretrained_embeddings_path=None, trainable_embeddings=True):
        self.model = None
        self.initial_epoch = 0
        self.pretrained_embeddings = None
        self.trainable_embeddings = trainable_embeddings

        if pretrained_embeddings_path:
            self.load_pretrained_embeddings(pretrained_embeddings_path)

    def load_pretrained_embeddings(self, embeddings_path):
        """Load pretrained embeddings from Word2Vec format file"""
        try:
            print(f"Loading pretrained embeddings from {embeddings_path}")
            embedding_model = KeyedVectors.load_word2vec_format(
                embeddings_path, binary=False
            )

            # Get the embedding dimension from the loaded model
            embedding_dim = embedding_model.vector_size

            # Initialize embedding matrix
            embedding_matrix = np.zeros((NUM_CARDS, embedding_dim))

            # Map card tokens to their embeddings
            for i in range(NUM_CARDS):
                # Convert token index to card representation
                # This mapping needs to match the one used in the original embedding training
                card_key = self._token_to_card_key(i)

                if card_key in embedding_model:
                    embedding_matrix[i] = embedding_model[card_key]
                else:
                    print(f"Warning: Card key '{card_key}' not found in embeddings")

            self.pretrained_embeddings = embedding_matrix
            print(f"Loaded pretrained embeddings with shape {embedding_matrix.shape}")

            # Update EMBED_DIM to match the pretrained embeddings
            global EMBED_DIM
            EMBED_DIM = embedding_dim

        except Exception as e:
            print(f"Error loading pretrained embeddings: {e}")
            self.pretrained_embeddings = None

    def _token_to_card_key(self, token_idx):
        card = decode_card(token_idx)
        return f"{card.suit}{card.rank}"

    def build(self):
        sequence_input = Input(shape=(INPUT_SEQUENCE_LENGTH,), name="sequence_input")

        # Use pretrained embeddings if available
        if self.pretrained_embeddings is not None:
            embedding_layer = Embedding(
                input_dim=NUM_CARDS,
                output_dim=self.pretrained_embeddings.shape[1],
                weights=[self.pretrained_embeddings],
                trainable=self.trainable_embeddings,
                name="card_embedding",
            )(sequence_input)
        else:
            embedding_layer = Embedding(
                input_dim=NUM_CARDS, output_dim=EMBED_DIM, name="card_embedding"
            )(sequence_input)

        # Transformer Encoder
        x = self.transformer_encoder(embedding_layer)

        # Global average pooling for final representation
        x = GlobalAveragePooling1D()(x)

        # Output layer (predicting one of 52 cards)
        outputs = Dense(NUM_CARDS, activation="softmax", name="card_output")(x)

        # Create model
        self.model = Model(inputs=sequence_input, outputs=outputs)

        # Compile model
        self.compile_model()

    def transformer_encoder(self, inputs):
        # Get the embedding dimension from the inputs
        embed_dim = inputs.shape[-1]

        attn_output = MultiHeadAttention(
            num_heads=NUM_HEADS, key_dim=embed_dim // NUM_HEADS
        )(inputs, inputs)
        attn_output = Dropout(0.3)(attn_output)
        attn_output = LayerNormalization(epsilon=1e-6)(Add()([inputs, attn_output]))

        ffn = Dense(FEED_FORWARD_DIM, activation="relu")(attn_output)
        ffn = Dense(embed_dim)(ffn)
        ffn = Dropout(0.3)(ffn)

        output = LayerNormalization(epsilon=1e-6)(Add()([attn_output, ffn]))
        return output

    def load(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        self.compile_model()  # Recompile to ensure metrics are built
        print(f"Pre-trained model loaded successfully: {model_path}", flush=True)

        self.initial_epoch = 0
        # Extract epoch number from filename if possible
        if "epoch_" in model_path:
            try:
                epoch_str = model_path.split("epoch_")[1].split(".")[0]
                self.initial_epoch = int(epoch_str) + 1
                print(f"Continuing from epoch {self.initial_epoch}", flush=True)
            except (IndexError, ValueError):
                self.initial_epoch = 0

    def train(self, game_states: List[GameState], epochs, batch_size):
        os.makedirs("models", exist_ok=True)
        os.makedirs("models/checkpoints", exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Define checkpoint path with versioning
        checkpoint_path = (
            f"models/checkpoints/model_epoch_{{epoch:03d}}_{timestamp}.keras"
        )

        # Create a new checkpoint callback
        versioned_checkpoint_callback = ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1,
        )

        X, y = build_train_data(game_states)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            initial_epoch=self.initial_epoch,
            batch_size=batch_size,
            callbacks=[versioned_checkpoint_callback],
        )

    def compile_model(self):
        """Compile the model with optimizer and metrics"""
        self.model.compile(
            optimizer=Adam(learning_rate=1e-4),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

    def load_latest_checkpoint(self):
        """Load the latest checkpoint if it exists"""
        checkpoint_dir = "models/checkpoints"
        self.initial_epoch = 0
        if not os.path.exists(checkpoint_dir):
            return

        # Find all checkpoint files
        checkpoints = [
            f
            for f in os.listdir(checkpoint_dir)
            if f.startswith("model_epoch_") and f.endswith(".keras")
        ]
        if not checkpoints:
            return

        # Get the latest checkpoint
        latest_checkpoint = max(
            checkpoints, key=lambda x: int(x.split("_")[2].split(".")[0])
        )
        epoch = int(latest_checkpoint.split("_")[2].split(".")[0])

        # Load the checkpoint
        checkpoint_path = os.path.join(checkpoint_dir, latest_checkpoint)
        print(f"Loading checkpoint from {checkpoint_path}", flush=True)
        self.load(checkpoint_path)

        self.initial_epoch = epoch + 1

    def predict(self, game_state: GameState):
        input_sequence = build_input_sequence(game_state)
        input_sequence = np.expand_dims(input_sequence, axis=0)
        predictions = self.model.predict(input_sequence)
        return predictions

    def save(self, number_of_game_states: int = 0):
        path = "models/latest.keras"
        if number_of_game_states > 0:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            path = f"models/model_{timestamp}_{number_of_game_states}.keras"
        self.model.save(path)

    def save_weights(self, path):
        self.model.save_weights(path)

    def load_weights(self, path):
        self.model.load_weights(path)

    def get_embedding_weights(self):
        """Extract the embedding weights from the model"""
        for layer in self.model.layers:
            if isinstance(layer, Embedding):
                return layer.get_weights()[0]
        return None

    def save_embeddings(self, output_path):
        """Save the current embeddings in Word2Vec format for visualization or transfer"""
        embedding_weights = self.get_embedding_weights()
        if embedding_weights is None:
            print("No embedding weights found in the model")
            return

        # Create the output file in Word2Vec format
        with open(output_path, "w") as f:
            # Header: number of vectors and vector size
            f.write(f"{NUM_CARDS} {embedding_weights.shape[1]}\n")

            # Write each vector
            for i in range(NUM_CARDS):
                card_key = self._token_to_card_key(i)
                vector_str = " ".join([str(val) for val in embedding_weights[i]])
                f.write(f"{card_key} {vector_str}\n")

        print(f"Embeddings saved to {output_path}")
