from Crypto.Hash import SHA256
import struct
from block import Block

class SignedBlock():

    def parse(self, raw_data):
        signature_len = struct.unpack_from("h", raw_data)[0]
        self.signature = struct.unpack_from("%sh" % signature_len, raw_data, 2)[0]
        block_length = struct.unpack_from("h", raw_data, 2 + signature_len)[0]
        raw_block = struct.unpack_from("%sh" % block_length, raw_data, 2 + signature_len + 2)[0]
        self.block = Block()
        self.block.parse(raw_block)

    def pack(self):
        #signature_len = hex(self.signature)
        #raw_signed_block = struct.pack("h", signature_len)
        #raw_signed_block += struct.pack("%sh" % signature_len, self.signature)
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
        pubkey.verify(block_hash, self.signature)
