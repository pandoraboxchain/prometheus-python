from tools.time import Time
from crypto.sum_random import sum_random, calculate_validators_indexes
from crypto.secret import decode_random
from crypto.keys import Keys
from crypto.entropy import Entropy
from crypto.private import Private
from transaction.secret_sharing_transactions import PrivateKeyTransaction, SplitRandomTransaction, PublicKeyTransaction
from transaction.commit_transactions import CommitRandomTransaction, RevealRandomTransaction
from chain.dag import ChainIter
from chain.params import Round, ROUND_DURATION, BLOCK_TIME


class Epoch:

    def __init__(self, dag):
        self.dag = dag
        self.tops_and_epochs = {dag.genesis_block().get_hash(): dag.genesis_block().get_hash()}
        self.dag.subscribe_to_new_top_block_notification(self)
        self.current_epoch = 1
        self.genesis_timestamp = dag.genesis_block().timestamp

    def set_logger(self, logger):
        self.logger = logger

    def get_current_timeframe_block_number(self):
        return self.get_block_number_from_timestamp(Time.get_current_time())

    def get_block_number_from_timestamp(self, timestamp):
        time_diff = timestamp - self.genesis_timestamp
        return int(time_diff / BLOCK_TIME)

    def get_current_round(self):
        current_block_number = self.get_current_timeframe_block_number()
        return self.get_round_by_block_number(current_block_number)

    @staticmethod
    def get_round_by_block_number(current_block_number):
        #
        epoch_block_number = Epoch.convert_to_epoch_block_number(current_block_number)
        round_number = int(epoch_block_number / ROUND_DURATION)
        if round_number == Round.INVALID: return Round.FINAL   # special case for last round being +1
        return Round(round_number)

    @staticmethod
    def get_duration():
        return (Round.FINAL + 1) * ROUND_DURATION + 1

    @staticmethod
    def get_epoch_number(current_block_number):
        if current_block_number == 0:
            return 0 
        return (current_block_number - 1) // Epoch.get_duration() + 1  # because genesis block is last block of era zero

    @staticmethod
    def get_epoch_start_block_number(epoch_number):
        if epoch_number == 0: return 0
        return Epoch.get_duration() * (epoch_number - 1) + 1
    
    @staticmethod
    def get_epoch_end_block_number(epoch_number):
        if epoch_number == 0: return 0
        epoch_start_block = Epoch.get_epoch_start_block_number(epoch_number)
        return epoch_start_block + Epoch.get_duration() - 1
    
    def calculate_validators_indexes(self, epoch_hash, validators_count, entropy_source):
        epoch_seed = self.calculate_epoch_seed(epoch_hash)
        entropy = Entropy.get_nth_derivative(epoch_seed, entropy_source)
        validators_list = calculate_validators_indexes(entropy, validators_count)
        return validators_list

    # returns traversable range
    @staticmethod
    def get_round_range(epoch_number, round_type):
        round_start, round_end = Epoch.get_round_bounds(epoch_number, round_type)
        return range(round_start, round_end + 1)

    # returns just tuple
    @staticmethod 
    def get_round_bounds(epoch_number, round_type):
        #
        epoch_start = Epoch.get_epoch_start_block_number(epoch_number)
        round_start = epoch_start + round_type * ROUND_DURATION
        round_end = round_start + ROUND_DURATION - 1
        if round_type == Round.FINAL:
            round_end += 1
        return round_start, round_end

    def get_private_keys_for_epoch(self, block_hash):
        round_iter = RoundIter(self.dag, block_hash, Round.PRIVATE)

        private_keys = []

        for block in round_iter:
            if block and block.block.system_txs:
                for tx in block.block.system_txs:
                    if isinstance(tx, PrivateKeyTransaction):
                        private_keys.append(tx.key)
                        break  # only one private key transaction can exist and it should be signed by block signer
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
                        public_keys[tx.pubkey_index] = tx.generated_pubkey

        return public_keys

    def get_random_splits_for_epoch(self, block_hash):
        random_pieces_list = []
        round_iter = RoundIter(self.dag, block_hash, Round.SECRETSHARE)
        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, SplitRandomTransaction):
                        random_pieces_list.append(tx.pieces)

        random_pieces_list = list(reversed(random_pieces_list))
        return random_pieces_list

    def get_commits_for_epoch(self, block_hash):
        commits = {}
        round_iter = RoundIter(self.dag, block_hash, Round.COMMIT)
        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, CommitRandomTransaction):
                        commits[tx.get_hash()] = tx

        return commits

    def get_reveals_for_epoch(self, block_hash):
        reveals = []
        round_iter = RoundIter(self.dag, block_hash, Round.REVEAL)
        for block in round_iter:
            if block:
                for tx in block.block.system_txs:
                    if isinstance(tx, RevealRandomTransaction):
                        reveals.append(tx)
        return reveals

    def calculate_epoch_seed(self, block_hash):
        secret_shared_random = self.extract_shared_random(block_hash)
        commited_random = self.reveal_commited_random(block_hash)
        return sum_random([secret_shared_random, commited_random])

    def reveal_commited_random(self, block_hash):
        if block_hash == self.dag.genesis_block().get_hash():
            return 0
        
        seed = 0
        commits = self.get_commits_for_epoch(block_hash)
        reveals = self.get_reveals_for_epoch(block_hash)
        randoms_list = []
        
        for reveal in reveals:
            if reveal.commit_hash in commits:
                commit = commits[reveal.commit_hash]
                key = Keys.from_bytes(reveal.key)
                revealed_data = Private.decrypt(commit.rand, key)
                randoms_list.append(int.from_bytes(revealed_data, byteorder='big'))
        seed = sum_random(randoms_list)
        return seed

    def extract_shared_random(self, block_hash):
        if block_hash == self.dag.genesis_block().get_hash():
            return 0
        
        private_keys = self.get_private_keys_for_epoch(block_hash)
        public_keys = self.get_public_keys_for_epoch(block_hash)
        published_private_keys = self.filter_out_skipped_public_keys(private_keys, public_keys)
        random_pieces_list = self.get_random_splits_for_epoch(block_hash)

        # self.log("pubkeys")
        # for _, public_key in public_keys.items():
            # self.log(Keys.to_visual_string(public_key))
        # self.log("privkeys converted")
        private_key_count = 0   # amount of sent keys
        matching_keys_count = 0 # amount of keys which have matching pubkeys 
        for key in published_private_keys:
            if not key:
                # self.log("None")
                continue
            pubkey = Private.publickey(key)
            # self.log(Keys.to_visual_string(pubkey))
            private_key_count += 1
            if Keys.to_bytes(pubkey) in public_keys.values():
                matching_keys_count += 1

        pubkey_count = len(public_keys)
        self.log("pubkey count",
                 pubkey_count,
                 "privkey count",
                 private_key_count,
                 "of them matching",
                 matching_keys_count)

        half_of_pubkeys = int(pubkey_count / 2) + 1
        half_of_privkeys = int(private_key_count / 2) + 1
        
        # TODO we should have a special handling for when not enough keys was sent for each round
        assert pubkey_count > 1, "Not enough public keys to decrypt random"
        assert private_key_count > 1, "Not enough private keys to decrypt random"
        assert pubkey_count >= half_of_privkeys, "Not enough public keys to decrypt random"
        assert private_key_count >= half_of_pubkeys, "Not enough private keys to decrypt random"
        assert matching_keys_count >= half_of_pubkeys, "Not enough matching keys in epoch"
        assert matching_keys_count >= half_of_privkeys, "Not enough matching keys in epoch"

        ordered_private_keys_count = len(private_keys) # total amount of both sent and unsent keys
        randoms_list = []
        for random_pieces in random_pieces_list:
            assert ordered_private_keys_count >= len(random_pieces), "Amount of splits must match amount of public keys"
            random = decode_random(random_pieces, Keys.list_from_bytes(published_private_keys))
            randoms_list.append(random)

        seed = sum_random(randoms_list)
        return seed

    @staticmethod
    def filter_out_skipped_public_keys(private_keys, public_keys):
        filtered_private_keys = []
        for private_key in private_keys:
            if private_key == None:
                filtered_private_keys.append(None)
            else:
                expected_public = Private.publickey(Keys.from_bytes(private_key))
                if Keys.to_bytes(expected_public) in public_keys.values():
                    filtered_private_keys.append(private_key)
        return filtered_private_keys

    def is_last_block_of_epoch(self, block_number):
        if block_number == 0:
            return True

        epoch_number = self.get_epoch_number(block_number)        
        return block_number == Epoch.get_epoch_end_block_number(epoch_number)
    
    @staticmethod
    def convert_to_epoch_block_number(global_block_number):
        epoch_number = Epoch.get_epoch_number(global_block_number)
        epoch_start_block_number = Epoch.get_epoch_start_block_number(epoch_number)
        return global_block_number - epoch_start_block_number
    
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

    def on_top_block_added(self, block, block_hash):
        previous_top_epoch_hash = None
        for prev_hash in block.block.prev_hashes:
            if prev_hash in self.tops_and_epochs:
                # when merging you vote for top hash by putting it first
                # TODO think if we should choose longest chain?
                if not previous_top_epoch_hash:
                    previous_top_epoch_hash = self.tops_and_epochs[prev_hash]
                del self.tops_and_epochs[prev_hash]
        
        if not previous_top_epoch_hash:
            previous_top_epoch_hash = self.find_epoch_hash_for_block(block_hash)
            
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
            # this could be optimized to just taking previous hahash as
            self.tops_and_epochs[top] = top

    def get_previous_epoch_hash(self, epoch_hash):
        block = self.dag.blocks_by_hash[epoch_hash]
        return self.find_epoch_hash_for_block(block.block.prev_hashes[0])

    def log(self, *args):
        if not hasattr(self, "logger"):
            return
        self.logger.debug(args)
        

class RoundIter:
    def __init__(self, dag, block_hash, round_type):
        block_number = dag.get_block_number(block_hash)
        epoch_number = Epoch.get_epoch_number(block_number)
        round_start, round_end = Epoch.get_round_bounds(epoch_number, round_type)
        
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
    
    def current_block_number(self):
        return self.chain_iter.block_number
    
    def next(self):
        return self.__next__()