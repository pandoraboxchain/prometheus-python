import random

from chain.validators import Validators

class Permissions():

    def get_permission(self, seed, block_number):
        if not hasattr(self, 'validators'):
            self.validators = Validators()
        index = self.get_next_validator_number(seed, block_number, self.validators.get_size())
        print("next block validator should be node", index)
        return self.validators.get_by_i(index)

    def get_next_validator_number(self, seed, block_number, validators_length):
        random.seed(seed)
        for block_number in range(0, block_number):
            _ = random.random()
        return random.randint(0, validators_length - 1)
