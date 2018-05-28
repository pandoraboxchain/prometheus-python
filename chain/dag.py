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
        self.blocks_by_hash = {}
        self.blocks_by_number = {}
        signed_genesis_block = SignedBlock()
        signed_genesis_block.set_block(self.genesis_block())
        self.add_signed_block(0, signed_genesis_block)

    def genesis_block(self):
        block = Block()
        block.timestamp = self.genesis_creation_time
        block.prev_hashes = [SHA256.new(b"0").digest()]
        block.randoms = []
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
        current_block_number = self.get_current_timeframe_block_number()
        self.add_signed_block(current_block_number, signed_block);
        print(block_hash.hex(), " was added to blockchain under number ", current_block_number)
        return signed_block
    
    def get_current_timeframe_block_number(self):
        time_diff = int(datetime.datetime.now().timestamp()) - self.genesis_block().timestamp
        return int(time_diff / BLOCK_TIME)

    def is_current_timeframe_block_present(self):
        genesis_timestamp = self.genesis_block().timestamp
        current_block_number = self.get_current_timeframe_block_number();
        time_from = genesis_timestamp + current_block_number * BLOCK_TIME
        time_to = genesis_timestamp + (current_block_number + 1) * BLOCK_TIME
        for _, block in self.blocks_by_hash.items():
            if time_from <= block.block.timestamp < time_to:
                return True
        return False
    
    def has_block_number(self, number):
        return number in self.blocks_by_number

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
    
    def get_era_hash(self, current_era_number):
        if current_era_number == 0:
            return self.genesis_block().get_hash().digest()

        era_duration = Epoch.ENCRYPTED_DURATION + Epoch.REVEALED_DURATION + Epoch.PARTIAL_DURATION
        previous_era_last_block_number = era_duration * current_era_number - 1
        return self.blocks_by_number[previous_era_last_block_number][0]
