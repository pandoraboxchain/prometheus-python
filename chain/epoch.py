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
        self.current_epoch = 1

    def get_current_timeframe_block_number(self):
        return self.get_block_number_from_timestamp(int(datetime.datetime.now().timestamp()))

    def get_block_number_from_timestamp(self, timestamp):
        time_diff = timestamp - self.dag.genesis_block().timestamp
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
        if epoch_number == 0: return 0
        return Epoch.get_duration() * (epoch_number - 1) + 1
    
    def get_epoch_end_block_number(epoch_number):
        if epoch_number == 0: return 0
        epoch_start_block = Epoch.get_epoch_start_block_number(epoch_number)
        return epoch_start_block + Epoch.get_duration() - 1
        
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
        validators_list = calculate_validators_indexes(epoch_seed, validators_count)
        print("calculated validators:", validators_list[0:3], validators_list[3:6], validators_list[6:9])
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
        round_iter = RoundIter(self.dag, block_hash, Round.PRIVATE)
        
        private_keys = []
        block_number = self.dag.get_block_number(block_hash)
        epoch_number = self.get_epoch_number(block_number)
        for i in range(block_number, Epoch.get_epoch_end_block_number(epoch_number)):
            private_keys.append(None)

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
                        if tx.sender_pubkey in public_keys:
                            assert False, "One sender published more than one public key. Aborting"
                        public_keys[tx.sender_pubkey] = tx.generated_pubkey
                        
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

        private_keys = self.get_private_keys_for_epoch(block_hash)
        public_keys = self.get_public_keys_for_epoch(block_hash)
        published_private_keys = self.filter_out_skipped_public_keys(private_keys, public_keys)
        random_pieces_list = self.get_random_splits_for_epoch(block_hash)

        print("pubkeys")
        for _, public_key in public_keys.items():
            print(Keys.to_visual_string(public_key))
        print("privkeys converted")
        private_key_count = 0
        for key in published_private_keys:
            if not key:
                print("None")
                continue
            pubkey = Keys.from_bytes(key).publickey()
            private_key_count += 1
            print(Keys.to_visual_string(pubkey))
        assert len(public_keys) == private_key_count, "Public and private keys must match"

        randoms_list = []
        for random_pieces in random_pieces_list:
            assert private_key_count == len(random_pieces), "Amount of splits must match amount of public keys"
            random = decode_random(random_pieces, Keys.list_from_bytes(published_private_keys))
            randoms_list.append(random)

        seed = sum_random(randoms_list)
        return seed

    def filter_out_skipped_public_keys(self, private_keys, public_keys):
        filtered_private_keys = []
        for private_key in private_keys:
            if private_key == None:
                filtered_private_keys.append(None)
            else:
                expected_public = Keys.from_bytes(private_key).publickey()
                if Keys.to_bytes(expected_public) in public_keys.values():
                    filtered_private_keys.append(private_key)
        return private_keys



    def is_last_block_of_epoch(self, block_number):
        if block_number == 0: return True

        epoch_number = self.get_epoch_number(block_number)        
        return block_number == Epoch.get_epoch_end_block_number(epoch_number)

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
        just_take_next_non_skipped_block = False
        for block in chain_iter:
            if self.is_last_block_of_epoch(chain_iter.block_number) or just_take_next_non_skipped_block:
                if block:                
                    return block.get_hash()
                else:
                    just_take_next_non_skipped_block = True
        return None
    
    # returns top blocks hashes and their corresponding epoch seeds
    def get_epoch_hashes(self):
        return self.tops_and_epochs

    def on_new_block_added(self, block):
        block_hash = block.get_hash()
        previous_top_epoch_hash = None
        for prev_hash in block.block.prev_hashes:
            if prev_hash in self.tops_and_epochs:
                previous_top_epoch_hash = self.tops_and_epochs[prev_hash]
                del self.tops_and_epochs[prev_hash]
        
        if previous_top_epoch_hash or not self.tops_and_epochs:
            self.tops_and_epochs[block_hash] = previous_top_epoch_hash
        
    # this method should be called before posibility of adding any new block, so it can recalculate epoch hashes
    def is_new_epoch_upcoming(self, upcoming_block_number):
        upcoming_epoch = self.get_epoch_number(upcoming_block_number)
        if upcoming_epoch > self.current_epoch:
            self.current_epoch = upcoming_epoch
            return True
        return False

    def accept_tops_as_epoch_hashes(self):
        for top, _ in self.tops_and_epochs.items():
            #this could be optimized to just taking previous hahash as 
            self.tops_and_epochs[top] = top

    def get_previous_epoch_hash(self, epoch_hash):
        block = self.dag.blocks_by_hash[epoch_hash]
        return self.find_epoch_hash_for_block(block.block.prev_hashes[0])


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