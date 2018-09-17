from base64 import b64decode
from Crypto.PublicKey import RSA


class Validator:

    def __init__(self, pubkey, stake):
        self.public_key = pubkey
        self.stake = stake


class Validators:

    def __init__(self):
        self.validators = []
        self.signers_order = []
        self.randomizers_order = []

    def get_from_file(self):
        with open('../../validators') as f:
            lines = f.readlines()

        for line in lines:
            decode = b64decode(line)
            if len(decode) != 0:
                key = RSA.importKey(decode)
                validator = Validator(key, 100)
                self.validators.append(validator)
        return self.validators

    def get_size(self):
        return len(self.validators)

    def get_by_i(self, i):
        return self.validators[i]

v = Validators()
