import struct
from hashlib import sha256
from transaction.transaction_parser import TransactionParser
from serialization.serializer import Serializer, Deserializer

class Block:

    def __init__(self):
        self.timestamp = None
        self.prev_hashes = []
        self.system_txs = []

    def get_hash(self):
        return sha256(self.pack()).digest()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)

        self.timestamp = deserializer.parse_u32()

        hash_count = deserializer.parse_u16()

        self.prev_hashes = []
        for i in range(0, hash_count):
            prev_hash = deserializer.read_and_move(32)
            self.prev_hashes.append(prev_hash)

        system_tx_count = deserializer.parse_u8()
        self.system_txs = []
        for i in range(0, system_tx_count):
            tx = TransactionParser.parse(deserializer.data) # TODO: (is) Better to deserialize passing deserializer directly
            self.system_txs.append(tx)
            deserializer.read_and_move(tx.get_len() + 1)  # one byte for type

    def pack(self):
        raw_block = Serializer.write_u32(self.timestamp)

        raw_block += Serializer.write_u16(len(self.prev_hashes))
        for prev_hash in self.prev_hashes:
            raw_block += prev_hash

        if hasattr(self, 'system_txs'):
            raw_block += Serializer.write_u8(len(self.system_txs))

            for tx in self.system_txs:
                raw_block += TransactionParser.pack(tx)
        else:
            raw_block += Serializer.write_u8(0)

        return raw_block

    def __hash__(self):
        return self.get_hash()