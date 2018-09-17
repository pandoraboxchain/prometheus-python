import struct

from Crypto.Hash import SHA256
from core.transaction.transaction_parser import TransactionParser


class Block:

    def __init__(self):
        self.timestamp = None
        self.prev_hashes = []
        self.system_txs = []

    def get_hash(self):
        return SHA256.new(self.pack()).digest()

    def parse(self, raw_data):
        self.timestamp = struct.unpack_from("I", raw_data)[0]
        hash_count = struct.unpack_from("h", raw_data, 4)[0]
        self.prev_hashes = []
        for i in range(0, hash_count):
            hash_start = 6 + 32 * i
            hash_end = hash_start + 32
            prev_hash = raw_data[hash_start: hash_end]
            self.prev_hashes.append(prev_hash)
        offset = 6 + 32 * hash_count
        system_tx_count = struct.unpack_from("B", raw_data, offset)[0]
        offset += 1
        self.system_txs = []
        for i in range(0, system_tx_count):
            tx = TransactionParser.parse(raw_data[offset:])
            self.system_txs.append(tx)
            offset += tx.get_len() + 1  # one byte for type

    def pack(self):
        raw_block = struct.pack("I", self.timestamp)
        raw_block += struct.pack("h", len(self.prev_hashes))
        for prev_hash in self.prev_hashes:
            raw_block += prev_hash

        if hasattr(self, 'system_txs'):
            raw_block += struct.pack("B", len(self.system_txs))
            for tx in self.system_txs:
                raw_block += TransactionParser.pack(tx)
        else:
            raw_block += struct.pack("B", 0)

        return raw_block


