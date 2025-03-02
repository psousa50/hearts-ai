import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Embedding, GlobalAveragePooling1D, Concatenate, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger, EarlyStopping, Callback
import json
import time

from common import encode_card, encode_game_state

class TrainingProgressCallback(Callback):
    def __init__(self, print_interval=1):
        super().__init__()
        self.print_interval = print_interval
        self.last_time = None
        
    def on_train_begin(self, logs=None):
        print("\nStarting training...", flush=True)
        self.last_time = time.time()
        
    def on_batch_end(self, batch, logs=None):
        if batch % self.print_interval == 0:
            current_time = time.time()
            elapsed = current_time - self.last_time
            self.last_time = current_time
            
            metrics = " - ".join(f"{k}: {v:.4f}" for k, v in logs.items())
            print(f"Batch {batch} ({elapsed:.2f}s) - {metrics}", flush=True)

class HeartsModel:
    def __init__(self):
        self.model = None

    def build_model(self, vocab_size=73, embedding_dim=64, sequence_length=84):
        """Build the model architecture
        
        vocab_size: Number of unique tokens
            - 0-12: trick numbers
            - 13-16: player indices
            - 17-68: card tokens
            - 69-72: winner tokens
            - 52: empty token
        sequence_length: Length of input sequence
            - 2 tokens for trick number and player
            - 13 tricks * 5 tokens = 65 (4 cards + winner)
            - 4 tokens for current trick
            - 13 tokens for hand
            Total: 84 tokens
        """
        # Input layer for sequence
        sequence_input = Input(shape=(sequence_length,), name='sequence_input')
        
        # Embedding layer with larger dimension
        x = Embedding(vocab_size, embedding_dim)(sequence_input)
        
        # Process sequence with deeper network
        # First process local context (current trick and hand)
        x1 = Dense(128, activation='relu')(x)
        x1 = Dense(64, activation='relu')(x1)
        
        # Then process full sequence for global context
        x2 = Dense(256, activation='relu')(x)
        x2 = Dense(128, activation='relu')(x2)
        
        # Combine local and global features
        x = Concatenate()([
            GlobalAveragePooling1D()(x1),
            GlobalAveragePooling1D()(x2)
        ])
        
        # Dense layers with dropout for regularization
        x = Dense(512, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = Dense(256, activation='relu')(x)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = Dense(128, activation='relu')(x)
        
        # Output layer (52 cards)
        predictions = Dense(52, activation='softmax', name='predictions')(x)
        
        # Create model
        self.model = Model(inputs=sequence_input, outputs=predictions)
        
        # Compile model with learning rate schedule
        initial_learning_rate = 0.001
        decay_steps = 1000
        decay_rate = 0.9
        
        learning_rate_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
            initial_learning_rate,
            decay_steps=decay_steps,
            decay_rate=decay_rate,
            staircase=True
        )
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate_schedule),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

    def compile_model(self):
        """Compile the model with optimizer and metrics"""
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

    def load_latest_checkpoint(self):
        """Load the latest checkpoint if it exists"""
        checkpoint_dir = 'models'
        if not os.path.exists(checkpoint_dir):
            return 0, None

        # Find all checkpoint files
        checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('model_epoch_') and f.endswith('.keras')]
        if not checkpoints:
            return 0, None

        # Get the latest checkpoint
        latest_checkpoint = max(checkpoints, key=lambda x: int(x.split('_')[2].split('.')[0]))
        epoch = int(latest_checkpoint.split('_')[2].split('.')[0])

        # Load the checkpoint
        checkpoint_path = os.path.join(checkpoint_dir, latest_checkpoint)
        print(f"Loading checkpoint from {checkpoint_path}", flush=True)
        self.model = tf.keras.models.load_model(checkpoint_path)
        
        # Recompile to ensure metrics are built
        self.compile_model()
        
        return epoch + 1, checkpoint_path

    def train(self, train_data_path: str, epochs: int = None, batch_size: int = None, validation_split: float = 0.2, initial_epoch: int = 0):
        """Train the model with automatically derived parameters based on dataset size
        
        Parameters are calculated as follows:
        - batch_size: sqrt(N) where N is number of examples, capped between 32 and 128
        - epochs: 100,000/N with minimum of 20 and maximum of 200
        - early stopping patience: epochs/10 with minimum of 3
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        # Load training data
        with open(train_data_path, 'r') as f:
            data = json.load(f)
        
        num_examples = len(data)
        print(f"Training on {num_examples} examples", flush=True)
        
        # Calculate optimal parameters
        if batch_size is None:
            # Square root of N, capped between 32 and 128
            batch_size = min(max(int(np.sqrt(num_examples)), 32), 128)
            
        if epochs is None:
            # 100,000/N with min 20, max 200
            epochs = min(max(int(100_000 / num_examples), 20), 200)
            
        # Early stopping patience: epochs/10 with min 3
        patience = max(3, epochs // 10)
        
        steps_per_epoch = num_examples * (1 - validation_split) / batch_size
        print(f"\nTraining parameters derived from dataset size:", flush=True)
        print(f"- Batch size: {batch_size} (sqrt of {num_examples} examples)", flush=True)
        print(f"- Epochs: {epochs} (100,000/{num_examples})", flush=True)
        print(f"- Steps per epoch: {steps_per_epoch:.1f}", flush=True)
        print(f"- Early stopping patience: {patience} epochs", flush=True)
        print(f"- Training examples: {int(num_examples * (1 - validation_split))}", flush=True)
        print(f"- Validation examples: {int(num_examples * validation_split)}\n", flush=True)
        
        # Prepare training data
        X = []
        y = []
        
        print("Loading training data...", flush=True)
        total = len(data)
        for i, example in enumerate(data, 1):
            if i % 1000 == 0:
                print(f"Processing example {i}/{total}...", flush=True)
                
            # Encode game state as sequence
            sequence = encode_game_state(
                trick_number=example['trick_number'],
                current_player_index=example['current_player_index'],
                previous_tricks=example['previous_tricks'],
                current_trick_cards=example['current_trick_cards'],
                hand=example['player_hand']
            )
            
            # One-hot encode target card
            target = np.zeros(52)
            card = example['played_card']
            idx = encode_card(card)
            target[idx] = 1
            
            X.append(sequence)
            y.append(target)
        
        print("Converting to numpy arrays...", flush=True)
        X = np.array(X)
        y = np.array(y)
        print("Data preparation complete!", flush=True)
        
        # Create directories if they don't exist
        os.makedirs('models', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Callbacks
        callbacks = [
            ModelCheckpoint(
                'models/model_epoch_{epoch:02d}.keras',
                save_best_only=True,
                monitor='val_accuracy',
                mode='max',
                verbose=1
            ),
            EarlyStopping(
                monitor='val_accuracy',
                mode='max',
                patience=patience,
                restore_best_weights=True,
                verbose=1
            ),
            CSVLogger('logs/training_log.csv')
        ]
        
        print("\nStarting model training...", flush=True)
        # Train with progress bar
        history = self.model.fit(
            X,
            y,
            epochs=epochs,
            initial_epoch=initial_epoch,
            batch_size=batch_size,
            callbacks=callbacks,
            validation_split=validation_split,
            verbose=2  # Show one line per epoch
        )
        
        # Save final model
        self.model.save('models/latest.keras')  # Using native Keras format
        
        return history
