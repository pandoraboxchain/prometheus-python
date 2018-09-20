import random
import string
import os

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from secretsharing import PlaintextToHexSecretSharer
from secretsharing import secret_int_to_points, points_to_secret_int
from base64 import b64decode
from crypto.keys import Keys
from crypto.public import Public
from crypto.private import Private

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
    enc_data = Public.encrypt(split, publickey)
    return enc_data

def dec_part_secret(privatekey, enc_data, number):
    split = Private.decrypt(enc_data, privatekey) #TODO check if this returns bytearray, those decryption success
    return (number + 1, int.from_bytes(split, byteorder="big"))

def decode_random(encoded_splits, private_keys):
    splits = []
    for i in range(0, len(encoded_splits)):
        split = encoded_splits[i]
        private_key = private_keys[i]
        if not private_key: continue
        split = dec_part_secret(private_key, split, i)
        splits.append(split)

    return recover_splits(splits)

def encode_splits(splits, public_keys):
    encoded_splits = []
    for i in range(0, len(splits)):
        public_key = public_keys[i]
        if public_key:
            encoded_split = enc_part_secret(public_key, splits[i])
            encoded_splits.append(encoded_split)
    
    return encoded_splits
