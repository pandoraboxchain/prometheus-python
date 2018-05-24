from chain.block import Block
from chain.signed_block import SignedBlock
from Crypto.Hash import SHA256
import binascii
import datetime

BLOCK_TIME = 5

class Epoch():
    ENCRYPTED = 0
    REVEALED = 1
    PARTIAL = 2

    ENCRYPTED_DURATION = 100
    REVEALED_DURATION = 200
    PARTIAL_DURATION = 3

class Dag():
    
    def __init__(self, genesis_creation_time):
        self.genesis_creation_time = genesis_creation_time
        self.blocks = {}
        genesis_hash = self.genesis_block().get_hash();
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.blocks[genesis_hash.digest()] = signed_genesis_block

    def genesis_block(self):
        block = Block()
        block.timestamp = self.genesis_creation_time
        block.prev_hashes = [SHA256.new(b"0").digest()]
        block.randoms = []
        return block

    def add_signed_block(self, signed_block):
        block_hash = signed_block.block.get_hash();
        self.blocks[block_hash.digest()] = signed_block
    
    def get_top_blocks(self):
        links = []
        for block_hash, signed_block in self.blocks.items():
            links += signed_block.block.prev_hashes
        
        top_blocks = self.blocks.copy();
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
        self.blocks[block1.get_hash().digest()] = signed_block1;

        block2 = Block()
        block2.prev_hashes = [block1.get_hash().digest()];
        block2.timestamp = 32452345;
        block2.randoms = []
        signed_block2 = SignedBlock()
        signed_block2.set_block(block2);
        self.blocks[block2.get_hash().digest()] = signed_block2;

        block3 = Block()
        block3.prev_hashes = [block1.get_hash().digest()];
        block3.timestamp = 1231827398;
        block3.randoms = []
        signed_block3 = SignedBlock()
        signed_block3.set_block(block3);
        self.blocks[block3.get_hash().digest()] = signed_block3;

        for keyhash in self.blocks:
            print(binascii.hexlify(keyhash))

        top_hashes = self.get_top_blocks();

        print("tops")
        for keyhash in top_hashes:
            print(binascii.hexlify(keyhash))

    def sign_block(self, private): #TODO move somewhere more approptiate
        block = Block()
        block.prev_hashes = [*self.get_top_blocks()]
        block.timestamp = int(datetime.datetime.now().timestamp())
        block.randoms = []

        block_hash = block.get_hash().digest()
        signature = private.sign(block_hash, 0)[0]  #for some reason it returns tuple with second item being None
        signed_block = SignedBlock()
        signed_block.set_block(block)
        signed_block.set_signature(signature)
        self.blocks[block_hash] = signed_block
        print(block_hash.hex(), " was added to blockchain")
        return signed_block
    
    def get_current_timeframe_block_number(self):
        time_diff = int(datetime.datetime.now().timestamp()) - self.genesis_block().timestamp
        return int(time_diff / BLOCK_TIME)

    def is_current_timeframe_block_present(self):
        genesis_timestamp = self.genesis_block().timestamp
        current_block_number = self.get_current_timeframe_block_number();
        time_from = genesis_timestamp + current_block_number * BLOCK_TIME
        time_to = genesis_timestamp + (current_block_number + 1) * BLOCK_TIME
        for _, block in self.blocks.items():
            if time_from <= block.block.timestamp < time_to:
                return True
        return False

    def get_current_epoch(self):
        current_block_number = self.get_current_timeframe_block_number();
        return self.get_epoch_by_block_number(current_block_number)

    def get_epoch_by_block_number(self, current_block_number):
        era_duration = Epoch.ENCRYPTED_DURATION + Epoch.REVEALED_DURATION + Epoch.PARTIAL_DURATION
        era_number = self.get_era_number(current_block_number)
        era_start_block = era_number * era_duration
        print(current_block_number, "is in era", era_number)
        if current_block_number <=  era_start_block + Epoch.ENCRYPTED_DURATION:
            return Epoch.ENCRYPTED
        elif current_block_number <=  era_start_block + Epoch.ENCRYPTED_DURATION + Epoch.REVEALED_DURATION:
            return Epoch.REVEALED
        else:
            return Epoch.PARTIAL

    def get_era_number(self, current_block_number):
        era_duration = Epoch.ENCRYPTED_DURATION + Epoch.REVEALED_DURATION + Epoch.PARTIAL_DURATION
        return current_block_number // era_duration