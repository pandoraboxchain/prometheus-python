from chain.block import Block
from chain.signed_block import SignedBlock
from Crypto.Hash import SHA256
import binascii

class Dag():
    
    def __init__(self, genesis_creation_time):
        self.genesis_creation_time = genesis_creation_time
        self.blocks_by_hash = {}
        self.blocks_by_number = {}
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.add_signed_block(0, signed_genesis_block)
        print("Genesis block hash", self.genesis_block().get_hash().hex())

    def genesis_block(self):
        block = Block()
        block.timestamp = self.genesis_creation_time
        block.prev_hashes = []
        return block

    def add_signed_block(self, index, block):
        block_hash = block.block.get_hash()
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

    def has_block_number(self, number):
        return number in self.blocks_by_number
    
    def get_block_number(self, block_hash):
        for number, block_list_by_number in self.blocks_by_number.items():
            for block_by_number in block_list_by_number:
                if block_by_number.block.get_hash() == block_hash:
                    return number
        return -1
    
    def calculate_chain_length(self, top_block_hash):
        length = [0]
        top_block = self.blocks_by_hash[top_block_hash]
        self.recursive_previous_block_count(top_block, length)
        return length[0]

    def recursive_previous_block_count(self, block, count):
        count[0] += 1   #trick to emulate pass by reference 
        for prev_hash in block.block.prev_hashes:
            block = self.blocks_by_hash[prev_hash]
            self.recursive_previous_block_count(block, count)


        
