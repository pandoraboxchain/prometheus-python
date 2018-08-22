import random
from random import getrandbits
from enum import IntEnum

class Source:
    SIGNERS = 0
    RANDOMIZERS = 1


class Entropy:
    @staticmethod
    def get_nth_derivative(seed, step):
        random.seed(seed)
        for _ in range(step):
            random.getrandbits(32)
        return random.getrandbits(32)

