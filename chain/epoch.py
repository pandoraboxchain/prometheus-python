import datetime
from transaction.commits_set import CommitsSet
from crypto.dec_part_random import decode_random_using_raw_key
from crypto.sum_random import sum_random, calculate_validators_indexes
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

    def __init__(self, dag):
        self.dag = dag
        self.tops_and_epochs = { dag.genesis_block().get_hash() : dag.genesis_block().get_hash() }

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
        if epoch_number == 0:
            return 0
        return Epoch.get_duration() * (epoch_number - 1) + 1
        
    def get_epoch_hash(self, epoch_number):
        if epoch_number == 0:
            return None
        if epoch_number == 1:
            return self.dag.genesis_block().get_hash()

        previous_era_last_block_number = self.get_epoch_start_block_number(epoch_number) - 1
        era_identifier_block = self.dag.blocks_by_number[previous_era_last_block_number][0]
        return era_identifier_block.block.get_hash()
    
    def calculate_validators_indexes(self, epoch_hash, validators_count):
        epoch_seed = self.calculate_epoch_seed(epoch_hash)
        validators_list = calculate_validators_indexes(epoch_seed, validators_count, Epoch.get_duration())
        return validators_list

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

    def get_private_keys_for_epoch(self, block_hash):
        private_keys = []
        round_iter = RoundIter(self.dag, block_hash, Round.PRIVATE)

        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, PrivateKeyTransaction):
                        private_keys.append(tx.key)
                        break #only one private key transaction can exist and it should be signed by block signer
            else:
                private_keys.append(None)
                
        private_keys = list(reversed(private_keys))

        return private_keys
    
    def get_public_keys_for_epoch(self, block_hash):
        public_keys = {}
        round_iter = RoundIter(self.dag, block_hash, Round.PUBLIC)

        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, PublicKeyTransaction):
                        if not tx.sender_pubkey in public_keys:
                            public_keys[tx.sender_pubkey] = [tx.generated_pubkey]
                        else:
                            public_keys[tx.sender_pubkey].append(tx.generated_pubkey)
                        
        return public_keys
    

    def get_random_splits_for_epoch(self, block_hash):
        random_pieces_list = []
        round_iter = RoundIter(self.dag, block_hash, Round.RANDOM)
        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, SplitRandomTransaction):
                        random_pieces_list.append(tx.pieces)
        
        random_pieces_list = list(reversed(random_pieces_list))
        # unique_randoms = Epoch.make_unique_list(random_pieces_list)
        return random_pieces_list

    def calculate_epoch_seed(self, block_hash):
        if block_hash == self.dag.genesis_block().get_hash():
            return 0
        
        block_number = self.dag.get_block_number(block_hash)
        if not self.is_last_block_of_epoch(block_number):
            x = 0
        assert self.is_last_block_of_epoch(block_number), "Epoch seed should be calculated from last epoch block"

        private_keys = self.get_private_keys_for_epoch(block_hash)
        random_pieces_list = self.get_random_splits_for_epoch(block_hash)
        randoms_list = []
        for random_pieces in random_pieces_list:
            random = decode_random(random_pieces, Keys.list_from_bytes(private_keys))
            randoms_list.append(random)

        seed = sum_random(randoms_list)
        return seed

    
    def is_last_block_of_epoch(self, block_number):
        if block_number == 0: return True

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
    
    def find_epoch_hash_for_block(self, block_hash):
        chain_iter = ChainIter(self.dag, block_hash)
        for block in chain_iter:
            if self.is_last_block_of_epoch(chain_iter.block_number):
                return block.get_hash()
        return None
    
    # returns top blocks hashes and their corresponding epoch seeds
    def get_epoch_hashes(self):
        return self.tops_and_epochs

    def on_new_block_added(self, block):
        block_hash = block.get_hash()
        previous_top_epoch_hash = None
        for prev_hash in block.block.prev_hashes:
            if prev_hash in self.tops_and_epochs:
                prev_block_number = self.dag.get_block_number(prev_hash)
                prev_block_epoch_number = Epoch.get_epoch_number(prev_block_number)
                block_number = self.dag.get_block_number(block_hash)
                block_epoch_number = Epoch.get_epoch_number(block_number)

                #if this block is from new epoch, then previous block must be last, so we may assume it is epoch hash
                if prev_block_epoch_number < block_epoch_number:
                    previous_top_epoch_hash = prev_hash
                else: #just preserve epoch hash
                    previous_top_epoch_hash = self.tops_and_epochs[prev_hash]
                del self.tops_and_epochs[prev_hash]
        
        if previous_top_epoch_hash or not self.tops_and_epochs:
            self.tops_and_epochs[block_hash] = previous_top_epoch_hash


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

    def __next__(self):
        block = self.chain_iter.next()
        block_number = self.chain_iter.block_number
        if block_number < self.round_end:
            raise StopIteration()
        
        return block
    
    def next(self):
        return self.__next__()