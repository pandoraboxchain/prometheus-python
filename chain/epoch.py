import datetime
from transaction.commits_set import CommitsSet
from crypto.dec_part_random import decode_random_using_raw_key
from crypto.sum_random import sum_random, calculate_validators_numbers
from crypto.secret import dec_part_secret_raw_key, recover_splits, enc_part_secret
from transaction.transaction import PrivateKeyTransaction, SplitRandomTransaction, PublicKeyTransaction

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
        current_block_number = self.get_current_timeframe_block_number();
        time_from = genesis_timestamp + current_block_number * BLOCK_TIME
        time_to = genesis_timestamp + (current_block_number + 1) * BLOCK_TIME
        for _, block in self.dag.blocks_by_hash.items():
            if time_from <= block.block.timestamp < time_to:
                return True
        return False

    def get_current_round(self):
        current_block_number = self.get_current_timeframe_block_number();
        return self.get_round_by_block_number(current_block_number)

    def get_round_by_block_number(self, current_block_number):
        epoch_number = self.get_epoch_number(current_block_number)
        epoch_start_block = self.get_epoch_start_block_number(epoch_number)
        if current_block_number <= epoch_start_block + Round.PUBLIC_DURATION:
            return Round.PUBLIC
        elif current_block_number <= epoch_start_block + Round.PUBLIC_DURATION + Round.RANDOM_DURATION:
            return Round.RANDOM
        else:
            return Round.PRIVATE

    def get_duration():
        return Round.PUBLIC_DURATION + Round.RANDOM_DURATION + Round.PRIVATE_DURATION

    def get_epoch_number(self, current_block_number):
        if current_block_number == 0:
            return 0 
        return (current_block_number - 1) // Epoch.get_duration() + 1 #because genesis block is last block of era zero

    def get_epoch_start_block_number(self, epoch_number):
        return Epoch.get_duration() * (epoch_number - 1) + 1
        
    def get_epoch_hash(self, epoch_number):
        if epoch_number == 0:
            return None
        if epoch_number == 1:
            return self.dag.genesis_block().get_hash().digest()

        previous_era_last_block_number = self.get_epoch_start_block_number(epoch_number) - 1
        era_identifier_block = self.dag.blocks_by_number[previous_era_last_block_number][0]
        return era_identifier_block.block.get_hash().digest()
    
    def calculate_validators_numbers(self, epoch_number, validators_count):
        if epoch_number in self.cached_epoch_validators:
            return self.cached_epoch_validators[epoch_number]

        epoch_seed = self.calculate_epoch_seed(epoch_number)
        validators_list = calculate_validators_numbers(epoch_seed, validators_count, Epoch.get_duration())
        self.cached_epoch_validators[epoch_number] = validators_list
        return validators_list

    def get_private_keys_for_epoch(self, epoch_number):
        pk_blocks = self.get_all_blocks_for_round(epoch_number, Round.PRIVATE)
        
        private_keys = []

        for block in pk_blocks:
            for tx in block.system_txs:
                if isinstance(tx, PrivateKeyTransaction):
                    private_keys.append(tx.key)
                    break #only one private key transaction can exists and it should be signed by block signer
        
        return private_keys

    def get_random_pieces_for_epoch(self, epoch_number):
        random_pieces_list = []
        blocks = self.get_all_blocks_for_round(epoch_number, Round.RANDOM)
        for block in blocks:
            for tx in block.system_txs:
                if isinstance(tx, SplitRandomTransaction):
                    random_pieces_list.append(tx.pieces)
        
        return random_pieces_list

    def get_all_blocks_for_round(self, epoch_number, round_type):
        round_start = self.get_epoch_start_block_number(epoch_number)
        round_end = 0
        if round_type == Round.PUBLIC:
            round_end += round_start + Round.PUBLIC_DURATION
        elif round_type == Round.RANDOM:
            round_start += Round.PUBLIC_DURATION
            round_end = round_start + Round.RANDOM_DURATION
        elif round_type == Round.PRIVATE:
            round_start += Round.PUBLIC_DURATION + Round.RANDOM_DURATION
            round_end = round_start + Round.PRIVATE_DURATION
        
        blocks = []
        for i in range(round_start, round_end):
            blocks_at_number = self.dag.blocks_by_number[i]
            for block in blocks_at_number:
                blocks.append(block.block)

        return blocks
    
    def decode_random(self, random_pieces, private_keys):
        splits = []
        for i in range(0, len(random_pieces)):
            piece = random_pieces[i]
            private_key = private_keys[i]
            split = dec_part_secret_raw_key(private_key, piece, i)
            splits.append(split)

        return recover_splits(splits)

    def encode_splits(self, splits, public_keys):
        encoded_splits = []
        for i in range(0, len(splits)):
            encoded_split = enc_part_secret(public_keys[i], splits[i])
            encoded_splits.append(encoded_split)
        
        return encoded_splits

    def calculate_epoch_seed(self, epoch_number):
        if epoch_number == 1:
            return 0
        
        epoch_hash = self.get_epoch_hash(epoch_number)
        private_keys = self.get_private_keys_for_epoch(epoch_number - 1)
        random_pieces_list = self.get_random_pieces_for_epoch(epoch_number - 1)

        randoms_list = []
        for random_pieces in random_pieces_list:
            random = self.decode_random(random_pieces, private_keys)
            randoms_list.append(random)

        seed = sum_random(randoms_list)
        return seed
    
    def backwards_collect_commit_blocks_for_epoch(self, epoch_number, starting_block_hash):
        commits = []
        block = self.dag.blocks_by_hash[starting_block_hash].block
        self.recursive_collect_commit_blocks(block, epoch_number, commits) 
        return commits

    def recursive_collect_commit_blocks(self, block, epoch_number, commits):
        block_number = self.dag.get_block_number(block.get_hash().digest())
        if self.get_epoch_number(block_number) != epoch_number:
            return

        commits.append(block)

        for prev_hash in block.prev_hashes:
            block = self.dag.blocks_by_hash[prev_hash].block
            self.recursive_collect_commit_blocks(block, epoch_number, commits)
        
    def collect_reveals_for_epoch(self, epoch_number):
        reveals = []
        epoch_start_block = self.get_epoch_start_block_number(epoch_number)
        reveal_round_start_block = epoch_start_block + Round.PUBLIC_DURATION
        reveal_round_end_block = reveal_round_start_block + Round.RANDOM_DURATION
        for i in range(reveal_round_start_block,reveal_round_end_block):
            block_list = self.dag.blocks_by_number[i]
            for block in block_list:
                if hasattr(block.block, "system_txs"):
                    for tx in block.block.system_txs:
                        reveals.append(tx)
        return reveals
    
    def is_last_block_of_era(self, block_number):
        epoch_number = self.get_epoch_number(block_number)        
        epoch_start_block = self.get_epoch_start_block_number(epoch_number)
        return block_number == epoch_start_block + Epoch.get_duration() - 1

    def get_validator_number(self, block_number, validators_count):
        epoch_number = self.get_epoch_number(block_number)
        epoch_start_block_number = self.get_epoch_start_block_number(epoch_number)
        block_number_in_epoch = block_number - epoch_start_block_number
        validators_list = self.get_epoch_validators_list(epoch_number)
        return validators_list[block_number_in_epoch]

    def convert_to_epoch_block_number(self, global_block_number):
        epoch_number = self.get_epoch_number(global_block_number)
        epoch_start_block_number = self.get_epoch_start_block_number(epoch_number)
        return global_block_number - epoch_start_block_number

    
    
