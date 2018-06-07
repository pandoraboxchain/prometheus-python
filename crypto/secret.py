import random
import string
import os

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from secretsharing import PlaintextToHexSecretSharer
from secretsharing import secret_int_to_points, points_to_secret_int
from base64 import b64decode

def split_secret(data, threshold, num_points):
    splits = []
    split_ints = secret_int_to_points(int.from_bytes(data, byteorder="big"), threshold, num_points)
    for item in split_ints:
        bytes = item[1].to_bytes(32, byteorder="big")
        splits.append(bytes)
    return splits

def split_random_secret(era_hash, threshold, num_points):
    random = os.urandom(32)
    data = random+era_hash
    return split_secret(data, threshold, num_points)

def recover_splits(splits):
    return points_to_secret_int(splits)

def enc_part_secret(publickey, split):
    enc_data = publickey.encrypt(split, 32)[0]
    return enc_data

def dec_part_secret(privatekey, enc_data, number):
    split = privatekey.decrypt(enc_data)
    return (number + 1, int.from_bytes(split, byteorder="big"))

def dec_part_secret_raw_key(key_bytes, enc_data, number):
    decoded_bytes = b64decode(key_bytes)
    key = RSA.importKey(decoded_bytes)
    return dec_part_secret(key, enc_data, number)
