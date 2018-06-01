import struct
import random
import os
from Crypto.PublicKey import RSA
from Crypto import Random

def enc_part_random(era_hash):
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)
    part_random = [random.getrandbits(8) for item in range(32)]
    part_random_pack = struct.pack("%sB" % len(part_random), *part_random)
    ed = part_random_pack+era_hash
    enc_data = key.publickey().encrypt(ed, 32)[0]
    return (enc_data, key)

def encode_value(value, era_hash):
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)
    value_bytes = value.to_bytes(32, byteorder='big')
    ed = value_bytes + era_hash
    enc_data = key.publickey().encrypt(ed, 32)[0]
    return (enc_data, key)
