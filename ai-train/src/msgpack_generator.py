import msgpack
import numpy as np
from game_state_reader import extract_game_states
from tensorflow.keras.utils import Sequence
from transformer_encoding import build_train_data


class MsgpackDataGenerator(Sequence):
    def __init__(self, msgpack_file, batch_size=32, sequence_length=13):
        self.msgpack_file = msgpack_file
        self.batch_size = batch_size
        self.sequence_length = sequence_length
        self.data = self._load_data()
        self.num_samples = len(self.data)

    def _load_data(self):
        """Loads Msgpack file in a memory-efficient way"""
        with open(self.msgpack_file, "rb") as f:
            unpacker = msgpack.Unpacker(f, raw=False)
            return list(unpacker)  # List of (moves, next_move)

    def __len__(self):
        """Number of batches per epoch"""
        return int(np.floor(self.num_samples / self.batch_size))

    def __getitem__(self, index):
        """Load batch data dynamically"""
        batch_data = self.data[index * self.batch_size : (index + 1) * self.batch_size]
        game_states = extract_game_states(batch_data)
        return build_train_data(game_states)


# Initialize generator
train_generator = MsgpackDataGenerator("game_data.msgpack", batch_size=32)
