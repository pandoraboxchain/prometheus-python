from base64 import b64decode
from Crypto.PublicKey import RSA

class BlockSigner:

    def __init__(self, private_key):
        self.private_key = private_key

    def set_private_key(self, private_key):
        self.private_key = private_key

class BlockSigners:

    def __init__(self):
        self.block_signers = []
        self.get_from_file()

    def get_from_file(self):
        with open('keys') as f:
            lines = f.readlines()

        for line in lines:
            decode = b64decode(line)
            if len(decode) != 0:
                key = RSA.importKey(decode)
                block_signer = BlockSigner(key)
                self.block_signers.append(block_signer)
