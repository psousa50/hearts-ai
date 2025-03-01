import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Embedding, Input, Dense, LayerNormalization, Dropout, LSTM
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from typing import List, Tuple, Dict

class HeartsModel:
    def __init__(self, max_seq_length: int = 128, embedding_dim: int = 128):
        self.max_seq_length = max_seq_length
        self.embedding_dim = embedding_dim
        self.model = None
        self.checkpoint_dir = "checkpoints"
        self.logs_dir = "logs"
        
        # Create directories if they don't exist
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Game tokens mapping
        self.game_tokens = self._create_game_tokens()
        
    def _create_game_tokens(self) -> Dict[str, int]:
        """Create mapping for game tokens (cards, suits, etc.)"""
        tokens = {}
        # Card tokens (RANK_X_SUIT_Y)
        for rank in range(2, 15):  # 2-14 (Ace is 14)
            for suit in ['H', 'D', 'C', 'S']:
                tokens[f"RANK_{rank}_SUIT_{suit}"] = len(tokens)
        # Special tokens
        special_tokens = ['PAD', 'START', 'END', 'TRICK_START', 'TRICK_END']
        for token in special_tokens:
            tokens[token] = len(tokens)
        return tokens
    
    def build_model(self):
        """Build the model architecture"""
        input_ids = Input(shape=(self.max_seq_length,), dtype=tf.int32, name="input_ids")
        
        # Embedding layer
        embedding_layer = Embedding(
            input_dim=len(self.game_tokens),
            output_dim=self.embedding_dim,
            mask_zero=True
        )(input_ids)
        
        # LSTM layers
        x = LSTM(256, return_sequences=True, use_cudnn=False)(embedding_layer)
        x = LSTM(128, use_cudnn=False)(x)
        
        # Dense layers
        x = LayerNormalization()(x)
        x = Dense(256, activation="relu")(x)
        x = Dropout(0.1)(x)
        x = Dense(128, activation="relu")(x)
        
        # Output layer (52 cards - 13 ranks * 4 suits)
        output_layer = Dense(52, activation="softmax", name="card_prediction")(x)
        
        # Create model
        self.model = Model(inputs=input_ids, outputs=output_layer)
        
        # Compile model
        self.model.compile(
            optimizer="adam",
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )
        
        return self.model
    
    def load_latest_checkpoint(self) -> Tuple[int, int]:
        """Load the latest checkpoint if it exists"""
        checkpoints = sorted([
            f for f in os.listdir(self.checkpoint_dir)
            if f.startswith("model_epoch")
        ])
        
        if not checkpoints:
            return 0, 0
        
        latest_checkpoint = checkpoints[-1]
        epoch = int(latest_checkpoint.split("_")[2])
        step = int(latest_checkpoint.split("_")[4].split(".")[0])
        
        self.model.load_weights(os.path.join(self.checkpoint_dir, latest_checkpoint))
        print(f"Loaded checkpoint from epoch {epoch}, step {step}")
        
        return epoch, step
    
    def train(self, 
              train_data_path: str,
              epochs: int = 100,
              batch_size: int = 32,
              validation_split: float = 0.2,
              initial_epoch: int = 0):
        """Train the model with checkpointing"""
        from data_processor import process_game_data
        
        # Process training data
        X_train, y_train, X_val, y_val = process_game_data(
            train_data_path,
            self.game_tokens,
            self.max_seq_length,
            test_size=validation_split
        )
        
        # Callbacks for saving progress
        callbacks = [
            ModelCheckpoint(
                filepath=os.path.join(
                    self.checkpoint_dir,
                    "model_epoch_{epoch:02d}.weights.h5"
                ),
                save_weights_only=True,
                save_best_only=True,
                monitor="val_accuracy"
            ),
            CSVLogger(
                os.path.join(self.logs_dir, "training_log.csv"),
                append=True
            )
        ]
        
        # Train the model
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            initial_epoch=initial_epoch
        )
        
        return history
    
    def predict_move(self, game_state: Dict) -> np.ndarray:
        """Predict the next move given a game state"""
        from data_processor import process_game_state
        
        # Process the game state
        X = process_game_state(game_state, self.game_tokens, self.max_seq_length)
        X = np.expand_dims(X, axis=0)  # Add batch dimension
        
        # Get predictions
        predictions = self.model.predict(X)
        return predictions[0]  # Remove batch dimension
