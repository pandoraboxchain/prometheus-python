from block import Block
from signed_block import SignedBlock
from Crypto.Hash import SHA256

class Dag():
    
    def __init__(self):
        self.blocks = {}
        genesis_hash = self.genesis_block().get_hash();
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.blocks[genesis_hash] = signed_genesis_block

    def genesis_block(self):
        block = Block()
        block.timestamp = 0
        block.prev_hashes = [SHA256.new(b"0").digest()]
        block.randoms = []
        return block

