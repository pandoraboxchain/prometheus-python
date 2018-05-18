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
        self.timestamp = struct.unpack_from("I", self.raw_data)[0]
        hash_count = struct.unpack_from("h", self.raw_data, 4)[0]
        self.prev_hashes = []
        for i in range(0, hash_count):
            prev_hash = struct.unpack_from("32s", self.raw_data, 6 + 32 * i)[0]
            self.prev_hashes.append(prev_hash)
        offset = 6 + 32 * hash_count
        randoms_count = struct.unpack_from("h", self.raw_data, offset)[0]
        if randoms_count > 0:
            self.randoms = struct.unpack_from("%sh" % randoms_count, self.raw_data, offset + 2)

    def pack(self):
        raw_block = struct.pack("I", self.timestamp)
        raw_block += struct.pack("h", len(self.prev_hashes))
        for prev_hash in self.prev_hashes:
            raw_block += struct.pack("32s", prev_hash)
        raw_block += struct.pack("h%sh" % len(self.randoms), len(self.randoms), *self.randoms)
        return raw_block

    def set_signature(self, signature):
        self.signature = signature

    def verify_signature(self, pubkey):
        self.get_hash().digest()
        public_key.verify(self.get_hash(), self.signature)
