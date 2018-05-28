import unittest
from Crypto.Hash import SHA256

from crypto.enc_random import enc_part_random
from crypto.dec_part_random import dec_part_random

class EncDec(unittest.TestCase):

    def test_enc_dec(self):
        era_hash = SHA256.new(b"323423").digest()
        enc_data, key = enc_part_random(era_hash)
        res_era_hash, rand = dec_part_random(enc_data, key)
        self.assertEqual(era_hash, res_era_hash)
