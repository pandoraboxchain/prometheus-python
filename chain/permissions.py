import random

from chain.validators import Validators

class Permissions():

    epoch_validators = {}

    def __init__(self):
        self.validators = Validators()

    def get_permission(self, epoch_number, block_number_in_epoch):
        index = self.epoch_validators[epoch_number][block_number_in_epoch]
        return self.validators.get_by_i(index)

    def get_validators_count(self):
        return self.validators.get_size()
    
    def set_validators_list(self, epoch_number, validators_list):
        self.epoch_validators[epoch_number] = validators_list

    def get_ordered_pubkeys_for_last_round(self, epoch_number, count):
        selected_epoch_validators = self.epoch_validators[epoch_number]
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
        if node_id == 8:
            return True
        return False

    def is_malicious_skip_block(self, node_id):
        if node_id == 1:
            return True
        return False

    


