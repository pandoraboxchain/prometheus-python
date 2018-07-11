import random

from chain.validators import Validators
from chain.epoch import Epoch
from transaction.stake_transaction import StakeHoldTransaction, PenaltyTransaction, StakeReleaseTransaction

class Permissions():

    def __init__(self, epoch):
        initial_validators = Validators()
        self.epoch = epoch
        self.epoch_validators = { genesis_hash : initial_validators.validators }
        genesis_hash = self.epoch.dag.genesis_block().get_hash()

    def get_permission(self, epoch_hash, block_number_in_epoch):
        validators_for_epoch = self.get_validators_for_epoch_hash(epoch_hash)
        #cycle validators in case of exclusion
        if block_number_in_epoch >= len(validators_for_epoch):
            block_number_in_epoch = block_number_in_epoch % len(validators_for_epoch)
            print("Looping epoch validators. Next block validator is as in block number", block_number_in_epoch)
        
        return validators_for_epoch[block_number_in_epoch]

    def get_validators_for_epoch_hash(self, epoch_hash):
        if not epoch_hash in self.epoch_validators:
            self.calculate_validators_for_epoch(epoch_hash)

        return self.epoch_validators[epoch_hash]

    def calculate_validators_for_epoch(self, epoch_hash):
        prev_epoch_hash = self.epoch.get_previous_epoch_hash(epoch_hash)
        validators = self.get_validators_for_epoch_hash(prev_epoch_hash)
        stake_actions = self.epoch.get_stake_actions(epoch_hash)
        validators = self.apply_stake_actions(validators, actions)
        sorted_validators = self.sort_by_stake(validators)
        random_indexes = self.epoch.calculate_validators_indexes(epoch_hash, self.get_validators_count())
        epoch_validators = []
        for index in random_indexes:
            index = index % len(sorted_validators)
            epoch_validators.append(sorted_validators[index])

        self.epoch_validators[epoch_hash] = epoch_validators

    def get_validators_count(self):
        return Epoch.get_duration()
        #TODO proper validators count deduction 
        # return self.validators.get_size()

    def get_ordered_pubkeys_for_last_round(self, epoch_hash, count):
        selected_epoch_validators = self.get_validators_for_epoch_hash(epoch_hash)
        return selected_epoch_validators[-3:]

    def get_pubkeys_by_indexes_list(self, indexes_list):
        pubkeys = []
        for index in indexes_list:
            validator_at_index = self.validators.get_by_i(index)
            pubkeys.append(validator_at_index.public_key)
        return pubkeys

    def is_malicious_excessive_block(self, node_id):
        if node_id == 1:
            return True
        return False

    def is_malicious_skip_block(self, node_id):
        if node_id == 15:
            return True
        return False

    def form_ordered_validators_list(self, epoch_hash):
        holds, releases, penalties = self.epoch.get_stakes_and_penalties_for_epoch(epoch_hash)
        
        penalized = self.get_penalized_pubkeys(penalties)
        validators = []
        for validator in self.validators.validators:
            pubkey = validator.public_key
            if not pubkey in penalized:
                validators.append(pubkey)
 
        return validators
    
    def get_pubkey_of_block_signer(self, block_hash)
        block_number = self.epoch.dag.get_block_number(block_hash)
        epoch_block_number = self.epoch.convert_to_epoch_block_number(block_number)
        epoch_hash = self.epoch.find_epoch_hash_for_block(block_hash)
        assert epoch_hash, "Can't find epoch hash for block"
        return self.get_permission(epoch_hash, epoch_block_number)
    
    def get_penalized_pubkeys(self, penalties):
        pubkeys = []
        for penalty in penalties:
            for block_hash in penalty.conflicts:
                pubkey = self.get_pubkey_of_block_signer(block_hash)
                pubkeys.append(pubkey)
        return pubkey

    #this method modifies list, but also returns it for API consistency
    def apply_stake_actions(self, validators, actions):
        for action in stake_actions:
            if isinstance(action, PenalizeTransaction):
                for conflict in action.conflicts:
                    culprit = self.get_pubkey_of_block_signer(conflict)
                    self.release_stake(validators, culprit)
            elif isinstance(action, StakeHoldTransaction):
                self.hold_stake(validators, action.pubkey, action.amount)
            elif isinstance(action, StakeReleaseTransaction):
                self.release_stake(validators, action.pubkey)
        return validators
                
    def hold_stake(self, validators, pubkey, stake):
        validators.append(Validator(pubkey, stake))

    def release_stake(self, validators, pubkey):
        for i in range(len(validators)):
            if validators[i].pubkey == pubkey:
                del validators[i]
                break
    
    def 1(self, validators):
        return sorted(validators, key=attrgetter("stake"), reverse=True)

