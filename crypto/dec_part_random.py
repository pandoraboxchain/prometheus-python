import struct
from Crypto.PublicKey import RSA
from Crypto import Random
from base64 import b64decode

def dec_part_random(enc_data, key):
    dec_data = key.decrypt(enc_data)
    #part_random = [random.getrandbits(8) for item in range(32)]
    #dec_data = struct.unpack("%sh" % len(part_random), enc_data)
    rand = dec_data[:32]
    era_hash = dec_data[32:]
    return (era_hash, rand)

def decode_random_using_raw_key(enc_data, key_bytes):
    decoded_bytes = b64decode(key_bytes)
    key = RSA.importKey(decoded_bytes)
    return dec_part_random(enc_data, key)
