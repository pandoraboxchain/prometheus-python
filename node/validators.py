from node.genesis_validators import GenesisValidators

class Validator:

    def __init__(self, pubkey, stake):
        self.public_key = pubkey
        self.stake = stake


class Validators:

    def __init__(self):
        self.validators = []
        self.signers_order = []
        self.randomizers_order = []

    @staticmethod  # reads only pubkeys
    def read_genesis_validators_from_file():
        validators = []

        for pubkey in GenesisValidators.public_keys:
            validator = Validator(pubkey, 100)
            validators.append(validator)
            
        return validators
