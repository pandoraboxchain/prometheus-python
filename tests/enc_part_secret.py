import unittest
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto import Random

from crypto.secret import enc_part_secret, dec_part_secret

class EncDecSecret(unittest.TestCase):

    def test_enc_dec_secret(self):
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        public_key = key.publickey()
        enc_data = enc_part_secret(public_key,'1-7da6b11af146449675780434f6589230a3435d9ab59910354205996f508b8d0d')
        dec = dec_part_secret(key, enc_data)
        self.assertEqual(dec, '1-7da6b11af146449675780434f6589230a3435d9ab59910354205996f508b8d0d'.encode('utf-8'))
