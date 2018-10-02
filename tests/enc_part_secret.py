import unittest
import os
from hashlib import sha256
from crypto.secret import enc_part_secret, dec_part_secret

class EncDecSecret(unittest.TestCase):

    def test_enc_dec_secret(self):
        key = Private.generate()
        public_key = Private.publickey(key)
        enc_data = enc_part_secret(public_key,'1-7da6b11af146449675780434f6589230a3435d9ab59910354205996f508b8d0d')
        dec = dec_part_secret(key, enc_data)
        self.assertEqual(dec, '1-7da6b11af146449675780434f6589230a3435d9ab59910354205996f508b8d0d'.encode('utf-8'))
