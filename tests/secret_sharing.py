import unittest
import os
from crypto.secret import split_secret, recover_splits, encode_splits, decode_random
from crypto.private import Private
from crypto.keys import Keys


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

    def test_encryption_and_decryption(self):
        private_keys = []
        public_keys = []
        for i in range(0, 5):
            private = Private.generate()
            private_keys.append(private)
            public_keys.append(private.publickey())

        raw_private_keys = Keys.list_to_bytes(private_keys)
        decoded_private_keys = Keys.list_from_bytes(raw_private_keys)

        random_bytes = os.urandom(32)
        random_value = int.from_bytes(random_bytes, byteorder='big')
        splits = split_secret(random_bytes, 3, 5)
        encoded_splits = encode_splits(splits, public_keys)
        decoded_random = decode_random(encoded_splits, decoded_private_keys)

        self.assertEqual(random_value, decoded_random)

