from Crypto.Hash import SHA256
import struct

class Block():

    def get_hash(self):
        return SHA256.new(self.pack())

    def parse(self, raw_data):
        self.timestamp = struct.unpack_from("I", raw_data)[0]
        hash_count = struct.unpack_from("h", raw_data, 4)[0]
        self.prev_hashes = []
        for i in range(0, hash_count):
            hash_start = 6 + 32 * i
            hash_end = hash_start + 32
            prev_hash = raw_data[hash_start : hash_end]
            self.prev_hashes.append(prev_hash)
        offset = 6 + 32 * hash_count
        randoms_count = struct.unpack_from("h", raw_data, offset)[0]
        if randoms_count > 0:
            self.randoms = struct.unpack_from("%sh" % randoms_count, raw_data, offset + 2)

    def pack(self):
        raw_block = struct.pack("I", self.timestamp)
        raw_block += struct.pack("h", len(self.prev_hashes))
        for prev_hash in self.prev_hashes:
            raw_block += prev_hash
        if hasattr(self, 'randoms') and len(self.randoms) > 0:
            raw_block += struct.pack("h%sh" % len(self.randoms), len(self.randoms), *self.randoms)
        else:
            raw_block += struct.pack("h", 0)
        return raw_block
