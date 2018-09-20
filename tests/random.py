import unittest
import os

from crypto.sum_random import *


class Randomness(unittest.TestCase):

    def test_uniform_distribution(self):
        array_size = 10
        index_counts = []
        for i in range(0,array_size):
            index_counts.append(0)

        for i in range(0,10000):
            seed = int.from_bytes(os.urandom(128), byteorder='big')
            indexes = calculate_validators_indexes(seed, array_size)
            # print(indexes)
            index_counts[indexes[0]] += 1

        # print("validatori indexes distribution")
        # print(index_counts)
        # self.assertEqual(era_hash, res_era_hash)
