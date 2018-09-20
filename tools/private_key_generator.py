from Crypto import Random
from Crypto.PublicKey import RSA
from base64 import b64encode

random_generator = Random.new().read
key = RSA.generate(1024, random_generator)
binPrivKey = key.exportKey('DER')

print(b64encode(binPrivKey).decode('utf-8'))
