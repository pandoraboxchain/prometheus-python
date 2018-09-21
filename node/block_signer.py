from base64 import b64decode,b64encode
from Crypto.PublicKey import RSA


class BlockSigner:

    def __init__(self, private_key):
        self.private_key = private_key

    def set_private_key(self, private_key):
        self.private_key = private_key


