import random

from chain.validators import Validators
from chain.epoch import Epoch

class Permissions():

    def __init__(self, epoch):
        self.validators = Validators()
        self.epoch = epoch
        self.epoch_validators = {}
        self.penalties = []

    def get_permission(self, epoch_hash, block_number_in_epoch):
        validators_for_epoch = self.get_validators_for_epoch_hash(epoch_hash)
        #cycle validators in case of exclusion
        if block_number_in_epoch >= len(validators_for_epoch):
            block_number_in_epoch = block_number_in_epoch % len(validators_for_epoch)
            print("Looping epoch validators. Next block validator is as in block number", block_number_in_epoch)
        
        return validators_for_epoch[block_number_in_epoch]

    def get_validators_for_epoch_hash(self, epoch_hash):
        if not epoch_hash in self.epoch_validators:
            self.calcultate_validators_for_epoch(epoch_hash)

        return self.epoch_validators[epoch_hash]

    def calcultate_validators_for_epoch(self, epoch_hash):
        validators = self.epoch.calculate_validators_indexes(epoch_hash, self.get_validators_count())
        validator_list = self.form_actual_validators_list()
        epoch_validators_pubkeys = []
        for index in validators:
            index = index % len(validator_list)
            epoch_validators_pubkeys.append(validator_list[index].public_key)

        self.epoch_validators[epoch_hash] = epoch_validators_pubkeys

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

    def form_actual_validators_list(self):
        validator_list = []
        for validator in self.validators.validators:
            if not validator in self.penalties:
                validator_list.append(validator)
        return validator_list
    


