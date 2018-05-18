from chain.block_signer import BlockSigner
from base64 import b64decode,b64encode
from Crypto.PublicKey import RSA

class BlockSigner():

    def __init__(self):
        self.validators = []
        self.get_from_file()

    def set_private_key(self, private_key):
        self.private_key = private_key
