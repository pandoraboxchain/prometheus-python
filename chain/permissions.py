import random

from chain.validator import Validator
from chain.validators import Validators
from chain.epoch import Epoch
from chain.params import Round
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction
from chain.stake_manager import StakeManager
from crypto.keys import Keys

class Permissions():

    def __init__(self, epoch):
        initial_validators = Validators()
        self.epoch = epoch
        self.stake_manager = StakeManager(epoch)
        genesis_hash = self.epoch.dag.genesis_block().get_hash()
        initial_indexes = self.epoch.calculate_validators_indexes(genesis_hash, len(initial_validators.validators))

        self.epoch_validators = { genesis_hash : initial_validators.validators }
        self.epoch_indexes = { genesis_hash : initial_indexes}

    def get_permission(self, epoch_hash, block_number_in_epoch):
        validators_for_epoch = self.get_validators_for_epoch_hash(epoch_hash)
        random_indexes = self.get_indexes_for_epoch_hash(epoch_hash)
        #cycle validators in case of exclusion
        if block_number_in_epoch >= len(validators_for_epoch):
            block_number_in_epoch = block_number_in_epoch % len(validators_for_epoch)
            print("Looping epoch validators. Next block validator is as in block number", block_number_in_epoch)
        index = random_indexes[block_number_in_epoch]
        return validators_for_epoch[index]

    def get_indexes_for_epoch_hash(self, epoch_hash):
        if not epoch_hash in self.epoch_indexes:
            epoch_validators = self.get_validators_for_epoch_hash(epoch_hash)
            print("total validators count", len(epoch_validators))
            random_indexes = self.epoch.calculate_validators_indexes(epoch_hash, len(epoch_validators))
            self.epoch_indexes[epoch_hash] = random_indexes
        
        return self.epoch_indexes[epoch_hash]

    def get_validators_for_epoch_hash(self, epoch_hash):
        if not epoch_hash in self.epoch_validators:
            self.calculate_validators_for_epoch(epoch_hash)

        return self.epoch_validators[epoch_hash]

    def calculate_validators_for_epoch(self, epoch_hash):
        prev_epoch_hash = self.epoch.get_previous_epoch_hash(epoch_hash)
        validators = self.get_validators_for_epoch_hash(prev_epoch_hash)
        stake_actions = self.stake_manager.get_stake_actions(epoch_hash)
        validators = self.apply_stake_actions(validators, stake_actions)
        self.epoch_validators[epoch_hash] = validators

    def get_ordered_pubkeys_for_last_round(self, epoch_hash):
        selected_epoch_validators = self.get_validators_for_epoch_hash(epoch_hash)
        epoch_random_indexes = self.get_indexes_for_epoch_hash(epoch_hash)
        round_start, round_end = Epoch.get_range_for_round(1, Round.PRIVATE)
        validators = []	
        for i in range(round_start - 1, round_end):	
            index = epoch_random_indexes[i]
            validators.append(selected_epoch_validators[index])

        return validators

    def get_random_senders_pubkeys(self, epoch_hash):
        selected_epoch_validators = self.get_validators_for_epoch_hash(epoch_hash)
        epoch_random_indexes = self.get_indexes_for_epoch_hash(epoch_hash)
        round_start, round_end = Epoch.get_range_for_round(1, Round.SECRETSHARE)
        validators = []	
        for i in range(round_start - 1, round_end):	
            index = epoch_random_indexes[i]
            validators.append(selected_epoch_validators[index])

        return validators
    
    def get_block_validator(self, block_hash):
        block_number = self.epoch.dag.get_block_number(block_hash)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(block_number)
        epoch_hash = self.epoch.find_epoch_hash_for_block(block_hash)
        assert epoch_hash, "Can't find epoch hash for block"
        return self.get_permission(epoch_hash, epoch_block_number)

    #this method modifies list, but also returns it for API consistency
    def apply_stake_actions(self, validators, actions):
        for action in actions:
            if isinstance(action, PenaltyTransaction):
                for conflict in action.conflicts:
                    culprit = self.get_block_validator(conflict)
                    self.release_stake(validators, Keys.to_bytes(culprit.public_key))
            elif isinstance(action, StakeHoldTransaction):
                self.hold_stake(validators, action.pubkey, action.amount)
            elif isinstance(action, StakeReleaseTransaction):
                self.release_stake(validators, action.pubkey)
        return validators
                
    def hold_stake(self, validators, pubkey, stake):
        validators.append(Validator(Keys.from_bytes(pubkey), stake))

    def release_stake(self, validators, pubkey):
        for i in range(len(validators)):
            if validators[i].public_key == Keys.from_bytes(pubkey):
                del validators[i]
                break
        
    
    def sort_by_stake(self, validators):
        return sorted(validators, key=attrgetter("stake"), reverse=True)

