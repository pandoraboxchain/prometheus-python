from chain.block import Block
from chain.signed_block import SignedBlock
from tools.time import Time

class BlockFactory():

    def create_block_dummy(prev_hashes):
        block = Block()
        block.prev_hashes = prev_hashes
        block.timestamp = Time.get_current_time()
        block.system_txs = []
        return block

    def create_block_with_timestamp(prev_hashes, timestamp):
        block = Block()
        block.prev_hashes = prev_hashes
        block.timestamp = timestamp
        block.system_txs = []
        return block
    
    def sign_block(block, private):
        block_hash = block.get_hash()
        signature = private.sign(block_hash, 0)[0]  #for some reason it returns tuple with second item being None
        signed_block = SignedBlock()
        signed_block.set_block(block)
        signed_block.set_signature(signature)
        return signed_block