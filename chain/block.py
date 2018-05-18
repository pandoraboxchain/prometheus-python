from Crypto.Hash import SHA256
import struct

class Block():

    def get_hash(self):
        if not hasattr(self, 'hash'):
            self.hash = SHA256.new(self.raw_data)
        return self.hash

    def set_raw_data(self, raw_data):
        self.raw_data = raw_data
        if hasattr(self, 'hash'):
            del self.hash

    def parse(self):
        self.timestamp = struct.unpack_from("I", self.raw_data)
        self.prev_hash = struct.unpack_from("32s", self.raw_data, 4)
        randoms_count = struct.unpack_from("h", self.raw_data, 36)[0]
        if randoms_count > 0:
            self.randoms = struct.unpack_from("%sh" % randoms_count, self.raw_data, 38)

    def pack(self):
        block_format = "I32sh%sh" % len(self.randoms)
        block_struct = struct.Struct(block_format)
        return block_struct.pack(self.timestamp,
            self.prev_hash.digest(),
            len(self.randoms),
            *self.randoms)


    def set_signature(self, signature):
        self.signature = signature

    def verify_signature(self, pubkey):
        self.get_hash().digest()
        public_key.verify(self.get_hash(), self.signature)