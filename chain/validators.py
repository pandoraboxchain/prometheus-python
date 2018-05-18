from chain.validator import Validator
from base64 import b64decode,b64encode
from Crypto.PublicKey import RSA

class Validators():

    def __init__(self):
        self.validators = []

    def get_from_file(self):
        with open('validators') as f:
            lines = f.readlines()

        for line in lines:
            decode = b64decode(line)
            if len(decode)!=0:
                key = RSA.importKey(decode)
                validator = Validator()
                validator.set_publick_key(key)
                self.validators.append(validator)

v = Validators()
