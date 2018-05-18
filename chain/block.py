import struct
from Crypto.Hash import SHA256

class Block():

    def get_hash(self):
        if not hasattr(self, 'hash'):
            self.hash = SHA256.new(self.raw_data)
        return self.hash

    def set_raw_data(self, raw_data):
        self.raw_data = raw_data
        if hasattr(self, 'hash')
            del self.hash

    def parse(self):
        self.timestamp = struct.unpack('<L', self.raw_data)[0]

    def set_signature(self, signature):
        self.signature = signature

    def verify_signature(self, pubkey)
        self.get_hash().digest()
        public_key.verify(self.get_hash(), self.signature)
