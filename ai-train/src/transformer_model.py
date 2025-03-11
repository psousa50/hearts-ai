import datetime
import os
from typing import List

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
    build_train_data,
)

NUM_CARDS = 52
EMBED_DIM = 16
NUM_HEADS = 4
FEED_FORWARD_DIM = 64


def transformer_encoder(inputs):
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


def build_model():
    sequence_input = Input(shape=(INPUT_SEQUENCE_LENGTH,), name="sequence_input")

    x = Embedding(input_dim=NUM_CARDS, output_dim=EMBED_DIM)(sequence_input)

    # Transformer Encoder
    x = transformer_encoder(x)

    # Global average pooling for final representation
    x = GlobalAveragePooling1D()(x)

    # Output layer (predicting one of 52 cards)
    outputs = Dense(NUM_CARDS, activation="softmax", name="card_output")(x)

    # Create model
    transformer_model = Model(inputs=sequence_input, outputs=outputs)

    # Compile model
    transformer_model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return transformer_model


def train_model(model, game_state: List[GameState], epochs=50, batch_size=16):
    os.makedirs("models", exist_ok=True)
    os.makedirs("models/checkpoints", exist_ok=True)

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
    model.fit(
        X_train,
        y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[versioned_checkpoint_callback],
    )
