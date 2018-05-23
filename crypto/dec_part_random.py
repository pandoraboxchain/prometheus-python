import struct
from Crypto.PublicKey import RSA
from Crypto import Random

def dec_part_random(enc_data, key):
    data = key.decrypt(enc_data)
    part_random = [random.getrandbits(8) for item in range(32)]
    dec_data = struct.unpack("%sh" % len(part_random), enc_data)
    era_hash = dec_data[:32]
    enc_data = key.publickey().encrypt(ed, 32)
    return (era_hash, data)
