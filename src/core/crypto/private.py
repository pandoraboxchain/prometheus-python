from Crypto import Random
from Crypto.PublicKey import RSA


class Private:
    @staticmethod
    def generate():
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        return key

    @staticmethod
    def sign(message, key):
        return key.sign(message, 0)[0]
