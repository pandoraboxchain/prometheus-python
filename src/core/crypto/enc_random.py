import os

from Crypto.PublicKey import RSA
from Crypto import Random

from core.crypto.private import Private


def enc_part_random(era_hash):
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)
    random = os.urandom(32)
    ed = random+era_hash
    enc_data = key.publickey().encrypt(ed, 32)[0]
    return enc_data, key


def encrypt_commit_bytes(random_bytes, era_hash):
    key = Private.generate()
    ed = random_bytes + era_hash
    encrypted = key.publickey().encrypt(ed, 32)[0]
    return encrypted, key
