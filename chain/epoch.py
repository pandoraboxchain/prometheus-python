import datetime

BLOCK_TIME = 5

class Round():
    COMMIT = 0
    REVEAL = 1
    PARTIAL = 2

    COMMIT_DURATION = 2
    REVEAL_DURATION = 2
    PARTIAL_DURATION = 2

class Epoch():
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
        era_number = self.get_epoch_number(current_block_number)
        era_start_block = era_number * Epoch.get_duration()
        if current_block_number <=  era_start_block + Round.COMMIT_DURATION:
            return Round.COMMIT
        elif current_block_number <=  era_start_block + Round.COMMIT_DURATION + Round.REVEAL_DURATION:
            return Round.REVEAL
        else:
            return Round.PARTIAL

    def get_duration():
        return Round.COMMIT_DURATION + Round.REVEAL_DURATION + Round.PARTIAL_DURATION

    def get_epoch_number(self, current_block_number):
        if current_block_number == 0:
            return 0 
        return current_block_number // Epoch.get_duration() + 1 #because genesis block is last block of era zero
    
    def get_epoch_hash(self, current_era_number):
        if current_era_number == 0:
            return None

        previous_era_last_block_number = Epoch.get_duration() * (current_era_number - 1)
        era_identifier_block = self.dag.blocks_by_number[previous_era_last_block_number][0]
        return era_identifier_block.block.get_hash().digest()