from Crypto.PublicKey import RSA
from base64 import b64decode,b64encode

class Keys():
    @staticmethod
    def from_bytes(key_bytes):
        decoded_bytes = b64decode(key_bytes)
        key = RSA.importKey(decoded_bytes)
        return key

    @staticmethod
    def to_bytes(key):
        return b64encode(key.exportKey('DER'))

    @staticmethod
    def list_from_bytes(key_bytes_list):
        decoded_keys = []
        for key in key_bytes_list:
            decoded_keys.append(Keys.from_bytes(key))
        return decoded_keys

    @staticmethod
    def list_to_bytes(keys_list):
        encoded_keys = []
        for key in keys_list:
            encoded_keys.append(Keys.to_bytes(key))
        return encoded_keys

    @staticmethod
    def display(key):
        if not isinstance(key, (bytes, bytearray)):
            key = Keys.to_bytes(key)
        print(key[77:90].hex()+"..."+key[-25:-12].hex())