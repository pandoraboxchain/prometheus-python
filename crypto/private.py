from Crypto.Hash import SHA256
from Crypto import Random
from Crypto.PublicKey import RSA
from base64 import b64decode,b64encode

class Private():
    @staticmethod
    def generate():
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        return key
    
    @staticmethod
    def sign(message, key):
        return key.sign(message, 0)[0]  #for some reason it returns tuple with second item being None

    @staticmethod
    def encrypt(message, key):
        return key.encrypt(message, 32)[0]  #same thing here

    @staticmethod
    def decrypt(message, key):
        return key.decrypt(message)

