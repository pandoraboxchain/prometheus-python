import unittest
import os
from crypto.secret import split_secret, recover_splits
from Crypto.Hash import SHA256

class TestSecretSharing(unittest.TestCase):

    def test_sharing(self):
        original_bytes = os.urandom(32)
        splits = split_secret(original_bytes, 3, 5)

        tuple_ordered_splits = []
        for i in range(0,3):
            ordered_tuple = (i + 1, int.from_bytes(splits[i], byteorder="big"))
            tuple_ordered_splits.append(ordered_tuple)

        recovered = recover_splits(tuple_ordered_splits)

        original_number = int.from_bytes(original_bytes, byteorder="big")
        self.assertEqual(original_number, recovered)

        non_recovered = recover_splits(tuple_ordered_splits[0:2])
        self.assertNotEqual(original_number, non_recovered)
        
