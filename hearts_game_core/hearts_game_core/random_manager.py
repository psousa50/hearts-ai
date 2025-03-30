from typing import Optional

import numpy as np


class RandomManager:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self._random = np.random.default_rng(self.seed)

    def random(self, *args, **kwargs):
        return self._random.random(*args, **kwargs)

    def choice(self, *args, **kwargs):
        return self._random.choice(*args, **kwargs)

    def shuffle(self, *args, **kwargs):
        return self._random.shuffle(*args, **kwargs)
