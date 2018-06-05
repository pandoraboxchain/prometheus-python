from chain.block import Block
from chain.signed_block import SignedBlock
from Crypto.Hash import SHA256
import binascii

BLOCK_TIME = 5

class Dag():
    
    def __init__(self, genesis_creation_time):
        self.genesis_creation_time = genesis_creation_time
        self.blocks_by_hash = {}
        self.blocks_by_number = {}
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.add_signed_block(0, signed_genesis_block)

    def genesis_block(self):
        block = Block()
        block.timestamp = self.genesis_creation_time
        block.prev_hashes = []
        return block

    def add_signed_block(self, index, block):
        block_hash = block.block.get_hash().digest()
        self.blocks_by_hash[block_hash] = block
        if index in self.blocks_by_number:
            self.blocks_by_number[index].append(block)
        else:
            self.blocks_by_number[index] = [block]
    
    def get_top_blocks(self):
        links = []
        for block_hash, signed_block in self.blocks_by_hash.items():
            links += signed_block.block.prev_hashes
        
        top_blocks = self.blocks_by_hash.copy();
        for link in links:
            if link in top_blocks:
                del top_blocks[link]

        return top_blocks

    def test_top_blocks(self):
        block1 = Block()
        block1.prev_hashes = [self.genesis_block().get_hash().digest()]
        block1.timestamp = 32452345234;
        block1.randoms = []
        signed_block1 = SignedBlock()
        signed_block1.set_block(block1);
        self.add_signed_block(1,signed_block1);

        block2 = Block()
        block2.prev_hashes = [block1.get_hash().digest()];
        block2.timestamp = 32452345;
        block2.randoms = []
        signed_block2 = SignedBlock()
        signed_block2.set_block(block2);
        self.add_signed_block(2,signed_block2);

        block3 = Block()
        block3.prev_hashes = [block1.get_hash().digest()];
        block3.timestamp = 1231827398;
        block3.randoms = []
        signed_block3 = SignedBlock()
        signed_block3.set_block(block3);
        self.add_signed_block(3,signed_block3);

        for keyhash in self.blocks_by_hash:
            print(binascii.hexlify(keyhash))

        top_hashes = self.get_top_blocks();

        print("tops")
        for keyhash in top_hashes:
            print(binascii.hexlify(keyhash))

    def has_block_number(self, number):
        return number in self.blocks_by_number
    
    def get_block_number_by_hash(self, block_hash):
        block_by_hash = self.blocks_by_hash[block_hash]
        for number, block_by_number in self.blocks_by_number.items():
            if block_by_hash == block_by_number:
                return number
        return -1