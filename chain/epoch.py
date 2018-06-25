import datetime
from transaction.commits_set import CommitsSet
from crypto.dec_part_random import decode_random_using_raw_key
from crypto.sum_random import sum_random, calculate_validators_numbers
from crypto.secret import recover_splits, enc_part_secret, decode_random, encode_splits
from crypto.keys import Keys
from transaction.transaction import PrivateKeyTransaction, SplitRandomTransaction, PublicKeyTransaction
from chain.dag import ChainIter
BLOCK_TIME = 4

class Round():
    PUBLIC = 0
    RANDOM = 1
    PRIVATE = 2

    PUBLIC_DURATION = 3
    RANDOM_DURATION = 3
    PRIVATE_DURATION = 3

class Epoch():

    cached_epoch_validators = {}

    def __init__(self, dag):
        self.dag = dag

    def get_current_timeframe_block_number(self):
        time_diff = int(datetime.datetime.now().timestamp()) - self.dag.genesis_block().timestamp
        return int(time_diff / BLOCK_TIME)

    def is_current_timeframe_block_present(self):
        genesis_timestamp = self.dag.genesis_block().timestamp
        current_block_number = self.get_current_timeframe_block_number()
        time_from = genesis_timestamp + current_block_number * BLOCK_TIME
        time_to = genesis_timestamp + (current_block_number + 1) * BLOCK_TIME
        for _, block in self.dag.blocks_by_hash.items():
            if time_from <= block.block.timestamp < time_to:
                return True
        return False

    def get_current_round(self):
        current_block_number = self.get_current_timeframe_block_number()
        return self.get_round_by_block_number(current_block_number)

    @staticmethod
    def get_round_by_block_number(current_block_number):
        epoch_number = Epoch.get_epoch_number(current_block_number)
        epoch_start_block = Epoch.get_epoch_start_block_number(epoch_number)
        if current_block_number < epoch_start_block + Round.PUBLIC_DURATION:
            return Round.PUBLIC
        elif current_block_number < epoch_start_block + Round.PUBLIC_DURATION + Round.RANDOM_DURATION:
            return Round.RANDOM
        else:
            return Round.PRIVATE

    @staticmethod
    def get_duration():
        return Round.PUBLIC_DURATION + Round.RANDOM_DURATION + Round.PRIVATE_DURATION

    @staticmethod
    def get_epoch_number(current_block_number):
        if current_block_number == 0:
            return 0 
        return (current_block_number - 1) // Epoch.get_duration() + 1 #because genesis block is last block of era zero

    @staticmethod
    def get_epoch_start_block_number(epoch_number):
        return Epoch.get_duration() * (epoch_number - 1) + 1
        
    def get_epoch_hash(self, epoch_number):
        if epoch_number == 0:
            return None
        if epoch_number == 1:
            return self.dag.genesis_block().get_hash()

        previous_era_last_block_number = self.get_epoch_start_block_number(epoch_number) - 1
        era_identifier_block = self.dag.blocks_by_number[previous_era_last_block_number][0]
        return era_identifier_block.block.get_hash()
    
    def calculate_validators_numbers(self, epoch_number, validators_count):
        if epoch_number in self.cached_epoch_validators:
            return self.cached_epoch_validators[epoch_number]

        epoch_seed = self.calculate_epoch_seed(epoch_number)
        validators_list = calculate_validators_numbers(epoch_seed, validators_count, Epoch.get_duration())
        self.cached_epoch_validators[epoch_number] = validators_list
        return validators_list

    def get_private_keys_for_epoch(self, epoch_number):
        #TODO properly handle block absence and multiple blocks with the same numbers
        
        pk_blocks = self.get_all_blocks_for_round(epoch_number, Round.PRIVATE)
        
        private_keys = []

        for block in pk_blocks:
            if block == None:
                private_keys.append(None)
            else:
                for tx in block.system_txs:
                    if isinstance(tx, PrivateKeyTransaction):
                        private_keys.append(tx.key)
                        break #only one private key transaction can exist and it should be signed by block signer

        #we need to take only unique keys as malicious user could send two or more blocks at the same time
        private_keys = Epoch.make_unique_list(private_keys)

        print("This epoch private keys")
        for pk in private_keys:
            Keys.display(Keys.from_bytes(pk).publickey())

        return private_keys

    def get_public_keys_for_epoch(self, epoch_number):
        blocks = self.get_all_blocks_for_round(epoch_number, Round.PUBLIC)
        
        public_keys = {}

        for block in blocks:
            for tx in block.system_txs:
                if isinstance(tx, PublicKeyTransaction):
                    if not tx.sender_pubkey in public_keys:
                        public_keys[tx.sender_pubkey] = [tx.generated_pubkey]
                    else:
                        public_keys[tx.sender_pubkey].append(tx.generated_pubkey)
                        
        return public_keys

    def get_random_splits_for_epoch(self, epoch_number):
        random_pieces_list = []
        blocks = self.get_all_blocks_for_round(epoch_number, Round.RANDOM)
        for block in blocks:
            for tx in block.system_txs:
                if isinstance(tx, SplitRandomTransaction):
                    random_pieces_list.append(tx.pieces)
        
        unique_randoms = Epoch.make_unique_list(random_pieces_list)
        return unique_randoms

    @staticmethod
    def get_range_for_round(epoch_number, round_type):
        round_start = Epoch.get_epoch_start_block_number(epoch_number)
        round_end = 0
        if round_type == Round.PUBLIC:
            round_end += round_start + Round.PUBLIC_DURATION
        elif round_type == Round.RANDOM:
            round_start += Round.PUBLIC_DURATION
            round_end = round_start + Round.RANDOM_DURATION
        elif round_type == Round.PRIVATE:
            round_start += Round.PUBLIC_DURATION + Round.RANDOM_DURATION
            round_end = round_start + Round.PRIVATE_DURATION
        round_end -= 1
        return (round_start, round_end)

    def get_all_blocks_for_round(self, epoch_number, round_type):
        round_start, round_end = Epoch.get_range_for_round(epoch_number, round_type)
        
        blocks = []
        for i in range(round_start, round_end + 1):
            if i in self.dag.blocks_by_number:
                blocks_at_number = self.dag.blocks_by_number[i]
                for block in blocks_at_number:
                    blocks.append(block.block)

        return blocks

    def get_private_keys_for_epoch_from_block(self, block_hash):

        block_number = self.dag.get_block_number(block_hash)
        epoch_number = self.get_epoch_number(block_number)
        round_start = self.get_epoch_start_block_number(epoch_number) + Round.PUBLIC_DURATION + Round.RANDOM_DURATION
        round_end = round_start + Round.PRIVATE_DURATION

        private_keys = []
        while block_number >= round_start:
            if self.dag.get_block_number(block_hash) != block_number:
                private_keys.append(None)
                continue

            block = self.dag.blocks_by_hash[block_hash]
            for tx in block.system_txs:
                if isinstance(tx, PrivateKeyTransaction):
                    private_keys.append(tx.key)
                    break #only one private key transaction can exist and it should be signed by block signer
            
            block = block.prev_hashes[0] #intentionally take first previous block as network would not accept blocks with other private keys
            block_number -= 1
        
        reversed(private_keys)

        return private_keys 

    def calculate_epoch_seed_from_block(self, block_hash):
        if block_hash == self.dag.genesis_block().get_hash():
            return 0
        
        block_number = self.dag.get_block_number(block_hash)
        assert self.is_last_block_of_epoch(block_number), "Epoch seed should be calculated from last epoch block"


    def calculate_epoch_seed(self, epoch_number):
        if epoch_number == 1:
            return 0
        private_keys = self.get_private_keys_for_epoch(epoch_number - 1)
        random_pieces_list = self.get_random_splits_for_epoch(epoch_number - 1)
        randoms_list = []
        for random_pieces in random_pieces_list:
            random = decode_random(random_pieces, Keys.list_from_bytes(private_keys))
            randoms_list.append(random)

        seed = sum_random(randoms_list)
        return seed
    
    def is_last_block_of_epoch(self, block_number):
        epoch_number = self.get_epoch_number(block_number)        
        epoch_start_block = self.get_epoch_start_block_number(epoch_number)
        return block_number == epoch_start_block + Epoch.get_duration() - 1

    def convert_to_epoch_block_number(self, global_block_number):
        epoch_number = self.get_epoch_number(global_block_number)
        epoch_start_block_number = self.get_epoch_start_block_number(epoch_number)
        return global_block_number - epoch_start_block_number

    @staticmethod
    def make_unique_list(list): #TODO move into separate file
        unique_list = [] 
        for item in list:       
            if not item in unique_list:
                unique_list.append(item)
        return unique_list

class RoundIter:
    def __init__(self, dag, block_hash, round_type):
        block_number = dag.get_block_number(block_hash)
        epoch_number = Epoch.get_epoch_number(block_number)
        round_start, round_end = Epoch.get_range_for_round(epoch_number, round_type)
        
        self.round_end = round_start
        self.chain_iter = ChainIter(dag, block_hash)
        while self.chain_iter.block_number > round_end + 1:
            self.chain_iter.next()

    def __iter__(self):
        return self

    def next(self):
        block = self.chain_iter.next()
        block_number = self.chain_iter.block_number
        if block_number < self.round_end:
            raise StopIteration()
        
        return block