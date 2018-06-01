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

