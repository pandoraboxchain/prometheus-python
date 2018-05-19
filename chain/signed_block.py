from Crypto.Hash import SHA256
import struct
from chain.block import Block

class SignedBlock():

    def parse(self, raw_data):
        self.signature = int.from_bytes(raw_data[0:128], byteorder='big')
        block_length = struct.unpack_from("h", raw_data, 128)[0]
        raw_block = raw_data[130:130+block_length]
        self.block = Block()
        self.block.parse(raw_block)

    def pack(self):
        raw_block = self.block.pack()
        raw_signed_block = self.signature.to_bytes(128, byteorder='big')
        raw_signed_block += struct.pack("h", len(raw_block))
        raw_signed_block += raw_block
        return raw_signed_block

    def set_block(self, block):
        self.block = block

    def set_signature(self, signature):
        self.signature = signature

    def verify_signature(self, pubkey):
        block_hash = self.block.get_hash().digest()
        return pubkey.verify(block_hash, (self.signature,))
