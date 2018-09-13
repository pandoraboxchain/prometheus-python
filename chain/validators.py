from chain.validator import Validator
from base64 import b64decode,b64encode
from Crypto.PublicKey import RSA

from crypto.keys import Keys

class Validators():

    def __init__(self):
        self.validators = []
        self.signers_order = []
        self.randomizers_order = []

    @staticmethod #reads only pubkeys
    def read_genesis_validators_from_file():
        validators = []
        with open('validators') as f:
            lines = f.readlines()

        for line in lines:
            decode = b64decode(line)
            if len(decode)!=0:
                key = RSA.importKey(decode)
                validator = Validator(key, 100)
                validators.append(validator)
        return validators
