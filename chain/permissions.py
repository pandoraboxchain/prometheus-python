import random

from chain.validators import Validators
from chain.epoch import Epoch

class Permissions():

    def __init__(self, epoch):
        self.validators = Validators()
        self.epoch = epoch
        self.epoch_validators = {}

    def get_permission(self, epoch_hash, block_number_in_epoch):
        validators_for_epoch = self.get_validators_for_epoch_hash(epoch_hash)
        index = validators_for_epoch[block_number_in_epoch]
        return self.validators.get_by_i(index)

    def get_validators_for_epoch_hash(self, epoch_hash):
        if not epoch_hash in self.epoch_validators:
            validators = self.epoch.calculate_validators_indexes(epoch_hash, self.get_validators_count())
            self.epoch_validators[epoch_hash] = validators 
        return self.epoch_validators[epoch_hash]

    def get_validators_count(self):
        return Epoch.get_duration()
        #TODO proper validators count deduction 
        # return self.validators.get_size()

    def get_ordered_pubkeys_for_last_round(self, epoch_hash, count):
        selected_epoch_validators = self.get_validators_for_epoch_hash(epoch_hash)
        length = len(selected_epoch_validators)
        indexes_list = []
        for i in range(length - count, length):
            indexes_list.append(selected_epoch_validators[i])
        
        return self.get_pubkeys_by_indexes_list(indexes_list)

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

    


