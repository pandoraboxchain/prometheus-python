from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.PublicKey import RSA
from base64 import b64decode,b64encode

class Private():
    def generate():
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        return key