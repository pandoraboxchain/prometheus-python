import datetime
from transaction.commits_set import CommitsSet
from crypto.dec_part_random import dec_part_random

BLOCK_TIME = 5

class Round():
    COMMIT = 0
    REVEAL = 1
    PARTIAL = 2

    COMMIT_DURATION = 2
    REVEAL_DURATION = 2
    PARTIAL_DURATION = 2

class Epoch():

    cached_epoch_seeds = {}

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
        epoch_start_block = (epoch_number - 1) * Epoch.get_duration() + 1
        if current_block_number <=  epoch_start_block + Round.COMMIT_DURATION:
            return Round.COMMIT
        elif current_block_number <=  epoch_start_block + Round.COMMIT_DURATION + Round.REVEAL_DURATION:
            return Round.REVEAL
        else:
            return Round.PARTIAL

    def get_duration():
        return Round.COMMIT_DURATION + Round.REVEAL_DURATION + Round.PARTIAL_DURATION

    def get_epoch_number(self, current_block_number):
        if current_block_number == 0:
            return 0 
        return current_block_number // Epoch.get_duration() + 1 #because genesis block is last block of era zero
    
    def get_epoch_hash(self, epoch_number):
        if epoch_number == 0:
            return None
        if epoch_number == 1:
            return self.dag.genesis_block().get_hash().digest()

        previous_era_last_block_number = Epoch.get_duration() * (epoch_number - 1) - 1
        era_identifier_block = self.dag.blocks_by_number[previous_era_last_block_number][0]
        return era_identifier_block.block.get_hash().digest()

    def get_epoch_seed(self, epoch_number):
        if epoch_number in self.cached_epoch_seeds:
            return self.cached_epoch_seeds[epoch_number]
        
        epoch_seed = self.calculate_epoch_seed(epoch_number)
        print("calculated epoch", epoch_number, "seed is", epoch_seed)
        self.cached_epoch_seeds[epoch_number] = epoch_seed

    def calculate_epoch_seed(self, epoch_number):
        if epoch_number == 1:
            return 0
        
        seed = 0
        epoch_hash = self.get_epoch_hash(epoch_number)
        commits_set = CommitsSet(self.dag, epoch_hash)
        reveals = self.collect_reveals_for_epoch(epoch_number - 1)
        for reveal in reveals:
            commit = commits_set.transactions_by_hash[reveal.commited_hash]
            rand = dec_part_random(commit.rand, reveal.key)
            seed += rand
            print("revealed random from", reveal.get_hash(), "is", rand)
        return seed

    def collect_reveals_for_epoch(self, epoch_number):
        reveals = []
        epoch_start_block = (epoch_number - 1) * Epoch.get_duration() + 1
        reveal_round_start_block = epoch_start_block + Round.COMMIT_DURATION
        reveal_round_end_block = reveal_round_start_block + Round.REVEAL_DURATION
        for i in range(reveal_round_start_block,reveal_round_end_block):
            block_list = self.dag.blocks_by_number[i]
            for block in block_list:
                if hasattr(block.block, "system_txs"):
                    for tx in block.block.system_txs:
                        reveals.append(tx)
        return reveals

