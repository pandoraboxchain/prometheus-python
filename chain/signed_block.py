import struct
import chain

from serialization.serializer import Serializer, Deserializer
from crypto.public import Public

class SignedBlock:

    def __init__(self):
        self.signature = None
        self.block = None

    def get_hash(self):
        return self.block.get_hash()

    def parse(self, raw_data):
        deserializer = Deserializer(raw_data)
        self.signatre = self.signature = deserializer.parse_signature()
        block_length = deserializer.parse_u32()
        raw_block = deserializer.read_and_move(block_length)
        self.block = chain.block.Block()
        self.block.parse(raw_block)
        return self

    def pack(self):
        raw_block = self.block.pack()
        raw_signed_block = Serializer.write_signature(self.signature)
        raw_signed_block += Serializer.write_u32(len(raw_block))
        raw_signed_block += raw_block
        return raw_signed_block

    def set_block(self, block):
        self.block = block

    def set_signature(self, signature):
        self.signature = signature

    def verify_signature(self, pubkey):
        block_hash = self.block.get_hash()
        return Public.verify(block_hash, self.signature, pubkey)

    def __hash__(self):
        return self.get_hash()