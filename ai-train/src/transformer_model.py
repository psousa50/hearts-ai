import datetime
import os
from typing import List

import numpy as np
import tensorflow as tf
from predict_request import GameState
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
)

NUM_CARDS = 52
EMBED_DIM = 16
NUM_HEADS = 4
FEED_FORWARD_DIM = 64


class HeartsTransformerModel:
    def __init__(self):
        self.model = None
        self.initial_epoch = 0

    def build(self):
        sequence_input = Input(shape=(INPUT_SEQUENCE_LENGTH,), name="sequence_input")

        x = Embedding(input_dim=NUM_CARDS, output_dim=EMBED_DIM)(sequence_input)

        # Transformer Encoder
        x = self.transformer_encoder(x)

        # Global average pooling for final representation
        x = GlobalAveragePooling1D()(x)

        # Output layer (predicting one of 52 cards)
        outputs = Dense(NUM_CARDS, activation="softmax", name="card_output")(x)

        # Create model
        self.model = Model(inputs=sequence_input, outputs=outputs)

        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=1e-4),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

    def transformer_encoder(self, inputs):
        attn_output = MultiHeadAttention(num_heads=NUM_HEADS, key_dim=EMBED_DIM)(
            inputs, inputs
        )
        attn_output = Dropout(0.3)(attn_output)
        attn_output = LayerNormalization(epsilon=1e-6)(Add()([inputs, attn_output]))

        ffn = Dense(FEED_FORWARD_DIM, activation="relu")(attn_output)
        ffn = Dense(EMBED_DIM)(ffn)
        ffn = Dropout(0.3)(ffn)

        output = LayerNormalization(epsilon=1e-6)(Add()([attn_output, ffn]))
        return output

    def load(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        self.compile_model()  # Recompile to ensure metrics are built
        print("Pre-trained model loaded successfully!", flush=True)

        self.compile_model()

        self.initial_epoch = 0
        # Extract epoch number from filename if possible
        if "epoch_" in model_path:
            try:
                epoch_str = model_path.split("epoch_")[1].split(".")[0]
                self.initial_epoch = int(epoch_str) + 1
                print(f"Continuing from epoch {self.initial_epoch}", flush=True)
            except (IndexError, ValueError):
                self.initial_epoch = 0

    def train(self, game_state: List[GameState], epochs=50, batch_size=16):
        os.makedirs("models", exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Define checkpoint path with versioning
        checkpoint_path = f"checkpoints/model_{timestamp}.keras"

        # Create a new checkpoint callback
        versioned_checkpoint_callback = ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            verbose=1,
        )

        X, y = build_train_data(game_state)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[versioned_checkpoint_callback],
        )

    def compile_model(self):
        """Compile the model with optimizer and metrics"""
        self.model.compile(
            optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"]
        )

    def load_latest_checkpoint(self):
        """Load the latest checkpoint if it exists"""
        checkpoint_dir = "models"
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

    def save_weights(self, path):
        self.model.save_weights(path)

    def load_weights(self, path):
        self.model.load_weights(path)
