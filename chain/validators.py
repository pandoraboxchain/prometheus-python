from chain.validator import Validator
from base64 import b64decode,b64encode
from Crypto.PublicKey import RSA

from crypto.keys import Keys

class Validators():

    def __init__(self):
        self.validators = []
        self.get_from_file()

    def get_from_file(self):
        with open('validators') as f:
            lines = f.readlines()

        for line in lines:
            decode = b64decode(line)
            if len(decode)!=0:
                key = RSA.importKey(decode)
                validator = Validator(Keys.to_bytes(key), 100)
                self.validators.append(validator)

    def get_size(self):
        return len(self.validators)

    def get_by_i(self, i):
        return self.validators[i]

v = Validators()
